# IceKube

<p align="center">
  <img src="./docs/logo.png" width="400" />
</p>

IceKube is a tool to help find attack paths within a Kubernetes cluster from a low privileged point, to a preferred location, typically `cluster-admin`

## Setup

* `docker-compose up -d` - Spins up neo4j, accessible at `http://localhost:7474/`
* `poetry install --no-dev` (creates venv) *OR* `pip install --user .` (installs the CLI globally)
* Make sure your `kubectl` current context is set to the target cluster, and has `cluster-admin` privileges

## Permissions Required

This requires elevated privileges within the target cluster to enumerate resources. This typically requires read-only access on all resources within the cluster including secrets. IceKube does not persist any secret data it retrieves from secrets if that is a concern. 

Resource types can also be filtered from IceKube, instructions can be found below in the `Filtering Resources` section.

## Usage

* `icekube enumerate` - Will enumerate all resources, and saves them into `neo4j` with generic relationships generated (note: not attack path relationships)
* `icekube attack-path` - Generates attack path relationships within `neo4j`, these are identified with relationships having the property `attack_path` which is set to `1`
* `icekube run` - Does both `enumerate` and `attack-path`, this will be the main option for quickly running IceKube against a cluster
* `icekube purge` - Removes everything from the `neo4j` database
* Run cypher queries within `neo4j` to discover attack paths and roam around the data, attack relationships will have the property `attack_path: 1`

**NOTE**: In the `neo4j` browser, make sure to disable `Connect result nodes` in the Settings tab on the bottom left. This will stop it rendering every possible relationship automatically between nodes, leaving just the path queried for

#### Filtering Resources

It is possible to filter out specific resource types from enumeration. This can be done with the `--ignore` parameter to `enumerate` and `run` which takes the resource types comma-delimtied. For example, if you wish to exclude events and componentstatuses, you could run `icekube run --ignore events,componentstatuses` (NOTE: this is the default)

Sensitive data from secrets are not stored in IceKube, data retrieved from the Secret resource type have their data fields deleted on ingestion. It is recommended to include secrets as part of the query if possible as IceKube can still analyse the secret type and relevant annotations to aid with attack path generation. 

## Not sure where to start?

Here is a quick introductory way on running IceKube for those new to the project:

* `poetry install` - Installs dependancies using `poetry`
* `poetry shell` - Create a shell within the python environment
* `docker-compose up -d` - Creates the neo4j docker container with easy to use network and environment settings (give this a minute for `neo4j` to start up)
* `icekube run` - Analyse a cluster using IceKube - this assumes your `kubectl` context is set appropriately to target a cluster
* Open the neo4j browser at `http://localhost:7474/`
* On the login form, simply click `Connect` - wait for the connection to be established
* Click the cog wheel on the bottom left to open settings
* Near the bottom of the new side-pane, de-select `Connect result nodes`
* Enter the following query into the query bar at the top
    * `MATCH p = shortestPath((src)-[*]->(cr:ClusterRole {name: 'cluster-admin'})) WHERE ALL (r in relationships(p) WHERE EXISTS (r.attack_path)) AND (src:ServiceAccount OR src:Pod or src:User or src:Group) AND all(n in [[x in nodes(p)][-2]] WHERE (n:ClusterRoleBinding)-[:GRANTS_PERMISSION]->(cr)) RETURN p`
    * This will find routes to cluster administrator from service accounts, pods, users, or groups
* Of the new window made with the query, click the Fullscreen button
* Roam around the graph generated, clicking on nodes or relationships to get more details on the right where wanted

## Example Cypher Queries

The following will find the shortest path from a Pod within the namespace `starting` to the ClusterRole `cluster-admin` using `attack_path` relationships

```cypher
MATCH p = shortestPath((src:Pod {namespace: 'starting'})-[*]->(dest:ClusterRole {name: 'cluster-admin'})) WHERE ALL (r in relationships(p) WHERE EXISTS (r.attack_path)) RETURN p
```

Same thing, but gives additional data on the Namespace a resource is within

```cypher
MATCH p = shortestPath((src:Pod {namespace: 'starting'})-[*]->(dest:ClusterRole {name: 'cluster-admin'})) WHERE ALL (r in relationships(p) WHERE EXISTS (r.attack_path)) UNWIND nodes(p) AS n MATCH (n)-[r:WITHIN_NAMESPACE]->(ns:Namespace) RETURN p, ns, r
```

Finds all Pods / ServiceAccounts / Users / Groups that have access to the ClusterRole `cluster-admin` through a ClusterRoleBinding to ensure it has a cluster wide scope

```cypher
MATCH p = shortestPath((src)-[*]->(cr:ClusterRole {name: 'cluster-admin'})) WHERE ALL (r in relationships(p) WHERE EXISTS (r.attack_path)) AND (src:ServiceAccount OR src:Pod or src:User or src:Group) AND all(n in [[x in nodes(p)][-2]] WHERE (n:ClusterRoleBinding)-[:GRANTS_PERMISSION]->(cr)) RETURN p
```

Finds any node that can get to the ClusterRole `cluster-admin` through a ClusterRoleBinding to ensure it has a cluster wide scope

```cypher
MATCH p1=((crb:ClusterRoleBinding)-[:GRANTS_PERMISSION]->(cr:ClusterRole {name: 'cluster-admin'})), p = shortestPath((src)-[*]->(crb)) WHERE ALL (r in relationships(p) WHERE r.attack_path = 1) AND (src <> crb) RETURN p, p1
```

## Acknowledgements

- [BloodHound](https://github.com/BloodHoundAD/BloodHound) - The original project showing the power of graph databases for security
- [KubeHound](https://github.com/DataDog/KubeHound) - An excellent and similar tool by DataDog, clearly we had similar ideas!
