> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Übergabe und isoliertes Staging

25.10.2026. **Vorbereitung, Produktionsstatus HOLD.**
Hier genannte spätere Betreiberaktionen wurden nicht ausgeführt. Für Server,
Ressourcen, Start oder Mutation ist ein eigener genehmigter Auftrag erforderlich.
Pflichtentscheidungen: [Verbleibende Gates](c26h_remaining_gates.md).

## Lokal reproduzieren

Im Repository mit einem bereits passenden Python3.12-Interpreter, ohne Installation:

```sh
C26H_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python
PYTHONDONTWRITEBYTECODE=1 "$C26H_PYTHON" -B -m scripts.c26h_offline_validation --integration-only
PYTHONDONTWRITEBYTECODE=1 "$C26H_PYTHON" -B -m scripts.c26h_offline_validation --broad-only
```

Der erste Befehl selektiert G/H-Konfiguration, Restore, Launcher, die gemeinsame
Collector-/Gate-/Coordinator-/Rollbackgrenze und die neuen Slow-start-Probes.
Der zweite selektiert nur die ergänzenden Offlinekomponenten, um den bereits
belegten D/E/F/C16-Basislauf nicht unnötig zu wiederholen. Ohne Auswahlflag startet
der Runner den vollständigen D/E/F/G/H-Vertragsumfang; `--broad` ergänzt diesen
um die breiteren Regressionen. Keine Ergebniszahlen verschiedener Läufe addieren.

Der Runner exportiert die tatsächliche H-Arbeitsdateifassung einschließlich neuer
Dateien auf Basis von `git archive HEAD`, schreibt einen vollständigen SHA-256-
Quellmanifest und legt Daten getrennt unter einer neuen `/tmp/c26h-offline-*`-Wurzel
an. Keine Index-/Refänderung. Er deaktiviert Autoloadplugins/Bytecode/Cachewrites
und sperrt Netzwerk/Listener und direkte Infrastrukturprozesse im Pytestprozess.
Das ist kein transitiver Betriebssystem-Sandboxersatz; bestehende Childprobes
verwenden synthetische Daten und kontrollierte lokale Adapter.

Git-Monitoringverträge benötigen echte `ls-files`-/`check-ignore`-Metadaten und
werden separat im zugewiesenen H-Worktree gelesen. Native H-Composechecks sind ein
expliziter, ausschließlich auf `config` begrenzter Teil des Externalprofils:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$C26H_PYTHON" -B -m pytest -q -o addopts= -p no:cacheprovider \
  -p tests.offline_guard tests/test_monitoring_config.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$C26H_PYTHON" -B -m pytest -q -o addopts= -p no:cacheprovider \
  --run-external tests/test_c26h_compose.py
```

Die Composefixture benutzt isoliertes `DOCKER_CONFIG`, ein nicht vorhandenes
Unix-Daemonsocket, synthetische Digests/Roots und `/dev/null` als Envdatei.
Sie startet keinen Container und zieht kein Image. Coolifyrouterlabels werden
explizit nur als synthetische Fixture bereitgestellt. Diese Prüfung belegt CLI-
Rendering und die H-Prüferkopplung, keine echte Coolify-/Ingressabnahme.

Die konkrete Baseline und tatsächlich ausgeführten Teilmengen stehen in der
[Validierung](c26h_validation.md). Ein direkter Dateiaufruf des H-Runners ohne
Repositoryimportpfad scheiterte vor Sammlung; reproduzierbarer Einstieg ist
`python -m scripts.c26h_offline_validation`.

## Manuelle Gitübergabe außerhalb der schreibgeschützten Sandbox

Diese Schritte sind ausschließlich für einen später autorisierten Bearbeiter;
hier wurden weder Branch noch Index geändert. Paket: `/tmp/c26h-delivery/`,
Manifest mit Basis, vollständiger Dateiliste, Hashes und Prüfverfahren.

1. Paket/Patchhash und sämtliche Arbeitsdateihashes prüfen. Ausgangsbasis muss
   `778367396cd52526eca59edd41c2367f5e43b897` sein; nicht einen vermeintlich bereits
   integrierten H-Commit voraussetzen. Zehn G-Dateien sind lokale Quellen ohne G-Commit.
2. Aktuellen Default-/PR-/Reviewzustand neu lesen. Lokale `master`-/Trackingrefs
   sind veraltet; frühere Livebeobachtung ist kein heutiger Integrationsbeleg.
3. In einer neuen ausdrücklich autorisierten Reviewkopie auf exakter Patchbasis
   arbeiten, beispielsweise mit einem neuen Branch `review/c26h-integration`.
   Bestehende H-/G-/D/E/F-/C27-Branches und Arbeitsbäume nicht umschreiben.
4. Patch zunächst prüfen, dann anwenden, vollständige Hashes vergleichen und
   ausschließlich die expliziten Paketpfade stagen:

```sh
git apply --check /path/to/c26h-delivery/c26h-controlled-integration.patch
git apply /path/to/c26h-delivery/c26h-controlled-integration.patch
git diff --check
git add --pathspec-from-file=/path/to/c26h-delivery/paths0 --pathspec-file-nul
git diff --cached --stat
git commit -m "Integrate C26 offline contracts and controlled staging bindings"
```

5. Erst nach gesondert zulässigem Veröffentlichungsweg den neuen Reviewbranch
   pushen und einen neuen Draft-PR erstellen; bestehende Drafts nicht ändern.
   PR-Inhalt aus Datei übergeben, z.B. `gh pr create --draft --base master
   --head review/c26h-integration --body-file /path/to/review-description.md`.
   Gegen den dann tatsächlichen Zielbranch Konflikte und Tests neu reviewen.
6. Keine Merges in diesem Auftrag. Erforderliche Reviews/CI und Betreiberentscheidungen
   abwarten. Bei später zulässiger Integration tatsächliche Inhalte aller sechs
   Berichte und sämtlicher vorgesehenen Änderungen in `master` verifizieren.
   Offener PR oder gleiche Patch-/Commit-ID allein genügt nicht.
7. Bestehenden H-Worktree und Branch erhalten. Keine automatische Bereinigung
   vor Integration und keine Löschung fremder/älterer Worktrees oder Stashes.

## Nächster isolierter Hetzner-Versuch, erst nach separatem Mandat

1. Einen ausdrücklich nicht produktiven Host/Scope samt Budget und Rettungsweg
   festlegen; neue Namen für Projekte, Netze und persistente Roots vergeben.
   Keine bestehenden Coolifyressourcen oder produktiven Trigger wiederverwenden.
2. Exakte reviewte Backend-/Gateway-/UIimages und deren Buildbelege außerhalb
   dieses Auftrags bereitstellen. Root-/Mount-/UID-/Quota-/Writerinventur und
   Netzwerk-/TLS-/IdP-Plan privat dokumentieren. Keine Secrets ins Repository.
3. Die Beispielsettings an neue Stagingroots binden, sämtliche Ausführungsflags
   zunächst false lassen, Identitäten/Kataloge leer halten. Private Configdateien
   und Cursor-Key extern mit passender UID und privaten Modi bereitstellen.
4. Backend aus `coolify.runtime-bootstrap.compose.yaml` plus H-Overlay und UI aus
   `coolify.ui.compose.yaml` plus Private-HTTPS- und H-UI-Overlay rendern. Effektive
   JSONmodelle redigiert aufbewahren und mit `scripts.c26h_preflight` prüfen.
   Keine profillose Konfiguration darf Rollen auswählen. Echte Coolifylabels
   dürfen nicht durch die synthetische Testfixture ersetzt werden.
5. Kaltprovisionierung von Queue/v2-Journal getrennt reviewen. Der initiale
   Gatestatus muss held sein; Prüfer/Startup dürfen fehlende Queues/Journale
   nicht automatisch öffnen oder migrieren. Ein leerer readonly Bootstrap ist
   noch keine funktionale Worker-/Fachabnahme.
6. Erst nach erneuter gezielter Startgenehmigung begrenzte Stagingrollen starten.
   Zunächst echte TLS-/Origin-/OIDC-/Rollen-/Widerrufs- und Mount-/Singleton-
   Negative prüfen. Synthetische Jobs nur mit eigens freigegebenem Stagingscope;
   P2-Zeiten phasenbezogen messen, keine pauschalen Timeoutänderungen.
7. Gestoppte konsistente Backup-/Restore-/Rollbackprobe in neuen Roots samt
   Ledger-/Blob-/Hash-/ACL-/Idempotenznachweisen und echter Alarmzustellung
   abnehmen. Unknown, Quarantäne oder unbestätigter Cleanup bleiben HOLD.
8. Ergebnis mit Scope, Datum, SHAs/Digests und benanntem Operator reviewen.
   Ein isoliertes Staging-GO ist weiterhin keine Produktionsfreigabe und kein
   Ersatz für den fehlenden produktiven Witness-/Verifier-/Driververtrag.
