# Entwicklungsablauf

## Vom Wunsch zur überprüften Änderung

1. Ein GitHub-Issue beschreibt **ein Ziel**, den Nutzen und Akzeptanzkriterien.
   Beispiel: „Kameranamen anzeigen“ mit „Liste aktualisierbar“ und „kein Einfrieren“.
2. Vom aktuellen `main` einen Branch erstellen:
   `git switch -c feat/12-camera-discovery`.
3. Kleine zusammengehörige Änderungen entwickeln und sinnvoll testen.
4. Vor dem Commit `git diff` und `git status` prüfen. Keine Aufnahmen, Zugangsdaten
   oder `.venv` committen.
5. Aussagekräftiger Commit: `feat(capture): add camera discovery`.
6. Branch pushen und Pull Request nach `main` öffnen. In die Beschreibung gehört
   `Closes #12`, damit GitHub das Issue beim Merge schließt.
7. CI abwarten und Diff prüfen. Für Solo-Arbeit denselben Review-Ablauf verwenden.
8. Per Squash Merge abschließen, lokalen `main` aktualisieren.

## Konventionen

Branches: `feat/<issue>-<kurzname>`, `fix/<issue>-<kurzname>`,
`docs/<issue>-<kurzname>`, `chore/<issue>-<kurzname>`.

Commits: `<typ>(<bereich>): <kurze englische Beschreibung>`.
Typen: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
Variablen und Funktionen in Englisch mit aussagekräftigen Namen; UI und
Lerndokumentation in Deutsch. Kleine Funktionen und klare Modulgrenzen bevorzugen.

## Definition of Done

- Akzeptanzkriterien erfüllt und relevante Fehlerfälle berücksichtigt.
- Tests, Lint und Formatprüfung erfolgreich.
- Anleitung bei verändertem Verhalten angepasst.
- Bei Kameraänderungen: Start/Stop/Neustart, fehlende Kamera, Dateiende und
  Quellenwechsel geprüft; Hardwaretests im PR ausdrücklich dokumentiert.
- Keine unüberprüften Anonymitätsversprechen.

## GitHub-Einrichtung

Privates Repository ohne automatisch erzeugte README anlegen, dann lokalen
Verlauf mit `main` verbinden. GitHub-Issues aktivieren. Optional ein Projektboard
mit Backlog, Ready, In Progress, Review und Done anlegen.
Empfohlene Labels: `bug`, `enhancement`, `documentation`, `privacy`, `testing`.
Für `main` Pull Requests und erfolgreichen Statuscheck `quality` verlangen,
soweit der GitHub-Tarif Regeln für private Repositories unterstützt.
Branchschutz gilt erst als eingerichtet, wenn er in GitHub tatsächlich geprüft wurde.

## Lernpfad

Zuerst einen Filtertest lesen und ausführen. Anschließend ein kleines Issue aus
dem Backlog wählen. Einen Branch erstellen, genau eine Änderung implementieren,
lokal testen und einen Pull Request eröffnen. Im Diff erklären können, warum
jede geänderte Datei nötig ist. So bleiben Entscheidungen nachvollziehbar.
