from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from icekube.utils import to_camel_case
from kubernetes import client
from pydantic import BaseModel, Field, root_validator

logger = logging.getLogger(__name__)


class Resource(BaseModel):
    apiVersion: str = Field(default=...)
    kind: str = Field(default=...)
    name: str = Field(default=...)
    plural: str = Field(default=...)
    namespace: Optional[str] = Field(default=None)
    raw: Optional[str] = Field(default=None)

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

    @root_validator(pre=True)
    def inject_missing_required_fields(cls, values):
        if not all(x in values for x in ["apiVersion", "kind", "plural"]):
            from icekube.kube import api_resources, preferred_versions

            test_kind = values.get("kind", cls.__name__)  # type: ignore

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
                    if field in values:
                        return values[field]

                    if cls.__fields__[field].default:
                        return cls.__fields__[field].default

                    if field == "kind":
                        return test_kind

                    return "N/A"

                values["apiVersion"] = get_value("apiVersion")
                values["kind"] = get_value("kind")
                values["plural"] = get_value("plural")

                return values

            if "apiVersion" not in values:
                values["apiVersion"] = api_resource.group

            if "kind" not in values:
                values["kind"] = api_resource.kind

            if "plural" not in values:
                values["plural"] = api_resource.name

        return values

    @classmethod
    def get_kind_class(cls, apiVersion: str, kind: str) -> Type[Resource]:
        subclasses = {x.__name__: x for x in cls.__subclasses__()}
        try:
            return subclasses[kind]
        except KeyError:
            return cls

    @property
    def api_group(self) -> str:
        if "/" in self.apiVersion:
            return self.apiVersion.split("/")[0]
        else:
            # When the base APIGroup is ""
            return ""

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
                        namespace, _preload_content=False
                    ).data
                )
            else:
                func = f"list_{to_camel_case(kind)}"
                resp = json.loads(
                    getattr(client.CoreV1Api(), func)(_preload_content=False).data
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
        from icekube.neo4j import mock

        relationships: List[RELATIONSHIP] = []

        if self.namespace is not None:
            ns = mock(Resource, name=self.namespace, kind="Namespace")
            relationships += [
                (
                    self,
                    "WITHIN_NAMESPACE",
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
