# CREATE_SECRET_WITH_TOKEN

### Overview

This attack aims to locate subjects which can gain access to a service account token by creating a secret which would be populated by the control plane with the relevant secret. The subject would also need a method to read the newly created secret.

### Description

Secrets can be configured with the type `kubernetes.io/service-account-token` and annotated with `kubernetes.io/service-account.name` which will result in the secret being automatically populated with a token for said service account.

An attacker could leverage this by creating a secret for a service account and use it to request a token for a service account they wish to gain access to. Once created, an attacker would need to read the secret. This could be done in a few different ways such as reading the secret directly or mounting it into a pod and using that to exfiltrate the secret.

### Defense

RBAC permissions regarding creating secrets should be reviewed. Access should be restricted where not needed.

### Cypher Deep-Dive

#### Listing secrets

```cypher
MATCH (src)-[:GRANTS_SECRETS_CREATE]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount) WHERE (src)-[:GRANTS_SECRETS_LIST]->(ns)

```

This query identifies subjects (`src`) that can create secrets within a namespace. It also checks whether the same subject can list secrets within the same namespace. This would allow them to read the secret upon creation.

#### Workload creation

```cypher
MATCH (src)-[:GRANTS_SECRETS_CREATE]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount) WHERE (src)-[:GRANTS_PODS_CREATE|GRANTS_REPLICATIONCONTROLLERS_CREATE|GRANTS_DAEMONSETS_CREATE|GRANTS_DEPLOYMENTS_CREATE|GRANTS_REPLICASETS_CREATE|GRANTS_STATEFULSETS_CREATE|GRANTS_CRONJOBS_CREATE|GRANTS_JOBS_CREATE]->(ns)
```

This query identifies subjects (`src`) that can create secrets within a namespace. It also checks the subject can create a workload within the same namespace which could be configured to mount the newly created secret for exfiltration purposes.

Workload creation includes the following:
- `pods`
- `replicationcontrollers`
- `daemonsets`
- `deployments`
- `replicasets`
- `statefulsets`
- `cornjobs`
- `jobs`
