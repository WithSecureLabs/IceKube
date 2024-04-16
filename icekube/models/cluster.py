import re

from typing import Dict, List

from icekube.models.base import RELATIONSHIP, Resource
from pydantic import computed_field


class Cluster(Resource):
    version: str
    kind: str = "Cluster"
    apiVersion: str = "N/A"
    plural: str = "clusters"
    supported_api_groups: List[str] = ["N"]

    def __repr__(self) -> str:
        return f"Cluster(name='{self.name}', version='{self.version}')"

    @computed_field
    @property
    def major_minor_version(self) -> float:
        return float(re.match(r"^v?(\d+\.\d+)[^\d]", self.version).groups()[0])

    @property
    def db_labels(self) -> Dict[str, str]:
        return {
            **self.unique_identifiers,
            "plural": self.plural,
            "version": self.version,
            "major_minor": self.major_minor_version,
        }

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        query = "MATCH (src) WHERE NOT src.apiVersion = 'N/A' "

        relationships += [((query, {}), "WITHIN_CLUSTER", self)]

        return relationships
