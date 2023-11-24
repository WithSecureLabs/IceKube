# GENERATE_CLIENT_CERTIFICATE

### Overview

This attack path aims to locate subjects which can create a certificate signing request (CSR) _and_ approve its signing. An attacker can use this to generate credentials for another user, service account, or group.

### Description

The CSR API allows the submission of Certificate Signing Requests (CSRs). Should the CSR be signed by the `kubernetes.io/kube-apiserver-client` signer, the signed certificate can be used as a client certificate for the purpose of authenticating to the cluster. The common name of the certificate specifies the users username, and the organisations their groups.

Should an attacker have the ability to create CSRs they could submit certificate requests for other subjects of the cluster. Should they also have the ability to approve the signing with the above signer, signed certificates for the specified subjects would be generated.

An attacker could use these to escalate their privileges within the cluster.

### Defense

RBAC permissions regarding the creation and approval of CSRs should be reviewed. Access should be restricted to required entities.

### Cypher Deep-Dive

```cypher
MATCH (src)-[:GRANTS_CERTIFICATESIGNINGREQUESTS_CREATE]->(cluster:Cluster), (dest)
WHERE (src)-[:HAS_CSR_APPROVAL]->(cluster) AND (src)-[:GRANTS_APPROVE]->(:Signer {
  name: "kubernetes.io/kube-apiserver-client"
}) AND (dest:User OR dest:Group OR dest:ServiceAccount)
```

The above query ensure a resource (`src`) has the following three permissions:

- Ability to create CSRs through `GRANTS_CERTIFICATESIGNINGREQUESTS_CREATE`
- Ability to approve CSRs through `HAS_CSR_APPROVAL`
- Approved to use the `kubernetes.io/kube-apiserver-client` signer through `GRANTS_APPROVE`

Should all three conditions be met, subjects (`dest`) are targeted if they are a `User`, `Group` or `ServiceAccount`
