import certifi
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


class IstatAILoader:
    """Carica metadati reali dall'API ISTAT SDMX e li trasforma per Claude."""

    def __init__(self, dataflow_id: str, agency: str = "IT1", version: str = "latest"):
        self.base_url = (
            "https://esploradati.istat.it/SDMXWS/rest/"
            f"dataflow/{agency}/{dataflow_id}/{version}"
        )

    def fetch_and_transform(self) -> str:
        """Scarica il dataflow ISTAT e decodifica il formato SDMX-XML."""
        headers = {"Accept": "application/vnd.sdmx.structure+xml;version=2.1"}

        print(f"[ISTAT] Chiamata API reale in corso su: {self.base_url}")
        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                timeout=15,
                verify=certifi.where(),
            )
            response.raise_for_status()
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


def interroga_claude(contesto_dati: str, quesito: str):
    """Invia il contesto ISTAT decodificato direttamente alle API di Claude."""
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
            f"CONTESTO ISTAT ESTRATTO DALL'API UFFICIALE:\n{contesto_dati}"
        ),
        messages=[{"role": "user", "content": quesito}],
    )
    return response.content[0].text


if __name__ == "__main__":
    DATAFLOW_ISTAT = "169_745"

    loader = IstatAILoader(dataflow_id=DATAFLOW_ISTAT)

    try:
        dati_istat_reali = loader.fetch_and_transform()
        print("Dati caricati")
        print(dati_istat_reali)

        # domanda_utente = (
        #     "Descrivi il dataflow ISTAT caricato e indica quali metadati sono disponibili."
        # )
        #
        # print(f"\n[Utente]: {domanda_utente}\n")
        #
        # risposta_ai = interroga_claude(contesto_dati=dati_istat_reali, quesito=domanda_utente)
        #
        # print("\n--- RISPOSTA DELL'ANALISTA ECONOMICO (Dati ISTAT Reali) ---")
        # print(risposta_ai)

    except Exception as error:
        print(f"\n[Errore di esecuzione]: {error}")
        print("Verifica la connessione o la disponibilita temporanea dei server sdmx.istat.it")
