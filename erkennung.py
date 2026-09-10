"""Erkennt, was eine Frage will - ohne Sprachmodell.

Schluesselwoerter und regulaere Ausdruecke, sonst nichts. Das ist bewusst so:
Wuerde hier ein Modell entscheiden, ob der sichere Pfad genommen wird, waere
der sichere Pfad nicht mehr sicher.

Alle Funktionen hier sind zeitunabhaengig. Woerter wie "heute" oder "jetzt"
werden nur erkannt und weitergegeben; aufgeloest werden sie erst in
antworten.py, wo die Zeit als Parameter hereinkommt.
"""

import re

from daten import WOCHENTAGE, alle_standorte


def normalisiere(text: str) -> str:
    """Kleinbuchstaben und Umlaute aufloesen, damit "Süd", "Sued" und "SÜD" gleich sind."""
    text = text.lower()
    for umlaut, ersatz in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, ersatz)
    return text


# --- Fachrichtungen -------------------------------------------------------
# Muster (auf normalisiertem Text) -> Name genau wie in standorte.json.
# \b ist eine Wortgrenze: r"\borthopaed" trifft "Orthopädie" und "Orthopäden",
# aber NICHT "Kieferorthopädie" - dort steht vor "orthopaed" ein Buchstabe.
# Die Reihenfolge entscheidet bei mehreren Treffern; genommen wird der erste.
# "Hausarzt oder Orthopäde?" liefert Allgemeinmedizin. Entscheidung 10.09.: so
# gelassen, zwei Fachrichtungen in einer Frage stehen in der README unter
# "was nicht funktioniert" - eine Rueckfrage dafuer waere ein Dialog, den der
# Dienst nicht fuehrt.
FACHRICHTUNGEN = {
    r"\ballgemeinmedizin|\bhausarzt|\bhausaerzt|\ballgemeinarzt|\ballgemeinaerzt": "Allgemeinmedizin",
    r"\binnere\b|\binternist": "Innere Medizin",
    r"\borthopaed": "Orthopädie",
    r"\bdermatolog|\bhautarzt|\bhautaerzt": "Dermatologie",
    r"\bradiolog|\broentgen|\bmrt\b|\bbildgeb": "Radiologie",
    r"\bgynaekolog|\bfrauenarzt|\bfrauenaerzt": "Gynäkologie",
    r"\bkardiolog": "Kardiologie",
    r"\bneurolog|\bnervenarzt": "Neurologie",
}

# --- Signalwoerter ----------------------------------------------------------
# Ueberweisung und Notdienst gehen IMMER ans Modell, auch wenn ein Standort
# oder "wann" in der Frage steht. Sonst wuerde "Wann brauche ich an der Alten
# Ziegelei eine Überweisung?" als Oeffnungszeiten-Frage beantwortet. Regel
# bestaetigt 10.09.: das Thema entscheidet vor dem Standort.
# Kosten (Parkgebuehren, Behandlungskosten) und Behindertenstellplaetze ebenso:
# die Antwort steht im Fliesstext oder an drei Stellen verschieden, nicht in
# einem Feld. Entscheidung vom 10.09.
# Bewertungen/Empfehlungen (Phase-4-Fund, 10.09.): stehen in keinen Daten - das
# Modell muss schweigen. Vorher machte "welcher Hausarzt hat die besten
# Bewertungen" eine Suche daraus und lieferte selbstbewusst eine Standortliste.
THEMEN_LLM = re.compile(
    r"\bueberweis|\bnotdienst|\bbereitschaft|\bnotfall"
    r"|\bkost|\bgebuehr|\bpreis|\bbezahl|\bbehindert"
    r"|\bbewert|\bempfehl"
    r"|\bausserhalb"  # "ausserhalb der Sprechzeiten" ist die Notdienst-Frage, keine Oeffnungszeiten-Frage
)

# Aktionen, die ein Auskunftsdienst nicht ausfuehrt: buchen, reservieren.
# Werden VOR dem Modell abgefangen, weil ein Sprachmodell gern so tut, als
# haette es gebucht. Bewusst nur "buch"/"reservier", nicht "termin": "Muss ich
# fuer die Radiologie einen Termin vereinbaren?" steht im Ueberweisungstext.
AUSSERHALB = re.compile(r"\bbuch|\breservier")

OEFFNUNG = re.compile(r"\boffen\b|\bgeoeffnet|\boeffnungszeit|\bsprechzeit|\bsprechstunde|\bwann\b|\buhr\b|\bgeschlossen")
ADRESSE = re.compile(r"\badresse|\banschrift|\bwo ist|\bwo liegt|\bwo finde|\bwie komme|\bwie erreiche|\berreich|\banfahrt|\bhinkomm|\bu-?bahn|\bs-?bahn|\bbahn\b|\bbus\b|\bbarrierefrei|\brollstuhl")
TELEFON = re.compile(r"\btelefon|\bnummer|\banruf|\btelefonisch")
# Parken: MIT Standort deterministisch aus dem Feld "parken", OHNE Standort ans
# Modell (Fliesstext "parken"). Entscheidung vom 08.09., Feld seit 10.09.
# "park" absichtlich ohne Wortgrenze: sonst fehlen "Behindertenparkplatz" und
# "Parkhaus". Dass "Stadtpark" mit anreisst, ist fuer eine Praxisauskunft egal.
PARKEN = re.compile(r"park|\bstellpl|\btiefgarage|\bgarage|\bauto\b|\bautos\b|\bpkw\b|\bhinstell|\babstell")
# Woerter, die aus "Fachrichtung erkannt" eine Suche machen: "Wo ...?", "Welcher Standort ...?"
SUCHE = re.compile(r"\bwo\b|\bwohin\b|\bwelche[rsm]?\b|\bgibt es\b|\bhabt ihr\b|\bhaben sie\b|\bbietet")

WOCHENTAG = re.compile(r"\b(" + "|".join(WOCHENTAGE) + r")s?\b")
# Zeitbezuege, die erst mit einem Datum einen Sinn ergeben.
ZEITBEZUG = {
    "heute": re.compile(r"\bheute\b"),
    "morgen": re.compile(r"\bmorgen\b"),
    "jetzt": re.compile(r"\bjetzt\b|\bgerade\b|\baktuell\b|\bim moment\b"),
}

# Strassen-Endungen, um eine Strasse zu erkennen, die NICHT zu uns gehoert
# (Beispiel aus der Aufgabenstellung: Humboldtstrasse). Laeuft auf dem Originaltext, damit
# der Name in der Antwort so aussieht wie in der Frage.
STRASSE = re.compile(r"\b(\w+(?:straße|strasse|gasse|weg|allee|ring|platz)|\w+\s+allee)\b", re.IGNORECASE)


# --- Erkennungsfunktionen ---------------------------------------------------

def erkenne_fachrichtung(frage: str) -> str | None:
    """Gibt die Fachrichtung zurueck, die in der Frage vorkommt, sonst None."""
    text = normalisiere(frage)
    for muster, name in FACHRICHTUNGEN.items():
        if re.search(muster, text):
            return name
    return None


def erkenne_wochentag(frage: str) -> str | None:
    """Gibt "samstag", "heute", "morgen", "jetzt" oder None zurueck.

    Ein konkreter Wochentag gewinnt gegen ein relatives Wort:
    "Samstag, also morgen?" ist eine Samstag-Frage.
    """
    text = normalisiere(frage)
    treffer = WOCHENTAG.search(text)
    if treffer:
        return treffer.group(1)
    for name, muster in ZEITBEZUG.items():
        if muster.search(text):
            return name
    return None


def _aliasse(standort: dict) -> list[str]:
    """Alle Schreibweisen, unter denen ein Standort in einer Frage vorkommen kann."""
    name = normalisiere(standort["name"])
    name = name.removeprefix("mvz ")
    strasse = normalisiere(standort["adresse"]["strasse"])
    strasse = re.sub(r"\s+\d+\w*$", "", strasse)  # Hausnummer weg: "auwiesenweg 12" -> "auwiesenweg"
    aliasse = [name, strasse]
    if name.startswith("am "):
        aliasse.append(name.removeprefix("am "))  # "Am Kupferberg" -> auch "Kupferberg"
    # Adjektive im Namen werden dekliniert: "zur Alten Ziegelei", "an der Alten Ziegelei".
    # Jedes Wort ausser dem letzten, das auf "e" endet, bekommt eine Variante mit "n".
    # Fund vom 10.09.: ohne das griff "mit dem Auto zur Alten Ziegelei" ins Leere.
    woerter = name.split()
    for i, wort in enumerate(woerter[:-1]):
        if wort.endswith("e"):
            aliasse.append(" ".join(woerter[:i] + [wort + "n"] + woerter[i + 1:]))
    return aliasse


def erkenne_standort_kandidaten(frage: str) -> list[str]:
    """Alle Standort-ids, deren Name oder Strasse in der Frage vorkommt."""
    text = normalisiere(frage)
    kandidaten = []
    for standort in alle_standorte():
        if any(alias in text for alias in _aliasse(standort)):
            kandidaten.append(standort["id"])
    return kandidaten


def erkenne_standort(frage: str) -> str | None:
    """Genau ein Standort -> seine id. Keiner oder mehrere ("Pegnitzaue") -> None.

    Im Zweifel keiner: dann fragt der Dienst zurueck, statt zu raten.
    """
    kandidaten = erkenne_standort_kandidaten(frage)
    if len(kandidaten) == 1:
        return kandidaten[0]
    return None


def erkenne_fremde_strasse(frage: str) -> str | None:
    """Eine Strasse in der Frage, die zu keinem unserer Standorte gehoert."""
    bekannte = {alias for standort in alle_standorte() for alias in _aliasse(standort)}
    for treffer in STRASSE.finditer(frage):
        wort = treffer.group(1)
        if normalisiere(wort) not in bekannte:
            return wort
    return None


def erkenne_art(frage: str) -> str:
    """Ordnet die Frage einer Anfrageart zu: suche, oeffnungszeiten, adresse oder unbekannt.

    "unbekannt" heisst hier nur: nicht mein Fall. Ob das Modell die Frage
    beantworten kann, entscheidet sich spaeter.
    """
    text = normalisiere(frage)

    if THEMEN_LLM.search(text):
        return "unbekannt"

    standort = erkenne_standort(frage)
    if standort:
        # Bei Standort + Adress- UND Oeffnungswort gewinnt die Adresse. Entscheidung
        # 10.09.: wer "wie komme ich ... wann" fragt, will zuerst den Weg; die
        # Oeffnungszeiten fragt er dann als Naechstes. Umgekehrt waere die Adresse weg.
        if ADRESSE.search(text) or TELEFON.search(text) or PARKEN.search(text):
            return "adresse"
        if OEFFNUNG.search(text) or erkenne_wochentag(frage):
            return "oeffnungszeiten"
        return "unbekannt"

    # Kein eindeutiger Standort. Fachrichtung + Suchwort/Tag = Suche ueber alle Standorte.
    if erkenne_fachrichtung(frage) and (erkenne_wochentag(frage) or SUCHE.search(text) or OEFFNUNG.search(text)):
        return "suche"

    if PARKEN.search(text):
        return "unbekannt"  # Parken ohne Standort -> Fliesstext -> Modell

    # Adresse oder Oeffnungszeiten ohne Standort: antworten.py fragt zurueck
    # oder schweigt (fremde Strasse).
    if ADRESSE.search(text) or TELEFON.search(text):
        return "adresse"
    # Ohne Standort zaehlt ein Wochentag allein NICHT als Signal:
    # "Wie wird das Wetter morgen?" bekam sonst eine Rueckfrage nach dem Standort.
    if OEFFNUNG.search(text):
        return "oeffnungszeiten"

    return "unbekannt"
