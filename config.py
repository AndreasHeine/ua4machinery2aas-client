import os

'''
AAS Configuration parameters. These can be set via environment variables or will fall back to default values.
'''
AAS_ENV_BASE_URL: str = os.getenv("AAS_ENV_BASE_URL", "http://localhost:8081")
AAS_ENV_REPO_PATH: str = os.getenv("AAS_ENV_REPO_PATH", "http://localhost:8081/shells")
SUBMODEL_ENV_REPO_PATH: str = os.getenv("SUBMODEL_ENV_REPO_PATH", "http://localhost:8081/submodels")
CD_ENV_REPO_PATH: str = os.getenv("CD_ENV_REPO_PATH", "http://localhost:8081/concept-descriptions")

AAS_DISCOVERY_PATH: str = os.getenv("AAS_DISCOVERY_PATH", "http://localhost:8084/lookup/shells")
DASHBOARD_SERVICE_PATH: str = os.getenv("DASHBOARD_SERVICE_PATH", "http://localhost:8085/api/elements")

'''
OPC UA Configuration parameters. These can be set via environment variables or will fall back to default values.
'''

UA_ENDPOINT_URL: str = os.getenv("UA_ENDPOINT_URL", "opc.tcp://opcua.umati.app:4843")
UA_REQUEST_TIMEOUT: int = int(os.getenv("UA_REQUEST_TIMEOUT", "4"))  # in seconds
UA_MACHINE_INSTANCE_NODEID: str = os.getenv("UA_MACHINE_INSTANCE_NODEID", "nsu=http://MyControledMachine-Namespace/UA;s=MyControledMachine")
UA_PUBLISHING_INTERVAL: int = int(os.getenv("UA_PUBLISHING_INTERVAL", "1000"))  # in milliseconds