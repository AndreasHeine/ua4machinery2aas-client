from asyncua import ua
from basyx.aas import model
from basyx_utils.register import register_in_basyx
from common.helper import clean_id, variant_to_json_serializable

def clean_job_data(event_data: dict) -> dict:
    cleaned_data = {}
    for key, value in event_data.items():
        cleaned_data[key] = variant_to_json_serializable(value)
    return cleaned_data


async def create_aas_for_job(data: dict) -> None:
    job_data = clean_job_data(data)
    # for key, value in job_data.items():
    #     print(f"{key}: {value}")
    aas_id = clean_id(job_data['JobOrder']['JobOrderID'])
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
    # submodels.append(addJobResponseSubmodel(job_data, aas)) # FIXME: Implement JobResponse Submodel after we have received an example of the JobOrderParameters structure, as this is currently not clear and we want to avoid making wrong assumptions here.
    # Register AAS and Submodel in BaSyx
    await register_in_basyx(aas, submodels)


def addJobOrderSubmodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    job_order: dict = job_data['JobOrder']
    job_order_id: str = clean_id(job_order['JobOrderID'])
    description = job_order["Description"][0]["Text"] if "Description" in job_order and isinstance(job_order["Description"], list) and len(job_order["Description"]) > 0 and "Text" in job_order["Description"][0] else "---"
    workmaster_id = job_order["WorkmasterId"][0]["ID"] if "WorkmasterId" in job_order and isinstance(job_order["WorkmasterId"], list) and len(job_order["WorkmasterId"]) > 0 and "ID" in job_order["WorkmasterId"][0] else "---"
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
                value=description,
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
                value=workmaster_id,
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
    job_order_id: str = clean_id(job_order['JobOrderID'])
    submodel_id = f"JobState {job_order_id}"
    job_state = job_data["JobState"][0]["StateText"]["Text"] if "JobState" in job_data and isinstance(job_data["JobState"], list) and len(job_data["JobState"]) > 0 and "StateText" in job_data["JobState"][0] and "Text" in job_data["JobState"][0]["StateText"] else "---"
    job_state_number = job_data["JobState"][0]["StateNumber"] if "JobState" in job_data and isinstance(job_data["JobState"], list) and len(job_data["JobState"]) > 0 and "StateNumber" in job_data["JobState"][0] else 0
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobState",
        submodel_element=[
            model.Property(
                id_short='StateText',
                value_type=model.datatypes.String,
                value=job_state,
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
                value=job_state_number,
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
    if job_order_parameters is None:
        job_order_parameters = {}
    job_order_id: str = clean_id(job_order['JobOrderID'])
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
