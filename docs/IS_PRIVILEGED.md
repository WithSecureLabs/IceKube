# IS_PRIVILEGED

### Overview

This attack path aims to locate pods which are privileged, and as such could breakout onto the underlying node.

### Description

Privileged pods run their containers without much of the segregation typical containers have. This makes it significantly easier for a container breakout to occur granting an attacker a foothold on the underlying node.

A number of techniques are available to breakout of a privileged pod. For example, mounting the underlying drives from `/dev/` and accessing the hosts filesystem.

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod {privileged: true})<-[:HOSTS_POD]-(dest:Node)
```

The query above finds pods (`src`) that have the `privileged` property set to true. This property is configured by IceKube and is retrieved from the pod spec. The node (`dest`) that hosts the pod is then targeted.
