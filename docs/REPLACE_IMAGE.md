# REPLACE_IMAGE

### Overview

This attack path aims to locate subjects which have the ability to modify pods. An attacker can use this to replace a pod image, which could be used to inject malicious code that could be used to gain a foothold within the pod.

### Description

An attacker with permissions to patch a pod could replace the pod's image with a malicious one. This malicious image could include code that could aid an attacker in getting a foothold within the pod. For example, it may connect to an attacker-controlled server with a reverse shell.

### Defense

RBAC permissions regarding the patch permission should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PATCH]->(dest:Pod)
 ```

Finds all resources (`src`) that have a `GRANTS_PATCH` relationship to pods (`dest`).
