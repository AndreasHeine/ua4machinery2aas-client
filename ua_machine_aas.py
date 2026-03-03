"""Create AAS representations for machine identification data."""

from basyx.aas import model
from basyx_utils.register import register_in_basyx


async def create_aas_for_identification(identifier: str, identification: dict) -> None:
    """Create an AAS for machine identification and register it in BaSyx."""
    # Use original value for globally unique id (preserves special chars)
    aas_id = identifier
    # Use cleaned value for human-readable idShort (alphanumeric only)
    aas_short_id = "AAS_Machine"
    aas = model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=aas_short_id,
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE, global_asset_id=(model.Identifier(aas_id))
        ),
    )
    submodels = [add_identification_submodel(identification, aas)]
    await register_in_basyx(aas, submodels)


def _create_identification_property(id_short: str, value, value_type=model.datatypes.String) -> model.Property:
    """Helper to create a property with semantic reference."""
    return model.Property(
        id_short=id_short,
        value_type=value_type,
        value=value,
        semantic_id=model.ExternalReference(
            (
                model.Key(
                    type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                ),
            )
        ),
    )


def _extract_localized_text(localized_value) -> str:
    """Extract text from LocalizedText or return as string."""
    if isinstance(localized_value, dict) and "Text" in localized_value:
        return str(localized_value["Text"])
    return str(localized_value) if localized_value is not None else "---"


def add_identification_submodel(identification: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the machine-identification submodel and link it to the AAS."""
    product_instance_uri = identification["ProductInstanceUri"]
    submodel_id = f"Machinery Identification {product_instance_uri}"

    # Build submodel elements list with mandatory and optional properties
    elements = [
        # Mandatory properties
        _create_identification_property("ProductInstanceUri", product_instance_uri),
        _create_identification_property("Manufacturer", _extract_localized_text(identification.get("Manufacturer"))),
        _create_identification_property("SerialNumber", str(identification.get("SerialNumber", "---"))),
    ]

    # Optional LocalizedText properties
    if "Model" in identification:
        elements.append(_create_identification_property("Model", _extract_localized_text(identification["Model"])))

    if "ComponentName" in identification:
        elements.append(_create_identification_property("ComponentName", _extract_localized_text(identification["ComponentName"])))

    # Optional String properties
    optional_string_props = [
        "Location", "DeviceClass", "DeviceManual", "DeviceRevision",
        "HardwareRevision", "SoftwareRevision", "ManufacturerUri",
        "ProductCode", "AssetId"
    ]
    for prop_name in optional_string_props:
        if prop_name in identification and identification[prop_name] is not None:
            elements.append(_create_identification_property(prop_name, str(identification[prop_name])))

    # Optional Integer properties
    if "YearOfConstruction" in identification and identification["YearOfConstruction"] is not None:
        elements.append(_create_identification_property(
            "YearOfConstruction", int(identification["YearOfConstruction"]), model.datatypes.Integer
        ))

    if "MonthOfConstruction" in identification and identification["MonthOfConstruction"] is not None:
        elements.append(_create_identification_property(
            "MonthOfConstruction", int(identification["MonthOfConstruction"]), model.datatypes.Integer
        ))

    if "RevisionCounter" in identification and identification["RevisionCounter"] is not None:
        elements.append(_create_identification_property(
            "RevisionCounter", int(identification["RevisionCounter"]), model.datatypes.Integer
        ))

    # Optional DateTime property (as String in AAS)
    if "InitialOperationDate" in identification and identification["InitialOperationDate"] is not None:
        elements.append(_create_identification_property(
            "InitialOperationDate", str(identification["InitialOperationDate"])
        ))

    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="MachineryIdentification",
        submodel_element=elements,
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel
