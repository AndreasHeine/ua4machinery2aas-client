import httpx
from basyx.aas import model
from basyx.client import AsyncBaSyxClient


async def post_aas_async(aas_repo_url: str, aas: model.AssetAdministrationShell) -> httpx.Response:
    """
    Async version of post_aas. Posts an Asset Administration Shell to the BaSyx endpoint.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.post_aas(aas_repo_url, aas)


async def add_aas_to_basyx_async(aas_repo_url: str, aas: model.AssetAdministrationShell,
                                 overwrite_existing: bool = True) -> httpx.Response:
    """
    Async version of add_aas_to_basyx. Adds an Asset Administration Shell to the BaSyx repository.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.add_aas_to_basyx(aas_repo_url, aas, overwrite_existing)


async def add_submodel_to_basyx_async(submodel_repo_url: str, submodel: model.Submodel,
                                      overwrite_existing: bool = True) -> httpx.Response:
    """
    Async version of add_submodel_to_basyx. Adds a Submodel to the BaSyx repository.

    Note: Creates a new client for each request. For multiple requests, use AsyncBaSyxClient.
    """
    async with AsyncBaSyxClient() as client:
        return await client.add_submodel_to_basyx(submodel_repo_url, submodel, overwrite_existing)
