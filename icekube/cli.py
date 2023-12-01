import json
import logging
from pathlib import Path
from typing import Iterator, List, Optional, cast

import typer
from icekube.config import config
from icekube.icekube import (
    create_indices,
    enumerate_resource_kind,
    generate_relationships,
    purge_neo4j,
    remove_attack_paths,
    setup_attack_paths,
)
from icekube.kube import (
    APIResource,
    Resource,
    all_resources,
    metadata_download,
)
from icekube.log_config import build_logger
from tqdm import tqdm

app = typer.Typer()

IGNORE_DEFAULT = "events,componentstatuses"


@app.command()
def run(
    ignore: str = typer.Option(
        IGNORE_DEFAULT,
        help="Names of resource types to ignore",
    ),
):
    enumerate(ignore)
    attack_path()


@app.command()
def enumerate(
    ignore: str = typer.Option(
        IGNORE_DEFAULT,
        help="Names of resource types to ignore",
    ),
):
    create_indices()
    enumerate_resource_kind(ignore.split(","))
    generate_relationships()


@app.command()
def relationships():
    generate_relationships()


@app.command()
def attack_path():
    remove_attack_paths()
    setup_attack_paths()


@app.command()
def purge():
    purge_neo4j()


@app.command()
def download(output_dir: str):
    path = Path(output_dir)
    path.mkdir(exist_ok=True)

    resources = all_resources()
    metadata = metadata_download()

    with open(path / "_metadata.json", "w") as fs:
        fs.write(json.dumps(metadata, indent=2, default=str))

    current_type = None
    current_group = []

    for resource in resources:
        if current_type is None:
            current_type = resource.resource_definition_name
        elif current_type != resource.resource_definition_name:
            with open(path / f"{current_type}.json", "w") as fs:
                fs.write(json.dumps(current_group, indent=4, default=str))
            current_group = []
            current_type = resource.resource_definition_name

        if resource.raw:
            current_group.append(json.loads(resource.raw))

    if current_type:
        with open(path / f"{current_type}.json", "w") as fs:
            fs.write(json.dumps(current_group, indent=4, default=str))


@app.command()
def load(input_dir: str, attack_paths: bool = True):
    path = Path(input_dir)
    metadata = json.load(open(path / "_metadata.json"))

    from icekube import kube
    from icekube import icekube

    kube.kube_version = lambda: cast(str, metadata["kube_version"])
    kube.context_name = lambda: cast(str, metadata["context_name"])
    kube.api_versions = lambda: cast(List[str], metadata["api_versions"])
    kube.preferred_versions = metadata["preferred_versions"]
    kube.api_resources = lambda: cast(
        List[APIResource],
        [APIResource(**x) for x in metadata["api_resources"]],
    )

    icekube.api_resources = kube.api_resources
    icekube.context_name = kube.context_name
    icekube.kube_version = kube.kube_version

    def all_resources(
        preferred_versions_only: bool = True,
        ignore: Optional[List[str]] = None,
    ) -> Iterator[Resource]:
        print("Loading files from disk")

        for file in tqdm(path.glob("*")):
            if file.name == "_metadata.json":
                continue
            try:
                # If downloaded via kubectl get -A
                data = json.load(open(file))["items"]
            except TypeError:
                # If downloaded via icekube download
                data = json.load(open(file))

            for resource in data:
                yield Resource(
                    apiVersion=resource["apiVersion"],
                    kind=resource["kind"],
                    name=resource["metadata"]["name"],
                    namespace=resource["metadata"].get("namespace"),
                    plural=file.name.split(".")[0],
                    raw=json.dumps(resource, default=str),
                )
        print("")

    kube.all_resources = all_resources
    icekube.all_resources = all_resources

    if attack_paths:
        run(IGNORE_DEFAULT)
    else:
        enumerate(IGNORE_DEFAULT)


@app.callback()
def callback(
    neo4j_url: str = typer.Option("bolt://localhost:7687", show_default=True),
    neo4j_user: str = typer.Option("neo4j", show_default=True),
    neo4j_password: str = typer.Option("neo4j", show_default=True),
    neo4j_encrypted: bool = typer.Option(False, show_default=True),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True),
):
    config["neo4j"]["url"] = neo4j_url
    config["neo4j"]["username"] = neo4j_user
    config["neo4j"]["password"] = neo4j_password
    config["neo4j"]["encrypted"] = neo4j_encrypted

    verbosity_levels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    build_logger(verbosity_levels[verbose])
