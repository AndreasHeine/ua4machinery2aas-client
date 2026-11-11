"""Create AAS representations for machine identification data."""

import datetime

from basyx.aas import model
from basyx_utils.client import AsyncBaSyxClient
from basyx_utils.register import register_in_basyx
from common.helper import as_int_or_none


async def create_aas_for_identification(
    identifier: str,
    identification: dict,
    client: AsyncBaSyxClient | None = None,
) -> None:
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
    await register_in_basyx(aas, submodels, client)


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
    product_instance_uri = identification.get("ProductInstanceUri")
    if product_instance_uri is None or str(product_instance_uri).strip() == "":
        # A missing identification URI must not crash the whole event processing.
        print("MachineryIdentification: identification has no ProductInstanceUri, using placeholder")
        product_instance_uri = "---"
    product_instance_uri = str(product_instance_uri)
    submodel_id = f"Machinery Identification {product_instance_uri}"

    # Build submodel elements list with mandatory and optional properties
    elements = [
        # Mandatory properties
        _create_identification_property("ProductInstanceUri", product_instance_uri),
        _create_identification_property("Manufacturer", _extract_localized_text(identification.get("Manufacturer"))),
        _create_identification_property("SerialNumber", str(identification.get("SerialNumber", "---"))),
    ]

    # Optional LocalizedText properties
    for localized_prop_name in ("Model", "ComponentName"):
        if localized_prop_name in identification:
            elements.append(
                _create_identification_property(
                    localized_prop_name,
                    _extract_localized_text(identification[localized_prop_name]),
                )
            )

    # Optional String properties
    optional_string_props = [
        "Location",
        "DeviceClass",
        "DeviceManual",
        "DeviceRevision",
        "HardwareRevision",
        "SoftwareRevision",
        "ManufacturerUri",
        "ProductCode",
        "AssetId",
    ]
    for prop_name in optional_string_props:
        if prop_name in identification and identification[prop_name] is not None:
            elements.append(_create_identification_property(prop_name, str(identification[prop_name])))

    # Optional Integer properties. Values that cannot be converted to int are kept
    # as strings instead of raising, because BaSyx rejects mismatching value types.
    for integer_prop_name in ("YearOfConstruction", "MonthOfConstruction", "RevisionCounter"):
        raw_value = identification.get(integer_prop_name)
        if raw_value is None:
            continue
        integer_value = as_int_or_none(raw_value)
        if integer_value is not None:
            elements.append(
                _create_identification_property(integer_prop_name, integer_value, model.datatypes.Integer)
            )
        else:
            print(f"MachineryIdentification: {integer_prop_name}={raw_value!r} is not an integer, kept as string")
            elements.append(_create_identification_property(integer_prop_name, str(raw_value)))

    # Optional DateTime property (as String in AAS)
    raw_initial_operation_date = identification.get("InitialOperationDate")
    if raw_initial_operation_date is not None:
        if isinstance(raw_initial_operation_date, (datetime.date, datetime.datetime)):
            # Keep an XSD dateTime compatible representation.
            raw_initial_operation_date = raw_initial_operation_date.isoformat()
        elements.append(
            _create_identification_property("InitialOperationDate", str(raw_initial_operation_date))
        )

    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="MachineryIdentification",
        submodel_element=elements,
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel
