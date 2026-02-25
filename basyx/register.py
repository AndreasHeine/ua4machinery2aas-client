from basyx.aas import model
from basyx.helper import add_aas_to_basyx_async, add_submodel_to_basyx_async
from config import AAS_ENV_REPO_PATH, SUBMODEL_ENV_REPO_PATH


async def register_in_basyx(aas: model.AssetAdministrationShell, submodels: list[model.Submodel]) -> None:
    res = await add_aas_to_basyx_async(AAS_ENV_REPO_PATH, aas)
    print(f"AAS Descriptor registration: {res.status_code}")
    if res.status_code >= 400:
        print("Error response:", res.text)
    for sm in submodels:
        res = await add_submodel_to_basyx_async(SUBMODEL_ENV_REPO_PATH, sm)
        print(f"Submodel registration: {res.status_code}")
        if res.status_code >= 400:
            print("Error response:", res.text)
