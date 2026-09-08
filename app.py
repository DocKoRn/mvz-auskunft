"""MVZ-Auskunftsdienst - Einstiegspunkt der Anwendung."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MVZ-Auskunftsdienst")


class Frage(BaseModel):
    """Was der Aufrufer schickt."""

    frage: str


class Antwort(BaseModel):
    """Was der Dienst zurueckgibt."""

    antwort: str
    quelle: Literal["daten", "llm", "unbekannt"]


@app.post("/frage")
def frage_beantworten(eingabe: Frage) -> Antwort:
    """Nimmt eine Frage entgegen. Vorerst nur eine Attrappe."""
    return Antwort(antwort="noch nicht gebaut", quelle="unbekannt")