"""Runtime configuration values for AAS and OPC UA connectivity."""

import os


def _int_env(name: str, default: int) -> int:
    """Read an integer environment variable, falling back to default on invalid input."""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        print(f"Warning: {name}={raw_value!r} is not an integer, using default {default}")
        return default


def _float_env(name: str, default: float) -> float:
    """Read a float environment variable, falling back to default on invalid input."""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return float(raw_value)
    except ValueError:
        print(f"Warning: {name}={raw_value!r} is not a number, using default {default}")
        return default


# AAS configuration parameters. These can be set via environment variables or
# will fall back to default values.
AAS_ENV_REPO_PATH: str = os.getenv("AAS_ENV_REPO_PATH", "http://localhost:8081/shells")
SUBMODEL_ENV_REPO_PATH: str = os.getenv("SUBMODEL_ENV_REPO_PATH", "http://localhost:8081/submodels")

AAS_REQUEST_TIMEOUT: float = _float_env("AAS_REQUEST_TIMEOUT", 10.0)  # in seconds
BASYX_MAX_ATTEMPTS: int = max(1, _int_env("BASYX_MAX_ATTEMPTS", 3))  # attempts per registration
BASYX_RETRY_BASE_DELAY: float = _float_env("BASYX_RETRY_BASE_DELAY", 1.0)  # in seconds

# OPC UA configuration parameters. These can be set via environment variables
# or will fall back to default values.

UA_ENDPOINT_URL: str = os.getenv("UA_ENDPOINT_URL", "opc.tcp://opcua.umati.app:4843")
UA_REQUEST_TIMEOUT: int = _int_env("UA_REQUEST_TIMEOUT", 4)  # in seconds
UA_MACHINE_INSTANCE_NODEID: str = os.getenv(
    "UA_MACHINE_INSTANCE_NODEID", "nsu=http://MyControledMachine-Namespace/UA;s=MyControledMachine"
)
UA_PUBLISHING_INTERVAL: int = max(10, _int_env("UA_PUBLISHING_INTERVAL", 1000))  # in milliseconds

# OPC UA connection behaviour. The initial connect is retried, because the OPC UA
# server is often started after this client (e.g. by docker compose).
UA_CONNECT_MAX_ATTEMPTS: int = _int_env("UA_CONNECT_MAX_ATTEMPTS", 0)  # 0 keeps retrying until it succeeds
UA_CONNECT_RETRY_BASE_DELAY: float = _float_env("UA_CONNECT_RETRY_BASE_DELAY", 1.0)  # in seconds
UA_RECONNECT_MAX_DELAY: float = _float_env("UA_RECONNECT_MAX_DELAY", 5.0)  # in seconds

# Event queue behaviour: incoming events are queued, the oldest event is dropped
# when the queue is full so that a slow BaSyx backend cannot grow memory usage.
EVENT_QUEUE_MAXSIZE: int = max(1, _int_env("EVENT_QUEUE_MAXSIZE", 100))  # queued events before the oldest is dropped
