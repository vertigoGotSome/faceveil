# Prüfprotokoll · 10. September 2026

## Lokal ausgeführt

- Windows, Python 3.11.0, isolierte `.venv`.
- Dependencies installiert; exakte Versionen in `requirements-dev.lock`.
- `pip check`: keine Konflikte.
- `ruff check .`: erfolgreich.
- `ruff format --check .`: erfolgreich.
- `pytest -q`: 32 Tests erfolgreich.
- Qt-Oberfläche ohne Bildschirmzugriff gerendert und visuell geprüft.
  Für dieses Offscreen-Rendering wurde die lokale Segoe-UI-Schrift explizit geladen.

Abgedeckt: Filtergrenzen, unveränderte Eingabebilder, Randbereiche, winzige
Gesichter, vollständige Abdeckung ohne Erkennung, ungültige Quellen,
Queue-Begrenzung, Videodecodierung und Dateiende, Fehler im Detektor mit
Quellenfreigabe, Standardzustand der UI, veraltete Frames nach Einstellungswechsel
sowie Video-Start/Stop/Neustart in einem echten Kindprozess.

## Noch nicht abgenommen

- Echte Webcam und Kameratreiber des Nutzers, Gerätewechsel und Abziehen.
- Qualität der Gesichtserkennung mit realen Gesichtern.
- Andere Betriebssysteme oder andere Python-Versionen.
- GitHub-CI, solange das private Remote-Repository nicht verbunden ist.
- Gepackte Windows-Anwendung und virtuelle Kamera (noch nicht implementiert).

## GitHub-Status

Connector-Zugriff auf das Konto `vertigoGotSome` wurde bestätigt. Die verfügbaren
Connector-Aktionen enthalten keine Repository-Erstellung. GitHub CLI ist nicht
installiert; im geprüften Browser war keine Anmeldung vorhanden.

Deshalb bisher nur lokales Git-Repository; kein öffentliches Repository erstellt,
kein Remote-Push durchgeführt. Issue-Formulare, PR-Vorlage, CI-Konfiguration und
Backlog sind vorbereitet. Live-Issues und Branchschutz sind noch nicht angelegt.
Fortsetzung nach Anmeldung oder Bereitstellung eines leeren privaten Repository-Links.

## Nachtrag · Auswahl verbundener Kameras

39 Tests erfolgreich, Ruff-Lint und Formatprüfung erfolgreich. Ergänzt wurden
Gerätenamen, Beibehalten der ausgewählten Gerätekennung nach Umsortierung,
leere Liste und nachträglich gefundene Kamera, Quellenabhängigkeit der sichtbaren
Bedienelemente, Auswahlauflösung anhand der ID und Qt-Bildkonvertierung.
Der Test mit echtem Video-Kindprozess stoppt jetzt durch Wechsel der Quelle.
Der Fehlertest prüft zusätzlich die Übergabe der gewählten Kamera an den Adapter.

Die Geräteabfrage in der eingeschränkten Ausführungsumgebung lieferte keine
Kameras. Deshalb wurde kein tatsächlicher Kamerastream für diesen Nachtrag
abgenommen; Gerätenamen und Zuordnung sind mit simulierten Geräten geprüft.
