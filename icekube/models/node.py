from __future__ import annotations

from typing import List

from icekube.models.base import Resource


class Node(Resource):
    supported_api_groups: List[str] = [""]
