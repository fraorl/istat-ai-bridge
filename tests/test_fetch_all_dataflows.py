import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.istat_loader import fetch_catalog

if __name__ == "__main__":
    output_file = fetch_catalog()
    print(f"File creato: {output_file}")
