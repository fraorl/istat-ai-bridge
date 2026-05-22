# References & Fonti Dati

Questo documento raccoglie i riferimenti tecnici, le fonti dei dati istituzionali e le specifiche delle API utilizzate per lo sviluppo di questo bridge tra ISTAT e Anthropic Claude.

---

## 1. Fonti Dati ISTAT (Sito Ufficiale e API)

L'applicazione interroga i dati ufficiali rilasciati dall'Istituto Nazionale di Statistica (ISTAT) attraverso i canali di interoperabilità standard.

*   **Hub della Statistica (Nuova API REST):** [https://sdmx.istat.it](https://sdmx.istat.it)
    *   L'endpoint utilizzato sfrutta lo standard internazionale **SDMX** (Statistical Data and Metadata Exchange).
*   **Specifiche del Formato JSON-stat:** [https://json-stat.org](https://json-stat.org)
    *   Il loader effettua il parsing dell'header HTTP `application/vnd.sdmx.data+json` per elaborare le risposte in modo leggero e strutturato.
*   **Dataset di Riferimento per i test:** 
    *   *Indice dei prezzi al consumo per l'intera collettività nazionale (NIC)* - Classificazione COICOP.

---

## 2. Documentazione Tecnica AI & LLM

L'integrazione con i modelli di linguaggio e la gestione della sicurezza dei prompt seguono le linee guida ufficiali fornite dai provider tecnologici.

*   **Anthropic Python SDK:** [https://github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)
    *   Utilizzato per l'integrazione nativa con il modello `claude-3-5-sonnet-latest`.
*   **Anthropic System Prompts Guide:** [https://docs.anthropic.com/claude/docs/system-prompts](https://docs.anthropic.com/claude/docs/system-prompts)
    *   Riferimento metodologico per l'isolamento del contesto dei dati e la prevenzione del rischio di *Prompt Injection* tramite il parametro nativo `system`.

---

## 3. Standard di Sviluppo e Community Italiane

*   **Linee Guida Nazionali per l'Interoperabilità dei Dati (AgID):** Riferimento ideale per i progetti inseriti nel catalogo dell'ecosistema open source italiano.
*   **Developers Italia:** [https://developers.italia.it](https://developers.italia.it) per le linee guida di riuso del software e la pubblicazione nelle community della Pubblica Amministrazione.