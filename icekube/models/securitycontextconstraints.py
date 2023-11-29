from __future__ import annotations

import json
from typing import List, Union

from icekube.models._helpers import load, save
from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.group import Group
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.user import User
from pydantic import model_validator
from pydantic.fields import Field


class SecurityContextConstraints(Resource):
    plural: str = "securitycontextconstraints"
    users: List[Union[User, ServiceAccount]] = Field(default_factory=list)
    groups: List[Group]
    supported_api_groups: List[str] = ["security.openshift.io"]

    @model_validator(mode="before")
    def inject_users_and_groups(cls, values):
        data = json.loads(load(values, "raw", "{}"))

        raw_users = data.get("users", [])
        users: List[Union[User, ServiceAccount]] = []
        for user in raw_users:
            if user.startswith("system:serviceaccount:"):
                ns, name = user.split(":")[2:]
                users.append(
                    ServiceAccount(
                        ServiceAccount,
                        name=name,
                        namespace=ns,
                    ),
                )
            else:
                users.append(User(name=user))

        groups = []
        raw_groups = data.get("groups", [])
        for group in raw_groups:
            groups.append(Group(name=group))

        values = save(values, "users", users)
        values = save(values, "groups", groups)

        return values

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        relationships += [(x, "GRANTS_USE", self) for x in self.users + self.groups]

        return relationships
