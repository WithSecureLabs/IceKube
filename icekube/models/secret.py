from __future__ import annotations

import json
from typing import Any, Dict, List, cast

from icekube.models._helpers import load, save
from icekube.models.base import RELATIONSHIP, Resource
from icekube.relationships import Relationship
from pydantic import model_validator


class Secret(Resource):
    secret_type: str
    annotations: Dict[str, Any]
    supported_api_groups: List[str] = [""]

    @model_validator(mode="before")
    def remove_secret_data(cls, values):
        data = json.loads(load(values, "raw", "{}"))
        if "data" in data:
            del data["data"]

        return save(values, "raw", json.dumps(data))

    @model_validator(mode="before")
    def extract_type(cls, values):
        data = json.loads(load(values, "raw", "{}"))

        return save(values, "secret_type", data.get("type", ""))

    @model_validator(mode="before")
    def extract_annotations(cls, values):
        data = json.loads(load(values, "raw", "{}"))

        return save(
            values, "annotations", data.get("metadata", {}).get("annotations") or {}
        )

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
