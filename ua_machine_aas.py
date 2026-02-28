from basyx.aas import model
from basyx_utils.register import register_in_basyx
from common.helper import clean_id


async def create_aas_for_identification(id: str, identification: dict) -> None:
    aas_id = clean_id(id)
    aas_short_id = f"AAS_Machine_{aas_id}"
    aas = model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=aas_short_id,
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE, global_asset_id=(model.Identifier(aas_id))
        ),
    )
    submodels = [addIdentificationSubmodel(identification, aas)]
    await register_in_basyx(aas, submodels)


def addIdentificationSubmodel(identification: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    id = identification["ProductInstanceUri"]
    submodel_id = f"Machinery Identification {id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="MachineryIdentification",
        submodel_element=[
            model.Property(
                id_short="ProductInstanceUri",
                value_type=model.datatypes.String,
                value=id,
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
