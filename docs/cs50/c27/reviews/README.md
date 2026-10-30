# C27: aktueller Review- und Integrationsstatus (R12, 30.10.2026)

R12 setzt die in R11 entschiedene Namespace-Trennung im bestehenden dedizierten
Learning-Worktree um. Basis/HEAD: `a8af1d9372eb435d3e1331c33b047d21120d57c2`, Branch
`feat/c27-cs50-learning-pipeline`. Alle 62 R11-Ausgangsdateien wurden vor Änderungen
gegen ihre SHA-256-Nachweise geprüft. Der Index bleibt leer. Es gibt keine
Gitintegration, keinen PR und keine Produktionsfreigabe. Der Livezustand von master
bleibt REMOTE_HEAD_UNVERIFIED; der gespeicherte lokale master ist keine neue Zielbasis.

Aktuelle Bedienung: [operations_current.md](../operations_current.md).
Das [Integrationsmanifest](../integration_manifest.v2.json) bindet exakt 82 andere
Zielpfade; sich selbst lässt es ausdrücklich aus. Insgesamt sind exakt die in R11
geplanten 83 Ziele vorgesehen (C1 34 / C2 30 / C3 19). Kein Verzeichnis ist pauschal
freigegeben. Die ursprünglichen elf Learning-Pfade werden durch elf neue Zielorte
ersetzt; vorhandener Acceptance-Inhalt wird dabei nicht angelegt oder überschrieben.

## Aktuelle Entscheidungen und Prüfergebnisse

| Gate | R12-Status | Begründung |
|---|---|---|
| Namespace-Migration | PASS | Zehn Paketdateien nach src/c27_learning_summary, zentrale Suite nach tests/test_c27_learning_summary.py; direkte/dynamische Imports, Monkeypatchziele und R06-Konfigpfad umgestellt |
| Acceptance-Kompatibilität | PASS im lokalen Dateioverlay | Sechs originale Acceptance-Suiten und beide Learning-/Koexistenzsuiten: 204 PASS; abschließende Prüfung der typbereinigten neuen Tests: 5 PASS |
| Learning-Regression | PARTIAL | Namespace/Backend 57 PASS; gezielt 444 PASS, ein echter UI-Fehler wegen fehlendem Streamlit, ein bestehender UI-Modulskip; breitere Matrix siehe unten |
| Export-Sicherheit | OPEN | Elf der zwölf R07-Fälle bestanden einschließlich echtem CLI; echter UI-Downloadtest mangels Streamlit offen; 75 URLs und unveränderte historische Bytes nachgewiesen |
| Commitumfang | READY_FOR_REVIEW | Exakte 83-Pfad-Allowlist, dokumentierte Verschiebungen, Hashes und Patches; Prüfgrenzen offen ausgewiesen, kein Staging |
| Integration | BLOCKED | UI-/PDF-Validierungsvoraussetzungen fehlen; unabhängige Prüfung nach vollständiger Umgebung und gegebenenfalls genehmigtem Liveabgleich erforderlich |
| Produktion | NOT_APPROVED | Kein Release-, Betriebs- oder Fachgate ausgeführt |

Die neue Koexistenzsuite verwendet echte Acceptance-Klassen nur, wenn Acceptance
vorhanden ist. Auf dieser Basis fehlen sie. Der gesonderte Nachweis liegt in einer
gewöhnlichen Dateikopie der Learning-Basis mit exakt 32 Delta-Dateien aus lokalem
`fix/c27-acceptance-exports` (`a0d3ebf7f64d44dd843f1848e70dc70a3a3af835`, gemeinsame
Basis `e502aa915ad0e928dbe7e92eacd44fff0152912b`). Kein Gitmerge, keine neue
Arbeitsbaumregistrierung, keine Acceptance-Kopie in diesem Vorschlag. Geprüft sind
beide kalten Importreihenfolgen ohne SDK/Netz/Schreibzugriffe, getrennte Klassen,
gegenseitige Ablehnung vollständiger Catalog-/Summary-/Claim-Payloads einschließlich
v1, getrennte Stores und Cache-Reuse. Das ist kein Live-/PR-Integrationsnachweis.

Vor dem Umzug erzeugte synthetische Learning-Ergebnisse, Reviews und Exporte bleiben
mit derselben Run-ID und demselben Summary-Cachekey nutzbar, ohne neue FakeLLM-Calls.
Alle 49 ursprünglichen Testartefakte bleiben bytegleich. Die Processingrevision und
damit der Processingkey ändern sich erwartungsgemäß, weil Modulnamen und Quellbytes
eingehen. Neue Processingausgaben werden wiederverwendet; alte Verzeichnisse und
Receipts bleiben unverändert. Eigene Learning-v1/v2-Ergebnisse bleiben lesbar;
Acceptance-v1 ist keine Learning-Migrationsquelle. Keine historische Migration.

Die breitere bestehende C27-Matrix ergibt 309 PASS, 2 FAIL, 94 Setupfehler und zwei
bestehende externe Profilskips. Alle 96 PDF-Fehler melden fehlendes `pymupdf` im
begrenzten PDF-Worker; die beiden Fehler und ein repräsentativer Setupfehler wurden
auch gegen die unveränderte R11-Ausgangskopie reproduziert. Auch der UI-Fehler besteht
auf dieser Ausgangskopie. Es wurde nichts installiert, heruntergeladen oder durch
Stubs ersetzt. Die beiden externen Profilskips betreffen
`test_optional_original_python_notes_read_only` und
`test_real_operator_exports_read_only`; sie gelten nicht als erfolgreiche Prüfungen.
Der gezielte bestehende Week-0-Lesetest wurde mit seinem bereits vorhandenen lokalen
Reviewinput und FakeLLM ausgeführt; keine zusätzlichen Rohdaten oder Provider.

Ruff und Formatprüfung bestehen für alle 27 Python-Zielpfade, auch mit der lokal
vorhandenen konfigurierten Hookversion Ruff 0.16.0. Der fokussierte Mypy-Vergleich
mit identischer strikter Konfiguration/Abhängigkeitsumgebung ergibt 648 → 648 Fehler,
null neue/entfallene Diagnosen nach Namespace-/Testpfadabbildung; beide Läufe Exit 1.
Zeilenpositionen ändern sich durch Importsortierung und den zusätzlichen Legacytest.
Die historisch globalen 6.104 Diagnosen wurden nicht global neu geprüft und sind
weiterhin NOT_GREEN. Einige bestehende isolierte Testkindprozesse erzeugten
ignorierten Python-Bytecode innerhalb dieses C27-Worktrees. Diese Laufzeitcaches
sind separat inventarisiert, bleiben erhalten und gehören nicht zu den 83
Commitzielen. Andere Worktrees wurden dadurch nicht beschrieben. Vorherige 498 gesammelte Node-IDs bleiben erhalten; vier neue
kommen hinzu. Die vorhandene UI-Modulskipgrenze bleibt ausdrücklich offen. Alle
bisherigen Python-Modelle, Validatoren und Testassertions sind nach der mechanischen
Namespaceabbildung und Importsortierung AST-identisch; zusätzliche Tests ergänzen
Koexistenz und den gemeinsamen Legacy-LLM-Konstruktor-/Callback-/Cachevertrag.

## Historische Belege und Statusfolge

| Zeitraum / Ablage | Rolle |
|---|---|
| docs/lecture_summary, C26-LS-01 (28.10.2026) | Ursprung von Learning, synthetisches v1-Beispiel, alte Bedienung und Tests; keine aktuelle Namespaceanleitung |
| übrige docs/cs50/c27-Dateien vor reviews | ursprüngliche C27-Integration und Remediations R02/R04/R06/R08, jeweils mit damaligem Zustand |
| [R09](r09/c27_r09_summary.md) | unabhängiger Abschluss der R08-/CAP-Evidenzprüfung im begrenzten Learning-Exportvertrag |
| [R10](r10/c27_r10_summary.md) | historisches Inventar; dessen Integrationsvorschlag wird durch R11 präzisiert |
| [R11](r11/c27_r11_summary.md) | eingefrorenes Design und 19 Dateientscheidungen; enthält keine nachträglichen R12-Testerfolge |
| diese Übersicht / operations_current / integration_manifest.v2 | aktuelle R12-Bedienungs-, Integritäts- und Statusdokumente |

R08s damaliges BLOCKED entstand am unveränderten 5-GiB-Freiraumwächter. CAP schloss
23 konkrete Regressionen und einen frischen Canary; R09 schloss sechs exakt
identifizierte historische Fälle (6/6). Diese Gruppen werden weder addiert noch
als R12-Ergebnisse ausgegeben. R09 verifizierte F04 und die zwölf ursprünglichen
R07-Exportverletzungen innerhalb des dokumentierten Learning-Vertrags, erhielt
75 CS50-URLwerte und fand im geprüften Umfang keine F01/F02/F03/F05-/Parent-Regression.
Die R12-UI-Lücke hebt diesen historischen Abschluss nicht rückwirkend auf und
ersetzt keinen aktuellen Test. Week 0 bleibt PARTIAL, Multiweek/Multicourse bleiben
PLANNING_ONLY; F06–F14 sowie Fach-/Provider-/Budget-/Resume-/Produktionsgates bleiben.

R02s alte URLregel und R04s HTTP(S)-Regel sind historisch; maßgeblich sind heute
R08-Feldprojektion und die exakte HTTPS-Freigabeliste. R06s Scanner ist ebenfalls
historisch weiterentwickelt. SourceRef.text und Claim.text bleiben fachlicher
Freitext. R09 ist keine Exportfreigabe für Acceptance. Bereits veröffentlichte
Exporte werden weder automatisch bereinigt noch als nachträglich sicher erklärt.

15 der 19 Reviewdateien bleiben exakt unveränderte historische Belege. Die vier
anderen Entscheidungen sind drei Namespace-/Testpfadverschiebungen und die folgende
begrenzte Markdownableitung. Insgesamt bleiben 29 von 30 alten Dokumentdateien und
alle 16 selektiv archivierten R09/R10/R11-Berichte bytegleich.

`docs/lecture_summary/example-summary.json` bleibt das synthetische historische
v1-Exportbeispiel und die Kompatibilitätsfixture, kein aktuelles R08-Exportmuster.
Seine sieben Referenzen verwenden drei mitgelieferte relative synthetische
Fixturequellen. Diese Quellenidentitäten sind nach R08 erlaubt und bleiben erhalten;
synthetisches approved beweist keine Kursfachabnahme.

`docs/lecture_summary/example-summary.md` ist die offen deklarierte Ableitung:
exakt ein abschließendes ASCII-Leerzeichen in Originalzeilen 159–164 entfernt,
sonst unverändert, insbesondere weiterhin ohne finales LF. Original-SHA-256:
`2e3f2f6ce4c288a8540b47e464ba6f557dde43da75501b5094b789aaf500a7cf`.
Ziel-SHA-256:
`4e5113bcef01b19fa7f90e74ed19fa7a90087f1d2b04defd3de14a570b4880cd`.
Originalbytes bleiben in den bestehenden externen Handoffs und im R12-Ausgangssnapshot;
keine Neugenerierung und keine Änderung von Ref-/Reviewhashes.

Nur end-of-file-fixer bekommt drei verankerte exakte Ausnahmen:
`docs/lecture_summary/example-summary.json`,
`docs/lecture_summary/example-summary.md` und
`tests/fixtures/lecture_summary/sources/transcript.json`.
Alle anderen Hookeinträge einschließlich trailing-whitespace und JSONsyntaxprüfung
bleiben unverändert aktiv. Keine allgemeine Hookdeaktivierung oder Skipumgebung.

Historische lokale Home-/tmp-Pfade bleiben bewusst als nicht geheime Orts- und
Laufprovenienz erhalten (R11 P01), relative synthetische Fixtureidentitäten nach
S01 ebenfalls. Pfadexistenz, Portabilität und damalige Autorisierung werden dadurch
nicht erneut zugesichert. R08s ursprünglicher Ort `/tmp/c27-remediation-r08.xqBDn5MQ`
ist historischer Alias der bereitgestellten Sicherung
`~/codex-logs/c27rollout/handoff/remediation-r08.YyLgkxTm/`.
Die archivierten Berichte verweisen teilweise auf private externe Evidenzpakete;
diese sind keine vollständig mitgelieferten Repositoryartefakte.

`docs/lecture_summary/handoff-files.json` (27 frühere Dateien) und
`docs/cs50/c27/handoff-files.v1.json` (50 frühere Dateien) bleiben unveränderte
historische Hashmanifeste. Sie binden alte Bytes und sind kein aktueller Integritätsnachweis.
Nur das neue Integrationsmanifest beschreibt die aktuelle 83-Pfad-Auswahl.

## Handoff, Retention und noch ausstehende Integration

R12-Evidenz liegt außerhalb des Worktrees unter
`/tmp/c27-r12-20261030-namespace/`: sieben Pflichtartefakte, vollständige Zielinventare,
R11-Delta-/Basispatch, SHA-256, exakte Testbefehle/Umgebung, unveränderte JUnitlogs,
Namespace-/Persistenznachweise, Schutzvergleich und ein Backupverfahren.
Der bevorzugte Home-Handoffpfad ist in dieser Sitzung nicht beschreibbar.
`/tmp` ist kein dauerhaftes Backup; die Sicherung nach
`~/codex-logs/c27rollout/handoff/remediation-r12/` muss durch einen schreibberechtigten
Operator erfolgen. `backup.sh` kopiert ohne Überschreiben und prüft die Paketchecksummen.

Staging, Commit, Push, Fetch, Rebase, Merge, Cherry-Pick und PR sind in R12 ausdrücklich
nicht autorisiert und wurden nicht ausgeführt. Die Dokumente liegen daher noch nicht
im tatsächlichen Defaultbranch master. Der AGENTS.md-Integrationslebenszyklus bleibt
PENDING. Keine neuen Git-Artefakte erstellt; der vorbestehende Branch/Worktree und alle
anderen Worktrees, Referenzen, Rohdaten und historischen Handoffs bleiben erhalten.
Nach vollständiger Umgebung die offenen Originaltests unverändert ausführen und
unabhängig reviewen. Erst ein gesondert autorisierter regulärer PR-/Reviewprozess
kann die Dokumente und Produktänderungen integrieren. Keine Cleanupfreigabe für
MAINT-Bestände oder vorbestehende Artefakte folgt aus R12.
