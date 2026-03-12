# Factory Hack — Løsningsdokumentasjon

**Team 8** | Atea AI Agent Hackathon | 2026-03-12

---

## Oppsett

### Forutsetninger
- macOS (Apple Silicon), lokalt miljø
- Azure CLI: `brew install azure-cli`
- Python 3 med venv

### Steg-for-steg

```bash
# 1. Klon repo
cd /tmp && git clone https://github.com/enokmn/factory-hack.git
cd /tmp/factory-hack

# 2. Fix .azure permissions (om nødvendig)
sudo chown -R $(whoami):staff ~/.azure/

# 3. Logg inn på Azure
az login --use-device-code
# Bruker: hackathonuser8@AteaCloudDemosNorway.onmicrosoft.com
# Subscription: factory_hack_subscription

# 4. Python venv (macOS PEP 668)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Hent nøkler
cd challenge-0
echo "hackathonuser8-rg" | bash get-keys.sh
cat ../.env  # verifiser

# 6. Eksportér env vars (gjør dette i HVER ny terminal)
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)

# 7. Seed data
cd challenge-0
bash seed-data.sh
```

### Feilsøking
| Problem | Løsning |
|---------|---------|
| pip install feiler | Bruk venv: `source .venv/bin/activate` |
| az permission denied | `sudo chown -R $(whoami):staff ~/.azure/` |
| Token utløpt | `az login --use-device-code` på nytt |
| Manglende env vars | `export $(cat .env | xargs)` |
| Seed "0 imported" | Data allerede seedet — OK (idempotent) |

---

## Challenge 0: Environment Setup ✅

**Tid:** ~15 min

### Hva ble gjort
1. Forket repo → https://github.com/enokmn/factory-hack
2. Jobbet lokalt (ikke Codespaces — sparer gratis-konto)
3. Installerte Azure CLI via Homebrew
4. Logget inn med hackathon-bruker
5. Resource group `hackathonuser8-rg` allerede provisjonert (francecentral)
6. Kjørte `get-keys.sh` → genererte .env med alle nøkler
7. Opprettet Python venv og installerte dependencies
8. Seedet data: 9 Cosmos DB containere + blob storage wiki + APIM proxyer

### Skipte tasks
- **Task 4** (Deploy resources) — allerede gjort av arrangør
- **Task 7** (Assign permissions) — allerede gjort av arrangør

### Azure-ressurser
| Ressurs | Navn |
|---------|------|
| Cosmos DB | `msagthack-cosmos-llwlhardm7pxa` |
| AI Foundry Hub | `msagthack-aifoundry-llwlhardm7pxa` |
| AI Foundry Project | `msagthack-aiproject-llwlhardm7pxa` |
| APIM | `msagthack-apim-llwlhardm7pxa` |
| AI Search | `msagthack-search-llwlhardm7pxa` |
| Storage | `msagthacksallwlhardm7pxa` |
| App Insights | `msagthack-appinsights-llwlhardm7pxa` |
| Container Registry | `msagthackcrllwlhardm7pxa` |

---

## Challenge 1: Anomaly Classification & Fault Diagnosis ✅

**Tid:** ~30 min

### Task 1: Anomaly Classification Agent (direkte Cosmos DB) ✅

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-1
python agents/anomaly_classification_agent.py
```

**Resultat:** Agent opprettet (ID: `d8c2615c-ab3c-4470-85b2-d9d511a9e51c`). Klassifiserte korrekt:
- curing_temperature 179.2°C → WARNING (threshold 178°C)
- cycle_time 14.5 → WARNING (threshold 14)

**Resultat MCP-agent:** Klassifiserte korrekt via remote MCP tools:
- curing_temperature 179.2°C → WARNING
- cycle_time mangler threshold-data i Maintenance API (forventet)

### Task 2: MCP-servere i APIM

#### 2.1 Test API-ene
```bash
# Test Machine API
curl -fsSL "$APIM_GATEWAY_URL/machine/machine-001" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json"

# Test Maintenance API
curl -fsSL "$APIM_GATEWAY_URL/maintenance/tire_curing_press" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json"
```

#### 2.2 Opprett MCP-servere (Azure Portal)
1. Gå til Azure Portal → API Management (`msagthack-apim-llwlhardm7pxa`)
2. Klikk **MCP Servers** → **Create MCP Server** → **Expose an API as MCP Server**

**MCP Server 1 — Machine:**
- API: `Machine API`
- Operations: `Get Machine`
- Display Name: `Get Machine Data`
- Name: `get-machine-data`
- Description: `Gets details about a specific machine`

**MCP Server 2 — Maintenance:**
- API: `Maintenance API`
- Operations: `Get Threshold`
- Display Name: `Get Maintenance Data`
- Name: `get-maintenance-data`
- Description: `Gets maintenance data such as thresholds for maintenance alerts`

3. Kopier begge MCP Server URL-er og legg i .env:
```bash
echo 'MACHINE_MCP_SERVER_ENDPOINT=https://msagthack-apim-llwlhardm7pxa.azure-api.net/get-machine-data/mcp' >> /tmp/factory-hack/.env
echo 'MAINTENANCE_MCP_SERVER_ENDPOINT=https://msagthack-apim-llwlhardm7pxa.azure-api.net/get-maintenance-data/mcp' >> /tmp/factory-hack/.env
export $(cat /tmp/factory-hack/.env | xargs)
```

#### 2.3-2.4 Kjør MCP-versjonen
```bash
python agents/anomaly_classification_agent_mcp.py
```

#### 2.5 Test i Foundry Portal
- Gå til https://ai.azure.com → Build → velg AnomalyClassificationAgent
- Test-spørringer i playground

### Task 3: Fault Diagnosis Agent med Foundry IQ

#### 3.2 Opprett knowledge base
Kan kjøres som notebook ELLER som Python-script. Vi kjørte det som script:

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
```

**Steg 1 — Knowledge source + knowledge base:**
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

storage_connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
search_endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"]
search_key = os.environ["SEARCH_ADMIN_KEY"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
embedding_model_deployment_name = os.environ["EMBEDDING_MODEL_DEPLOYMENT_NAME"]
openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
openai_key = os.environ["AZURE_OPENAI_KEY"]

index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))

ks = AzureBlobKnowledgeSource(
    name="machine-wiki-blob-ks",
    description="Knowledge source from blob storage machine wiki",
    azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
        connection_string=storage_connection_string,
        container_name="machine-wiki", is_adls_gen2=False,
        ingestion_parameters=KnowledgeSourceIngestionParameters(
            disable_image_verbalization=False,
            chat_completion_model=KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint, deployment_name=model_deployment_name,
                    api_key=openai_key, model_name=model_deployment_name)),
            embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint, deployment_name=embedding_model_deployment_name,
                    api_key=openai_key, model_name=embedding_model_deployment_name)),
            content_extraction_mode=KnowledgeSourceContentExtractionMode.MINIMAL)))
index_client.create_or_update_knowledge_source(ks)
print("✅ Knowledge source created")

aoai_params = AzureOpenAIVectorizerParameters(
    resource_url=openai_endpoint, api_key=openai_key,
    deployment_name=model_deployment_name, model_name=model_deployment_name)
kb = KnowledgeBase(
    name="machine-kb",
    description="Knowledge base for manufacturing machine issues",
    retrieval_instructions="Use the machine-wiki-blob-ks to query potential root causes",
    answer_instructions="Provide a single sentence for the likely cause based on retrieved documents.",
    output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    knowledge_sources=[KnowledgeSourceReference(name="machine-wiki-blob-ks")],
    models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=aoai_params)],
    retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort)
index_client.create_or_update_knowledge_base(kb)
print("✅ Knowledge base created")
PYEOF
```

**Steg 2 — Project connection for Foundry IQ:**
```python
python3 << 'PYEOF'
import os, requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
project_resource_id = os.environ["AZURE_AI_PROJECT_RESOURCE_ID"]
search_endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"]
mcp_endpoint = f"{search_endpoint}/knowledgebases/machine-kb/mcp?api-version=2025-11-01-preview"

bearer_token_provider = get_bearer_token_provider(credential, "https://management.azure.com/.default")
headers = {"Authorization": f"Bearer {bearer_token_provider()}"}

response = requests.put(
    f"https://management.azure.com{project_resource_id}/connections/machine-wiki-connection?api-version=2025-10-01-preview",
    headers=headers,
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
print("✅ Connection 'machine-wiki-connection' created")
PYEOF
```

#### 3.3 Legg til Foundry IQ MCP tool
I `fault_diagnosis_agent.py`, erstatt `# TODO: add Foundry IQ MCP tool` med:
```python
MCPTool(
    server_label="machine-wiki",
    server_url=machine_wiki_mcp_endpoint,
    require_approval="never",
    project_connection_id="machine-wiki-connection"
)
```

#### 3.4 Kjør agenten
```bash
python agents/fault_diagnosis_agent.py
```

**Resultat Fault Diagnosis Agent:**
- FaultType: `curing_temperature_excessive`
- RootCause: `Heating element malfunction`
- Severity: `High`
- MostLikelyRootCauses: Heating element malfunction, Temperature sensor drift, Steam pressure too high, Thermostat failure, Inadequate cooling water flow
- Hentet fra knowledge base via Foundry IQ MCP ✅

---

## Challenge 2: Repair Planner (.NET + Copilot) ✅

**Tid:** ~10 min (brukte example-solution)

### Oppsett
```bash
# Installér .NET (om ikke installert)
brew install dotnet  # Installerer .NET 10

# Kopier example-solution (alternativt: bygg fra scratch med Copilot @agentplanning)
cp -r challenge-2/example-solution/RepairPlanner challenge-2/RepairPlanner
cd challenge-2/RepairPlanner
dotnet restore
```

### Kjør
```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-2/RepairPlanner
dotnet run
```

### Resultat
- RepairPlannerAgent opprettet i Foundry
- Work order `WO-20260312-001` lagret i Cosmos DB
- Tildelt tekniker `tech-001` (John Smith — Senior Tire Equipment Technician)
- 7 reparasjonsoppgaver generert med sikkerhetsinstruksjoner
- Deler: TCP-HTR-4KW (heater element) + GEN-TS-K400 (thermocouple)
- Estimert varighet: 180 min

### Prosjektstruktur
```
RepairPlanner/
├── RepairPlanner.csproj      # .NET 10, Azure.AI.Projects, Cosmos SDK
├── Program.cs                # DI setup, sample fault, kjører workflow
├── RepairPlannerAgent.cs     # Agent: prompt → parse → save work order
├── Models/
│   ├── DiagnosedFault.cs     # Input fra Fault Diagnosis Agent
│   ├── Technician.cs         # Cosmos DB: teknikere med skills
│   ├── Part.cs               # Cosmos DB: reservedeler
│   ├── WorkOrder.cs          # Output: komplett arbeidsordre
│   ├── RepairTask.cs         # Individuelle reparasjonssteg
│   └── WorkOrderPartUsage.cs # Deler brukt i ordren
└── Services/
    ├── CosmosDbService.cs    # Cosmos DB queries + write
    ├── CosmosDbOptions.cs    # Config
    └── FaultMappingService.cs # Statisk fault→skills/parts mapping
```

### Nøkkelpunkter
- Bruker `Azure.AI.Projects` + `Microsoft.Agents.AI` SDK-er
- Dual JSON-attributter (`[JsonPropertyName]` + `[JsonProperty]`) for Cosmos DB
- `NumberHandling = AllowReadingFromString` — LLM returnerer noen ganger "60" i stedet for 60
- `NoWarn CA2252` i .csproj for preview API-warnings

---

## Challenge 3: Maintenance Scheduler & Parts Ordering ✅

**Tid:** ~15 min (inkl. batch-kjøring)

### Task 1: Maintenance Scheduler Agent ✅

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-3
python agents/maintenance_scheduler_agent.py wo-2024-468
```

**Resultat:**
- MaintenanceSchedulerAgent registrert i Foundry
- Schedule `sched-1773306240` lagret i Cosmos DB
- machine-005: Risk Score 45/100, Failure Probability 24%, Action: SCHEDULED
- Valgte natt-vindu (22:00-06:00) med lav produksjonsimpakt
- Work order status oppdatert til "Scheduled"

### Task 2: Parts Ordering Agent ✅

```bash
python agents/parts_ordering_agent.py wo-2024-468
```

**Resultat:**
- PartsOrderingAgent registrert i Foundry
- wo-2024-468: Alle deler på lager → status "Ready"
- wo-2024-456: 2 deler bestilt (PO-2f39a813, $575) → status "PartsOrdered"

### Task 3: Tracing & Observability ✅

```bash
python run-batch.py
```

**Resultat:** 10/10 kjøringer vellykket (5 scheduler + 5 parts ordering) på 118.6 sek.

Se traces i Azure AI Foundry:
1. Gå til https://ai.azure.com
2. Velg prosjekt → Agents → MaintenanceSchedulerAgent/PartsOrderingAgent → Monitor

### Nøkkelpunkter
- Begge agenter bruker **agent memory** (chat history per maskin/work order i Cosmos DB)
- Tracing via **Application Insights** (`APPLICATIONINSIGHTS_CONNECTION_STRING`)
- Agentene leser/skriver til Cosmos DB (MaintenanceSchedules, PartsOrders, WorkOrders)
- Risk scores beregnes basert på historiske data, MTBF, og fault type

---

## Oppsummering

| Challenge | Status | Agenter opprettet |
|-----------|--------|-------------------|
| 0: Environment Setup | ✅ | - |
| 1: Anomaly & Fault Diagnosis | ✅ | AnomalyClassificationAgent, FaultDiagnosisAgent |
| 2: Repair Planner (.NET) | ✅ | RepairPlannerAgent |
| 3: Scheduler & Parts Ordering | ✅ | MaintenanceSchedulerAgent, PartsOrderingAgent |

**Totalt 5 agenter** opprettet og fungerende i Azure AI Foundry.
