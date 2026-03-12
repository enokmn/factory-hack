# Challenge 1: Anomaly Classification & Fault Diagnosis — Teknisk oppskrift

**Atea AI Agent Hackathon — 12. mars 2026 | Team 8**

---

## Mål

Bygge to AI-agenter: en **AnomalyClassificationAgent** som klassifiserer telemetri-anomalier, og en **FaultDiagnosisAgent** som diagnostiserer rotårsaken. Gjennom tre oppgaver lærer du tre fundamentalt forskjellige integrasjonsmønstre:

| Task | Mønster | Beskrivelse |
|------|---------|-------------|
| 1 | Direkte Cosmos DB | Python-funksjoner kaller Cosmos DB direkte |
| 2 | MCP via APIM | Agent bruker MCP-servere eksponert gjennom API Management |
| 3 | Foundry IQ (RAG) | Agent søker i kunnskapsbase via MCP |

## Forutsetninger

- Challenge 0 fullført (Azure-miljø, `.env`, seed-data)
- Python venv aktivert med avhengigheter installert
- Miljøvariabler eksportert

```bash
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)
```

## Tidsbruk

Ca. 30 minutter

---

## Task 1: Anomaly Classification Agent (direkte Cosmos DB)

### Hva den gjør

Agenten mottar telemetri-data for en maskin og sammenligner verdiene mot terskelverdier lagret i Cosmos DB. Den returnerer et strukturert JSON-svar med advarsler og alvorlighetsgrad.

### Kjør agenten

```bash
cd /tmp/factory-hack/challenge-1
python agents/anomaly_classification_agent.py
```

### Hva skjer under panseret

1. **Cosmos DB-tilkobling:** Scriptet kobler direkte til `FactoryOpsDB`-databasen og leser fra `Thresholds` og `Machines`-containerne
2. **Verktøyfunksjoner:** To Python-funksjoner (`get_thresholds`, `get_machine_data`) registreres som verktøy agenten kan kalle
3. **Agent Framework:** `AzureAIClient` oppretter agenten i Azure AI Foundry med instruksjoner og verktøy
4. **Test:** Agenten tester seg selv med `machine-001` og to anomalier

### Forventet resultat

```
✅ Created Anomaly Classification Agent: <agent-id>
🧪 Testing the agent with a sample query...
✅ Agent response: {
  "status": "medium",
  "alerts": [
    {"name": "curing_temperature", "severity": "warning", "description": "179.2°C exceeds warning threshold 178°C"},
    {"name": "cycle_time", "severity": "warning", "description": "14.5 min exceeds warning threshold 14 min"}
  ],
  "summary": {"totalRecordsProcessed": 2, "violations": {"critical": 0, "warning": 2}}
}
```

### Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `ModuleNotFoundError: agent_framework` | Manglende pakker | `pip install -r requirements.txt` i venv |
| `CosmosHttpResponseError: 401` | Feil nøkler | Sjekk at `COSMOS_ENDPOINT` og `COSMOS_KEY` er eksportert |
| `DefaultAzureCredential` feiler | Ikke logget inn | `az login --use-device-code` |
| Tomt resultat fra `get_thresholds` | Feil maskintype | Sjekk at seed-data er kjørt (`bash seed-data.sh`) |

---

## Task 2: MCP-servere i APIM + MCP-basert agent

### Steg 1: Verifiser at API-ene fungerer

```bash
# Machine API — hent maskindata
curl -fsSL "$APIM_GATEWAY_URL/machine/machine-001" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json" | python3 -m json.tool

# Maintenance API — hent terskelverdier
curl -fsSL "$APIM_GATEWAY_URL/maintenance/tire_curing_press" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json" | python3 -m json.tool
```

Begge skal returnere JSON-data. Hvis ikke — sjekk at APIM-proxyer ble opprettet under seed.

### Steg 2: Opprett MCP-servere i Azure Portal

1. Gå til **Azure Portal** → søk etter din **API Management**-ressurs
2. I venstre meny: **MCP Servers** → **Create MCP Server**

**MCP Server 1 — Maskindata:**
- API: `Machine API`
- Operasjon: `Get Machine`
- Display Name: `Get Machine Data`
- MCP Server Name: `get-machine-data`

**MCP Server 2 — Vedlikeholdsdata:**
- API: `Maintenance API`
- Operasjon: `Get Threshold`
- Display Name: `Get Maintenance Data`
- MCP Server Name: `get-maintenance-data`

> **Merk:** MCP-servere i APIM må opprettes manuelt i portalen — det finnes (per mars 2026) ingen CLI/API for dette.

### Steg 3: Legg MCP-endepunkter i .env

Erstatt `<din-apim-ressurs>` med ditt APIM-ressursnavn:

```bash
echo 'MACHINE_MCP_SERVER_ENDPOINT=https://<din-apim-ressurs>.azure-api.net/get-machine-data/mcp' >> /tmp/factory-hack/.env
echo 'MAINTENANCE_MCP_SERVER_ENDPOINT=https://<din-apim-ressurs>.azure-api.net/get-maintenance-data/mcp' >> /tmp/factory-hack/.env
export $(cat /tmp/factory-hack/.env | xargs)
```

### Steg 4: Kjør MCP-versjonen av agenten

```bash
python agents/anomaly_classification_agent_mcp.py
```

### Hva skjer under panseret

1. **Prosjektkoblinger:** Scriptet oppretter to `RemoteTool`-koblinger i Azure AI Foundry som peker til MCP-endepunktene i APIM
2. **MCPTool:** I stedet for Python-funksjoner bruker agenten `MCPTool`-objekter som refererer til MCP-serverne
3. **Named agent:** Agenten opprettes med `create_version()` (ikke `create_agent()`) — dette gir en named agent i Foundry

### Steg 5: Test i Azure AI Foundry Portal

1. Gå til https://ai.azure.com → **Build** → velg prosjektet
2. Finn **AnomalyClassificationAgent** → klikk **Playground**
3. Test med: *"Classify anomalies for machine-001: curing_temperature=179.2, cycle_time=14.5"*

### Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `403 Forbidden` ved MCP-kall | APIM subscription key mangler | Sjekk at `APIM_SUBSCRIPTION_KEY` er korrekt i `.env` |
| `Connection already exists` | Kjørt scriptet flere ganger | Helt OK — `create_or_update` er idempotent |
| Agent opprettes men test feiler | MCP-server ikke opprettet i portal | Sjekk steg 2 — MCP-serverne må opprettes manuelt |
| `MCPTool` not found | Gammel SDK-versjon | `pip install --upgrade azure-ai-projects` |

### Viktig forskjell: Task 1 vs Task 2

| | Task 1 (direkte) | Task 2 (MCP) |
|--|------------------|--------------|
| Datakilde | Cosmos DB via Python SDK | Cosmos DB via APIM → MCP |
| Portabilitet | Kun lokalt | Fungerer lokalt, i Foundry Portal, og i sky |
| Verktøy | Python-funksjoner | MCPTool (standardisert) |
| Agent-type | Ephemeral (AzureAIClient) | Named (create_version) |

---

## Task 3: Fault Diagnosis Agent med Foundry IQ

### Steg 1: Opprett kunnskapskilde og kunnskapsbase

Dette er et lengre steg som setter opp Foundry IQ — Microsofts administrerte RAG-løsning.

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
```

**Opprett knowledge source (Blob Storage → AI Search):**

```python
python3 << 'PYEOF'
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureBlobKnowledgeSource, AzureBlobKnowledgeSourceParameters,
    AzureOpenAIVectorizerParameters, KnowledgeBase, KnowledgeBaseAzureOpenAIModel,
    KnowledgeRetrievalLowReasoningEffort, KnowledgeRetrievalOutputMode,
    KnowledgeSourceAzureOpenAIVectorizer, KnowledgeSourceContentExtractionMode,
    KnowledgeSourceIngestionParameters, KnowledgeSourceReference,
)

storage_conn = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
search_endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"]
search_key = os.environ["SEARCH_ADMIN_KEY"]
model = os.environ["MODEL_DEPLOYMENT_NAME"]
embedding_model = os.environ["EMBEDDING_MODEL_DEPLOYMENT_NAME"]
openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
openai_key = os.environ["AZURE_OPENAI_KEY"]

client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))

# Kunnskapskilde: Blob Storage med fabrikk-wiki
ks = AzureBlobKnowledgeSource(
    name="machine-wiki-blob-ks",
    description="Fabrikk-wiki fra Blob Storage",
    azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
        connection_string=storage_conn, container_name="machine-wiki", is_adls_gen2=False,
        ingestion_parameters=KnowledgeSourceIngestionParameters(
            disable_image_verbalization=False,
            chat_completion_model=KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint, deployment_name=model,
                    api_key=openai_key, model_name=model)),
            embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint, deployment_name=embedding_model,
                    api_key=openai_key, model_name=embedding_model)),
            content_extraction_mode=KnowledgeSourceContentExtractionMode.MINIMAL)))
client.create_or_update_knowledge_source(ks)
print("✅ Kunnskapskilde opprettet")

# Kunnskapsbase: Indeksert søk med RAG
aoai = AzureOpenAIVectorizerParameters(
    resource_url=openai_endpoint, api_key=openai_key, deployment_name=model, model_name=model)
kb = KnowledgeBase(
    name="machine-kb",
    description="Kunnskapsbase for feilsøking av produksjonsmaskiner",
    retrieval_instructions="Bruk machine-wiki-blob-ks for å finne mulige årsaker",
    answer_instructions="Gi et enkelt svar basert på dokumentene som ble funnet.",
    output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    knowledge_sources=[KnowledgeSourceReference(name="machine-wiki-blob-ks")],
    models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=aoai)],
    retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort)
client.create_or_update_knowledge_base(kb)
print("✅ Kunnskapsbase opprettet")
PYEOF
```

### Steg 2: Opprett prosjektkobling for Foundry IQ

```python
python3 << 'PYEOF'
import os, requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
project_resource_id = os.environ["AZURE_AI_PROJECT_RESOURCE_ID"]
search_endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"]
mcp_endpoint = f"{search_endpoint}/knowledgebases/machine-kb/mcp?api-version=2025-11-01-preview"

bearer = get_bearer_token_provider(credential, "https://management.azure.com/.default")
response = requests.put(
    f"https://management.azure.com{project_resource_id}/connections/machine-wiki-connection?api-version=2025-10-01-preview",
    headers={"Authorization": f"Bearer {bearer()}"},
    json={
        "name": "machine-wiki-connection",
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": mcp_endpoint,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"}
        }
    })
response.raise_for_status()
print("✅ Prosjektkobling 'machine-wiki-connection' opprettet")
PYEOF
```

### Steg 3: Kjør Fault Diagnosis Agent

```bash
python agents/fault_diagnosis_agent.py
```

### Forventet resultat

```json
{
  "MachineId": "machine-001",
  "FaultType": "curing_temperature_excessive",
  "RootCause": "Heating element malfunction",
  "Severity": "High",
  "DetectedAt": "2026-03-12T10:30:00Z",
  "Metadata": {
    "MostLikelyRootCauses": [
      "Heating element malfunction",
      "Temperature sensor drift",
      "Steam pressure too high",
      "Thermostat failure",
      "Inadequate cooling water flow"
    ]
  }
}
```

Alle svar er hentet fra kunnskapsbasen via Foundry IQ MCP — **ikke** fra LLM-ens generelle kunnskap. Agenten er instruert til å svare «I don't know» hvis svaret ikke finnes i kunnskapsbasen.

### Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `Knowledge source not found` | Indexering ikke ferdig | Vent 2-3 minutter — Foundry IQ indekserer asynkront |
| `machine-wiki-connection` feiler | Manglende tilganger | Sjekk at prosjektet har Managed Identity med Search-tilgang |
| Agent svarer «I don't know» | Wiki-filer mangler | Sjekk at seed-data lastet opp wiki-filer til Blob Storage |
| `SEARCH_SERVICE_ENDPOINT` mangler `/` | URL-formatering | Sjekk at endepunktet ender med `/` |

---

## Verifisering — alle tre agenter

Etter fullført Challenge 1 skal du ha:

| Agent | Registrert i Foundry | Testet | Verktøy |
|-------|---------------------|--------|---------|
| AnomalyClassificationAgent (Task 1) | ✅ | ✅ | Python-funksjoner (Cosmos DB direkte) |
| AnomalyClassificationAgent (Task 2) | ✅ | ✅ | MCP-servere via APIM |
| FaultDiagnosisAgent (Task 3) | ✅ | ✅ | MCP (APIM + Foundry IQ) |

Alle agenter er synlige i Azure AI Foundry Portal under prosjektet ditt.

---

## Lærdom

- **MCP gjør agenter portable** — fra lokal testing til sky-deployment uten kodeendring
- **MCP-servere i APIM opprettes manuelt** i portalen (ingen CLI ennå)
- **Named agents** (`create_version`) bruker `openai_client.responses.create()` med `extra_body` — **ikke** `AgentsClient`
- **Foundry IQ** håndterer indeksering, chunking og embedding automatisk — du peker bare på Blob Storage
- **Grounding** er eksplisitt: agenten svarer kun basert på verktøydata, aldri egen kunnskap
