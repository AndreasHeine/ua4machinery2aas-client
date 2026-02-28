from basyx.aas import model
from basyx_utils.helper import (
    AAS_HTTP_STATUS_CODES,
    SM_HTTP_STATUS_CODES,
    add_aas_to_basyx_async,
    add_submodel_to_basyx_async,
)
from config import AAS_ENV_REPO_PATH, SUBMODEL_ENV_REPO_PATH


async def register_in_basyx(aas: model.AssetAdministrationShell, submodels: list[model.Submodel]) -> None:
    res = await add_aas_to_basyx_async(AAS_ENV_REPO_PATH, aas)
    print(
        f"AAS registration for id: {aas.id}, status: {res.status_code} [{AAS_HTTP_STATUS_CODES.get(res.status_code, 'Unknown Status')}]"
    )
    for sm in submodels:
        res = await add_submodel_to_basyx_async(SUBMODEL_ENV_REPO_PATH, sm)
        print(
            f"Submodel registration for id: {sm.id}, status: {res.status_code} [{SM_HTTP_STATUS_CODES.get(res.status_code, 'Unknown Status')}]"
        )
