from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, TypeVar

from icekube.config import config
from icekube.models import Cluster, Resource
from neo4j import BoltDriver, GraphDatabase
from neo4j.io import ServiceUnavailable

T = TypeVar("T")

logger = logging.getLogger(__name__)


driver: Optional[BoltDriver] = None


def get_driver() -> BoltDriver:
    global driver

    if not driver:
        driver = init_connection()

    return driver


def init_connection(
    uri: str = "bolt://localhost:7687",
    auth: Tuple[str, str] = ("neo4j", "neo4j"),
    encrypted: bool = False,
) -> BoltDriver:
    neo4j_config = config.get("neo4j", {})
    uri = neo4j_config.get("url", uri)
    auth = (
        neo4j_config.get("username", auth[0]),
        neo4j_config.get("password", auth[1]),
    )
    encrypted = neo4j_config.get("encrypted", encrypted)

    return GraphDatabase.driver(uri, auth=auth, encrypted=encrypted)


def create_index(kind: str, namespace: bool) -> None:
    cmd = f"CREATE INDEX {kind.lower()} FOR (n:{kind}) ON (n.name"
    if namespace:
        cmd += ", n.namespace"
    cmd += ")"

    driver = get_driver()

    with driver.session() as session:
        session.run(cmd)


def get(
    resource: Resource,
    identifier: str = "",
    prefix: str = "",
) -> Tuple[str, Dict[str, str]]:
    kwargs: Dict[str, str] = {}
    labels: List[str] = []
    identifier = identifier or prefix

    if prefix:
        prefix += "_"

    for key, value in resource.unique_identifiers.items():
        labels.append(f"{key}: ${prefix}{key}")
        kwargs[f"{prefix}{key}"] = value

    cmd = f"MERGE ({identifier}:{resource.kind} {{ {', '.join(labels)} }}) "

    return cmd, kwargs


def create(resource: Resource, prefix: str = "") -> Tuple[str, Dict[str, Any]]:
    cmd, kwargs = get(resource, "x", prefix)

    labels: List[str] = []

    if prefix:
        prefix += "_"

    for key, value in resource.db_labels.items():
        labels.append(f"{key}: ${prefix}{key}")
        kwargs[f"{prefix}{key}"] = value

    cmd += f"SET x += {{ {', '.join(labels)} }} "

    return cmd, kwargs


def find(
    resource: Optional[Type[Resource]] = None,
    raw: bool = False,
    **kwargs: str,
) -> Generator[Resource, None, None]:
    labels = [f"{key}: ${key}" for key in kwargs.keys()]
    if resource is None or resource is Resource:
        cmd = f"MATCH (x {{ {', '.join(labels)} }}) "
    else:
        cmd = f"MATCH (x:{resource.__name__} {{ {', '.join(labels)} }}) "

    if raw:
        cmd += "WHERE EXISTS (x.raw) "

    cmd += "RETURN x"

    driver = get_driver()

    with driver.session() as session:
        logger.debug(f"Starting neo4j query: {cmd}, {kwargs}")
        results = session.run(cmd, kwargs)

        for result in results:
            result = result[0]
            props = result._properties
            logger.debug(
                f"Loading resource: {props['kind']} "
                f"{props.get('namespace', '')} {props['name']}",
            )

            if resource is None:
                res = Resource(**props)
            else:
                res = resource(**props)

            yield res


def find_or_mock(resource: Type[T], **kwargs: str) -> T:
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

    cluster = find_or_mock(Cluster, kind="Cluster")

    return cluster
