"""Functions to register AAS and Submodels in BaSyx repositories."""

import asyncio
from typing import Awaitable, Callable, Optional

import httpx
from basyx.aas import model

from basyx_utils.client import AsyncBaSyxClient
from basyx_utils.helper import AAS_HTTP_STATUS_CODES, SM_HTTP_STATUS_CODES
from config import AAS_ENV_REPO_PATH, BASYX_MAX_ATTEMPTS, BASYX_RETRY_BASE_DELAY, SUBMODEL_ENV_REPO_PATH

SUCCESS_STATUS_CODES: tuple[int, ...] = (200, 201, 204)
RETRYABLE_STATUS_CODES: tuple[int, ...] = (500, 502, 503, 504)


def _retry_delay(attempt: int) -> float:
    """Exponential backoff for the given (1-based) attempt."""
    return BASYX_RETRY_BASE_DELAY * (2 ** (attempt - 1))


async def _register_with_retry(
    request: Callable[[], Awaitable[httpx.Response]],
    kind: str,
    identifier: str,
    status_codes: dict[int, str],
) -> bool:
    """
    Run one BaSyx registration with bounded retries.

    Transport errors (connection refused, timeouts) and 5xx responses are retried.
    4xx responses are reported once with the response body, because a validation
    error does not fix itself on retry.

    Returns True when the resource was accepted by BaSyx.
    """
    for attempt in range(1, BASYX_MAX_ATTEMPTS + 1):
        try:
            res = await request()
        except httpx.TransportError as exc:
            print(f"{kind} registration for id: {identifier}, attempt {attempt}/{BASYX_MAX_ATTEMPTS} failed: {exc!r}")
            if attempt < BASYX_MAX_ATTEMPTS:
                await asyncio.sleep(_retry_delay(attempt))
            continue

        status_text = status_codes.get(res.status_code, "Unknown Status")
        if res.status_code in SUCCESS_STATUS_CODES:
            print(f"{kind} registration for id: {identifier}, status: {res.status_code} [{status_text}]")
            return True

        if res.status_code in RETRYABLE_STATUS_CODES and attempt < BASYX_MAX_ATTEMPTS:
            print(f"{kind} registration for id: {identifier}, status: {res.status_code} [{status_text}], retrying...")
            await asyncio.sleep(_retry_delay(attempt))
            continue

        print(
            f"{kind} registration for id: {identifier} rejected, status: {res.status_code} [{status_text}]\n"
            f"  response body: {res.text.strip()[:300]}"
        )
        return False

    print(f"{kind} registration for id: {identifier} failed after {BASYX_MAX_ATTEMPTS} attempts")
    return False


async def register_in_basyx(
    aas: model.AssetAdministrationShell,
    submodels: list[model.Submodel],
    client: Optional[AsyncBaSyxClient] = None,
) -> bool:
    """
    Register an AAS and its submodels in the configured BaSyx repositories.

    Args:
        aas: The Asset Administration Shell to register.
        submodels: The Submodels belonging to the AAS.
        client: Optional shared AsyncBaSyxClient. When omitted, a temporary client
            is created and closed again.

    Returns:
        bool: True when the AAS and every submodel were accepted by BaSyx.
    """
    own_client = client is None
    basyx_client = client if client is not None else AsyncBaSyxClient()
    try:
        success = await _register_with_retry(
            lambda: basyx_client.add_aas_to_basyx(AAS_ENV_REPO_PATH, aas),
            "AAS",
            aas.id,
            AAS_HTTP_STATUS_CODES,
        )
        for submodel in submodels:
            submodel_ok = await _register_with_retry(
                lambda current=submodel: basyx_client.add_submodel_to_basyx(SUBMODEL_ENV_REPO_PATH, current),
                "Submodel",
                submodel.id,
                SM_HTTP_STATUS_CODES,
            )
            success = success and submodel_ok
        return success
    finally:
        if own_client:
            await basyx_client.close()
