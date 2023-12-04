from __future__ import annotations

import json
from typing import List, Optional

from icekube.relationships import Relationship
from icekube.models.base import RELATIONSHIP, BaseResource, Resource
from icekube.models.secret import Secret
from icekube.neo4j_util import mock


class SecretReference(BaseResource):
    apiVersion: str = "v1"
    kind: str = "SecretReference"

    name: str
    namespace: str

    @property
    def db_labels(self):
        return self.model_dump()
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(
            self, 
            Relationship.REFERENCES, 
            mock(Secret, apiVersion="v1", kind="Secret", name=self.name, namespace=self.namespace)
        )]

class ObjectReference(BaseResource):
    apiVersion: str
    kind: str
    name: str
    namespace: Optional[str] = None
    corekind: Optional[str] = "ObjectReference"

    fieldPath: Optional[str] = None
    resourceVersion: Optional[str] = None
    uid: Optional[str] = None

    @property
    def db_labels(self):
        return self.model_dump()
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(
            self, 
            Relationship.REFERENCES, 
            mock(Resource, apiVersion=self.apiVersion, kind=self.kind, name=self.name, namespace=self.namespace)
        )]