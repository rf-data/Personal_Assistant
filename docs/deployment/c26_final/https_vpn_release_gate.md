# C26 HTTPS/VPN Release Gate – 23.10.2026

Entscheidung: **operator_action_required**. Keine Produktivfreigabe. Ein Merge
oder bestandene Offline-Tests sind keine Abnahme des produktiven Deployment-Schutzes.
Die historische Inventur-/Abnahmemethode aus
[PR #153](https://github.com/rf-data/Personal_Assistant/pull/153) bleibt Grundlage;
aktuelle technische Belege stehen in `validation.v1.json` und `integration.v1.json`.

## Aktuelle Integrationsbasis und Reviewempfehlung

Backend-default `master`: `c4b057a75c38655e43b8ac35a35cc82645ba2826`.
UI-default `main`: `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`.
#144/#147/#150/#151/#152/#153/#154 sowie UI #19 sind integriert. Die Dokumente
und ZIP-Korrektur aus #153/#154 wurden auf dem aktuellen Master erneut gelesen.

| Offener PR | Geprüfter Head | Technische Bewertung | Freigabegrenze |
| --- | --- | --- | --- |
| [Backend #149](https://github.com/rf-data/Personal_Assistant/pull/149) | `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb` | Unveränderter Diff auf aktuellem Master und zusammen mit diesem C18-Follow-up anwendbar; echte HTML- und B5/B6-Tests erneut geprüft | Technisch zum Fachreview empfohlen; keine selbstständige Produktivfreigabe, Triggerprüfung vor Merge |
| [Backend #148](https://github.com/rf-data/Personal_Assistant/pull/148) | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Bestehender Gate-Kern und bestehende C16/C18-Pfade lokal geprüft; keine zweite Implementierung | Draft: realer Driver/Bootstrap/Hostbelege fehlen, offene Laufzeitdiagnose nicht verbergen |
| [UI #20](https://github.com/rf-data/personal-assistant-ui/pull/20) | `6b84e3c09f877309a3fd1c6f9cbcf61bb9f46788` | Dokumentations-Follow-up auf integriertem #19; 20 HTTPS-/OIDC-/Launcherfälle, 9 Subtests bestanden | Technisch reviewfähig, keine Live-/Browser-/VPN-Abnahme |

Keine eingereichten Reviews oder Inline-Reviewthreads; keine Check-Runs an den
geprüften Heads. Commitstatus `pending` mit `total_count=0` ist **kein laufender
oder grüner CI-Testbeleg**. Git-Konfliktfreiheit separat von fachlicher und
betrieblicher Freigabe behandeln. Alle drei bleiben Draft; Issue #146 bleibt offen.
#153/#154 verursachen keine direkten Dateiüberschneidungen mit den Draft-Diffs.
Dieser Follow-up bleibt ebenfalls bis zum regulären Review unintegriert.

**Keiner dieser Merges ist aktuell betrieblich freigegeben.** Das tatsächliche
Coolify-Auto-Deploy-Verhalten ist unbekannt; auch Dokumentations-Merges oder Pushes
in überwachte Branches könnten Containerwechsel auslösen. UUIDs, Trigger oder
installierte Versionen wurden nicht aus Repositorydaten geraten.

## Echte HTML- und Laufzeitbelege

Die ursprünglichen 237 Notes-Blöcke mit 34 Codeblöcken, 28 PSet-Blöcke und fünf
Aufgabenlinks bleiben erhalten. #149 prüft Linkprojektion, Listen-/Parenthierarchie,
Code und v1/v2-Handoff-Kompatibilität auf den echten, unveränderten Exporten. Die
früheren `passed`-Qualitätsberichte werden nicht in neue produktive Erfolge
umgedeutet. PDF-/Transcript-Originale und vollständige alte Jobketten fehlen.

Der frühere Socketfehler wurde als Sandboxproblem abgegrenzt: der unveränderte
Transportfall besteht mit eigenen synthetischen Loopbacksockets. Die vorliegende
UI-Prüfung verwendet ausschließlich bereits vorhandene Pakete, keine neue Venv.

Die C18-Quarantäne ist **nicht pauschal als Umgebungsfehler geschlossen**. Ein
Diagnoselauf auf aktuellem Master plus unveränderten #148/#149-Diffs, ohne neue
Child-Integration, reproduzierte bei `stale...[config]` eine Quarantäne. Im lokalen
SQLite-Jobdatensatz steht `Execution interrupted (OperationalError)`; der erste
Job war vollständig abgeschlossen, der Resumejob wurde unterbrochen und gesperrt.
Dies ist kein nachgewiesener neuer Child-Adapterfehler. Die genaue ursprüngliche
SQLite-Fehlernummer wurde vom bestehenden Guardian nicht aufgezeichnet. Ein
gezielter Dreierlauf und ein weiterer vollständiger 24er-Lauf mit Diagnose
bestanden; kein daraus abgeleiteter kausaler Fix und keine Lockerung von
Quarantäne/Locking/Timeouts. Der separate erste Dreier-Diagnoseversuch war durch
eine Dateinamenskollision des Hilfsloggers ungültig und wird nicht als
Produktregression gezählt. Alle Läufe, auch Fehler, bleiben im Validierungsbeleg.

Der bestehende Gate-Kern prüft atomare Annahme-/Dispatchsperren, Drain,
Worker-/Queuezustand, konkurrierende Annahme, Prozessverlust, fehlende/falsche/
abgelaufene Freigaben und SHA-/Imagebindung, Audit, Recovery, Rollback und separate
Resume-Freigabe. Pflichtgate-/Mountfehler bleiben geschlossen. Keine DB-Migration,
keine zusätzliche Queue oder Workerrolle, kein produktiver Coolify-Driver.
Der Default `deployment_gate_required=false` schützt alte Writer nicht automatisch.

## Reproduzierbare read-only Hostinventur (Betreiber)

**Nicht durch Codex ausgeführt.** Nur ein separat entschiedener Betreiberlauf
auf dem bestehenden Host darf diesen Bestand erfassen. Ausführliche gefilterte
Kommandos stehen in [der integrierten Anleitung](../c26_release_readiness_2026_10_23.md#read-only-betreiberinventur).
`operator_inventory.template.v1.json` enthält ausdrücklich unbekannte Werte.
Privat ausfüllen, vor Weitergabe redigieren; UUID-/IP-/Pfadzuordnung privat behalten.

1. In Coolify rein lesend alle bestehenden Rollen und Ressourcen zuordnen:
   Backend, UI, vorhandener Executor, unabhängige Pilot-/Importprozesse. Buildtyp,
   Quellbranch, aktive Instanzen, konkrete installierte Version und Image-ID/Digest
   mit Buildnachweis erfassen. Labels allein sind kein Code-/Versionsbeweis.
2. Auto-/Preview-/Git-/Webhook-/Registry-/API-/Schedulertrigger, Deployrechte und
   wartende Deployments bestätigen. Keine Toggleänderung oder Deploymentprobe
   während der Inventur. Nur Zustände und Verantwortliche teilen, keine URLs/Tokens.
3. Auf dem Host ausschließlich gefilterte Metadaten erfassen:

   ```sh
   df -h
   df -i
   docker container ls --format '{{.ID}}\t{{.Status}}'
   : "${C26_CONTAINER_ID:?Privat bestaetigte bestehende Rolle}"
   docker container inspect --format \
     '{{.Image}} {{.State.Running}} {{.RestartCount}}' "$C26_CONTAINER_ID"
   docker container inspect --format \
     '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}}' \
     "$C26_CONTAINER_ID"
   ```

   Keine vollständigen Inspect-/Compose-/Env-/Log-/Prozessargumentausgaben.
   Keine Keys, Cookie-/OIDC-Secrets oder privaten Tokenpfade teilen. Kein `exec`,
   Restart, Pull, Prune, Volumewechsel oder Compose-Up zur Inventur. Unbrauchbare
   Inodeanzeigen bleiben unknown. Die Quelle und das Ziel eines Mounts privat
   prüfen und ausschließlich Root-/Queue-/Netzaliase berichten.
4. Über bereits vorhandene authentifizierte read-only Anzeigen die tatsächliche
   Queue, Jobs, genau einen Worker und sämtliche Annahmepfade zuordnen. Kein neues
   `Controller`-/DB-Initialisieren, Gate-Initialize oder Probejob zur Inventur.
   Unabhängige Pilot-/Importroots nicht allein über eine C16-Queue als idle erklären.
5. Bestehende private API-/Ingressnetze, Router, TLS-Serviceport, VPN-Quelladresse,
   angehängte RemoteAddr-Allowlist, exakte UI-Origin-/WebSocketkette und bestätigte
   Proxy-Socketpeers privat prüfen. Keine zweite API und kein neuer Proxy.
6. VPN-Verfahren, Geräte/Routen, Domain/DNS, Zertifikatsausstellung/Renewal und
   Alarmierung, OIDC-Issuer/Callback/Subjects/Rollen/Widerruf dokumentieren.
   Letzten Backup-/isolierten Restore-/Rollbackbeleg und Rettungszugang zuordnen;
   keine aktive SQLite blind kopieren oder Restore ausführen.

Fehlt eine Angabe, bleibt sie unknown und verhindert ihre Freigabe. Inventur ist
keine Erlaubnis, Trigger, Netzwerke oder Ressourcen zu verändern.

## Noch erforderliche Entscheidungen und sichere Reihenfolge

1. Betreiber bestätigt Ressourcen-/Rollen-/Queue-/Mount-/UID-/Lock-/Pilotzuordnung,
   Hostkapazität und Rettungszugang. SQLite-/WALbetrieb und lokale Linux-Locks
   müssen zum Single-Host-Vertrag passen; NFS-/Mehrhostbetrieb nicht freigegeben.
2. Betreiber entscheidet VPN, genehmigte Geräte/Routen, Domain/DNS/TLS, private
   HTTPS-API, OIDC-Callback und individuelle Rollen-/Tokenbindung. Außen-VPN-
   Abschirmung und Quelladresserhalt benötigen echte Belege.
3. Alle alternativen Deployauslöser und ausstehenden Deployments prüfen. Erst nach
   separater Freigabe einen exklusiven kontrollierten Triggerpfad herstellen.
   Vorher kein Merge in einen möglicherweise überwachten Produktivbranch.
4. Den konkreten Driver für genau eine bestehende Ressource/Buildart anhand des
   Bestands implementieren/reviewen lassen. Neue SHA↔Digest-Bindung und geschützte
   Ressourcen prüfen. Keine geratenen Coolify-Aufrufe oder Branchhead-Auflösung.
5. Erstbootstrap separat freigeben: sämtliche Annahmepfade sperren, laufende Arbeit
   auslaufen lassen, Idle/Locks beweisen, bestehenden Worker ohne Überlappung auf
   Gatecode bringen und Journal geschlossen initialisieren. Keine Pilotdaten ändern.
6. Exakte Backend-/UI-SHAs und Images genehmigen. Wartung/Drain/Idle/Versions-/
   Mount-/Scopeprüfung vor genau einem Containerwechsel, danach neue Instanz,
   Liveness und getrennte API-/Worker-/Queue-Readiness prüfen.
7. VPN/HTTPS mit bestehendem Traefik abnehmen: Zertifikat, Login/Callback, HTTP-
   und WebSocket-Origin, individuelle Viewer-/Operator-/Course-/Ownergrenzen,
   Ablauf und Rechteentzug. Öffentlich/außerhalb VPN müssen UI/API/WebSockets und
   direkte Ports verweigern; manipulierte Forwarded-/Originheader negativ prüfen.
8. Rollback-/Wiederanlaufprobe separat genehmigen. Bei Fehler/Koordinatorverlust
   Annahmen geschlossen halten, reale Instanz und Journal privat sichern. Kein
   Löschen von Lockdateien, keine gespeicherten PIDs signalisieren und kein Replay.
   Nur exakte vorige Version mit neuer Rollbackfreigabe oder belegte Recovery;
   anschließend eigene frische Resume-Freigabe und Liveprüfung. Auth/TLS/VPN erhalten.
9. Reale Belege und Betreiberfreigaben dauerhaft dokumentieren. Erst dann über
   Issue #146 und `production_approved` entscheiden.

Nächste Betreiberaktion: die read-only Inventur, besonders **Auto-Deploy-Trigger
und Queue-/Mount-/Pilotzuordnung**, privat erfassen und redigiert bereitstellen.
Dieses Review hat keinen Host betreten, keine produktiven Writer gestartet und
keine Container-, VPN-, Traefik-, DNS-, Firewall- oder IdPänderung vorgenommen.

## Aktuelle Testergebnisse und Aufbewahrung

| Lauf | Tatsächliches Ergebnis |
| --- | --- |
| Aktueller Master + beide unveränderten Draft-Diffs + C18-Follow-up | 433 bestanden, 3 Setupfehler, 502,17 s |
| Finaler zusätzlicher Quellroot-Schutz, eigene neue Tests | 20 bestanden, 152,41 s |
| Derselbe finale Stand zusammen mit #148/#149 | 20 bestanden, 154,69 s |
| UI #20 / integriertes #19 | 20 bestanden, 9 Subtests, 3,12 s |
| Unveränderter Master, alter Metadata-/Tamper-Fall | 1 bestanden, 4,48 s |
| Diagnose vor neuer Child-Integration: C18 + Transport | 24 bestanden, 1 Quarantänefehler, 129,12 s |
| Gezielte Wiederholung Config/Parser/Metadata mit Diagnose | 3 bestanden, 19,52 s |
| Weitere vollständige C18-Diagnose | 24 bestanden, 172,76 s |

Alle 66 Gate-, 34 HTML- und 24 C18-Fälle sowie B5/B6 und Materialbatch-Worker
bestanden im breiten Kompatibilitätslauf. Dieser Lauf enthält die letzte zusätzliche
Quellroot-Sperre noch nicht; dafür wurden danach alle 15 neuen Assignment- und
5 Speicherfälle auf beiden finalen Ständen erneut geprüft. Die Läufe überlappen
und werden nicht addiert.

Die drei Setupfehler betreffen ausschließlich die älteren Knowledge-/LLM-
Batchtests in `test_cs50_batch.py`: `tiktoken` ist in der vorhandenen Umgebung
nicht installiert. Auch die gezielte Wiederholung endet beim Import. Sie sind
keine fehlgeschlagenen neuen Materialbatch-Workflows, bleiben aber echte offene
Testumgebungslücken. Keine Abhängigkeiten oder Modell-/Tokenizerdaten nachgeladen;
keine vollständige grüne Gesamtsuite behauptet. Warnungen aus absichtlich
ungültiger kopierter URL und doppeltem synthetischem ZIPnamen sind dokumentiert.

Der ursprüngliche `test_metadata_permission_and_hash_tamper_are_rejected` bestand
auf unverändertem neuem Master und in den Wiederholungen. Die beobachtete
zusätzliche Config-Resume-Quarantäne bleibt unabhängig davon offen. Ein erfolgreicher
Repeat ist kein Fixbeleg. Diagnosepatches/Hilfslogger sind ausschließlich lokale
Prüfartefakte und nicht Bestandteil des Produktcodes.

Eigener Branch `feat/c26-final-pilot-readiness`, Worktrees
`Personal_Assistant-c26-final-pilot`, `Personal_Assistant-c26-final-compat` und
`personal-assistant-ui-c26-final-check`; getrennte Ergebnisse unter
`Personal_Assistant-c26-final-results`. Kompatibilitätsworktree enthält bewusst
die eigenen angewendeten Prüfpatches; Hashes und Patchdateien bleiben erhalten.
Kein fremder Worktree, alte Branches, Bundles, Originale oder Venvs gelöscht.
Der neue Review-PR wird ohne Merge erstellt. Branch, Worktrees und verifiziertes
Git-Bundle bleiben deshalb erhalten; die neuen Dokumente sind erst nach dem
regulären Review/Merge im Default-Branch integriert.
