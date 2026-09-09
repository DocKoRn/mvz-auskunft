"""Bausteine des deterministischen Pfads - ohne Dienst, ohne Modell, ohne echte Uhr.

Diese Tests pruefen die Funktionen einzeln. Ob der Dienst als Ganzes
funktioniert, prueft spaeter pruefe_testfragen.py gegen den Endpunkt.
"""

from datetime import datetime

from antworten import beantworte, oeffnungszeiten_aus_daten, standorte_suchen
from daten import standort_nach_id
from erkennung import erkenne_art, erkenne_fachrichtung, erkenne_fremde_strasse, erkenne_standort

# Eingefrorene Zeit: Mittwoch, 09.09.2026. Pegnitzaue Nord hat mittwochs 08:00-12:00.
MITTWOCH_VORMITTAG = datetime(2026, 9, 9, 10, 0)
MITTWOCH_NACHMITTAG = datetime(2026, 9, 9, 13, 0)
SAMSTAG = datetime(2026, 9, 12, 10, 0)


# --- erkennung.py -----------------------------------------------------------

def test_samstag_hausarzt_ist_eine_suche():
    assert erkenne_art("Wo kann ich am Samstag zum Hausarzt?") == "suche"


def test_ueberweisung_ist_nicht_deterministisch():
    # Beispielfrage 2 aus der Aufgabenstellung: Fliesstext, gehoert ans Modell.
    assert erkenne_art("Brauche ich für die Orthopädie eine Überweisung?") == "unbekannt"


def test_ueberweisung_schlaegt_oeffnungswort():
    assert erkenne_art("Wann brauche ich an der Alten Ziegelei eine Überweisung?") == "unbekannt"


def test_standort_ueber_namen():
    assert erkenne_standort("Wie komme ich zum MVZ Lindenhof?") == "lindenhof"


def test_standort_ueber_strasse_ohne_umlaut():
    assert erkenne_standort("Wann hat die Praxis in der Herbstweiherstrasse offen?") == "pegnitzaue-sued"


def test_pegnitzaue_allein_ist_mehrdeutig():
    assert erkenne_standort("Hat Pegnitzaue am Montag offen?") is None


def test_kieferorthopaedie_ist_keine_orthopaedie():
    assert erkenne_fachrichtung("Habt ihr Kieferorthopädie?") is None


def test_humboldtstrasse_ist_fremd():
    assert erkenne_fremde_strasse("Wie erreiche ich die Praxis in der Humboldtstraße?") == "Humboldtstraße"


# --- antworten.py: nachschlagen -------------------------------------------

def test_suche_samstag_allgemeinmedizin():
    treffer = standorte_suchen("Allgemeinmedizin", "samstag")
    assert [s["id"] for s in treffer] == ["pegnitzaue-sued"]


def test_suche_sonntag_findet_nichts():
    assert standorte_suchen("Allgemeinmedizin", "sonntag") == []


def test_oeffnungszeiten_samstag_sued():
    text = oeffnungszeiten_aus_daten(standort_nach_id("pegnitzaue-sued"), wochentag="samstag")
    assert "09:00" in text and "12:00" in text


def test_jetzt_offen_mit_eingefrorener_zeit():
    text = oeffnungszeiten_aus_daten(standort_nach_id("pegnitzaue-nord"), jetzt=MITTWOCH_VORMITTAG)
    assert "geöffnet" in text


def test_jetzt_geschlossen_mit_eingefrorener_zeit():
    text = oeffnungszeiten_aus_daten(standort_nach_id("pegnitzaue-nord"), jetzt=MITTWOCH_NACHMITTAG)
    assert "geschlossen" in text


# --- antworten.py: der ganze Pfad -----------------------------------------

def test_heute_wird_aus_eingefrorener_zeit_aufgeloest():
    ergebnis = beantworte("Hat Pegnitzaue Süd heute offen?", jetzt=SAMSTAG)
    assert ergebnis.quelle == "daten"
    assert "Samstag" in ergebnis.antwort and "09:00" in ergebnis.antwort


def test_telefon_sonnenfeld_schweigt():
    ergebnis = beantworte("Wie ist die Telefonnummer vom MVZ Sonnenfeld?", jetzt=MITTWOCH_VORMITTAG)
    assert ergebnis.quelle == "unbekannt"


def test_humboldtstrasse_schweigt():
    ergebnis = beantworte("Wie erreiche ich die Praxis in der Humboldtstraße?", jetzt=MITTWOCH_VORMITTAG)
    assert ergebnis.quelle == "unbekannt"
    assert "Humboldtstraße" in ergebnis.antwort


def test_wetter_mit_morgen_bekommt_keine_rueckfrage():
    # "morgen" allein ist kein Grund, nach dem Standort zu fragen.
    assert beantworte("Wie wird das Wetter morgen?", jetzt=MITTWOCH_VORMITTAG) is None


def test_fliesstext_frage_wird_weitergereicht():
    assert beantworte("Brauche ich für die Orthopädie eine Überweisung?", jetzt=MITTWOCH_VORMITTAG) is None
