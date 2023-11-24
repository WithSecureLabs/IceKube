# CAN_EXEC_THROUGH_KUBELET

### Overview

This attack path aims to locate subjects which can execute commands on pods directly through the kubelet. This could allow an attacker to get a foothold on that pod.

### Description

The kubelet runs its own API with its own set of access controls. Authorisation for these endpoints are based on allowed verbs to sub resources on the `nodes` resource. For example, a GET request to `/stats/*` requires the `get` verb on `nodes/stats`. Tables showing the required request verb and sub resource for a particular endpoint can be found in the [Kubernetes documentation](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/#kubelet-authorization)
The `/exec` path allows for the execution of commands in containers. This path is authorised by the `nodes/proxy` sub resource and the required verb is create.

An attacker with create on `nodes/proxy` for a particular node can execute commands on containers running on that node. Potentially gaining a foothold within those containers.

### Defense

RBAC permissions regarding the `nodes/proxy`sub resource should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PROXY_CREATE]->(:Node)-[:HOSTS_POD]->(dest:Pod)
```

The above query finds subjects (`src`) with the create permission on the `nodes/proxy` sub resource. The target is set as pods (`dest`) running on that particular node determined through the `HOSTS_POD` relationship.
