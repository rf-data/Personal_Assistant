# C27-R18 – CI-Readiness

## Integrität und Konflikte

AGENTS.md im C27-Worktree und die übergeordnete Datei wurden gelesen. Auftragsspezifisch ausschließlich externe Vorbereitung; keine Default-Branch-Integration und keine Commits. `input_verification.json` enthält alle sechs R12–R17-Manifeste samt Manifesthashes sowie den Vergleich mit R17-Staging und dem R12-Overlay. Alle Einträge stimmen. `worktree_before.json` sichert HEAD, Branch, Indexhash, Status, Diff und Worktree-Inventar. Abschlussvergleich steht in `final_verification.json`.

1117 R16-Inputdateien stimmen in Größe und SHA-256. Die 75 unversionierten Inputdateien entsprechen exakt R17/git_coverage; 4 weitere historische Berichte stimmen mit R12. 1042 Inputdateien sind bereits versioniert, davon 4 geändert; 1038 bleiben ohne Staging. Die 32 Acceptance-Dateien bleiben unter ci/c27-r18/acceptance-overlay isoliert. Insbesondere src/runtime_paths.py und src/tools_materials/storage.py werden im Learning-Checkout nicht überschrieben. Nur eine spätere wegwerfbare Acceptance-Kopie bekommt die beiden erklärten Ersetzungen; danach 1147 Dateien.

`target_conflicts.json` prüft jeden neuen Payloadpfad gegen den aktuellen C27-Worktree, einschließlich Symlink-/Datei-Ahnen. Keine Kollision. Die sieben Dokumentationsziele werden gesondert im Inventar aufgeführt. Das Ergebnis autorisiert noch keine Übernahme. Keine Datei im bestehenden C27-Worktree wurde ergänzt.

## Workflow und Änderungen an R17

Ziel: `.github/workflows/c27-r18.yml`. Einziger Trigger workflow_dispatch; kein push, pull_request_target, schedule oder workflow_run. Checkout verwendet github.sha, shallow, ohne persistierte Credentials, Submodule oder LFS. Der Job akzeptiert nur rf-data/Personal_Assistant und refs/heads/c27-ci/r18-first-run. Ein fremder Fork oder master bekommt keine Testausführung. Berechtigung ausschließlich contents:read; alle anderen Repositorytokenrechte implizit none. Checkout/Artefakttransport verwenden technisch GitHubs kurzlebige Runner-Authentisierung; sie wird keinem Testcontainer mitgegeben. Keine vom Nutzer angelegten Secrets oder produktiven Credentials.

Die festen R17-SHAs von actions/checkout und actions/upload-artifact wurden über deren offizielle action.yml rein lesend geprüft. Eingaben existieren. YAML BaseLoader, Struktur-/Kontextkontrolle und bash -n bestehen. actionlint ist nicht verfügbar und wurde nicht installiert. Eine vollständige actionlint-/GitHub-Schemavalidierung ist weiterhin NICHT erfolgt; YAML-Parsing ist kein Ersatz. Der Plattform-Akzeptanztest muss vor dem Erstlauf separat erfolgen.

Matrix PDF_PROFILE / UI_PROFILE / NAMESPACE_INTEGRATION, max-parallel 1, fail-fast false. Workflowweiter Concurrency-Schlüssel; keine automatische Wiederholung. 75 Minuten pro Job: Pull bis 5, Fetch bis 10, Installation bis 10, Namespace maximal 2 × (3 Collection + 15 Ausführung) = 36 Minuten; zusammen 61 Minuten plus Vorbereitung/Uploads. Die R17-Grenze 55 Minuten wurde wegen der zusätzlichen getrennten Phase angepasst.

Wesentliche Korrektur: Docker entfernt tmpfs-Inhalte beim Stoppen. R17s anschließendes docker cp konnte so seine JUnit-Berichte verlieren. R18 nutzt einen frischen dedizierten Ergebnis-Bind-Mount; docker cp übernimmt dessen Inhalte mit Operatorbesitz. /input, /plan, /opt/venv und Root-Dateisystem der Tests bleiben read-only. /work und /tmp bleiben tmpfs. Jeder Testcontainer hat explizites Arbeitsverzeichnis /input und nutzt /opt/venv/bin/python. Das dedizierte nichtgeheime Evidenzverzeichnis ist für den Host-Watchdog lesbar (0755); Arbeitsverzeichnisse bleiben 0700.

Quelle: [Docker tmpfs](https://docs.docker.com/engine/storage/tmpfs/), [Docker cp](https://docs.docker.com/reference/cli/docker/container/cp/). Container- und Kopierverhalten müssen im autorisierten Erstlauf bestätigt werden.

R17s Legacybuilder wird vollständig vermieden. Kein Dockerfile, BuildKit oder Dockerbuild ist nötig. Das geprüfte Pythonbasisimage wird explizit bezogen; danach ausschließlich --pull never. Netzwerkfähiger Beschaffungscontainer verarbeitet nur die festgelegten Wheel-URLs, weder Produktcode noch private Rohdaten. Ein frischer Container installiert die vollständige Closure aus dem Wheelhouse mit --network none, --no-index, --no-deps, --only-binary und --require-hashes, anschließend pip check. Testcontainer sind ebenfalls --network none.

## Sicherheits- und Ergebnisprüfung

Jeder Testcontainer: UID/GID 10001, capabilities ALL entfernt, no-new-privileges, 2 CPUs, 4 GiB RAM, kein zusätzlicher Swap, 256 PIDs, 64 MiB shm, FD-Limit 1024, Dateigröße 128 MiB. Docker HostConfig wird vor Start geprüft und als security-report.json geschrieben. Der Runner prüft cgroup v2 zusätzlich. Kein Docker-Socket, Hosthome, .env, Credentialverzeichnis oder Hostumgebung im Testcontainer. Source/Plan als Allowlistkopien, readonly. Der bestehende tests.offline_guard und Pluginpolitik bleiben aktiv.

Hostaufnahme: 2 CPUs, 7 GiB RAM, 10 GiB freie Disk; Reserve 6 GiB, Prüfung alle 2 Sekunden. Ergebnis-Bind-Mount: 128 MiB weiche Überwachung, keine harte Gesamtdiskquote; Einzeldatei-Limit bleibt hart. Logs 32 MiB plus begrenztes Dockerlogging. Ein abrupt beendeter Runner kann Artefaktupload verhindern; fehlende Evidenz ist INCOMPLETE. Beschaffung hat eine URL-Allowlist im überprüften Helfer, keine Kernel-Egress-Allowlist; der netzfähige Beschaffungsprozess darf keine Anwendung importieren. Tests/Installation haben dagegen echte Netzwerk-Namespace-Isolation.

105 offene Fälle bleiben exakt 96 PDF + 9 UI. Die 3+4 Koexistenzfälle werden separat ausgewiesen, nicht als zusätzliche offene Fälle oder als 112 eindeutige Tests. Die R16-ID-Arrays sind bytegleich manifestiert; R17s statische AST-Prüfung wurde übernommen. Vor Ausführung muss echte Collection exakt stimmen. Setup/call/teardown je ID genau einmal passed; Skip, xfail/xpass, OOM, Timeout und fehlendes XML blockieren.

always()-Summary und Artefaktupload pro Profil, sieben Tage Retention, eindeutiger Name mit Run-ID und Versuch. Enthalten: JUnit, collected.json, outcomes.json, command.json, Containerstatus, security-report.json, Ressourcen, Installationsbericht, Wheelhashes, Paketversionen und Jobidentität. Artefakt-SHA256SUMS werden vor Upload erzeugt und vom Vergleichshelfer geprüft. Kein Upload von Quelldateien oder privaten Daten. `compare_results.py` prüft die tatsächlichen Call-IDs und getrennt Namespace, Run-ID, Versuch, SHA und JUnit. Sicherheitsberichte sind Konfigurations-/Ressourcennachweise, kein CVE-Scan.

## Erstlaufblocker

GitHub verlangt workflow_dispatch auf dem Default-Branch. Deshalb muss ausschließlich dieser Workflow in einem separaten regulär geprüften Bootstrap auf master registriert werden; keine ausführbaren Trigger auf master, und sein Jobguard lässt dort keine Testausführung zu. Der eigentliche Testcode bleibt im isolierten Testbranch. Diese Integration ist außerhalb R18 ausdrücklich verboten und wird hier nur geplant. Ohne Bootstrap kann ein gh workflow run --ref allein das Problem nicht lösen.

Neun ausschließlich synthetische lokale Helferprüfungen bestehen: vollständige künstliche Evidenz, Abweisung von Skip, Duplikat, fehlender ID, altem SHA, leerem JUnit und Hashabweichung sowie künstliche Wheelmetadaten-/Korruptionsprüfung. Weder Produktcode noch pytest, Docker, Netzwerk oder Installationsfunktionen wurden dabei ausgeführt. Details in synthetic_helper_checks.json.

Zusätzlich: geprüfter Pythonimage-Digest fehlt, tatsächliche Runner-/cgroupfähigkeit nicht gemessen, volle Schemavalidierung offen, Commit-/Datenschutzprüfung und separate Freigaben ausstehend.

[GitHub Workflowsyntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [Manueller Start und Default-Branch-Voraussetzung](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
