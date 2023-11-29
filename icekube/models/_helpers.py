from typing import Any, Dict

from kubernetes.client import ApiClient


def load(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    else:
        return getattr(obj, key) or default


def save(obj, key, value):
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)

    return obj


def to_dict(resource) -> Dict[str, Any]:
    resp: Dict[str, Any] = ApiClient().sanitize_for_serialization(resource)
    return resp
