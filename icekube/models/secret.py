from __future__ import annotations

import json
from typing import Any, Dict, List, cast

from icekube.models.base import RELATIONSHIP, Resource
from icekube.neo4j import mock
from icekube.relationships import Relationship
from pydantic import root_validator


class Secret(Resource):
    secret_type: str
    annotations: Dict[str, Any]

    @root_validator(pre=True)
    def remove_secret_data(cls, values):
        data = json.loads(values.get("raw", "{}"))
        if "data" in data:
            del data["data"]

        values["raw"] = json.dumps(data)

        return values

    @root_validator(pre=True)
    def extract_type(cls, values):
        data = json.loads(values.get("raw", "{}"))
        values["secret_type"] = data.get("type", "")

        return values

    @root_validator(pre=True)
    def extract_annotations(cls, values):
        data = json.loads(values.get("raw", "{}"))
        values["annotations"] = data.get("metadata", {}).get("annotations") or {}

        return values

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        if self.secret_type == "kubernetes.io/service-account-token":
            from icekube.models.serviceaccount import ServiceAccount

            sa = self.annotations.get("kubernetes.io/service-account.name")
            if sa:
                account = mock(
                    ServiceAccount,
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
