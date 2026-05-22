from anthropic import RateLimitError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from core.claude_client import ask_dataset_filter
from core.istat_loader import load_datasets

app = FastAPI(title="ISTAT AI Bridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/datasets")
def get_datasets():
    try:
        return load_datasets()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        datasets = load_datasets()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Errore caricamento dataset: {exc}")
    try:
        return ask_dataset_filter(datasets, req.message)
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Limite di richieste API Claude superato. Attendi qualche secondo e riprova."
        )
