# RAM, CPU und Speicher: konservatives Budget

Alle Rollengrenzen bleiben unverändert. Keine Erhöhung oder Absenkung bestehender
Limits und keine Annahme zweier paralleler Materialjobs. Die Beispielconfig hat
`max_parallel=1`, `max_queued=1` und deaktivierte Execution; vorhandene externe
Writer müssen zusätzlich ausgeschlossen werden.

| Vorgesehene Rolle | RAM-Obergrenze | CPU-Obergrenze | Tmpfs |
| --- | ---: | ---: | ---: |
| API | 256 MiB | 0,25 | 64 MiB |
| Interner Caddy | 256 MiB | 0,25 | 64 MiB |
| Ein C26-Kapazitätsworker | 1.024 MiB | 1,00 | 128 MiB |
| Eine bestehende Streamlit-UI | 768 MiB | konservativ 1,00 | 64 MiB |
| Summe | **2.304 MiB** | **2,50** | **320 MiB** |

UI: 1 CPU aus der gezeigten Repository-Grunddatei; die frühere geschützte C26-
UI-Vorlage schlägt 0,75 vor. Für diese Rechnung gilt der höhere Wert; die real
wirksame UI-Grenze ist noch zuzuordnen. Tmpfs-Verbrauch zählt innerhalb der
jeweiligen RAM-Cgroup, nicht nochmals 320 MiB addieren. Andere Betriebssystem-
und Docker-/Kernelkosten bleiben zusätzlich. Prozess-RLIMIT_AS (768 MiB im
bestehenden Workflowvertrag) ist keine gesamte Worker-Cgroupmessung.

## 4-GiB-Szenario, keine gemessene Produktionsbelegung

4.096 MiB minus 2.304 MiB Rollen = **1.792 MiB** für alles andere. Konservativ
512 MiB für OS/Kernel und 512 MiB Notfallreserve vorsehen: Dann bleiben
**768 MiB** für Coolify, dessen Datenbank/Redis/Systemdienste, Traefik und sämtliche
weiteren Container zusammen. Diese Restdienste wurden nicht live gemessen.

Mit einer ausdrücklich als Planannahme angesetzten 1.024-MiB-Summe für diese
Restdienste wären 4.352 MiB erforderlich, also **256 MiB mehr als 4 GiB**.
Das ist ein konservatives Szenario, kein gemessener tatsächlicher Fehlbetrag und
keine automatische Upgradeforderung. Vollständiger Worst-Case-Fit ist aktuell
**nicht nachgewiesen**. Benötigt werden tatsächlicher Host-RAM, verfügbare Reserve,
wirksame Limits und Spitzen der vorhandenen Dienste; auch Docker-Cgroups allein
erfassen nicht alle Hostkosten. Kein spontanes Absenken des Workers als Lösung.

CPUanzahl fehlt. Bei zwei logischen CPUs übersteigen allein die Rollengrenzen
die Kapazität um 0,5 CPU, zusätzlich zur Infrastruktur. Quotas sind Obergrenzen,
keine zugesicherten Reservierungen; daraus folgt kein bewiesener Ausfall, aber
auch keine ausreichende Latenz-/Drain-/Healthreserve. Bei einer anderen CPUzahl
neu rechnen. Ein einzelner Worker garantiert noch keine freie CPU für Coolify.

Der bestätigte Backendbuilder läuft auf dem Deploymentserver. Imagebuildspitzen
sind in diesem Laufzeitbudget **nicht enthalten**. Kein paralleler Build während
eines Materialjobs; später separat freigegebenes Buildfenster/anderer Builder
oder ausreichende gemessene Reserve. Dies ändert jetzt keine Coolifyeinstellung.

## Drei Dateisysteme ausdrücklich auseinanderhalten

| Scope | Tatsächlicher Nachweis | Bedeutung |
| --- | --- | --- |
| Lokale Entwicklung | Btrfs `/dev/vdc`, circa 3,4 GiB frei, `df -i` meldet 0/0; `os.replace` zuvor mit errno 28 fehlgeschlagen | Nicht als Hetznerkapazität verwenden; Metadaten können trotz freier Datenblöcke knapp sein |
| Neue isolierte Testroots | Lokales `tmpfs` `/dev/shm`, vor dem Lauf circa 3,3 GiB Kapazität, kleine synthetische Dateien | Anderes Testdateisystem, kein persistenter Produktionspfad und kein dauerhafter Ersatz für Btrfs |
| Hetznerhost | Betreiberbefund ext4, 38 GiB gesamt, circa 20 GiB frei, circa 91 % Inodes frei | Keine neue Codex-Hostmessung; vor tatsächlichem Rollout frisch prüfen |
| Tatsächlicher Worker-Jobroot | Unter dem bestätigten `/app/data`-Bindmount noch nicht eindeutig zugeordnet | Ohne Root/Dateisystem/Limits/Reserve kein belastbares Batchbudget |

Das bisherige Ein-Material-Szenario mit circa **7,02 GiB einschließlich 5-GiB-
Reserve** liegt unter dem gemeldeten freien Hostplatz. Es verwendet einen
konservativen Planungsvorschlag, keine bestätigte produktive Limitsdatei.
Rechnerisch bleiben circa 12,98 GiB für Images, Backups und weiteres Wachstum;
deren tatsächliche Größe ist unbekannt. Deshalb kein exakt gemessener zusätzlicher
Produktionsspeicherbedarf ableitbar. Den Laptopmangel nicht auf Hetzner übertragen.

Aktuelle Preflight-Schätzung mit der **konkret genehmigten** Batch-/Limitsdatei
und demselben tatsächlichen Mount wiederholen, erst in einer eigenen Freigabe.
Vorhandene 755 MB bleiben erhalten. Keine Bereinigung, kein Balance/Resize,
keine Datenverschiebung, keine neuen Downloads oder ZIP-Imports.
