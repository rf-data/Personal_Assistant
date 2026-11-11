# C18, SQLite und ENOSPC: abgegrenzter Befund

Die erste breite Btrfs-Prüfung bleibt **356 bestanden / ein Quarantänefehler**.
Der Resumejob endete `interrupted` mit `OperationalError`; SQLitecode und
ursprüngliche Fehlerstelle wurden damals nicht gespeichert. Die Datenbank war
bei lesendem `quick_check` intakt. Diese Information identifiziert weder BUSY
noch FULL und lässt sich aus einem späteren erfolgreichen Lauf nicht ergänzen.

Spätere Diagnoseversuche belegen unabhängig **errno 28 bei `os.replace`** der
Adapter-State-Publikation, nicht bei `fsync`. Kleine Dateischreib-/Fsyncproben
bestanden, atomarer Ersatz auf Btrfs scheiterte. Auch `/tmp` ist dort Btrfs und
war kein vollständiger Ausweg. Alle alten Versuche bleiben in den Belegen.

## Neue Prüfung auf einem anderen lokalen Dateisystem

Neue, private Roots unter `/dev/shm/c26-runtime-test.S6wlBM/`; **tmpfs**, keine
Wiederverwendung oder Verschiebung alter C18-Roots. Isolierte Testumgebung auf
dem Entwicklungsrechner, kein Hetzner-/Produktionsroot und kein ext4-Beleg.

| Lauf | Ergebnis | Bindung |
| --- | --- | --- |
| Parser-/Config-Resume und Metadatenmanipulation | 3 bestanden | Bisher betroffene Fälle, Produktcode unverändert |
| C18 + SQLite + Executor + Runtime/Transport | 54 bestanden | Eigenes frisches Testverzeichnis; Resume, Cancellation, harter Neustart und Quarantäne eingeschlossen |
| Breite Kombination #155 + #156/#149/#148 + #157-Tests | 386 bestanden, 6 optionale Fälle übersprungen, 1 Docker-CLI-Fall abgewählt | Eigene neue Roots; Label-Listen-Kandidat, vor letzter Bindvariablenkorrektur |
| Finale Definitions-/Verweigerungstests | 6 bestanden | Beide endgültigen Composekorrekturen |
| Echte lokale HTML-Exporte | 5 bestanden | Fünf übersprungene Exportfälle gezielt nachgeholt; Originalbytes unverändert |
| UI-Main + #20 | 24 Tests + 9 Subtests bestanden | Eigener Test-TMPDIR; keine zusätzliche UI-Instanz |

Die Läufe überlappen; ihre Zahlen nicht als unabhängige Tests zusammenzählen.
Der breite Lauf umfasst zusätzliche Knowledge-Tests gegenüber dem alten
357er-Schnitt. Die sechs Skipfälle betreffen fünf explizit einzubindende lokale
HTML-Exportvergleiche und einen fehlenden importierten Originaltranscript-Stand.
Die fünf HTML-Fälle wurden separat mit dem bereits freigegebenen Exportpfad
erfolgreich nachgeholt; keine zusätzlichen Pakete, APIs oder Downloads dafür. JUnit-Gruppen, Skipgründe,
Hashes und konkrete Pfade stehen in `validation.v1.json`.

Die fünf deterministischen #156-SQLitefälle bestehen: echtes Setup-
`SQLITE_BUSY=5`, einmaliger Transaktionseintritt, keine Wiederholung des Bodys,
weiter verweigerter persistenter Lock und kein Retry für `SQLITE_ERROR=1`.
Das setzt den alten unklassifizierten Fehler nicht mit diesem BUSY-Fall gleich.

## Dateisystem, Journale, Cleanup und Unsicherheit

Lesende Btrfs-Zähler zum Diagnosezeitpunkt: Metadata `total_bytes=811597824`,
`bytes_used=719388672`, `bytes_may_use=85000192`, reserved/pinned jeweils 0.
Rechnerisch verbleiben **7208960 Bytes (6,875 MiB)** nach diesen Reservierungen,
obwohl `df` mehrere GiB freie Datenblöcke meldet. Das passt zu Metadatendruck,
beweist aber den genauen Kernel-/Quota-/Allokationsgrund nicht abschließend.
`df -i` mit 0/0 auf Btrfs ist kein Beleg für erschöpfte Inodes.

Die neuen Testroots enthalten insgesamt circa 21,5 MB logische Dateien und
214 synthetische SQLite-Datenbanken. Acht lesende Integritätsstichproben ergeben
`ok`. Quarantänemarker in absichtlich fehlerhaften Fixtures bleiben bestehen;
keine Locks/Marker zur Freigabe gelöscht. WAL-/Lock-/Restartprüfungen und
Fail-Closed-Verträge wurden nicht verändert. Jede Laufserie hat einen neuen Root.

**Bewertung:** Der Fehler ist auf tmpfs mit unverändertem Produktcode über die
gezielten und breiten Fälle nicht reproduziert. Lokaler Dateisystemdruck ist
stark eingegrenzt; kein bewiesener Anwendungsfix, keine reparierte Btrfs-Umgebung
und keine rückwirkende SQLitecode-Erklärung. Deshalb keine neue Retrylogik,
Quarantänelockerung, Balance, Bereinigung oder Limitänderung.

Vor produktiver Freigabe tatsächlichen Worker-Mount, vorhandenen Root, Reserve
und Grenzen belegen. Eine Rename/Fsync/flock/WAL- und C18-Abnahme auf dem echten
Zieldateisystem benötigt ein separat erlaubtes isoliertes Testziel und die
geprüfte gebaute Version. Im aktuellen Auftrag kein Schreiben auf Hetzner.
