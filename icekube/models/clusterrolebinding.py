from __future__ import annotations

from functools import cached_property
from typing import Any, Dict, List, Optional, Union

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.clusterrole import ClusterRole
from icekube.models.group import Group
from icekube.models.role import Role
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from icekube.relationships import Relationship
from pydantic import computed_field


def get_role(
    role_ref: Dict[str, Any],
    namespace: Optional[str] = None,
) -> Union[ClusterRole, Role]:
    from icekube.neo4j import find_or_mock

    role_ref["kind"] = role_ref.get("kind", "ClusterRole")
    if role_ref["kind"] == "ClusterRole":
        return find_or_mock(ClusterRole, name=role_ref["name"])
    elif role_ref["kind"] == "Role":
        return find_or_mock(
            Role,
            name=role_ref["name"],
            namespace=role_ref.get("namespace", namespace),
        )
    else:
        raise Exception(f"Unknown RoleRef kind: {role_ref['kind']}")


def get_subjects(
    subjects: List[Dict[str, Any]],
    namespace: Optional[str] = None,
) -> List[Union[ServiceAccount, User, Group]]:
    results: List[Union[ServiceAccount, User, Group]] = []

    if subjects is None:
        return results

    for subject in subjects:
        if subject["kind"] in ["SystemUser", "User"]:
            results.append(User(name=subject["name"]))
        elif subject["kind"] in ["SystemGroup", "Group"]:
            results.append(Group(name=subject["name"]))
        elif subject["kind"] == "ServiceAccount":
            results.append(
                ServiceAccount(
                    name=subject["name"],
                    namespace=subject.get("namespace", namespace),
                ),
            )
        else:
            raise Exception(f"Unknown Subject Kind: {subject['kind']}")

    return results


class ClusterRoleBinding(Resource):
    supported_api_groups: List[str] = [
        "rbac.authorization.k8s.io",
        "authorization.openshift.io",
    ]

    @computed_field  # type: ignore
    @cached_property
    def role(self) -> Union[ClusterRole, Role]:
        role_ref = self.data.get("roleRef")
        if role_ref:
            return get_role(role_ref)
        else:
            return ClusterRole(name="")

    @computed_field  # type: ignore
    @cached_property
    def subjects(self) -> List[Union[ServiceAccount, User, Group]]:
        return get_subjects(self.data.get("subjects", []))

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()
        relationships += [(self, Relationship.GRANTS_PERMISSION, self.role)]
        relationships += [
            (subject, Relationship.BOUND_TO, self) for subject in self.subjects
        ]

        cluster_query = (
            "MATCH ({prefix}) WHERE {prefix}.kind =~ ${prefix}_kind ",
            {"apiVersion": "N/A", "kind": "Cluster"},
        )

        if not initial:
            for role_rule in self.role.rules:
                if role_rule.contains_csr_approval:
                    relationships.append(
                        (self, Relationship.HAS_CSR_APPROVAL, cluster_query),
                    )
                for relationship, resource in role_rule.affected_resource_query():
                    relationships.append((self, relationship, resource))

        return relationships
