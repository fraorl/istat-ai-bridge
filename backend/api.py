import xml.etree.ElementTree as ET
from pathlib import Path

import certifi
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ISTAT AI Bridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

NAMESPACES = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

# downloaded_data/ è relativa alla root del progetto, da cui si lancia uvicorn
DATA_DIR = Path(__file__).resolve().parents[1] / "downloaded_data"


def _latest_catalog_file() -> Path | None:
    files = sorted(DATA_DIR.glob("catalog_IT1_*.xml"), reverse=True)
    return files[0] if files else None


def _parse_catalog(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    datasets = []
    for df in root.findall(".//structure:Dataflow", NAMESPACES):
        name_it = df.findtext("common:Name[@{http://www.w3.org/XML/1998/namespace}lang='it']", namespaces=NAMESPACES)
        name_en = df.findtext("common:Name[@{http://www.w3.org/XML/1998/namespace}lang='en']", namespaces=NAMESPACES)
        desc_it = df.findtext("common:Description[@{http://www.w3.org/XML/1998/namespace}lang='it']", namespaces=NAMESPACES)
        desc_en = df.findtext("common:Description[@{http://www.w3.org/XML/1998/namespace}lang='en']", namespaces=NAMESPACES)
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


@app.get("/api/datasets")
def get_datasets():
    catalog = _latest_catalog_file()
    if catalog:
        return _parse_catalog(catalog.read_bytes())

    try:
        response = requests.get(
            "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1",
            headers={"Accept": "application/vnd.sdmx.structure+xml;version=2.1"},
            timeout=60,
            verify=certifi.where(),
        )
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return _parse_catalog(response.content)
