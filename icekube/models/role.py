from __future__ import annotations

import json
from typing import List

from icekube.models.base import Resource
from icekube.models.policyrule import PolicyRule
from pydantic import root_validator
from pydantic.fields import Field


class Role(Resource):
    rules: List[PolicyRule] = Field(default_factory=list)

    @root_validator(pre=True)
    def inject_role(cls, values):
        data = json.loads(values.get("raw", "{}"))

        if "rules" not in values:
            values["rules"] = []

        for rule in data.get("rules", []) or []:
            values["rules"].append(PolicyRule(**rule))

        return values
