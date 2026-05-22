import json

from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"


def ask_analyst(context: str, question: str) -> str:
    client = Anthropic()
    print(f"[Claude] Invio {len(context.splitlines())} record a {MODEL}...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        temperature=0,
        system=(
            "Sei un analista economico di alto livello specializzato nel mercato italiano. "
            "Rispondi alle domande dell'utente basandoti rigorosamente ed esclusivamente sul contesto "
            "dei dati ufficiali ISTAT forniti sotto. Analizza le variazioni, confronta i territori "
            "e genera una risposta strutturata e professionale.\n\n"
            f"CONTESTO ISTAT ESTRATTO DALL'API UFFICIALE:\n{context}"
        ),
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def ask_dataset_filter(datasets: list[dict], message: str) -> dict:
    client = Anthropic()
    catalog_text = "\n".join(f"{d['id']}: {d['name_it']}" for d in datasets)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "Sei un assistente specializzato nel catalogo dei dataset ISTAT. "
            "Rispondi sempre in italiano. "
            "Quando l'utente chiede di filtrare o trovare dataset, identifica gli ID rilevanti. "
            "Rispondi SEMPRE con un JSON valido in questo formato:\n"
            '{"reply": "testo risposta per l\'utente", "filtered_ids": ["id1", "id2"] oppure null se non si filtra}\n\n'
            f"CATALOGO DATASET ISTAT (id: nome):\n{catalog_text}"
        ),
        messages=[{"role": "user", "content": message}],
    )
    raw = response.content[0].text.strip()
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"reply": raw, "filtered_ids": None}
