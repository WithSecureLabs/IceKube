# EXEC_INTO

### Overview

This attack path aims to locate subjects which can execute into pods. An attacker could use this to gain a foothold in a running pod.

### Description

An attacker with the ability to execute commands within a pod could gain access to the data within. This would include access to its processes, filesystem, network position, etc. This could be used as a foothold for further attacks within the cluster.

Executing commands in a pod requires two permissions. The first is `create` on `pods/exec` and the second is `get` on `pods`. Both of those permissions should affect the target pod.

### Defense

RBAC permissions regarding the outlined permissions should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_EXEC_CREATE]->(dest:Pod)<-[:GRANTS_GET]-(src)
```

The above query finds all resources (`src`) that have `GRANTS_EXEC_CREATE` and `GRANTS_GET` on a Pod (`dest`). The two relationships map to the two required permissions for executing commands within a pod.
