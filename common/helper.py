"""Common helper functions for ID normalization and OPC UA value serialization."""

import base64
import datetime
import uuid
from typing import Any

from asyncua import ua


NODEID_TYPE_TO_PREFIX: dict[ua.NodeIdType, str] = {
    ua.NodeIdType.Numeric: "i",
    ua.NodeIdType.String: "s",
    ua.NodeIdType.Guid: "g",
    ua.NodeIdType.ByteString: "b",
    ua.NodeIdType.TwoByte: "i",
    ua.NodeIdType.FourByte: "i",
}


def utf8_base64_url_encode(text: str) -> str:
    """
    Encodes text as UTF-8 and then as URL-safe Base64 string.

    Args:
        text (str): The text to be encoded

    Returns:
        str: The Base64-URL-encoded string without padding characters
    """
    utf8_bytes = text.encode("utf-8")
    base64_bytes = base64.urlsafe_b64encode(utf8_bytes)
    base64_url_encoded = base64_bytes.decode("utf-8")
    return base64_url_encoded.rstrip("=")


def ensure_list(value: Any) -> list:
    """
    Normalize an OPC UA field value into a list.

    OPC UA structures may carry an array field as a real list, as a single
    structure (array of length one) or as ``None``. All three are mapped to a
    list so downstream code only has to handle one shape.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def pick_field(data: dict, *field_names: str) -> Any:
    """
    Return the value of the first field that is present in ``data``.

    Used for field names that differ between information models (e.g. OPC UA for
    ISA-95 names the job state array ``State`` while other servers call it
    ``JobState``).
    """
    for field_name in field_names:
        if data.get(field_name) is not None:
            return data[field_name]
    return None


def as_int_or_none(value: Any) -> int | None:
    """Convert numeric-ish values to int, returning None when that is not possible."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def make_expanded_nodeid_from_string(nodeid_string: str, namespace_array: list[str]) -> ua.ExpandedNodeId:
    """
    Parses an OPC UA NodeId/ExpandedNodeId string and returns an ExpandedNodeId.

    Supported forms:
      - ``ns=<namespaceindex>;<type>=<value>``
      - ``srv=<serverindex>;ns=<namespaceindex>;<type>=<value>``
      - ``nsu=<uri>;<type>=<value>``
      - ``srv=<serverindex>;nsu=<uri>;<type>=<value>``

    Identifier type mapping:
      - ``i``: Numeric
      - ``s``: String
      - ``g``: Guid
      - ``b``: ByteString (Base64, with ASCII fallback)
    """
    normalized_nodeid_string = nodeid_string.replace("svr=", "srv=")
    has_namespace_index = any(part.strip().startswith("ns=") for part in normalized_nodeid_string.split(";"))

    try:
        parsed_nodeid = ua.NodeId.from_string(normalized_nodeid_string)
    except Exception as exc:
        raise ValueError(
            f"OPC-UA-Client: make_expanded_nodeid_from_string - Could not parse string: {nodeid_string}"
        ) from exc

    if isinstance(parsed_nodeid, ua.ExpandedNodeId):
        expanded_nodeid = parsed_nodeid
    else:
        expanded_nodeid = ua.ExpandedNodeId(
            Identifier=parsed_nodeid.Identifier,
            NamespaceIndex=parsed_nodeid.NamespaceIndex,
            NodeIdType=parsed_nodeid.NodeIdType,
            NamespaceUri=None,
            ServerIndex=0,
        )

    if not has_namespace_index and expanded_nodeid.NamespaceUri:
        mapped_index = (
            namespace_array.index(expanded_nodeid.NamespaceUri)
            if expanded_nodeid.NamespaceUri in namespace_array
            else 0
        )
        return ua.ExpandedNodeId(
            Identifier=expanded_nodeid.Identifier,
            NamespaceIndex=mapped_index,
            NodeIdType=expanded_nodeid.NodeIdType,
            NamespaceUri=expanded_nodeid.NamespaceUri,
            ServerIndex=expanded_nodeid.ServerIndex,
        )

    return expanded_nodeid


def make_nodeid_string_from_expanded_nodeid(enid: ua.ExpandedNodeId) -> str:
    """
    Converts an ExpandedNodeId into ``ns=<index>;<identifierType>=<value>`` format.
    """
    identifier_type = NODEID_TYPE_TO_PREFIX.get(enid.NodeIdType)
    if identifier_type is None:
        raise ValueError(f"Unsupported NodeIdType: {enid.NodeIdType}")

    value = enid.Identifier
    if isinstance(value, uuid.UUID):
        value = str(value)
    elif isinstance(value, bytes):
        value = base64.b64encode(value).decode("ascii")

    return f"ns={enid.NamespaceIndex};{identifier_type}={value}"


def make_nodeid_string(enid_string: str, namespace_array: list[str]) -> str:
    """
    Convert an ExpandedNodeId string into a plain NodeId string by parsing and
    normalizing namespace/index information.
    """
    enid = make_expanded_nodeid_from_string(enid_string, namespace_array)
    return make_nodeid_string_from_expanded_nodeid(enid)


def variant_to_json_serializable(variant: Any) -> Any:
    """Recursively convert OPC UA variant payloads into JSON-serializable values."""
    def _serialize(value: Any, active: set[int]) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, ua.Variant):
            return _serialize(value.Value, active)
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            # Keep a stable ISO 8601 representation instead of str(), which uses
            # a space separator and is not valid XSD dateTime.
            return value.isoformat()
        if isinstance(value, bytes):
            return base64.b64encode(value).decode("ascii")

        obj_id = id(value)

        if isinstance(value, dict):
            if obj_id in active:
                return "<circular-reference>"
            active.add(obj_id)
            try:
                return {str(key): _serialize(item, active) for key, item in value.items()}
            finally:
                active.discard(obj_id)

        if isinstance(value, (list, tuple, set)):
            if obj_id in active:
                return "<circular-reference>"
            active.add(obj_id)
            try:
                return [_serialize(item, active) for item in value]
            finally:
                active.discard(obj_id)

        if hasattr(value, "__dict__"):
            if obj_id in active:
                return "<circular-reference>"
            active.add(obj_id)
            try:
                return {
                    key: _serialize(item, active)
                    for key, item in vars(value).items()
                    if not key.startswith("_") and not callable(item)
                }
            finally:
                active.discard(obj_id)

        if hasattr(value, "__slots__"):
            if obj_id in active:
                return "<circular-reference>"
            active.add(obj_id)
            result: dict[str, Any] = {}
            try:
                for slot in value.__slots__:
                    if slot.startswith("_") or not hasattr(value, slot):
                        continue
                    item = getattr(value, slot)
                    if callable(item):
                        continue
                    result[slot] = _serialize(item, active)
            finally:
                active.discard(obj_id)
            return result

        return str(value)

    return _serialize(variant, set())
