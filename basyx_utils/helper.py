"""Status-code mappings for BaSyx registration responses."""

AAS_HTTP_STATUS_CODES = {
    200: "OK",
    201: "Asset Administration Shell Descriptor created successfully",
    204: "Asset Administration Shell Descriptor updated successfully",
    400: "Bad Request, e.g. the request parameters of the format of the request body is wrong",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: (
        "Conflict, a resource which shall be created exists already. "
        "Might be thrown if a Submodel or SubmodelElement with the same ShortId is contained in a POST request"
    ),
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

SM_HTTP_STATUS_CODES = {
    200: "OK",
    201: "Submodel created successfully",
    204: "Submodel updated successfully",
    400: "Bad Request, e.g. the request parameters of the format of the request body is wrong",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: (
        "Conflict, a resource which shall be created exists already. "
        "Might be thrown if a Submodel or SubmodelElement with the same ShortId is contained in a POST request"
    ),
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}
