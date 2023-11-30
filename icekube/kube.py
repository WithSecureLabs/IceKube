import logging
from collections.abc import Iterator
from typing import Any, Dict, List, Optional, cast

from icekube.models import APIResource, Resource
from kubernetes import client, config
from tqdm import tqdm

logger = logging.getLogger(__name__)

loaded_kube_config = False
api_resources_cache: Optional[List[APIResource]] = None
preferred_versions: Dict[str, str] = {}


def load_kube_config():
    global loaded_kube_config

    if not loaded_kube_config:
        config.load_kube_config()
        loaded_kube_config = True


def kube_version() -> str:
    load_kube_config()
    return cast(str, client.VersionApi().get_code().git_version)


def context_name() -> str:
    load_kube_config()
    return cast(str, config.list_kube_config_contexts()[1]["context"]["cluster"])


def api_versions() -> List[str]:
    load_kube_config()
    versions = []

    for version in client.CoreApi().get_api_versions().versions:
        versions.append(f"{version}")

    for api in client.ApisApi().get_api_versions().groups:
        preferred_versions[api.name] = api.preferred_version.version
        for v in api.versions:
            versions.append(f"{api.name}/{v.version}")

    return sorted(versions)


def api_resources() -> List[APIResource]:
    global api_resources_cache
    load_kube_config()

    if api_resources_cache is not None:
        return api_resources_cache

    try:
        versions = api_versions()
    except Exception:
        logger.error("Failed to access Kubernetes cluster")
        api_resources_cache = []
        return api_resources_cache

    resources: List[APIResource] = []

    for version in versions:
        if "/" in version:
            group, vers = version.split("/")
            resp = client.CustomObjectsApi().list_cluster_custom_object(
                group,
                vers,
                "",
            )
            preferred = preferred_versions[group] == vers
        else:
            resp = client.CoreV1Api().get_api_resources()
            preferred = True
            resp = resp.to_dict()
        for item in resp["resources"]:
            # if "/" in item["name"]:
            #     continue
            # if not any(x in item["verbs"] for x in ["get", "list"]):
            #     continue

            additional_verbs = {
                "roles": ["bind", "escalate"],
                "clusterroles": ["bind", "escalate"],
                "serviceaccounts": ["impersonate"],
                "users": ["impersonate"],
                "groups": ["impersonate"],
            }

            if item["name"] in additional_verbs.keys():
                item["verbs"] = list(
                    set(item["verbs"] + additional_verbs[item["name"]]),
                )

            resources.append(
                APIResource(
                    name=item["name"],
                    namespaced=item["namespaced"],
                    group=version,
                    kind=item["kind"],
                    preferred=preferred,
                    verbs=item["verbs"],
                ),
            )

    if not any(x.name == "users" for x in resources):
        resources.append(
            APIResource(
                name="users",
                namespaced=False,
                group="",
                kind="User",
                preferred=True,
                verbs=["impersonate"],
            ),
        )

    if not any(x.name == "groups" for x in resources):
        resources.append(
            APIResource(
                name="groups",
                namespaced=False,
                group="",
                kind="Group",
                preferred=True,
                verbs=["impersonate"],
            ),
        )

    if not any(x.name == "signers" for x in resources):
        resources.append(
            APIResource(
                name="signers",
                namespaced=False,
                group="certificates.k8s.io/v1",
                kind="Signer",
                preferred=True,
                verbs=["approve", "sign"],
            )
        )

    api_resources_cache = resources
    return resources


def all_resources(
    preferred_versions_only: bool = True,
    ignore: Optional[List[str]] = None,
) -> Iterator[Resource]:
    load_kube_config()

    if ignore is None:
        ignore = []

    all_namespaces: List[str] = [
        x.metadata.name for x in client.CoreV1Api().list_namespace().items
    ]

    print("Enumerating Kubernetes resources")
    for resource_kind in tqdm(api_resources()):
        if "list" not in resource_kind.verbs:
            continue

        if preferred_versions_only and not resource_kind.preferred:
            continue

        if resource_kind.name in ignore:
            continue

        logger.info(f"Fetching {resource_kind.name} resources")
        try:
            resource_class = Resource.get_kind_class(
                resource_kind.group,
                resource_kind.kind,
            )
            if resource_kind.namespaced:
                for ns in all_namespaces:
                    yield from resource_class.list(
                        resource_kind.group,
                        resource_kind.kind,
                        resource_kind.name,
                        ns,
                    )
            else:
                yield from resource_class.list(
                    resource_kind.group,
                    resource_kind.kind,
                    resource_kind.name,
                )
        except client.exceptions.ApiException:
            logger.error(f"Failed to retrieve {resource_kind.name}")
    print("")


def metadata_download() -> Dict[str, Any]:
    return {
        "kube_version": kube_version(),
        "context_name": context_name(),
        "api_versions": api_versions(),
        "preferred_versions": preferred_versions,
        "api_resources": [x.dict() for x in api_resources()],
    }
