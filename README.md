# OPC for Machinery to AAS Client

What this program does (in simple terms):
- It connects to a machine's OPC UA server.
- It listens for specific machine/job events.
- When a matching event arrives, it extracts relevant job information.
- It sends that information to create/update an Asset Administration Shell (AAS)
    representation via the BaSyx APIs.

Why this is useful:
- OPC UA is used by machines to expose data and events.
- AAS is a standardized digital representation of an asset (for example, a machine
    or a job) so IT systems can consume it consistently.
- This script acts as a translator/bridge: machine events in, AAS updates out.

## OPC UA Event Subscription Flow

In `main.py`, the client currently performs the following steps to find and process relevant events:

1. Connect to the OPC UA server using `UA_ENDPOINT_URL` and `UA_REQUEST_TIMEOUT`.
2. Load type definitions (`load_data_type_definitions`, `load_type_definitions`) and read the namespace array (`get_namespace_array`).
3. Resolve namespace indices from the namespace array for
	- `http://opcfoundation.org/UA/Machinery/`
	- `http://opcfoundation.org/UA/Machinery/Jobs/`
4. Enter via the configured machine instance `UA_MACHINE_INSTANCE_NODEID` (normalized using the helper `make_nodeid_string(...)`).
5. Navigate the address space:
	- `Machine -> MachineryBuildingBlocks -> JobManager -> JobOrderResults`
6. Read `GeneratesEvent` references from `JobOrderResults`.
7. Use the first reference as expected event type (`EVENT_TYPE_NODEID`) and resolve the event type node.
8. Create a subscription with `UA_PUBLISHING_INTERVAL`.
9. Subscribe with a server-side filter via `subscribe_events(...)`:
	- `sourcenode=job_order_results_node`
	- `evtypes=[found_eventtype_node]`
	- `where_clause_generation=True`
10. Process events continuously via queue:
	- `SubscriptionHandler` puts incoming events into `EVENT_QUEUE`.
	- `process_event(...)` only processes events whose `EventType` matches the previously determined `EVENT_TYPE_NODEID`.
	- A `job_data` payload for `create_aas_for_job(...)` is built from the event.

Event filtering is already done server-side in the subscription; client-side `EventType` checking remains as an additional safeguard.

## Features

- OPC UA connectivity via `asyncua`
- Event subscription
- AAS and submodel creation/update via BaSyx REST APIs
- Fully configurable via environment variables

## Requirements

- Python 3.11+ (recommended)
- Docker + Docker Compose (for local BaSyx backend)

## Quickstart

### 1) Install Python dependencies

```bash
python -m venv env
env\\Scripts\\activate
pip install -r requirements.txt
```

### 2) Start BaSyx backend (local)

```bash
cd backend
docker-compose up -d
```

The following services are available by default:

- AAS Environment: http://localhost:8081
- AAS Registry: http://localhost:8082
- Submodel Registry: http://localhost:8083
- AAS Discovery: http://localhost:8084
- Dashboard API: http://localhost:8085
- AAS Web UI: http://localhost:3000

### 3) Start client

```bash
python main.py
```

## Configuration (ENV)

All parameters in `config.py` can be overridden via environment variables.

### AAS/BaSyx

| Variable | Default |
|---|---|
| `AAS_ENV_BASE_URL` | `http://localhost:8081` |
| `AAS_ENV_REPO_PATH` | `http://localhost:8081/shells` |
| `SUBMODEL_ENV_REPO_PATH` | `http://localhost:8081/submodels` |
| `CD_ENV_REPO_PATH` | `http://localhost:8081/concept-descriptions` |
| `AAS_DISCOVERY_PATH` | `http://localhost:8084/lookup/shells` |
| `DASHBOARD_SERVICE_PATH` | `http://localhost:8085/api/elements` |

### OPC UA

| Variable | Default | Note |
|---|---|---|
| `UA_ENDPOINT_URL` | `opc.tcp://opcua.umati.app:4843` | OPC UA server endpoint |
| `UA_REQUEST_TIMEOUT` | `4` | Seconds (int) |
| `UA_MACHINE_INSTANCE_NODEID` | `ns=49;s=MyControledMachine` | NodeId of the machine instance |
| `UA_PUBLISHING_INTERVAL` | `1000` | Milliseconds (int) |

## Troubleshooting

- **HTTP 4xx/5xx during AAS/submodel registration:** Check whether `backend/docker-compose.yml` is running and the `*_REPO_PATH` URLs are correct.
- **No OPC UA events:** Verify `UA_MACHINE_INSTANCE_NODEID` and the namespace/model of the target server.
- **Timeouts:** Increase `UA_REQUEST_TIMEOUT` and check server connectivity.
