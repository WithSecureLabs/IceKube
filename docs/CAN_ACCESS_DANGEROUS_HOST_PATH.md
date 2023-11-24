# CAN_ACCESS_DANGEROUS_HOST_PATH

### Overview

This attack path aims to locate pods which have potentially dangerous paths from the underlying node's file system mounted. These could be used to gain a foothold on the underlying node or gain node credentials.

### Description

Pods can mount paths from the underlying host. These are `hostPath` volume types. Access to certain paths on the host could be considered dangerous as it may grant access to sensitive resources on the host. This could include the kubelet credentials, the roots home directory, the container socket, etc. 

An attacker with access to these resources could potentially gain access to the underlying host, or gain access to sensitive credentials.

### Defense

Pod Security Admission (PSA) should be configured to enforce the `restricted` standard. Should this be too restrictive, `baseline` could be used instead. 

PSA can be limited in its flexibility, for example having a policy that slightly deviates from the `restricted` standard. Should further flexibility be required compared to what PSA can provide, custom admission webhooks should be used to enforce pod security.

Should host path volumes be required, the volumes should be reviewed to ensure they do not expose sensitive files from the host.

### Cypher Deep-Dive

```cypher
MATCH (src:Pod {dangerous_host_path: true})<-[:HOSTS_POD]-(dest:Node)
```

The above query finds pods (`src`) with the `dangerous_host_path` property set to `true`. This property is set by IceKube if a `hostPath` volume matches a number of pre-configured dangerous paths. The node (`dest`) that hosts the pod is then targeted.
