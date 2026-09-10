"""Schickt jede Frage aus testfragen.json an den laufenden Dienst und vergleicht.

Prueft den Dienst als Ganzes - im Unterschied zu den pytest-Tests, die die
Bausteine einzeln pruefen. Geprueft wird die quelle und ein Stichwort, nicht
der Wortlaut.

Drei Zustaende je Fall:
  OK       quelle und Stichwort stimmen
  FALSCH   quelle oder Stichwort stimmen nicht
  AUSFALL  der Dienst hat "nicht_verfuegbar" geantwortet - der Modell-Pfad
           laeuft nicht. Zaehlt als nicht bestanden, ist aber von FALSCH
           unterscheidbar: ein toter Modell-Pfad ist keine falsche Antwort.

Exit-Code 0 nur, wenn alles OK ist - so laesst sich das Skript als Quality
Gate in eine Pipeline haengen. Exit 2 = Dienst nicht erreichbar (kein
Testergebnis, sondern gar keins).

Aufruf:  python pruefe_testfragen.py [--url http://localhost:8000/frage]
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

TESTFRAGEN = Path(__file__).parent / "testfragen.json"


def frage_stellen(url: str, frage: str) -> dict:
    """POST /frage - gibt das JSON der Antwort zurueck."""
    daten = json.dumps({"frage": frage}).encode("utf-8")
    anfrage = urllib.request.Request(url, data=daten, headers={"Content-Type": "application/json"})
    # 30 s, weil ab Phase 5 ein Modellaufruf dahinter haengt.
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        return json.load(antwort)


def pruefe_fall(fall: dict, antwort: dict) -> str:
    """Ein Fall -> "OK", "FALSCH" oder "AUSFALL"."""
    if antwort["quelle"] == "nicht_verfuegbar":
        return "AUSFALL"
    if antwort["quelle"] == fall["erwartete_quelle"] and fall["erwartet_enthaelt"] in antwort["antwort"]:
        return "OK"
    return "FALSCH"


def main() -> int:
    parser = argparse.ArgumentParser(description="Testfragen gegen den laufenden Dienst pruefen.")
    parser.add_argument("--url", default="http://localhost:8000/frage")
    args = parser.parse_args()

    faelle = json.loads(TESTFRAGEN.read_text(encoding="utf-8"))["faelle"]
    summe = {"OK": 0, "FALSCH": 0, "AUSFALL": 0}

    for fall in faelle:
        try:
            antwort = frage_stellen(args.url, fall["frage"])
        except (urllib.error.URLError, TimeoutError) as fehler:
            print(f"Dienst nicht erreichbar unter {args.url}: {fehler}")
            return 2
        zustand = pruefe_fall(fall, antwort)
        summe[zustand] += 1
        print(f"{zustand:8}[{fall['erwartete_quelle']:9}] {fall['frage']}")
        if zustand == "FALSCH":
            print(f"         erwartet: {fall['erwartete_quelle']} + '{fall['erwartet_enthaelt']}'")
            print(f"         bekommen: {antwort['quelle']} - {antwort['antwort']}")

    print(f"\n{len(faelle)} Faelle: {summe['OK']} OK, {summe['FALSCH']} FALSCH, {summe['AUSFALL']} AUSFALL")
    return 0 if summe["FALSCH"] == 0 and summe["AUSFALL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
