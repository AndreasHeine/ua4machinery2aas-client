"""Transformation of OPC UA job event payloads into BaSyx AAS/Submodel structures."""

from typing import Any

from basyx.aas import model
from basyx_utils.client import AsyncBaSyxClient
from basyx_utils.register import register_in_basyx
from common.helper import as_int_or_none, ensure_list, pick_field, variant_to_json_serializable

INTEROP4X_HAS_ATTRIBUTE = "http://interop4X.deg/Properties/HasAttribute"


def clean_job_data(event_data: dict) -> dict:
    """Normalize OPC UA event values into JSON-serializable Python objects."""
    return {key: variant_to_json_serializable(value) for key, value in event_data.items()}


# ---------------------------------------------------------------------------
# Generic element builders
# ---------------------------------------------------------------------------


def _semantic_id() -> model.ExternalReference:
    """Semantic id used for every element produced by this mapping."""
    return model.ExternalReference(
        (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value=INTEROP4X_HAS_ATTRIBUTE),)
    )


def _string_property(id_short: str, value: Any) -> model.Property:
    """Property of type String. The value is stringified to avoid type mismatches."""
    return model.Property(
        id_short=id_short,
        value_type=model.datatypes.String,
        value=str(value),
        semantic_id=_semantic_id(),
    )


def _create_typed_property(id_short: str, value) -> model.Property:
    """Property whose AAS value type is derived from the Python value."""
    if isinstance(value, bool):
        value_type = model.datatypes.Boolean
        property_value = value
    elif isinstance(value, int):
        value_type = model.datatypes.Integer
        property_value = value
    elif isinstance(value, float):
        value_type = model.datatypes.Double
        property_value = value
    else:
        value_type = model.datatypes.String
        property_value = str(value) if value is not None else "---"

    return model.Property(
        id_short=id_short,
        value_type=value_type,
        value=property_value,
        semantic_id=_semantic_id(),
    )


def _numeric_property(id_short: str, raw_value: Any, default: int = 0) -> model.Property:
    """
    Property for values that are numeric in the OPC UA information model.

    Numeric values (including numeric strings) map to an Integer property. Missing
    values use ``default``. Non-numeric values are emitted as a String property
    instead of raising, because BaSyx rejects a value that does not match the
    declared value type.
    """
    number = as_int_or_none(raw_value)
    if number is not None:
        return _create_typed_property(id_short, number)
    if raw_value is None:
        return _create_typed_property(id_short, default)
    return _create_typed_property(id_short, str(raw_value))


def _collection(id_short: str | None, value: list[model.SubmodelElement]) -> model.SubmodelElementCollection:
    return model.SubmodelElementCollection(id_short=id_short, value=value, semantic_id=_semantic_id())


def _element_list(id_short: str, value: list[model.SubmodelElement]) -> model.SubmodelElementList:
    """
    List of SubmodelElementCollection entries.

    ``order_relevant=False`` is required: the entries carry no idShort, and BaSyx
    rejects ordered lists whose entries are addressed by idShort.
    """
    return model.SubmodelElementList(
        id_short=id_short,
        type_value_list_element=model.SubmodelElementCollection,
        order_relevant=False,
        value=value,
        semantic_id=_semantic_id(),
    )


def _localized_text_collection(id_short: str | None, localized_text: Any) -> model.SubmodelElementCollection:
    """SubmodelElementCollection with the Text (and optional Locale) of a LocalizedText."""
    text_value = "---"
    locale_value = None
    if isinstance(localized_text, dict):
        if localized_text.get("Text") is not None:
            text_value = str(localized_text.get("Text"))
        if localized_text.get("Locale") is not None:
            locale_value = str(localized_text.get("Locale"))

    elements: list[model.SubmodelElement] = [_string_property("Text", text_value)]
    if locale_value is not None:
        elements.append(_string_property("Locale", locale_value))
    return _collection(id_short, elements)


def _dict_entries(entries: Any) -> list:
    """Filter a normalized entry list down to the entries that are structures."""
    return [entry for entry in ensure_list(entries) if isinstance(entry, dict)]


def _localized_text_list(id_short: str, entries: Any) -> model.SubmodelElementList:
    """List of LocalizedText entries; entries that are not LocalizedText are skipped."""
    return _element_list(id_short, [_localized_text_collection(None, entry) for entry in _dict_entries(entries)])


def _optional_localized_text_list(id_short: str, entries: Any) -> list[model.SubmodelElement]:
    """Same as `_localized_text_list`, but yields nothing when there is no entry."""
    dict_entries = _dict_entries(entries)
    if not dict_entries:
        return []
    return [_element_list(id_short, [_localized_text_collection(None, entry) for entry in dict_entries])]


def _localized_text_element(id_short: str, value: Any) -> list[model.SubmodelElement]:
    """
    LocalizedText that may arrive either as a single structure or as an array.

    A single LocalizedText becomes a SubmodelElementCollection, an array becomes a
    SubmodelElementList. Missing values yield nothing.
    """
    if isinstance(value, dict):
        return [_localized_text_collection(id_short, value)]
    dict_entries = _dict_entries(value)
    if not dict_entries:
        return []
    if len(dict_entries) == 1:
        return [_localized_text_collection(id_short, dict_entries[0])]
    return [_element_list(id_short, [_localized_text_collection(None, entry) for entry in dict_entries])]


def _workmaster_description_element(entry: dict) -> list[model.SubmodelElement]:
    """
    Description of a work master.

    ISA95WorkMasterDataType declares Description as LocalizedText, older servers use
    a plain string; both shapes are mapped.
    """
    description = entry.get("Description")
    if description is None:
        return []
    if isinstance(description, dict):
        return [_localized_text_collection("Description", description)]
    return [_string_property("Description", description)]


def _workmaster_parameters_element(entry: dict) -> list[model.SubmodelElement]:
    """Parameters of a work master (ISA95WorkMasterDataType declares ISA95ParameterDataType[])."""
    parameters = _dict_entries(entry.get("Parameters"))
    if not parameters:
        return []
    return [
        _element_list("Parameters", [_create_isa95_parameter_collection(parameter, None) for parameter in parameters])
    ]


# ---------------------------------------------------------------------------
# ISA-95 sub structures
# ---------------------------------------------------------------------------


def _create_engineering_units_collection(id_short: str, engineering_units: dict) -> model.SubmodelElementCollection:
    """EngineeringUnits (EUInformation) as a SubmodelElementCollection."""
    value_elements: list[model.SubmodelElement] = []

    value_elements.extend(_localized_text_element("DisplayName", engineering_units.get("DisplayName")))
    value_elements.extend(_localized_text_element("Description", engineering_units.get("Description")))

    if engineering_units.get("UnitId") is not None:
        value_elements.append(_string_property("UnitId", engineering_units.get("UnitId")))

    # EUInformation provides NamespaceIndex, while some servers expose NamespaceUri.
    if engineering_units.get("NamespaceUri") is not None:
        value_elements.append(_string_property("NamespaceUri", engineering_units.get("NamespaceUri")))
    elif engineering_units.get("NamespaceIndex") is not None:
        value_elements.append(_string_property("NamespaceIndex", engineering_units.get("NamespaceIndex")))

    return _collection(id_short, value_elements)


def _optional_engineering_units(engineering_units: Any) -> list[model.SubmodelElement]:
    if not isinstance(engineering_units, dict):
        return []
    return [_create_engineering_units_collection("EngineeringUnits", engineering_units)]


def _create_isa95_parameter_collection(parameter_data: dict, id_short=None) -> model.SubmodelElementCollection:
    """ISA95ParameterDataType as a SubmodelElementCollection (recursive)."""
    subparameters = _dict_entries(parameter_data.get("Subparameters"))

    value_elements: list[model.SubmodelElement] = [
        _string_property("ID", parameter_data.get("ID", "---")),
        _create_typed_property("Value", parameter_data.get("Value", "---")),
    ]
    value_elements.extend(_optional_localized_text_list("Description", parameter_data.get("Description")))
    value_elements.extend(_optional_engineering_units(parameter_data.get("EngineeringUnits")))
    if subparameters:
        value_elements.append(
            _element_list(
                "Subparameters",
                [_create_isa95_parameter_collection(subparameter, None) for subparameter in subparameters],
            )
        )

    return _collection(id_short, value_elements)


def _create_isa95_property_collection(property_data: dict, id_short=None) -> model.SubmodelElementCollection:
    """ISA95PropertyDataType as a SubmodelElementCollection (recursive)."""
    subproperties = _dict_entries(pick_field(property_data, "Subproperties", "SubProperties"))

    property_id = property_data.get("ID")
    if property_id is None:
        property_id = property_data.get("PropertyID", "---")

    value_elements: list[model.SubmodelElement] = [
        _string_property("ID", property_id),
        _create_typed_property("Value", property_data.get("Value", "---")),
    ]
    value_elements.extend(_optional_localized_text_list("Description", property_data.get("Description")))
    value_elements.extend(_optional_engineering_units(property_data.get("EngineeringUnits")))
    if subproperties:
        value_elements.append(
            _element_list(
                "Subproperties",
                [_create_isa95_property_collection(subproperty, None) for subproperty in subproperties],
            )
        )

    return _collection(id_short, value_elements)


def _create_resource_collection(
    resource_data: dict,
    id_short: str | None,
    use_field: str,
    properties_field: str = "Properties",
) -> model.SubmodelElementCollection:
    """
    Shared shape of ISA95PersonnelDataType / ISA95EquipmentDataType /
    ISA95PhysicalAssetDataType: ID, Description, <Role>Use, Quantity, EngineeringUnits, Properties.
    """
    properties = _dict_entries(resource_data.get(properties_field))

    value_elements: list[model.SubmodelElement] = [
        _string_property("ID", resource_data.get("ID", "---")),
    ]
    value_elements.extend(_optional_localized_text_list("Description", resource_data.get("Description")))
    if resource_data.get(use_field) is not None:
        value_elements.append(_string_property(use_field, resource_data.get(use_field)))
    if resource_data.get("Quantity") is not None:
        value_elements.append(_string_property("Quantity", resource_data.get("Quantity")))
    value_elements.extend(_optional_engineering_units(resource_data.get("EngineeringUnits")))
    if properties:
        value_elements.append(
            _element_list(
                properties_field,
                [_create_isa95_property_collection(property_entry, None) for property_entry in properties],
            )
        )

    return _collection(id_short, value_elements)


def _create_isa95_material_collection(material_data: dict, id_short=None) -> model.SubmodelElementCollection:
    """ISA95MaterialDataType as a SubmodelElementCollection."""
    material_properties = _dict_entries(material_data.get("Properties"))

    value_elements: list[model.SubmodelElement] = []
    for id_field in ("MaterialClassID", "MaterialDefinitionID", "MaterialLotID", "MaterialSublotID"):
        if material_data.get(id_field) is not None:
            value_elements.append(_string_property(id_field, material_data.get(id_field)))

    value_elements.extend(_optional_localized_text_list("Description", material_data.get("Description")))
    if material_data.get("MaterialUse") is not None:
        value_elements.append(_string_property("MaterialUse", material_data.get("MaterialUse")))
    if material_data.get("Quantity") is not None:
        value_elements.append(_string_property("Quantity", material_data.get("Quantity")))
    value_elements.extend(_optional_engineering_units(material_data.get("EngineeringUnits")))
    if material_properties:
        value_elements.append(
            _element_list(
                "Properties",
                [_create_isa95_property_collection(property_entry, None) for property_entry in material_properties],
            )
        )

    if not value_elements:
        # BaSyx requires at least one element to identify the material reference.
        value_elements.append(_string_property("MaterialDefinitionID", "---"))

    return _collection(id_short, value_elements)


def _create_job_state_list(id_short: str, state_entries: list) -> model.SubmodelElementList:
    """ISA95StateDataType entries as a SubmodelElementList."""
    return _element_list(
        id_short,
        [
            _collection(
                None,
                [
                    _string_property("StateText", _state_text_value(entry.get("StateText"))),
                    _numeric_property("StateNumber", entry.get("StateNumber")),
                ],
            )
            for entry in state_entries
        ],
    )


def _state_text_value(state_text) -> str:
    """StateText is a LocalizedText in the spec, but some servers report a plain string."""
    if isinstance(state_text, dict):
        return str(state_text.get("Text", "---"))
    if state_text is None:
        return "---"
    return str(state_text)


def _job_state_entries(payload: dict) -> list:
    """State entries of a payload, tolerating the spec name `State` and a single structure."""
    return _dict_entries(pick_field(payload, "JobState", "State"))


# ---------------------------------------------------------------------------
# Job AAS
# ---------------------------------------------------------------------------


def _resolve_job_order_id(job_data: dict) -> str:
    """JobOrderID from the event payload, or an empty string when it is not present."""
    job_order = job_data.get("JobOrder")
    raw_id = job_order.get("JobOrderID") if isinstance(job_order, dict) else job_data.get("JobOrderID")
    if raw_id is None or str(raw_id).strip() == "":
        return ""
    return str(raw_id)


async def create_aas_for_job(data: dict, client: AsyncBaSyxClient | None = None) -> None:
    """Create and register all job-related submodels (order, state, response)."""
    job_data = clean_job_data(data)
    job_order = job_data.get("JobOrder")
    job_order_id = _resolve_job_order_id(job_data)

    if not isinstance(job_order, dict) or not job_order_id:
        print(
            "Event has no usable JobOrder/JobOrderID, skipping. "
            f"Received event fields: {sorted(job_data.keys())}"
        )
        return

    aas_id = job_order_id
    aas_short_id = "AAS_JOBORDER"
    aas = model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=aas_short_id,
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE, global_asset_id=(model.Identifier(aas_id))
        ),
    )

    if "JobState" not in job_data and "State" not in job_data:
        print(f"JobOrder {job_order_id}: event payload has no JobState/State field")

    if "JobResponse" not in job_data:
        print(f"JobOrder {job_order_id}: event payload has no JobResponse field")

    submodels = []
    submodels.append(add_job_order_submodel(job_data, aas))
    submodels.append(add_job_state_submodel(job_data, aas))
    submodels.append(add_job_response_submodel(job_data, aas))
    # Register AAS and Submodel in BaSyx
    await register_in_basyx(aas, submodels, client)


def add_job_order_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobOrder submodel from ISA95 job-order payload data."""
    job_order_value = job_data.get("JobOrder")
    job_order: dict = job_order_value if isinstance(job_order_value, dict) else {}
    job_order_id = _resolve_job_order_id(job_data) or "---"

    workmaster_entries = _dict_entries(pick_field(job_order, "WorkmasterId", "WorkMasterID"))
    job_order_parameters_entries = _dict_entries(job_order.get("JobOrderParameters"))
    personnel_requirements_entries = _dict_entries(job_order.get("PersonnelRequirements"))
    equipment_requirements_entries = _dict_entries(job_order.get("EquipmentRequirements"))
    physical_asset_requirements_entries = _dict_entries(job_order.get("PhysicalAssetRequirements"))
    material_requirements_entries = _dict_entries(job_order.get("MaterialRequirements"))

    submodel_id = f"JobOrder {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobOrder",
        submodel_element=[
            _string_property("JobOrderID", job_order_id),
            _localized_text_list("Description", job_order.get("Description")),
            _element_list(
                "WorkMasterID",
                [
                    _collection(
                        None,
                        [
                            _string_property("ID", entry.get("ID") if entry.get("ID") is not None else "---"),
                            *_workmaster_description_element(entry),
                            *_workmaster_parameters_element(entry),
                        ],
                    )
                    for entry in workmaster_entries
                ],
            ),
            _string_property("StartTime", job_order.get("StartTime", "---")),
            _string_property("EndTime", job_order.get("EndTime", "---")),
            _numeric_property("Priority", job_order.get("Priority", 0)),
            _element_list(
                "JobOrderParameters",
                [_create_isa95_parameter_collection(entry, None) for entry in job_order_parameters_entries],
            ),
            _element_list(
                "PersonnelRequirements",
                [
                    _create_resource_collection(entry, None, "PersonnelUse")
                    for entry in personnel_requirements_entries
                ],
            ),
            _element_list(
                "EquipmentRequirements",
                [_create_resource_collection(entry, None, "EquipmentUse") for entry in equipment_requirements_entries],
            ),
            _element_list(
                "PhysicalAssetRequirements",
                [
                    _create_resource_collection(entry, None, "PhysicalAssetUse")
                    for entry in physical_asset_requirements_entries
                ],
            ),
            _element_list(
                "MaterialRequirements",
                [_create_isa95_material_collection(entry, None) for entry in material_requirements_entries],
            ),
        ],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def add_job_state_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobState submodel from ISA95 job-state payload data."""
    job_order_id = _resolve_job_order_id(job_data) or "---"
    submodel_id = f"JobState {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobState",
        submodel_element=[_create_job_state_list("JobStateList", _job_state_entries(job_data))],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def add_job_response_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobResponse submodel from ISA95 job-response payload data."""
    job_order_value = job_data.get("JobOrder")
    job_order: dict = job_order_value if isinstance(job_order_value, dict) else {}
    job_response_value = job_data.get("JobResponse")
    job_response: dict = job_response_value if isinstance(job_response_value, dict) else {}

    job_order_id = _resolve_job_order_id(job_data) or "---"
    job_response_id = str(job_response.get("JobResponseID", "---"))

    response_job_state_entries = _job_state_entries(job_response)
    job_response_data_entries = _dict_entries(job_response.get("JobResponseData"))
    personnel_actuals_entries = _dict_entries(job_response.get("PersonnelActuals"))
    equipment_actuals_entries = _dict_entries(job_response.get("EquipmentActuals"))
    physical_asset_actuals_entries = _dict_entries(job_response.get("PhysicalAssetActuals"))
    material_actuals_entries = _dict_entries(job_response.get("MaterialActuals"))

    # Description is a LocalizedText in the spec; some servers send it as an array.
    description_elements = _localized_text_element("Description", job_response.get("Description"))

    submodel_id = f"JobResponse {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobResponse",
        submodel_element=[
            _string_property("JobResponseID", job_response_id),
            _string_property(
                "JobOrderID",
                job_response.get("JobOrderID", job_order.get("JobOrderID", "---")),
            ),
            *description_elements,
            _string_property("StartTime", job_response.get("StartTime", "---")),
            _string_property("EndTime", job_response.get("EndTime", "---")),
            _create_job_state_list("JobStateList", response_job_state_entries),
            _element_list(
                "JobResponseData",
                [_create_isa95_parameter_collection(entry, None) for entry in job_response_data_entries],
            ),
            _element_list(
                "PersonnelActuals",
                [_create_resource_collection(entry, None, "PersonnelUse") for entry in personnel_actuals_entries],
            ),
            _element_list(
                "EquipmentActuals",
                [_create_resource_collection(entry, None, "EquipmentUse") for entry in equipment_actuals_entries],
            ),
            _element_list(
                "PhysicalAssetActuals",
                [
                    _create_resource_collection(entry, None, "PhysicalAssetUse")
                    for entry in physical_asset_actuals_entries
                ],
            ),
            _element_list(
                "MaterialActuals",
                [_create_isa95_material_collection(entry, None) for entry in material_actuals_entries],
            ),
        ],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel
