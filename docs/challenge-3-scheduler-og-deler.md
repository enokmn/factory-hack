# Challenge 3: Maintenance Scheduler & Parts Ordering — Teknisk oppskrift

**Atea AI Agent Hackathon — 12. mars 2026 | Team 8**

---

## Mål

Bygge to Python-agenter med **persistent hukommelse** og **observability**:
1. **MaintenanceSchedulerAgent** — analyserer arbeidsordrer, beregner risikoscore, og planlegger optimalt vedlikeholdsvindu
2. **PartsOrderingAgent** — sjekker lagerbeholdning, evaluerer leverandører, og bestiller manglende deler

Begge agenter lagrer interaksjonshistorikk i Cosmos DB og sender traces til Application Insights.

## Forutsetninger

- Challenge 0–2 fullført (minst én arbeidsordre i Cosmos DB)
- Python venv aktivert med avhengigheter
- Miljøvariabler eksportert

```bash
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)
```

## Tidsbruk

Ca. 15 minutter (inkl. batch-kjøring)

---

## Task 1: Maintenance Scheduler Agent

### Kjør agenten

```bash
cd /tmp/factory-hack/challenge-3
python agents/maintenance_scheduler_agent.py wo-2024-468
```

Argumentet (`wo-2024-468`) er ID-en til en arbeidsordre fra seed-data.

### Hva skjer under panseret

1. **Henter arbeidsordre** fra Cosmos DB (`WorkOrders`-containeren)
2. **Henter vedlikeholdshistorikk** for maskinen (`MaintenanceHistory`)
3. **Henter tilgjengelige vedlikeholdsvinduer** (`MaintenanceWindows`)
4. **Bygger analysekontekst** med all data
5. **Sender til LLM** (GPT-4.1) for risikoscoring og planlegging
6. **Lagrer vedlikeholdsplan** i Cosmos DB (`MaintenanceSchedules`)
7. **Oppdaterer arbeidsordre-status** til «Scheduled»
8. **Lagrer chat-historikk** for persistent memory

### Forventet resultat

```
✅ MaintenanceSchedulerAgent registrert i Azure AI Foundry
📊 Vedlikeholdsplan for wo-2024-468:
   - Maskin: machine-005
   - Risk Score: 45/100
   - Failure Probability: 24%
   - Anbefalt handling: SCHEDULED
   - Valgt vindu: 22:00–06:00 (nattskift, lav produksjonspåvirkning)
   - Status oppdatert: Scheduled
```

### Risikoscoring

Agenten beregner risk score basert på:
- **MTBF** (Mean Time Between Failures) for maskintypen
- **Feilhistorikk** — antall og type tidligere feil
- **Gjeldende feiltype** — alvorlighetsgrad og konsekvens
- **Produksjonspåvirkning** — hvor kritisk maskinen er for linjen

---

## Task 2: Parts Ordering Agent

### Kjør agenten

```bash
python agents/parts_ordering_agent.py wo-2024-468
```

### Hva skjer under panseret

1. **Henter arbeidsordre** med nødvendige deler
2. **Sjekker lagerbeholdning** i `PartsInventory`
3. **Evaluerer leverandører** basert på pris, leveringstid og pålitelighet
4. **Genererer bestilling** hvis deler mangler, eller markerer «Ready» hvis alt er på lager
5. **Oppdaterer arbeidsordre-status** til «PartsOrdered» eller «Ready»
6. **Lagrer bestilling** i Cosmos DB (`PartsOrders`)

### Forventet resultat

**Scenario A — Alt på lager:**
```
✅ wo-2024-468: Alle deler på lager → status "Ready"
```

**Scenario B — Deler mangler:**
```
✅ wo-2024-456: 2 deler bestilt
   - PO-2f39a813: $575 totalt
   - Leverandør: TirePartsDirect (pålitelighet: 98%, leveringstid: 2 dager)
   - Status: "PartsOrdered"
```

---

## Task 3: Tracing og observability

### Aktiver tracing

Observability er innebygd via `observability.py` som konfigurerer OpenTelemetry med Azure Monitor:

```python
# observability.py bruker:
# - APPLICATIONINSIGHTS_CONNECTION_STRING fra .env
# - Azure Monitor OpenTelemetry exporters for traces, metrics og logs
# - Sensitive data capture for prompts og completions
```

Tracing aktiveres automatisk når `APPLICATIONINSIGHTS_CONNECTION_STRING` er satt i miljøet.

### Kjør batch

```bash
python run-batch.py
```

Batch-scriptet kjører begge agenter for alle 5 seed-arbeidsordrer:

### Forventet resultat

```
🔄 Running maintenance scheduler batch...
  ✅ wo-2024-468: Scheduled (risk: 45)
  ✅ wo-2024-456: Scheduled (risk: 72)
  ✅ wo-2024-789: Scheduled (risk: 33)
  ✅ wo-2024-321: Scheduled (risk: 58)
  ✅ wo-2024-654: Scheduled (risk: 61)

🔄 Running parts ordering batch...
  ✅ wo-2024-468: Ready
  ✅ wo-2024-456: PartsOrdered ($575)
  ✅ wo-2024-789: Ready
  ✅ wo-2024-321: PartsOrdered ($890)
  ✅ wo-2024-654: Ready

📊 Batch complete: 10/10 successful | 118.6 seconds
```

### Se traces i Azure AI Foundry

1. Gå til https://ai.azure.com
2. Velg prosjekt → **Agents** → velg agent
3. Klikk **Monitor** / **Tracing**
4. Du ser en komplett tidslinje: verktøykall, LLM-interaksjoner, og agentens resonnering

---

## Persistent Memory (agent-hukommelse)

### Hvordan det fungerer

Begge agenter lagrer chat-historikk i Cosmos DB (`ChatHistory`-containeren) med:
- **Maskin-ID** som partisjonsnøkkel
- **Tidsstempel** for hver interaksjon
- **Input og output** fra agenten

Ved neste kjøring for samme maskin henter agenten historikken og inkluderer den i konteksten:

```python
# Forenklet eksempel fra maintenance_scheduler_agent.py:
chat_history = cosmos_service.get_chat_history(machine_id)
context = f"Previous interactions:\n{chat_history}\n\nCurrent work order:\n{work_order}"
```

### Hvorfor det betyr noe

Uten hukommelse er hver agent-samtale isolert. Med persistent memory:
- Agenten vet at maskin-005 hadde temperatursensor-feil forrige måned
- Risk score justeres basert på mønster i historiske data
- Leverandørvalg påvirkes av tidligere erfaringer (f.eks. sen levering)

---

## Prosjektstruktur

```
challenge-3/
├── agents/
│   ├── maintenance_scheduler_agent.py  # 470 linjer — scheduler med risikoscoring
│   ├── parts_ordering_agent.py         # 424 linjer — bestilling med leverandørvurdering
│   ├── cosmos_db_service.py            # 592 linjer — all Cosmos DB-interaksjon
│   └── observability.py                # 43 linjer — OpenTelemetry-konfigurasjon
├── run-batch.py                        # 156 linjer — batch-kjøring av begge agenter
└── README.md
```

---

## Feilsøking

| Problem | Årsak | Løsning |
|---------|-------|---------|
| `No work orders found` | Feil work order ID | Sjekk med `wo-2024-468` (fra seed-data) |
| `APPLICATIONINSIGHTS_CONNECTION_STRING not set` | Manglende miljøvariabel | `export $(cat .env | xargs)` |
| Traces vises ikke i Foundry | Latens i Application Insights | Vent 2–5 minutter etter kjøring |
| `Mock suppliers generated` i loggen | Seed-data mangler leverandører | Helt OK — `cosmos_db_service.py` genererer mock-leverandører som fallback |
| `Mock maintenance windows generated` | Seed-data mangler vinduer | Helt OK — fallback genererer realistiske vinduer |
| Batch tar lang tid (>3 min) | LLM-latens | Normalt — 10 LLM-kall tar tid. Sjekk at du ikke ratelimites |

---

## Lærdom

- **Persistent memory** er forskjellen mellom en demo og et produksjonssystem
- **Observability** (Application Insights + OpenTelemetry) er et krav, ikke en bonus
- **Mock-data som fallback** gjør agentene robuste mot manglende data i databasen
- **Batch-kjøring** verifiserer at agenter fungerer konsistent — ikke bare på ett tilfelle
- **Risk scoring** kombinerer deterministisk logikk (MTBF, historikk) med LLM-resonnering — beste fra begge verdener
