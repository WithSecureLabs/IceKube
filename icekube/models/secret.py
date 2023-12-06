from __future__ import annotations

import json
from functools import cached_property
from typing import Any, Dict, List, Optional, cast

from icekube.models.base import RELATIONSHIP, Resource
from icekube.relationships import Relationship
from pydantic import computed_field, field_validator


class Secret(Resource):
    supported_api_groups: List[str] = [""]

    @field_validator("raw")
    @classmethod
    def remove_secret_data(cls, v: Optional[str]) -> Optional[str]:
        if v:
            data = json.loads(v)

            if "data" in data:
                del data["data"]

            return json.dumps(data)

        return v

    @computed_field  # type: ignore
    @cached_property
    def secret_type(self) -> str:
        return cast(str, self.data.get("type", ""))

    @computed_field  # type: ignore
    @cached_property
    def annotations(self) -> Dict[str, Any]:
        return self.data.get("metadata", {}).get("annotations") or {}

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        if self.secret_type == "kubernetes.io/service-account-token":
            from icekube.models.serviceaccount import ServiceAccount

            sa = self.annotations.get("kubernetes.io/service-account.name")
            if sa:
                account = ServiceAccount(
                    name=sa,
                    namespace=cast(str, self.namespace),
                )
                relationships.append(
                    (
                        self,
                        Relationship.AUTHENTICATION_TOKEN_FOR,
                        account,
                    ),
                )

        return relationships
