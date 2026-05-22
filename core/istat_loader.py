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


def fetch_category_scheme(agency: str = "IT1") -> bytes:
    url = f"{SDMX_BASE}/categoryscheme/{agency}"
    print(f"[ISTAT] Scarico category scheme da: {url}")
    content = _get(url, "application/vnd.sdmx.structure+xml;version=2.1", timeout=60)
    save_raw(content, timestamped_name(f"categoryscheme_{agency}"))
    return content


def _parse_categories_recursive(element, parent_id: str | None, scheme_id: str, result: list):
    for cat in element.findall("structure:Category", NAMESPACES_STRUCTURE):
        cat_id = cat.attrib.get("id")
        name_it = cat.findtext(
            "common:Name[@{http://www.w3.org/XML/1998/namespace}lang='it']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        name_en = cat.findtext(
            "common:Name[@{http://www.w3.org/XML/1998/namespace}lang='en']",
            namespaces=NAMESPACES_STRUCTURE,
        )
        result.append({
            "id": cat_id,
            "scheme_id": scheme_id,
            "parent_id": parent_id,
            "name_it": name_it or name_en or cat_id,
            "name_en": name_en or name_it or cat_id,
        })
        _parse_categories_recursive(cat, cat_id, scheme_id, result)


def parse_category_scheme(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    result = []
    for scheme in root.findall(".//structure:CategoryScheme", NAMESPACES_STRUCTURE):
        _parse_categories_recursive(scheme, None, scheme.attrib.get("id", ""), result)
    return result


def fetch_categorisations(agency: str = "IT1") -> bytes:
    url = f"{SDMX_BASE}/categorisation/{agency}"
    print(f"[ISTAT] Scarico categorisations da: {url}")
    content = _get(url, "application/vnd.sdmx.structure+xml;version=2.1", timeout=60)
    save_raw(content, timestamped_name(f"categorisation_{agency}"))
    return content


def parse_categorisations(xml_bytes: bytes) -> dict[str, str]:
    """Ritorna {dataflow_id: category_id} usando la prima categorizzazione trovata."""
    root = ET.fromstring(xml_bytes)
    mapping: dict[str, str] = {}
    for item in root.findall(".//structure:Categorisation", NAMESPACES_STRUCTURE):
        source = item.find("structure:Source", NAMESPACES_STRUCTURE)
        target = item.find("structure:Target", NAMESPACES_STRUCTURE)
        if source is None or target is None:
            continue
        src_ref = source.find("Ref")
        tgt_ref = target.find("Ref")
        if src_ref is None or tgt_ref is None:
            continue
        dataflow_id = src_ref.attrib.get("id")
        category_id = tgt_ref.attrib.get("id")
        if dataflow_id and category_id and dataflow_id not in mapping:
            mapping[dataflow_id] = category_id
    return mapping


def load_category_scheme(agency: str = "IT1") -> list[dict]:
    cached = latest_file(f"categoryscheme_{agency}_*.xml")
    if cached:
        return parse_category_scheme(cached.read_bytes())
    return parse_category_scheme(fetch_category_scheme(agency))


def load_categorisations(agency: str = "IT1") -> dict[str, str]:
    cached = latest_file(f"categorisation_{agency}_*.xml")
    if cached:
        return parse_categorisations(cached.read_bytes())
    return parse_categorisations(fetch_categorisations(agency))


def load_datasets(agency: str = "IT1") -> list[dict]:
    cached = latest_file(f"catalog_{agency}_*.xml")
    raw = cached.read_bytes() if cached else fetch_catalog(agency)
    datasets = parse_catalog(raw)

    categorisations = load_categorisations(agency)
    for d in datasets:
        d["category_id"] = categorisations.get(d["id"])

    return datasets


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
