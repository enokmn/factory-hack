# Challenge 0: Environment Setup — Teknisk oppskrift

**Atea AI Agent Hackathon — 12. mars 2026 | Team 8**

---

## Mål

Klargjøre hele Azure-miljøet: provisjonere ressurser, installere verktøy, seede fabrikkdata, og verifisere at alt er tilgjengelig for de påfølgende utfordringene.

## Forutsetninger

- macOS (Apple Silicon) eller Linux
- GitHub-konto
- Azure-tilgang (hackathon-bruker)

## Tidsbruk

Ca. 15 minutter (ekskl. feilsøking)

---

## Steg 1: Fork og klon repo

```bash
# Fork via GitHub: https://github.com/magnuseliass1/factory-hack → Fork
# Vår fork: https://github.com/<ditt-brukernavn>/factory-hack

cd /tmp
git clone https://github.com/<ditt-brukernavn>/factory-hack.git
cd /tmp/factory-hack
```

---

## Steg 2: Installer Azure CLI

```bash
brew install azure-cli
```

### Problem: `.azure`-mappen eid av root

Ved første kjøring av `az login` kan `.azure/`-mappen bli opprettet som root, noe som gir «Permission denied» ved senere bruk.

**Symptom:**
```
ERROR: AADSTS error - Permission denied: /Users/<bruker>/.azure/msal_token_cache.json
```

**Løsning:**
```bash
sudo chown -R $(whoami):staff ~/.azure/
```

---

## Steg 3: Logg inn på Azure

```bash
az login --use-device-code
```

Terminalen viser en kode og en URL. Åpne https://login.microsoft.com/device i nettleseren, skriv inn koden, og logg inn med hackathon-brukeren.

**Bruker:** `<din-bruker>@AteaCloudDemosNorway.onmicrosoft.com`
**Subscription:** `factory_hack_subscription`

### Verifiser innlogging

```bash
az account show --query "{name:name, user:user.name}" -o json
```

Forventet output:
```json
{
  "name": "factory_hack_subscription",
  "user": "<din-bruker>@AteaCloudDemosNorway.onmicrosoft.com"
}
```

---

## Steg 4: Python virtual environment

macOS har fra Python 3.12 innført PEP 668 som blokkerer `pip install` utenfor virtual environments. Du **må** bruke venv.

```bash
cd /tmp/factory-hack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Problem: `pip install` feiler med «externally-managed-environment»

**Symptom:**
```
error: externally-managed-environment
× This environment is externally managed
```

**Årsak:** macOS PEP 668 — systemet nekter pip-installasjoner utenfor venv.

**Løsning:** Alltid bruk venv som vist over. Aldri bruk `pip install --break-system-packages`.

---

## Steg 5: Hent nøkler og endepunkter

`get-keys.sh` henter alle Azure-nøkler og genererer en `.env`-fil i roten av repo-et.

```bash
cd challenge-0
echo "<din-bruker>-rg" | bash get-keys.sh
```

### Problem: Scriptet krever interaktiv input

`get-keys.sh` spør etter resource group-navn interaktivt. Ved å pipe inn navnet slipper du å taste det manuelt.

### Verifiser at .env er komplett

```bash
cat ../.env | head -10
```

Skal inneholde bl.a.:
- `RESOURCE_GROUP`
- `AZURE_AI_PROJECT_ENDPOINT`
- `COSMOS_ENDPOINT` / `COSMOS_KEY`
- `APIM_GATEWAY_URL` / `APIM_SUBSCRIPTION_KEY`
- `SEARCH_SERVICE_ENDPOINT` / `SEARCH_ADMIN_KEY`
- `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_KEY`

---

## Steg 6: Eksportér miljøvariabler

**Viktig: Gjør dette i HVER ny terminal!**

```bash
cd /tmp/factory-hack
source .venv/bin/activate
export $(cat .env | xargs)
```

> Uten dette vil agentene ikke finne Azure-endepunkter og nøkler.

---

## Steg 7: Seed fabrikkdata

```bash
cd challenge-0
bash seed-data.sh
```

### Hva seedet-scriptet gjør

| Hva | Detaljer |
|-----|---------|
| **9 Cosmos DB-containere** | Machines, Thresholds, Telemetry, KnowledgeBase, PartsInventory, Technicians, WorkOrders, MaintenanceHistory, MaintenanceWindows |
| **5 wiki-filer** | Markdown-filer til Blob Storage (`machine-wiki`-container) |
| **2 APIM-proxyer** | Machine API og Maintenance API med Cosmos Managed Identity |

### Problem: Seed viser «0 imported»

**Symptom:** Scriptet kjører uten feil, men sier «0 documents imported» for noen containere.

**Årsak:** Seed-scriptet er idempotent — dokumenter som allerede finnes importeres ikke på nytt.

**Konklusjon:** Helt OK. Betyr bare at noen andre allerede har seedet dataen (f.eks. arrangøren).

---

## Steg 8: Verifiser oppsettet

```bash
# Sjekk at Cosmos DB svarer
curl -s "$COSMOS_ENDPOINT" | head -1

# Sjekk at APIM svarer
curl -fsSL "$APIM_GATEWAY_URL/machine/machine-001" \
  -H "Ocp-Apim-Subscription-Key: $APIM_SUBSCRIPTION_KEY" \
  -H "Accept: application/json" | python3 -m json.tool | head -5
```

---

## Oppgaver vi hoppet over

- **Task 4** (Deploy Azure resources) — allerede provisjonert av arrangør
- **Task 7** (Assign permissions) — allerede konfigurert av arrangør

---

## Azure-ressurser opprettet

| Tjeneste | Ressursnavn | Region |
|----------|-------------|--------|
| Cosmos DB | `msagthack-cosmos-llwlhardm7pxa` | France Central |
| AI Foundry Hub | `msagthack-aifoundry-llwlhardm7pxa` | France Central |
| AI Foundry Project | `msagthack-aiproject-llwlhardm7pxa` | France Central |
| API Management | `msagthack-apim-llwlhardm7pxa` | France Central |
| AI Search | `msagthack-search-llwlhardm7pxa` | France Central |
| Storage Account | `msagthacksallwlhardm7pxa` | France Central |
| Application Insights | `msagthack-appinsights-llwlhardm7pxa` | France Central |
| Container Registry | `msagthackcrllwlhardm7pxa` | France Central |

---

## Viktige filer etter oppsett

| Fil | Innhold | OBS |
|-----|---------|-----|
| `/tmp/factory-hack/.env` | Alle nøkler og endepunkter | **Aldri commit til git!** |
| `/tmp/factory-hack/.venv/` | Python virtual environment | Lokal — ikke commit |
| `/tmp/factory-hack/challenge-0/` | Setup-scripts | Kjøres bare én gang |

---

## Lærdom

- macOS krever alltid venv for Python-pakker (PEP 668)
- Azure CLI kan lage `.azure/` med feil eierskap — sjekk rettigheter
- `get-keys.sh` krever interaktiv input — bruk pipe for automatisering
- Seed-data er idempotent — trygt å kjøre flere ganger
- **Eksportér alltid miljøvariabler** i ny terminal — dette er den vanligste feilen gjennom hele hackathonen
