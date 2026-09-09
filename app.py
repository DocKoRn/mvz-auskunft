"""MVZ-Auskunftsdienst - Einstiegspunkt der Anwendung."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from antworten import WEISS_NICHT, beantworte

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
    """Nimmt eine Frage entgegen. Erst der deterministische Pfad, dann das Modell."""
    ergebnis = beantworte(eingabe.frage)
    if ergebnis is None:
        # [PRÜFEN 9] Platzhalter bis Phase 5: hier kommt der Aufruf des Modells hin.
        return Antwort(antwort=WEISS_NICHT, quelle="unbekannt")
    return Antwort(antwort=ergebnis.antwort, quelle=ergebnis.quelle)
