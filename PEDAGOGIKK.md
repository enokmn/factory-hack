# Hva Atea vil lære oss — Pedagogisk oppsummering

**Atea AI Agent Hackathon — 12. mars 2026**

---

## Overordnet mål

Hackathonen tar deg fra **null til fungerende multi-agent system** for prediktiv vedlikehold i en dekkfabrikk. Gjennom fem challenges bygger du gradvis opp et komplett system der fem AI-agenter samarbeider for å oppdage feil, diagnostisere årsaker, planlegge reparasjoner, planlegge vedlikehold og bestille deler — alt automatisk.

Atea ønsker å vise at AI-agenter ikke er fremtidsmusikk. Det er **praktisk verktøy du kan bygge i dag** med eksisterende Azure-tjenester og åpne standarder.

**Kjernepoenget som gjentas gjennom hele hackathonen:**
> *Agenter er en del av applikasjonen, ikke hele applikasjonen.*

Du bygger fortsatt tjenester, definerer grensesnitt og konfigurerer miljøer — agentene forsterker løsningens kapabiliteter. De erstatter ikke tradisjonell utvikling, men gjør den kraftigere.

---

## Teknologiene bak hackathonen

Før vi dykker inn i utfordringene, er det verdt å forstå de sentrale teknologiene som brukes. Flere av disse er helt nye og representerer hvor bransjen beveger seg.

### Model Context Protocol (MCP)

MCP er en åpen standard utviklet av Anthropic, lansert i november 2024, som standardiserer hvordan AI-modeller kobler seg til eksterne verktøy, datakilder og systemer. Tenk på det som **«USB-C for AI»** — en universell kontakt som lar enhver AI-agent snakke med enhver datakilde gjennom et felles grensesnitt.

Protokollen har fått bred adopsjon: OpenAI, Google, Microsoft, Amazon og alle store AI-leverandører støtter den. I desember 2025 ble MCP donert til Linux Foundation under den nye **Agentic AI Foundation (AAIF)**. Python- og TypeScript-SDKene har over 97 millioner nedlastinger per måned.

**I hackathonen** brukes MCP til å eksponere Cosmos DB-APIer og kunnskapsbaser som verktøy agentene kan kalle via standardiserte HTTP-endepunkter gjennom Azure API Management.

### Microsoft Foundry (tidl. Azure AI Foundry)

Azure AI Foundry ble rebrandert til **Microsoft Foundry** på Microsoft Ignite i november 2025, og posisjonert som den tredje hovedpilaren i Microsofts plattform — ved siden av Microsoft 365 og Fabric. Det er Microsofts samlede plattform for å bygge, orkestrere og distribuere AI-agenter og -applikasjoner.

Plattformen har gått fra enkeltagent-flyten til fullstendig multi-agent-orkestrering med visuell bygging i portalen, minnehåndtering på tvers av sesjoner, og støtte for A2A-protokollen. SDK-et (`azure-ai-projects` v2) samler agenter, inferens, evaluering og minne i én pakke.

**I hackathonen** er Microsoft Foundry plattformen der agentene hostes, modellene (GPT-4.1) er distribuert, og tracing overvåkes.

### Agent-to-Agent-protokollen (A2A)

A2A er en åpen kommunikasjonsprotokoll lansert av Google i april 2025 som lar AI-agenter fra ulike leverandører og rammeverk kommunisere med hverandre. Mens MCP handler om **agent-til-verktøy** (hvordan en agent bruker et verktøy), handler A2A om **agent-til-agent** (hvordan agenter samarbeider).

Protokollen bruker «Agent Cards» i JSON-format for å oppdage hva andre agenter kan gjøre, og definerer livssyklusen for oppgaver mellom agenter. A2A er nå donert til Linux Foundation og støttes av over 50 partnere, inkludert Atlassian, Salesforce, SAP og ServiceNow.

**I hackathonen** brukes A2A slik at .NET-workflowen kan kalle Python-agenter (MaintenanceScheduler og PartsOrdering) og omvendt, uten at de trenger å vite noe om hverandres implementasjon.

### Microsoft Agent Framework

Microsoft Agent Framework er et open-source rammeverk for å bygge, orkestrere og distribuere AI-agenter, tilgjengelig for både .NET og Python. Det er resultatet av en sammenslåing av **Semantic Kernel** og **AutoGen** — det kombinerer AutoGens enkle abstraksjoner for single- og multi-agent-mønstre med Semantic Kernels enterprise-funksjoner som tilstandshåndtering, typesikkerhet, filtre og telemetri. Rammeverket nådde Release Candidate-status i februar 2026.

**I hackathonen** er dette SDK-et som brukes til å bygge alle agenter — i Python for Challenge 1 og 3, og i .NET for Challenge 2.

### .NET Aspire

Aspire er Microsofts kode-først, polyglott verktøy for å bygge distribuerte applikasjoner. Det lar utviklere modellere, kjøre og distribuere hele systemer — inkludert infrastruktur, tjenester og konfigurasjon — fra én enkelt kildekode. Aspire 13 ble sluppet på .NET Conf 2025 sammen med .NET 10 LTS, og inkluderer AI-integrasjon via MCP.

**I hackathonen** orkestrerer Aspire hele multi-agent-workflowen: Python-app, .NET-workflow og React-frontend kjøres som én samlet applikasjon med felles dashboard for logger, helse og traces.

### Foundry IQ

Foundry IQ er et administrert kunnskapslag i Microsoft Foundry som kobler strukturerte og ustrukturerte data på tvers av Azure, SharePoint, OneLake og web. Det leverer automatisk indeksering, vektorisering og berikelse av dokumenter, og bruker en agentisk retrieval-motor som planlegger, søker og syntetiserer svar på tvers av kilder. Sikkerhetsetiketter fra Microsoft Purview følger med gjennom hele pipelinen.

**I hackathonen** indekserer Foundry IQ fabrikk-wikien (feilsøkingsguider for maskintyper) og gjør den tilgjengelig for FaultDiagnosisAgent via MCP, slik at agenten kan diagnostisere feil basert på bedriftens egen dokumentasjon — ikke LLM-ens generelle kunnskap.

---

## Læringsreisen — utfordring for utfordring

### Challenge 0: Grunnmuren
**Du lærer:** Hvordan sette opp Azure-infrastruktur for AI-agenter

Før du kan bygge en eneste agent, trenger du et solid fundament. Challenge 0 handler om å klargjøre hele Azure-miljøet: provisjonere ressurser, seede fabrikkdata og verifisere at alt er tilgjengelig.

| Komponent | Hva det er | Hvorfor du trenger det |
|-----------|-----------|----------------------|
| Azure AI Foundry | Prosjekt, modeller, endepunkter | Plattformen agentene lever på |
| Cosmos DB | 9 containere med fabrikkdata | Maskiner, telemetri, terskelverdier, tekniker, deler, arbeidsordrer |
| API Management | API-gateway | Sikker eksponering av data — blir MCP-servere i Challenge 1 |
| Azure AI Search + Blob Storage | Kunnskapsbase | Wiki-filer som indekseres for RAG i Challenge 1 |
| Application Insights | Overvåking | Tracing og observability brukt i Challenge 3 og 4 |

**Atea sitt poeng:** AI er bare så god som dataen den har tilgang til. Uten et ryddig datafundament — strukturert i Cosmos DB, eksponert via APIM, dokumentert i kunnskapsbaser — er agentene verdiløse. Infrastruktur først, AI etterpå.

---

### Challenge 1: Agenter og verktøy
**Du lærer:** Tre fundamentalt forskjellige måter å gi agenter tilgang til data

Dette er hackathonens viktigste konseptuelle challenge. Du bygger to agenter (AnomalyClassificationAgent og FaultDiagnosisAgent), men det sentrale er **hvordan** de får tilgang til data — og hvorfor metoden betyr alt for portabilitet og vedlikehold.

| Task | Integrasjonsmønster | Hva du lærer |
|------|---------------------|-------------|
| **Task 1:** Lokal agent | Python-funksjoner kaller Cosmos DB direkte | Enklest mulig — men agenten er bundet til maskinen den kjører på |
| **Task 2:** MCP-agent | APIM eksponerer API som MCP-server → agent kaller via HTTP | **Agenten blir portabel** — kan kjøre lokalt, i skyen eller i Foundry Portal |
| **Task 3:** Kunnskapsbase | Foundry IQ indekserer wiki-filer → agent søker via MCP | **RAG (Retrieval-Augmented Generation)** — agenten svarer basert på bedriftens dokumentasjon, ikke LLM-ens generelle kunnskap |

**Nøkkelkonsepter du tar med deg:**

- **MCP som universelt grensesnitt:** I stedet for å skrive integrasjonskode per agent og per datakilde, eksponerer du API-er som MCP-servere i APIM. Alle agenter bruker dem gjennom et standardisert grensesnitt — akkurat som USB-C lar deg koble alt til samme port.

- **Grounding er ikke valgfritt:** Agenten har eksplisitt instruks: «Du må aldri svare basert på egen kunnskap. Hvis du ikke finner svaret i verktøyene, svar med 'I don't know'.» I produksjon er dette kritisk — hallusinering i en vedlikeholdsanbefaling kan føre til feil reparasjon.

- **Foundry IQ gjør RAG enkelt:** Du laster opp Markdown-filer til Blob Storage, peker Foundry IQ mot dem, og agenten kan automatisk søke i dem via MCP. Ingen manuell indeksering, chunking eller embedding-kode nødvendig.

**Atea sitt poeng:** MCP er den nye standarden for verktøyintegrasjon, og den er allerede støttet av alle store AI-leverandører. Grounding og RAG er ikke nisje-teknikker — de er grunnleggende krav for enhver produksjonsagent.

---

### Challenge 2: Polyglot agenter og AI-assistert utvikling
**Du lærer:** At agenter kan bygges i flere språk, og at AI akselererer selve utviklingen

Challenge 2 skifter fra Python til .NET og introduserer to viktige konsepter: språkvalg som bevisst arkitekturbeslutning, og bruk av GitHub Copilot som utviklingsassistent.

| Komponent | Hva du lærer |
|-----------|-------------|
| .NET Foundry Agents SDK | Agenter er ikke begrenset til Python — .NET gir ytelse og enterprise-integrasjon |
| GitHub Copilot `@agentplanning` | En spesialisert Copilot-agent som hjelper deg planlegge og bygge agenter — meta-nivå AI |
| Cosmos DB direkte integrasjon | Noen agenter trenger lav-latens datatilgang uten å gå via APIM |
| Work order-oppretting | Agenter som **skriver** data tilbake til systemet, ikke bare leser og svarer |

**Nøkkelkonsepter du tar med deg:**

- **Språkvalg er en feature, ikke en begrensning:** Python er fantastisk for rask prototyping og datanære oppgaver. .NET gir bedre ytelse, sterkere typing og smidigere integrasjon med eksisterende enterprise-systemer. Microsoft Agent Framework er førsteklasses i begge.

- **Agenter gjør ting i den virkelige verden:** RepairPlannerAgent nøyer seg ikke med å foreslå en reparasjon — den oppretter en faktisk arbeidsordre i Cosmos DB, tildeler tekniker basert på kompetanse og tilgjengelighet, og legger til deleliste med lagerstatus. Dette er ikke en chatbot som svarer på spørsmål.

- **Copilot som medarkitekt:** `@agentplanning` er en spesialtrent Copilot-agent med instruksjoner og verktøy tilpasset agent-utvikling. Den kan planlegge arkitektur, generere kode og hjelpe deg iterere. AI brukes til å bygge AI.

**Atea sitt poeng:** Enterprise-agenter bygges i det språket teamet kan best. Og med GitHub Copilot som assistent kan én utvikler gjøre arbeidet som før krevde et helt team. Fremtidens utvikling er AI-assistert — hackathonen er et konkret eksempel.

---

### Challenge 3: Hukommelse og observability
**Du lærer:** Agenter som husker kontekst over tid og kan overvåkes i produksjon

Challenge 3 tar agentene fra demo-kvalitet til noe som ligner produksjon. To nye konsepter er sentrale: persistent hukommelse (agenten husker hva som skjedde sist) og observability (du kan se nøyaktig hva agenten gjorde og hvorfor).

| Komponent | Hva du lærer |
|-----------|-------------|
| Agent memory (persistent threads) | Agenten beholder kontekst mellom samtaler — husker tidligere vedlikehold per maskin |
| Risiko-scoring med historiske data | Beslutninger basert på MTBF, feilhistorikk og maskintype — ikke bare LLM-intuisjon |
| Application Insights tracing | Full tidslinje for hva agenten gjorde: API-kall, verktøybruk, beslutninger |
| Batch-kjøring (10 work orders) | Verifiserer at agenter fungerer konsistent i skala, ikke bare på ett enkelttilfelle |

**Nøkkelkonsepter du tar med deg:**

- **Persistent memory forandrer alt:** Uten hukommelse er hver agent-samtale en ny start. Med persistent threads (lagret i Cosmos DB) husker MaintenanceSchedulerAgent at maskin-005 hadde temperatursensor-feil forrige måned, og justerer risikovurderingen deretter. I vedlikehold er historikk avgjørende.

- **Observability er et produksjonskrav:** Når fem agenter samarbeider og en av dem tar en merkelig beslutning, må du kunne spore tilbake. Application Insights + Foundry tracing gir deg en komplett tidslinje: hvilke verktøy ble kalt, hvilke data ble hentet, og hvordan agenten resonnerte seg frem til svaret.

- **Data-drevne beslutninger:** MaintenanceSchedulerAgent beregner risk score (0-100) basert på maskinens MTBF (Mean Time Between Failures), feilhistorikk, gjeldende feiltype og produksjonspåvirkning. Den velger vedlikeholdsvindu basert på faktisk produksjonsplan — ikke bare «snarest mulig».

**Atea sitt poeng:** Enhver agent kan svare på ett spørsmål. Utfordringen er å bygge agenter som fungerer over tid, i skala, og som du kan feilsøke når noe går galt. Hukommelse og observability er forskjellen mellom en demo og et produksjonssystem.

---

### Challenge 4: Orkestrering — alt sammen
**Du lærer:** Å kjøre alle fem agenter som én samlet applikasjon med felles observability

Challenge 4 er kulminasjonen. Her kobles alt sammen: Python-agenter og .NET-agenter kommuniserer via A2A, Aspire orkestrerer alle prosessene, og en React-frontend lar en sluttbruker trigge hele pipelinen med ett klikk.

| Komponent | Hva du lærer |
|-----------|-------------|
| .NET Aspire | Orkestrerer Python, .NET og React som én samlet applikasjon — «docker-compose for AI, men smartere» |
| A2A (Agent-to-Agent) | Agenter kaller hverandre på tvers av språk og prosesser via en åpen standard |
| Polyglot workflow | Python + .NET + React i samme pipeline, med felles konfigurasjon |
| Aspire Dashboard | Én samlet visning for logger, helsestatus og traces på tvers av alle tjenester |
| Web-frontend | Sluttbrukergrensesnitt som visualiserer hele agent-pipelinen steg for steg |

**Nøkkelkonsepter du tar med deg:**

- **A2A-protokollen muliggjør polyglot samarbeid:** .NET-workflowen kaller Python-agenter via A2A uten å vite noe om Python. Python-agentene kaller Foundry-agenter uten å vite noe om .NET. Hver agent er en selvstendig tjeneste med et standardisert grensesnitt.

- **Aspire er limet:** Med én kommando (`aspire run`) starter du Python-appen, .NET-workflowen og React-frontenden. Aspire konfigurerer nettverksforbindelser, eksponerer endepunkter og gir deg et dashboard med logger og traces fra alle tjenester samlet. Det er infrastruktur-som-kode for distribuerte applikasjoner.

- **Sekvensiell agent-pipeline:** Hele workflowen er en kjede der output fra én agent blir input til neste. AnomalyClassification oppdager at noe er galt → FaultDiagnosis finner årsaken → RepairPlanner lager arbeidsordre → MaintenanceScheduler planlegger tidspunkt → PartsOrdering sikrer at delene er tilgjengelige. Hver agent er spesialist på sitt domene.

- **Hybrid hosting:** Anomaly- og FaultDiagnosis-agentene kjører i Azure AI Foundry (skyen), mens RepairPlanner, Scheduler og PartsOrdering kjører lokalt. I produksjon ville alle kjørt i skyen (f.eks. Azure Container Apps), men dette viser at hosting-valg er uavhengig av agent-implementasjon.

**Atea sitt poeng:** Fremtidens applikasjoner er en blanding av tradisjonelle tjenester og AI-agenter. Du trenger ikke velge mellom «gammel» og «ny» arkitektur — du kombinerer dem. Aspire + A2A er mønsteret for å bygge, kjøre og overvåke dette.

---

## Den røde tråden

```
Challenge 0          Challenge 1          Challenge 2          Challenge 3          Challenge 4
Infrastruktur   →   Agenter + MCP    →   Polyglot + AI    →   Hukommelse +     →   Orkestrering
og data             og RAG               assistert dev        observability        og E2E-workflow

"Grunnmuren"        "Agenten forstår"   "Agenten handler"   "Agenten husker     "Agentene
                                                              og overvåkes"       samarbeider"
```

### Progresjon av kompleksitet

| Dimensjon | Ch. 0 | Ch. 1 | Ch. 2 | Ch. 3 | Ch. 4 |
|-----------|-------|-------|-------|-------|-------|
| **Agenter** | 0 | 2 | 1 | 2 | Alle 5 |
| **Språk** | Bash/Python | Python | .NET (C#) | Python | Python + .NET + React |
| **Datatilgang** | Seeding | Les via MCP | Les + skriv (Cosmos DB) | Les + skriv + hukommelse | Alt kombinert |
| **Integrasjonsmønster** | CLI/scripts | MCP + Foundry IQ | Direkte DB + Copilot | Cosmos DB + threads | MCP + A2A + alt |
| **Observability** | Ingen | Ingen | Ingen | Application Insights | Aspire Dashboard + App Insights |
| **Hosting** | Lokal | Azure Agent Service | Lokal | Azure Agent Service | Hybrid (lokal + sky) |

---

## De seks tingene Atea egentlig vil at du tar med hjem

### 1. AI-agenter er klare for produksjon — nå
Ikke om fem år. Du kan bygge og distribuere multi-agent systemer i dag med Microsoft Foundry, MCP og Microsoft Agent Framework. Hackathonen beviser at dette ikke krever et PhD-team — en utvikler med riktige verktøy kan bygge et komplett system på timer.

### 2. MCP er den nye universelle standarden
Model Context Protocol er i ferd med å bli for AI-verktøy det HTTP ble for web. Alle store leverandører støtter det. I stedet for å skrive integrasjonskode per agent og per datakilde, eksponerer du API-er som MCP-servere. Enhver agent kan bruke dem — uansett leverandør eller språk.

### 3. Polyglot er en styrke, ikke et problem
Bruk Python der det passer (rask prototyping, data science). Bruk .NET der det passer (ytelse, enterprise-integrasjon). Bruk React for brukergrensesnitt. A2A-protokollen lar dem samarbeide uten tight coupling. Språkvalg er en arkitekturbeslutning, ikke en begrensning.

### 4. Observability er ikke valgfritt
Når fem agenter samarbeider og noe går galt, må du kunne finne ut hva som skjedde. Application Insights + Aspire Dashboard gir full innsikt: hvilke verktøy ble kalt, hvilke data ble hentet, hvordan agenten resonnerte, og hvor det gikk galt. Uten dette er multi-agent-systemer en svart boks.

### 5. Agenter forsterker applikasjoner — de erstatter dem ikke
En vedlikeholdsapplikasjon med AI-agenter er bedre enn enten en ren app eller en ren chatbot. Du bygger fortsatt tjenester, databaser og brukergrensesnitt — men agentene gir applikasjonen evnen til å resonnere, planlegge og ta beslutninger basert på data.

### 6. Fremtiden er agentisk — og den er her
Ifølge tech-talken vil mennesker innen 2028 stå for ca. 40 % av IT-arbeidet — AI-agenter tar over resten. Innen 2027 vil nesten ingen skrive kode 100 % manuelt. Hackathonen er ikke et tankeeksperiment — det er en praktisk demonstrasjon av hvordan dette ser ut i virkeligheten.

---

## Komplett teknologistabel

| Teknologi | Hva det er | Rolle i hackathonen |
|-----------|-----------|-------------------|
| **Microsoft Foundry** | Microsofts plattform for AI-agenter (tidl. Azure AI Foundry) | Hosting av agenter, modeller og tracing |
| **GPT-4.1** | OpenAIs store språkmodell, distribuert via Azure | LLM-motoren bak alle fem agenter |
| **MCP** | Model Context Protocol — åpen standard fra Anthropic/Linux Foundation | Agent-til-verktøy-kommunikasjon via APIM |
| **A2A** | Agent-to-Agent-protokoll — åpen standard fra Google/Linux Foundation | Agent-til-agent-kommunikasjon på tvers av språk |
| **Microsoft Agent Framework** | Open-source SDK for agenter (Python + .NET) | Rammeverket agentene bygges med |
| **Foundry IQ** | Administrert kunnskapslag i Microsoft Foundry | RAG: indeksering og søk i fabrikk-wiki |
| **Azure Cosmos DB** | NoSQL-database | All operasjonell data: maskiner, telemetri, ordrer |
| **Azure API Management** | API-gateway | Eksponerer Cosmos DB som MCP-servere |
| **Azure AI Search** | Søketjeneste | Indeksering av kunnskapsbase for Foundry IQ |
| **Application Insights** | Overvåking og tracing | End-to-end traces av agentoperasjoner |
| **.NET Aspire 13** | Polyglott orkestreringsverktøy for distribuerte apper | Kjører Python + .NET + React som én app |
| **GitHub Copilot** | AI-kodingsassistent | Assistert utvikling + `@agentplanning`-agent |
| **React / Vite** | Frontend-rammeverk | Web-UI for å visualisere agent-pipelinen |

---

## Sammenheng: MCP + A2A = komplett agentisk arkitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Sluttbruker (Frontend)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Workflow-orkestrator (Aspire)                    │
│                                                              │
│   Agent 1 ──A2A──▶ Agent 2 ──A2A──▶ Agent 3 ──A2A──▶ ...  │
│                                                              │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
   ┌───────┐         ┌───────┐         ┌───────┐
   │  MCP  │         │  MCP  │         │  MCP  │
   │Server │         │Server │         │Server │
   └───┬───┘         └───┬───┘         └───┬───┘
       │                  │                  │
       ▼                  ▼                  ▼
   Cosmos DB          AI Search       Blob Storage
   (via APIM)        (Foundry IQ)     (Wiki-filer)
```

**MCP** = hvordan agenter snakker med **verktøy** (databaser, APIer, kunnskapsbaser)
**A2A** = hvordan agenter snakker med **hverandre** (på tvers av språk og hosting)

Sammen utgjør de en komplett, standardbasert arkitektur for agentiske systemer.
