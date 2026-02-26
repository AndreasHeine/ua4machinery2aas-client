"""
Async BaSyx Client using httpx for async HTTP requests.
"""

from basyx.aas import model
import basyx.aas.adapter.json
import httpx
import json 
from typing import Optional
from common.helper import utf8_base64_url_encode


class AsyncBaSyxClient:
    """
    Async BaSyx client for managing Asset Administration Shells and Submodels.
    Uses httpx for async HTTP requests with proper session management.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the async BaSyx client.

        Args:
            timeout (float): Request timeout in seconds. Default: 30.0
        """
        self.headers = {
            "Content-Type": "application/json"
        }
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the httpx client, creating it if necessary."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the client session."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def set_headers(self, headers: dict):
        """
        Set custom headers for the client.

        Args:
            headers (dict): A dictionary of headers to set
        """
        self.headers = headers

    def update_headers(self, headers: dict):
        """
        Update existing headers with new values.

        Args:
            headers (dict): A dictionary of headers to update
        """
        self.headers.update(headers)

    def reset_headers(self):
        """Reset headers to the default Content-Type."""
        self.headers = {
            "Content-Type": "application/json"
        }

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

    async def add_aas_to_basyx(self, aas_repo_url: str, aas: model.AssetAdministrationShell,
                               overwrite_existing: bool = True) -> httpx.Response:
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
        return await self.client.put(submodel_repo_url, content=data, headers=self.headers)

    async def add_submodel_to_basyx(self, submodel_repo_url: str, submodel: model.Submodel,
                                    overwrite_existing: bool = True) -> httpx.Response:
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
            url = f"{submodel_repo_url}/{utf8_base64_url_encode(submodel.id)}"
            return await self.put_submodel(url, submodel)
        return res

    async def update_submodelelement_in_basyx(self, submodel_repo_url: str, submodel_id: str,
                                              submodel_element: model.SubmodelElement) -> httpx.Response:
        """
        Updates a Submodel Element via PATCH at the BaSyx endpoint.

        Args:
            submodel_repo_url (str): The URL of the Submodel repository endpoint e.g. http://localhost:8081/submodels
            submodel_id (str): The ID of the Submodel containing the element to update e.g. "Machinery Job Response asdf"
            submodel_element (basyx.aas.model.SubmodelElement): The Submodel Element to be updated

        Returns:
            httpx.Response: The HTTP response from the server

        Raises:
            TypeError: If the SubmodelElement is an abstract type or unknown
        """
        if isinstance(submodel_element, model.Property):
            body = submodel_element.value
        elif isinstance(submodel_element, model.DataElement):
            raise TypeError("DataElement is Abstract!")
        elif isinstance(submodel_element, model.SubmodelElement):
            raise TypeError("SubmodelElement is Abstract!")
        else:
            raise TypeError("Unknown SubmodelElement type!")

        # Example: "http://localhost:8081/submodels/TWFjaGluZXJ5IEpvYiBSZXNwb25zZSBhc2Rm/submodel-elements/timestamp/$value"
        url = f"{submodel_repo_url}/{utf8_base64_url_encode(submodel_id)}/submodel-elements/{submodel_element.id_short}/$value"
        data = json.dumps(body, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        return await self.client.patch(url, content=data, headers=self.headers)

    async def update_submodel_property_in_basyx(self, submodel_repo_url: str, submodel_id: str,
                                                property: model.Property) -> httpx.Response:
        """
        Updates a Property of a Submodel via PATCH at the BaSyx endpoint.

        Args:
            submodel_repo_url (str): The URL of the Submodel repository endpoint e.g. http://localhost:8081/submodels
            submodel_id (str): The ID of the Submodel containing the Property to update e.g. "Machinery Job Response asdf"
            property (basyx.aas.model.Property): The Property to be updated

        Returns:
            httpx.Response: The HTTP response from the server
        """
        return await self.update_submodelelement_in_basyx(submodel_repo_url, submodel_id, property)

    async def add_submodel_reference_to_aas_in_basyx(self, aas_repo_url: str, aas_id: str,
                                                     submodel: model.Submodel) -> httpx.Response:
        """
        Posts a Submodel Reference to the BaSyx endpoint.

        Args:
            aas_repo_url (str): The URL of the AAS repository endpoint e.g. http://localhost:8081/shells
            aas_id (str): The ID of the AAS to which the Submodel Reference will be added e.g. "asdf"
            submodel (basyx.aas.model.Submodel): The Submodel to create a reference for

        Returns:
            httpx.Response: The HTTP response from the server
        """
        url = f"{aas_repo_url}/{utf8_base64_url_encode(aas_id)}/submodel-refs"
        submodel_ref = model.ModelReference.from_referable(submodel)
        data = json.dumps(submodel_ref, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)
        return await self.client.post(url, content=data, headers=self.headers)
