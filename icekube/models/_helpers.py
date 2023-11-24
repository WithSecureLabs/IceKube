from typing import Any, Dict

from kubernetes.client import ApiClient


def to_dict(resource) -> Dict[str, Any]:
    resp: Dict[str, Any] = ApiClient().sanitize_for_serialization(resource)
    return resp
