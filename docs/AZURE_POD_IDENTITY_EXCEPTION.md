# AZURE_POD_IDENTITY_EXCEPTION

### Overview

This attack path aims to locate subjects which can access the cluster's Azure managed identity, allowing them to retrieve cluster administrator credentials in cases where Kubernetes local accounts are enabled.

### Description

`AzurePodIdentityException` creates exceptions for pods to remove IPTables filtering for their access to Instance Metadata Service (IMDS). If a pod is exempt from this filtering, they can communicate with IMDS to retrieve the clusters Node Managed Identity (NMI) and authenticate as it. Once authenticated, this can be used to gain cluster administrator access in clusters where Kubernetes local accounts are enabled.

An attacker has multiple avenues that could leverage `AzurePodIdentityException`. The first would be reviewing the pod labels from an existing `AzurePodIdentityException`, and creating or modifying workloads to meet those criteria within the same namespace. The resultant pods would have access to IMDS, and could contain malicious code based of the pod configuration that allows an attacker to gain a foothold within to leverage the access.

Another option would be to create a new `AzurePodIdentityException` within the same namespace of a compromised pod. This exception would need to specify the labels of the compromised workload. This would remove any filtering from the workload, allowing it to once again access IMDS.

### Defense

RBAC permissions regarding `AzurePodIdentityExceptions` should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive


#### Create workload based of existing APIE

```cypher
MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(azexc:AzurePodIdentityException)-[:WITHIN_NAMESPACE]->(ns:Namespace), (dest:ClusterRoleBinding)
WHERE (dest.name = 'aks-cluster-admin-binding' OR dest.name = 'aks-cluster-admin-binding-aad') AND (EXISTS {
  MATCH (src)-[:GRANTS_REPLICATIONCONTROLLERS_CREATE|GRANTS_DAEMONSETS_CREATE|GRANTS_DEPLOYMENTS_CREATE|GRANTS_REPLICASETS_CREATE|GRANTS_STATEFULSETS_CREATE|GRANTS_CRONJOBS_CREATE|GRANTS_JOBS_CREATE|GRANTS_POD_CREATE]->(ns)
} OR EXISTS {
  MATCH (src)-[:GRANTS_PATCH|GRANTS_UPDATE]->(workload)-[:WITHIN_NAMESPACE]->(ns)
  WHERE (workload:ReplicationController OR workload:DaemonSet OR workload:Deployment OR workload:ReplicaSet OR workload:StatefulSet OR workload:CronJob OR workload:Job)
})
```

The above query finds subjects (`src`) which can view the `AzurePodIdentityException` configuration. It then checks that same subject can create or update workloads in the same namespace as the `AzurePodIdentityException`. The target is set as the default AKS cluster admin role bindings.


#### Create APIE based of existing workload

```cypher
MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(pod:Pod)-[:WITHIN_NAMESPACE]->(ns:Namespace), (src)-[r {
  attack_path: 1
}]->(pod), (dest:ClusterRoleBinding)
WHERE (dest.name='aks-cluster-admin-binding' OR dest.name='aks-cluster-admin-binding-aad') AND (EXISTS {
  (src)-[:GRANTS_AZUREPODIDENTITYEXCEPTIONS_CREATE]->(ns)
} OR EXISTS {
  (src)-[:GRANTS_UPDATE|GRANTS_PATCH]->(:AzurePodIdentityException)-[:WITHIN_NAMESPACE]->(ns)
})
```

The above query finds subjects (`src`) which can get pods, and have an attack path to that pod. It then ensures the subject can create or update `AzurePodIdentityException` within the same namespace. The target is set as the default AKS cluster admin cluster role bindings.
