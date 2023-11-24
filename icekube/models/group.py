from __future__ import annotations

from typing import Dict

from icekube.models.base import Resource


class Group(Resource):
    plural: str = "groups"

    @property
    def unique_identifiers(self) -> Dict[str, str]:
        return {**super().unique_identifiers, "plural": self.plural}
