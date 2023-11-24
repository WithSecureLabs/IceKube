from typing import List, Type

from icekube.models.api_resource import APIResource
from icekube.models.base import Resource
from icekube.models.cluster import Cluster
from icekube.models.clusterrole import ClusterRole
from icekube.models.clusterrolebinding import ClusterRoleBinding
from icekube.models.group import Group
from icekube.models.namespace import Namespace
from icekube.models.pod import Pod
from icekube.models.role import Role
from icekube.models.rolebinding import RoleBinding
from icekube.models.secret import Secret
from icekube.models.securitycontextconstraints import (
    SecurityContextConstraints,
)
from icekube.models.serviceaccount import ServiceAccount
from icekube.models.signer import Signer
from icekube.models.user import User

enumerate_resource_kinds: List[Type[Resource]] = [
    ClusterRole,
    ClusterRoleBinding,
    Namespace,
    Pod,
    Role,
    RoleBinding,
    Secret,
    SecurityContextConstraints,
    ServiceAccount,
]


# plurals: Dict[str, Type[Resource]] = {x.plural: x for x in enumerate_resource_kinds}


__all__ = [
    "APIResource",
    "Cluster",
    "ClusterRole",
    "ClusterRoleBinding",
    "Group",
    "Namespace",
    "Pod",
    "Role",
    "RoleBinding",
    "Secret",
    "SecurityContextConstraints",
    "ServiceAccount",
    "Signer",
    "User",
]
