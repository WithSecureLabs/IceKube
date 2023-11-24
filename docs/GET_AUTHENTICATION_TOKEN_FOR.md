# GET_AUTHENTICATION_TOKEN_FOR

### Overview

This attack path aims to locate resources which can get a long-lived service account token for a given service account. Upon successful exploitation, an attacker will gain the permissions of the target service account.

### Description

Kubernetes secrets can contain long-lived tokens for service accounts. These are when the secret type is set to `kubernetes.io/service-account-token`. Should this be set, the `kubernetes.io/service-account.name` annotation determines which service account the token is created for by a Kubernetes controller with which the secret is automatically populated.

An attacker with read access to this secret would be able to use the token to perform actions against the API server as the service account.

### Defense

Long-lived service account tokens should be avoided in favour of short-lived tokens using the `TokenRequest` API. Should this not be possible, RBAC permissions should be reviewed to limit access to this permission to those required.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(secret:Secret)-[:AUTHENTICATION_TOKEN_FOR]->(dest:ServiceAccount)
```

Thee above query finds all resources (`src`) that have either the GET, LIST or WATCH permissions on a secret containing a token. The service account that the token is for is the target (`dest`).
