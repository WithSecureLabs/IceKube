from typing import List

from pydantic import BaseModel, field_validator


class APIResource(BaseModel):
    name: str
    namespaced: bool
    group: str
    kind: str
    verbs: List[str]
    preferred: bool = False

    @field_validator("kind")
    @classmethod
    def kind_can_only_have_underscore(cls, v: str) -> str:
        s = "".join([x if x.isalnum() else "_" for x in v])
        return s
