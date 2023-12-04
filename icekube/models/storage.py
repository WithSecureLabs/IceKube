from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from icekube.relationships import Relationship
from icekube.models.base import RELATIONSHIP, BaseResource, Resource
from icekube.models.node import NodeSelector
from icekube.models.objectreference import ObjectReference, SecretReference
from pydantic import BaseModel, Field, root_validator


def build_default(kvp: Dict[str, Any], key: str, value: Optional[Any]) -> Resource:
    kvp[key] = value
    return kvp

def build_default_resource(
    kvp: BaseModel,
    key: str,
    objRef: Type[Resource],
    value: Dict[str, Any]
) -> Resource:
    if value is not None:
        kvp[key] = objRef(**value)
    else:
        kvp[key] = None

    return kvp

def build_default_toplevel_str(
    values: BaseModel,
    key: str,
    spec: Dict[str, Any]
) -> Resource:
    build_default(values, key, spec.get(key))
    return values

def build_default_toplevel_resource(
    cls: Type[Resource],
    key: str,
    values: BaseModel,
    spec: Dict[str, Any]
) -> Resource:
    build_default_resource(values, key, cls, spec.get(key))
    return values

class AWSElasticBlockSourceVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "AWSElasticBlockStoreVolumeSource"

    fsType: Optional[str] = None
    partition: Optional[int] = None
    readOnly: Optional[bool] = None
    volumeID: Optional[str] = None

class AzureDiskVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "AzureDiskVolumeSource"

    cachingMode: Optional[str] = None
    diskName: Optional[str] = None
    diskURI: Optional[str] = None
    fsType: Optional[str] = None
    kind: Optional[str] = None
    readOnly: Optional[bool] = None

class AzureFilePersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "AzureFilePersistentVolumeSource"

    readOnly: Optional[bool] = None
    secretName: Optional[str] = None
    secretNamespace: Optional[str] = None
    shareName: Optional[str] = None

class CephFSPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "CephFSPersistentVolumeSource"

    monitors: List[str] = []
    path: Optional[str] = None
    readOnly: Optional[bool] = None
    secretFile: Optional[str] = None
    secretRef: Optional[Union[SecretReference, str]] = None
    user: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class CinderPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "CinderPersistentVolumeSource"

    fsType: Optional[str] = None
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[SecretReference, str]] = None
    volumeID: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class CSIPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "CSIPersistentVolumeSource"

    controllerExpandSecretRef: Optional[Union[SecretReference, str]] = None
    controllerPublishSecretRef: Optional[Union[SecretReference, str]] = None
    driver: Optional[str] = None
    fsType: Optional[str] = None
    nodeExpandSecretRef: Optional[Union[SecretReference, str]] = None
    nodePublishSecretRef: Optional[Union[SecretReference, str]] = None
    nodeStageSecretRef: Optional[Union[SecretReference, str]] = None
    readOnly: Optional[bool] = None
    volumeAttributes: Dict[str, Any] = {}
    volumeHandle: Optional[str] = None

    @root_validator(pre=True)
    def extract_fields(cls, values):
        spec = json.loads(values.get("raw", "{}")).get("spec", {})

        volumeAttributes = spec.get("volumeAttributes", {})
        if volumeAttributes is not None and isinstance(volumeAttributes, str):
            volumeAttributes = json.loads(volumeAttributes)

        values["volumeAttributes"] = volumeAttributes
        return values

    @property
    def referenced_objects(self):
        return [
            self.controllerExpandSecretRef,
            self.controllerPublishSecretRef,
            self.nodeExpandSecretRef,
            self.nodePublishSecretRef,
            self.nodeStageSecretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class FCVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "FCVolumeSource"

    fsType: Optional[str] = None
    lun: Optional[int] = None
    readOnly: Optional[bool] = None
    targetWWNs: List[str] = []
    wwids: List[str] = []

class FlexPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "FlexPersistentVolumeSource"

    driver: Optional[str] = None
    fsType: Optional[str] = None
    options: Dict[str, Any] = {}
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[SecretReference, str]] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]

    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class FlockerVolumeSource(BaseResource):
    apiversion: str = "v1"
    kind: str = "FlockerVolumeSource"

    datasetName: Optional[str] = None
    datasetUUID: Optional[str] = None

class GCEPersistentDiskVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "GCEPersistentDiskVolumeSource"

    fsType: Optional[str] = None
    partition: Optional[int] = None
    pdName: Optional[str] = None
    readOnly: Optional[bool] = None

class GlusterfsPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "GlusterfsPersistentVolumeSource"

    endpoints: Optional[str] = None
    endpointsNamespace: Optional[str] = None
    path: Optional[str] = None
    readOnly: Optional[bool] = None

class HostPathVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "HostPathVolumeSource"

    path: Optional[str] = None
    type: Optional[str] = None

class ISCSIPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "ISCSIPersistentVolumeSource"

    chapAuthDiscovery: Optional[bool] = None
    chapAuthSession: Optional[bool] = None
    fsType: Optional[str] = None
    initiatorName: Optional[str] = None
    iqn: Optional[str] = None
    iscsiInterface: Optional[str] = None
    lun: Optional[int] = None
    portals: Optional[List[str]] = None
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[SecretReference, str]] = None
    targetPortal: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class LocalVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "LocalVolumeSource"

    fsType: Optional[str] = None
    path: Optional[str] = None

class NFSVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "NFSVolumeSource"

    path: Optional[str] = None
    readOnly: Optional[bool] = None
    server: Optional[str] = None

class VolumeNodeAffinity(BaseResource):
    apiVersion: str = "v1"
    kind: str = "VolumeNodeAffinity"

    required: NodeSelector

    @property
    def referenced_objects(self):
        return [
            self.required
        ]

class PhotonPersistentDiskVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "PhotonPersistentDiskVolumeSource"

    fsType: Optional[str] = None
    pdID: Optional[str] = None

class PortworxVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "PortworxVolumeSource"

    fsType: Optional[str] = None
    readOnly: Optional[bool] = None
    volumeID: Optional[str] = None

class QuobyteVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "QuobyteVolumeSource"

    group: Optional[str] = None
    readOnly: Optional[bool] = None
    registry: Optional[str] = None
    tenant: Optional[str] = None
    user: Optional[str] = None
    volume: Optional[str] = None

class RBDPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "RBDPersistentVolumeSource"

    fsType: Optional[str] = None
    image: Optional[str] = None
    keyring: Optional[str] = None
    monitors: Optional[List[str]] = None
    pool: Optional[str] = None
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[SecretReference, str]] = None
    user: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class ScaleIOPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "ScaleIOPersistentVolumeSource"

    fsType: Optional[str] = None
    gateway: Optional[str] = None
    protectionDomain: Optional[str] = None
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[SecretReference, str]] = None
    sslEnabled: Optional[bool] = None
    storageMode: Optional[str] = None
    storagePool: Optional[str] = None
    system: Optional[str] = None
    volumeName: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class StorageOSPersistentVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "StorageOSPersistentVolumeSource"

    fsType: Optional[str] = None
    readOnly: Optional[bool] = None
    secretRef: Optional[Union[ObjectReference, str]] = None
    volumeName: Optional[str] = None
    volumeNamespace: Optional[str] = None

    @property
    def referenced_objects(self):
        return [
            self.secretRef
        ]
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]


class VsphereVirtualDiskVolumeSource(BaseResource):
    apiVersion: str = "v1"
    kind: str = "VsphereVirtualDiskVolumeSource"

    fsType: Optional[str] = None
    storagePolicyID: Optional[str] = None
    storagePolicyName: Optional[str] = None
    volumePath: Optional[str] = None

class PersistentVolume(Resource):
    apiVersion: str = "v1"
    kind: str = "PersistentVolume"

    accessModes: Optional[List[str]] = None
    awsElasticBlockStore: Optional[AWSElasticBlockSourceVolumeSource] = None
    azureDisk: Optional[AzureDiskVolumeSource] = None
    azureFile: Optional[AzureFilePersistentVolumeSource] = None
    capacity: Optional[Dict[str, Any]] = None
    cephfs: Optional[CephFSPersistentVolumeSource] = None
    cinder: Optional[CinderPersistentVolumeSource] = None
    claimRef: Optional[Union[ObjectReference, str]] = None
    csi: Optional[CSIPersistentVolumeSource] = None
    fc: Optional[FCVolumeSource] = None
    flexVolume: Optional[FlexPersistentVolumeSource] = None
    flocker: Optional[FlockerVolumeSource] = None
    gcePersistentDisk: Optional[GCEPersistentDiskVolumeSource] = None
    glusterfs: Optional[GlusterfsPersistentVolumeSource] = None
    hostPath: Optional[HostPathVolumeSource] = None
    iscsi: Optional[ISCSIPersistentVolumeSource] = None
    local: Optional[LocalVolumeSource] = None
    mountOptions: Optional[List[str]] = None
    nfs: Optional[NFSVolumeSource] = None
    nodeAffinity: Optional[VolumeNodeAffinity] = None
    persistentVolumeReclaimPolicy: Optional[str] = None
    photonPersistentDisk: Optional[PhotonPersistentDiskVolumeSource] = None
    portworxVolume: Optional[PortworxVolumeSource] = None
    quobyte: Optional[QuobyteVolumeSource] = None
    rbd: Optional[RBDPersistentVolumeSource] = None
    scaleIO: Optional[ScaleIOPersistentVolumeSource] = None
    storageClassName: Optional[str] = None
    storageos: Optional[StorageOSPersistentVolumeSource] = None
    volumeMode: Optional[str] = None
    vsphereVolume: Optional[VsphereVirtualDiskVolumeSource] = None

    @root_validator(pre=True)
    def extract_fields(cls, values):
        spec = json.loads(values.get("raw", "{}")).get("spec", {})

        values = build_default_toplevel_resource(AWSElasticBlockSourceVolumeSource, "awsElasticBlockStore", values, spec)
        values = build_default_toplevel_resource(AzureDiskVolumeSource, "azureDisk", values, spec)
        values = build_default_toplevel_resource(AzureFilePersistentVolumeSource, "azureFile", values, spec)
        values = build_default_toplevel_resource(CephFSPersistentVolumeSource, "cephfs", values, spec)
        values = build_default_toplevel_resource(CinderPersistentVolumeSource, "cinder", values, spec)
        values = build_default_toplevel_resource(CSIPersistentVolumeSource, "csi", values, spec)
        values = build_default_toplevel_resource(FCVolumeSource, "fc", values, spec)
        values = build_default_toplevel_resource(FlexPersistentVolumeSource, "flexVolume", values, spec)
        values = build_default_toplevel_resource(FlockerVolumeSource, "flocker", values, spec)
        values = build_default_toplevel_resource(GCEPersistentDiskVolumeSource, "gcePersistentDisk", values, spec)
        values = build_default_toplevel_resource(GlusterfsPersistentVolumeSource, "glusterfs", values, spec)
        values = build_default_toplevel_resource(HostPathVolumeSource, "hostPath", values, spec)
        values = build_default_toplevel_resource(ISCSIPersistentVolumeSource, "iscsi", values, spec)
        values = build_default_toplevel_resource(LocalVolumeSource, "local", values, spec)
        values = build_default_toplevel_resource(NFSVolumeSource, "nfs", values, spec)
        values = build_default_toplevel_resource(PhotonPersistentDiskVolumeSource, "photonPersistentDisk", values, spec)
        values = build_default_toplevel_resource(PortworxVolumeSource, "portworxVolume", values, spec)
        values = build_default_toplevel_resource(QuobyteVolumeSource, "quobyte", values, spec)
        values = build_default_toplevel_resource(RBDPersistentVolumeSource, "rbd", values, spec)
        values = build_default_toplevel_resource(ScaleIOPersistentVolumeSource, "scaleIO", values, spec)
        values = build_default_toplevel_resource(StorageOSPersistentVolumeSource, "storageos", values, spec)
        values = build_default_toplevel_resource(VsphereVirtualDiskVolumeSource, "vsphereVolume", values, spec)
        values = build_default_toplevel_resource(VolumeNodeAffinity, "nodeAffinity", values, spec)

        values["accessModes"] = spec.get("accessModes")

        # We define it as a generic dictionary, but we store it in the DB as a string.
        # We need to deserialize it by converting it back into a dictionary when validating.
        capacity = spec.get("capacity")
        if capacity is not None and isinstance(capacity, str):
            capacity = json.loads(capacity)

        values["capacity"] = capacity
        values["mountOptions"] = spec.get("mountOptions")
        values["persistentVolumeReclaimPolicy"] = spec.get("persistentVolumeReclaimPolicy")
        values["storageClassName"] = spec.get("storageClassName")
        values["volumeMode"] = spec.get("volumeMode")

        return values

    @property
    def db_labels(self) -> Dict[str, Any]:
        labels = {
            **super().db_labels,
            **{k: (v["objHash"] if v is not None and "objHash" in v else v) for k, v in self.model_dump().items()}
        }

        # No support for Maps in neo4j, so we need to convert capacity to a string
        labels["capacity"] = json.dumps(labels["capacity"])
        return labels
    
    @property
    def referenced_objects(self):
        objects = [
            self.awsElasticBlockStore,
            self.azureDisk,
            self.azureFile,
            self.cephfs,
            self.cinder,
            self.csi,
            self.fc,
            self.flexVolume,
            self.flocker,
            self.gcePersistentDisk,
            self.glusterfs,
            self.hostPath,
            self.iscsi,
            self.local,
            self.nfs,
            self.photonPersistentDisk,
            self.portworxVolume,
            self.quobyte,
            self.rbd,
            self.scaleIO,
            self.storageos,
            self.vsphereVolume,
            self.nodeAffinity
        ]
        return objects
    
    def relationships(self, initial: bool = True) -> List[RELATIONSHIP]:
        # I don't know how to make this work via inheritance, so we're copy and pasting it around for now
        return [(self, Relationship.DEFINES, i) for i in self.referenced_objects if i is not None]
