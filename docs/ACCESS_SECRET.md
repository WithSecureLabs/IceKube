# ACCESS_SECRET

### Overview

This attack path locates subjects which can access a secret. An attacker could use this to gain access to sensitive information, such as credentials.

### Description

Kubernetes secrets typically contain sensitive information, and are a prime target for attackers. This attack path identifies subjects which have the ability to read a secret.

### Defense

RBAC permissions regarding reading secrets should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(dest:Secret)
```

The above query finds subjects (`src`) which have read permissions on a secret (`dest`).
