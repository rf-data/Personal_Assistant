# C27-R11 – Gateentscheidungen

| Gate | Entscheidung | Konkrete Grundlage |
|---|---|---|
| REVIEW_REQUIRED-Dateien | **RESOLVED** | 19/19 individuelle Inhalt-/Zweck-/Abschnittsentscheidungen; 15 KEEP_AS_HISTORICAL_EVIDENCE, vier INCLUDE_AFTER_CHANGE. Keine ungeklärte I01/P01/S01/W01-Empfehlung. |
| Konfliktdesign | **COMPLETE** | Alle drei tatsächlichen Pfade gegen Worktree, fix und origin/master verglichen; getrennte Namespaces/Modellfamilien, kein stiller Ersatz; APIs, Risiken, Tests und konkrete Änderungszuordnung dokumentiert. |
| Commitumfang | **DEFINED** | 62 Quellen → 62 Zielpfade plus 21 ausdrücklich geplante Zusätze = 83; 21 exakte Pfadausschlüsse und ausgeschlossene Original-MD-Byteversion erklärt. |
| Integrationsvorbereitung | **READY_FOR_IMPLEMENTATION_APPROVAL** | Prüffähiger Entwurf mit drei Commits, aktueller Dokumentation, Offlinevalidierung, Review und Revertstrategie. Das ist eine Empfehlung zur Freigabe der späteren Arbeit. |
| Produktion | **NOT_APPROVED** | Kein Produkt-/Release-/Betriebs-/Restoregate beauftragt oder ausgeführt. |
| Live-Zielbranch | **REMOTE_HEAD_UNVERIFIED** | Kein Netzwerk/Fetch; a8af1d9 ist allein gespeicherter origin/master. Lokaler master ist 173 Commits zurück. |
| Implementierung / Gitintegration | **NOT_EXECUTED; NOT_AUTHORIZED_BY_R11** | Kein Repositoryinhalt verändert, kein Index/Ref/Branch/Worktree mutiert, kein PR erstellt. |
| Erneute Produkttests | **NOT_RUN_BY_DESIGN** | Nur Scope-/Integrationsanalyse; keine neuen Produktbytes. Neue gezielte Tests sind Teil des späteren Plans. |
| Historische technische Evidenz | **INHERITED_WITH_SCOPE** | CAP 23/23 plus frischer Canary; R09 sechs exakte historische Fälle 6/6. Keine Addition und keine Übertragung auf noch nicht erzeugte Namespacebytes oder Acceptance. |
| Globale Typprüfung | **NOT_GREEN (historisch)** | 6.104 Diagnosen aus R09 übernommen; kein neuer globaler Lauf. |
| Week 0 / Multiweek / Multicourse | **PARTIAL / PLANNING_ONLY** | Bestehende F06–F14-Grenzen bleiben, insbesondere vollständiges HTML, ZIPmapping, Fachreview und Budget/Resume. |
| Dauerhafte Defaultbranch-Dokumentation | **PENDING** | Auftragsverbot hat Vorrang; die 16 geplanten Reviewkopien und aktuellen Abschlussdokumente müssen später regulär nach master integriert werden. |
| Retention / Cleanup | **RETAIN_REQUIRED** | Keine eigenen Git-Artefakte erstellt; bestehender schmutziger Learning-Worktree, alle fremden/MAINT-Branches und Handoffs erhalten. /tmp-Paket bleibt zur gesonderten dauerhaften Sicherung erhalten. |

## Aufgelöste R10-Entscheidungen

**I01:** Learning als eigener src.c27_learning_summary-Vertrag; Acceptance bleibt getrennt. Kein Vollmerge der fix-Fortsetzung und keine Pflicht, diese vor Learning zu integrieren. Wer eine gemeinsame API wünscht, braucht einen eigenen ausdrücklich beauftragten Migrationsentwurf.

**P01:** Die geprüften lokalen Home-/tmp-Pfade in den 14 historischen Reviewdateien empfehlen wir bewusst als nicht geheime Orts-/Laufprovenienz zu erhalten. Keine tatsächlichen Zugangsdaten identifiziert. Sie sind weder portable Bedienungsbefehle noch aktuelle Pfadexistenz- oder Ausführungserlaubnis. Die später mitaufzunehmenden vier R09-Berichte und sechs R10-Berichte haben dieselbe historische Rolle; ihre lokalen Befehle und externen Verweise bleiben im neuen Index so eingeordnet. Ganze private Belegpakete bleiben außerhalb von Git. Keine pauschale Freigabe aller lokalen Pfade oder beliebiger Quelltexte.

**S01:** Die drei synthetischen Fixturequellpfade in sieben Referenzeinträgen des JSON und den Sourceabschnitten des Markdown sind zulässige relative Identitäten nach R08. Kein fachlicher Freigabenachweis; v1-JSON bleibt historische Migrationsfixture, nicht aktuelles Exportbeispiel. Keine Neugenerierung mit veränderten Ref-/Reviewhashes.

**W01:** Neue veröffentlichte Markdownableitung entfernt exakt sechs bekannte Schlussleerzeichen; Originalversion bleibt extern unverändert. Vorher-/vorhergesagter Nachherhash und sechs Zeilen stehen in evidence/planned_example_normalization.json; Ausführung erst später. Historische Manifeste nicht an die Ableitung anpassen.

**C3:** Vier R09-, sechs R10- und sechs R11-Berichte exakt benannt archivieren; aktuelle Reviewübersicht, Bedienung und finales Integrationsmanifest zusätzlich anlegen. Ignoreausnahmen nur für die vier neuen Dokument-JSONziele, separat zu den neuen Paket-/bisherigen Fixtureausnahmen. Private Evidenz wird nicht als im Repository mitgeliefert behauptet.

## Verbleibende Ausführungsvoraussetzungen, keine offenen Designentscheidungen

Eine spätere ausdrückliche Implementierungsfreigabe muss Namespace-/Publikationswahl und Scope bestätigen. Danach sind tatsächliche Zielbasis, Schutz-/Reviewregeln, neue Dateibytes und zielbezogene Tests zu prüfen. Unbekannter Livezustand ist eine Ausführungsvoraussetzung und kein Anlass, in diesem netzfreien Entwurfsauftrag Tatsachen zu erfinden. Weicht die neue Basis ab, betroffenen Plan präzise aktualisieren. Aus READY_FOR_IMPLEMENTATION_APPROVAL folgen weder Integration noch Veröffentlichung, PR, Provider- oder Produktionsfreigabe.

Abschluss dieses Berichtsauftrags bedeutet vollständige Entscheidungsunterlage, **keinen abgeschlossenen AGENTS.md-Integrationslebenszyklus**. Dauerhafte Sicherung und Defaultbranchintegration bleiben konkret aus den Schreib-/Gitverboten dieses Auftrags ausstehend. Vorbestehende Artefakte werden niemals aufgrund dieses Plans gelöscht.

**Hookkonflikt gelöst:** zusätzliche, explizit reviewbare .pre-commit-config.yaml-Anpassung für exakt drei LF-lose historische/Fixturepfade ausschließlich bei end-of-file-fixer. Alle anderen Hooks bleiben aktiv. Dies ist eine konkrete weitere notwendige Vorcommit-Anpassung, keine pauschale Ausnahme und keine bereits erfolgte Änderung. Endgültiger Scope: 83 Ziele; C1 34 / C2 30 / C3 19.
