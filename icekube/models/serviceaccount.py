from __future__ import annotations

import json
from typing import List

from icekube.models._helpers import load, save
from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.secret import Secret
from icekube.relationships import Relationship
from pydantic import model_validator
from pydantic.fields import Field


class ServiceAccount(Resource):
    secrets: List[Secret] = Field(default_factory=list)
    supported_api_groups: List[str] = [""]

    @model_validator(mode="before")
    def inject_secrets(cls, values):
        data = json.loads(load(values, "raw", "{}"))

        secrets = []
        raw_secrets = data.get("secrets") or []

        for secret in raw_secrets:
            secrets.append(
                Secret(  # type: ignore
                    name=secret.get("name", ""),
                    namespace=data.get("metadata", {}).get("namespace", ""),
                )
            )

        return save(values, "secrets", secrets)

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()
        relationships += [
            (x, Relationship.AUTHENTICATION_TOKEN_FOR, self) for x in self.secrets
        ]
        return relationships
