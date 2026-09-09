# CLAUDE.md — Regeln für den Assistenten in diesem Repo

Projekt: MVZ-Auskunftsdienst, Praxisaufgabe. Der Bauplan (Roadmap) liegt bewusst
außerhalb des Repos; hier landet nur, was zum Dienst gehört.

## Arbeitsweise
- Deutsch, auch in Code-Kommentaren. Im Code ohne Umlaute, in Texten für Nutzer mit.
- Der Entwickler entscheidet, Claude erklärt. Jeder Vorschlag mit Begründung, nicht als fertige Wahrheit.
- Schreibt Claude Code, werden die Dateien vor dem Commit gemeinsam durchgegangen.
  Offene Stellen sind im Code mit `[PRÜFEN n]` markiert und vor dem Commit aufgelöst.
- Nichts über den Bauplan hinaus: kein Frontend, kein RAG, keine Datenbank,
  höchstens 8 Standorte, keine vierte Anfrageart.
- „Fertig" heißt: Datei geöffnet, Tests gelaufen, Ausgabe gesehen.
  Ein Dateiname in einer Commit-Nachricht ist keine Fertigmeldung.

## Git
- Der Entwickler committet. Claude schlägt die Commit-Nachricht vor.
- Die Historie wird nie umgeschrieben: kein rebase, kein amend, kein force-push.
- Nie einen API-Schlüssel committen. Vor jedem Push: `git ls-files` ansehen,
  `grep -ri "sk-ant" . --exclude=CLAUDE.md` muss leer bleiben (die Regel selbst enthält das Wort).

## Fehlerjournal
- Jede Stelle, an der der Assistent danebenlag, kommt sofort in `NOTIZEN.md`
  (nicht versioniert): Vorschlag · was falsch war · woran es aufgefallen ist.

## Technik
- Python 3.14, FastAPI, pytest. Tests: `pytest` im Projektordner.
- Zeitabhängiger Code nimmt `jetzt` als Parameter entgegen; Tests frieren die Zeit ein.
- Der Dienst muss ohne `.env` starten. Ohne Schlüssel laufen die deterministischen
  Pfade weiter, der Modell-Pfad meldet sich sauber ab.
