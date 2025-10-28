"""解决FastAPI中使用Union类型时，OpenAPI文档中显示为anyOf的问题

"""
from typing import Any, Dict

def change_union_serialization(d: Dict[str, Any]):
    """用OneOF替换anyOf

    """
    if "anyOf" in d:
        d["oneOf"] = d["anyOf"]
        del d["anyOf"]

    for child in d.values():
        if isinstance(child, dict):
            change_union_serialization(child)

    return d
