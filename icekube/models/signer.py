from typing import Dict, List

from icekube.models.base import Resource


class Signer(Resource):
    apiVersion: str = "certificates.k8s.io/v1"
    kind: str = "Signer"
    plural: str = "signers"
    supported_api_groups: List[str] = ["certificates.k8s.io"]

    def __repr__(self) -> str:
        return f"Signer(name={self.name})"

    @property
    def db_labels(self) -> Dict[str, str]:
        return {
            **self.unique_identifiers,
            "plural": self.plural,
        }
