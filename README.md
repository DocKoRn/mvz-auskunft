# MVZ-Auskunftsdienst

Ein kleiner Auskunftsdienst für ein erfundenes Medizinisches Versorgungszentrum mit sechs
Standorten. Er beantwortet Patientenfragen zu Standorten, Öffnungszeiten, Anfahrt und Parken
**ohne Sprachmodell** direkt aus den hinterlegten Daten. Fragen zu Überweisungen, Notdienst
und Kosten sind für ein Sprachmodell vorgesehen – dieser Pfad ist noch nicht angebunden
(siehe unten, *Wo ich aufgehört habe*).

Praxisaufgabe im Rahmen einer Bewerbung, September 2026. Python 3.14, FastAPI, pytest.
Gebaut mit Claude Code – die Steuerungsdatei ist `CLAUDE.md`; wo der Assistent danebenlag und
woran ich es gemerkt habe, steht in `ASSISTENT.md`.

## Starten

Lokal:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8000
```

Oder mit Docker:

```bash
docker compose up --build
```

Der Dienst startet auch ohne `.env` – die deterministischen Antworten brauchen keinen
Schlüssel. Für die spätere Modellanbindung: `.env.example` nach `.env` kopieren.

## Beispiel

```bash
curl -s -X POST localhost:8000/frage -H 'Content-Type: application/json' \
  -d '{"frage": "Wo kann ich am Samstag zum Hausarzt?"}'
```

```json
{"antwort": "Allgemeinmedizin am Samstag: MVZ Pegnitzaue Süd (Herbstweiherstraße 4, 90461 Nürnberg), 09:00–12:00 Uhr.", "quelle": "daten"}
```

Jede Antwort trägt ein Feld `quelle`, das von außen zeigt, welcher Pfad gelaufen ist:

| `quelle` | Bedeutung |
|---|---|
| `daten` | aus `data/standorte.json` nachgeschlagen |
| `llm` | vom Sprachmodell (noch nicht angebunden) |
| `unbekannt` | bewusst nicht beantwortet: Rückfrage, fremde Straße, fehlende Angabe, Aktion |
| `nicht_verfuegbar` | der Modell-Pfad läuft nicht – technischer Ausfall, kein Schweigen |

Die vierte Ausprägung gibt es, damit ein Ausfall nicht wie ein bewusstes Schweigen aussieht.
Sonst wäre ein Schweige-Testfall grün, obwohl kein Modell läuft.

## Was ohne Modell beantwortet wird – und warum

Drei Anfragearten werden rein deterministisch beantwortet (`erkennung.py` erkennt die Art per
Schlüsselwörtern und regulären Ausdrücken, `antworten.py` schlägt nach):

- **Suche** – „Wo kann ich am Samstag zum Hausarzt?" Ein Filter über alle Standorte:
  Fachrichtung plus Wochentag.
- **Öffnungszeiten** – fester Wochentag, „heute", „morgen", „jetzt". Die Uhrzeit kommt als
  Parameter herein, damit die Tests sie einfrieren können.
- **Adresse** – Anschrift, Telefon, Anfahrt, Parken je Standort.

Warum: Alle drei haben genau eine richtige Antwort, die in den Daten steht. Ein Modell könnte
sie beantworten – aber eben auch danebenliegen, und dann steht jemand vor verschlossener Tür.
Die Suche ist der stärkste Fall: Wer „Hausarzt am Samstag" an ein Sprachmodell gibt, lässt
eine Datenbankabfrage würfeln.

Außerdem wird **vor** dem Modell abgefangen: Aufforderungen zu buchen oder zu reservieren.
Ein Sprachmodell tut sonst gern so, als hätte es gebucht.

Bewusst **nicht** deterministisch: Überweisungsregeln, Notdienst, Kosten, Behindertenstellplätze.
Die Antworten stehen im Fließtext oder an mehreren Stellen verschieden – Textverständnis ist
die Stärke des Modells, nicht der Regex.

## Woher ich weiß, dass es funktioniert

Zwei Ebenen, bewusst getrennt:

```bash
pytest                       # 27 Tests: die Bausteine einzeln, Zeit eingefroren
python pruefe_testfragen.py  # 20 Testfragen gegen den laufenden Dienst
```

`testfragen.json` enthält je Fall Frage, erwartete `quelle`, ein Stichwort und den Grund.
Geprüft wird die Quelle, nicht der Wortlaut. Das Skript gibt eine Zeile pro Fall aus und am
Ende die Summe; Exit-Code 0 nur, wenn alles OK ist. Drei Zustände:

- **OK** – Quelle und Stichwort stimmen
- **FALSCH** – Quelle oder Stichwort stimmen nicht
- **AUSFALL** – der Dienst hat `nicht_verfuegbar` geantwortet

Aktueller Stand: **11 OK, 0 FALSCH, 9 AUSFALL.** Die neun AUSFALL sind die Fälle, die das
Modell brauchen – vier, in denen es antworten soll, fünf, in denen es schweigen soll.

Schweige-Fälle, die schon jetzt funktionieren: fehlende Telefonnummer (MVZ Sonnenfeld),
Straße, die zu keinem Standort gehört (Humboldtstraße), fehlende Parkangabe (MVZ Lindenhof),
Buchungsaufforderungen.

## Was nicht funktioniert

- **Der Modell-Pfad ist nicht angebunden.** Alles, was ans Modell geht, kommt als
  `nicht_verfuegbar` zurück.
- Öffnungszeiten gelten je Standort, nicht je Fachrichtung. „Orthopädie am Samstag in Süd"
  bekommt die Zeiten des Hauses plus einen Hinweis darauf.
- Zwei Fachrichtungen in einer Frage: die erste gewinnt.
- „Wochenende" als Tag, Tippfehler in Standortnamen, Fragen in anderen Sprachen.
- Keine Rückfrage-Dialoge über mehrere Runden: „Welchen Standort meinen Sie?" ist das Ende.
- Keine Entfernungen („welcher Arzt ist in meiner Nähe?"), keine Termine, keine medizinische
  Beratung („zu welchem Arzt muss ich mit Knieschmerzen?") – nichts davon steht in den Daten,
  also wird nichts davon beantwortet.
- Die Erkennung ist großzügig: „Stadtpark" zählt als Parkfrage. Sie entscheidet nur den Pfad,
  nie die Antwort – die kommt aus den Daten.

## Wo ich aufgehört habe und warum

Fertig sind Datenmodell, deterministischer Kern, Endpunkt, Container und der Testlauf.
Nicht fertig ist die Anbindung des Sprachmodells (`anthropic` ist installiert, `llm.py`
existiert nicht). Vorgesehen: System-Prompt mit den Fließtexten und Standortdaten, harte
Regel „nur aus den Daten, sonst wörtlich: Das weiß ich nicht"; wörtliches „Das weiß ich nicht"
wird zu `unbekannt`, jede Ausnahme zu `nicht_verfuegbar`.

Die Reihenfolge war Absicht: Der deterministische Kern und der Testlauf kamen zuerst, weil
die Aufgabe genau darauf zielt – und weil der Testlauf ohne Modell zeigen muss, dass er einen
Ausfall von einem Schweigen unterscheiden kann. Das tut er.

## Daten

`data/standorte.json` – sechs erfundene Standorte in Nürnberg mit Adresse, Telefon,
Fachrichtungen, Öffnungszeiten je Wochentag, Erreichbarkeit und Parken; dazu drei Fließtexte
(Überweisungsregeln, Notdienst, Parken allgemein). Lücken sind Absicht: MVZ Sonnenfeld hat
keine Telefonnummer, Lindenhof und Sonnenfeld keine Parkangabe – das sind die Schweige-Fälle.
Keine Datenbank, kein RAG: sechs Standorte passen in ein Kontextfenster, ein Retrieval wäre
eine Fehlerquelle ohne Nutzen.

## Anmerkung zur Historie

Am 10.09.2026 wurde die Git-Historie einmalig umgeschrieben (`git filter-repo`), um
personenbezogene Daten zu entfernen: Vornamen in Code-Kommentaren, in der Testdatei und in
`CLAUDE.md` sowie Klarname und Mailadresse in der Autor-Zeile aller Commits. Inhalt,
Reihenfolge, Nachrichten und Zeitstempel der Commits sind unverändert – nur die Hashes sind
neu. Die Regel „Historie wird nie umgeschrieben" in `CLAUDE.md` hat genau diese eine
Ausnahme, und sie steht dort.
