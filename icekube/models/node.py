from __future__ import annotations
from typing import List, Optional

from icekube.models.base import BaseResource, Resource


class NodeSelectorRequirement(BaseResource):
    apiVersion: str = "v1"
    kind: str = "NodeSelectorRequirement"

    key: str
    operator: str
    values: List[str]

    @property
    def db_labels(self):
        return self.model_dump()

class NodeSelectorTerm(BaseResource):
    apiVersion: str = "v1"
    kind: str = "NodeSelectorTerm"

    matchExpressions: Optional[NodeSelectorRequirement]
    matchFields: Optional[NodeSelectorRequirement]

    @property
    def db_labels(self):
        return {
            "matchExpressions": self.matchExpressions.objHash,
            "matchFields": self.matchFields.objHash
        }
    
    @property
    def referenced_objects(self):
        return [
            self.matchExpressions,
            self.matchFields
        ]

class NodeSelector(BaseResource):
    apiVersion: str = "v1"
    kind: str = "NodeSelector"

    nodeSelectorTerms: NodeSelectorTerm

    @property
    def db_labels(self):
        return {
            "nodeSelectorTerms": self.nodeSelectorTerms.objHash
        }
    
    @property
    def referenced_objects(self):
        return [
            self.nodeSelectorTerms
        ]



class Node(Resource):
    ...
