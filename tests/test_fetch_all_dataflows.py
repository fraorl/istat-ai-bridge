import certifi
import requests
from datetime import datetime
from pathlib import Path


def fetch_all_dataflows() -> Path:
    url = "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1"
    headers = {"Accept": "application/vnd.sdmx.structure+xml;version=2.1"}

    print(f"[ISTAT] Scarico catalogo completo da: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=60, verify=certifi.where())
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Errore durante il download del catalogo ISTAT: {exc}")

    output_dir = Path("downloaded_data")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_file = output_dir / f"catalog_IT1_{timestamp}.xml"
    raw_file.write_bytes(response.content)
    print(f"[ISTAT] Catalogo salvato in: {raw_file} ({len(response.content) / 1024:.1f} KB)")
    return raw_file


if __name__ == "__main__":
    output_file = fetch_all_dataflows()
    print(f"File creato: {output_file}")
