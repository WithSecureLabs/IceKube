from __future__ import annotations

import json
from typing import List

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.secret import Secret
from icekube.relationships import Relationship
from pydantic import root_validator
from pydantic.fields import Field


class ServiceAccount(Resource):
    secrets: List[Secret] = Field(default_factory=list)
    supported_api_groups: List[str] = [""]

    @root_validator(pre=True)
    def inject_secrets(cls, values):
        data = json.loads(values.get("raw", "{}"))

        if "secrets" not in values:
            values["secrets"] = []

        if "secrets" in data and data["secrets"] is None:
            data["secrets"] = []

        for secret in data.get("secrets", []):
            values["secrets"].append(
                Secret(  # type: ignore
                    name=secret.get("name", ""),
                    namespace=data.get("metadata", {}).get("namespace", ""),
                )
            )

        return values

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()
        relationships += [
            (x, Relationship.AUTHENTICATION_TOKEN_FOR, self) for x in self.secrets
        ]
        return relationships
