from __future__ import annotations

from typing import Any, Dict, List

from icekube.models.base import Resource
from pydantic import computed_field


class Node(Resource):
    supported_api_groups: List[str] = [""]

    @computed_field  # type: ignore
    @property
    def node_roles(self) -> List[str]:
        return [
            x.split("/", 1)[1]
            for x in self.labels.keys()
            if x.startswith("node-role.kubernetes.io/")
        ]

    @property
    def db_labels(self) -> Dict[str, Any]:
        return {
            **super().db_labels,
            "node_roles": self.node_roles,
        }
