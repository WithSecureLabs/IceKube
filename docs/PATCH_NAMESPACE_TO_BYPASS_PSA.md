# PATCH_NAMESPACE_TO_BYPASS_PSA

### Overview

This attack path aims to locate subjects that can both create workloads within a namespace that has Pod Security Admission (PSA) enforced, and the ability to modify the same namespace. This would allow the modification of the PSA policy, and therefore enable the deployment of insecure workloads as described in `CREATE_PRIVILEGED_WORKLOAD` gaining privileged access to nodes within the cluster.

### Description

While Namespace resources are cluster-wide, they are also considered a namespaced resource for certain actions against that particular namespace. This includes `get`, `patch`, `update` and `delete`. An entity with permissions constrained to solely to a namespace using a RoleBinding, could have permissions against the Namespace resource itself. Should this include `patch` or `update`, an attacker can modify the Namespace.

PSA is configured through labels on a namespace. These can be modified by an entity with `patch` or `update` permissions on the namespace. Therefore, an attacker with these permissions on the namespace could modify the PSA to allow all workloads to be deployed.

After such a modification is made, a privileged workload can be created within the namespace as described in `CREATE_PRIVILEGED_WORKLOAD`.

### Defense

Ensure permissions assigned to entities follow the principles of least privilege. Specifically, granting permissions on a namespace within a Role / RoleBinding should be avoided. Due care should be given when utilising wildcards in RBAC as this may inadvertently grant undesired permissions.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PODS_CREATE|{create_workload_query()}]->(ns:Namespace)-[:WITHIN_CLUSTER]->(cluster), (dest:Node) WHERE (src)-[:GRANTS_PATCH|GRANTS_UPDATE]->(ns) AND cluster.major_minor >= 1.25
```

The above query finds all entities (`src`) that have the CREATE permission against workload resource types within a specified namespace. All CREATE verbs are against the namespace for a namespaced resource. The target node (`dest`) is a node within the cluster.

The Cluster object is also retrieved to have access to the clusters Kubernetes version. Filters are performed to ensure the cluster version is greater than 1.25, where PSA moved to stable, and it is assumed that PSA is the sole enforcer of pod security within the cluster. 

The query also validates that the entity has the ability to `patch` or `update` the namespace. Should they have this permission, the specifics of which PSA are currently enforced on the namespace are irrelevant as the attacker can simply change it to a more favourable value.

Workload creation is used as opposed to solely pods because various Kubernetes controllers create pods automatically from more abstract workload resources. Configuration of the workload resource also configures the created pod, thus it would allow an attacker to create the desired pod.

Workload creation includes the following:
- `pods`
- `replicationcontrollers`
- `daemonsets`
- `deployments`
- `replicasets`
- `statefulsets`
- `cornjobs`
- `jobs`
