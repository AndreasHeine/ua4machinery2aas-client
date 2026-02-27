import base64
import uuid

from asyncua import ua


NODEID_TYPE_TO_PREFIX: dict[ua.NodeIdType, str] = {
    ua.NodeIdType.Numeric: 'i',
    ua.NodeIdType.String: 's',
    ua.NodeIdType.Guid: 'g',
    ua.NodeIdType.ByteString: 'b',
    ua.NodeIdType.TwoByte: 'i',
    ua.NodeIdType.FourByte: 'i',
}


def clean_id(id: str) -> str:
    """
    Cleans an ID by removing spaces and replacing hyphens with underscores.

    Args:
        id (str): The ID string to be cleaned

    Returns:
        str: The cleaned ID with spaces removed and hyphens replaced by underscores
    """
    return f"{id.replace(' ', '_').replace('-', '_')}"


def utf8_base64_url_encode(text: str) -> str:
    """
    Encodes text as UTF-8 and then as URL-safe Base64 string.

    Args:
        text (str): The text to be encoded

    Returns:
        str: The Base64-URL-encoded string without padding characters
    """
    utf8_bytes = text.encode('utf-8')
    base64_bytes = base64.urlsafe_b64encode(utf8_bytes)
    base64_url_encoded = base64_bytes.decode('utf-8')
    return base64_url_encoded.rstrip('=')


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
    normalized_nodeid_string = nodeid_string.replace('svr=', 'srv=')
    has_namespace_index = any(part.strip().startswith('ns=') for part in normalized_nodeid_string.split(';'))

    try:
        parsed_nodeid = ua.NodeId.from_string(normalized_nodeid_string)
    except Exception as exc:
        raise ValueError(f"OPC-UA-Client: make_expanded_nodeid_from_string - Could not parse string: {nodeid_string}") from exc

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
        mapped_index = namespace_array.index(expanded_nodeid.NamespaceUri) if expanded_nodeid.NamespaceUri in namespace_array else 0
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
        value = base64.b64encode(value).decode('ascii')

    return f"ns={enid.NamespaceIndex};{identifier_type}={value}"


def make_nodeid_string(enid_string: str, namespace_array: list[str]) -> str:
    """
    Combines make_expanded_nodeid_from_string and make_nodeid_string_from_expanded_nodeid to convert an ExpandedNodeId string into a NodeId string.
    """
    enid = make_expanded_nodeid_from_string(enid_string, namespace_array)
    return make_nodeid_string_from_expanded_nodeid(enid)
