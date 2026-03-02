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


def add_identification_submodel(identification: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    """Create the machine-identification submodel and link it to the AAS."""
    product_instance_uri = identification["ProductInstanceUri"]
    submodel_id = f"Machinery Identification {product_instance_uri}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="MachineryIdentification",
        submodel_element=[
            model.Property(
                id_short="ProductInstanceUri",
                value_type=model.datatypes.String,
                value=product_instance_uri,
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="Manufacturer",
                value_type=model.datatypes.String,
                value=identification["Manufacturer"]["Text"],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="SerialNumber",
                value_type=model.datatypes.String,
                value=identification["SerialNumber"],
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="Model",
                value_type=model.datatypes.String,
                value=identification.get("Model", "---"),
                semantic_id=model.ExternalReference(
                    (
                        model.Key(
                            type_=model.KeyTypes.GLOBAL_REFERENCE, value="http://interop4X.deg/Properties/HasAttribute"
                        ),
                    )
                ),
            ),
            model.Property(
                id_short="Location",
                value_type=model.datatypes.String,
                value=identification.get("Location", "---"),
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
