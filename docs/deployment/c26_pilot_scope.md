# C26-PILOT-INTEGRATION – Umfang und Freigabestatus

27.10.2026. **HOLD für Pilotbetrieb und C26. Offline-Reviewkandidat vorhanden.**
C26-04 bleibt DEFERRED. Kein SSH, Coolifyeingriff, Domain-/Firewall-/IdPwechsel,
Imagepull, Containerstart, produktiver Job, Download, Push oder Merge.

Das technische Ergebnis ist die gemeinsam übernommene D/E/F/G/H-Gatekette,
der vorhandene C16-/C22-Runtimepfad und die unveränderte UI-OIDC-Implementierung.
Die [aktuelle Integrationsmatrix](c26_pilot_gap_analysis.md) unterscheidet
Commitobjekte, den gesicherten H-Arbeitsstand und neue Änderungen. Die
[Validierung](c26_pilot_validation.md) enthält ausschließlich wirklich ausgeführte
Läufe mit Fehlern, Skips und Abnahmegrenzen.

Der neue kleine Pilot verwendet weiterhin genau eine C16-Queue und einen
CapacityExecutor. `material_planning` verarbeitet nur lokale synthetische
Discoveryseiten; im Test ein Courseindex und eine Week-0-Übersicht plus Manifest,
keine extern geladenen Inhalte. Nur der Manifest-Katalogeintrag ist autorisiert;
das vorhandene Materialbundle wird nicht in den Pilotkatalog übernommen.
`max_jobs=max_queued=max_parallel=1` begrenzt auch nach terminalem Abschluss
auf einen erzeugten Job pro frischem Root. URLs im Plan sind Referenzen,
keine Downloadaufträge. Kein Scheduler, kein Modellaufruf, keine LLMkosten.

Ausführung startet deaktiviert. API/Gateway sind getrennt vom Worker profilierbar.
Eine Konfigurationsänderung auf true ist keine Freigabe: ohne vorhandenes,
passendes und geöffnetes Gate werden Create/Start/Resume/Dispatch abgewiesen.
Öffnung benötigt den bestehenden expliziten Resumevertrag. **Dessen vorhandene
v2-/Koordinatorimplementierung ist offline_fixture bzw. local_test_only.**
Es existiert absichtlich kein livefreigegebener Ersatzdriver oder Testgrant für
Hetzner. Der Übergang zu erlaubter Liveausführung bleibt bis zur produktiven
Autorisierungsintegration technisch und organisatorisch BLOCKED.

Der neue Prüfer akzeptiert nur die leere deaktivierte Bootstrapkonfiguration
und liefert selbst bei Erfolg `deployment_permitted=false`, `production_release=HOLD`.
Er initialisiert keine Queue und beweist weder Idle noch eine gesunde Runtime.
Keine verlorene/fehlende Bestandsqueue als neue leere Queue interpretieren.

## Release-/HOLD-Matrix

Die bestehende Streamlitoberfläche zeigt derzeit Jobstatus und
Artefaktmetadaten. Der neue authentifizierte `GET /v1/jobs/{job_id}/result`-
Vertrag liefert den vollständigen hashgeprüften Plan; seine Anbindung durch
den vorhandenen UI-Client ist offline geprüft. **Das Plananzeigewidget fehlt.**
Ein separater persistenter UI-Checkout/Branch außerhalb des Backend-Repositories
ist in dieser Sandbox nicht beschreibbar. Deshalb wurde keine UI-Produktdatei
geändert und der komplette Browser-Ergebnisworkflow bleibt technisch HOLD.

| Umfang | Status | Voraussetzung für nächsten Schritt |
| --- | --- | --- |
| Technische Quellintegration / Review | Kandidat und Patch gesichert | Unabhängiges Review, offener Quarantänebefund und finale Testbilanz beachten |
| Defaultbranchintegration | PENDING | Regulärer PR-/Reviewprozess; automatischer Merge ausdrücklich verboten |
| Image-/Containerabnahme #109 | HOLD | Exakte gebaute Digests, Lockclosure, isolierte UID/Cgroup/OOM/PID1/Cancelbelege |
| Access #110 / UI #14 | HOLD | Echter IdP, CA/SAN, Browser, WSS, Widerruf, IPv6 und unabhängige Negativquelle |
| Gatebetrieb #146 | HOLD | Produktive Trust-/Witness-/Driverkette, exklusive Trigger und Cold Bootstrap |
| Ein synthetischer Hetznerjob | HOLD | Alle obigen Gates plus separate konkrete Job-/Resumeautorisierung |
| UI #15 / echtes CS50 / vollständiges C26 | HOLD | Separate fachliche/Betriebsabnahme; nicht vom synthetischen Plan ableiten |
| C26-04 #111 | DEFERRED | Eigenständiger Backup-/Restoreauftrag |

Die vollständige Blockerliste steht in `artifacts/c26_pilot_integration/blockers.json`.
Offene Planungsquarantäne, PDF-Exit3 und Worker-SQLite-Lock sind getrennte Befunde;
eine gemeinsame Ursache ist nicht nachgewiesen. Der Zeitfixturefehler des breiten
Gatefalls wurde behoben und mit 66 Gatefällen nachgeprüft.

Branch und Worktree werden wegen Mergesperre, schreibgeschützter gemeinsamer
Gitmetadaten und ausstehender Integration beibehalten. Keine Altartefakte entfernt.

---

## Historische Abgrenzung des Betreiberpakets 1f53289

# C26-PILOT – Betriebsumfang und Entscheidung

Stand: 27.10.2026. **Vorbereitung zur Review; Pilot HOLD, C26 insgesamt HOLD,
C26-04 DEFERRED.** Issue [#111](https://github.com/rf-data/Personal_Assistant/issues/111)
bleibt offen. Es wurde kein Server kontaktiert und kein echter Job gestartet.

## Lesereihenfolge

1. [Integrationsbefund und Lücken](c26_pilot_gap_analysis.md)
2. [Runtime und Konfiguration](c26_pilot_runtime_matrix.md)
3. [Sicherheitsabnahme](c26_pilot_security_acceptance.md)
4. [Wechselplan](c26_pilot_deployment_plan.md)
5. [Rückweg](c26_pilot_rollback.md)
6. [Einzeln ausführbare Betreiberchecks](c26_pilot_operator_checks.md)
7. [Tatsächliche Offlinevalidierung](c26_pilot_validation.md)

## Abgegrenztes Zielprofil

| Grenze | Verbindliches Pilotprofil |
| --- | --- |
| Benutzer | Ein individuell genehmigter OIDC-Operator; keine Anmeldung über gemeinsame Kennung |
| Zugang | `https://admin.franke-data.dev`, ausschließlich bestätigte private/VPN-Quellen; Domain noch nicht aktivieren |
| UI | Kanonischer Launcher für `app_admin.py`, OIDC, HTTPS-/Origin-/Proxyprüfung; kein direktes `streamlit run app_ui.py` |
| Backend | Privates HTTPS-Gateway, API nur Loopback im Gateway-Namespace, keine Hostports; eigene individuelle C16-Identität |
| Ausführung | Ein C16-Executor, vorhandene SQLite-Queue; keine zweite Engine, kein Scheduler |
| Annahme | Frischer separater Pilotroot, `max_jobs=1`, `max_queued=1`, `max_parallel=1`; ein bestätigter Job insgesamt |
| Anfangszustand | `execution_enabled=false`; API/Gateway zuerst, Executor ausdrücklich gestoppt (Start mit false wird verweigert); Workflow/PDF/Import/Index ebenfalls false |
| Eingaben | Ein synthetisches, hashgebundenes Manifest mit einer freigegebenen lokalen HTML-Seite; keine produktiven Speicher |
| Netzwerk | Executor `network_mode: none`; kein Download-/LLM-Profil; UI nur IdP und privates Backend nach expliziter Egressentscheidung |
| Stop | Jobowner fordert Cancel an; Abschluss erst nach bestätigtem Prozessende. Unbekanntes Cleanup → Quarantäne/HOLD |
| Fehler | Keine automatische Jobwiederholung; kein automatischer Resume; kein unbekanntes Deployment wiederholen |
| Deployment | Ausschließlich separate SHA-/Digest-/Konfigurationsfreigabe; alle alternativen Trigger gesperrt, vollständiges Gate erforderlich |
| Daten | Sämtliche Testinputs extern reproduzierbar; Ausgaben verwerfbar. Bestehende Bind-Mounts nicht übernehmen oder umwidmen |

`max_queued=1` alleine erlaubt einen laufenden **und** einen wartenden Job.
`max_jobs=1` begrenzt auf dem frischen Root alle angelegten Jobs einschließlich
terminaler Jobs. Auch ein nur angelegter Job verbraucht diesen Slot. Weitere
Versuche benötigen einen neu geprüften isolierten Pilotdurchlauf; niemals die
Jobdatenbank zurücksetzen, um diese Grenze zu umgehen. Kein laufendes Limit anheben.

## Kleinster geeigneter Job

Nach Behebung der P0-Lücken und eigener Livefreigabe: `material_planning` auf
einem einzigen synthetischen `manifest`-Katalogeintrag, Course `cs50_python`,
Section `0`, Output `pilot-material-plan`. Bestehender Pfad:
UI Preview → ausdrückliche Bestätigung → C16 Create/Start → vorhandener Executor
→ lokaler Materialplan als JSON. Keine URL wird dafür abgerufen; die
synthetische HTML-Seite liegt bereits im freigegebenen, read-only Katalog.

Dieser Job nutzt den vorhandenen Runner `src.tools_materials.processing.make_plan`.
Seine festen Registrybudgets sind 30 s Wandzeit, 20 s CPU, 768 MiB virtueller
Adressraum, 8 MiB je Ausgabedatei, 64 Dateideskriptoren und NPROC 32. Guardian und
Containergrenzen ergänzen diese Grenzen; NPROC ist unter Linux UID-weit.
Kataloggrenzen: 8 MiB je Datei, 32 MiB insgesamt. Für den Pilot zusätzlich
höchstens 1 MiB synthetische Eingaben und ein 128-MiB-Projektquota verlangen.
Diese zusätzliche Gesamtspeichergrenze ist im bestehenden Compose **nicht** eingerichtet.

Nur ein `manifest`-Katalogeintrag wird freigegeben: der ebenfalls registrierte
`quality_evaluation` benötigt ein `material_bundle` und hat so keine genehmigten
Inputs. Das ist eine Katalog-/Rechtegrenze, keine neue Prozessallowlist im Code.

## Ausführbar und weiterhin gesperrt

| Aufgabe | Entscheidung |
| --- | --- |
| Repositoryaudit, synthetische Offlineprüfungen | In diesem Auftrag erlaubt und ausgeführt |
| Betreiberinventur ohne Änderungen | Betreiber kann R-Schritte ausführen; Codex hat keinen Livezugriff |
| Authentifiziertes Lesen/Preview auf synthetischem Pilotkatalog | Erst nach Auth-/TLS-/Routingabnahme; erzeugt keinen Ausführungsauftrag |
| Obiger einzelner Planungsjob | Technisch implementiert, auf dem Server derzeit BLOCKED |
| Qualitätsevaluation | Implementiert, im ersten Pilot mangels passendem freigegebenem Katalog gesperrt |
| PDF, Workflow/Resume, Import, Index | Opt-ins bleiben false; zusätzliche Container-/Datenabnahme erforderlich |
| Kursdownloads, Audio/Video, OCR, Embeddings, LLM, Mailaktionen | Nicht freigegeben; kein stiller Egress und keine Modellinitialisierung |
| Autonomer Dauerbetrieb oder unbegrenzte Jobs | Nicht Teil dieses Profils |

## Abschlussfragen A–H

**A. Implementiert:** C16-Authentifizierung/Viewer-/Operator-/Ownerprüfungen,
Preview/Idempotenz, begrenzte persistente Queue, Executor/Guardian/Cancel,
C22-Rolleneinstiege, Non-root-Images und Healthvorlagen; UI-OIDC, Sessiongrenzen,
HTTPS-/WebSocketmiddleware und individuelle Backendbindings. Lokale Erfolge und
Grenzen stehen in der Validierung. Kein davon abgeleiteter Hostnachweis.

**B. Fehlend:** Gate-/Observer-/Collector-/Koordinatorintegration im tatsächlichen
master, produktive Vertrauensbasis und mutierender Driver; geprüftes
Coolify-Backend-Compose für die vorhandene Ressource; Pilotlimits/Quota und
Restartpolicy als geprüftes Overlay; Imageprovenienz und vollständige Liveabnahme.
Die vorhandenen Drafts wiederverwenden, keine zweite Queue entwickeln.

**C. Sofort prüfbar:** R01–R12 im Betreiberhandbuch: Versions-/Ressourceninventur,
Mount-/Netzzuordnung, Commit-/Buildbindung, Trigger und offene Deployments,
Vorhandensein des Wiederherstellungswegs. Keine Secrets an Codex senden.

**D. Separate Freigabe:** Jede C-Aktion sowie alle L-Aktionen; insbesondere
Konfigurationssicherung, IdP-/Identitätsanlage, Netz-/Storage-/Rollenwechsel,
DNS/TLS/Router, Deployment, Ausführungsaktivierung, echter Testjob und Rollback.
Dieser Auftrag erteilt keine dieser Freigaben.

**E. Kleinster Job:** Der oben beschriebene lokale synthetische Materialplan;
derzeit nur durch isolierte bestehende Tests nachgewiesen, nicht serverbereit.

**F. Laptopunabhängigkeit:** API/Worker/UI auf dem Host, persistenter gemeinsamer
Pilotroot, dauerhafte serverseitige Identitäts-/CAkonfiguration, unabhängiger
Deploymentkoordinator und überprüfte private Erreichbarkeit. Kein Chromebookpfad,
SSH-Tunnel, lokaler Worker oder lokaler Scheduler darf Voraussetzung sein.
Nach Start muss ein getrennter Browserclient den Job nach Schließen des ersten
Clients beobachten können. Automatischer Wiederanlauf nach Hostreboot bleibt bis
eigener Restartabnahme gesperrt; Laptopunabhängigkeit erfordert keine Auto-Retries.

**G. Backuprestrisiko:** Konfigurations-, Secret-, Zertifikats-, Mount- und
Queueverlust sind ohne vollständigen Restore nicht abgedeckt. Deshalb nur
reproduzierbare Testdaten; destruktive/überschreibende Änderungen ohne einzeln
belegten Rückweg bleiben ausdrücklich blockiert. Ein altes Image allein stellt
keine Konfiguration oder Daten wieder her.

**H. Vollständiges C26:** Zusätzlich #111 mit endgültigem Storage und isoliertem
konsistentem Restore, vollständige #109/#110/#146 und weitere offene
Betriebs-/Monitoring-/Recoveryabnahmen, belastbare Last-/Fehler-/Restartnachweise,
unabhängiger Review und ausdrückliche Produktionsfreigabe. Pilotabnahme schließt
keines dieser Issues und erklärt C26 niemals GO.

## C26-INT-02-Nachtrag zur Plananzeige

Das zuvor fehlende Widget liegt jetzt in einem vollständigen separaten UI-Patch
mit Client-, Streamlit- und synthetischen IPCtests vor. Anwendung und Tests im
tatsächlichen UI-Repository stehen wegen der Schreibgrenze aus. Die Darstellung
ist eine sichere JSONprojektion des empfangenen Plans, ohne freie Titel, URLs,
Provenienz oder lokale Pfade. Kein direkter SQLitezugriff und keine Veränderung
von Rollen-/Ownerrechten. Der Backendvertrag sperrt Quarantäne ausdrücklich.
C26 bleibt HOLD, C26-04 bleibt DEFERRED; keine Produktionsfreigabe.
[Stabilisierung und Übergabe](c26_int_02_validation.md).
