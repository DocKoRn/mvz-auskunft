"""MVZ-Auskunftsdienst - Einstiegspunkt der Anwendung."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from antworten import beantworte

app = FastAPI(title="MVZ-Auskunftsdienst")

# Antwort, wenn der Modell-Pfad nicht laeuft (kein Schluessel, API nicht erreichbar,
# Zeitueberschreitung). Bewusst OHNE technische Details - die gehoeren ins Log,
# nicht zum Patienten. Wandert in Phase 5 nach llm.py.
NICHT_VERFUEGBAR = "Diese Frage kann ich gerade nicht beantworten, der Auskunftsdienst ist nur eingeschränkt verfügbar."


class Frage(BaseModel):
    """Was der Aufrufer schickt."""

    frage: str


class Antwort(BaseModel):
    """Was der Dienst zurueckgibt."""

    antwort: str
    # daten = nachgeschlagen · llm = vom Modell · unbekannt = bewusst nicht beantwortet
    # · nicht_verfuegbar = Modell-Pfad technisch ausgefallen. Der vierte Wert ist
    # noetig, weil ein Ausfall sonst wie ein bewusstes Schweigen aussieht - und ein
    # Schweige-Testfall gruen waere, obwohl kein Modell laeuft (Entscheidung 10.09.).
    quelle: Literal["daten", "llm", "unbekannt", "nicht_verfuegbar"]


@app.post("/frage")
def frage_beantworten(eingabe: Frage) -> Antwort:
    """Nimmt eine Frage entgegen. Erst der deterministische Pfad, dann das Modell."""
    ergebnis = beantworte(eingabe.frage)
    if ergebnis is None:
        # Platzhalter bis Phase 5: hier kommt der Aufruf des Modells hin. Bis dahin
        # ist der Modell-Pfad ehrlich "nicht verfuegbar" - nicht "unbekannt".
        return Antwort(antwort=NICHT_VERFUEGBAR, quelle="nicht_verfuegbar")
    return Antwort(antwort=ergebnis.antwort, quelle=ergebnis.quelle)
