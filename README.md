# AAS Client Async

Asynchroner Client zum Erstellen und Registrieren von Asset Administration Shells (AAS) in BaSyx-Repositories.

## Beschreibung

Dieses Projekt bietet Python-Funktionen zum asynchronen Erstellen von AAS für:
- Job Orders mit zugehörigen Submodels (JobOrder, JobState, JobResponse)
- Maschinenidentifikation mit MachineryIdentification Submodel

Die erstellten AAS werden automatisch in einem BaSyx-Repository registriert.

## Voraussetzungen

- Python 3.7+
- BaSyx-Server (läuft auf den konfigurierten Ports)

## Installation

1. Erstellen Sie eine virtuelle Umgebung:
```bash
python -m venv env
```

2. Aktivieren Sie die virtuelle Umgebung:
```bash
# Windows CMD
env\Scripts\activate.bat

# Windows PowerShell
env\Scripts\Activate.ps1

# Linux/Mac
source env/bin/activate
```

3. Installieren Sie die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

## Konfiguration

Die URLs für die BaSyx-Services können über Umgebungsvariablen konfiguriert werden. Ohne Konfiguration werden die folgenden Standardwerte verwendet:

| Umgebungsvariable | Standardwert | Beschreibung |
|------------------|--------------|--------------|
| `AAS_ENV_BASE_URL` | `http://localhost:8081` | Basis-URL für AAS Environment |
| `AAS_ENV_REPO_PATH` | `http://localhost:8081/shells` | Repository-Pfad für AAS |
| `SUBMODEL_ENV_REPO_PATH` | `http://localhost:8081/submodels` | Repository-Pfad für Submodels |
| `CD_ENV_REPO_PATH` | `http://localhost:8081/concept-descriptions` | Repository-Pfad für Concept Descriptions |
| `AAS_DISCOVERY_PATH` | `http://localhost:8084/lookup/shells` | Pfad zum AAS Discovery Service |
| `DASHBOARD_SERVICE_PATH` | `http://localhost:8085/api/elements` | Pfad zum Dashboard Service |

### Umgebungsvariablen setzen

**PowerShell:**
```powershell
$env:AAS_ENV_BASE_URL = "http://example.com:8081"
$env:AAS_ENV_REPO_PATH = "http://example.com:8081/shells"
```

**CMD:**
```cmd
set AAS_ENV_BASE_URL=http://example.com:8081
set AAS_ENV_REPO_PATH=http://example.com:8081/shells
```

**Oder verwenden Sie eine .env-Datei** (erfordert `python-dotenv`):
```env
AAS_ENV_BASE_URL=http://example.com:8081
AAS_ENV_REPO_PATH=http://example.com:8081/shells
SUBMODEL_ENV_REPO_PATH=http://example.com:8081/submodels
```

## Verwendung

Führen Sie das Hauptskript aus:

```bash
python main.py
```

### Beispiel: AAS für Job Order erstellen

```python
import asyncio
from main import create_aas_for_job
from datetime import datetime

async def example():
    await create_aas_for_job({
        "JobOrder": {
            "JobOrderID": "JOB_001",
            "Description": "Produce 100 units of product XYZ",
            "WorkmasterId": "WM_001",
            "StartTime": datetime.now().isoformat(),
            "EndTime": datetime.now().isoformat(),
            "Priority": 500,
            "JobOrderParameters": {
                "JobName": ["XYZ", "xyz"],
                "OrderNumbers": [100, 101]
            }
        },
        "JobState": "Ended",
        "JobStateNumber": 5
    })

asyncio.run(example())
```

### Beispiel: AAS für Maschinenidentifikation erstellen

```python
import asyncio
from main import create_aas_for_identification
from basyx_helper_async import clean_id

async def example():
    await create_aas_for_identification(
        clean_id("Machine_001"),
        {
            "ProductInstanceUri": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
            "Manufacturer": "konzeptpark GmbH",
            "Model": "FactoryNexus",
            "SerialNumber": "SN123456789",
            "Location": "Factory Floor A"
        }
    )

asyncio.run(example())
```

## Projektstruktur

```
aas-client-async/
├── main.py                    # Hauptskript mit AAS-Erstellungsfunktionen
├── basyx_helper_async.py      # Hilfsfunktionen für BaSyx-Interaktion
├── requirements.txt           # Python-Abhängigkeiten
├── README.md                  # Diese Datei
└── env/                       # Virtuelle Umgebung (nicht versioniert)
```

## Abhängigkeiten

Die wichtigsten Abhängigkeiten sind:
- `basyx-python-sdk` - BaSyx Python SDK für AAS-Modelle
- `httpx` - Asynchroner HTTP-Client
- `anyio` - Asynchrone I/O-Bibliothek

Siehe `requirements.txt` für eine vollständige Liste.
