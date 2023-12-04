# flake8: noqa

from typing import List
from icekube.relationships import Relationship

WORKLOAD_TYPES = [
    "ReplicationController",
    "DaemonSet",
    "Deployment",
    "ReplicaSet",
    "StatefulSet",
    "CronJob",
    "Job",
]


def create_workload_query(workloads: List[str] = WORKLOAD_TYPES) -> str:
    relationships = [f"GRANTS_{workload.upper()}S_CREATE" for workload in workloads]
    return "|".join(relationships)


def workload_query(
    workloads: List[str] = WORKLOAD_TYPES, name: str = "workload"
) -> str:
    joined = f" OR {name}:".join(WORKLOAD_TYPES)
    return f"({name}:{joined})"


attack_paths = {
    # Subject -> Role Bindings
    Relationship.BOUND_TO: "MATCH (src)-[:BOUND_TO]->(dest)",
    # Role Binding -> Role
    Relationship.GRANTS_PERMISSION: "MATCH (src)-[:GRANTS_PERMISSION]->(dest)",
    # Pod -> Service Account
    Relationship.USES_ACCOUNT: "MATCH (src:Pod)-[:USES_ACCOUNT]->(dest:ServiceAccount)",
    # Pod -> Secrett
    Relationship.MOUNTS_SECRET: "MATCH (src:Pod)-[:MOUNTS_SECRET]->(dest:Secret)",
    # Subject has permission to create pod within namespace with target
    # Service Account
    Relationship.CREATE_POD_WITH_SA: f"""
        MATCH (src)-[:GRANTS_PODS_CREATE|{create_workload_query()}]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount)
        """,
    # Subject has permission to update workload within namespace with target
    # Service Account
    Relationship.UPDATE_WORKLOAD_WITH_SA: f"""
        MATCH (src)-[:GRANTS_UPDATE|GRANTS_PATCH]->(workload)-[:WITHIN_NAMESPACE]->(ns:Namespace)<-[:WITHIN_NAMESPACE]-(dest:ServiceAccount)
        WHERE {workload_query()}
        """,
    # Subject -> Pod
    Relationship.EXEC_INTO: "MATCH (src)-[:GRANTS_EXEC_CREATE]->(dest:Pod)<-[:GRANTS_GET]-(src)",
    # Subject -> Pod
    Relationship.REPLACE_IMAGE: "MATCH (src)-[:GRANTS_PATCH]->(dest:Pod)",
    # Subject -> Pod
    Relationship.DEBUG_POD: "MATCH (src)-[:GRANTS_EPHEMERAL_PATCH]->(dest:Pod)",
    # Subject has permission to read authentication token for Service Account
    Relationship.GET_AUTHENTICATION_TOKEN_FOR: """
        MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(secret:Secret)-[:AUTHENTICATION_TOKEN_FOR]->(dest:ServiceAccount)
        """,
    # Subject -> Secret
    Relationship.ACCESS_SECRET: "MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(dest:Secret)",
    # Generate service account token
    Relationship.GENERATE_TOKEN: "MATCH (src)-[:GRANTS_TOKEN_CREATE]->(dest:ServiceAccount)",
    # RBAC escalate verb to change a role to be more permissive
    Relationship.RBAC_ESCALATE_TO: [
        # RoleBindings
        """
        MATCH (src:RoleBinding)-[:GRANTS_ESCALATE]->(role)-[:WITHIN_NAMESPACE]->(:Namespace)<-[:WITHIN_NAMESPACE]-(dest)
        WHERE (role:Role OR role:ClusterRole) AND (src)-[:GRANTS_PERMISSION]->(role)
        """,
        # ClusterRoleBindings
        """
        MATCH (src:ClusterRoleBinding)-[:GRANTS_ESCALATE]->(role:ClusterRole), (dest)
        WHERE (src)-[:GRANTS_PERMISSION]->(role)
        """,
    ],
    # Subject -> User / Group / ServiceAccount
    Relationship.GENERATE_CLIENT_CERTIFICATE: """
        MATCH (src)-[:GRANTS_CERTIFICATESIGNINGREQUESTS_CREATE]->(cluster:Cluster), (dest)
        WHERE (src)-[:HAS_CSR_APPROVAL]->(cluster) AND (src)-[:GRANTS_APPROVE]->(:Signer {
          name: "kubernetes.io/kube-apiserver-client"
        }) AND (dest:User OR dest:Group OR dest:ServiceAccount)
        """,
    # Impersonate
    Relationship.CAN_IMPERSONATE: "MATCH (src)-[:GRANTS_IMPERSONATE]->(dest)",
    # Pod breakout
    Relationship.IS_PRIVILEGED: "MATCH (src:Pod {privileged: true})<-[:HOSTS_POD]-(dest:Node)",
    Relationship.CAN_CGROUP_BREAKOUT: 'MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node) WHERE "SYS_ADMIN" in src.capabilities',
    Relationship.CAN_LOAD_KERNEL_MODULES: 'MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node) WHERE "SYS_MODULE" in src.capabilities',
    Relationship.CAN_ACCESS_DANGEROUS_HOST_PATH: "MATCH (src:Pod {dangerous_host_path: true})<-[:HOSTS_POD]-(dest:Node)",
    Relationship.CAN_NSENTER_HOST: 'MATCH (src:Pod {hostPID: true})<-[:HOSTS_POD]-(dest:Node) WHERE all(x in ["SYS_ADMIN", "SYS_PTRACE"] WHERE x in src.capabilities)',
    Relationship.CAN_ACCESS_HOST_FD: 'MATCH (src:Pod)<-[:HOSTS_POD]-(dest:Node) WHERE "DAC_READ_SEARCH" in src.capabilities',
    # Can jump to pods running on node
    Relationship.ACCESS_POD: "MATCH (src:Node)-[:HOSTS_POD]->(dest:Pod)",
    # Can exec into pods on a node
    Relationship.CAN_EXEC_THROUGH_KUBELET: "MATCH (src)-[:GRANTS_PROXY_CREATE]->(:Node)-[:HOSTS_POD]->(dest:Pod)",
    # Can update aws-auth ConfigMap
    Relationship.UPDATE_AWS_AUTH: """
        MATCH (src)-[:GRANTS_PATCH|GRANTS_UPDATE]->(:ConfigMap {
          name: 'aws-auth', namespace: 'kube-system'
        }), (dest:Group {
          name: 'system:masters'
        })
        """,
    Relationship.AZURE_POD_IDENTITY_EXCEPTION: [
        # Create workload based of existing APIE
        f"""
        MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(azexc:AzurePodIdentityException)-[:WITHIN_NAMESPACE]->(ns:Namespace), (dest:ClusterRoleBinding)
        WHERE (dest.name = 'aks-cluster-admin-binding' OR dest.name = 'aks-cluster-admin-binding-aad') AND (EXISTS {{
            MATCH (src)-[:{create_workload_query()}|GRANTS_PODS_CREATE]->(ns)
        }} OR EXISTS {{
            MATCH (src)-[:GRANTS_PATCH|GRANTS_UPDATE]->(workload)-[:WITHIN_NAMESPACE]->(ns)
            WHERE {workload_query()}
        }})
        """,
        # Create APIE based of existing workload
        """
        MATCH (src)-[:GRANTS_GET|GRANTS_LIST|GRANTS_WATCH]->(pod:Pod)-[:WITHIN_NAMESPACE]->(ns:Namespace), (src)-[r {
          attack_path: 1
        }]->(pod), (dest:ClusterRoleBinding)
        WHERE (dest.name='aks-cluster-admin-binding' OR dest.name='aks-cluster-admin-binding-aad') AND (EXISTS {
            (src)-[:GRANTS_AZUREPODIDENTITYEXCEPTIONS_CREATE]->(ns)
        } OR EXISTS {
            (src)-[:GRANTS_UPDATE|GRANTS_PATCH]->(:AzurePodIdentityException)-[:WITHIN_NAMESPACE]->(ns)
        })
        """,
    ],
}
