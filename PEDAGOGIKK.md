# Hva Atea vil lære oss — Pedagogisk oppsummering

**Atea AI Agent Hackathon — 2026-03-12**

---

## Overordnet mål

Hackathonen tar deg fra **null til fungerende multi-agent system** for prediktiv vedlikehold i en dekkfabrikk. Atea ønsker å vise at AI-agenter ikke er science fiction — det er **praktisk verktøy du kan bygge i dag** med eksisterende Azure-tjenester.

Kjernepoenget: **Agenter er en del av applikasjonen, ikke hele applikasjonen.** Du bygger fortsatt tjenester, definerer grensesnitt og konfigurerer miljøer — agenter forsterker løsningens kapabiliteter.

---

## Læringsreisen — challenge for challenge

### Challenge 0: Grunnmur
**Du lærer:** Hvordan sette opp Azure-infrastruktur for AI-agenter

| Hva | Hvorfor |
|-----|---------|
| Azure AI Foundry (prosjekt, modeller, endepunkter) | Plattformen agentene lever på |
| Cosmos DB (9 containere med fabrikkdata) | Operasjonell data agentene trenger |
| API Management (APIM) | Sikkert eksponere data som API-er |
| Azure AI Search + Blob Storage | Kunnskapsbase for RAG |
| Application Insights | Observability fra dag 1 |

**Atea sitt poeng:** Før du bygger agenter, trenger du et solid datafundament. AI er bare så god som dataen den har tilgang til.

---

### Challenge 1: Agenter og verktøy
**Du lærer:** Tre måter å gi agenter tilgang til data

| Task | Mønster | Hva du lærer |
|------|---------|-------------|
| Task 1: Lokal agent | Python-funksjoner kaller Cosmos DB direkte | Enklest — men agenten kan bare kjøre lokalt |
| Task 2: MCP-agent | APIM eksponerer API som MCP-server → agent kaller via HTTP | **Agenten blir portabel** — kan kjøre hvor som helst |
| Task 3: Knowledge base | Foundry IQ indekserer wiki-filer → agent søker via MCP | **RAG** — agenten svarer basert på bedriftens dokumentasjon, ikke egen "fantasi" |

**Nøkkelkonsepter:**
- **MCP (Model Context Protocol):** Standard for å koble agenter til verktøy. I stedet for å skrive kode per integrasjon, eksponerer du API-er som MCP-servere. Agenten kaller dem via et standardisert grensesnitt.
- **Grounding:** Agenten MÅ svare basert på data den finner — ikke hallusinere. Hvis den ikke finner svaret, skal den si "I don't know".
- **Foundry IQ:** Managed RAG — du laster opp dokumenter, Azure indekserer dem, agenten søker automatisk.

**Atea sitt poeng:** MCP er fremtiden for agent-integrasjoner. Én standard, mange verktøy. Og grounding er ikke valgfritt — det er kritisk for produksjon.

---

### Challenge 2: Polyglot agenter + Copilot-drevet utvikling
**Du lærer:** Bygge agenter i .NET med GitHub Copilot som assistent

| Hva | Hvorfor |
|-----|---------|
| .NET Foundry Agents SDK | Viser at agenter ikke er Python-only |
| GitHub Copilot `@agentplanning` | AI-assistert arkitektur og koding |
| Cosmos DB direkte integrasjon | Noen agenter trenger lav-latens datatilgang |
| Work order-oppretting | Agenter som **skriver** data, ikke bare leser |

**Nøkkelkonsepter:**
- **Språkvalg er en feature:** Bruk Python for rask prototyping, .NET for ytelse og enterprise-integrasjon. Begge er førsteklasses i Microsoft Agent Framework.
- **Agenter gjør ting:** RepairPlannerAgent oppretter faktiske work orders i Cosmos DB med tekniker-tilordning, deleliste og reparasjonstrinn. Dette er ikke bare chatbot-svar.
- **Copilot som arkitekt:** `@agentplanning` er en spesialisert Copilot-agent som hjelper deg planlegge og bygge — meta-nivå AI.

**Atea sitt poeng:** AI handler ikke bare om Python og notebooks. Enterprise-agenter bygges i det språket teamet kan best. Og Copilot akselererer utviklingen dramatisk.

---

### Challenge 3: Hukommelse og observability
**Du lærer:** Agenter som husker og kan overvåkes

| Hva | Hvorfor |
|-----|---------|
| Agent memory (persistent threads) | Agenten husker tidligere samtaler per maskin |
| Risk scoring med historiske data | Data-drevne beslutninger, ikke bare LLM-gjetning |
| Application Insights tracing | Se nøyaktig hva agenten gjorde og hvorfor |
| Batch-kjøring (10 work orders) | Tester at agenter fungerer i skala |

**Nøkkelkonsepter:**
- **Persistent memory:** Agenten har en "tråd" (thread) per maskin/work order. Neste gang du spør om samme maskin, husker den hva som skjedde sist. Kritisk for vedlikeholdsscenarier.
- **Observability er ikke valgfritt:** Når du har 5 agenter som samarbeider, MÅ du kunne se hva hver enkelt gjør. Application Insights + Foundry tracing gir deg full tidslinje.
- **Data-drevne agenter:** MaintenanceSchedulerAgent beregner risk score basert på MTBF, feilhistorikk og maskintype — ikke bare LLM-intuisjon.

**Atea sitt poeng:** Produksjonsagenter trenger hukommelse og overvåking. Uten dette er det bare en demo.

---

### Challenge 4: Orkestrering — alt sammen
**Du lærer:** Kjøre alle 5 agenter som én samlet applikasjon

| Hva | Hvorfor |
|-----|---------|
| .NET Aspire | Orkestrerer multi-service apper lokalt og i sky |
| A2A (Agent-to-Agent) | Agenter kaller hverandre på tvers av språk |
| Polyglot workflow | Python + .NET + React i samme pipeline |
| Aspire Dashboard | Én plass for logger, helse og traces |
| Web-frontend | Sluttbrukergrensesnitt for workflow |

**Nøkkelkonsepter:**
- **A2A-protokollen:** Standardisert måte for agenter å kalle hverandre. Workflowen bryr seg ikke om agenten er Python eller C# — den kaller via A2A.
- **Aspire som lim:** Starter alle prosesser, konfigurerer nettverksforbindelser, gir deg dashboard. Tenk "docker-compose for AI-agenter, men smartere".
- **Sekvensiell pipeline:** Output fra agent 1 → input til agent 2 → ... → agent 5. Hver agent er spesialist på sitt domene.

**Atea sitt poeng:** Fremtidens applikasjoner er en blanding av tradisjonelle tjenester og AI-agenter. Aspire + A2A er mønsteret for å bygge og drifte dette.

---

## Den røde tråden

```
Challenge 0          Challenge 1          Challenge 2          Challenge 3          Challenge 4
Infrastruktur   →   Agenter + MCP    →   Polyglot + AI    →   Memory +         →   Orkestrering
& data              & RAG                 assistert dev        Observability        & E2E workflow

"Grunnmuren"        "Agenten forstår"    "Agenten handler"   "Agenten husker     "Agentene
                                                              og kan overvåkes"    samarbeider"
```

### Progresjon av kompleksitet

| Dimensjon | Challenge 0 | Challenge 1 | Challenge 2 | Challenge 3 | Challenge 4 |
|-----------|-------------|-------------|-------------|-------------|-------------|
| **Agenter** | 0 | 2 | 1 | 2 | 5 (alle) |
| **Språk** | Bash | Python | .NET | Python | Python + .NET |
| **Data** | Seed | Les (MCP) | Les + skriv | Les + skriv + hukommelse | Alt |
| **Verktøy** | CLI | MCP, Foundry IQ | Cosmos DB, Copilot | Cosmos DB, threads | MCP + A2A + alt |
| **Observability** | Ingen | Ingen | Ingen | App Insights | Aspire Dashboard |
| **Hosting** | Lokal | Agent Service | Lokal | Agent Service | Hybrid (lokal + sky) |

---

## Hva Atea egentlig vil si oss

### 1. AI-agenter er her NÅ
Ikke om 5 år. Du kan bygge multi-agent systemer i dag med Azure AI Foundry, MCP og Microsoft Agent Framework. Hackathonen beviser det.

### 2. MCP er den nye standarden
Model Context Protocol er hvordan agenter snakker med verktøy. I stedet for å skrive integrasjonskode per agent, eksponerer du API-er som MCP-servere. Alle agenter kan bruke dem.

### 3. Polyglot er en styrke
Bruk Python der det passer, .NET der det passer, React for frontend. A2A-protokollen lar dem samarbeide uten tight coupling.

### 4. Observability er kritisk
Uten tracing og logging er multi-agent systemer en svart boks. Application Insights + Aspire Dashboard gir innsikt du trenger for produksjon.

### 5. Agenter + applikasjoner = fremtiden
Agenter erstatter ikke tradisjonell utvikling. De forsterker den. En vedlikeholdsapplikasjon med AI-agenter er bedre enn enten en ren app eller en ren chatbot.

### 6. Innen 2028 gjør AI 60% av IT-arbeidet
(Fra tech-talken) Mennesker vil fokusere på kreativt arbeid, arkitektur og beslutninger. AI håndterer resten. Hackathonen er et konkret eksempel på hvordan dette ser ut i praksis.

---

## Teknologistabel — komplett oversikt

| Teknologi | Rolle i hackathonen |
|-----------|-------------------|
| **Azure AI Foundry** | Plattform for agent-hosting og modell-deployments |
| **GPT-4.1** | LLM-motor bak alle agenter |
| **MCP** | Standardisert agent-til-verktøy-kommunikasjon |
| **Foundry IQ** | Managed RAG / kunnskapsbase |
| **Azure Cosmos DB** | Operasjonell datalagring (maskiner, telemetri, work orders) |
| **Azure API Management** | API gateway + MCP-server-eksponering |
| **Azure AI Search** | Indeksering for kunnskapsbase (Foundry IQ) |
| **Application Insights** | Tracing og observability |
| **Microsoft Agent Framework** | Python + .NET SDK for å bygge agenter |
| **A2A-protokollen** | Agent-til-agent-kommunikasjon på tvers av språk |
| **.NET Aspire** | Multi-service orkestrering og dashboard |
| **GitHub Copilot** | AI-assistert utvikling (+ `@agentplanning`) |
| **React / Vite** | Frontend for workflow-visualisering |
