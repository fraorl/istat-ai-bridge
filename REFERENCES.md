# References & Fonti Dati

Riferimenti tecnici, fonti istituzionali e specifiche delle API utilizzate nel progetto.

---

## 1. API ISTAT — SDMX REST

L'applicazione interroga l'API ufficiale ISTAT tramite lo standard **SDMX 2.1** (Statistical Data and Metadata Exchange).

- **Portale dati ISTAT:** https://esploradati.istat.it
- **Base URL API:** `https://esploradati.istat.it/SDMXWS/rest/`

### Endpoint utilizzati

| Endpoint | Descrizione |
|---|---|
| `GET /dataflow/IT1` | Catalogo completo di tutti i dataset disponibili |
| `GET /dataflow/IT1/{id}/{version}` | Metadati strutturali di un singolo dataset |
| `GET /data/IT1,{id},{version}/` | Osservazioni reali (serie temporali) di un dataset |

### Formato delle risposte

- **Metadati:** `application/vnd.sdmx.structure+xml;version=2.1`
- **Dati:** `application/vnd.sdmx.genericdata+xml;version=2.1`

### Dataset di riferimento per i test

- ID `169_745` — FOI (Indice dei prezzi al consumo per famiglie di operai e impiegati), mensili dal 2016 (base 2015)

---

## 2. Anthropic Claude API

- **SDK Python:** https://github.com/anthropics/anthropic-sdk-python
- **Documentazione API:** https://docs.anthropic.com/
- **Rate limits:** https://docs.anthropic.com/en/api/rate-limits

### Modello utilizzato

`claude-haiku-4-5-20251001` — scelto per velocità e costo contenuto nelle query sul catalogo.

### Funzioni implementate

| Funzione | Modulo | Descrizione |
|---|---|---|
| `ask_analyst` | `core/claude_client.py` | Analisi dati ISTAT con system prompt da analista economico |
| `ask_dataset_filter` | `core/claude_client.py` | Filtraggio del catalogo tramite linguaggio naturale (max 1000 dataset) |

---

## 3. Stack tecnologico

### Backend
- **FastAPI** https://fastapi.tiangolo.com — server REST con CORS e gestione errori HTTP
- **Uvicorn** https://www.uvicorn.org — ASGI server per FastAPI
- **requests** https://requests.readthedocs.io — chiamate HTTP verso l'API ISTAT
- **certifi** https://pypi.org/project/certifi/ — bundle certificati SSL

### Frontend
- **Vite + React** https://vitejs.dev — scaffolding e dev server con proxy verso il backend
- **React Router** https://reactrouter.com — routing lato client

---

## 4. Standard e riferimenti normativi

- **Specifiche SDMX 2.1:** https://sdmx.org/resources/sdmx-technical-standards/
- **Linee Guida Nazionali per l'Interoperabilità (AgID):** riferimento per progetti nell'ecosistema open data italiano
- **Developers Italia:** https://developers.italia.it
