# DEBUG_POD

### Overview

This attack path aims to locate subjects which can create debug containers within a pod. An attacker could use this to gain a foothold within a pod.

### Description

An attacker with permissions to debug a pod can contain a new container in the pod. This could also be configured to share the process namespace of an existing container in the pod. An attacker could use this to gain access to the containers filesystem, including service account tokens, as well as its network stack. 

The ability to debug a pod requires the `patch` verb on `pods/ephemeral` for the targeted pod.

### Defense

RBAC permissions regarding the `patch` permission on the `pods/ephemeral` sub resource should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_EPHEMERAL_PATCH]->(dest:Pod)
```
Finds all resources (`src`) that have a `GRANTS_EPHEMERAL_PATCH` relationship to pods (`dest`).
