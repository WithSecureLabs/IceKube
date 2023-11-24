# USES_ACCOUNT

### Overview

This attack path aims to locate pods which mount a service account token. Upon compromise of a pod, an attacker would gain access to the token allowing them to perform actions as the associated service account.

### Description

An attacker which gained access to a pod which uses a service account could leverage the service account's permissions, thus furthering themselves within the cluster.

Pods are associated with service account. Should the service account token be mounted, it can typically be found at `/var/run/secrets/kubernetes.io/serviceaccount/token`. Upon compromise, an attacker can access the token and use it to communicate with the API server. This would allow them to perform actions as the service account. 

### Defense

Service account tokens should only be mounted into a pod should it be required. By default, the tokens are mounted in so this needs to be explicitly disabled. This can be done by setting `automountServiceAccountToken` to `false` in the pod spec, or within the service account. Examples for both can be seen below:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
automountServiceAccountToken: false
...
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  automountServiceAccountToken: false
  ...
```

### Cypher Deep-Dive

```
MATCH (src:Pod)-[:USES_ACCOUNT]->(dest:ServiceAccount)
```

The above query finds all `Pod` resources (`src`) and finds the configured `ServiceAccount` node (`dest`) by means of the `USE_ACCOUNT` relationship.
