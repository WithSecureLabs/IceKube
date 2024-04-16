from __future__ import annotations

import json
import logging
import traceback
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

from icekube.models._helpers import load, save
from icekube.relationships import Relationship
from icekube.utils import to_camel_case
from kubernetes import client
from pydantic import BaseModel, Field, computed_field, model_validator

logger = logging.getLogger(__name__)


def api_group(api_version: str) -> str:
    if "/" in api_version:
        return api_version.split("/")[0]
    # When the base APIGroup is ""
    return ""


class Resource(BaseModel):
    apiVersion: str = Field(default=...)
    kind: str = Field(default=...)
    name: str = Field(default=...)
    plural: str = Field(default=...)
    namespace: Optional[str] = Field(default=None)
    raw: Optional[str] = Field(default=None)
    supported_api_groups: List[str] = Field(default_factory=list)

    def __new__(cls, **kwargs):
        kind_class = cls.get_kind_class(
            kwargs.get("apiVersion", ""),
            kwargs.get("kind", cls.__name__),
        )
        return super(Resource, kind_class).__new__(kind_class)

    def __repr__(self) -> str:
        if self.namespace:
            return f"{self.kind}(namespace='{self.namespace}', name='{self.name}')"
        else:
            return f"{self.kind}(name='{self.name}')"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other) -> bool:
        comparison_points = ["apiVersion", "kind", "namespace", "name"]

        return all(getattr(self, x) == getattr(other, x) for x in comparison_points)

    @cached_property
    def data(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], json.loads(self.raw or "{}"))

    @computed_field  # type: ignore
    @property
    def labels(self) -> Dict[str, str]:
        return cast(Dict[str, str], self.data.get("metadata", {}).get("labels", {}))

    @model_validator(mode="before")
    def inject_missing_required_fields(cls, values):
        if not all(load(values, x) for x in ["apiVersion", "kind", "plural"]):
            from icekube.kube import api_resources, preferred_versions

            test_kind = load(values, "kind", cls.__name__)  # type: ignore

            for x in api_resources():
                if x.kind == test_kind:
                    if "/" in x.group:
                        group, version = x.group.split("/")
                        if preferred_versions[group] != version:
                            continue
                    api_resource = x
                    break
            else:
                # Nothing found, setting them to blank
                def get_value(field):
                    if isinstance(values, dict) and field in values:
                        return values[field]
                    elif not isinstance(values, dict) and getattr(values, field):
                        return getattr(values, field)

                    if cls.__fields__[field].default:
                        return cls.__fields__[field].default

                    if field == "kind":
                        return test_kind

                    return "N/A"

                for t in ["apiVersion", "kind", "plural"]:
                    values = save(values, t, get_value(t))

                return values

            for attr, val in [
                ("apiVersion", api_resource.group),
                ("kind", api_resource.kind),
                ("plural", api_resource.name),
            ]:
                if load(values, attr) is None:
                    values = save(values, attr, val)

        return values

    @classmethod
    def get_kind_class(cls, apiVersion: str, kind: str) -> Type[Resource]:
        for subclass in cls.__subclasses__():
            if subclass.__name__ != kind:
                continue

            supported = subclass.model_fields["supported_api_groups"].default
            if not isinstance(supported, list):
                continue

            if api_group(apiVersion) not in supported:
                continue

            return subclass

        return cls

    @property
    def api_group(self) -> str:
        return api_group(self.apiVersion)

    @property
    def resource_definition_name(self) -> str:
        if self.api_group:
            return f"{self.plural}.{self.api_group}"
        else:
            return self.plural

    @property
    def unique_identifiers(self) -> Dict[str, str]:
        ident = {
            "apiGroup": self.api_group,
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "name": self.name,
        }
        if self.namespace:
            ident["namespace"] = self.namespace
        return ident

    @property
    def db_labels(self) -> Dict[str, Any]:
        return {
            **self.unique_identifiers,
            "plural": self.plural,
            "raw": self.raw,
        }

    @classmethod
    def list(
        cls: Type[Resource],
        apiVersion: str,
        kind: str,
        name: str,
        namespace: Optional[str] = None,
    ) -> List[Resource]:
        try:
            group, version = apiVersion.split("/")
        except ValueError:
            # Core v1 API
            group = None
            version = apiVersion
        resources: List[Resource] = []
        if group:
            if namespace:
                resp = client.CustomObjectsApi().list_namespaced_custom_object(
                    group,
                    version,
                    namespace,
                    name,
                )
            else:
                resp = client.CustomObjectsApi().list_cluster_custom_object(
                    group,
                    version,
                    name,
                )
        else:
            if namespace:
                func = f"list_namespaced_{to_camel_case(kind)}"
                resp = json.loads(
                    getattr(client.CoreV1Api(), func)(
                        namespace,
                        _preload_content=False,
                    ).data,
                )
            else:
                func = f"list_{to_camel_case(kind)}"
                resp = json.loads(
                    getattr(client.CoreV1Api(), func)(_preload_content=False).data,
                )

        for item in resp.get("items", []):
            item["apiVersion"] = apiVersion
            item["kind"] = kind
            try:
                resources.append(
                    Resource(
                        apiVersion=apiVersion,
                        kind=kind,
                        name=item["metadata"]["name"],
                        namespace=item["metadata"]["namespace"] if namespace else None,
                        plural=name,
                        raw=json.dumps(item, default=str),
                    ),
                )
            except Exception:
                logger.error(
                    f"Error when processing {kind} - "
                    f"{item['metadata'].get('namespace', '')}:"
                    f"{item['metadata']['name']}",
                )
                traceback.print_exc()

        return resources

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        logger.debug(
            f"Generating {'initial' if initial else 'second'} set of relationships",
        )
        relationships: List[RELATIONSHIP] = []

        if self.namespace is not None:
            ns = Resource(name=self.namespace, kind="Namespace")
            relationships += [
                (
                    self,
                    Relationship.WITHIN_NAMESPACE,
                    ns,
                ),
            ]

        return relationships


QUERY_RESOURCE = Tuple[str, Dict[str, str]]

RELATIONSHIP = Tuple[
    Union[Resource, QUERY_RESOURCE],
    Union[str, List[str]],
    Union[Resource, QUERY_RESOURCE],
]
