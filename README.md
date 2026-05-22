# ISTAT AI Bridge

Progetto che combina le API ufficiali ISTAT (formato SDMX) con i modelli Claude di Anthropic. Espone un'interfaccia web per esplorare il catalogo dei dataset statistici italiani e interrogarli tramite linguaggio naturale.

---

## Struttura del progetto

```
istat-ai-bridge/
├── core/
│   ├── claude_client.py   # Chiamate alle API Claude (analisi dati e chat)
│   ├── istat_loader.py    # Fetch e parsing SDMX dall'API ISTAT
│   ├── logger.py          # Logger su file con rotazione automatica
│   └── storage.py         # Gestione percorsi e salvataggio file raw
├── backend/
│   └── api.py             # Server FastAPI (REST API per il frontend)
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── DatasetList.jsx   # Pagina elenco dataset con filtri e chat
│       └── components/
│           └── Chat.jsx          # Pannello chat AI
├── tests/
│   └── test_fetch_all_dataflows.py  # Test download catalogo completo
├── downloaded_data/        # File XML scaricati dall'API ISTAT (gitignored)
├── log/                    # Log delle chiamate a Claude (gitignored)
├── main.py                 # Entry point CLI per analisi da riga di comando
└── requirements.txt
```

---

## Prerequisiti

- Python 3.10+
- Node.js 18+
- Chiave API Anthropic

---

## Installazione

```bash
# 1. Clona il repository
git clone https://github.com/tuo-username/istat-ai-bridge.git
cd istat-ai-bridge

# 2. Crea e attiva l'ambiente virtuale
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Installa le dipendenze Python
pip install -r requirements.txt

# 4. Configura la chiave API
cp .env.example .env
# Modifica .env e inserisci ANTHROPIC_API_KEY=sk-...

# 5. Installa le dipendenze del frontend
cd frontend
npm install
cd ..
```

---

## Avvio

Servono due terminali:

```bash
# Terminale 1 — backend FastAPI (porta 8000)
.venv\Scripts\uvicorn backend.api:app --reload

# Terminale 2 — frontend React (porta 5173)
cd frontend
npm run dev
```

Apri il browser su `http://localhost:5173`.

---

## Funzionalità

### Interfaccia web

- **Elenco Dataset ISTAT** — catalogo completo dei dataset disponibili sull'API SDMX di ISTAT
- **Raggruppamento per serie storica** — i dataset con lo stesso nome base vengono raggruppati in una sola card con badge per ogni anno disponibile
- **Ricerca testuale** — filtra per nome o ID dataset
- **Filtro regioni** — mostra solo i dataset con riferimento a regioni italiane, solo quelli senza, o tutti
- **Chat AI** — pannello laterale che interroga Claude per filtrare i dataset tramite linguaggio naturale (es. "mostrami i dataset sull'inflazione")

### Architettura ELT

Ogni dato scaricato dall'API ISTAT viene prima salvato in formato grezzo in `downloaded_data/` e poi trasformato in memoria. I file vengono usati come cache per le chiamate successive.

### Analisi da riga di comando

```bash
python main.py
```

Scarica le osservazioni del dataset configurato in `main.py` e le invia a Claude per l'analisi.

---

## Modello AI utilizzato

`claude-haiku-4-5-20251001` — modello veloce ed economico, adatto per query sul catalogo e analisi dati strutturati.

---

## Note tecniche

- Il catalogo ISTAT contiene circa 5000 dataset; alla chat vengono passati al massimo 1000 per rispettare i limiti di token
- Gli errori delle chiamate Claude vengono loggati in `log/claude_client.log` con rotazione automatica a 5 MB
- Il frontend usa Vite + React con proxy verso il backend FastAPI
