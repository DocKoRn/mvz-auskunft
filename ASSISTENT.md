# Wo der Assistent danebenlag – und woran ich es gemerkt habe

Gebaut mit Claude Code. Die Regeln dafür stehen in `CLAUDE.md`. Jede Stelle, an der der
Assistent danebenlag, habe ich sofort in ein Journal geschrieben – nicht am Ende aus dem
Gedächtnis. Das hier ist die Auswahl daraus, chronologisch.

**Ein Skript hätte die Datendatei zerstört.** Der Assistent wollte zwei Fließtexte per
Skript an `standorte.json` anhängen und nahm an, die Datei ende auf `}` ohne Zeilenumbruch.
Sie endete mit Zeilenumbruch; das Muster hätte nicht gepasst, die JSON wäre kaputt gewesen.
Gemerkt hat es nicht ich, sondern eine `assert`-Zeile, die ich vorher verlangt hatte: Sie
prüfte die Annahme und brach ab, bevor geschrieben wurde. Erst `od -c` zeigte das fehlende `\n`.

**Die Regeldatei war leer.** Ein Commit hieß „CLAUDE.md anlegen", und der Assistent führte die
Datei danach als vorhandene Regeldatei. Sie hatte null Bytes – so auch committet. Aufgefallen
beim Zeitabgleich am nächsten Tag: `ls -la` zeigte die 0, `git show` bestätigte, dass die
Leere in der Historie liegt. Ein Dateiname in einer Commit-Nachricht ist keine Fertigmeldung.

**„Zur Alten Ziegelei" war kein Standort.** Die Standorterkennung verglich den Namen wörtlich:
Alias `alte ziegelei`. Dekliniert – „zur *Alten* Ziegelei" – passte nichts. Der vorhandene Test
mit genau dieser Formulierung war trotzdem grün, weil in der Frage „Überweisung" stand und die
Erkennung vorher ans Modell abbog: Der Test prüfte die Vorfahrtsregel, nicht den Standort.
Gemerkt an einem neuen Test beim Umbau der Parkfunktion, der rot war.

**Ein Ausfall sah aus wie ein Schweigen.** Der Bauplan des Assistenten sah vor: kein Schlüssel,
API nicht erreichbar → Antwort mit `quelle: "unbekannt"` – derselbe Wert wie bei einer bewussten
Rückfrage oder einer fehlenden Telefonnummer. Ein Schweige-Testfall wäre damit grün gewesen,
obwohl kein Modell läuft. Gemerkt beim Durchdenken der drei Ausgänge des deterministischen
Pfads: Ich habe gefragt, was am „nicht mein Fall" hängt, wenn die API ausfällt, und die
Antwort wäre dieselbe gewesen wie beim gewollten Schweigen. Seitdem gibt es `nicht_verfuegbar`.

**Die Suche antwortete auf eine Bewertungsfrage.** „Welcher Hausarzt hat die besten
Bewertungen?" enthält Hausarzt und „welcher" – und bekam eine selbstbewusste Standortliste mit
`quelle: daten`. Bewertungen gibt es in den Daten nicht. Gemerkt an eigenen Testfragen, die
nicht aus dem Bauplan stammten, sondern so formuliert waren, wie Patienten fragen; zwei von
fünf liefen falsch (die zweite: „Buche mir einen Termin" ging ans Modell). Die Erkennung sagt
nur, welcher Pfad – nie, ob die Frage beantwortbar ist.

**Das Fehlerjournal lag im Docker-Image.** Beim Anhängen an `.dockerignore` fehlte der
Zeilenumbruch am Dateiende; aus `NOTIZEN.md` und `tests/` wurde eine Zeile, die auf nichts
passte. Derselbe Fehler wie beim ersten Punkt, diesmal ohne `assert`. Gemerkt an einem `ls` im
laufenden Container, das ich als Kontrolle mitlaufen ließ – der Testlauf davor war grün.
Ein grüner Lauf sagt nichts über das, was nicht geprüft wurde.

**Namen im öffentlichen Repo.** Der Assistent schrieb Vornamen in Code-Kommentare, in die
Testdatei und in `CLAUDE.md`, als wäre das Repo ein Notizbuch. Gemerkt, weil ich vor der Abgabe
eine Prüfung auf personenbezogene Daten angeordnet habe – drei Durchgänge, auch über die
Historie. Es gab eine Prüfung auf API-Schlüssel vor jedem Push; eine auf Namen gab es nicht,
und beide sind dieselbe Sorte. Die Historie habe ich deshalb einmal umgeschrieben; was und
warum, steht in der README.

**Was ich daraus mitnehme:** Der Assistent liefert richtige Werte und falsche Deutungen – ein
Dateiname, ein grüner Test, ein Rückgabewert, der zwei Bedeutungen hat. Gefunden habe ich die
Fehler nie durch Lesen, sondern durch Prüfen: eine Zusicherung im Skript, ein `ls` im Container,
eine Frage, die nicht im Plan stand. Was ich nicht selbst erklären kann, habe ich nicht gebaut.
