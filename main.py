from dotenv import load_dotenv

from core.claude_client import ask_analyst
from core.istat_loader import IstatAILoader

load_dotenv()

if __name__ == "__main__":
    DATAFLOW_ISTAT = "169_745"

    loader = IstatAILoader(dataflow_id=DATAFLOW_ISTAT)

    try:
        dati_istat_reali = loader.fetch_data_and_transform()
        print("Dati caricati")
        print(dati_istat_reali)

        domanda_utente = "quali anni sono presenti nel dataset e quali sono i criteri geografici."

        print(f"\n[Utente]: {domanda_utente}\n")

        risposta_ai = ask_analyst(context=dati_istat_reali, question=domanda_utente)

        print("\n--- RISPOSTA DELL'ANALISTA ECONOMICO (Dati ISTAT Reali) ---")
        print(risposta_ai)

    except Exception as error:
        print(f"\n[Errore di esecuzione]: {error}")
        print("Verifica la connessione o la disponibilita temporanea dei server sdmx.istat.it")
