from __future__ import annotations

from functools import cached_property
from typing import List

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.secret import Secret
from icekube.relationships import Relationship
from pydantic import computed_field


class ServiceAccount(Resource):
    supported_api_groups: List[str] = [""]

    @computed_field  # type: ignore
    @cached_property
    def secrets(self) -> List[Secret]:
        secrets = []
        raw_secrets = self.data.get("secrets") or []

        for secret in raw_secrets:
            secrets.append(
                Secret(name=secret.get("name", ""), namespace=self.namespace),
            )

        return secrets

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()
        relationships += [
            (x, Relationship.AUTHENTICATION_TOKEN_FOR, self) for x in self.secrets
        ]
        return relationships
