"""Unit tests for the BaSyx registration behaviour in basyx_utils.register."""

# pylint: disable=too-few-public-methods

import asyncio

import httpx
from basyx.aas import model

from basyx_utils import register


class FakeResponse:
    """Minimal stand-in for an httpx.Response."""

    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class FakeBaSyxClient:
    """Replays queued responses/exceptions and records every call."""

    def __init__(self, results=None) -> None:
        self.results = list(results) if results is not None else []
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    async def add_aas_to_basyx(self, _repo_url, aas):
        """Record the AAS registration call and replay the next queued result."""
        self.calls.append(("aas", aas.id))
        return await self._next()

    async def add_submodel_to_basyx(self, _repo_url, submodel):
        """Record the Submodel registration call and replay the next queued result."""
        self.calls.append(("submodel", submodel.id))
        return await self._next()

    async def close(self) -> None:
        """Mark the client as closed."""
        self.closed = True

    async def _next(self):
        if not self.results:
            return FakeResponse(201)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def _build_aas_and_submodels(count: int = 2):
    aas = model.AssetAdministrationShell(
        id_=model.Identifier("urn:example:aas"),
        id_short="AAS_Test",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=model.Identifier("urn:example:aas"),
        ),
    )
    submodels = [
        model.Submodel(id_=model.Identifier(f"urn:example:submodel:{index}"), id_short=f"SM{index}")
        for index in range(count)
    ]
    for submodel in submodels:
        aas.submodel.add(model.ModelReference.from_referable(submodel))
    return aas, submodels


def _fast_retries(monkeypatch) -> None:
    """Keep retry behaviour but without waiting, so the tests run instantly."""
    monkeypatch.setattr(register, "BASYX_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(register, "BASYX_RETRY_BASE_DELAY", 0.0)


def test_transport_errors_are_retried_and_reported_as_false(monkeypatch) -> None:
    """A BaSyx backend that is unreachable must not raise out of the event loop."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(1)
    client = FakeBaSyxClient([httpx.ConnectError("connection refused") for _ in range(50)])

    result = asyncio.run(register.register_in_basyx(aas, submodels, client))

    assert result is False
    # 2 attempts for the AAS and 2 attempts for the single submodel
    assert len([call for call in client.calls if call[0] == "aas"]) == 2
    assert len([call for call in client.calls if call[0] == "submodel"]) == 2


def test_server_errors_are_retried_until_success(monkeypatch) -> None:
    """A 5xx response is retried and a following success is reported as True."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(1)
    client = FakeBaSyxClient([FakeResponse(503, "unavailable"), FakeResponse(201), FakeResponse(201)])

    result = asyncio.run(register.register_in_basyx(aas, submodels, client))

    assert result is True
    assert [call[0] for call in client.calls] == ["aas", "aas", "submodel"]


def test_client_errors_are_reported_once_without_retry(monkeypatch) -> None:
    """Validation errors (4xx) do not fix themselves, so they are not retried."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(1)
    client = FakeBaSyxClient([FakeResponse(400, "idShort is not valid"), FakeResponse(201)])

    result = asyncio.run(register.register_in_basyx(aas, submodels, client))

    assert result is False
    assert [call[0] for call in client.calls] == ["aas", "submodel"]


def test_rejected_submodel_makes_the_whole_registration_fail(monkeypatch) -> None:
    """The result reports whether the AAS and every submodel were accepted."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(2)
    client = FakeBaSyxClient([FakeResponse(201), FakeResponse(201), FakeResponse(409, "conflict")])

    result = asyncio.run(register.register_in_basyx(aas, submodels, client))

    assert result is False


def test_self_created_client_is_closed(monkeypatch) -> None:
    """Without a shared client, the temporary client is closed again."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(1)
    created: list[FakeBaSyxClient] = []

    def _fake_client_factory() -> FakeBaSyxClient:
        client = FakeBaSyxClient()
        created.append(client)
        return client

    monkeypatch.setattr(register, "AsyncBaSyxClient", _fake_client_factory)

    result = asyncio.run(register.register_in_basyx(aas, submodels))

    assert result is True
    assert len(created) == 1
    assert created[0].closed is True


def test_shared_client_is_not_closed(monkeypatch) -> None:
    """A shared client belongs to the caller and stays open for the next event."""
    _fast_retries(monkeypatch)
    aas, submodels = _build_aas_and_submodels(1)
    client = FakeBaSyxClient()

    result = asyncio.run(register.register_in_basyx(aas, submodels, client))

    assert result is True
    assert client.closed is False
