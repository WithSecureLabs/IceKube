from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from icekube.models.base import RELATIONSHIP, Resource
from icekube.models.node import Node
from icekube.models.secret import Secret
from icekube.models.serviceaccount import ServiceAccount
from icekube.neo4j import mock
from pydantic import root_validator

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
    service_account: Optional[ServiceAccount]
    node: Optional[Node]
    containers: List[Dict[str, Any]]
    capabilities: List[str]
    host_path_volumes: List[str]
    privileged: bool
    hostPID: bool
    hostNetwork: bool

    @root_validator(pre=True)
    def inject_service_account(cls, values):
        data = json.loads(values.get("raw", "{}"))
        sa = data.get("spec", {}).get("serviceAccountName")
        if sa:
            values["service_account"] = mock(
                ServiceAccount,
                name=sa,
                namespace=values.get("namespace"),
            )
        else:
            values["service_account"] = None
        return values

    @root_validator(pre=True)
    def inject_node(cls, values):
        data = json.loads(values.get("raw", "{}"))
        node = data.get("spec", {}).get("nodeName")
        if node:
            values["node"] = mock(Node, name=node)
        else:
            values["node"] = None

        return values

    @root_validator(pre=True)
    def inject_containers(cls, values):
        data = json.loads(values.get("raw", "{}"))

        values["containers"] = data.get("spec", {}).get("containers", [])

        return values

    @root_validator(pre=True)
    def inject_capabilities(cls, values):
        data = json.loads(values.get("raw", "{}"))

        containers = data.get("spec", {}).get("containers", [])
        capabilities = set()

        for container in containers:
            security_context = container.get("securityContext") or {}
            caps = security_context.get("capabilities") or {}
            addl = caps.get("add") or []
            addl = [x.upper() for x in addl]
            add = set(addl)

            if "ALL" in add:
                add.remove("ALL")
                add.update(set(CAPABILITIES))

            capabilities.update(add)

        values["capabilities"] = list(capabilities)

        return values

    @root_validator(pre=True)
    def inject_privileged(cls, values):
        data = json.loads(values.get("raw", "{}"))

        containers = data.get("spec", {}).get("containers", [])
        privileged = False
        for container in containers:
            context = container.get("securityContext") or {}

            if context.get("privileged", False):
                privileged = True

        values["privileged"] = privileged

        return values

    @root_validator(pre=True)
    def inject_host_path_volumes(cls, values):
        data = json.loads(values.get("raw", "{}"))
        volumes = data.get("spec", {}).get("volumes") or []
        host_volumes = [x for x in volumes if "hostPath" in x and x["hostPath"]]

        values["host_path_volumes"] = [x["hostPath"]["path"] for x in host_volumes]

        return values

    @root_validator(pre=True)
    def inject_host_pid(cls, values):
        data = json.loads(values.get("raw", "{}"))

        values["hostPID"] = data.get("spec", {}).get("hostPID") or False

        return values

    @root_validator(pre=True)
    def inject_host_network(cls, values):
        data = json.loads(values.get("raw", "{}"))

        values["hostNetwork"] = data.get("spec", {}).get("hostNetwork") or False

        return values

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
            relationships += [(self, "USES_ACCOUNT", self.service_account)]
        if self.node:
            relationships += [(self.node, "HOSTS_POD", self)]
        for secret in self.mounted_secrets:
            relationships += [
                (
                    self,
                    "MOUNTS_SECRET",
                    mock(Secret, namespace=cast(str, self.namespace), name=secret),
                ),
            ]

        return relationships
