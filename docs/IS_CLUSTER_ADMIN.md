# IS_CLUSTER_ADMIN

### Overview

This attack path aims to provide a route for nodes that are expected to grant cluster administrator access just due to the nature of the resource. 

### Description

Compromise of certain resources within a cluster can be considered to grant cluster administrator due to the nature of the resource compromised.

For example, compromise of a control plane node within a Kubernetes cluster that runs services such as the API server or etcd effectively grants cluster administrator access.

### Defense

Security of resources that are effectively cluster administrator should be reviewed and hardened.

### Cypher Deep-Dive

```cypher
MATCH (src:Node), (dest:ClusterRoleBinding)-[:GRANTS_PERMISSION]->(:ClusterRole {name: "cluster-admin"}) WHERE any(x in ["master", "control-plane"] WHERE x in src.node_roles)
```

The above query finds nodes `src` that have the `master` or `control-plane` role. The destination is set to a cluster role binding that binds to `cluster-admin`.
