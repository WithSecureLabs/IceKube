from __future__ import annotations

import json
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.node import Node
from icekube.models.secret import Secret
from icekube.models.serviceaccount import ServiceAccount
from icekube.relationships import Relationship
from pydantic import computed_field

CAPABILITIES = [
    "AUDIT_CONTROL",
    "AUDIT_READ",
    "AUDIT_WRITE",
    "BLOCK_SUSPEND",
    "BPF",
    "CHECKPOINT_RESTORE",
    "CHOWN",
    "DAC_OVERRIDE",
    "DAC_READ_SEARCH",
    "FOWNER",
    "FSETID",
    "IPC_LOCK",
    "IPC_OWNER",
    "KILL",
    "LEASE",
    "LINUX_IMMUTABLE",
    "MAC_ADMIN",
    "MAC_OVERRIDE",
    "MKNOD",
    "NET_ADMIN",
    "NET_BIND_SERVICE",
    "NET_BROADCAST",
    "NET_RAW",
    "PERFMON",
    "SETFCAP",
    "SETGID",
    "SETPCAP",
    "SETUID",
    "SYSLOG",
    "SYS_ADMIN",
    "SYS_BOOT",
    "SYS_CHROOT",
    "SYS_MODULE",
    "SYS_NICE",
    "SYS_PACCT",
    "SYS_PTRACE",
    "SYS_RAWIO",
    "SYS_RESOURCE",
    "SYS_TIME",
    "SYS_TTY_CONFIG",
    "WAKE_ALARM",
]


class Pod(Resource):
    supported_api_groups: List[str] = [""]

    @computed_field  # type: ignore
    @cached_property
    def service_account(self) -> Optional[ServiceAccount]:
        sa = self.data.get("spec", {}).get("serviceAccountName")

        if sa:
            return ServiceAccount(name=sa, namespace=self.namespace)
        else:
            return None

    @computed_field  # type: ignore
    @cached_property
    def node(self) -> Optional[Node]:
        node = self.data.get("spec", {}).get("nodeName")

        if node:
            return Node(name=node)
        else:
            return None

    @computed_field  # type: ignore
    @cached_property
    def containers(self) -> List[Dict[str, Any]]:
        return cast(
            List[Dict[str, Any]],
            self.data.get("spec", {}).get("containers", []),
        )

    @computed_field  # type: ignore
    @cached_property
    def capabilities(self) -> List[str]:
        capabilities = set()

        for container in self.containers:
            security_context = container.get("securityContext") or {}
            caps = security_context.get("capabilities") or {}
            addl = caps.get("add") or []
            addl = [x.upper() for x in addl]
            add = set(addl)

            if "ALL" in add:
                add.remove("ALL")
                add.update(set(CAPABILITIES))

            capabilities.update(add)

        return list(capabilities)

    @computed_field  # type: ignore
    @cached_property
    def privileged(self) -> bool:
        containers = self.data.get("spec", {}).get("containers", [])
        privileged = False
        for container in containers:
            context = container.get("securityContext") or {}

            if context.get("privileged", False):
                privileged = True

        return privileged

    @computed_field  # type: ignore
    @cached_property
    def host_path_volumes(self) -> List[str]:
        volumes = self.data.get("spec", {}).get("volumes") or []
        host_volumes = [x for x in volumes if "hostPath" in x and x["hostPath"]]

        return [x["hostPath"]["path"] for x in host_volumes]

    @computed_field  # type: ignore
    @cached_property
    def hostPID(self) -> bool:
        return self.data.get("spec", {}).get("hostPID") or False

    @computed_field  # type: ignore
    @cached_property
    def hostNetwork(self) -> bool:
        return self.data.get("spec", {}).get("hostNetwork") or False

    @property
    def dangerous_host_path(self) -> bool:
        # Dangerous paths to check for
        # Not all of these give direct node compromise, but will grant enough
        # permissions to maybe steal certificates to help with API server
        # as the node, or the like
        dangerous_paths = [
            "/etc/kubernetes/admin.conf",
            "/etc/kubernetes/kubeconfig",
            "/etc/shadow",
            "/proc/sys/kernel",
            "/root/.kube/config",
            "/root/.ssh/authorized_keys",
            "/run/containerd/containerd.sock",
            "/run/containerd/containerd.sock",
            "/run/crio/crio.sock",
            "/run/cri-dockerd.sock",
            "/run/docker.sock",
            "/run/dockershim.sock",
            "/var/lib/kubelet/pods/",
            "/var/lib/kubernetes/",
            "/var/lib/minikube/certs/apiserver.key",
            "/var/log",
            "/var/run/containerd/containerd.sock",
            "/var/run/containerd/containerd.sock",
            "/var/run/crio/crio.sock",
            "/var/run/cri-dockerd.sock",
            "/var/run/docker.sock",
            "/var/run/dockershim.sock",
        ]
        for volume, test_path in product(self.host_path_volumes, dangerous_paths):
            try:
                Path(test_path).relative_to(Path(volume))
                return True
            except ValueError:
                pass
        return False

    @property
    def mounted_secrets(self) -> List[str]:
        if self.raw:
            data = json.loads(self.raw)
        else:
            return []

        secrets = []

        volumes = data.get("spec", {}).get("volumes") or []

        for volume in volumes:
            if volume.get("secret"):
                secrets.append(volume["secret"]["secretName"])

        for container in data.get("spec", {}).get("containers") or []:
            if not container.get("env"):
                continue
            for env in container["env"]:
                try:
                    secrets.append(env["valueFrom"]["secretKeyRef"]["name"])
                except (KeyError, TypeError):
                    pass

        return secrets

    @property
    def db_labels(self) -> Dict[str, Any]:
        return {
            **super().db_labels,
            "capabilities": self.capabilities,
            "host_path_volumes": self.host_path_volumes,
            "dangerous_host_path": self.dangerous_host_path,
            "privileged": self.privileged,
            "hostPID": self.hostPID,
            "hostNetwork": self.hostNetwork,
        }

    def relationships(
        self,
        initial: bool = True,
    ) -> List[RELATIONSHIP]:
        relationships = super().relationships()

        if self.service_account:
            relationships += [(self, Relationship.USES_ACCOUNT, self.service_account)]
        if self.node:
            relationships += [(self.node, Relationship.HOSTS_POD, self)]
        for secret in self.mounted_secrets:
            relationships += [
                (
                    self,
                    Relationship.MOUNTS_SECRET,
                    Secret(
                        namespace=cast(str, self.namespace),
                        name=secret,
                    ),
                ),
            ]

        return relationships
