"""
Async BaSyx Client using httpx for async HTTP requests.
"""

import json
from typing import Optional

import basyx.aas.adapter.json
import httpx
from basyx.aas import model

from common.helper import utf8_base64_url_encode
from config import AAS_REQUEST_TIMEOUT


class AsyncBaSyxClient:
    """
    Async BaSyx client for managing Asset Administration Shells and Submodels.
    Uses httpx for async HTTP requests with proper session management.

    A single instance should be reused for the lifetime of the process; creating
    a client per request wastes connections.
    """

    def __init__(self, timeout: float = AAS_REQUEST_TIMEOUT):
        """
        Initialize the async BaSyx client.

        Args:
            timeout (float): Request timeout in seconds. Default: AAS_REQUEST_TIMEOUT
        """
        self.headers = {"Content-Type": "application/json"}
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the httpx client, creating it if necessary."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the client session."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def post_aas(self, aas_repo_url: str, aas: model.AssetAdministrationShell) -> httpx.Response:
        """
        Posts an Asset Administration Shell to the BaSyx endpoint.

        Args:
            aas_repo_url (str): The URL of the AAS repository endpoint e.g. http://localhost:8081/shells
            aas (basyx.aas.model.AssetAdministrationShell): The Asset Administration Shell to be posted

        Returns:
            httpx.Response: The HTTP response from the server
        """
        data = json.dumps(aas, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        return await self.client.post(aas_repo_url, content=data, headers=self.headers)

    async def put_aas(self, aas_repo_url: str, aas: model.AssetAdministrationShell) -> httpx.Response:
        """
        Updates an Asset Administration Shell via PUT at the BaSyx endpoint.

        Args:
            aas_repo_url (str): The URL of the AAS repository endpoint e.g. http://localhost:8081/shells
            aas (basyx.aas.model.AssetAdministrationShell): The Asset Administration Shell to be updated

        Returns:
            httpx.Response: The HTTP response from the server
        """
        data = json.dumps(aas, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        url = f"{aas_repo_url}/{utf8_base64_url_encode(aas.id)}"
        return await self.client.put(url, content=data, headers=self.headers)

    async def add_aas_to_basyx(
        self, aas_repo_url: str, aas: model.AssetAdministrationShell, overwrite_existing: bool = True
    ) -> httpx.Response:
        """
        Adds an Asset Administration Shell to the BaSyx repository or overwrites an existing one.

        Args:
            aas_repo_url (str): The URL of the AAS repository endpoint e.g. http://localhost:8081/shells
            aas (basyx.aas.model.AssetAdministrationShell): The Asset Administration Shell to be added
            overwrite_existing (bool, optional): Whether to overwrite existing AAS. Default: True

        Returns:
            httpx.Response: The HTTP response from the server
        """
        res = await self.post_aas(aas_repo_url, aas)
        if res.status_code == 409 and overwrite_existing:
            # "/shells/{aasIdentifier}" - Updates an existing Asset Administration Shell
            return await self.put_aas(aas_repo_url, aas)
        return res

    async def post_submodel(self, submodel_repo_url: str, submodel: model.Submodel) -> httpx.Response:
        """
        Posts a Submodel to the BaSyx endpoint.

        Args:
            submodel_repo_url (str): The URL of the Submodel repository endpoint e.g. http://localhost:8081/submodels
            submodel (basyx.aas.model.Submodel): The Submodel to be posted

        Returns:
            httpx.Response: The HTTP response from the server
        """
        data = json.dumps(submodel, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        return await self.client.post(submodel_repo_url, content=data, headers=self.headers)

    async def put_submodel(self, submodel_repo_url: str, submodel: model.Submodel) -> httpx.Response:
        """
        Updates a Submodel via PUT at the BaSyx endpoint.

        Args:
            submodel_repo_url (str): The URL of the Submodel repository endpoint e.g. http://localhost:8081/submodels
            submodel (basyx.aas.model.Submodel): The Submodel to be updated

        Returns:
            httpx.Response: The HTTP response from the server
        """
        data = json.dumps(submodel, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        url = f"{submodel_repo_url}/{utf8_base64_url_encode(submodel.id)}"
        return await self.client.put(url, content=data, headers=self.headers)

    async def add_submodel_to_basyx(
        self, submodel_repo_url: str, submodel: model.Submodel, overwrite_existing: bool = True
    ) -> httpx.Response:
        """
        Adds a Submodel to the BaSyx repository or overwrites an existing one.

        Args:
            submodel_repo_url (str): The URL of the Submodel repository endpoint e.g. http://localhost:8081/submodels
            submodel (basyx.aas.model.Submodel): The Submodel to be added
            overwrite_existing (bool, optional): Whether to overwrite existing Submodel. Default: True

        Returns:
            httpx.Response: The HTTP response from the server
        """
        res = await self.post_submodel(submodel_repo_url, submodel)
        if res.status_code == 409 and overwrite_existing:
            # "/submodels/{submodelIdentifier}" - Updates an existing Submodel
            return await self.put_submodel(submodel_repo_url, submodel)
        return res
