import certifi
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


class IstatAILoader:
    """Carica metadati reali dall'API ISTAT SDMX e li trasforma per Claude."""

    def __init__(self, dataflow_id: str, agency: str = "IT1", version: str = "1.0"):
        self.dataflow_id = dataflow_id
        self.agency = agency
        self.version = version
        self.base_dataflow_url = (
            "https://esploradati.istat.it/SDMXWS/rest/"
            f"dataflow/{agency}/{dataflow_id}/{version}"
        )
        self.base_data_url = (
            "https://esploradati.istat.it/SDMXWS/rest/"
            f"data/{agency},{dataflow_id},{version}/"
        )

    def fetch_dataflow_and_transform(self) -> str:
        """Scarica la definizione strutturale del dataflow ISTAT (metadati SDMX)."""
        headers = {"Accept": "application/vnd.sdmx.structure+xml;version=2.1"}

        print(f"[ISTAT] Chiamata dataflow in corso su: {self.base_dataflow_url}")
        try:
            response = requests.get(
                self.base_dataflow_url,
                headers=headers,
                timeout=15,
                verify=certifi.where(),
            )
            response.raise_for_status()

            # ELT — Load: salvataggio del dato grezzo prima di qualsiasi trasformazione
            output_dir = Path("downloaded_data")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = output_dir / f"raw_dataflow_{self.dataflow_id}_{timestamp}.xml"
            raw_file.write_bytes(response.content)
            print(f"[ISTAT] Dato grezzo salvato in: {raw_file}")

            root = ET.fromstring(response.content)
        except Exception as exc:
            raise RuntimeError(f"Errore durante l'interrogazione dell'API ISTAT: {exc}")

        namespaces = {
            "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
            "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
        }
        dataflows = root.findall(".//structure:Dataflow", namespaces)
       
        if not dataflows:
            raise RuntimeError("La risposta ISTAT non contiene dataflow SDMX.")

        print(f"[ISTAT] Righe (dataflow): {len(dataflows)}, Colonne (attributi): {len(dataflows[0].attrib)}")

        narrative_data = []
        for dataflow in dataflows:
            dataflow_id = dataflow.attrib.get("id", "sconosciuto")
            agency_id = dataflow.attrib.get("agencyID", "sconosciuta")
            version = dataflow.attrib.get("version", "sconosciuta")
            name = dataflow.findtext(
                "common:Name",
                default=dataflow_id,
                namespaces=namespaces,
            )
            structure_ref = dataflow.find(".//Ref")
            dsd_id = (
                structure_ref.attrib.get("id", "non indicata")
                if structure_ref is not None
                else "non indicata"
            )

            narrative_data.append(
                "- Dataflow ISTAT "
                f"[agenzia: {agency_id}, id: {dataflow_id}, versione: {version}] "
                f"-> Nome: {name}; DSD collegata: {dsd_id}"
            )

        return "\n".join(narrative_data)

    def fetch_data_and_transform(self) -> str:
        """Scarica le osservazioni reali del dataset ISTAT (dati SDMX)."""
        headers = {"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1"}

        print(f"[ISTAT] Chiamata data in corso su: {self.base_data_url}")
        try:
            response = requests.get(
                self.base_data_url,
                headers=headers,
                timeout=30,
                verify=certifi.where(),
            )
            response.raise_for_status()

            # ELT — Load: salvataggio del dato grezzo prima di qualsiasi trasformazione
            output_dir = Path("downloaded_data")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = output_dir / f"raw_data_{self.dataflow_id}_{timestamp}.xml"
            raw_file.write_bytes(response.content)
            print(f"[ISTAT] Dato grezzo salvato in: {raw_file}")

            root = ET.fromstring(response.content)
        except Exception as exc:
            raise RuntimeError(f"Errore durante l'interrogazione dell'API ISTAT: {exc}")

        namespaces = {
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
            "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
        }
        series_list = root.findall(".//generic:Series", namespaces)

        if not series_list:
            raise RuntimeError("La risposta ISTAT non contiene serie di dati SDMX.")

        print(f"[ISTAT] Serie trovate: {len(series_list)}")

        narrative_data = []
        for series in series_list:
            key_values = {
                kv.attrib["id"]: kv.attrib["value"]
                for kv in series.findall("generic:SeriesKey/generic:Value", namespaces)
            }
            obs_list = series.findall("generic:Obs", namespaces)
            for obs in obs_list:
                period = obs.findtext("generic:ObsDimension", namespaces=namespaces)
                if period is None:
                    dim = obs.find("generic:ObsDimension", namespaces)
                    period = dim.attrib.get("value", "?") if dim is not None else "?"
                value_el = obs.find("generic:ObsValue", namespaces)
                value = value_el.attrib.get("value", "?") if value_el is not None else "?"
                key_str = ", ".join(f"{k}={v}" for k, v in key_values.items())
                narrative_data.append(f"- [{key_str}] periodo={period}, valore={value}")

        return "\n".join(narrative_data)


def interroga_claude(contesto_dati: str, quesito: str):
    """Invia il contesto ISTAT decodificato direttamente alle API di Claude."""
    client = Anthropic()
    modello = "claude-haiku-4-5-20251001"

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
            f"CONTESTO ISTAT ESTRATTO DALL'API UFFICIALE:\n{contesto_dati}"
        ),
        messages=[{"role": "user", "content": quesito}],
    )
    return response.content[0].text


if __name__ == "__main__":
    DATAFLOW_ISTAT = "169_745"

    loader = IstatAILoader(dataflow_id=DATAFLOW_ISTAT)

    try:
        dati_istat_reali = loader.fetch_data_and_transform()
        print("Dati caricati")
        print(dati_istat_reali)

        domanda_utente = (
            #"Descrivi il dataflow ISTAT caricato e indica quali metadati sono disponibili."
              "quali anni sono presenti nel dataset e uali sono i criteri geografici."
        )
        
        print(f"\n[Utente]: {domanda_utente}\n")
        
        #risposta_ai = interroga_claude(contesto_dati=dati_istat_reali, quesito=domanda_utente)
        
        print("\n--- RISPOSTA DELL'ANALISTA ECONOMICO (Dati ISTAT Reali) ---")
        print(risposta_ai)

    except Exception as error:
        print(f"\n[Errore di esecuzione]: {error}")
        print("Verifica la connessione o la disponibilita temporanea dei server sdmx.istat.it")
