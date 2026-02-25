import os


AAS_ENV_BASE_URL = os.getenv("AAS_ENV_BASE_URL", "http://localhost:8081")
AAS_ENV_REPO_PATH = os.getenv("AAS_ENV_REPO_PATH", "http://localhost:8081/shells")
SUBMODEL_ENV_REPO_PATH = os.getenv("SUBMODEL_ENV_REPO_PATH", "http://localhost:8081/submodels")
CD_ENV_REPO_PATH = os.getenv("CD_ENV_REPO_PATH", "http://localhost:8081/concept-descriptions")

AAS_DISCOVERY_PATH = os.getenv("AAS_DISCOVERY_PATH", "http://localhost:8084/lookup/shells")
DASHBOARD_SERVICE_PATH = os.getenv("DASHBOARD_SERVICE_PATH", "http://localhost:8085/api/elements")
