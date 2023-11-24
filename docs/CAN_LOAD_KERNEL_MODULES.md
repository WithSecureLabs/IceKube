# CAN_LOAD_KERNEL_MODULES

### Overview

This attack path aims to locate pods which have the `SYS_MODULE` capability, and as such can breakout onto the underlying node.

### Description

The `SYS_MODULE` capability allows management of Kernel modules. This includes loading additional modules.

An attacker with this capability could load a custom module with malicious code. The code would then be executed by the kernel allowing for commands to be run outside of the container, effectively breaking out. 

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node)
WHERE "SYS_MODULE" in src.capabilities
```

The above query finds pods (`src`) where `SYS_MODULE` is in its `capabilities` property. This property is populated by IceKube with the capabilities calculated from the pod spec. The node (`dest`) that hosts the pod is then targeted.
