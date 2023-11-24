# UPDATE_AWS_AUTH

### Overview

This attack path is specific to AWS EKS, and aims to locate subjects which can make changes to the `aws-auth` ConfigMap. Upon successful exploitation, an attacker is considered to have reached the `system:masters` group.

### Description

In AWS EKS, the `aws-auth` ConfigMap is used to map AWS IAM roles to Kubernetes RBAC users and groups. As such, it allows the API server to enforce authorisation on AWS entities when accessing the cluster. Once an IAM identity is added to the ConfigMap, it will be able to access the cluster using the Kubernetes API with its permissions depending on the mapping created.

An attacker with privileges which allows them to modify the `aws-auth` ConfigMap could add their own IAM roles to this configuration and granting their own role permissions within the cluster, including the `system:masters` group.

An example addition to the ConfigMap can be seen below for the `mapRoles` section:

```yaml
- groups:
    - system:masters
  rolearn: ATTACKER_CONTROLLED_ARN
  username: user
```

An EKS token can then be manually generated or the kubeconfig file can be updated to automatically request a token for the configured role ARN which can be used to authenticate against the cluster. 

### Defense

RBAC write access to the `aws-auth` ConfigMap within the `kube-system` namespace should be reviewed. Access should be restricted to required entities. 

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_PATCH|GRANTS_UPDATE]->(:ConfigMap {
  name: 'aws-auth', namespace: 'kube-system'
}), (dest:Group {
  name: 'system:masters'
})
```

The above query finds all resources (`src`) that have the `PATCH` or `UPDATE` permission against the `aws-auth` ConfigMap. Both the namespace and name are used to specify the exact ConfigMap in case another version is present in a different namespace. 

As all queries must have a `src` and `dest` so IceKube knows the two sides of a relationship, and as this is one of the rare instances where the original query doesn't include the destination resource. A secondary query is added to query for the `system:masters` group and specify that as the `dest`.
