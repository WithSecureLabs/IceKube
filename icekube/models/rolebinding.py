from __future__ import annotations

from functools import cached_property
from typing import List, Union

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.clusterrole import ClusterRole
from icekube.models.clusterrolebinding import get_role, get_subjects
from icekube.models.group import Group
from icekube.models.role import Role
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from icekube.relationships import Relationship
from pydantic import computed_field


class RoleBinding(Resource):
    supported_api_groups: List[str] = [
        "rbac.authorization.k8s.io",
        "authorization.openshift.io",
    ]

    @computed_field  # type: ignore
    @cached_property
    def role(self) -> Union[ClusterRole, Role]:
        role_ref = self.data.get("roleRef")

        if role_ref:
            return get_role(role_ref, self.namespace)
        else:
            return ClusterRole(name="")

    @computed_field  # type: ignore
    @cached_property
    def subjects(self) -> List[Union[ServiceAccount, User, Group]]:
        return get_subjects(self.data.get("subjects", []), self.namespace)

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()
        relationships += [(self, Relationship.GRANTS_PERMISSION, self.role)]
        relationships += [
            (subject, Relationship.BOUND_TO, self) for subject in self.subjects
        ]

        if not initial:
            for role_rule in self.role.rules:
                for relationship, resource in role_rule.affected_resource_query(
                    self.namespace,
                ):
                    relationships.append((self, relationship, resource))

        return relationships
