"""Laedt die Standortdaten aus data/standorte.json und stellt sie bereit.

Diese Datei ist die einzige Stelle, die die JSON-Datei anfasst. Alle anderen
Module holen sich die Daten von hier - so gibt es genau einen Ort, an dem
sich der Pfad oder das Format aendern kann.
"""

import json
from pathlib import Path

# Path(__file__) ist diese Datei selbst; .parent der Projektordner.
# So funktioniert der Pfad unabhaengig davon, aus welchem Verzeichnis
# der Dienst gestartet wird (lokal, im Container, unter pytest).
DATEN_PFAD = Path(__file__).parent / "data" / "standorte.json"

# Reihenfolge wie datetime.weekday(): Montag = 0 ... Sonntag = 6.
# Damit uebersetzt WOCHENTAGE[datum.weekday()] ein Datum in den deutschen Namen.
WOCHENTAGE = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]


def lade_daten(pfad: Path = DATEN_PFAD) -> dict:
    """Liest die JSON-Datei und gibt sie als Dictionary zurueck."""
    with open(pfad, encoding="utf-8") as datei:
        return json.load(datei)


# [PRÜFEN 1] Die Daten werden genau einmal beim Import geladen.
# Fehlt die Datei oder ist das JSON kaputt, faellt der Dienst schon beim
# Start um - nicht erst bei der ersten Frage. Das ist Absicht (fail fast),
# muss aber als Entscheidung benannt werden koennen.
DATEN = lade_daten()


def alle_standorte() -> list[dict]:
    """Alle Standorte in der Reihenfolge der Datei."""
    return DATEN["standorte"]


def standort_nach_id(standort_id: str) -> dict | None:
    """Sucht einen Standort ueber seine id. None, wenn es ihn nicht gibt."""
    for standort in alle_standorte():
        if standort["id"] == standort_id:
            return standort
    return None


def alle_fachrichtungen() -> set[str]:
    """Jede Fachrichtung genau einmal, egal an wie vielen Standorten sie vorkommt."""
    fachrichtungen = set()
    for standort in alle_standorte():
        fachrichtungen.update(standort["fachrichtungen"])
    return fachrichtungen
