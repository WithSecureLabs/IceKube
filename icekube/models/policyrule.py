import itertools
from fnmatch import filter as fnfilter
from fnmatch import fnmatch
from typing import Dict, Iterator, List, Optional, Tuple, Union

from icekube.relationships import Relationship
from pydantic import BaseModel
from pydantic.fields import Field


def generate_query(
    filters: Dict[str, Union[str, List[str]]]
) -> Tuple[str, Dict[str, str]]:
    query = "MATCH ({prefix}) WHERE"
    final_filters = {}
    query_parts = []
    for key, value in filters.items():
        if isinstance(value, list):
            part = " OR ".join(
                f"{{prefix}}.{key} =~ ${{prefix}}_{key}_{idx}"
                for idx in range(len(value))
            )
            query_parts.append(f" ({part}) ")
            for idx, v in enumerate(value):
                final_filters[f"{key}_{idx}"] = v
        else:
            query_parts.append(f" {{prefix}}.{key} =~ ${{prefix}}_{key} ")
            final_filters[key] = value
    query += "AND".join(query_parts)
    return query, final_filters


def remove_version(group):
    if "/" in group:
        return group.split("/")[0]
    else:
        return ""


class PolicyRule(BaseModel):
    apiGroups: List[str] = Field(default_factory=list)
    nonResourceURLs: List[str] = Field(default_factory=list)
    resourceNames: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    verbs: List[str] = Field(default_factory=list)

    @property
    def contains_csr_approval(self) -> bool:
        resource = any(
            fnmatch("certificatesigningrequests/approval", x) for x in self.resources
        )
        verb = any(fnmatch("update", x) for x in self.verbs)

        return resource and verb

    def api_resources(self):
        from icekube.kube import api_resources

        for api_group, resource in itertools.product(self.apiGroups, self.resources):
            for res in api_resources():
                if fnmatch(remove_version(res.group), api_group) and fnmatch(
                    res.name,
                    resource,
                ):
                    yield res

    def affected_resource_query(
        self,
        namespace: Optional[str] = None,
    ) -> Iterator[Tuple[Union[str, List[str]], Tuple[str, Dict[str, str]]]]:
        for api_resource in self.api_resources():
            resource = api_resource.name
            sub_resource = None
            if "/" in resource:
                resource, sub_resource = resource.split("/")
                sub_resource.replace("-", "_")

            find_filter = {"apiVersion": api_resource.group, "plural": resource}
            if namespace:
                find_filter["namespace"] = namespace

            valid_verbs = set()
            for verb in self.verbs:
                valid_verbs.update(fnfilter(api_resource.verbs, verb.lower()))

            if "create" in valid_verbs and sub_resource is None:
                if namespace:
                    query_filter: Dict[str, Union[str, List[str]]] = {
                        "kind": "Namespace",
                        "name": namespace,
                    }
                else:
                    query_filter = {"kind": "Cluster"}
                    yield (
                        Relationship.generate_grant(resource, "CREATE"),
                        generate_query(query_filter),
                    )
                    query_filter = {"kind": "Namespace"}
                yield (
                    Relationship.generate_grant(resource, "CREATE"),
                    generate_query(query_filter),
                )
                valid_verbs.remove("create")

            if not valid_verbs:
                continue

            tags = [Relationship.generate_grant(verb, sub_resource) for verb in valid_verbs]

            if not self.resourceNames:
                yield (tags, generate_query(find_filter))
            else:
                names = [name.replace("*", ".*") for name in self.resourceNames]
                yield (tags, generate_query({**find_filter, "name": names}))
