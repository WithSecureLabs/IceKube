# CREATE_PRIVILEGED_WORKLOAD

### Overview

This attack path aims to locate subjects that can create workloads that can be considered `privileged`. These are workloads deliberately configured with known weaknesses in their pod specification that could allow for a container breakout. Upon successful execution, an attacker would gain potentially privileged access to nodes they can deploy workloads upon.

### Description

An attacker with the ability to create a pod could configure the pod to have attributes that would align with the `privileged` Pod Security Standard (PSS). These include configurations that allow for a breakout, for example the `privileged` flag, or access to the host filesystem.

As they are creating the pod themselves, they would also be able to configure the process to run as root and set a custom malicious command to allow code execution on the host as the root user gaining privileged access. This assumes user namespaces are not in effect.

### Defense

PSS should be enforced within the cluster. This could be done through Pod Security Admission (PSA) through labels on the namespace. Should more granularity be required, a validating admission webhook could be used as an alternative.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PODS_CREATE|{create_workload_query()}]->(ns:Namespace)-[:WITHIN_CLUSTER]->(cluster), (dest:Node) WHERE cluster.major_minor >= 1.25 AND (ns.psa_enforce <> 'restricted' AND ns.psa_enforce <> 'baseline')
```

The above query finds all entities (`src`) that have the CREATE permission against workload resource types within a specified namespace. All CREATE verbs are against the namespace for a namespaced resource. The target node (`dest`) is a node within the cluster.

The Cluster object is also retrieved to have access to the clusters Kubernetes version. Filters are performed to ensure the cluster version is greater than 1.25, where PSA moved to stable, and it is assumed that PSA is the sole enforcer of pod security within the cluster. The query then validates that the namespace does not enforce the `restricted` or `baseline` standards. This leaves `privileged` or blank both of which do not specify any restrictions on a pod specification. IceKube retrieves this configuration from the `pod-security.kubernetes.io/enforce` label of the namespace.

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
