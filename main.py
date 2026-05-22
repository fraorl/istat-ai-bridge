import os
import json
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

class IstatAILoader:
    """Carica i dati reali dall'API ISTAT in formato JSON-stat e li trasforma per Claude."""
    
    def __init__(self, dataset_code: str):
        # Utilizziamo l'endpoint di data dissemination dell'Hub ISTAT
        self.base_url = f"https://esploradati.istat.it/SDMXWS/rest/data/{dataset_code}/all/ALL"
        
    def fetch_and_transform(self) -> str:
        """Scarica i dati reali dall'API ISTAT e decodifica il formato JSON-stat."""
        # Chiediamo esplicitamente il formato JSON-stat tramite gli header HTTP richiesti dall'ISTAT
        headers = {"Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd"}
        
        print(f"[ISTAT] Chiamata API reale in corso su: {self.base_url}")
        try:
            response = requests.get(self.base_url, headers=headers, timeout=15)
            response.raise_for_status()
            raw_data = response.json()
        except Exception as e:
            raise RuntimeError(f"Errore durante l'interrogazione dell'API ISTAT: {e}")

        # Nel formato JSON-stat, la radice contiene l'ID del dataset o una chiave generica.
        # Estraiamo il primo blocco di dataset disponibile.
        dataset_key = list(raw_data.keys())[0]
        dataset = raw_data[dataset_key]
        
        # Estrariamo i due pilastri del formato JSON-stat: i valori e le dimensioni
        values = dataset.get("value", [])
        dimensions = dataset.get("dimension", {})
        
        # Individuiamo l'ordine logico delle dimensioni (es. ['FREQ', 'TIMECOD', 'TERRITOTIO', 'INDICATORE'])
        # Questo array determina l'ordine dei cicli per mappare l'indice del vettore lineare 'value'
        id_dimension_order = dimensions.get("id", [])
        
        # Costruiamo una struttura d'appoggio per associare i codici interni ai testi leggibili (le 'label')
        dim_mappings = {}
        dim_sizes = []
        
        for dim_id in id_dimension_order:
            dim_data = dimensions[dim_id]
            # Lista ordinata dei codici di questa specifica dimensione (es. ['IT', 'ITC', 'ITF'])
            categories_index = dim_data.get("category", {}).get("index", [])
            # Dizionario delle etichette umane legate ai codici (es. {'IT': 'Italia', 'ITF': 'Sud'})
            categories_label = dim_data.get("category", {}).get("label", {})
            
            # Se l'indice è strutturato come dizionario, lo ordiniamo in base al valore dell'indice posizionale
            if isinstance(categories_index, dict):
                sorted_keys = sorted(categories_index.keys(), key=lambda k: categories_index[k])
            else:
                sorted_keys = categories_index
                
            dim_mappings[dim_id] = {
                "keys": sorted_keys,
                "labels": categories_label,
                "name": dim_data.get("label", dim_id)
            }
            dim_sizes.append(len(sorted_keys))
            
        narrative_data = []
        
        # Algoritmo di scompattamento dell'indice piatto JSON-stat:
        # Iteriamo su tutte le posizioni del vettore dei valori disponibili.
        for index, current_value in enumerate(values):
            # Se il valore è None o non rilevato dall'Istat, lo saltiamo per risparmiare token
            if current_value is None:
                continue
                
            # Calcoliamo la coordinata per ogni dimensione partendo dall'indice lineare piatto
            temp_index = index
            coordinates = {}
            
            # Scorriamo le dimensioni al contrario per scorporare i resti matematici delle matrici posizionali
            for i in reversed(range(len(id_dimension_order))):
                dim_id = id_dimension_order[i]
                size = dim_sizes[i]
                
                coord = temp_index % size
                coordinates[dim_id] = coord
                temp_index = temp_index // size
                
            # Ricostruiamo la riga descrittiva traducendo i codici tecnici in stringhe in italiano
            descriptions = []
            metadata_log = {}
            
            for dim_id in id_dimension_order:
                coord = coordinates[dim_id]
                dim_info = dim_mappings[dim_id]
                
                # Recuperiamo il codice tecnico (es. 'IT1') e la sua traduzione (es. 'Nord-ovest')
                code_key = dim_info["keys"][coord]
                human_readable_label = dim_info["labels"].get(code_key, code_key)
                
                descriptions.append(f"{dim_info['name']}: '{human_readable_label}'")
                metadata_log[dim_info['name']] = human_readable_label

            # Creiamo la stringa descrittiva ottimizzata per l'attention-mechanism di Claude
            context_line = f"- Rilevazione [ {', '.join(descriptions)} ] -> Valore registrato: {current_value}"
            narrative_data.append(context_line)
            
            # Limite di sicurezza per evitare di saturare il contesto dei prompt durante i primi test completi
            if len(narrative_data) >= 150:
                break
                
        return "\n".join(narrative_data)


def interroga_claude(contesto_dati: str, quesito: str):
    """Invia i record reali decodificati da ISTAT direttamente alle API di Claude."""
    client = Anthropic()
    modello = "claude-3-5-sonnet-latest"
    
    print(f"[Claude] Invio di {len(contesto_dati.splitlines())} record statistici a {modello}...")
    
    response = client.messages.create(
        model=modello,
        max_tokens=1000,
        temperature=0,
        system=(
            "Sei un analista economico di alto livello specializzato nel mercato italiano. "
            "Rispondi alle domande dell'utente basandoti rigorosamente ed esclusivamente sul contesto "
            "dei dati ufficiali ISTAT forniti sotto. Analizza le variazioni, confronta i territori "
            "e genera una risposta strutturata e professionale.\n\n"
            f"DATI REALI ESTRATTI DALL'API ISTAT:\n{contesto_dati}"
        ),
        messages=[{"role": "user", "content": quesito}]
    )
    return response.content[0].text


if __name__ == "__main__":
    # Utilizziamo un codice dataset reale dell'Istat: 
    # DCSC_INDPRODCONSUMO (Indice dei prezzi al consumo NIC per l'intera collettività)
    # Nota: se l'Istat aggiorna i filtri sui server, puoi usare qualsiasi codice catalogo valido da sdmx.istat.it
    CODICE_DATASET_REALE = "IT1,DCSC_INDPRODCONSUMO"
    
    loader = IstatAILoader(dataset_code=CODICE_DATASET_REALE)
    
    try:
     
        # Generiamo il contesto estraendo i dati veri dall'infrastruttura pubblica
        dati_istat_reali = loader.fetch_and_transform()
        print("Dati caricati")
        # domanda_utente = (
        #     "Analizza i dati estratti. Quali sono le principali discrepanze geografiche o "
        #     "temporali che emergono negli indici dei prezzi al consumo?"
        # )
        
        # print(f"\n[Utente]: {domanda_utente}\n")
        
        # risposta_ai = interroga_claude(contesto_dati=dati_istat_reali, quesito=domanda_utente)
        
        # print("\n--- RISPOSTA DELL'ANALISTA ECONOMICO (Dati ISTAT Reali) ---")
        # print(risposta_ai)
        
    except Exception as error:
        print(f"\n[Errore di esecuzione]: {error}")
        print("Verifica la connessione o la disponibilità temporanea dei server sdmx.istat.it")