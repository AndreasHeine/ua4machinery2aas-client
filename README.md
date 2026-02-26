# AAS Client

Python-Client zur Anbindung eines OPC-UA-Servers und Registrierung von AAS/Submodels in einer BaSyx-Umgebung.

Der Client verbindet sich mit einer Maschine, abonniert Events und erzeugt darauf basierend AAS-Datenstrukturen.

## Features

- Verbindung zu OPC UA via `asyncua`
- Subscription auf Events
- Erstellung/Update von AAS und Submodels via BaSyx REST APIs
- Vollständig über Umgebungsvariablen konfigurierbar

## Voraussetzungen

- Python 3.11+ (empfohlen)
- Docker + Docker Compose (für lokales BaSyx-Backend)

## Projektstruktur

- `main.py` – OPC-UA-Subscription und Event-Verarbeitung
- `old_main.py` – lokaler Demo/Smoke-Test für AAS-Erstellung ohne OPC UA
- `config.py` – zentrale Konfiguration über ENV-Variablen
- `ua_job_aas.py` – Erstellung von Job-AAS/Submodels
- `ua_machine_aas.py` – Erstellung von Maschinen-Identifikations-AAS
- `basyx_utils/` – async REST-Client und Register-Helfer für BaSyx
- `backend/` – Docker-Compose für BaSyx, Registry, Discovery, UI, Dashboard API

## Quickstart

### 1) Python-Abhängigkeiten installieren

```bash
python -m venv env
env\\Scripts\\activate
pip install -r requirements.txt
```

### 2) BaSyx-Backend starten (lokal)

```bash
cd backend
docker-compose up -d
```

Danach sind standardmäßig erreichbar:

- AAS Environment: http://localhost:8081
- AAS Registry: http://localhost:8082
- Submodel Registry: http://localhost:8083
- AAS Discovery: http://localhost:8084
- Dashboard API: http://localhost:8085
- AAS Web UI: http://localhost:3000

### 3) Client starten

```bash
python main.py
```

## Konfiguration (ENV)

Alle Parameter in `config.py` können per Umgebungsvariable überschrieben werden.

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

| Variable | Default | Hinweis |
|---|---|---|
| `UA_ENDPOINT_URL` | `opc.tcp://opcua.umati.app:4843` | OPC-UA-Server-Endpoint |
| `UA_REQUEST_TIMEOUT` | `4` | Sekunden (int) |
| `UA_MACHINE_INSTANCE_NODEID` | `ns=49;s=MyControledMachine` | NodeId der Maschineninstanz |
| `UA_PUBLISHING_INTERVAL` | `1000` | Millisekunden (int) |

### Beispiele zum Setzen von Variablen

**PowerShell:**

```powershell
$env:UA_ENDPOINT_URL = "opc.tcp://my-server:4840"
$env:UA_MACHINE_INSTANCE_NODEID = "ns=2;s=MyMachine"
$env:UA_PUBLISHING_INTERVAL = "500"
python main.py
```

**Windows CMD:**

```cmd
set UA_ENDPOINT_URL=opc.tcp://my-server:4840
set UA_MACHINE_INSTANCE_NODEID=ns=2;s=MyMachine
set UA_PUBLISHING_INTERVAL=500
python main.py
```

## Hinweise zum aktuellen Stand

- In `main.py` ist das Mapping von empfangenen OPC-UA-Events auf das erwartete `job_data`-Schema noch als `TODO` markiert.
- Für einen schnellen Funktionstest der BaSyx-Registrierung ohne OPC-UA-Events kann `old_main.py` genutzt werden.
- Bei bestehenden IDs wird in BaSyx per PUT überschrieben (Upsert-Verhalten).

## Troubleshooting

- **HTTP 4xx/5xx bei AAS/Submodel-Registrierung:** Prüfen, ob `backend/docker-compose.yml` läuft und die `*_REPO_PATH`-URLs korrekt sind.
- **Keine OPC-UA-Events:** `UA_MACHINE_INSTANCE_NODEID` und Namespace/Model des Zielservers prüfen.
- **Timeouts:** `UA_REQUEST_TIMEOUT` erhöhen und Server-Erreichbarkeit testen.
