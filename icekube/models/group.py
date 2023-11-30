from __future__ import annotations

from typing import List

from icekube.models.base import Resource


class Group(Resource):
    plural: str = "groups"
    supported_api_groups: List[str] = ["", "user.openshift.io"]
