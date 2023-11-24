# MOUNTS_SECRET

### Overview

This attack path locates pods with mounted secrets. An attacker on a foothold on one of these pods would be able to access the values in the secret.

### Description

Kubernetes secrets typically contain sensitive information, and are a prime target for attackers. This attack path identifies pods which have this data mounted.

### Defense

Review which secrets are mounted into a pod, and ensure all secrets are required.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod)-[:MOUNTS_SECRET]->(dest:Secret)
```

The above query finds pods (`src`) which have secrets (`dest`) mounted.
