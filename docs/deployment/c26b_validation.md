# C26-B – Ausführungs- und Freigabebeleg

20.10.2026. Status `https_deployment_prepared`, `production_release_blocked`.
Noch keine Produktionsfreigabe, kein Hetzner-/SSH-/DNS-/ACME-/Port-/Datenzugriff.
[Betreiberhandbuch, Schritte und Rollback](https.md).

## Implementierung

B1: ausschließlich UI-Compose mit beiden Coolify-Zugangsprofilen, erforderlichen
Digest-/Secret-/Netzwerkparametern und Offline-Audit des finalen Coolify-Exports.
B2 im UI-Repository: Authlib im offiziellen Streamlit-auth-Extra, sichere
Produktionsstartverweigerung, begrenzte Claims-Sessions, Cookie-/Host-/Origin-/
Proxyprüfung in derselben kanonischen Admin-App und authentifizierte Readiness.
B3: ausführbarer lokaler Browser-/OIDC-/TLS-/Traefik-/C16-/FTS-/Restart-Test,
gezielte Securitytests und das ergänzte bestehende Betriebshandbuch.

Keine produktive Backendmodul-, Queue-, Worker-, Datenmodell- oder Proxyarchitektur-
Änderung. Der lokale Testserver ist eine isolierte Acceptancehilfe, keine
produktionsfähige zusätzliche Anwendung. Er verwendet bestehende synthetische
Fixtures und den tatsächlichen Handler/Executor.

## Bisher ausgeführte Prüfungen

- Tatsächliche Docker-Compose-CLI: beide Profile rendern; 17 unsichere Mutationen
  und fehlende Pflichtwerte werden abgewiesen. **20 passed**.
- UI-Start-/Secretsuite **9 passed**, neue HTTPS-/OIDC-Claimsuite **7 passed**.
- Bestehende Backendregression plus neue Konfigurationstests: **173 passed,
  2 failed / 175** in 437,36 s. SQLite-Lock im Resume-Normalized-Fall bestand bei
  gezieltem Wiederholungslauf; Schemasnapshot bleibt abweichend. Vergleich mit
  unverändertem master und Nachprüfung sind getrennt protokolliert, kein grüner
  Gesamtstatus wird behauptet.
- Bestehende UI-Gesamtsuite: 171 Testmethoden, fünf Error-Einträge in drei
  Workflow-Testmethoden, weil der vorhandene E2E-Treiber einen sauberen
  Backendcheckout verlangt. Kein fachlicher Erfolg für diese Fälle behauptet;
  gezielte Wiederholung nach dem vorbereitenden Commit folgt.
- UI-Dockerbuild aus verifizierten Python-/uv-Manifestdigests tatsächlich lokal
  ausgeführt. Ein abschließender Build mit der endgültigen Revision folgt.
- Browser-E2E-Treiber wird lokal mit echtem Traefik v3.6 und temporärem IdP geprüft;
  bislang kein erfolgreicher Gesamt-E2E behauptet. Zwischenfehler im Treiber
  (unprivilegierte Testports, JWK-Erzeugung, SNI, Traefik-Dateiformat) wurden
  korrigiert; tatsächliche Abschlussresultate folgen als Nachtrag.

## Ausstehende Hostabnahme (`not_tested`)

Coolify 4.4.2 auf Hetzner, tatsächliche Containerrolle/Revision/Netzmitglieder,
vorhandener authentifizierter API-TLS-Endpunkt, gewählter IdP und seine Claims,
Browser-Vertrauensspeicher, echtes VPN/CIDRs, DNS/ACME/Erneuerung, globales
Proxylog-Redacting, Alarmzustellung, Zielhostlimits/OOM, Backup-/Restore und
Rollback der echten Route. Keine `production_approved`-Vergabe.

## Git-/Reviewstand

Eigene Worktrees `Personal_Assistant-c26b` und `personal-assistant-ui-c26b`, jeweils
Branch `feat/c26b-https`; bestehende primäre Checkouts und MAINT-Artefakte bleiben
unberührt. Zwei zugeordnete Review-PRs sind vorgesehen, keine automatischen Merges.
Dokumente verbleiben bis Review in diesen PRs und sind noch nicht in master/main
integriert. Deshalb bleiben Branches/Worktrees erhalten; Lebenszyklusabschluss
und Produktivfreigabe stehen aus. Siehe das führende Handbuch für alle noch
notwendigen Betreiberentscheidungen und die exakten späteren Coolify-Schritte.
