from typing import Any


def serialize_tool_result(obj: Any) -> Any:
    if obj is None:
        return None

    if hasattr(obj, "to_api_request_json"):
        return obj.to_api_request_json()

    if isinstance(obj, list):
        return [serialize_tool_result(item) for item in obj]

    return obj
