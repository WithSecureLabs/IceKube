from __future__ import annotations

import json
from typing import List

from icekube.models._helpers import load, save
from icekube.models.base import Resource
from icekube.models.policyrule import PolicyRule
from pydantic import model_validator
from pydantic.fields import Field


class ClusterRole(Resource):
    rules: List[PolicyRule] = Field(default_factory=list)
    supported_api_groups: List[str] = [
        "rbac.authorization.k8s.io",
        "authorization.openshift.io",
    ]

    @model_validator(mode="before")
    def inject_rules(cls, values):
        data = json.loads(load(values, "raw", "{}"))

        raw_rules = data.get("rules") or []
        rules = []

        for rule in raw_rules:
            rules.append(PolicyRule(**rule))

        return save(values, "rules", rules)
