# GRANTS_PERMISSION

### Overview

This rule establishes an attack path relationship between a role binding and its role. This allows IceKube to consider role permissions for the associated role binding and, by extension, its subjects.

### Description

Role bindings bind a number of subjects with a role. The permissions granted to the subjects will be that of the bound role. If both the role binding and role are scoped cluster-wide, the permissions are also granted cluster-wide.

### Defense

Review associated roles for a role binding, and ensure roles that grant the minimal set of permissions required are attached.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PERMISSION]->(dest)
```

Finds all resources (`src`) that have a `GRANTS_PERMISSION` relationship to other resources (`dest`). The `GRANTS_PERMISSION` relationship is only between role binding and roles, thereby limiting `src` to `RoleBinding` or `ClusterRoleBinding` and `dest` to `Role` or `ClusterRole`.
