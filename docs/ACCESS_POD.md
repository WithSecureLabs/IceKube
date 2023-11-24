# ACCESS_POD

### Overview

This rule establishes an attack path between a node and pods hosted upon it. This allows IceKube to consider accessible pods should an attacker break out onto a node.

### Description

An attacker with access to a node can access all pods running on the node.

### Defense

N/A

### Cypher Deep-Dive

```cypher
MATCH (src:Node)-[:HOSTS_POD]->(dest:Pod)
```

The above query finds nodes (`src`) hosting pods (`dest`) through the `HOSTS_POD` relationship.
