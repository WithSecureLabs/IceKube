from __future__ import annotations

from functools import cached_property
from typing import List, Union

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.group import Group
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from pydantic import computed_field


class SecurityContextConstraints(Resource):
    plural: str = "securitycontextconstraints"
    supported_api_groups: List[str] = ["security.openshift.io"]

    @computed_field
    @cached_property
    def users(self) -> List[Union[User, ServiceAccount]]:
        users = []
        raw_users = self.data.get("users", [])

        for user in raw_users:
            if user.startswith("system:serviceaccount:"):
                ns, name = user.split(":")[2:]
                users.append(ServiceAccount(name=name, namespace=ns))
            else:
                users.append(User(name=user))

        return users

    @computed_field
    @cached_property
    def groups(self) -> List[Group]:
        raw_groups = self.data.get("groups", [])

        return [Group(name=x) for x in raw_groups]

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        relationships += [(x, "GRANTS_USE", self) for x in self.users + self.groups]

        return relationships
