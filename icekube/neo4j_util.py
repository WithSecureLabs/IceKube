from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from icekube.models import Cluster
from neo4j.io import ServiceUnavailable

T = TypeVar("T")

logger = logging.getLogger(__name__)


# Created file to resolve circular dependency when importing cluster
def find_or_mock(resource: Type[T], **kwargs: str) -> T:
    from icekube.neo4j import find
    try:
        return next(find(resource, **kwargs))  # type: ignore
    except (StopIteration, IndexError, ServiceUnavailable):
        return resource(**kwargs)


def mock(resource: Type[T], **kwargs: str) -> T:
    return resource(**kwargs)


cluster: Optional[Cluster] = None


def get_cluster_object() -> Cluster:
    global cluster

    if cluster:
        return cluster

    return find_or_mock(Cluster, kind="Cluster")
