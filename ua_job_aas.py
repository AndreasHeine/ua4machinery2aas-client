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
    submodels.append(addJobResponseSubmodel(job_data, aas))
    # Register AAS and Submodel in BaSyx
    await register_in_basyx(aas, submodels)


def addJobOrderSubmodel(job_data: dict, aas: model.AssetAdministrationShell) -> model.Submodel:
    job_order: dict = job_data['JobOrder']
    job_order_id: str = clean_id(job_order['JobOrderID'])
    description_entries = job_order.get("Description")
    workmaster_entries = job_order.get("WorkmasterId") or job_order.get("WorkMasterID")
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
            model.SubmodelElementList(
                id_short='Description',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short='Text',
                                value_type=model.datatypes.String,
                                value=str(entry["Text"]) if isinstance(entry, dict) and "Text" in entry and entry["Text"] is not None else "---",
                                semantic_id=model.ExternalReference(
                                    (model.Key(
                                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                                        value='http://interop4X.deg/Properties/HasAttribute'
                                    ),)
                                )
                            ),
                            *([
                                model.Property(
                                    id_short='Locale',
                                    value_type=model.datatypes.String,
                                    value=str(entry["Locale"]),
                                    semantic_id=model.ExternalReference(
                                        (model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value='http://interop4X.deg/Properties/HasAttribute'
                                        ),)
                                    )
                                )
                            ] if isinstance(entry, dict) and "Locale" in entry and entry["Locale"] is not None else [])
                        ],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in (description_entries if isinstance(description_entries, list) else [])
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='WorkmasterId',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short='ID',
                                value_type=model.datatypes.String,
                                value=str(entry["ID"]) if isinstance(entry, dict) and "ID" in entry and entry["ID"] is not None else "---",
                                semantic_id=model.ExternalReference(
                                    (model.Key(
                                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                                        value='http://interop4X.deg/Properties/HasAttribute'
                                    ),)
                                )
                            ),
                            *([
                                model.Property(
                                    id_short='Description',
                                    value_type=model.datatypes.String,
                                    value=str(entry["Description"]),
                                    semantic_id=model.ExternalReference(
                                        (model.Key(
                                            type_=model.KeyTypes.GLOBAL_REFERENCE,
                                            value='http://interop4X.deg/Properties/HasAttribute'
                                        ),)
                                    )
                                )
                            ] if isinstance(entry, dict) and "Description" in entry and entry["Description"] is not None else [])
                        ],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in (workmaster_entries if isinstance(workmaster_entries, list) else [])
                ],
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
    job_state_entries = job_data.get("JobState")
    if not isinstance(job_state_entries, list):
        job_state_entries = []
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobState",
        submodel_element=[
            model.SubmodelElementList(
                id_short='JobStateList',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short='StateText',
                                value_type=model.datatypes.String,
                                value=str(entry["StateText"]["Text"]) if isinstance(entry, dict) and isinstance(entry.get("StateText"), dict) and entry["StateText"].get("Text") is not None else "---",
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
                                value=entry["StateNumber"] if isinstance(entry, dict) and "StateNumber" in entry and entry["StateNumber"] is not None else 0,
                                semantic_id=model.ExternalReference(
                                    (model.Key(
                                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                                        value='http://interop4X.deg/Properties/HasAttribute'
                                    ),)
                                )
                            )
                        ],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in job_state_entries
                ],
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
    job_response = job_data.get('JobResponse')
    if not isinstance(job_response, dict):
        job_response = {}

    job_order_id: str = clean_id(job_order['JobOrderID'])
    job_response_id = str(job_response.get('JobResponseID', '---'))

    description_data = job_response.get('Description')
    description_text = "---"
    description_locale = None
    if isinstance(description_data, dict):
        if description_data.get('Text') is not None:
            description_text = str(description_data.get('Text'))
        if description_data.get('Locale') is not None:
            description_locale = str(description_data.get('Locale'))

    response_job_state_entries = job_response.get('JobState')
    if not isinstance(response_job_state_entries, list):
        response_job_state_entries = []

    job_response_data_entries = job_response.get('JobResponseData')
    if not isinstance(job_response_data_entries, list):
        job_response_data_entries = []

    personnel_actuals_entries = job_response.get('PersonnelActuals')
    if not isinstance(personnel_actuals_entries, list):
        personnel_actuals_entries = []

    equipment_actuals_entries = job_response.get('EquipmentActuals')
    if not isinstance(equipment_actuals_entries, list):
        equipment_actuals_entries = []

    physical_asset_actuals_entries = job_response.get('PhysicalAssetActuals')
    if not isinstance(physical_asset_actuals_entries, list):
        physical_asset_actuals_entries = []

    material_actuals_entries = job_response.get('MaterialActuals')
    if not isinstance(material_actuals_entries, list):
        material_actuals_entries = []

    submodel_id = f"JobResponse {job_order_id}"
    submodel = model.Submodel(
        id_=model.Identifier(submodel_id),
        id_short="JobResponse",
        submodel_element=[
            model.Property(
                id_short='JobResponseID',
                value_type=model.datatypes.String,
                value=job_response_id,
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.Property(
                id_short='JobOrderID',
                value_type=model.datatypes.String,
                value=str(job_response.get('JobOrderID', job_order.get('JobOrderID', '---'))),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementCollection(
                id_short='Description',
                value=[
                    model.Property(
                        id_short='Text',
                        value_type=model.datatypes.String,
                        value=description_text,
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ),
                    *([
                        model.Property(
                            id_short='Locale',
                            value_type=model.datatypes.String,
                            value=description_locale,
                            semantic_id=model.ExternalReference(
                                (model.Key(
                                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                                    value='http://interop4X.deg/Properties/HasAttribute'
                                ),)
                            )
                        )
                    ] if description_locale is not None else [])
                ],
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
                value=str(job_response.get('StartTime', '---')),
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
                value=str(job_response.get('EndTime', '---')),
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='JobStateList',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[
                            model.Property(
                                id_short='StateText',
                                value_type=model.datatypes.String,
                                value=str(entry['StateText']['Text']) if isinstance(entry, dict) and isinstance(entry.get('StateText'), dict) and entry['StateText'].get('Text') is not None else '---',
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
                                value=entry['StateNumber'] if isinstance(entry, dict) and entry.get('StateNumber') is not None else 0,
                                semantic_id=model.ExternalReference(
                                    (model.Key(
                                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                                        value='http://interop4X.deg/Properties/HasAttribute'
                                    ),)
                                )
                            )
                        ],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in response_job_state_entries
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='JobResponseData',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in job_response_data_entries if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='PersonnelActuals',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in personnel_actuals_entries if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='EquipmentActuals',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in equipment_actuals_entries if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='PhysicalAssetActuals',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in physical_asset_actuals_entries if isinstance(entry, dict)
                ],
                semantic_id=model.ExternalReference(
                    (model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value='http://interop4X.deg/Properties/HasAttribute'
                    ),)
                )
            ),
            model.SubmodelElementList(
                id_short='MaterialActuals',
                type_value_list_element=model.SubmodelElementCollection,
                value=[
                    model.SubmodelElementCollection(
                        id_short=None,
                        value=[],
                        semantic_id=model.ExternalReference(
                            (model.Key(
                                type_=model.KeyTypes.GLOBAL_REFERENCE,
                                value='http://interop4X.deg/Properties/HasAttribute'
                            ),)
                        )
                    ) for entry in material_actuals_entries if isinstance(entry, dict)
                ],
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
