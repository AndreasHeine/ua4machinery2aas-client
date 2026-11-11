"""Unit tests for the machine identification mapping in ua_machine_aas."""

import asyncio

from basyx.aas import model

import ua_machine_aas


def _new_aas(aas_id: str = "MachineAAS") -> model.AssetAdministrationShell:
    return model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short="AAS_Machine",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=model.Identifier(aas_id),
        ),
    )


def _find_by_id_short(elements, id_short: str):
    for element in elements:
        if getattr(element, "id_short", None) == id_short:
            return element
    raise AssertionError(f"Element with id_short='{id_short}' not found")


def _has_id_short(elements, id_short: str) -> bool:
    return any(getattr(element, "id_short", None) == id_short for element in elements)


def _property_of(submodel: model.Submodel, id_short: str):
    return _find_by_id_short(submodel.submodel_element, id_short)


def test_missing_product_instance_uri_does_not_raise() -> None:
    """An incomplete identification payload must not crash event processing."""
    aas = _new_aas("MachineAASMissingUri")
    submodel = ua_machine_aas.add_identification_submodel({"SerialNumber": "sn-1"}, aas)

    assert submodel.id_short == "MachineryIdentification"
    assert submodel.id == "Machinery Identification ---"
    assert _property_of(submodel, "ProductInstanceUri").value == "---"
    assert _property_of(submodel, "SerialNumber").value == "sn-1"


def test_non_numeric_integer_values_are_kept_as_strings() -> None:
    """Values that cannot be cast to int are reported as strings instead of raising."""
    aas = _new_aas("MachineAASBadIntegers")
    submodel = ua_machine_aas.add_identification_submodel(
        {
            "ProductInstanceUri": "urn:example:machine",
            "YearOfConstruction": "unknown",
            "MonthOfConstruction": "n/a",
            "RevisionCounter": "7",
        },
        aas,
    )

    year = _property_of(submodel, "YearOfConstruction")
    month = _property_of(submodel, "MonthOfConstruction")
    revision = _property_of(submodel, "RevisionCounter")

    assert year.value_type is model.datatypes.String
    assert year.value == "unknown"
    assert month.value_type is model.datatypes.String
    assert month.value == "n/a"
    assert revision.value_type is model.datatypes.Integer
    assert revision.value == 7


def test_localized_text_and_date_values_are_mapped() -> None:
    """LocalizedText values are flattened and dates use ISO 8601 strings."""
    aas = _new_aas("MachineAASLocalized")
    submodel = ua_machine_aas.add_identification_submodel(
        {
            "ProductInstanceUri": "urn:example:machine",
            "Manufacturer": {"Text": "ACME", "Locale": "en"},
            "ComponentName": {"Text": "Cell 1"},
            "Location": "Hall 2",
            "InitialOperationDate": "2026-06-05T14:48:01+00:00",
        },
        aas,
    )

    assert _property_of(submodel, "Manufacturer").value == "ACME"
    assert _property_of(submodel, "ComponentName").value == "Cell 1"
    assert _property_of(submodel, "Location").value == "Hall 2"
    assert _property_of(submodel, "InitialOperationDate").value == "2026-06-05T14:48:01+00:00"
    assert not _has_id_short(submodel.submodel_element, "Model")


def test_create_aas_for_identification_passes_shared_client(monkeypatch) -> None:
    """The shared BaSyx client is forwarded to the registration function."""
    captured = {}

    async def _fake_register(aas, submodels, client=None):
        captured["aas"] = aas
        captured["submodels"] = submodels
        captured["client"] = client

    monkeypatch.setattr(ua_machine_aas, "register_in_basyx", _fake_register)
    shared_client = object()

    asyncio.run(
        ua_machine_aas.create_aas_for_identification(
            "urn:example:machine", {"ProductInstanceUri": "urn:example:machine"}, shared_client
        )
    )

    assert captured["client"] is shared_client
    assert captured["aas"].id == "urn:example:machine"
    assert [submodel.id_short for submodel in captured["submodels"]] == ["MachineryIdentification"]
