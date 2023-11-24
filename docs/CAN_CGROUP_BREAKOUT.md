# CAN_CGROUP_BREAKOUT

### Overview

This attack path aims to locate pods which have the `SYS_ADMIN` capability, and as such can breakout onto the underlying node.

### Description

The `SYS_ADMIN` capability provides the ability to perform a wide range of administrator operations. One of these operations is the ability to configure a release agent for a cgroup. This agent is triggered once the last task of the cgroup exits. The release agent is run as root on the underlying host.

An attacker with this capability could utilise cgroups to execute commands on the underlying node, thereby breaking out of the current container.

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node)
WHERE "SYS_ADMIN" in src.capabilities
```

The above query finds pods (`src`) where `SYS_ADMIN` is in its `capabilities` property. This property is populated by IceKube with the capabilities calculated from the pod spec. The node (`dest`) that hosts the pod is then targeted.
