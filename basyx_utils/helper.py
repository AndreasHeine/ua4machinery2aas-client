import httpx
from basyx.aas import model
from basyx_utils.client import AsyncBaSyxClient


AAS_HTTP_STATUS_CODES = {
    200: "OK",
    201: "Asset Administration Shell Descriptor created successfully",
    204: "Asset Administration Shell Descriptor updated successfully",
    400: "Bad Request, e.g. the request parameters of the format of the request body is wrong",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict, a resource which shall be created exists already. Might be thrown if a Submodel or SubmodelElement with the same ShortId is contained in a POST request",
    500: "Internal Server Error",
}

SM_HTTP_STATUS_CODES = {
    200: "OK",
    201: "Submodel created successfully",
    204: "Submodel updated successfully",
    400: "Bad Request, e.g. the request parameters of the format of the request body is wrong",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict, a resource which shall be created exists already. Might be thrown if a Submodel or SubmodelElement with the same ShortId is contained in a POST request",
    500: "Internal Server Error",
}


async def post_aas_async(aas_repo_url: str, aas: model.AssetAdministrationShell) -> httpx.Response:
    """
    Async version of post_aas. Posts an Asset Administration Shell to the BaSyx endpoint.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.post_aas(aas_repo_url, aas)


async def add_aas_to_basyx_async(
    aas_repo_url: str, aas: model.AssetAdministrationShell, overwrite_existing: bool = True
) -> httpx.Response:
    """
    Async version of add_aas_to_basyx. Adds an Asset Administration Shell to the BaSyx repository.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.add_aas_to_basyx(aas_repo_url, aas, overwrite_existing)


async def add_submodel_to_basyx_async(
    submodel_repo_url: str, submodel: model.Submodel, overwrite_existing: bool = True
) -> httpx.Response:
    """
    Async version of add_submodel_to_basyx. Adds a Submodel to the BaSyx repository.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.add_submodel_to_basyx(submodel_repo_url, submodel, overwrite_existing)
