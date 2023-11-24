# RBAC_ESCALATE_TO

### Overview

This attack path aims to locate subjects which can escalate their privileges within the cluster by modifying bound roles.

### Description

By default, a subject is unable to grant more permissions in RBAC than they originally have access to. The `escalate` verb is a special verb that bypasses this restriction. It permits the modification of roles to add more permissions than the editor may have.

This could be used by an attacker to modify a role that grants them permissions to include 

### Defense

RBAC permissions regarding the `escalate` permission on roles should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

#### RoleBindings

```cypher
MATCH (src:RoleBinding)-[:GRANTS_ESCALATE]->(role)-[:WITHIN_NAMESPACE]->(:Namespace)<-[:WITHIN_NAMESPACE]-(dest)
WHERE (role:Role OR role:ClusterRole) AND (src)-[:GRANTS_PERMISSION]->(role)
```

The above query finds role bindings (`src`) that has escalate permissions on a role. The role can either be a `Role` or a `ClusterRole`. The role binding must also be bound to the role with through the `GRANTS_PERMISSION` relationship. Finally, the namespace for the role is retrieved, and all resources within that namespace are targeted (`dest`). 

#### ClusterRoleBindings

```cypher
MATCH (src:ClusterRoleBinding)-[:GRANTS_ESCALATE]->(role:ClusterRole), (dest)
WHERE (src)-[:GRANTS_PERMISSION]->(role)
```

The above query finds cluster role bindings (`src`) that has escalate permissions on a cluster role. The role binding must also be bound to the role with through the `GRANTS_PERMISSION` relationship. Finally, all resources within the database are targeted (`dest`).
