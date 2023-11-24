from typing import List

from pydantic import BaseModel


class APIResource(BaseModel):
    name: str
    namespaced: bool
    group: str
    kind: str
    verbs: List[str]
    preferred: bool = False
