import xml.etree.ElementTree as ET

import certifi
import requests

from core.storage import latest_file, save_raw, timestamped_name

SDMX_BASE = "https://esploradati.istat.it/SDMXWS/rest"

NAMESPACES_STRUCTURE = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}
NAMESPACES_DATA = {
    "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}


def _get(url: str, accept: str, timeout: int = 30) -> bytes:
    response = requests.get(
        url,
        headers={"Accept": accept},
        timeout=timeout,
        verify=certifi.where(),
    )
    response.raise_for_status()
    return response.content


def fetch_catalog(agency: str = "IT1") -> bytes:
    url = f"{SDMX_BASE}/dataflow/{agency}"
    print(f"[ISTAT] Scarico catalogo da: {url}")
    content = _get(url, "application/vnd.sdmx.structure+xml;version=2.1", timeout=60)
    save_raw(content, timestamped_name(f"catalog_{agency}"))
    return content


def parse_catalog(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    datasets = []
    for df in root.findall(".//structure:Dataflow", NAMESPACES_STRUCTURE):
        name_it = df.findtext(
            "common:Name[@{http://www.w3.org/XML/1998/namespace}lang='it']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        name_en = df.findtext(
            "common:Name[@{http://www.w3.org/XML/1998/namespace}lang='en']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        desc_it = df.findtext(
            "common:Description[@{http://www.w3.org/XML/1998/namespace}lang='it']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        desc_en = df.findtext(
            "common:Description[@{http://www.w3.org/XML/1998/namespace}lang='en']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        datasets.append({
            "id": df.attrib.get("id"),
            "agency": df.attrib.get("agencyID"),
            "version": df.attrib.get("version"),
            "name_it": name_it or name_en or df.attrib.get("id"),
            "name_en": name_en or name_it or df.attrib.get("id"),
            "description_it": desc_it,
            "description_en": desc_en,
        })
    return datasets


def load_datasets(agency: str = "IT1") -> list[dict]:
    cached = latest_file(f"catalog_{agency}_*.xml")
    if cached:
        return parse_catalog(cached.read_bytes())
    return parse_catalog(fetch_catalog(agency))


class IstatAILoader:
    def __init__(self, dataflow_id: str, agency: str = "IT1", version: str = "1.0"):
        self.dataflow_id = dataflow_id
        self.agency = agency
        self.version = version
        self.base_dataflow_url = f"{SDMX_BASE}/dataflow/{agency}/{dataflow_id}/{version}"
        self.base_data_url = f"{SDMX_BASE}/data/{agency},{dataflow_id},{version}/"

    def fetch_dataflow_and_transform(self) -> str:
        print(f"[ISTAT] Chiamata dataflow: {self.base_dataflow_url}")
        try:
            content = _get(self.base_dataflow_url, "application/vnd.sdmx.structure+xml;version=2.1", timeout=15)
            save_raw(content, timestamped_name(f"raw_dataflow_{self.dataflow_id}"))
            root = ET.fromstring(content)
        except Exception as exc:
            raise RuntimeError(f"Errore API ISTAT dataflow: {exc}")

        dataflows = root.findall(".//structure:Dataflow", NAMESPACES_STRUCTURE)
        if not dataflows:
            raise RuntimeError("La risposta ISTAT non contiene dataflow SDMX.")

        print(f"[ISTAT] Righe: {len(dataflows)}, Colonne: {len(dataflows[0].attrib)}")

        rows = []
        for df in dataflows:
            df_id = df.attrib.get("id", "sconosciuto")
            agency_id = df.attrib.get("agencyID", "sconosciuta")
            version = df.attrib.get("version", "sconosciuta")
            name = df.findtext("common:Name", default=df_id, namespaces=NAMESPACES_STRUCTURE)
            ref = df.find(".//Ref")
            dsd_id = ref.attrib.get("id", "non indicata") if ref is not None else "non indicata"
            rows.append(
                f"- Dataflow ISTAT [agenzia: {agency_id}, id: {df_id}, versione: {version}]"
                f" -> Nome: {name}; DSD collegata: {dsd_id}"
            )
        return "\n".join(rows)

    def fetch_data_and_transform(self) -> str:
        print(f"[ISTAT] Chiamata data: {self.base_data_url}")
        try:
            content = _get(self.base_data_url, "application/vnd.sdmx.genericdata+xml;version=2.1", timeout=30)
            save_raw(content, timestamped_name(f"raw_data_{self.dataflow_id}"))
            root = ET.fromstring(content)
        except Exception as exc:
            raise RuntimeError(f"Errore API ISTAT data: {exc}")

        series_list = root.findall(".//generic:Series", NAMESPACES_DATA)
        if not series_list:
            raise RuntimeError("La risposta ISTAT non contiene serie di dati SDMX.")

        print(f"[ISTAT] Serie trovate: {len(series_list)}")

        rows = []
        for series in series_list:
            key_values = {
                kv.attrib["id"]: kv.attrib["value"]
                for kv in series.findall("generic:SeriesKey/generic:Value", NAMESPACES_DATA)
            }
            for obs in series.findall("generic:Obs", NAMESPACES_DATA):
                dim = obs.find("generic:ObsDimension", NAMESPACES_DATA)
                period = dim.attrib.get("value", "?") if dim is not None else "?"
                val_el = obs.find("generic:ObsValue", NAMESPACES_DATA)
                value = val_el.attrib.get("value", "?") if val_el is not None else "?"
                key_str = ", ".join(f"{k}={v}" for k, v in key_values.items())
                rows.append(f"- [{key_str}] periodo={period}, valore={value}")
        return "\n".join(rows)
