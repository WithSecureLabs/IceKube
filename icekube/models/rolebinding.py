from __future__ import annotations

import json
from typing import List, Union

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.clusterrole import ClusterRole
from icekube.models.clusterrolebinding import get_role, get_subjects
from icekube.models.group import Group
from icekube.models.role import Role
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from icekube.relationships import Relationship
from pydantic import root_validator
from pydantic.fields import Field


class RoleBinding(Resource):
    role: Union[ClusterRole, Role]
    subjects: List[Union[ServiceAccount, User, Group]] = Field(default_factory=list)
    supported_api_groups: List[str] = [
        "rbac.authorization.k8s.io",
        "authorization.openshift.io",
    ]

    @root_validator(pre=True)
    def inject_role_and_subjects(cls, values):
        data = json.loads(values.get("raw", "{}"))

        ns = values.get("namespace")

        role_ref = data.get("roleRef")
        if role_ref:
            values["role"] = get_role(role_ref, ns)
        else:
            values["role"] = ClusterRole(name="")

        values["subjects"] = get_subjects(data.get("subjects", []), ns)

        return values

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
