from __future__ import annotations

from functools import cached_property
from typing import List

from icekube.models.base import Resource
from icekube.models.policyrule import PolicyRule
from pydantic import computed_field


class Role(Resource):
    supported_api_groups: List[str] = [
        "rbac.authorization.k8s.io",
        "authorization.openshift.io",
    ]

    @computed_field  # type: ignore
    @cached_property
    def rules(self) -> List[PolicyRule]:
        rules = []
        raw_rules = self.data.get("rules") or []

        for rule in raw_rules:
            rules.append(PolicyRule(**rule))

        return rules
