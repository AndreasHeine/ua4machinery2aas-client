"""Transformation of OPC UA job event payloads into BaSyx AAS/Submodel structures."""

from basyx.aas import model
from basyx_utils.register import register_in_basyx
from common.helper import clean_id, variant_to_json_serializable


def clean_job_data(event_data: dict) -> dict:
    """Normalize OPC UA event values into JSON-serializable Python objects."""
    cleaned_data = {}
    for key, value in event_data.items():
        cleaned_data[key] = variant_to_json_serializable(value)
    return cleaned_data


def _create_localized_text_collection(id_short, localized_text) -> model.SubmodelElementCollection:
    text_value = "---"
    locale_value = None
    if isinstance(localized_text, dict):
        if localized_text.get("Text") is not None:
            text_value = str(localized_text.get("Text"))
        if localized_text.get("Locale") is not None:
            locale_value = str(localized_text.get("Locale"))

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=[
            model.Property(
                id_short="Text",
                value_type=model.datatypes.String,
                value=text_value,
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            *(
                [
                    model.Property(
                        id_short="Locale",
                        value_type=model.datatypes.String,
                        value=locale_value,
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                ]
                if locale_value is not None
                else []
            ),
        ],
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_typed_property(id_short: str, value) -> model.Property:
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
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_engineering_units_collection(id_short: str, engineering_units: dict) -> model.SubmodelElementCollection:
    return model.SubmodelElementCollection(
        id_short=id_short,
        value=[
            *(
                [_create_localized_text_collection("DisplayName", engineering_units.get("DisplayName"))]
                if isinstance(engineering_units.get("DisplayName"), dict)
                else []
            ),
            *(
                [_create_localized_text_collection("Description", engineering_units.get("Description"))]
                if isinstance(engineering_units.get("Description"), dict)
                else []
            ),
            *(
                [
                    model.Property(
                        id_short="UnitId",
                        value_type=model.datatypes.String,
                        value=str(engineering_units.get("UnitId")),
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                ]
                if engineering_units.get("UnitId") is not None
                else []
            ),
            *(
                [
                    model.Property(
                        id_short="NamespaceUri",
                        value_type=model.datatypes.String,
                        value=str(engineering_units.get("NamespaceUri")),
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                ]
                if engineering_units.get("NamespaceUri") is not None
                else []
            ),
        ],
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_parameter_collection(parameter_data: dict, id_short=None) -> model.SubmodelElementCollection:
    description_entries = parameter_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = parameter_data.get("EngineeringUnits")

    subparameters = parameter_data.get("Subparameters")
    if not isinstance(subparameters, list):
        subparameters = []

    value_elements = [
        model.Property(
            id_short="ID",
            value_type=model.datatypes.String,
            value=str(parameter_data.get("ID", "---")),
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                    ),
                )
            ),
        ),
        _create_typed_property("Value", parameter_data.get("Value", "---")),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Subparameters",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_parameter_collection(subparameter, None)
                        for subparameter in subparameters
                        if isinstance(subparameter, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(subparameters) > 0
            else []
        ),
    ]

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_property_collection(property_data: dict, id_short=None) -> model.SubmodelElementCollection:
    description_entries = property_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = property_data.get("EngineeringUnits")

    subproperties = property_data.get("Subproperties")
    if not isinstance(subproperties, list):
        subproperties = property_data.get("SubProperties")
    if not isinstance(subproperties, list):
        subproperties = []

    property_id = property_data.get("ID")
    if property_id is None:
        property_id = property_data.get("PropertyID", "---")

    value_elements = [
        model.Property(
            id_short="ID",
            value_type=model.datatypes.String,
            value=str(property_id),
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                    ),
                )
            ),
        ),
        _create_typed_property("Value", property_data.get("Value", "---")),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Subproperties",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_property_collection(subproperty, None)
                        for subproperty in subproperties
                        if isinstance(subproperty, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(subproperties) > 0
            else []
        ),
    ]

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_material_collection(material_data: dict, id_short=None) -> model.SubmodelElementCollection:
    description_entries = material_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = material_data.get("EngineeringUnits")

    material_properties = material_data.get("Properties")
    if not isinstance(material_properties, list):
        material_properties = []

    value_elements = [
        *(
            [
                model.Property(
                    id_short="MaterialClassID",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("MaterialClassID")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("MaterialClassID") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="MaterialDefinitionID",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("MaterialDefinitionID")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("MaterialDefinitionID") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="MaterialLotID",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("MaterialLotID")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("MaterialLotID") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="MaterialSublotID",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("MaterialSublotID")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("MaterialSublotID") is not None
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [
                model.Property(
                    id_short="MaterialUse",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("MaterialUse")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("MaterialUse") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="Quantity",
                    value_type=model.datatypes.String,
                    value=str(material_data.get("Quantity")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if material_data.get("Quantity") is not None
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Properties",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_property_collection(property_entry, None)
                        for property_entry in material_properties
                        if isinstance(property_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(material_properties) > 0
            else []
        ),
    ]

    if len(value_elements) == 0:
        value_elements.append(
            model.Property(
                id_short="MaterialDefinitionID",
                value_type=model.datatypes.String,
                value="---",
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            )
        )

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_physical_asset_collection(
    physical_asset_data: dict, id_short=None
) -> model.SubmodelElementCollection:
    description_entries = physical_asset_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = physical_asset_data.get("EngineeringUnits")

    physical_asset_properties = physical_asset_data.get("Properties")
    if not isinstance(physical_asset_properties, list):
        physical_asset_properties = []

    value_elements = [
        model.Property(
            id_short="ID",
            value_type=model.datatypes.String,
            value=str(physical_asset_data.get("ID", "---")),
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                    ),
                )
            ),
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [
                model.Property(
                    id_short="PhysicalAssetUse",
                    value_type=model.datatypes.String,
                    value=str(physical_asset_data.get("PhysicalAssetUse")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if physical_asset_data.get("PhysicalAssetUse") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="Quantity",
                    value_type=model.datatypes.String,
                    value=str(physical_asset_data.get("Quantity")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if physical_asset_data.get("Quantity") is not None
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Properties",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_property_collection(property_entry, None)
                        for property_entry in physical_asset_properties
                        if isinstance(property_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(physical_asset_properties) > 0
            else []
        ),
    ]

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_personnel_collection(personnel_data: dict, id_short=None) -> model.SubmodelElementCollection:
    description_entries = personnel_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = personnel_data.get("EngineeringUnits")

    personnel_properties = personnel_data.get("Properties")
    if not isinstance(personnel_properties, list):
        personnel_properties = []

    value_elements = [
        model.Property(
            id_short="ID",
            value_type=model.datatypes.String,
            value=str(personnel_data.get("ID", "---")),
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                    ),
                )
            ),
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [
                model.Property(
                    id_short="PersonnelUse",
                    value_type=model.datatypes.String,
                    value=str(personnel_data.get("PersonnelUse")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if personnel_data.get("PersonnelUse") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="Quantity",
                    value_type=model.datatypes.String,
                    value=str(personnel_data.get("Quantity")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if personnel_data.get("Quantity") is not None
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Properties",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_property_collection(property_entry, None)
                        for property_entry in personnel_properties
                        if isinstance(property_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(personnel_properties) > 0
            else []
        ),
    ]

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


def _create_isa95_equipment_collection(equipment_data: dict, id_short=None) -> model.SubmodelElementCollection:
    description_entries = equipment_data.get("Description")
    if isinstance(description_entries, dict):
        description_entries = [description_entries]
    if not isinstance(description_entries, list):
        description_entries = []

    engineering_units = equipment_data.get("EngineeringUnits")

    equipment_properties = equipment_data.get("Properties")
    if not isinstance(equipment_properties, list):
        equipment_properties = []

    value_elements = [
        model.Property(
            id_short="ID",
            value_type=model.datatypes.String,
            value=str(equipment_data.get("ID", "---")),
            semantic_id=model.ExternalReference(
                (
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                    ),
                )
            ),
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Description",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_localized_text_collection(None, description_entry)
                        for description_entry in description_entries
                        if isinstance(description_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(description_entries) > 0
            else []
        ),
        *(
            [
                model.Property(
                    id_short="EquipmentUse",
                    value_type=model.datatypes.String,
                    value=str(equipment_data.get("EquipmentUse")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if equipment_data.get("EquipmentUse") is not None
            else []
        ),
        *(
            [
                model.Property(
                    id_short="Quantity",
                    value_type=model.datatypes.String,
                    value=str(equipment_data.get("Quantity")),
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if equipment_data.get("Quantity") is not None
            else []
        ),
        *(
            [_create_engineering_units_collection("EngineeringUnits", engineering_units)]
            if isinstance(engineering_units, dict)
            else []
        ),
        *(
            [
                model.SubmodelElementList(
                    id_short="Properties",
                    type_value_list_element=model.SubmodelElementCollection,
                    value=[
                        _create_isa95_property_collection(property_entry, None)
                        for property_entry in equipment_properties
                        if isinstance(property_entry, dict)
                    ],
                    semantic_id=model.ExternalReference(
                        (
                            model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value="http://interop4X.deg/Properties/HasAttribute",
                            ),
                        )
                    ),
                )
            ]
            if len(equipment_properties) > 0
            else []
        ),
    ]

    return model.SubmodelElementCollection(
        id_short=id_short,
        value=value_elements,
        semantic_id=model.ExternalReference(
            (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"),)
        ),
    )


async def create_aas_for_job(data: dict) -> None:
    """Create and register all job-related submodels (order, state, response)."""
    job_data = clean_job_data(data)
    original_job_order_id = job_data["JobOrder"]["JobOrderID"]
    # Use original value for globally unique id (preserves special chars)
    aas_id = original_job_order_id
    # Use cleaned value for human-readable idShort (alphanumeric only)
    aas_short_id = f"AAS_JOB_{clean_id(original_job_order_id)}"
    aas = model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=aas_short_id,
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE, global_asset_id=(model.Identifier(aas_id))
        ),
    )
    submodels = []
    submodels.append(add_job_order_submodel(job_data, aas))
    submodels.append(add_job_state_submodel(job_data, aas))
    submodels.append(add_job_response_submodel(job_data, aas))
    # Register AAS and Submodel in BaSyx
    await register_in_basyx(aas, submodels)


def add_job_order_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobOrder submodel from ISA95 job-order payload data."""
    job_order: dict = job_data["JobOrder"]
    job_order_id: str = clean_id(job_order["JobOrderID"])
    description_entries = job_order.get("Description")
    workmaster_entries = job_order.get("WorkmasterId") or job_order.get("WorkMasterID")
    if not isinstance(workmaster_entries, list):
        workmaster_entries = []

    job_order_parameters_entries = job_order.get("JobOrderParameters")
    if not isinstance(job_order_parameters_entries, list):
        job_order_parameters_entries = []

    personnel_requirements_entries = job_order.get("PersonnelRequirements")
    if not isinstance(personnel_requirements_entries, list):
        personnel_requirements_entries = []

    equipment_requirements_entries = job_order.get("EquipmentRequirements")
    if not isinstance(equipment_requirements_entries, list):
        equipment_requirements_entries = []

    physical_asset_requirements_entries = job_order.get("PhysicalAssetRequirements")
    if not isinstance(physical_asset_requirements_entries, list):
        physical_asset_requirements_entries = []

    material_requirements_entries = job_order.get("MaterialRequirements")
    if not isinstance(material_requirements_entries, list):
        material_requirements_entries = []

    submodel_id = f"JobOrder {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobOrder",
        submodel_element=[
            model.Property(
                id_short="JobOrderID",
                value_type=model.datatypes.String,
                value=job_order_id,
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="Description",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short="Text",
                                value_type=model.datatypes.String,
                                value=(
                                    str(entry["Text"])
                                    if isinstance(entry, dict) and "Text" in entry and entry["Text"] is not None
                                    else "---"
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                            *(
                                [
                                    model.Property(
                                        id_short="Locale",
                                        value_type=model.datatypes.String,
                                        value=str(entry["Locale"]),
                                        semantic_id=model.ExternalReference(
                                            (
                                                model.Key(
                                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                    value="http://interop4X.deg/Properties/HasAttribute",
                                                ),
                                            )
                                        ),
                                    )
                                ]
                                if isinstance(entry, dict) and "Locale" in entry and entry["Locale"] is not None
                                else []
                            ),
                        ],
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                    for entry in (description_entries if isinstance(description_entries, list) else [])
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="WorkMasterID",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short="ID",
                                value_type=model.datatypes.String,
                                value=(
                                    str(entry["ID"])
                                    if isinstance(entry, dict) and "ID" in entry and entry["ID"] is not None
                                    else "---"
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                            *(
                                [
                                    model.Property(
                                        id_short="Description",
                                        value_type=model.datatypes.String,
                                        value=str(entry["Description"]),
                                        semantic_id=model.ExternalReference(
                                            (
                                                model.Key(
                                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                                    value="http://interop4X.deg/Properties/HasAttribute",
                                                ),
                                            )
                                        ),
                                    )
                                ]
                                if isinstance(entry, dict)
                                and "Description" in entry
                                and entry["Description"] is not None
                                else []
                            ),
                        ],
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                    for entry in workmaster_entries
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="StartTime",
                value_type=model.datatypes.String,
                value=job_order.get("StartTime", "---"),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="EndTime",
                value_type=model.datatypes.String,
                value=job_order.get("EndTime", "---"),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="Priority",
                value_type=model.datatypes.Integer,
                value=job_order.get("Priority", 0),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="JobOrderParameters",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_parameter_collection(entry, None)
                    for entry in job_order_parameters_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="PersonnelRequirements",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_personnel_collection(entry, None)
                    for entry in personnel_requirements_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="EquipmentRequirements",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_equipment_collection(entry, None)
                    for entry in equipment_requirements_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="PhysicalAssetRequirements",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_physical_asset_collection(entry, None)
                    for entry in physical_asset_requirements_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="MaterialRequirements",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_material_collection(entry, None)
                    for entry in material_requirements_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
        ],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def add_job_state_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobState submodel from ISA95 job-state payload data."""
    job_order: dict = job_data["JobOrder"]
    job_order_id: str = clean_id(job_order["JobOrderID"])
    submodel_id = f"JobState {job_order_id}"
    job_state_entries = job_data.get("JobState")
    if not isinstance(job_state_entries, list):
        job_state_entries = []
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobState",
        submodel_element=[
            model.SubmodelElementList(
                id_short="JobStateList",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short="StateText",
                                value_type=model.datatypes.String,
                                value=(
                                    str(entry["StateText"]["Text"])
                                    if isinstance(entry, dict)
                                    and isinstance(entry.get("StateText"), dict)
                                    and entry["StateText"].get("Text") is not None
                                    else "---"
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                            model.Property(
                                id_short="StateNumber",
                                value_type=model.datatypes.Integer,
                                value=(
                                    entry["StateNumber"]
                                    if isinstance(entry, dict)
                                    and "StateNumber" in entry
                                    and entry["StateNumber"] is not None
                                    else 0
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                        ],
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                    for entry in job_state_entries
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
        ],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def add_job_response_submodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the JobResponse submodel from ISA95 job-response payload data."""
    job_order: dict = job_data["JobOrder"]
    job_response = job_data.get("JobResponse")
    if not isinstance(job_response, dict):
        job_response = {}

    job_order_id: str = clean_id(job_order["JobOrderID"])
    job_response_id = str(job_response.get("JobResponseID", "---"))

    description_data = job_response.get("Description")
    description_text = "---"
    description_locale = None
    if isinstance(description_data, dict):
        if description_data.get("Text") is not None:
            description_text = str(description_data.get("Text"))
        if description_data.get("Locale") is not None:
            description_locale = str(description_data.get("Locale"))

    response_job_state_entries = job_response.get("JobState")
    if not isinstance(response_job_state_entries, list):
        response_job_state_entries = []

    job_response_data_entries = job_response.get("JobResponseData")
    if not isinstance(job_response_data_entries, list):
        job_response_data_entries = []

    personnel_actuals_entries = job_response.get("PersonnelActuals")
    if not isinstance(personnel_actuals_entries, list):
        personnel_actuals_entries = []

    equipment_actuals_entries = job_response.get("EquipmentActuals")
    if not isinstance(equipment_actuals_entries, list):
        equipment_actuals_entries = []

    physical_asset_actuals_entries = job_response.get("PhysicalAssetActuals")
    if not isinstance(physical_asset_actuals_entries, list):
        physical_asset_actuals_entries = []

    material_actuals_entries = job_response.get("MaterialActuals")
    if not isinstance(material_actuals_entries, list):
        material_actuals_entries = []

    submodel_id = f"JobResponse {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobResponse",
        submodel_element=[
            model.Property(
                id_short="JobResponseID",
                value_type=model.datatypes.String,
                value=job_response_id,
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="JobOrderID",
                value_type=model.datatypes.String,
                value=str(job_response.get("JobOrderID", job_order.get("JobOrderID", "---"))),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementCollection(
                id_short="Description",
                value=[
                    model.Property(
                        id_short="Text",
                        value_type=model.datatypes.String,
                        value=description_text,
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    ),
                    *(
                        [
                            model.Property(
                                id_short="Locale",
                                value_type=model.datatypes.String,
                                value=description_locale,
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            )
                        ]
                        if description_locale is not None
                        else []
                    ),
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="StartTime",
                value_type=model.datatypes.String,
                value=str(job_response.get("StartTime", "---")),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="EndTime",
                value_type=model.datatypes.String,
                value=str(job_response.get("EndTime", "---")),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="JobStateList",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short="StateText",
                                value_type=model.datatypes.String,
                                value=(
                                    str(entry["StateText"]["Text"])
                                    if isinstance(entry, dict)
                                    and isinstance(entry.get("StateText"), dict)
                                    and entry["StateText"].get("Text") is not None
                                    else "---"
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                            model.Property(
                                id_short="StateNumber",
                                value_type=model.datatypes.Integer,
                                value=(
                                    entry["StateNumber"]
                                    if isinstance(entry, dict) and entry.get("StateNumber") is not None
                                    else 0
                                ),
                                semantic_id=model.ExternalReference(
                                    (
                                        model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value="http://interop4X.deg/Properties/HasAttribute",
                                        ),
                                    )
                                ),
                            ),
                        ],
                        semantic_id=model.ExternalReference(
                            (
                                model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value="http://interop4X.deg/Properties/HasAttribute",
                                ),
                            )
                        ),
                    )
                    for entry in response_job_state_entries
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="JobResponseData",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_parameter_collection(entry, None)
                    for entry in job_response_data_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="PersonnelActuals",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_personnel_collection(entry, None)
                    for entry in personnel_actuals_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="EquipmentActuals",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_equipment_collection(entry, None)
                    for entry in equipment_actuals_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="PhysicalAssetActuals",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_physical_asset_collection(entry, None)
                    for entry in physical_asset_actuals_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.SubmodelElementList(
                id_short="MaterialActuals",
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    _create_isa95_material_collection(entry, None)
                    for entry in material_actuals_entries
                    if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
        ],
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel
