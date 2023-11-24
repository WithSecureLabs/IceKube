# CAN_IMPERSONATE

### Overview

This attack path aims to locate subjects which have the impersonate permission, allowing them to impersonate other subjects.

### Description

Should a subject have the `impersonate` verb on another subject, they can perform requests against the API server specifying the other subject as an impersonation target. The actions performed are then performed as if the original subject was the targeted subject. This could be done with the `--as` flag to `kubectl`.

An attacker could use this to laterally move within the cluster to other subjects. 

### Defense

RBAC permissions regarding the impersonate verb should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_IMPERSONATE]->(dest)
```

The above query finds all resources (`src`) that have the impersonate verb on a target resource (`dest`)
