# Architekturentscheidungen

## 001 · Python, PySide6 und OpenCV

PySide6 liefert native Desktop-Widgets und Kamerazugriff, OpenCV Dateizugriff und
Bildoperationen. Python 3.11 ist die lokal verfügbare, getestete Basis.
Eine Weboberfläche würde zusätzliche Browser-/Server-Komponenten benötigen.
Dokumentation: https://doc.qt.io/qtforpython-6/gettingstarted.html
und https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html.

## 002 · Verarbeitung in einem eigenen Prozess

UI → Einstellungen/Stoppsignal → Capture-Prozess → begrenzte Frame-Queue → UI.
Der Prozess besitzt die Quelle und den Detektor. Er liest, erkennt, filtert und
spiegelt; erst danach wird ein Bild weitergegeben. Maximal zwei Bilder warten
auf die UI. Bei Überlast werden Bilder verworfen. Die maximale Verarbeitungsbreite
ist 1280 Pixel; Videodateien werden gemäß FPS gedrosselt, ohne Audio.
Bei teuren Filtern kann die Wiedergabe langsamer als Echtzeit sein.

Ein Prozess kostet mehr Startzeit und Speicher als ein Thread, kann aber bei
einem hängenden nativen Kameratreiber beendet werden. Stop setzt zuerst das
Stoppsignal und wartet kurz; danach wird der Prozess bei Bedarf terminiert.
Nach acht Sekunden ohne aktuelles Bild beendet die UI die Vorschau.

Jede Einstellungsänderung erhält eine Generationsnummer. Die UI leert sofort das
Bild und akzeptiert nur Frames der neuesten Generation. Alte Bilder können so
nach Aktivierung der vollständigen Abdeckung nicht wieder eingeblendet werden.
Die Befehlsqueue ist ebenfalls begrenzt; bei Überlauf stoppt die Vorschau.

## 003 · Austauschbares Basismodell

OpenCVs eingebautes Haar-Modell vermeidet zusätzliche Modell-Downloads.
Es eignet sich als überprüfbare Ausgangsbasis, nicht als zuverlässige
Anonymisierung. Später folgt ein evaluierter Detektor mit Profilen und Tracking.
Auch dann sind Fehlerraten zu messen. Ein Fehler im Detektor liefert keine
ungefilterte Vorschau; die Verarbeitung stoppt.

## 004 · Keine Medienpersistenz

Keine Aufnahme, Uploads oder Screenshots von Nutzerbildern. Die Tests erzeugen
synthetische Frames und temporäre Videos. Ein späterer Export benötigt eigene
Anforderungen, insbesondere für Ausfälle und versehentlich sichtbare Gesichter.

## 005 · Reproduzierbare Entwicklung

`src`-Layout verhindert versehentliche Imports aus dem Arbeitsordner.
`pyproject.toml` beschreibt Paket und Werkzeugkonfiguration. Der Versions-Snapshot
in `requirements-dev.lock` hält direkte und transitive Entwicklungsdependencies
fest. Aktualisierungen erfolgen in separaten PRs mit Tests.

## 006 · Kamera anhand der Gerätekennung auswählen

QMediaDevices liefert Gerätenamen und IDs; QCamera öffnet im Kindprozess exakt
die gewählte ID. Die Reihenfolge einer OpenCV-Geräteliste wird nicht vorausgesetzt.
QVideoSink liefert Frames, die vor der Filterung in BGR konvertiert werden.
Die UI behält die Auswahl anhand der ID auch bei einer umsortierten Liste.
Fehlt die aktive Kamera nach einer Geräteänderung, stoppt die Vorschau.
Eine Kamera wird erst nach dem Start geöffnet, nicht beim Auflisten.
Quelle und Kamera können während der Vorschau geändert werden; der Wechsel
stoppt zunächst die alte Quelle. Qt-Geräteüberwachung und ein Aktualisieren-Knopf
ermöglichen neu angeschlossene Kameras. Hardware-Abnahme weiterhin erforderlich.

Referenz: https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaDevices.html
