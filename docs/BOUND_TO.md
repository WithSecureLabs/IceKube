# BOUND_TO

### Overview

This rule establishes an attack path relationship between a role binding and its subjects. This allows IceKube to consider permissions associated with the role binding for required subjects.

### Description

Role bindings bind a number of subjects with a role. The permissions granted to the subjects will be that of the bound role. If both the role binding and role are scoped cluster-wide, the permissions are also granted cluster-wide.

### Defense

Review subjects in role bindings, and ensure subjects are only bound to roles that grant the minimal set of permissions required for use.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:BOUND_TO]->(dest)
```

Finds all resources (`src`) that have a `BOUND_TO` relationship to other resources (`dest`). The `BOUND_TO` relationship is only between role binding and subject, thereby limiting `dest` to `RoleBinding` or `ClusterRoleBinding` and `src` to one of `Group`, `User`, `ServiceAccount`.
