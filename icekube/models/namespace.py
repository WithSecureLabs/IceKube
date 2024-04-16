from __future__ import annotations

import json
from functools import cached_property
from typing import List, Dict, Any

from icekube.models.base import RELATIONSHIP, Resource
from pydantic import computed_field


class Namespace(Resource):
    supported_api_groups: List[str] = [""]

    @computed_field
    @cached_property
    def psa_enforce(self) -> str:
        return self.labels.get("pod-security.kubernetes.io/enforce", "privileged")

    @property
    def db_labels(self) -> Dict[str, Any]:
        return {
            **super().db_labels,
            "psa_enforce": self.psa_enforce,
        }
