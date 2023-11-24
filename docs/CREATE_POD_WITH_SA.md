# CREATE_POD_WITH_SA

### Overview

This attack path aims to locate subjects which can create pods in a namespace with the target service account. Upon successful exploitation, an attacker will gain the permissions of the target service account.

### Description

An attacker with the ability to create a pod could configure the service account associated with the pod by setting the `serviceAccountName` field in the pod spec. Should the value specified match the name of a service account in the namespace the pod is deployed in, the token for that service account can be mounted into the pod. 

As the attacker has created the pod, they would also have control of the image and the command executed. This could be configured to exfiltrate the token to the attacker. This could be by outputting it to `stdout` if the attacker has `pods/logs` permissions, or exfiltrating the token over the network, or some other means.

Once the attacker has acquired the token, they would be able to perform actions against the API server as the service account.

### Defense

RBAC permissions to create pods and workloads should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PODS_CREATE|GRANTS_REPLICATIONCONTROLLERS_CREATE|GRANTS_DAEMONSETS_CREATE|GRANTS_DEPLOYMENTS_CREATE|GRANTS_REPLICASETS_CREATE|GRANTS_STATEFULSETS_CREATE|GRANTS_CRONJOBS_CREATE|GRANTS_JOBS_CREATE]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount)
```

The above query finds all resources (`src`) that have the `CREATE` permission against workload resources types within a specified namespace. All `CREATE` verbs are against the namespace for a namespaced resource. The target node (`dest`) is a service account within the same namespace as where the workload creation is permitted.

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
