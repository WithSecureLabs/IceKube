from typing import ClassVar, Optional


class Relationship:
    """
    Consolidates the various relationship types into a single class for better
    tracking of where we assign each relationship across the codebase.

    Relationships in the order (ObjectOne, RELATIONSHIP, ObjectTwo) are 
    in this direction in neo4j: (ObjectOne)-[:RELATIONSHIP]->(ObjectTwo)
    """
    USES_ACCOUNT: ClassVar[str] = "USES_ACCOUNT"
    HOSTS_POD: ClassVar[str] = "HOSTS_POD"

    AUTHENTICATION_TOKEN_FOR: ClassVar[str] = "AUTHENTICATION_TOKEN_FOR"
    GET_AUTHENTICATION_TOKEN_FOR: ClassVar[str] = "GET_AUTHENTICATION_TOKEN_FOR"

    WITHIN_NAMESPACE: ClassVar[str] = "WITHIN_NAMESPACE"

    GRANTS_PODS_CREATE: ClassVar[str] = "GRANTS_PODS_CREATE"
    GRANTS_REPLICATIONCONTROLLERS_CREATE: ClassVar[str] = "GRANTS_REPLICATIONCONTROLLERS_CREATE"
    GRANTS_DAEMONSETS_CREATE: ClassVar[str] = "GRANTS_DAEMONSETS_CREATE"
    GRANTS_DEPLOYMENTS_CREATE: ClassVar[str] = "GRANTS_DEPLOYMENTS_CREATE"
    GRANTS_REPLICASETS_CREATE: ClassVar[str] = "GRANTS_REPLICASETS_CREATE"
    GRANTS_STATEFULSETS_CREATE: ClassVar[str] = "GRANTS_STATEFULSETS_CREATE"
    GRANTS_CRONJOBS_CREATE: ClassVar[str] = "GRANTS_CRONJOBS_CREATE"
    GRANTS_JOBS_CREATE: ClassVar[str] = "GRANTS_JOBS_CREATE"
    
    GRANTS_AZUREPODIDENTITYEXCEPTIONS_CREATE: ClassVar[str] = "GRANTS_AZUREPODIDENTITYEXCEPTIONS_CREATE"
    GRANTS_CERTIFICATESIGNINGREQUESTS_CREATE: ClassVar[str] = "GRANTS_CERTIFICATESIGNINGREQUESTS_CREATE"
    GRANTS_PROXY_CREATE: ClassVar[str] = "GRANTS_PROXY_CREATE"
    
    GRANTS_GET: ClassVar[str] = "GRANTS_GET"
    GRANTS_LIST: ClassVar[str] = "GRANTS_LIST"
    GRANTS_UPDATE: ClassVar[str] = "GRANTS_UPDATE"
    GRANTS_WATCH: ClassVar[str] = "GRANTS_WATCH"
    GRANTS_PATCH: ClassVar[str] = "GRANTS_PATCH"
    GRANTS_APPROVE: ClassVar[str] = "GRANTS_APPROVE"
    GRANTS_PERMISSION: ClassVar[str] = "GRANTS_PERMISSION"
    
    GRANTS_ESCALATE: ClassVar[str] = "GRANTS_ESCALATE"
    GRANTS_IMPERSONATE: ClassVar[str] = "GRANTS_IMPERSONATE"
    GRANTS_TOKEN_CREATE: ClassVar[str] = "GRANTS_TOKEN_CREATE"
    GRANTS_EPHEMERAL_PATCH: ClassVar[str] = "GRANTS_EPHEMERAL_PATCH"

    BOUND_TO: ClassVar[str] = "BOUND_TO"
    USES_ACCOUNT: ClassVar[str] = "USES_ACCOUNT"
    MOUNTS_SECRET: ClassVar[str] = "MOUNTS_SECRET"
    CREATE_POD_WITH_SA: ClassVar[str] = "CREATE_POD_WITH_SA"
    UPDATE_WORKLOAD_WITH_SA: ClassVar[str] = "UPDATE_WORKLOAD_WITH_SA"

    EXEC_INTO: ClassVar[str] = "EXEC_INTO"
    REPLACE_IMAGE: ClassVar[str] = "REPLACE_IMAGE"
    DEBUG_POD: ClassVar[str] = "DEBUG_POD"

    ACCESS_SECRET: ClassVar[str] = "ACCESS_SECRET"
    GENERATE_TOKEN: ClassVar[str] = "GENERATE_TOKEN"
    RBAC_ESCALATE_TO: ClassVar[str] = "RBAC_ESCALATE_TO"

    GENERATE_CLIENT_CERTIFICATE: ClassVar[str] = "GENERATE_CLIENT_CERTIFICATE"
    HAS_CSR_APPROVAL: ClassVar[str] = "HAS_CSR_APPROVAL"

    CAN_IMPERSONATE: ClassVar[str] = "CAN_IMPERSONATE"

    IS_PRIVILEGED: ClassVar[str] = "IS_PRIVILEGED"
    CAN_CGROUP_BREAKOUT: ClassVar[str] = "CAN_CGROUP_BREAKOUT"
    CAN_LOAD_KERNEL_MODULES: ClassVar[str] = "CAN_LOAD_KERNEL_MODULES"
    CAN_ACCESS_DANGEROUS_HOST_PATH: ClassVar[str] = "CAN_ACCESS_DANGEROUS_HOST_PATH"
    CAN_NSENTER_HOST: ClassVar[str] = "CAN_NSENTER_HOST"
    CAN_ACCESS_HOST_FD: ClassVar[str] = "CAN_ACCESS_HOST_FD"
    CAN_EXEC_THROUGH_KUBELET: ClassVar[str] = "CAN_EXEC_THROUGH_KUBELET"

    ACCESS_POD: ClassVar[str] = "ACCESS_POD"
    UPDATE_AWS_AUTH: ClassVar[str] = "UPDATE_AWS_AUTH"
    AZURE_POD_IDENTITY_EXCEPTION: ClassVar[str] = "AZURE_POD_IDENTITY_EXCEPTION"

    # Current resource defines the spec/creation of the subresource
    DEFINES: ClassVar[str] = "DEFINES"
    # Defines a reference to another object (e.g. Pod -> ServiceAccount)
    REFERENCES: ClassVar[str] = "REFERENCES"
    # Directly consumes a resource (e.g. PersistentVolumeClaim -> PersistentVolume)
    CONSUMES: ClassVar[str] = "CONSUMES"
    # Indirectly consumes a resource, without an exclusive relationship to the refering node (e.g. PersistentVolume -> StorageClass)
    USES: ClassVar[str] = "USES"
    # Defines ownership of a resource (e.g. Deployment-[:OWNS]->ReplicaSet)
    OWNS: ClassVar[str] = "OWNS"

    @staticmethod
    def generate_grant(verb: str, sub_resource: Optional[str]) -> str:
        if sub_resource is None:
            return f"GRANTS_{verb.upper()}".replace("-", "_")

        return f"GRANTS_{sub_resource}_{verb}".upper().replace("-", "_")