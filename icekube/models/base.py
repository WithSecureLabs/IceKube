from __future__ import annotations

import hashlib
import json
import logging
import traceback
from json import JSONEncoder
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from icekube.relationships import Relationship
from icekube.utils import to_camel_case
from kubernetes import client
from pydantic import BaseModel, Field, root_validator

logger = logging.getLogger(__name__)


class ResourceDecoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()

        if not hasattr(obj, "__dict__"):
            return obj

        return obj.__dict__


class BaseResource(BaseModel):
    apiVersion: str = Field(default=...)
    kind: str = Field(default=...)
    objHash: Optional[str] = Field(default=None)

    def __new__(cls, **kwargs):
        kind_class = cls.get_kind_class(
            kwargs.get("apiVersion", ""),
            kwargs.get("corekind", kwargs.get("kind", cls.__name__)),
        )
        return super(BaseResource, kind_class).__new__(kind_class)

    def __repr__(self) -> str:
        if self.objHash is not None:
            return (
                f'{self.kind}(apiVersion="{self.apiVersion}", objHash="{self.objHash}")'
            )
        return f'{self.kind}(apiVersion="{self.apiVersion}")'

    def __str__(self) -> str:
        return self.__repr__()

    @root_validator(pre=True)
    def inject_object_hash(cls, values):
        if isinstance(values, str):
            # This could be happening due to some subclasses
            # redefining the type of the field as a string/hash
            # and when deserializing, we think that the value stored
            # in neo4j is a struct, but actually is a hash value.
            from icekube.neo4j import find

            found = list(find(type(cls), raw=False, **{"objHash": values}))
            return found[0].model_dump() if len(found) > 0 else values

        if "objHash" not in values or values["objHash"] is None:
            jsonObj = json.dumps(values, cls=ResourceDecoder)
            jsonHash = hashlib.sha256(jsonObj.encode("utf-8")).hexdigest()
            values["objHash"] = jsonHash

        return values

    @classmethod
    def get_kind_class(cls, apiVersion: str, kind: str) -> Type[BaseResource]:
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
    def unique_identifiers(self) -> Dict[str, str]:
        return {
            "apiGroup": self.api_group,
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "objHash": self.objHash if self.objHash is not None else "",
        }

    @property
    def db_labels(self):
        labels = {
            k: (
                v["objHash"]
                if v is not None and "objHash" in v
                else [
                    i["objHash"] if i is not None and "objHash" in i else i for i in v
                ]
                if isinstance(v, list)
                else v
            )
            for k, v in self.model_dump().items()
        }

        if self.kind is None:
            labels["kind"] = self.__class__.__name__

        return labels

    @property
    def referenced_objects(self) -> List[Optional[BaseResource]]:
        return []

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [
            (self, Relationship.DEFINES, i)
            for i in self.referenced_objects
            if i is not None
        ]


class Resource(BaseResource):
    name: str = Field(default=...)
    plural: str = Field(default=...)
    namespace: Optional[str] = Field(default=None)
    raw: Optional[str] = Field(default=None)

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
            "objHash": self.objHash if self.objHash is not None else "",
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
                    Relationship.WITHIN_NAMESPACE,
                    ns,
                ),
            ]

        return relationships


QUERY_RESOURCE = Tuple[str, Dict[str, str]]

RELATIONSHIP = Tuple[
    Union[BaseResource, QUERY_RESOURCE],
    Union[str, List[str]],
    Union[BaseResource, QUERY_RESOURCE],
]
