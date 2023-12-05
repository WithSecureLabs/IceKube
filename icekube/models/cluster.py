from typing import Dict, List

from icekube.models.base import RELATIONSHIP, Resource


class Cluster(Resource):
    version: str
    kind: str = "Cluster"
    apiVersion: str = "N/A"
    plural: str = "clusters"
    supported_api_groups: List[str] = ["N"]

    def __repr__(self) -> str:
        return f"Cluster(name='{self.name}', version='{self.version}')"

    @property
    def db_labels(self) -> Dict[str, str]:
        return {
            **self.unique_identifiers,
            "plural": self.plural,
            "version": self.version,
        }

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        query = "MATCH (src) WHERE NOT src.apiVersion = 'N/A' "

        relationships += [((query, {}), "WITHIN_CLUSTER", self)]

        return relationships
