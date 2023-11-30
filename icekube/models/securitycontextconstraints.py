from __future__ import annotations

import json
from typing import List, Union

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.group import Group
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from pydantic import root_validator
from pydantic.fields import Field


class SecurityContextConstraints(Resource):
    plural: str = "securitycontextconstraints"
    users: List[Union[User, ServiceAccount]] = Field(default_factory=list)
    groups: List[Group]
    supported_api_groups: List[str] = ["security.openshift.io"]

    @root_validator(pre=True)
    def inject_users_and_groups(cls, values):
        data = json.loads(values.get("raw", {}))

        users = data.get("users", [])
        values["users"] = []
        for user in users:
            if user.startswith("system:serviceaccount:"):
                ns, name = user.split(":")[2:]
                values["users"].append(
                    ServiceAccount(
                        name=name,
                        namespace=ns,
                    ),
                )
            else:
                values["users"].append(User(name=user))

        groups = data.get("groups", [])
        values["groups"] = []
        for group in groups:
            values["groups"].append(Group(name=group))

        return values

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        relationships += [(x, "GRANTS_USE", self) for x in self.users + self.groups]

        return relationships
