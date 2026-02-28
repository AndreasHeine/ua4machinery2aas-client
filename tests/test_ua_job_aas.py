"""Unit tests for Job AAS mapping functions."""

import asyncio

from basyx.aas import model

import ua_job_aas


def _new_aas(aas_id: str = "TestAAS") -> model.AssetAdministrationShell:
    return model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=f"AAS_{aas_id}",
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


def _collection_property_value(collection: model.SubmodelElementCollection, prop_name: str):
    prop = _find_by_id_short(collection.value, prop_name)
    return prop.value


def test_add_job_order_submodel_maps_workmaster_and_parameters() -> None:
    aas = _new_aas("JobOrderAAS")
    job_data = {
        "JobOrder": {
            "JobOrderID": "job-001",
            "Description": [{"Text": "Order Description", "Locale": "en"}],
            "WorkMasterID": [
                {"ID": "1", "Description": None},
                {"ID": "2", "Description": "Alt workmaster"},
            ],
            "Priority": 7,
            "JobOrderParameters": [
                {
                    "ID": "Speed",
                    "Value": 1200,
                    "Description": [{"Text": "rpm", "Locale": "en"}],
                    "Subparameters": [{"ID": "Tolerance", "Value": 10}],
                }
            ],
            "MaterialRequirements": [
                {"MaterialDefinitionID": "MAT-42", "Quantity": "12.5"}
            ],
        }
    }

    submodel = ua_job_aas.add_job_order_submodel(job_data, aas)

    assert submodel.id_short == "JobOrder"

    workmaster_list = _find_by_id_short(submodel.submodel_element, "WorkMasterID")
    assert len(workmaster_list.value) == 2
    assert _collection_property_value(list(workmaster_list.value)[0], "ID") == "1"
    assert _collection_property_value(list(workmaster_list.value)[1], "ID") == "2"

    parameter_list = _find_by_id_short(submodel.submodel_element, "JobOrderParameters")
    assert len(parameter_list.value) == 1
    parameter_collection = list(parameter_list.value)[0]
    assert _collection_property_value(parameter_collection, "ID") == "Speed"

    material_list = _find_by_id_short(submodel.submodel_element, "MaterialRequirements")
    assert len(material_list.value) == 1


def test_add_job_state_submodel_creates_grouped_job_state_list() -> None:
    aas = _new_aas("JobStateAAS")
    job_data = {
        "JobOrder": {"JobOrderID": "job-002"},
        "JobState": [
            {"StateText": {"Text": "Running", "Locale": "en-EN"}, "StateNumber": 3},
            {"StateText": {"Text": "Finished", "Locale": "en-EN"}, "StateNumber": 5},
        ],
    }

    submodel = ua_job_aas.add_job_state_submodel(job_data, aas)
    state_list = _find_by_id_short(submodel.submodel_element, "JobStateList")

    assert len(state_list.value) == 2
    first_entry = list(state_list.value)[0]
    assert _collection_property_value(first_entry, "StateText") == "Running"
    assert _collection_property_value(first_entry, "StateNumber") == 3


def test_add_job_response_submodel_maps_actuals_and_parameters() -> None:
    aas = _new_aas("JobResponseAAS")
    job_data = {
        "JobOrder": {"JobOrderID": "job-003"},
        "JobResponse": {
            "JobResponseID": "resp-003",
            "JobOrderID": "job-003",
            "JobResponseData": [{"ID": "Temp", "Value": 36.5}],
            "PersonnelActuals": [{"ID": "person-1", "Quantity": "1"}],
            "EquipmentActuals": [{"ID": "eq-1", "Quantity": "1"}],
            "PhysicalAssetActuals": [{"ID": "asset-1", "Quantity": "1"}],
            "MaterialActuals": [{"MaterialDefinitionID": "mat-1", "Quantity": "2.0"}],
        },
    }

    submodel = ua_job_aas.add_job_response_submodel(job_data, aas)

    response_data_list = _find_by_id_short(submodel.submodel_element, "JobResponseData")
    personnel_actuals = _find_by_id_short(submodel.submodel_element, "PersonnelActuals")
    equipment_actuals = _find_by_id_short(submodel.submodel_element, "EquipmentActuals")
    physical_assets = _find_by_id_short(submodel.submodel_element, "PhysicalAssetActuals")
    materials = _find_by_id_short(submodel.submodel_element, "MaterialActuals")

    assert len(response_data_list.value) == 1
    assert len(personnel_actuals.value) == 1
    assert len(equipment_actuals.value) == 1
    assert len(physical_assets.value) == 1
    assert len(materials.value) == 1


def test_create_aas_for_job_calls_register_with_three_submodels(monkeypatch) -> None:
    captured = {}

    async def _fake_register(aas, submodels):
        captured["aas"] = aas
        captured["submodels"] = submodels

    monkeypatch.setattr(ua_job_aas, "register_in_basyx", _fake_register)

    payload = {
        "JobOrder": {"JobOrderID": "job-004", "WorkMasterID": [{"ID": "1"}]},
        "JobState": [{"StateText": {"Text": "Queued"}, "StateNumber": 1}],
        "JobResponse": {"JobResponseID": "resp-004", "JobOrderID": "job-004"},
    }

    asyncio.run(ua_job_aas.create_aas_for_job(payload))

    assert "aas" in captured
    assert len(captured["submodels"]) == 3
    assert [submodel.id_short for submodel in captured["submodels"]] == ["JobOrder", "JobState", "JobResponse"]
