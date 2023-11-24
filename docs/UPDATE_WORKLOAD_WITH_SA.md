# UPDATE_WORKLOAD_WITH_SA

### Overview

This attack path aims to locate subjects which can update workloads in a namespace with the target service account. Upon successful exploitation, an attacker will gain the permissions of the target service account.

### Description

An attacker with the ability to update workloads could configure the service account associated with the resultant pod by setting the `serviceAccountName` field in the pod spec. Should the value specified match the name of a service account in the namespace the pod is deployed in, the token for that service account can be mounted into the pod. 

As the attacker has configured the workload, they would also have control of the image and the command executed. This could be configured to exfiltrate the token to the attacker. This could be by outputting it to `stdout` if the attacker has `pods/logs` permissions, or exfiltrating the token over the network, or some other means.

Once the attacker has acquired the token, they would be able to perform actions against the API server as the service account.

### Defense

RBAC permissions to update workloads should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_UPDATE|GRANTS_PATCH]->(workload)-[:WITHIN_NAMESPACE]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount)
WHERE (workload:ReplicationController OR workload:DaemonSet OR workload:Deployment OR workload:ReplicaSet OR workload:StatefulSet OR workload:CronJob OR workload:Job)
```

The above query finds all resources (`src`) that have the `PATCH` or `UPDATE` permission against workload resources types within a specified namespace. All `PATCH` or `UPDATE` verbs are against the namespace for a namespaced resource. The target node (`dest`) is a service account within the same namespace as where the workload creation is permitted.

Workload creation is used because various Kubernetes controllers create pods automatically from more abstract workload resources. Configuration of the workload resource also configures the created pod, thus it would allow an attacker to create the desired pod.

Workload creation includes the following:
- `replicationcontrollers`
- `daemonsets`
- `deployments`
- `replicasets`
- `statefulsets`
- `cornjobs`
- `jobs`
