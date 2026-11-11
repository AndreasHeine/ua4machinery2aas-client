"""Tests for the AAS structures and BaSyx JSON output produced by ua_job_aas."""

import asyncio
import json

from basyx.aas import model
from basyx.aas.adapter.json import AASToJsonEncoder

import ua_job_aas


def _new_aas(aas_id: str = "JobAAS") -> model.AssetAdministrationShell:
    return model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short="AAS_JOBORDER",
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


def _iter_json_nodes(node):
    """Walk every object of an encoded AAS payload."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _iter_json_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_json_nodes(item)


def _nested_job_data() -> dict:
    return {
        "JobOrder": {
            "JobOrderID": "job-nested",
            "Description": [{"Text": "Order Description", "Locale": "en"}],
            "WorkMasterID": [{"ID": "1", "Description": {"Text": "Work master", "Locale": "en"}}],
            "StartTime": "2026-06-05T14:48:01+00:00",
            "EndTime": "2026-06-05T15:48:01+00:00",
            "Priority": 7,
            "JobOrderParameters": [
                {
                    "ID": "Speed",
                    "Value": 1200,
                    "Description": [{"Text": "rpm", "Locale": "en"}],
                    "EngineeringUnits": {
                        "NamespaceIndex": 1,
                        "UnitId": 5,
                        "DisplayName": [{"Text": "rpm", "Locale": "en"}],
                    },
                    "Subparameters": [{"ID": "Tolerance", "Value": 10}],
                }
            ],
            "PersonnelRequirements": [
                {
                    "ID": "person-1",
                    "PersonnelUse": "operator",
                    "Quantity": 1,
                    "Properties": [{"ID": "certification", "Value": "ISO"}],
                }
            ],
            "EquipmentRequirements": [
                {"ID": "eq-1", "EquipmentUse": "machine", "Properties": [{"ID": "vendor", "Value": "ACME"}]}
            ],
            "PhysicalAssetRequirements": [{"ID": "asset-1", "PhysicalAssetUse": "pallet"}],
            "MaterialRequirements": [
                {"MaterialDefinitionID": "MAT-42", "Quantity": 12, "Properties": [{"ID": "density", "Value": 7.9}]}
            ],
        },
        "JobState": [{"StateText": {"Text": "Running", "Locale": "en-EN"}, "StateNumber": 3}],
        "JobResponse": {
            "JobResponseID": "resp-nested",
            "JobOrderID": "job-nested",
            "Description": {"Text": "Finished", "Locale": "en"},
            "State": [{"StateText": {"Text": "Finished", "Locale": "en-EN"}, "StateNumber": 5}],
            "JobResponseData": [{"ID": "Temp", "Value": 36.5}],
            "MaterialActuals": [{"MaterialDefinitionID": "MAT-42", "Quantity": 11}],
        },
    }


def _build_submodels() -> list:
    job_data = _nested_job_data()
    aas = _new_aas("NestedJobAAS")
    return [
        ua_job_aas.add_job_order_submodel(job_data, aas),
        ua_job_aas.add_job_state_submodel(job_data, aas),
        ua_job_aas.add_job_response_submodel(job_data, aas),
    ]


def test_every_list_is_not_order_relevant() -> None:
    """BaSyx rejects idShort-less entries in ordered lists, so all lists must be unordered."""
    encoded_submodels = [json.loads(json.dumps(sm, cls=AASToJsonEncoder)) for sm in _build_submodels()]
    assert len(encoded_submodels) == 3

    total_lists = 0
    for payload in encoded_submodels:
        list_nodes = [node for node in _iter_json_nodes(payload) if node.get("modelType") == "SubmodelElementList"]
        total_lists += len(list_nodes)
        for node in list_nodes:
            assert node.get("orderRelevant") is False

    # JobOrder alone contains seven lists, so the payload is deep enough for this check.
    assert total_lists >= 10


def test_nested_payload_is_json_serializable() -> None:
    """The whole submodel can be encoded for the BaSyx JSON API."""
    for submodel in _build_submodels():
        payload = json.dumps(submodel, cls=AASToJsonEncoder)
        assert isinstance(payload, str)

    job_order = _build_submodels()[0]
    parameter_list = _find_by_id_short(job_order.submodel_element, "JobOrderParameters")
    parameter = list(parameter_list.value)[0]
    engineering_units = _find_by_id_short(parameter.value, "EngineeringUnits")
    assert _find_by_id_short(engineering_units.value, "NamespaceIndex").value == "1"
    subparameters = _find_by_id_short(parameter.value, "Subparameters")
    assert len(subparameters.value) == 1


def test_workmaster_description_keeps_localized_text_structure() -> None:
    """A LocalizedText description must not be emitted as Python dict repr."""
    job_order = _build_submodels()[0]
    workmaster_list = _find_by_id_short(job_order.submodel_element, "WorkMasterID")
    workmaster = list(workmaster_list.value)[0]

    description = _find_by_id_short(workmaster.value, "Description")
    assert isinstance(description, model.SubmodelElementCollection)
    assert _find_by_id_short(description.value, "Text").value == "Work master"
    assert _find_by_id_short(description.value, "Locale").value == "en"


def test_priority_accepts_numeric_strings_and_defaults_to_zero() -> None:
    """BaSyx rejects a String value for an Integer property, so values are converted."""
    aas = _new_aas("PriorityAAS")

    numeric_string = ua_job_aas.add_job_order_submodel(
        {"JobOrder": {"JobOrderID": "job-prio", "Priority": "7"}}, aas
    )
    non_numeric = ua_job_aas.add_job_order_submodel(
        {"JobOrder": {"JobOrderID": "job-prio", "Priority": "highest"}}, aas
    )
    missing = ua_job_aas.add_job_order_submodel({"JobOrder": {"JobOrderID": "job-prio"}}, aas)

    numeric_property = _find_by_id_short(numeric_string.submodel_element, "Priority")
    non_numeric_property = _find_by_id_short(non_numeric.submodel_element, "Priority")
    missing_property = _find_by_id_short(missing.submodel_element, "Priority")

    assert numeric_property.value_type is model.datatypes.Integer
    assert numeric_property.value == 7
    assert non_numeric_property.value_type is model.datatypes.String
    assert non_numeric_property.value == "highest"
    assert missing_property.value_type is model.datatypes.Integer
    assert missing_property.value == 0


def test_spec_field_name_state_is_accepted_for_job_state() -> None:
    """OPC UA for ISA-95 names the state array of JobOrderAndState `State`."""
    aas = _new_aas("StateNameAAS")
    job_data = {
        "JobOrder": {"JobOrderID": "job-state"},
        "State": [{"StateText": {"Text": "Queued", "Locale": "en"}, "StateNumber": 1}],
    }

    submodel = ua_job_aas.add_job_state_submodel(job_data, aas)
    state_list = _find_by_id_short(submodel.submodel_element, "JobStateList")

    assert len(state_list.value) == 1
    entry = list(state_list.value)[0]
    assert _find_by_id_short(entry.value, "StateText").value == "Queued"
    assert _find_by_id_short(entry.value, "StateNumber").value == 1


def test_workmaster_parameters_are_not_dropped() -> None:
    """ISA95WorkMasterDataType carries Parameters, so they must appear in the JobOrder submodel."""
    aas = _new_aas("WorkmasterParametersAAS")
    job_data = {
        "JobOrder": {
            "JobOrderID": "job-wm",
            "WorkMasterID": [{"ID": "1", "Parameters": [{"ID": "Feed", "Value": 12}]}],
        }
    }

    submodel = ua_job_aas.add_job_order_submodel(job_data, aas)
    workmaster_list = _find_by_id_short(submodel.submodel_element, "WorkMasterID")
    workmaster = list(workmaster_list.value)[0]

    parameters = _find_by_id_short(workmaster.value, "Parameters")
    assert len(parameters.value) == 1
    assert _find_by_id_short(list(parameters.value)[0].value, "ID").value == "Feed"


def test_event_without_job_order_is_skipped(monkeypatch, capsys) -> None:
    """An event that carries no JobOrder must not create or register anything."""
    calls = []

    async def _fake_register(aas, submodels, client=None):
        calls.append((aas, submodels, client))

    monkeypatch.setattr(ua_job_aas, "register_in_basyx", _fake_register)

    asyncio.run(ua_job_aas.create_aas_for_job({"EventType": "ns=2;i=5000", "JobState": [{"StateNumber": 1}]}))

    assert not calls
    output = capsys.readouterr().out
    assert "no usable JobOrder/JobOrderID" in output
    assert "JobState" in output


def test_missing_state_and_response_fields_are_reported(monkeypatch, capsys) -> None:
    """Silent data loss is avoided by reporting absent payload sections."""
    async def _fake_register(aas, submodels, client=None):  # pylint: disable=unused-argument
        return None

    monkeypatch.setattr(ua_job_aas, "register_in_basyx", _fake_register)

    asyncio.run(ua_job_aas.create_aas_for_job({"JobOrder": {"JobOrderID": "job-missing"}}))

    output = capsys.readouterr().out
    assert "no JobState/State field" in output
    assert "no JobResponse field" in output
