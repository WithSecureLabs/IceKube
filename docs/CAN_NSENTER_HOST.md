# CAN_NSENTER_HOST

### Overview

This attack path aims to locate pods which have either the `SYS_ADMIN` or `SYS_PTRACE` capability and share the host's PID namespace allowing them to break out onto the underlying node.

### Description

An attacker with access to a pod which has either the `SYS_ADMIN` or `SYS_PTRACE` capability and shares the host's PID namespace could potentially break out of the pod using the `nsenter` utility.

An example command could be `nsenter -t 1 -a`.

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod {hostPID: true})<-[:HOSTS_POD]-(dest:Node)
WHERE all(x in ["SYS_ADMIN", "SYS_PTRACE"] WHERE x in src.capabilities)
```

The above query finds pods (`src`) configured with both the `SYS_ADMIN` or `SYS_PTRACE` capabilities and shares the node's PID namespace. These parameters are configured by IceKube based of the pod spec. The target (`dest`) is set as the node upon which the pod is running.
