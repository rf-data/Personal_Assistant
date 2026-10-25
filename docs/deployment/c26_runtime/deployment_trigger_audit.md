# Coolify-Triggernachtrag — Betreiberbefund 23.10., Prüfstand 24.10.2026

**GO für Review und weitere lesende Inventur; NO-GO für Deploy/Bootstrap.**
Befunde und Quellenbindungen: [deployment_trigger_audit.v1.json](deployment_trigger_audit.v1.json).
Dieser Nachtrag ändert ausschließlich Dokumentation und Inventar.

## Betreiberbefunde, ausdrücklich operator_observed

| Feld | Backend | UI |
| --- | --- | --- |
| Application-UUID, ausdrücklich benannt | `syboxap8mpf8lgjzpjdsqm0z` | `a8xzljz4fq52vt1yt43nheg5` |
| Auto deploy | Manual deployments only | Manual deployments only |
| Preview Deployments, angezeigter Bestand | None | None |
| Deployment-APIeinstieg angezeigt | ja | ja |

Gespeichert wird ausschließlich das relative Muster
`/api/v1/deploy?uuid=<application_uuid>&force=false`. Keine vollständige Coolify-
URL, kein Token/Secret und kein tatsächlicher Endpointaufruf. Aus der angezeigten
URL wird auch keine geprüfte HTTPmethode oder erfolgreiche Ausführung abgeleitet.

**None ist ein Anzeige-/Bestandsbefund.** Er belegt nicht automatisch ein
abgeschaltetes Preview-Feature oder ausgeschlossene künftige Previewauslöser.
Die Applicationkennungen sind jetzt Betreiberangaben und werden nicht aus
Composeprojektnamen abgeleitet. Sourcebranch, Buildpfade und Livebindung bleiben offen.

## Zwei getrennte GitHubprüfungen

Die vier fest gepinnten Gitbäume wurden auf Workflowdefinitionen und Coolify-
Bezüge/Deploypfade untersucht, ohne Env-/Secret-/Datenbank-/Archivdateien zu lesen:

| Repository / Scope | Commit | Quellfiles geprüft | `.github/workflows` |
| --- | --- | ---: | --- |
| Backend master | `e502aa915ad0e928dbe7e92eacd44fff0152912b` | 827 | keine |
| Backend Draft #157 vor Nachtrag | `f502fed60c4e676a29752f417841d6a62a8fe458` | 846 | keine |
| UI main | `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff` | 91 | keine |
| UI Draft #20 | `6b84e3c09f877309a3fd1c6f9cbcf61bb9f46788` | 91 | keine |

Treffer wurden nach Dokumentation, Compose, Tests und Quellcode getrennt geprüft.
Kein ausführender Coolifydeployment-Aufruf wurde in diesem geprüften Quellumfang
gefunden. Der neue Readclient hat nur zwei zugelassene lesende GET-Pfade;
Deploy-URLliterale stehen in Verweigerungstests. Weitere Treffer sind Kommentare,
Compose-/Traefikdefinitionen, lokale Preflight-/Abnahmeprogramme und Dokumentation.
Ein ETL-Webhookbeispiel ist auskommentiert und kein Coolifydeploy.

Zusätzlich wurden GitHub-API-Metadaten zu registrierten Workflows und Runs gelesen:

- **Backend:** ein aktiver dynamischer Workflow `Dependency Graph`, ID `274818592`,
  Pfad `dynamic/dependabot/update-graph`. Ein historischer Run `25686254534`,
  Event `dynamic`, 11.05.2026, completed/failure, Branch master, Commit
  `986da32ca2a0675702a29a673958189731fef2ad`. Job `update-uv-graph`; Schritt
  `Run Dependabot` fehlgeschlagen. Nur Metadaten gelesen, keine Logs.
- **UI:** registrierte Workflows total_count0, Runs total_count0 bei dieser Abfrage.

Die Runs-Abfrage war auf höchstens100 Datensätze begrenzt; total_count war1
beziehungsweise0. Workflowlisten wurden mit Pagination gelesen. Der dynamische
Backendworkflow ist kein im Gitbaum konfigurierter Deploymentworkflow. Seine
Aktivität/Ausführung ist trotzdem ein eigener tatsächlicher GitHubbefund und darf
nicht durch „keine Workflowdateien“ unterschlagen werden. Die Metadaten zeigen
keinen Coolifydeployzusammenhang. Ein fehlgeschlagener Run beweist seinerseits
keine globale Nebenwirkungsfreiheit oder fehlende externe Deployausführung.

## Konfiguration, Berechtigung und Ausführung getrennt halten

| Ebene | Belegt | Weiter offen |
| --- | --- | --- |
| Konfigurierter Auslöser/Einstieg | Manual only, Previewanzeige None, Deployment-APIeinstieg; dynamischer GitHub-Dependency-Graph-Workflow | Previewfeatureflag, separate Webhooks/API-/Registry-/Schedulerwege, tatsächliche Coolify-Sourcebranchbindung |
| Berechtigung/Kontrolle | Angezeigter APIeinstieg und Actions-Metadaten benennen keine Coolifyberechtigten | Tokenabilities, Deployakteure, GitHub-App-/Webhookrechte, exklusiver Koordinator-/Wartungspfad |
| Tatsächliche Ausführung | Ein historischer fehlgeschlagener Dependency-Graph-Run; keine UI-Actions-Runs in APIantwort | Echte Coolify-/API-/Webhookausführungen und Zuordnung zu Akteur/Deployment/Container |

Keine pauschale Aussage über alle anderen Branches oder externe GitHub-Apps,
Hooks, Secret-/Runtimekonfigurationen und externe Dienste. Der tatsächlich in
Coolify gewählte Repositorybranch ist noch nicht bestätigt. Quellprüfung ist
kein Laufzeittrace und kein Nachweis, dass eine externe URL nie aufgerufen wurde.

## Konsequenz für den bestehenden Driververtrag

`additional_triggers_controlled` bleibt **unverified**, kein genehmigter
Triggerpolicy-Fingerprint wird erzeugt. Weder Manual only noch None noch ein
vorhandener APIeinstieg darf dieses Flag auf true setzen. Die bestehende
Fail-Closed-Prüfung bleibt unverändert; ohne vollständigen aktuellen Akteurs-/
Trigger-/Writer-/Intakebeleg gibt es keine Gatefreigabe. Das Previewfeatureflag
wird aus der UIanzeige nicht auf false gesetzt.

Nächste lesende Betreiberangaben betreffen die noch offenen Akteure/Wege und
wirkliche Coolify-Source-/Buildbindung, nicht erneut die bereits bestätigten
UUIDs/Manual-only-/Previewanzeigen. [Aktualisierte fünf Prüfpakete](operator_binding_check.md).
Keine produktiven API-/Webhook-Testaufrufe, Containerstarts, Jobs, Merges oder
Produktivänderungen ausgeführt. Arbeitskopien/Belege bleiben wegen Mergeverbots erhalten.
