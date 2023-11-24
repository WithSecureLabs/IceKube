import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import List, Optional

from icekube.attack_paths import attack_paths
from icekube.kube import (
    all_resources,
    api_resources,
    context_name,
    kube_version,
)
from icekube.models import Cluster, Signer
from icekube.models.base import Resource
from icekube.neo4j import create, find, get, get_driver
from neo4j import BoltDriver
from tqdm import tqdm

logger = logging.getLogger(__name__)


def create_indices():
    for resource in api_resources():
        if "list" not in resource.verbs:
            continue

        kind = resource.kind
        namespace = resource.namespaced

        cmd = f"CREATE INDEX {kind.lower()} IF NOT EXISTS "
        cmd += f"FOR (n:{kind}) ON (n.name"
        if namespace:
            cmd += ", n.namespace"
        cmd += ")"

        with get_driver().session() as session:
            session.run(cmd)


def enumerate_resource_kind(
    ignore: Optional[List[str]] = None,
) -> List[Resource]:
    if ignore is None:
        ignore = []

    resources: List[Resource] = []

    with get_driver().session() as session:
        cluster = Cluster(name=context_name(), version=kube_version())
        cmd, kwargs = create(cluster)
        session.run(cmd, **kwargs)

        signers = [
            "kubernetes.io/kube-apiserver-client",
            "kubernetes.io/kube-apiserver-client-kubelet",
            "kubernetes.io/kubelet-serving",
            "kubernetes.io/legacy-unknown",
        ]
        for signer in signers:
            s = Signer(name=signer)
            cmd, kwargs = create(s)
            session.run(cmd, **kwargs)

        for resource in all_resources(ignore=ignore):
            resources.append(resource)
            cmd, kwargs = create(resource)
            session.run(cmd, **kwargs)

    return resources


def relationship_generator(
    driver: BoltDriver,
    initial: bool,
    resource: Resource,
):
    with driver.session() as session:
        logger.info(f"Generating relationships for {resource}")
        for source, relationship, target in resource.relationships(initial):
            if isinstance(source, Resource):
                src_cmd, src_kwargs = get(source, prefix="src")
            else:
                src_cmd = source[0].format(prefix="src")
                src_kwargs = {f"src_{key}": value for key, value in source[1].items()}

            if isinstance(target, Resource):
                dst_cmd, dst_kwargs = get(target, prefix="dst")
            else:
                dst_cmd = target[0].format(prefix="dst")
                dst_kwargs = {f"dst_{key}": value for key, value in target[1].items()}

            cmd = src_cmd + "WITH src " + dst_cmd

            if isinstance(relationship, str):
                relationship = [relationship]
            cmd += "".join(f"MERGE (src)-[:{x}]->(dst) " for x in relationship)

            kwargs = {**src_kwargs, **dst_kwargs}
            logger.debug(f"Starting neo4j query: {cmd}, {kwargs}")
            session.run(cmd, kwargs)


def generate_relationships(threaded: bool = False) -> None:
    logger.info("Generating relationships")
    logger.info("Fetching resources from neo4j")
    driver = get_driver()
    resources = find()
    logger.info("Fetched resources from neo4j")
    generator = partial(relationship_generator, driver, True)

    if threaded:
        with ThreadPoolExecutor() as exc:
            exc.map(generator, resources)
    else:
        print("First pass for relationships")
        for resource in tqdm(resources):
            generator(resource)
        print("")

    # Do a second loop across relationships to handle objects created as part
    # of other relationships

    resources = find()
    generator = partial(relationship_generator, driver, False)

    if threaded:
        with ThreadPoolExecutor() as exc:
            exc.map(generator, resources)
    else:
        print("Second pass for relationships")
        for resource in tqdm(resources):
            generator(resource)
        print("")


def remove_attack_paths() -> None:
    with get_driver().session() as session:
        session.run("MATCH ()-[r]-() WHERE EXISTS (r.attack_path) DELETE r")


def setup_attack_paths() -> None:
    print("Generating attack paths")
    for relationship, query in tqdm(attack_paths.items()):
        with get_driver().session() as session:
            if isinstance(query, str):
                query = [query]
            for q in query:
                cmd = q + f" MERGE (src)-[:{relationship} {{ attack_path: 1 }}]->(dest)"

                session.run(cmd)
    print("")


def purge_neo4j() -> None:
    with get_driver().session() as session:
        session.run("MATCH (x)-[r]-(y) DELETE x, r, y")
        session.run("MATCH (x) DELETE x")
