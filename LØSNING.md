# Factory Hack — Komplett løsningsdokumentasjon

**Team 8** | Atea AI Agent Hackathon | 12. mars 2026
**Repo:** https://github.com/enokmn/factory-hack

---

## Innholdsfortegnelse

1. [Oppsett og forutsetninger](#oppsett-og-forutsetninger)
2. [Challenge 0: Environment Setup](#challenge-0-environment-setup-)
3. [Challenge 1: Anomaly Classification og Fault Diagnosis](#challenge-1-anomaly-classification--fault-diagnosis-)
4. [Challenge 2: Repair Planner (.NET)](#challenge-2-repair-planner-net-)
5. [Challenge 3: Maintenance Scheduler og Parts Ordering](#challenge-3-maintenance-scheduler--parts-ordering-)
6. [Challenge 4: End-to-End Workflow med Aspire](#challenge-4-end-to-end-agent-workflow-med-aspire-)
7. [Bugfikser og erfaringer](#bugfikser-og-erfaringer)
8. [Oppsummering](#oppsummering)

---

## Oppsett og forutsetninger

### Maskinvare og programvare
- **OS:** macOS (Apple Silicon)
- **Runtime:** Python 3.14, .NET 10, Node.js LTS
- **Verktøy:** Azure CLI, uv (Python), Aspire CLI, git, GitHub CLI

### Steg-for-steg oppsett

```bash
# 1. Klon repo
cd /tmp && git clone https://github.com/enokmn/factory-hack.git
cd /tmp/factory-hack

# 2. Fiks .azure-rettigheter (om nødvendig på macOS)
sudo chown -R $(whoami):staff ~/.azure/

# 3. Logg inn på Azure
az login --use-device-code
# Bruker: hackathonuser8@AteaCloudDemosNorway.onmicrosoft.com
# Subscription: factory_hack_subscription

# 4. Python virtual environment (påkrevd på macOS pga. PEP 668)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Hent alle nøkler og endepunkter
cd challenge-0
echo "hackathonuser8-rg" | bash get-keys.sh
cat ../.env  # verifiser at alle variabler er satt

# 6. Eksportér miljøvariabler (KJØR DETTE I HVER NY TERMINAL)
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)

# 7. Seed fabrikkdata til Cosmos DB og Blob Storage
cd challenge-0
bash seed-data.sh
```

### Vanlige problemer og løsninger

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `pip install` feiler med «externally-managed-environment» | macOS PEP 668 | Bruk venv: `python3 -m venv .venv && source .venv/bin/activate` |
| `az` permission denied | `.azure/` eid av root | `sudo chown -R $(whoami):staff ~/.azure/` |
| Token utløpt | Azure-sesjon utløpt | `az login --use-device-code` på nytt |
| Manglende miljøvariabler | Ny terminal uten export | `source .venv/bin/activate && export $(cat .env | xargs)` |
| Seed-data viser «0 imported» | Data allerede seedet | Helt OK — seed-scriptet er idempotent |

---

## Challenge 0: Environment Setup ✅

**Tidsbruk:** ca. 15 minutter

### Hva ble gjort
1. Forket repo til https://github.com/enokmn/factory-hack
2. Valgte å jobbe **lokalt** (ikke Codespaces) — raskere og mer fleksibelt
3. Installerte Azure CLI via Homebrew
4. Logget inn med hackathon-bruker via device code
5. Bekreftet at resource group `hackathonuser8-rg` (francecentral) var provisjonert
6. Kjørte `get-keys.sh` → genererte `.env` med alle nøkler og endepunkter
7. Opprettet Python venv og installerte avhengigheter
8. Seedet data: 9 Cosmos DB-containere, wiki-filer til Blob Storage, APIM-proxyer

### Oppgaver som ble hoppet over
- **Task 4** (Deploy resources) — allerede utført av arrangør
- **Task 7** (Assign permissions) — allerede utført av arrangør

### Azure-ressurser (hackathonuser8-rg)

| Tjeneste | Ressursnavn |
|----------|-------------|
| Cosmos DB | `msagthack-cosmos-llwlhardm7pxa` |
| AI Foundry Hub | `msagthack-aifoundry-llwlhardm7pxa` |
| AI Foundry Project | `msagthack-aiproject-llwlhardm7pxa` |
| API Management | `msagthack-apim-llwlhardm7pxa` |
| AI Search | `msagthack-search-llwlhardm7pxa` |
| Storage Account | `msagthacksallwlhardm7pxa` |
| Application Insights | `msagthack-appinsights-llwlhardm7pxa` |
| Container Registry | `msagthackcrllwlhardm7pxa` |

### Seedet data

| Container | Innhold |
|-----------|---------|
| Machines | 5 maskiner (dekkproduksjonsutstyr) |
| Thresholds | 13 terskelverdier per maskintype |
| Telemetry | 10 telemetri-samples med bevisste anomalier |
| KnowledgeBase | 10 feilsøkingsguider |
| PartsInventory | 16 reservedeler |
| Technicians | 6 teknikere med kompetanseprofiler |
| WorkOrders | Tomme (fylles av agenter) |
| MaintenanceHistory | Historiske vedlikeholdsdata |
| MaintenanceWindows | Tilgjengelige vedlikeholdsvinduer |

---

## Challenge 1: Anomaly Classification & Fault Diagnosis ✅

**Tidsbruk:** ca. 30 minutter

### Task 1: Anomaly Classification Agent (direkte Cosmos DB)

Første agent — klassifiserer telemetri-avvik ved å sammenligne verdier direkte mot terskelverdier i Cosmos DB.

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-1
python agents/anomaly_classification_agent.py
```

**Resultat:** Agent opprettet i Azure AI Foundry. Testet med machine-001:
- `curing_temperature` 179.2°C → **WARNING** (terskel: 178°C)
- `cycle_time` 14.5 min → **WARNING** (terskel: 14 min)

### Task 2: MCP-servere i APIM + MCP-basert agent

#### Steg 1: Test at API-ene fungerer
```bash
# Machine API
curl -fsSL "$APIM_GATEWAY_URL/machine/machine-001" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json"

# Maintenance API (terskelverdier)
curl -fsSL "$APIM_GATEWAY_URL/maintenance/tire_curing_press" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json"
```

#### Steg 2: Opprett MCP-servere i Azure Portal
1. Gå til Azure Portal → API Management → **MCP Servers** → **Create MCP Server**

**MCP Server 1 — Maskindata:**
- API: `Machine API`
- Operasjon: `Get Machine`
- Display Name: `Get Machine Data`
- Navn: `get-machine-data`

**MCP Server 2 — Vedlikeholdsdata:**
- API: `Maintenance API`
- Operasjon: `Get Threshold`
- Display Name: `Get Maintenance Data`
- Navn: `get-maintenance-data`

#### Steg 3: Legg MCP-endepunkter i .env
```bash
echo 'MACHINE_MCP_SERVER_ENDPOINT=https://msagthack-apim-llwlhardm7pxa.azure-api.net/get-machine-data/mcp' >> /tmp/factory-hack/.env
echo 'MAINTENANCE_MCP_SERVER_ENDPOINT=https://msagthack-apim-llwlhardm7pxa.azure-api.net/get-maintenance-data/mcp' >> /tmp/factory-hack/.env
export $(cat /tmp/factory-hack/.env | xargs)
```

#### Steg 4: Kjør MCP-versjonen av agenten
```bash
python agents/anomaly_classification_agent_mcp.py
```

#### Steg 5: Test i Azure AI Foundry Portal
- Gå til https://ai.azure.com → Build → velg AnomalyClassificationAgent → Playground

### Task 3: Fault Diagnosis Agent med Foundry IQ (kunnskapsbase)

#### Steg 1: Opprett kunnskapskilde og kunnskapsbase

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
```

**Opprett knowledge source og knowledge base:**
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
print("Kunnskapskilde opprettet")

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
print("Kunnskapsbase opprettet")
PYEOF
```

**Opprett prosjektkobling for Foundry IQ:**
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
print("Prosjektkobling 'machine-wiki-connection' opprettet")
PYEOF
```

#### Steg 2: Legg til Foundry IQ MCP-verktøy i agenten

I `fault_diagnosis_agent.py`, erstatt `# TODO: add Foundry IQ MCP tool` med:
```python
MCPTool(
    server_label="machine-wiki",
    server_url=machine_wiki_mcp_endpoint,
    require_approval="never",
    project_connection_id="machine-wiki-connection"
)
```

#### Steg 3: Kjør Fault Diagnosis Agent
```bash
python agents/fault_diagnosis_agent.py
```

**Resultat:**
- **FaultType:** `curing_temperature_excessive`
- **RootCause:** `Heating element malfunction`
- **Severity:** `High`
- **MostLikelyRootCauses:** Heating element malfunction, Temperature sensor drift, Steam pressure too high, Thermostat failure, Inadequate cooling water flow
- Alle svar hentet fra kunnskapsbasen via Foundry IQ MCP

---

## Challenge 2: Repair Planner (.NET) ✅

**Tidsbruk:** ca. 10 minutter (brukte example-solution)

### Oppsett og kjøring

```bash
# Installér .NET (om ikke installert)
brew install dotnet  # .NET 10

# Kopier example-solution (alternativt: bygg fra scratch med Copilot @agentplanning)
cp -r challenge-2/example-solution/RepairPlanner challenge-2/RepairPlanner
cd challenge-2/RepairPlanner
dotnet restore

# Kjør agenten
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-2/RepairPlanner
dotnet run
```

### Resultat
- RepairPlannerAgent opprettet og registrert i Azure AI Foundry
- Arbeidsordre **WO-20260312-001** opprettet i Cosmos DB med:
  - **Tildelt tekniker:** tech-001 (John Smith — Senior Tire Equipment Technician)
  - **7 reparasjonsoppgaver** med sikkerhetsinstruksjoner
  - **Reservedeler:** TCP-HTR-4KW (varmeelement) + GEN-TS-K400 (termoelement)
  - **Estimert varighet:** 180 minutter

### Prosjektstruktur
```
RepairPlanner/
├── RepairPlanner.csproj      # .NET 10, Azure.AI.Projects, Cosmos SDK
├── Program.cs                # Dependency injection, sample fault, kjører workflow
├── RepairPlannerAgent.cs     # Agent: prompt → parse → lagre arbeidsordre
├── Models/
│   ├── DiagnosedFault.cs     # Input fra Fault Diagnosis Agent
│   ├── Technician.cs         # Cosmos DB: teknikere med kompetanseprofiler
│   ├── Part.cs               # Cosmos DB: reservedeler med lagerstatus
│   ├── WorkOrder.cs          # Output: komplett arbeidsordre
│   └── RepairTask.cs         # Individuelle reparasjonssteg
└── Services/
    ├── CosmosDbService.cs    # Cosmos DB-spørringer + skriving
    └── FaultMappingService.cs # Statisk feil→kompetanse/deler-mapping (10 feiltyper)
```

---

## Challenge 3: Maintenance Scheduler & Parts Ordering ✅

**Tidsbruk:** ca. 15 minutter (inkl. batch-kjøring)

### Task 1: Maintenance Scheduler Agent

```bash
cd /tmp/factory-hack
source .venv/bin/activate && export $(cat .env | xargs)
cd challenge-3
python agents/maintenance_scheduler_agent.py wo-2024-468
```

**Resultat:**
- MaintenanceSchedulerAgent registrert i Azure AI Foundry
- Vedlikeholdsplan `sched-1773306240` lagret i Cosmos DB
- Machine-005: **Risk Score 45/100**, Failure Probability 24%, Action: **SCHEDULED**
- Valgte nattvindu (22:00–06:00) med lav produksjonspåvirkning
- Arbeidsordre-status oppdatert til «Scheduled»

### Task 2: Parts Ordering Agent

```bash
python agents/parts_ordering_agent.py wo-2024-468
```

**Resultat:**
- PartsOrderingAgent registrert i Azure AI Foundry
- wo-2024-468: Alle deler på lager → status **«Ready»**
- wo-2024-456: 2 deler bestilt (PO-2f39a813, $575) → status **«PartsOrdered»**

### Task 3: Tracing og observability

```bash
python run-batch.py
```

**Resultat:** 10/10 kjøringer vellykket (5 scheduler + 5 parts ordering) på 118,6 sekunder.

Se traces i Azure AI Foundry:
1. Gå til https://ai.azure.com
2. Velg prosjekt → Agents → velg agent → Monitor/Tracing

### Viktige egenskaper
- Begge agenter bruker **persistent memory** (chat history per maskin/arbeidsordre i Cosmos DB)
- Tracing via **Application Insights** (`APPLICATIONINSIGHTS_CONNECTION_STRING`)
- Agentene leser og skriver til Cosmos DB (MaintenanceSchedules, PartsOrders, WorkOrders)
- Risk scores beregnes basert på historiske data, MTBF og feiltype — ikke bare LLM-intuisjon

---

## Challenge 4: End-to-End Agent Workflow med Aspire ✅

### Oversikt

Multi-agent orkestrering med .NET Aspire — kjører alle fem agenter i en samlet workflow med web-UI, Aspire Dashboard for observability, og A2A-kommunikasjon mellom Python- og .NET-agenter.

### Arkitektur

```
Bruker (React/Vite frontend)
    │
    ▼
.NET Workflow (Aspire-orkestrert)
    │
    ├──▶ 1. AnomalyClassificationAgent  (Azure AI Foundry, MCP-verktøy)
    ├──▶ 2. FaultDiagnosisAgent          (Azure AI Foundry, MCP + AI Search)
    ├──▶ 3. RepairPlannerAgent           (.NET lokal, A2A, Cosmos DB-verktøy)
    ├──▶ 4. MaintenanceSchedulerAgent    (Python lokal, A2A, Cosmos DB)
    └──▶ 5. PartsOrderingAgent           (Python lokal, A2A, Cosmos DB)
```

### Task 1: Installere Aspire CLI lokalt (macOS)

```bash
# Installer Aspire CLI som dotnet global tool
dotnet tool install -g aspire.cli

# Sett DOTNET_ROOT (nødvendig for brew-installert .NET på macOS)
export DOTNET_ROOT=/opt/homebrew/Cellar/dotnet/10.0.103/libexec
export PATH="$PATH:$HOME/.dotnet/tools"

# Verifiser
aspire --version
# 13.1.2+895a2f0b09d747a052aaaf0273d55ad0e2dc95b0
```

> **Merk:** I Codespaces installeres Aspire automatisk via devcontainer-feature. Lokalt på macOS må man installere manuelt. Pakkenavnet i NuGet er `aspire.cli` (ikke `aspire` eller `aspire8`).

### Task 2: Konfigurer og start Aspire

```bash
# Kopier .env til app-mappen og dotnetworkflow
cp /tmp/factory-hack/.env /tmp/factory-hack/challenge-4/agent-workflow/app/.env
cp /tmp/factory-hack/.env /tmp/factory-hack/challenge-4/agent-workflow/dotnetworkflow/.env

# Eksportér miljøvariabler
cd /tmp/factory-hack/challenge-4/agent-workflow
export $(cat /tmp/factory-hack/.env | xargs)

# Start Aspire
aspire run
```

**Aspire starter tre prosesser:**

| Prosess | Teknologi | Port | Ansvar |
|---------|-----------|------|--------|
| **app** | Python/uvicorn | 8000 | Anomaly + Fault Diagnosis-agenter, A2A-endepunkter for Scheduler/PartsOrdering |
| **dotnetworkflow** | .NET/Kestrel | dynamisk | RepairPlanner + workflow-orkestrering |
| **frontend** | React/Vite | dynamisk | Web-UI for å trigge og visualisere workflow |

### Task 3–6: Bruk web-grensesnittet

Etter at Aspire har startet, vises lenker i terminalen:
- **Frontend:** `http://localhost:{port}` (dynamisk — se Aspire-output)
- **Aspire Dashboard:** `https://localhost:17072/login?t={token}` (token vises i output)

**Steg:**
1. Åpne frontend-lenken i nettleseren
2. Fyll inn maskin-ID og telemetri, eller klikk **«Load Demo»** for eksempeldata
3. Klikk **«Trigger Anomaly»** for å starte hele pipelinen
4. Se alle fem agenter prosessere sekvensielt i UI-et
5. Åpne Aspire Dashboard for logger, helsestatus og traces

### Verifisert resultat — alle fem agenter end-to-end

Testet med `POST /api/analyze_machine` (machine-001, curing_temperature=179.2, cycle_time=14.5):

| Agent | Resultat |
|-------|----------|
| **AnomalyClassificationAgent** | Status: medium. 2 warnings — temperatur 179.2 > 178°C, syklustid 14.5 > 14 min |
| **FaultDiagnosisAgent** | Feiltype: curing_temperature_excessive. Rotårsak: Heating element malfunction. Alvorlighet: High |
| **RepairPlannerAgent** | Arbeidsordre opprettet. Tekniker: John Smith. Varighet: 90 min. 7 reparasjonsoppgaver. Cosmos DB-verktøy brukt |
| **MaintenanceSchedulerAgent** | Risk score: 75/100. Feilsannsynlighet: 62 %. Anbefalt handling: URGENT. Planlagt neste nattvindu |
| **PartsOrderingAgent** | Alle nødvendige deler på lager — ingen bestilling nødvendig |

---

## Bugfikser og erfaringer

### Bugfix 1: Blank frontend (VITE_API_URL)

**Symptom:** Frontenden viste blank side uten feilmeldinger.

**Årsak:** `apphost.cs` brukte `apiEndpoint.ToString()` inne i en lambda for å sette `VITE_API_URL`. Men `EndpointReference.ToString()` returnerer C#-typenavnet (`Aspire.Hosting.ApplicationModel.EndpointReference`) — ikke den faktiske URL-en.

**Løsning:** Erstatt lambda med `ReferenceExpression`:
```csharp
// Feil (gir typenavnet som URL):
.WithEnvironment("VITE_API_URL", () => {
    var baseUrl = (apiEndpoint.ToString() ?? ...).TrimEnd('/');
    return $"{baseUrl}/";
})

// Riktig (Aspire resolver endepunktet korrekt):
.WithEnvironment("VITE_API_URL", ReferenceExpression.Create($"{apiEndpoint}/"))
```

### Bugfix 2: Named agents vs. Assistants API

**Symptom:** `Invalid 'assistant_id': 'AnomalyClassificationAgent'. Expected an ID that begins with 'asst'.`

**Årsak:** Python-workflowen (`agents.py`) brukte `AzureAIAgentClient` med `agent_id="AnomalyClassificationAgent"`. Men `AzureAIAgentClient` bruker underliggende `AgentsClient` (OpenAI Assistants API) som krever ID-er med `asst_`-prefix. Våre agenter er opprettet med `create_version()` (named agents) som har ID-er som `AnomalyClassificationAgent:2`.

**Løsning:** Bruk `AIProjectClient.get_openai_client().responses.create()` med agent references i stedet:
```python
# Riktig måte å kalle named Foundry-agenter:
project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
openai_client = project_client.get_openai_client()
conversation = openai_client.conversations.create()
response = openai_client.responses.create(
    conversation=conversation.id,
    input=prompt,
    extra_body={"agent": {"name": "AnomalyClassificationAgent", "type": "agent_reference"}},
)
```

### Generelle erfaringer

| Erfaring | Detaljer |
|----------|---------|
| **Lokalt > Codespaces** | Alt fungerte raskere og mer pålitelig lokalt på macOS enn i GitHub Codespaces |
| **Aspire CLI-pakke** | Heter `aspire.cli` i NuGet, ikke `aspire` eller `aspire8` |
| **DOTNET_ROOT på macOS** | Må settes eksplisitt for brew-installert .NET: `export DOTNET_ROOT=/opt/homebrew/Cellar/dotnet/10.0.103/libexec` |
| **MCP-servere i APIM** | Må opprettes manuelt i Azure Portal — ingen CLI/API for dette ennå |
| **PEP 668** | macOS krever virtual environment for pip install — bruk alltid venv |

---

## Oppsummering

| Challenge | Status | Agenter og komponenter | Tidsbruk |
|-----------|--------|----------------------|----------|
| **0:** Environment Setup | ✅ | Azure-ressurser, Cosmos DB (9 containere), APIM, seed data | ~15 min |
| **1:** Anomaly & Fault Diagnosis | ✅ | AnomalyClassificationAgent, FaultDiagnosisAgent (MCP + Foundry IQ) | ~30 min |
| **2:** Repair Planner (.NET) | ✅ | RepairPlannerAgent (Cosmos DB-verktøy, arbeidsordre-oppretting) | ~10 min |
| **3:** Scheduler & Parts Ordering | ✅ | MaintenanceSchedulerAgent, PartsOrderingAgent (memory, tracing) | ~15 min |
| **4:** End-to-End Workflow | ✅ | Aspire host, React frontend, A2A, OpenTelemetry | ~45 min |

**Totalt fem agenter** opprettet, verifisert og fungerende — orkestrert via .NET Aspire med full end-to-end workflow.

**Dokumentasjon:**
- `LØSNING.md` — denne filen (steg-for-steg løsning)
- `PEDAGOGIKK.md` — læringsmål og analyse av hva Atea vil lære oss
