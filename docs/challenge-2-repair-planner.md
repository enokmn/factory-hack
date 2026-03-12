# Challenge 2: Repair Planner Agent (.NET) — Teknisk oppskrift

**Atea AI Agent Hackathon — 12. mars 2026 | Team 8**

---

## Mål

Bygge en **RepairPlannerAgent** i .NET som leser diagnostiserte feil, slår opp nødvendige kompetanser og reservedeler, finner tilgjengelige teknikere, og oppretter en komplett arbeidsordre i Cosmos DB.

## Forutsetninger

- Challenge 0 og 1 fullført
- .NET 10 installert (`brew install dotnet`)
- Miljøvariabler eksportert

```bash
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)
```

## Tidsbruk

Ca. 10–20 minutter (avhengig av om du bruker example-solution eller bygger fra scratch)

---

## To veier til målet

### Vei A: Bruk example-solution (raskest)

```bash
cp -r challenge-2/example-solution/RepairPlanner challenge-2/RepairPlanner
cd challenge-2/RepairPlanner
dotnet restore
dotnet run
```

### Vei B: Bygg fra scratch med GitHub Copilot

Åpne VS Code / GitHub Codespaces, og bruk `@agentplanning`:

1. Beskriv til Copilot hva agenten skal gjøre
2. La Copilot generere prosjektstruktur, modeller og services
3. Iterer med Copilot for å finjustere

> **Merk:** Vei B tar 20–30 minutter, men gir bedre læringsutbytte om AI-assistert utvikling.

---

## Prosjektstruktur

```
RepairPlanner/
├── RepairPlanner.csproj      # .NET 10, Azure.AI.Projects, Cosmos SDK
├── Program.cs                # Dependency injection, sample fault, kjører workflow
├── RepairPlannerAgent.cs     # Agent: prompt → parse → lagre arbeidsordre
├── Models/
│   ├── DiagnosedFault.cs     # Input fra Fault Diagnosis Agent
│   ├── Technician.cs         # Teknikere med kompetanseprofiler
│   ├── Part.cs               # Reservedeler med lagerstatus
│   ├── WorkOrder.cs          # Output: komplett arbeidsordre
│   ├── WorkOrderPartUsage.cs # Delelinje i arbeidsordre
│   └── RepairTask.cs         # Individuelle reparasjonssteg
└── Services/
    ├── CosmosDbService.cs    # Cosmos DB-spørringer + skriving
    ├── CosmosDbOptions.cs    # Konfigurasjon
    └── FaultMappingService.cs # Feil → kompetanse/deler-mapping
```

## Hva agenten gjør steg for steg

1. **Mottar diagnostisert feil** fra FaultDiagnosisAgent (JSON med maskin-ID, feiltype, rotårsak, alvorlighetsgrad)
2. **Slår opp nødvendige kompetanser** via `FaultMappingService` — statisk mapping av 10 feiltyper til påkrevde skills og reservedeler
3. **Søker etter tilgjengelige teknikere** i Cosmos DB basert på nødvendige kompetanser
4. **Henter reservedeler** fra `PartsInventory` i Cosmos DB
5. **Genererer reparasjonsplan** via LLM (GPT-4.1) med all kontekst
6. **Oppretter arbeidsordre** i Cosmos DB med tekniker, deler, oppgaver og tidslinje

## Kjøring

```bash
cd /tmp/factory-hack
export $(cat .env | xargs)
cd challenge-2/RepairPlanner
dotnet run
```

## Forventet resultat

```
✅ RepairPlannerAgent opprettet i Azure AI Foundry
📋 Arbeidsordre WO-20260312-001 opprettet:
   - Maskin: machine-001
   - Feil: curing_temperature_excessive
   - Tekniker: John Smith (tech-001) — Senior Tire Equipment Technician
   - Estimert varighet: 180 minutter
   - Deler: TCP-HTR-4KW (varmeelement), GEN-TS-K400 (termoelement)
   - 7 reparasjonsoppgaver med sikkerhetsinstruksjoner
```

### Verifiser i Cosmos DB

Du kan verifisere arbeidsordren direkte:

```bash
# Via APIM (hvis Maintenance API støtter work orders)
# Eller direkte i Azure Portal → Cosmos DB → FactoryOpsDB → WorkOrders
```

---

## Nøkkelkonsepter

### FaultMappingService — 10 feiltyper

Agenten bruker en statisk mapping som kobler feiltype til nødvendige kompetanser og deler:

| Feiltype | Eksempel-kompetanser | Eksempel-deler |
|----------|---------------------|----------------|
| `curing_temperature_excessive` | Electrical, Temperature Control | Heating element, Thermocouple |
| `mixing_temperature_excessive` | Mixing Systems, Temperature Control | Mixing blade, Temperature sensor |
| `tread_thickness_deviation` | Extrusion, Quality Control | Extrusion die, Thickness gauge |
| ... | ... | ... |

### Cosmos DB direkte (ikke MCP)

I motsetning til Challenge 1 Task 2 bruker RepairPlannerAgent **direkte Cosmos DB-tilkobling** — ikke MCP. Dette er et bevisst valg:

- Agenten trenger **lav latens** og **skrivetilgang** (oppretter arbeidsordre)
- MCP er best for lesetilgang via standardiserte grensesnitt
- Skriveoperasjoner er ofte applikasjonsspesifikke og passer bedre som direkte integrasjon

### Named agent vs. Assistants API

RepairPlannerAgent registreres som named agent i Foundry via `create_version()`. For å kalle den programmatisk bruker du:

```csharp
// .NET: Direkte via Foundry Agents SDK
var agent = await projectClient.GetAIAgent("RepairPlannerAgent");
var result = await agent.RunAsync(prompt);
```

---

## Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `dotnet restore` feiler | NuGet-feeds utilgjengelig | Sjekk internettilkobling, prøv `dotnet nuget locals all --clear` |
| Cosmos DB timeout | Feil endepunkt | Sjekk `COSMOS_ENDPOINT` og `COSMOS_KEY` |
| Agent returnerer ustrukturert tekst | LLM følger ikke instruksjoner | Agenten har fallback-logikk som fyller inn standardverdier |
| `System.Text.Json` parse-feil | LLM returnerer markdown-wrappet JSON | `RepairPlannerAgent.cs` stripper markdown-kodeblokker automatisk |
| `brew install dotnet` gir .NET 10 | Forventet versjon | Helt riktig — .NET 10 er LTS fra november 2025 |

---

## Lærdom

- **.NET og Python side om side:** Foundry Agent Framework er førsteklasses i begge språk — velg basert på teamets kompetanse
- **Agenter som skriver data:** RepairPlannerAgent er ikke bare en chatbot — den oppretter faktiske arbeidsordrer i databasen
- **GitHub Copilot `@agentplanning`:** En spesialtrent Copilot-agent som akselererer agent-utvikling
- **Statisk mapping + LLM:** Kombinasjonen av deterministisk logikk (FaultMappingService) og LLM-resonnering gir pålitelige resultater
- **Cosmos DB direkte vs. MCP:** Skriveoperasjoner passer bedre som direkte integrasjon — MCP er best for standardisert lesetilgang
