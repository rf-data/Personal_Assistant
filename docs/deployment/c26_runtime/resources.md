# Ressourcenbudget mit dem Betreiberbefund vom 23.10.2026

**operator_observed**, keine neue Codex-Hostmessung: RAM 3,7 GiB,
MemAvailable ungefähr 2,2 GiB; Swap 4 GiB, davon etwa 688 MiB benutzt, aktuell
kein erheblicher Swap-in/-out. Ext4 `/dev/sda1`, 38 GiB gesamt, etwa 20 GiB frei,
91 % Inodes frei; vorhandene Daten etwa 755 MB. Kein Lasttest. Diese Angaben
ersetzen das frühere pauschale 4-GiB-Szenario.

| Rolle | RAM-Obergrenze | CPU-Obergrenze | Tmpfs innerhalb der Cgroup |
| --- | ---: | ---: | ---: |
| API | 256 MiB | 0,25 | 64 MiB |
| Interner Caddy | 256 MiB | 0,25 | 64 MiB |
| Genau ein Kapazitätsworker | 1.024 MiB | 1,00 | 128 MiB |
| Bestehende UI, konservative Repositorygrenze | 768 MiB | 1,00 | 64 MiB |
| Summe | **2.304 MiB** | **2,50** | **320 MiB, nicht nochmals addieren** |

Keine bestehenden Limits verändert. Prozess-RLIMIT_AS 768 MiB ist kein gemessener
Gesamtverbrauch des Workers. CPUanzahl und effektive UI-/Hostgrenzen noch prüfen.

3,7 GiB entsprechen ungefähr 3.789 MiB. Nach 2.304 MiB Rollenobergrenzen bleiben
1.485 MiB. Mit je 512 MiB OS-/Notfallreserve bleiben **461 MiB für Coolify,
Traefik, Datenbank/Redis und alle weiteren Dienste**. Die frühere zusätzliche
Restdienste-Planannahme von 1.024 MiB ergäbe 4.352 MiB Gesamtbedarf, also etwa
**563 MiB Fehlbetrag**. Das ist eine Planannahme, kein gemessener RAMmangel.

Bei aktuell 2,2 GiB MemAvailable und zusätzlich höchstens 1.536 MiB für die drei
neuen Rollen bleiben rechnerisch **717 MiB**, nach 512 MiB Notfallreserve nur
**205 MiB** für weitere Peaks. Die schon laufende UI ist in diesem zweiten
Ansatz bereits Teil der Hostbasis und wird nicht doppelt abgezogen. Beide
Rechnungen sind Näherungen, kein bewiesener Worst-Case-Fit. Belegter Swapgebrauch
ist keine zusätzliche RAMreserve; unveränderter Swapverkehr beweist keinen
Lastfit. Vor Start aktuelle Host-/Containerwerte und Buildspitzen messen.

Der Builder läuft auf dem Deploymentserver. Builds und Jobs dürfen nicht parallel
laufen; Buildfenster oder anderer Builder brauchen eigene Freigabe. CPUquoten
sind Obergrenzen, keine reservierten freien CPUs. Kein Limit spontan absenken.

## Ein-Material-Diskbudget

Bestätigte Limits nun tatsächlich als Ausgangswerte verwendet: Reserve 5 GiB,
Archiv 64 MiB, Katalog 128 MiB, Jobroot 512 MiB, Report 16 MiB, max_materials 1.
Konservativ vollständige Obergrenzen addiert: **5,703125 GiB** frei erforderlich.
Bei gemeldeten 20 GiB wären etwa **14,30 GiB** für Image-Staging, Backups und
sonstiges Wachstum übrig; dafür liegen keine vollständigen Größen vor. Für
reines Batchbudget rechnerisch **0 GiB zusätzlicher Platz**, Gesamtbedarf erst
`max(0, 5,703125 GiB + zusätzliche Images + zusätzliche Backups + Wachstum -
frischer freier Platz)` nachmessen. Vorhandene 755 MB sind bei `df` bereits
belegt und werden nicht erneut als freier Zusatzbedarf gezählt.

| Scope | Befund / Grenze |
| --- | --- |
| Lokale Entwicklung | Btrfs `/dev/vdc`, am neuen Auftragseingang ca. 3,5 GiB frei, df-Inodes 0/0 ohne Aussage über Inodemangel; historische errno28 bei `os.replace`, Metadatendruck plausibel |
| Isolierte Tests | Neues eigenes `/dev/shm`-tmpfs, synthetische Daten; kein dauerhafter Hostroot und kein Btrfsfix |
| Hetznerhost | Obiger gemeldeter ext4-/RAM-/Swapbestand; kein Codexzugriff |
| Neuer Workerroot | Vorgeschlagener eigener Bind `/srv/personal-assistant/runtime/c26-v1` → `/app/runtime-state`, noch nicht vorhanden oder genehmigt nachgewiesen |

Daher **GO für kleinen Budgetvorschlag/Review, NO-GO für Rollenstart ohne frischen
Mount-/RAM-/Backup-/Imagebeleg**. Kein Cleanup, Resize, Datenverschieben,
Paketnachladen oder neue Kurs-/ZIPbeschaffung.
