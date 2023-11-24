import re


def to_camel_case(string: str) -> str:
    string = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", string)
    string = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", string)
    string = string.replace("-", "_")
    return string.lower()
