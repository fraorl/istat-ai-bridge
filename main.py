import requests
import pandas as pd
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class IstatDataLLMLoader:
    """Loader personalizzato per trasformare i dati dell'API ISTAT in Documenti per LLM."""
    
    def __init__(self, dataset_code: str):
        # Endpoint ufficiale del nuovo Hub della Statistica ISTAT (SDMX REST API)
        self.base_url = f"https://sdmx.istat.it/SDMXWS/rest/data/{dataset_code}/all/ALL"
        
    def load_as_documents(self, max_records: int = 50) -> List[Document]:
        """Scarica i dati e li converte in un formato narrativo 'comprensibile' dall'LLM."""
        headers = {"Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd"}
        
        print(f"Collegamento all'API ISTAT per il dataset: {self.base_url}...")
        response = requests.get(self.base_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Errore nel recupero dati ISTAT: {response.status_code}")
            
        data = response.json()
        
        # --- PARSING DEI DATI ISTAT (Semplificato per l'esempio) ---
        # ISTAT organizza i dati in Dimensioni (regioni, anni, ecc.) e Osservazioni (i valori numerici).
        # In un progetto di produzione qui farai il parsing completo del formato JSON-stat o SDMX.
        
        documents = []
        
        # Simulazione del risultato del parsing di un dataset sull'Inflazione/Prezzi ISTAT
        # (Sostituire questo dizionario con il ciclo reale di parsing sul JSON dell'API)
        sample_records = [
            {"anno": "2024", "territorio": "Lazio", "indicatore": "NIC (Prezzi al consumo)", "valore": "1.2"},
            {"anno": "2024", "territorio": "Lombardia", "indicatore": "NIC (Prezzi al consumo)", "valore": "0.9"},
            {"anno": "2023", "territorio": "Lazio", "indicatore": "NIC (Prezzi al consumo)", "valore": "5.4"},
            {"anno": "2023", "territorio": "Lombardia", "indicatore": "NIC (Prezzi al consumo)", "valore": "5.1"},
        ]
        
        for record in sample_records[:max_records]:
            # TRASFORMAZIONE CHIAVE: Convertiamo il dato grezzo in testo narrativo (Data-to-Text)
            # Questo permette all'LLM di fare inferenze logiche precise senza confondersi con matrici grezze.
            page_content = (
                f"Statistica ISTAT dell'anno {record['anno']} per il territorio '{record['territorio']}'. "
                f"L'indicatore rilevato è '{record['indicatore']}' e il valore registrato è pari a {record['valore']}%."
            )
            
            # Creiamo il Documento standard di LangChain inserendo metadati utili per il recupero (RAG)
            metadata = {
                "source": "ISTAT API",
                "anno": record["anno"],
                "territorio": record["territorio"]
            }
            
            documents.append(Document(page_content=page_content, metadata=metadata))
            
        return documents

# --- PIPELINE DI ESECUZIONE CON LLM ---
if __name__ == "__main__":
    # 1. Inizializziamo il nostro Loader (es. Codice fittizio ISTAT per i prezzi al consumo: IT1,123_456)
    loader = IstatDataLLMLoader(dataset_code="IT1,DCSC_INDPRODCONSUMO")
    
    # 2. Carichiamo i documenti strutturati per l'AI
    docs = loader.load_as_documents()
    
    # Uniamo il contenuto dei documenti per passarlo come contesto all'LLM
    contexto_dati = "\n".join([d.page_content for d in docs])
    
    # 3. Definiamo il prompt per l'LLM
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Sei un analista economico esperto di dati italiani. Rispondi alla domanda dell'utente basandoti esclusivamente sul contesto dei dati ufficiali ISTAT forniti.\n\nContesto ISTAT:\n{context}"),
        ("human", "{question}")
    ])
    
    # 4. Inizializziamo il modello (Configura la tua API Key di OpenAI o usa Ollama per farlo in locale)
    # Assicurati di aver fatto nel terminale: export OPENAI_API_KEY="la-tua-chiave"
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    chain = prompt | llm
    
    # 5. Facciamo una domanda complessa che richiede il confronto tra record diversi
    domanda = "Quale regione ha registrato l'inflazione più alta nel 2024 tra quelle presenti? E com'è cambiata rispetto al 2023?"
    
    print(f"\nDomanda per l'LLM: {domanda}\n")
    risposta = chain.invoke({"context": contexto_dati, "question": domanda})
    
    print("--- RISPOSTA DELL'LLM ---")
    print(risposta.content)