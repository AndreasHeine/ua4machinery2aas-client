from basyx.aas import model
from basyx.register import register_in_basyx


async def create_aas_for_job(job_data: dict) -> None:
    aas_id = job_data['JobOrder']['JobOrderID']
    aas_short_id = f"AAS_JOB_{aas_id}"
    aas = model.AssetAdministrationShell(
        id_=model.Identifier(aas_id),
        id_short=aas_short_id,
        asset_information=model.AssetInformation(
            asset_kind=model.AssetKind.INSTANCE,
            global_asset_id=(model.Identifier(aas_id))
        )
    )
    submodels = []
    submodels.append(addJobOrderSubmodel(job_data, aas))
    submodels.append(addJobStateSubmodel(job_data, aas))
    submodels.append(addJobResponseSubmodel(job_data, aas))
    # Register AAS and Submodel in BaSyx
    await register_in_basyx(aas, submodels)


def addJobOrderSubmodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    job_order: dict = job_data['JobOrder']
    job_order_id: str = job_order['JobOrderID']
    submodel_id = f"JobOrder {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobOrder",
        submodel_element=[
            model.Property(
                id_short='JobOrderID',
                value_type=model.datatypes.String,
                value=job_order_id,
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='Description',
                value_type=model.datatypes.String,
                value=job_order.get('Description', "---"),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='WorkmasterId',
                value_type=model.datatypes.String,
                value=job_order.get('WorkmasterId', "---"),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='StartTime',
                value_type=model.datatypes.String,
                value=job_order.get('StartTime', "---"),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='EndTime',
                value_type=model.datatypes.String,
                value=job_order.get('EndTime', "---"),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='Priority',
                value_type=model.datatypes.Integer,
                value=job_order.get('Priority', 0),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
        ]
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def addJobStateSubmodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    job_order: dict = job_data['JobOrder']
    job_order_id: str = job_order['JobOrderID']
    submodel_id = f"JobState {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobState",
        submodel_element=[
            model.Property(
                id_short='StateText',
                value_type=model.datatypes.String,
                value=job_data.get('JobState', "---"),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='StateNumber',
                value_type=model.datatypes.Integer,
                value=job_data.get('JobStateNumber', 0),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
        ]
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel


def addJobResponseSubmodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    job_order: dict = job_data['JobOrder']
    job_order_parameters: dict = job_order.get('JobOrderParameters', {})
    job_order_id: str = job_order['JobOrderID']
    submodel_id = f"JobResponse {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobResponse",
        submodel_element=[
            model.SubmodelElementCollection(
                id_short='JobOrderParameters',
                value=[
                    model.Property(
                        id_short='JobName',
                        value_type=model.datatypes.String,
                        value=job_order_parameters.get('JobName', ["---"])[0],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ),
                    model.Property(
                        id_short='OrderNumbers',
                        value_type=model.datatypes.Integer,
                        value=job_order_parameters.get('OrderNumbers', [0])[0],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    )
                ]
            )
        ]
    )
    aas.submodel.add(model.ModelReference.from_referable(submodel))
    return submodel
