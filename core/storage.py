from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "downloaded_data"


def save_raw(content: bytes, filename: str) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    path.write_bytes(content)
    print(f"[Storage] Salvato: {path} ({len(content) / 1024:.1f} KB)")
    return path


def timestamped_name(prefix: str, ext: str = "xml") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"


def latest_file(pattern: str) -> Path | None:
    files = sorted(DATA_DIR.glob(pattern), reverse=True)
    return files[0] if files else None
