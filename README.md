# FaceVeil

Eine eigenständige lokale Python-Desktop-App für Kamera-Gesichtsfilter.
Version 0.1 ist ein Entwicklungsprototyp, keine zertifizierte Anonymisierung.

## Start auf Windows

Python 3.11 ist die getestete Version. Im Projektordner:

```powershell
.\setup.ps1
.\start.ps1
```

Falls PowerShell Skripte sperrt, dieselben Schritte ohne Änderung der Sicherheitsrichtlinie:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m faceveil
```

Die virtuelle Umgebung `.venv` enthält ausschließlich die Pakete dieses Projekts.
Sie wird nicht in Git gespeichert. `pip install -e .` verbindet die Installation
mit dem Quellcode: Änderungen sind beim nächsten Start direkt verfügbar.
VS Code: Projektordner öffnen und `.venv\Scripts\python.exe` als Interpreter wählen.

## Benutzung

1. Unter **Quelle** entweder **Kamera** oder **Videodatei** wählen.
   Unter **Kamera** erscheint die Liste angeschlossener Geräte mit Namen,
   einschließlich verfügbarer virtueller Kameras. Bei Bedarf **Kameraliste
   aktualisieren** drücken. Die Liste aktualisiert sich auch bei Geräteänderungen.
   Bei **Videodatei** erscheinen stattdessen Dateiauswahl und Dateiname.
2. **Vorschau starten**. Die Kamera wird erst jetzt geöffnet.
3. Standardmäßig ist das gesamte Bild schwarz abgedeckt. Zum Ausprobieren der
   Gesichtseffekte **Gesamtes Bild schwarz abdecken** deaktivieren.
4. Pixelation, Blur, Mosaic oder Abdecken wählen; Stärke und Gesichtsrand anpassen.
   Bei Abdecken ist die Stärke ohne Bedeutung. Spiegelung betrifft die Vorschau.
5. Ein Quellen- oder Kamerawechsel stoppt die laufende Vorschau automatisch.
   Danach **Vorschau starten** drücken. Dateiende stoppt die Vorschau ebenfalls.

Pixelation erzeugt grobe Farbblöcke, Blur einen Gauß-Weichzeichner, Mosaic ein
sichtbares Kachelraster, Abdecken schwarze Rechtecke über erkannten Gesichtern.
Die vollständige Bildabdeckung arbeitet unabhängig vom Detektor.

## Grenzen der Gesichtserkennung

Das mit OpenCV gelieferte Haar-Modell erkennt vor allem frontale Gesichter.
Profile, Verdeckung, schlechte Beleuchtung, Bewegung und kleine Gesichter können
zu übersehenen Gesichtern führen. Auch wenn ein Gesicht erkannt wird, können
weitere Gesichter im selben Bild unentdeckt bleiben. Es gibt noch kein Tracking.
Pixelation und Blur sind visuelle Effekte und garantieren keine Unkenntlichkeit.
Nur die vollständige schwarze Bildabdeckung entfernt in dieser Vorschau sämtliche
Bildinformation. Das Originalvideo auf der Festplatte bleibt unverändert.

Die App speichert keine Bilder und enthält keine Upload-, Netzwerkstream- oder
Telemetriefunktion. Kamera-/Videodaten werden lokal verarbeitet. Keine virtuelle
Kamera, Bildschirmaufnahme, Audioverarbeitung oder Exportfunktion in Version 0.1.

## Projektaufbau

```text
src/faceveil/
  app.py         Desktop-UI und Prozesssteuerung
  capture.py     Quellenvalidierung und Verarbeitungsschleife
  detection.py   austauschbare Gesichtserkennung
  devices.py     Gerätenamen, Gerätekennungen und Qt-Kamerazugriff
  filters.py     Einstellungen und Bildfilter ohne UI-Abhängigkeit
tests/           Filter-, Video- und UI-Tests ohne echte Kamera
.github/         CI, Issue-Formulare und Pull-Request-Vorlage
docs/            Architektur, Lernpfad und geplante Arbeitspakete
```

Warum diese Trennung? Filter lassen sich mit künstlichen Bildern testen.
Eine spätere bessere Gesichtserkennung ersetzt `detection.py`, ohne die UI neu
zu schreiben. Ein Kindprozess hält blockierende Kameratreiber von der UI fern.
Die Vorschau empfängt ausschließlich verarbeitete Bilder, keine Rohbilder.

## Qualität prüfen

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
```

Ruff findet typische Codefehler und vereinheitlicht die Formatierung.
Pytest prüft Verhalten; pytest-qt testet die Oberfläche ohne eine echte Kamera.
Die GitHub-Action führt diese Prüfungen bei Pull Requests und Änderungen auf
`main` auf Windows mit Python 3.11 aus. `requirements-dev.lock` hält die lokal
geprüften Paketversionen fest; es enthält keine Hash-Prüfung der Downloads.

## Zusammenarbeit

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Issue → Branch → Commit → PR → Merge.
Der initiale Aufbau wird in nachvollziehbaren Commits festgehalten; nachfolgende
Änderungen erhalten jeweils ein Issue. Nächste Arbeitspakete stehen im
[Backlog](docs/BACKLOG.md), die technischen Entscheidungen in der
[Architektur](docs/ARCHITECTURE.md).

## Herkunft und Sichtbarkeit

Inspiriert vom allgemeinen Konzept lokaler visueller Filter, unter anderem
[Beta Blocker](https://isla2d.itch.io/beta-blocker). Kein Code, Designmaterial oder
Asset dieses Produkts wurde übernommen. FaceVeil ist nicht damit verbunden.

Das GitHub-Repository muss **privat** sein. Dieser Projektcode wird aktuell nicht
unter einer Open-Source-Lizenz freigegeben. Drittanbieterpakete und das
OpenCV-Modell behalten ihre jeweiligen Lizenzen; siehe
[THIRD_PARTY.md](THIRD_PARTY.md).
