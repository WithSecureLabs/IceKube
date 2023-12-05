from __future__ import annotations

from typing import List

from icekube.models.base import Resource


class User(Resource):
    plural: str = "users"
    supported_api_groups: List[str] = ["", "user.openshift.io"]
