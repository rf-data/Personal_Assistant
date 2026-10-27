> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Integrationsplan und Entscheidungen

25.10.2026. **HOLD.** Vor umfangreichen Codeänderungen erstellt.

1. Saubere H-Basis, lokale/Tracking-/Liveheads und G-Dateistand inventarisieren. Keine anderen Arbeitsbäume verändern. G-Dateien mit SHA256 erfassen.
2. Einmaliger kumulativer F-Diff vom gemeinsamen Vorfahren e682752 nach 7ffb4ed: 91 geprüfte Pfade, keine Überschneidung mit den MAINT-Codeänderungen der H-Basis. Erst git apply --check, dann reine Quellübernahme ohne Index/Refänderung. Keine Cherry-pick-Serie mit geerbten Duplikaten. Zehn G-Dateien byteidentisch übernehmen.
3. Unveränderten D/E/F/G/C16-Verbund mit Offlineguard als Integrationsbaseline testen; Exitcodeabweichung nicht als erledigt einstufen. Neue Launcherregressionen vor Produktivänderung ausführen.
4. Managed scripts.deployment um explizite API-/check-Argumente für bestehende Content-/Review-/Search-Loader erweitern. Review/Content müssen dieselbe Bindung haben; Search braucht Content. Bestehenden Wartungslock und Application verwenden, keine neuen Services. Legacyaufrufe bleiben opt-in ohne Fachfunktionen.
5. Separates H-Stagingtemplate mit v2-Pflicht, deaktivierten Flags und zusätzlichem Laufzeitvertrag. F-/G-Historie nicht umschreiben. H-Prüfer validiert effektives Compose ohne Containerstart, Mounts, Rollen, Limits, Image-Digests und deaktivierte Fachsettings. Externe Keys nur als Pfadreferenzen; keine Secretbytes im Repo.
6. Reproduzierbarer H-Offline-Runner prüft tatsächliche integrierte Quellen, Launcher, negative Konfiguration/Auth, Collector→Offline-Trennlinie, Coordinator/Gate, Crash/Wiederanlauf, Verbundrestore und Rollback. Nur neue Tempwurzeln, kein Dockerstart. Echte Compose-config-Auswertung separat und ausschließlich synthetisch.
7. Relevante Persistenz-/HTTP-/C16-Regression, breite Offlineauswahl soweit sinnvoll, Ruff/Format. Jede Bilanz separat mit skips/deselected/not-run. Fehlgeschlagene Nodes auf unveränderter Basiskopie vergleichen; keine pauschalen Retries/Timeout-/Assertionlockerungen.
8. Sechs H-Berichte finalisieren. Vollständiger Patch einschließlich neuer Dateien und Manifest, Forward/Reverse-Checks und Bytevergleich auf frischer Basis. Gemeinsames Git read-only nachgewiesen durch git add --dry-run (index.lock: Read-only file system); kein Umgehungsindex, Commit, Push, PR-Mutation oder Merge. Zielcommit bleibt Basis; Kandidat über Patchhash/Dateimanifest identifizieren.

## Bewusste Grenzen

Authentifizierte Captures werden nicht in synthetische Gatebeweise umetikettiert. D/F bleiben offline_fixture mit lokalem Testwitness und inertem Driver. Produktiver EvaluationStore-Verbundadapter, Producer/Registrytrust, unabhängiger Witness, Live-Driver und Betreiberfreigaben bleiben Gates. Produktionsstatus HOLD.

MAINT-03B/04B: SQLite-Locks, Guardian-Quarantäne, Exit 3 und Hardlink-Crashfenster bleiben unterscheidbare offene Befunde. Keine Quarantäne entfernen, keine Sicherheitsassertion lockern, keine optionalen SDKs nachinstallieren. Vorhandene Interpreter ausschließlich lesend, keine parallelen Prozesslastsuiten.

Kein automatischer Merge und keine Löschung sind in diesem Auftrag erlaubt. AGENTS.md-Defaultintegration bleibt pending; Branch und Worktree sind zu erhalten.

## Ergänzungen der Fortsetzung

- P1 erhält nach deterministischem Basis-/H-Nachweis ausschließlich einen
  Readinesshandshake der Testprobe; keine andere Signal-/Timeout-/Produktpolicy.
- P2 bleibt trotz erfolgreicher Einzel-/Gruppenprüfung kausal offen.
- `--broad-only` prüft die noch offenen Offlinekomponenten ohne erneuten
  vollständigen 594er-Basislauf. Monitoring benötigt echten Gitindex und wird
  ausdrücklich separat lesend im H-Worktree geprüft, kein künstlicher Index.
- Sieben neue native H-Composechecks sind explizit External und ausschließlich
  `config`; weder Daemonkontakt noch Containerstart.
- Endstand, tatsächliche rote Vorläufe und Nachweise sind in der
  [Validierung](c26h_validation.md) festgehalten. Alle ursprünglichen Grenzen
  dieses Plans bleiben bestehen.
