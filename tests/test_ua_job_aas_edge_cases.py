"""Edge-case and recursion tests for ISA95 mapping helpers in ua_job_aas."""

# pylint: disable=protected-access

from basyx.aas import model

import ua_job_aas


def _find_by_id_short(elements, id_short: str):
    for element in elements:
        if getattr(element, "id_short", None) == id_short:
            return element
    raise AssertionError(f"Element with id_short='{id_short}' not found")


def _collection_property_value(collection: model.SubmodelElementCollection, prop_name: str):
    prop = _find_by_id_short(collection.value, prop_name)
    return prop.value


def test_parameter_value_type_mapping_bool_int_float_string() -> None:
    """Maps Python scalar types to the expected ISA95 Property value types."""
    bool_coll = ua_job_aas._create_isa95_parameter_collection({"ID": "B", "Value": True}, None)
    int_coll = ua_job_aas._create_isa95_parameter_collection({"ID": "I", "Value": 42}, None)
    float_coll = ua_job_aas._create_isa95_parameter_collection({"ID": "F", "Value": 12.5}, None)
    str_coll = ua_job_aas._create_isa95_parameter_collection({"ID": "S", "Value": "abc"}, None)

    bool_value = _find_by_id_short(bool_coll.value, "Value")
    int_value = _find_by_id_short(int_coll.value, "Value")
    float_value = _find_by_id_short(float_coll.value, "Value")
    str_value = _find_by_id_short(str_coll.value, "Value")

    assert bool_value.value_type is model.datatypes.Boolean
    assert int_value.value_type is model.datatypes.Integer
    assert float_value.value_type is model.datatypes.Double
    assert str_value.value_type is model.datatypes.String


def test_parameter_subparameters_recursion_depth_two() -> None:
    """Creates nested Subparameters collections recursively to depth two."""
    parameter = {
        "ID": "root",
        "Value": 1,
        "Subparameters": [
            {
                "ID": "child",
                "Value": 2,
                "Subparameters": [
                    {"ID": "grandchild", "Value": 3},
                ],
            }
        ],
    }

    root_coll = ua_job_aas._create_isa95_parameter_collection(parameter, None)
    subparams_list = _find_by_id_short(root_coll.value, "Subparameters")

    assert len(subparams_list.value) == 1
    child_coll = list(subparams_list.value)[0]
    assert _collection_property_value(child_coll, "ID") == "child"

    grandchild_list = _find_by_id_short(child_coll.value, "Subparameters")
    assert len(grandchild_list.value) == 1
    grandchild_coll = list(grandchild_list.value)[0]
    assert _collection_property_value(grandchild_coll, "ID") == "grandchild"


def test_property_subproperties_recursion() -> None:
    """Creates nested Subproperties collections recursively."""
    property_data = {
        "ID": "p_root",
        "Value": "v0",
        "Subproperties": [
            {
                "ID": "p_child",
                "Value": "v1",
                "Subproperties": [{"ID": "p_grandchild", "Value": "v2"}],
            }
        ],
    }

    root = ua_job_aas._create_isa95_property_collection(property_data, None)
    subprops = _find_by_id_short(root.value, "Subproperties")

    assert len(subprops.value) == 1
    child = list(subprops.value)[0]
    assert _collection_property_value(child, "ID") == "p_child"

    child_subprops = _find_by_id_short(child.value, "Subproperties")
    assert len(child_subprops.value) == 1
    grandchild = list(child_subprops.value)[0]
    assert _collection_property_value(grandchild, "ID") == "p_grandchild"


def test_material_collection_with_minimal_identifiers_and_properties() -> None:
    """Builds minimal material collection with class id and property list."""
    material = {
        "MaterialClassID": "class-1",
        "Properties": [
            {"ID": "density", "Value": 7.9},
        ],
    }

    coll = ua_job_aas._create_isa95_material_collection(material, None)

    assert _collection_property_value(coll, "MaterialClassID") == "class-1"
    props_list = _find_by_id_short(coll.value, "Properties")
    assert len(props_list.value) == 1


def test_job_response_defaults_when_optional_sections_missing() -> None:
    """Keeps optional JobResponse sections present even when payload omits them."""
    aas = model.AssetAdministrationShell(
        id_=model.Identifier("AAS_Test"),
        id_short="AAS_Test",
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=model.Identifier("AAS_Test"),
        ),
    )

    job_data = {
        "JobOrder": {"JobOrderID": "job-defaults"},
        "JobResponse": {"JobResponseID": "resp-defaults", "JobOrderID": "job-defaults"},
    }

    submodel = ua_job_aas.add_job_response_submodel(job_data, aas)

    assert submodel.id_short == "JobResponse"
    assert _find_by_id_short(submodel.submodel_element, "JobResponseData") is not None
    assert _find_by_id_short(submodel.submodel_element, "PersonnelActuals") is not None
    assert _find_by_id_short(submodel.submodel_element, "EquipmentActuals") is not None
    assert _find_by_id_short(submodel.submodel_element, "PhysicalAssetActuals") is not None
    assert _find_by_id_short(submodel.submodel_element, "MaterialActuals") is not None
