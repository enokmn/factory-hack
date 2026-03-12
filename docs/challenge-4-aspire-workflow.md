# Challenge 4: End-to-End Agent Workflow med Aspire — Teknisk oppskrift

**Atea AI Agent Hackathon — 12. mars 2026 | Team 8**

---

## Mål

Koble alle fem agenter sammen i en **end-to-end pipeline** orkestrert av .NET Aspire. En React-frontend lar brukeren trigge hele workflowen, og Aspire Dashboard gir full observability.

## Arkitektur

```
Bruker (React/Vite frontend)
    │
    ▼
.NET Workflow (Aspire-orkestrert)
    │
    ├──▶ 1. AnomalyClassificationAgent  (Azure AI Foundry, MCP)
    ├──▶ 2. FaultDiagnosisAgent          (Azure AI Foundry, MCP + Foundry IQ)
    ├──▶ 3. RepairPlannerAgent           (.NET, A2A, Cosmos DB)
    ├──▶ 4. MaintenanceSchedulerAgent    (Python, A2A, Cosmos DB)
    └──▶ 5. PartsOrderingAgent           (Python, A2A, Cosmos DB)
```

## Forutsetninger

- Challenge 0–3 fullført (alle agenter registrert i Foundry)
- .NET 10, Node.js LTS, Python 3.12+ installert
- Miljøvariabler eksportert

## Tidsbruk

Ca. 45 minutter (inkl. feilsøking av bugs)

---

## Task 1: Installer Aspire CLI lokalt (macOS)

```bash
# Installer som global dotnet tool
dotnet tool install -g aspire.cli

# Sett DOTNET_ROOT (NØDVENDIG for brew-installert .NET på macOS)
export DOTNET_ROOT=/opt/homebrew/Cellar/dotnet/10.0.103/libexec
export PATH="$PATH:$HOME/.dotnet/tools"

# Verifiser
aspire --version
# Forventet: 13.1.2+...
```

> **Viktig:** Pakkenavnet i NuGet er `aspire.cli` — **ikke** `aspire` eller `aspire8`. Søk med `dotnet tool search aspire` om du er usikker.

### Feilsøking: Aspire finner ikke .NET

**Symptom:**
```
You must install .NET to run this application.
```

**Årsak:** Aspire leter etter .NET på standard path, men brew installerer til `/opt/homebrew/Cellar/dotnet/...`

**Løsning:**
```bash
# Finn din dotnet-path
dotnet --info | grep "Base Path"
# Eksempel: /opt/homebrew/Cellar/dotnet/10.0.103/libexec/sdk/10.0.103/

# Sett DOTNET_ROOT til parent av sdk-mappen
export DOTNET_ROOT=/opt/homebrew/Cellar/dotnet/10.0.103/libexec
```

---

## Task 2: Konfigurer og start Aspire

### Kopier .env-filer

```bash
# Aspire-appen trenger .env i flere mapper
cp /tmp/factory-hack/.env /tmp/factory-hack/challenge-4/agent-workflow/app/.env
cp /tmp/factory-hack/.env /tmp/factory-hack/challenge-4/agent-workflow/dotnetworkflow/.env
```

### Start Aspire

```bash
cd /tmp/factory-hack/challenge-4/agent-workflow
export $(cat /tmp/factory-hack/.env | xargs)
aspire run
```

### Hva Aspire starter

| Prosess | Teknologi | Port | Ansvar |
|---------|-----------|------|--------|
| **app** | Python/uvicorn | 8000 | Anomaly + Fault Diagnosis, A2A for Scheduler/PartsOrdering |
| **dotnetworkflow** | .NET/Kestrel | dynamisk | RepairPlanner + workflow-orkestrering |
| **frontend** | React/Vite | dynamisk | Web-UI |
| **Aspire Dashboard** | .NET | 17072 | Logger, helse, traces |

Lenker vises i terminalen etter oppstart. Dashboard-lenken inkluderer et token for autentisering.

---

## Task 3–6: Bruk web-grensesnittet

1. Åpne **frontend-lenken** fra Aspire-output i nettleseren
2. Klikk **«Load Demo»** for å fylle inn eksempeldata (machine-001, telemetri med anomalier)
3. Klikk **«Trigger Anomaly»** for å starte hele pipelinen
4. Se alle fem agenter prosessere sekvensielt i UI-et
5. Åpne **Aspire Dashboard** for logger, helsestatus og traces

### Alternativt: Test via curl

```bash
# Finn dotnetworkflow-porten fra Aspire-output
curl -X POST http://localhost:5231/api/analyze_machine \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "machine-001",
    "telemetry": [
      {"metric": "curing_temperature", "value": 179.2},
      {"metric": "cycle_time", "value": 14.5}
    ]
  }'
```

---

## Verifisert resultat — alle fem agenter

| Agent | Resultat |
|-------|----------|
| **AnomalyClassificationAgent** | Status: medium. 2 warnings — temperatur 179.2 > 178°C, syklustid 14.5 > 14 min |
| **FaultDiagnosisAgent** | Feiltype: curing_temperature_excessive. Rotårsak: Heating element malfunction. Alvorlighet: High |
| **RepairPlannerAgent** | Arbeidsordre opprettet. Tekniker: John Smith. Varighet: 90 min. 7 oppgaver |
| **MaintenanceSchedulerAgent** | Risk score: 75/100. Feilsannsynlighet: 62%. URGENT. Neste nattvindu |
| **PartsOrderingAgent** | Alle nødvendige deler på lager — ingen bestilling nødvendig |

---

## Bugfikser vi måtte gjøre

### Bugfix 1: Blank frontend (VITE_API_URL)

**Symptom:** Frontenden lastet men viste blank side.

**Årsak:** I `apphost.cs` ble `VITE_API_URL` satt via en lambda med `apiEndpoint.ToString()`. Men `EndpointReference.ToString()` i Aspire returnerer **C#-typenavnet** (`Aspire.Hosting.ApplicationModel.EndpointReference`) — ikke den faktiske URL-en.

**Fil:** `challenge-4/agent-workflow/apphost.cs`

```csharp
// FØR (feil — gir typenavnet som URL):
.WithEnvironment("VITE_API_URL", () => {
    var baseUrl = (apiEndpoint.ToString()
        ?? throw new InvalidOperationException("...")).TrimEnd('/');
    return $"{baseUrl}/";
})

// ETTER (riktig — Aspire resolver endepunktet):
.WithEnvironment("VITE_API_URL", ReferenceExpression.Create($"{apiEndpoint}/"))
```

### Bugfix 2: Named agents vs. Assistants API

**Symptom:**
```
Invalid 'assistant_id': 'AnomalyClassificationAgent'. Expected an ID that begins with 'asst'.
```

**Årsak:** Python-workflowen (`agents.py`) brukte `AzureAIAgentClient` med `agent_id="AnomalyClassificationAgent"`. Men `AzureAIAgentClient` bruker `AgentsClient` (OpenAI Assistants API) som forventer `asst_`-prefix. Våre agenter er opprettet med `create_version()` og har ID-er som `AnomalyClassificationAgent:2`.

**Fil:** `challenge-4/agent-workflow/app/agents.py`

```python
# FØR (feil — Assistants API krever asst_-prefix):
agent_client = await project_client.agents.get_agent(agent_id="AnomalyClassificationAgent")
result = await agent_client.run(prompt)

# ETTER (riktig — OpenAI responses API med agent reference):
openai_client = project_client.get_openai_client()
conversation = openai_client.conversations.create()
response = openai_client.responses.create(
    conversation=conversation.id,
    input=prompt,
    extra_body={"agent": {"name": "AnomalyClassificationAgent", "type": "agent_reference"}},
)
result = response.output_text
```

### Problem 3: TLS-versjonsmismatch (Python ↔ .NET Kestrel)

**Symptom:**
```
[SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version
```

**Årsak:** Python httpx-klienten og .NET Kestrel ble uenige om TLS-versjon for interne HTTPS-kall.

**Workaround:** Brukte Aspire DCP proxy (HTTP) i stedet for direkte Kestrel-HTTPS. Port 5231 fra Aspire resolver dette automatisk.

---

## Nøkkelfiler

| Fil | Rolle |
|-----|-------|
| `apphost.cs` | Aspire AppHost — definerer Python, .NET og React som ressurser |
| `app/agents.py` | Python: wrapper for Foundry-agenter + A2A |
| `app/main.py` | FastAPI app med A2A-mounts |
| `dotnetworkflow/Program.cs` | .NET workflow entry point |
| `dotnetworkflow/AgentProviders.cs` | Agent service providers |
| `frontend/src/App.tsx` | React frontend |
| `frontend/vite.config.ts` | Vite proxy config |

---

## AppHost-arkitektur (apphost.cs)

```csharp
// Aspire AppHost bruker filbasert SDK-syntaks:
// #:sdk Aspire.AppHost.Sdk@13.1.0

// Python-app (uvicorn)
var app = builder.AddPythonUvicornApp("app", "../app", "main:app", port: 8000)
    .WithEnvironment("AZURE_AI_PROJECT_ENDPOINT", ...)
    .WithEnvironment("COSMOS_ENDPOINT", ...);

// .NET workflow
var dotnetworkflow = builder.AddProject<Projects.dotnetworkflow>("dotnetworkflow")
    .WithReference(app);

// React frontend
var frontend = builder.AddNpmApp("frontend", "../frontend")
    .WithEnvironment("VITE_API_URL", ReferenceExpression.Create($"{apiEndpoint}/"));
```

---

## Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `aspire: command not found` | Tool ikke i PATH | `export PATH="$PATH:$HOME/.dotnet/tools"` |
| `You must install .NET` | DOTNET_ROOT mangler | `export DOTNET_ROOT=/opt/homebrew/Cellar/dotnet/10.0.103/libexec` |
| Blank frontend | VITE_API_URL feil | Se Bugfix 1 over |
| `asst_` ID-feil | Feil agent-klient | Se Bugfix 2 over |
| Dashboard viser rødt for en tjeneste | Tjenesten krasjet | Sjekk logger i Dashboard → klikk på tjenesten |
| Frontend kan ikke nå API | CORS / port-feil | Sjekk at Vite proxy peker til riktig port |
| `npm install` feiler | Node.js mangler | `brew install node` |

---

## Lærdom

- **Aspire CLI** heter `aspire.cli` i NuGet — ikke `aspire`
- **DOTNET_ROOT** må settes eksplisitt for brew-installert .NET på macOS
- **`EndpointReference.ToString()`** returnerer typenavnet — bruk `ReferenceExpression.Create()` i stedet
- **Named agents** krever `openai_client.responses.create()` med `extra_body` — ikke `AgentsClient`
- **Lokalt > Codespaces** — alt kjørte raskere og mer stabilt lokalt på macOS
- **Aspire Dashboard** gir fullstendig oversikt over alle tjenester — logger, helse og traces i én visning
- **A2A muliggjør polyglot:** .NET kaller Python som kaller Foundry — uten tight coupling
