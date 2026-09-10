# Start-Backlog für GitHub-Issues

## 1. Kameras mit Gerätenamen auswählen

Ziel: Kameraauswahl ohne Raten des Index.

- [x] Geräte mit Namen auflisten und über dieselbe Qt-Gerätekennung öffnen.
- [x] Liste bei Geräteänderungen und per Aktualisieren-Knopf erneuern, ohne Kameras zu öffnen.
- [x] Leere Geräteliste und Auswahl nach Umsortieren behandeln.
- [ ] Belegte Kamera und Hotplug mit echter Hardware abnehmen.
- [ ] Auswahl öffnet nachweislich die angezeigte Kamera.

## 2. Gesichtserkennung evaluieren und verbessern

- [ ] Front, Profil, mehrere Personen, Bewegung und schlechte Beleuchtung testen.
- [ ] Nur freigegebene Testbilder verwenden und deren Herkunft dokumentieren.
- [ ] Fehlerrate und Laufzeit mit Basismodell vergleichen.
- [ ] Tracking und Abdeckung bei Erkennungsverlust definieren.
- [ ] Modelllizenz und Download-/Offlineverhalten dokumentieren.

## 3. Hardware-Abnahme unter Windows

- [ ] Echte Kamera starten, stoppen und erneut öffnen.
- [ ] Zweite Kamera und Videoquelle abwechselnd auswählen.
- [ ] Alle vier Filter, Spiegelung und vollständige Abdeckung prüfen.
- [ ] Kamera abziehen, Berechtigung verweigern und App schließen.
- [ ] Ergebnisse mit Windows-Version und Kameramodell dokumentieren.

## 4. Virtuelle Kamera für OBS planen

- [ ] Gewünschte Zielanwendungen und Treiberanforderungen erfassen.
- [ ] Bei Fehlern nur schwarze Ersatzbilder ausgeben.
- [ ] Keine ungefilterten Bilder beim Start oder Quellenwechsel.
- [ ] Installation und Deinstallation nachvollziehbar gestalten.

## 5. Windows-Paket erstellen

- [ ] Sauberes Windows-System ohne Python als Testumgebung.
- [ ] Qt-Plattformplugin und Haar-Modell mitliefern.
- [ ] Drittanbieterlizenzen im Paket prüfen und beilegen.
- [ ] Start, Fehlerfälle und Prozessende des gepackten Programms testen.
