# CAN_ACCESS_HOST_FD

### Overview

This attack path aims to locate pods which have the `DAC_READ_SEARCH` capability which could allow accessing files on the host filesystem. An attacker could use this to break out onto the underlying node.

### Description

The `DAC_READ_SEARCH` capability grants access to `open_by_handle_at` which allows opening file descriptors across mount namespaces. `DAC_READ_SEARCH` by itself simply grants read access to the files opened, however when combined with `DAC_OVERRIDE` (a default capability) can provide write permissions.

An attacker could use this access to open sensitive files on the underlying host, and either retrieve credentials to gain access to the underlying host or the kubelet credentials. Should `DAC_OVERRIDE` be present, access could be used to write authentication material such as an SSH key to an `authorized_keys` file.

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node)
WHERE "DAC_READ_SEARCH" in src.capabilities
```

The above query finds pods (`src`) where `DAC_READ_SEARCH` is in its `capabilities` property. This property is populated by IceKube with the capabilities calculated from the pod spec. The node (`dest`) that hosts the pod is then targeted.
