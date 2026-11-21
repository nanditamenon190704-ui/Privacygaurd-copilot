from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import ask
from privacy import redact, restore

app = FastAPI(title="PrivacyGuard Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit trail: stores only counts and timestamps, never the raw text
AUDIT_LOG = []


class RedactRequest(BaseModel):
    text: str


class AskRequest(BaseModel):
    text: str
    question: str


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/redact")
def redact_endpoint(req: RedactRequest):
    result = redact(req.text)
    result.pop("mapping")  # never send the real values back out
    return result


@app.post("/ask")
async def ask_endpoint(req: AskRequest):
    result = redact(req.text)
    mapping = result.pop("mapping")  # stays here, never sent to the AI

    ai_answer = await ask(result["redacted_text"], result["counts"], req.question)
    final_answer = restore(ai_answer, mapping)

    AUDIT_LOG.append(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "redaction_counts": result["counts"],
            "input_length": len(req.text),
        }
    )
    return {
        "redacted_text": result["redacted_text"],
        "counts": result["counts"],
        "ai_answer": ai_answer,
        "answer": final_answer,
    }


@app.get("/audit")
def audit():
    return AUDIT_LOG