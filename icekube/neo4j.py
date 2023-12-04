from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, TypeVar

from icekube.config import config
from icekube.models import BaseResource, Resource
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
    database: Optional[str] = "neo4j",
) -> BoltDriver:
    neo4j_config = config.get("neo4j", {})
    uri = neo4j_config.get("url", uri)
    auth = (
        neo4j_config.get("username", auth[0]),
        neo4j_config.get("password", auth[1]),
    )
    encrypted = neo4j_config.get("encrypted", encrypted)
    database = neo4j_config.get("database", database)

    return GraphDatabase.driver(uri, auth=auth, encrypted=encrypted, database=database)


def create_index(kind: str, namespace: bool) -> None:
    cmd = f"CREATE INDEX {kind.lower()} FOR (n:{kind}) ON (n.name"
    if namespace:
        cmd += ", n.namespace"
    cmd += ")"

    driver = get_driver()

    with driver.session() as session:
        session.run(cmd)


def get(
    resource: BaseResource,
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

    # For ObjectReferences and SecretReferences, we need to use the core kind to keep track
    # of the resource rather than rely on using `kind` to reconstruct the object.
    kind = resource.corekind if hasattr(resource, "corekind") and resource.corekind is not None else resource.kind
    cmd = f"MERGE ({identifier}:{kind} {{ {', '.join(labels)} }}) "

    return cmd, kwargs


def create(resource: BaseResource, prefix: str = "") -> Tuple[str, Dict[str, Any]]:
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
    resource: Optional[Type[BaseResource]] = None,
    raw: bool = False,
    **kwargs: str,
) -> Generator[BaseResource, None, None]:
    labels = [f"{key}: ${key}" for key in kwargs.keys()]
    if resource is None or resource is BaseResource:
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

            if len(result.labels) > 0:
                corekind, *_ = result.labels
            else:
                logger.warn(f"Result empty for type: {resource}")
                continue

            logger.debug(
                f"Loading resource: {corekind} "
                f"{props.get('namespace', '')} {props.get('name', '')}",
            )

            if resource is None and "raw" not in props:
                res = BaseResource(**props)
            elif "raw" in props:
                res = Resource(**props)
            elif resource is not None:
                res = resource(**props)
            else:
                continue

            if hasattr(res, "corekind"):
                res.corekind = corekind

            yield res

