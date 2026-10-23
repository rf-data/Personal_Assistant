# C26 Integration und Produktionsabnahme – 23.10.2026

Status: Offline-Review vorbereitet, Produktion **blocked**. Keine Merges,
Deployments, SSH-/Hostzugriffe oder Änderungen an Containern, Volumes, VPN,
Traefik, DNS, Firewall, IdP oder Pilotdaten. Diese Bestandsaufnahme ersetzt die
historischen Prüfungen nicht. Der gleichzeitig bearbeitete Week-0-Auftrag liegt
auf `feat/c26-week0-acceptance` in einem eigenen Worktree.

## Verifizierter GitHub-Stand

GitHub-API und anschließend Git-Fetch, 23.10.2026:
Backend `master = d180a8f6e65f900a4d0d169475d78a4cb42b0d8c`,
UI `main = e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`.
#142 (`81897b7`), #144 (`ef0aa1c`), #147 (`d0a58f3`), #150 (`c6415d3`),
#151 (`0bb9a5b`) und #152 (`5d4c12b`) sind gemergt. UI #19 (`371befb`) ist
in `e4be7a2` integriert. Issue #146 ist weiterhin offen.

| PR | Geprüfter Head | GitHub / lokale Konfliktprüfung | Integrationsempfehlung |
| --- | --- | --- | --- |
| Backend [#149](https://github.com/rf-data/Personal_Assistant/pull/149) | `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb` | Draft, mergeable; unveränderter Diff ab `e581e201` auf `d180a8f` anwendbar | Technisch reviewfähig; betriebliche Voraussetzungen zum Merge ungeklärt |
| Backend [#148](https://github.com/rf-data/Personal_Assistant/pull/148) | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Draft, mergeable; zusammen mit #149 konfliktfrei auf `d180a8f` anwendbar | Draft beibehalten: Driver, Bootstrap und reale Abnahme fehlen |
| UI [#20](https://github.com/rf-data/personal-assistant-ui/pull/20) | `6b84e3c09f877309a3fd1c6f9cbcf61bb9f46788` | Draft, mergeable; Dokumentations-Follow-up auf aktuellem UI-main | Technisch reviewfähig; gekoppelte Betriebsfreigabe fehlt |

Bei allen drei Drafts: keine eingereichten Reviews, keine Inline-Reviewthreads
und keine Check-Runs am geprüften Head. Das ist kein grüner CI-Nachweis. Eine
Prüfung aller möglichen externen Statusanbieter wurde nicht durchgeführt.
Die API zeigte bei #148 zunächst `mergeable=null`; die spätere Abfrage bestätigte
`true`. GitHub-Base-SHAs der Backend-Drafts stehen noch auf `e581e201`; deshalb
wurde ausdrücklich gegen den aktuellen Master getestet.

**Aktuell sicher zum Merge freigegeben: keiner dieser PRs.** Technische
Konfliktfreiheit beweist keine betriebliche Sicherheit. Alle Merges in überwachte
Backend-/UI-Branches könnten einen Produktiv-Redeploy auslösen, auch reine
Dokumentations-Merges und dieser Follow-up-PR. Die tatsächlichen Coolify-Trigger
sind unbekannt. Vor jedem Merge muss der Betreiber deren Zustand und Wirkung
bestätigen und gegebenenfalls separat kontrollieren. Draft-Status allein sperrt
keinen späteren Push-/Merge-/Webhook-Trigger. Kein Draft wurde hier umgestellt.

## Aktuelle Offline-Belege

Die unveränderten Diffs von #148 und #149 wurden ausschließlich im eigenen
Worktree auf `d180a8f` angewendet, zusammen getestet und danach exakt rückwärts
angewendet. Dieser PR liefert keine zweite Kopie dieser Implementierungen.
Die Patchdateien und ihre Fingerprints bleiben in den lokalen Prüfergebnissen.

| Lauf | Ergebnis / Grenze |
| --- | --- |
| Gate + HTML-Projektion + B5/B6 + C18 + HTTPS-Composeaudit + Transport + Runtime | **304 bestanden, 2 fehlgeschlagen**, 334,01 s, 306 Fälle |
| C18-Einzelwiederholung `test_metadata_permission_and_hash_tamper_are_rejected` | **1 bestanden**, 8,91 s; Guardian-Verlust aus dem breiten Lauf nicht reproduziert, Ursache offen |
| Transport-Einzelwiederholung | **1 bestanden**, 15,79 s; ausschließlich eigene synthetische Loopback-API/Worker, ohne Sandbox-Socketsperre |
| UI #20 auf integriertem #19: HTTPS-/OIDC-/Startschutz | **20 bestanden, 9 Subtests**, 12,62 s |

Der breite Lauf ist ausdrücklich keine vollständig grüne Suite. C18 meldete
`Guardian lost; dispatch quarantined`; es gibt keinen belegten kausalen Fix.
Der Transportfall scheiterte im ersten Lauf bereits bei der Socketanlage mit
`PermissionError`; der genehmigte lokale Loopback-Wiederholungslauf bestand.
Die erste UI-Collection scheiterte an fehlendem `pydantic_settings` in der
Backend-Testumgebung; die Wiederholung verwendete zusätzlich ausschließlich die
bereits vorhandenen Pakete der UI-Umgebung. Keine neue Venv oder Dependency.

Die 66 Gatefälle des aktuellen Laufs bestanden: atomische konkurrierende Annahme,
Dispatch/Drain, unbekannte Worker/Queue, fehlende/falsche/abgelaufene Freigabe und
SHA/Image, Prozessverlust, geschlossene Recovery/Rollback/Resume, Auditmanipulation,
Restore und fehlender Pflichtmount. Die 34 HTML-Fälle bestanden einschließlich
beider echten Exportfälle. Die Originale der Notes (237 Blöcke, **34 Codeblöcke**)
und des PSet (28 Blöcke, **5 Aufgabenlinks**) wurden ausschließlich gelesen.
Link-/Listenhierarchie, Code, Handoff-v1-Lesbarkeit und v2-Projektion sowie
B5/B6-Modelle und Planung bestanden gemeinsam. Die vollständige ursprüngliche
Produktionskette aus Plan/Downloadreceipt/Jobjournal liegt nicht vor: daraus folgt
keine neue produktive Quality-Gate-Abnahme.

Die Tests führten keine Kursdownloads aus. Compose wurde nur lokal gerendert,
kein Container gestartet oder verändert. Kein aktueller Browser-/Traefik-/TLS-
End-to-End-Beleg, keine Hosted-CI- oder produktive Job-/Mountprüfung. Ältere
ENOSPC-/Browserläufe sind keine aktuellen Erfolge.

Reproduktion mit vorhandenen Paketen, explizitem schreibgeschütztem Exportroot und
einem eigenen temporären Testziel:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$TEST_PYTHON" -B -m pytest -q -p no:cacheprovider \
  tests/test_deployment_gate.py tests/test_cs50_html_projection.py \
  tests/test_cs50_course.py tests/test_cs50_week_materials.py \
  tests/test_cs50_workflows.py tests/test_https_preflight.py \
  tests/test_deployment_transport.py tests/test_runtime_paths.py \
  --basetemp="$OWN_TEST_ROOT" --junitxml="$OWN_TEST_XML"
```

Dabei müssen beide geprüften Draft-Diffs in einer isolierten Kopie angewendet und
`CS50_WEEK0_QUALITY_EXPORT` sowie die expliziten Pfade gesetzt sein. Der
Transporttest benötigt lokale Loopbacksockets. UI-Tests:
`tests/test_https_security.py tests/test_container_runtime.py` im UI-Checkout.
Exakte Ergebnis-/Quellhashes: `c26_release_readiness_2026_10_23.v1.json`.

## Architektur- und Kompatibilitätsbewertung

#148 ergänzt das bestehende C16-Admission-/Dispatchlocking und bestehende Queue,
Executor und C18-Pfade. `deployment_gate_required=false` erhält den bisherigen
Default. Keine neue DB, Queue, Workerrolle oder DB-Migration. Ein bestehender
Legacy-Writer nimmt dadurch noch nicht am Gate teil. Neue Journal-/Lockdateien
und alle Writer müssen auf demselben bestätigten lokalen Linux-Jobroot liegen;
NFS-/Mehrhostbetrieb ist nicht freigegeben. Das Journal ist lokal hashverkettet,
kein extern unveränderliches Audit gegen Root.

Der **Erstbootstrap** benötigt ein eigenes kontrolliertes Wartungsfenster:
Trigger und sämtliche Annahmepfade sperren, bestehende Arbeit auslaufen lassen,
Idle/Locks/Pilotabgrenzung bestätigen, bestehende Rollen ohne Workerüberlappung
auf Gatecode bringen, Pflichtgate auf genau dem bestehenden Root aktivieren und
Journal geschlossen initialisieren. Kein fehlender Mount darf eine Ersatzqueue
erzeugen. Ein genehmigtes neues Image öffnet Annahmen nicht automatisch;
Resume benötigt eigene frische Freigabe und Liveprüfung.

Ein produktiver Coolify-Driver fehlt weiterhin. Ohne bestätigte Ressourcen-UUID,
Buildtyp, Triggerkontrolle, konkrete SHA↔Registrydigest-Bindung, neue
Containeridentität, private Mount-/Queue-/Scope- und Healthbelege darf kein Driver
wechseln. Außerhalb C16 gestartete Imports/Transkript-/Pilotprozesse benötigen eine
dauerhafte separate Sperre oder belegte Ressourcentrennung. Ein einmaliges
„idle“ genügt nicht. #146 bleibt offen; keine Produktivabnahme aus Offline-Tests.

Backend #147 und UI #19 passen zum privaten HTTPS-Profil: TLS terminiert am
bestehenden Traefik, die UI verwendet genau den kanonischen HTTPS-Origin,
WebSockets brauchen einen eindeutigen passenden Origin; Callback-Navigation darf
Origin auslassen. Nur bestätigte Proxy-Socketpeers dürfen Forwarded-Header liefern.
Die VPN-Allowlist muss die tatsächliche Quelladresse prüfen; ein UI-Profilname
beweist keine VPN-Sperre. Private C16-HTTPS-API, individuelle Backendtokens,
OIDC-Issuer/Callback/Subjects und identische Rollen bleiben Voraussetzung.
Kein zusätzlicher Proxy, kein zweiter API-/Auth-/Workerpfad. Reale Headerketten,
VPN-Adresshaltung, Zertifikatsrotation und IdP-Widerruf sind noch nicht abgenommen.

## Read-only Betreiberinventur

Dieses Verfahren ist vorbereitet; **nicht durch Codex auf dem Host ausgeführt**.
Ausführung und jeder weitere Hostzugriff sind eine eigene Betreiberentscheidung.
Den Bericht zuerst privat in einer vorhandenen geschützten Ablage führen. Keine
kompletten Inspect-/Compose-/Env-/Prozessargument-/Logausgaben exportieren, keine
Tokens, Webhook-URLs, Cookies, privaten Schlüssel oder OIDC-Secrets erfassen.
Vor Weitergabe Namen, öffentliche/private Adressen, Hostpfade und IDs durch
stabile lokale Aliase ersetzen; die private Zuordnung beim Betreiber behalten.

1. In der vorhandenen Coolify-Oberfläche **lesend** je bestehender Rolle Backend,
   UI, Worker/Pilot erfassen: Ressourcenalias und privat zugeordnete UUID, Buildtyp,
   Quellrepo/Branch/Watch-Paths, Auto-/Preview-Deploy, Git-/Registry-/Webhook-/API-
   und Schedulertrigger, berechtigte Deploykonten sowie wartende Deployments.
   Nur `aktiv/inaktiv/unbekannt` und Verantwortlichkeit berichten; keine URLs oder
   Credentials kopieren. Kein Toggle verändern, keine Builds auslösen.
2. Auf dem bereits vorgesehenen Host ausschließlich lesende Befehle verwenden:

   ```sh
   df -h
   df -i
   docker container ls --format '{{.ID}}\t{{.Status}}'
   # Je EINER vorher identifizierten bestehenden Rolle, keine geratene Auswahl:
   : "${C26_CONTAINER_ID:?Privat bestaetigte bestehende Container-ID}"
   docker container inspect --format \
     '{{.Id}} {{.Image}} {{.State.Running}} {{.RestartCount}}' "$C26_CONTAINER_ID"
   docker container inspect --format \
     '{{range .Mounts}}{{.Type}} {{.RW}}{{println}}{{end}}' "$C26_CONTAINER_ID"
   docker container inspect --format \
     '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}}' \
     "$C26_CONTAINER_ID"
   ```

   Keine `exec`-/Restart-/Pull-/Prune-/Volume-/Compose-Up-Befehle. Keinen Docker-
   Socket in ein neues Werkzeug mounten. Formatierte Metadaten sind kein
   Rollenbeweis: tatsächliche Rollen/Mountquellen privat zuordnen, im Bericht
   Root-/Queue-/Netzaliase verwenden. Bei unbrauchbarer Inodeanzeige `unknown`
   dokumentieren; kein Erfolg aus `0/0/0` ableiten.
3. Gemeinsam mit der vorhandenen Betriebsdokumentation privat bestätigen:
   genau ein Executor, alle Jobs/Queues/Annahmepfade und deren Root-/UID-/Lock-/
   WAL-Zuordnung, verbleibende unabhängige Pilot-/Importprozesse und Kapazität.
   Bestehende authentifizierte Diagnose-/Healthwege nur nach gesondert geklärtem
   Zugriff nutzen; keine neue API und keinen Probejob starten. Bei noch fehlendem
   Gatecode keinen `initialize`-Aufruf zur Inventur verwenden.
4. Bestehende Netzwerk-/Traefikkonfiguration gezielt in der Oberfläche prüfen:
   UI- und private API-Netze getrennt, keine direkten öffentlichen Ports,
   Router/TLS-Serviceport/Middlewarebezug, kanonischer Origin, vertrauenswürdige
   Proxy-CIDRs, VPN-Quelladresserhalt und RemoteAddr-Allowlist. Nur notwendige
   Werte privat abgleichen; keine vollständigen Labels oder Konfiguration teilen.
5. Zertifikatsverantwortung und Renewal/Fehleralarm, VPN-Geräte/Routen, IdP-Issuer/
   Callback/Subjects/Rollen und Widerrufsverfahren als Entscheidungen erfassen.
   Je Image laufende Image-ID/Digest ↔ Buildnachweis ↔ freigegebene Commit-SHA
   prüfen; OCI-Label allein ist kein Laufzeitnachweis. Vorgängerversion benennen.
6. Letztes vorhandenes Backup, bisherigen isolierten Restorebeleg, SQLite-
   Konsistenzverfahren, Wiederanlauf, Rettungszugang, Alarmempfänger und
   Rollbackverantwortung dokumentieren. Kein Backup/Restore während Inventur
   ausführen und keine laufende DB blind kopieren.

Jede unbekannte Angabe bleibt `unknown` und sperrt die entsprechende Freigabe.
Minimaler Ergebnisbogen je Rolle: Buildtyp, bestätigte aktive Version, Trigger-
status, Queue-/Mount-/Netzaliase, Workerzahl, Health, Limits, Backup-/Rollbackbeleg,
Zeitpunkt und prüfender Betreiber. Keine ausgedachten UUIDs/SHA/Digests einsetzen.

## Geordnete Produktionsabnahme (noch nicht ausgeführt)

1. Betreiber entscheidet VPN/Geräte/Routen, Domain/DNS/TLS, IdP/Callback/Rollen,
   private API, Rettungszugang und Verantwortlichkeiten.
2. Obige read-only Inventur privat ausführen, redigieren und gegen Rollen-/Queue-/
   Pilotbestand prüfen. Unbekannte Zustände blockieren.
3. Alle Coolify-Auslöser, Rechte und wartenden Deployments prüfen. Wirkung eines
   Merges/Pushevents nachweisen; erforderliche Triggeränderungen separat freigeben.
4. Konkreten bestehenden-Ressourcen-Driver reviewen; Bootstrap, Maintenancefence,
   Drain und Stop-before-start separat freigeben. Negative Freigabe-/SHA-/Worker-
   und Konkurrenzfälle sowie Prozessverlust/Recovery auf isolierter Kopie abnehmen.
5. Exakte Backend-/UI-SHAs und unveränderliche Images inklusive Rückweg genehmigen.
   Bestehende Rollen/Mounts kontrolliert integrieren, keine Workerüberlappung.
6. HTTPS über bestehenden Traefik, private VPN-Route, Zertifikat und Allowlist
   abnehmen; keine öffentliche Ausweichroute.
7. OIDC-Login/Logout/Callback, Sessionablauf und Rechteentzug sowie Viewer-/Operator-
   und Source-/Course-/Ownergrenzen mit individuellen Identitäten prüfen.
8. Öffentlich/außerhalb VPN: UI, API, WebSocket und direkte Ports müssen verweigern;
   fremde/doppelte Origins und manipulierte Forwarded-Header negativ testen.
9. Liveness und getrennte API-/Worker-/Queue-Readiness, neue Instanz und exakte
   installierte Version sowie unveränderte geschützte Ressourcen bestätigen.
10. Rollback und Wiederanlauf mit exakter separater Freigabe testen. Annahmen bleiben
    nach Wechsel/Fehler geschlossen; erst frischer Resume-Beleg öffnet sie.
11. Reale Ergebnisse, Logs ohne Secrets, Freigaben und verbleibende Gaps dauerhaft
    dokumentieren. Erst dann Issue #146 und Produktivbereitschaft bewerten.

Nächster konkreter Betreiber-Schritt: die read-only Inventur und insbesondere
**Auto-Deploy-/Queue-/Mountzuordnung** bereitstellen. Bis dahin bleiben alle
Produktiv-Merges und die Hostadapter-/Bootstrapfreigabe ausstehend.

## Aufbewahrung

Eigener Branch `docs/c26-release-readiness`, eigener Backend-Worktree
`Personal_Assistant-c26-release-readiness`, UI-Prüfworktree
`personal-assistant-ui-c26-release-check` (detached #20), Ergebnisse im separaten
`Personal_Assistant-c26-release-results`. PR/Branch und Worktrees bleiben für
Review und Reproduktion erhalten, weil kein Merge autorisiert ist. Die Dokumente
sind erst nach regulärem Review/Merge im Default-Branch integriert. Keine alten
Worktrees, Bundles, Quellarchive, Daten oder Umgebungen bereinigt.
