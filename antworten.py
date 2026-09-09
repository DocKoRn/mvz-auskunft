"""Antworten aus den Daten - nachschlagen, nicht erzeugen.

Die Funktionen hier lesen aus standorte.json und formulieren daraus Saetze.
Sie erfinden nichts. Steht etwas nicht in den Daten, sagen sie das.

Zeit: Alles, was von "jetzt" abhaengt, bekommt die Zeit als Parameter
`jetzt` herein. Im Betrieb ist das datetime.now(), im Test ein festes Datum.
So laeuft ein Test montags genauso durch wie sonntags.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from daten import WOCHENTAGE, alle_standorte, standort_nach_id
from erkennung import (
    PARKEN,
    TELEFON,
    erkenne_art,
    erkenne_fachrichtung,
    erkenne_fremde_strasse,
    erkenne_standort,
    erkenne_standort_kandidaten,
    erkenne_wochentag,
    normalisiere,
)

WEISS_NICHT = "Das weiß ich nicht."


@dataclass
class Ergebnis:
    """Was der deterministische Pfad zurueckgibt: Text plus Herkunft."""

    antwort: str
    quelle: str  # "daten" oder "unbekannt" - "llm" kommt erst in Phase 5


# --- Hilfsfunktionen --------------------------------------------------------

def wochentag_aus_datum(datum: datetime) -> str:
    """datetime -> "montag" ... "sonntag"."""
    return WOCHENTAGE[datum.weekday()]


def _gross(wochentag: str) -> str:
    return wochentag.capitalize()


def _zeitfenster_text(fenster: list[list[str]]) -> str:
    """[["08:00","12:00"],["14:00","18:00"]] -> "08:00–12:00 und 14:00–18:00 Uhr"."""
    if not fenster:
        return "geschlossen"
    teile = [f"{von}–{bis}" for von, bis in fenster]
    return " und ".join(teile) + " Uhr"


def _ist_offen(fenster: list[list[str]], uhrzeit: str) -> bool:
    """Liegt die Uhrzeit ("13:30") in einem der Zeitfenster?

    Vergleich als Text funktioniert, weil alle Zeiten mit fuehrender Null
    geschrieben sind: "08:00" < "13:30" stimmt, "9:00" < "13:30" nicht.
    """
    return any(von <= uhrzeit < bis for von, bis in fenster)


def _adresse_kurz(standort: dict) -> str:
    adresse = standort["adresse"]
    return f"{adresse['strasse']}, {adresse['plz']} {adresse['ort']}"


# --- Die drei Nachschlage-Funktionen (Roadmap Phase 3, Punkt 4) ------------

def standorte_suchen(fachrichtung: str, wochentag: str | None = None) -> list[dict]:
    """Alle Standorte mit dieser Fachrichtung; mit Wochentag nur die, die dann offen haben.

    Das ist die Suche: ein Filter ueber alle Standorte, keine Nachschlagefrage.
    """
    treffer = []
    for standort in alle_standorte():
        if fachrichtung not in standort["fachrichtungen"]:
            continue
        if wochentag and not standort["oeffnungszeiten"][wochentag]:
            continue
        treffer.append(standort)
    return treffer


def oeffnungszeiten_aus_daten(standort: dict, wochentag: str | None = None, jetzt: datetime | None = None) -> str:
    """Ein Satz zu den Oeffnungszeiten.

    - ohne Wochentag: die ganze Woche
    - mit Wochentag: nur dieser Tag
    - mit jetzt: ob gerade offen ist (Wochentag wird dann aus jetzt genommen)
    """
    name = standort["name"]
    zeiten = standort["oeffnungszeiten"]

    if jetzt is not None:
        tag = wochentag_aus_datum(jetzt)
        uhrzeit = jetzt.strftime("%H:%M")
        zustand = "geöffnet" if _ist_offen(zeiten[tag], uhrzeit) else "geschlossen"
        return (f"{name} ist jetzt ({_gross(tag)}, {uhrzeit} Uhr) {zustand}. "
                f"Öffnungszeiten am {_gross(tag)}: {_zeitfenster_text(zeiten[tag])}.")

    if wochentag is not None:
        if not zeiten[wochentag]:
            return f"{name} ist am {_gross(wochentag)} geschlossen."
        return f"{name} hat am {_gross(wochentag)} von {_zeitfenster_text(zeiten[wochentag])} geöffnet."

    tage = [f"{_gross(tag)} {_zeitfenster_text(zeiten[tag])}" for tag in WOCHENTAGE]
    return f"Öffnungszeiten {name}: " + ", ".join(tage) + "."


def adresse_aus_daten(standort: dict) -> str:
    """Adresse, Telefon und Erreichbarkeit in einem Satz."""
    telefon = standort["telefon"]
    telefon_text = f"Telefon: {telefon}." if telefon else "Eine Telefonnummer ist nicht hinterlegt."
    return f"{standort['name']}, {_adresse_kurz(standort)}. {telefon_text} Anfahrt: {standort['erreichbarkeit']}"


# --- Zusammenbau: von der Frage zur Antwort ---------------------------------

def _rueckfrage(frage: str) -> Ergebnis:
    """Kein eindeutiger Standort: die Kandidaten nennen, sonst alle."""
    ids = erkenne_standort_kandidaten(frage)
    standorte = [standort_nach_id(i) for i in ids] if len(ids) > 1 else alle_standorte()
    namen = ", ".join(s["name"] for s in standorte)
    # [PRÜFEN 5] Eine Rueckfrage ist keine Antwort -> quelle "unbekannt".
    # Lesart von quelle: "daten" = beantwortet aus den Daten, "unbekannt" = nicht beantwortet.
    return Ergebnis(f"Welchen Standort meinen Sie? Ich kenne: {namen}.", "unbekannt")


def _antwort_suche(frage: str, jetzt: datetime) -> Ergebnis:
    fachrichtung = erkenne_fachrichtung(frage)
    wochentag = _wochentag_aufloesen(erkenne_wochentag(frage), jetzt)
    treffer = standorte_suchen(fachrichtung, wochentag)
    if not treffer:
        wann = f" am {_gross(wochentag)}" if wochentag else ""
        return Ergebnis(f"Keiner unserer Standorte mit {fachrichtung} hat{wann} geöffnet.", "daten")
    if wochentag:
        teile = [f"{s['name']} ({_adresse_kurz(s)}), {_zeitfenster_text(s['oeffnungszeiten'][wochentag])}" for s in treffer]
        return Ergebnis(f"{fachrichtung} am {_gross(wochentag)}: " + "; ".join(teile) + ".", "daten")
    teile = [f"{s['name']} ({_adresse_kurz(s)})" for s in treffer]
    return Ergebnis(f"{fachrichtung} gibt es an diesen Standorten: " + "; ".join(teile) + ".", "daten")


def _antwort_oeffnungszeiten(frage: str, standort: dict, jetzt: datetime) -> Ergebnis:
    tag_wort = erkenne_wochentag(frage)
    if tag_wort == "jetzt":
        text = oeffnungszeiten_aus_daten(standort, jetzt=jetzt)
    else:
        text = oeffnungszeiten_aus_daten(standort, wochentag=_wochentag_aufloesen(tag_wort, jetzt))
    # [PRÜFEN 6 · KRITISCH] Die Daten kennen Oeffnungszeiten nur je Standort, nicht je
    # Fachrichtung. Fragt jemand nach "Orthopädie am Samstag in Süd", gilt die
    # Antwort fuer das Haus - der Hinweis macht das sichtbar, statt es zu verschweigen.
    if erkenne_fachrichtung(frage):
        text += " Die Zeiten gelten für den Standort, nicht für einzelne Fachrichtungen."
    return Ergebnis(text, "daten")


def _antwort_adresse(frage: str, standort: dict) -> Ergebnis:
    text = normalisiere(frage)
    name = standort["name"]

    if TELEFON.search(text):
        if standort["telefon"] is None:
            return Ergebnis(f"{WEISS_NICHT} Für {name} ist keine Telefonnummer hinterlegt.", "unbekannt")
        return Ergebnis(f"{name} erreichen Sie telefonisch unter {standort['telefon']}.", "daten")

    if PARKEN.search(text):
        # [PRÜFEN 7 · KRITISCH] Aus der Erreichbarkeit nur die Saetze mit "park" - eine
        # Textfilterung, kein Nachschlagen. Grenzfall fuer "deterministisch".
        saetze = [s.strip() for s in standort["erreichbarkeit"].split(".") if "park" in s.lower()]
        if not saetze:
            return Ergebnis(f"{WEISS_NICHT} Zu Parkmöglichkeiten am {name} ist nichts hinterlegt.", "unbekannt")
        return Ergebnis(f"Parken am {name}: " + ". ".join(saetze) + ".", "daten")

    return Ergebnis(adresse_aus_daten(standort), "daten")


def _wochentag_aufloesen(tag_wort: str | None, jetzt: datetime) -> str | None:
    """"heute"/"morgen"/"jetzt" -> echter Wochentag; "samstag" bleibt; None bleibt."""
    if tag_wort in ("heute", "jetzt"):
        return wochentag_aus_datum(jetzt)
    if tag_wort == "morgen":
        return wochentag_aus_datum(jetzt + timedelta(days=1))
    return tag_wort


def beantworte(frage: str, jetzt: datetime | None = None) -> Ergebnis | None:
    """Der deterministische Pfad. None heisst: nicht mein Fall, das Modell ist dran.

    `jetzt` ist die einzige Stelle, an der die echte Uhr ins Spiel kommt.
    [PRÜFEN 8 · KRITISCH] Drei Ausgaenge: Ergebnis mit "daten" (beantwortet), Ergebnis mit
    "unbekannt" (bewusst nicht beantwortet: Rueckfrage, fremde Strasse, fehlende
    Nummer) und None (weiterreichen). In Phase 5 haengt am None der LLM-Aufruf.
    """
    if jetzt is None:
        jetzt = datetime.now()

    art = erkenne_art(frage)
    if art == "unbekannt":
        return None

    if art == "suche":
        return _antwort_suche(frage, jetzt)

    standort_id = erkenne_standort(frage)
    if standort_id is None:
        fremde = erkenne_fremde_strasse(frage)
        if fremde:
            return Ergebnis(f"{WEISS_NICHT} Einen Standort in der {fremde} habe ich nicht in meinen Daten.", "unbekannt")
        return _rueckfrage(frage)

    standort = standort_nach_id(standort_id)
    if art == "oeffnungszeiten":
        return _antwort_oeffnungszeiten(frage, standort, jetzt)
    return _antwort_adresse(frage, standort)
