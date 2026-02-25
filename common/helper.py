import base64


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
