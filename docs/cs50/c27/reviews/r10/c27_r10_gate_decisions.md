# C27-R10 – Technische Gateentscheidungen

| Gate | Entscheidung | Begründung |
|---|---|---|
| Abbruchdiagnose | MODEL_CAPACITY_REPORTED | error Zeile 65 und turn.failed Zeile 66 nennen Modellkapazität; Pythonfehler Zeile 13 gefolgt von Erfolgen |
| Commitinventar | COMPLETE | exakt 62 Pfade, 3 modifiziert/59 unversioniert, Größe/Modus/Hash/Herkunft/Kategorie/Entscheidung je Datei |
| Commitumfang | NEEDS_REVIEW | drei konkurrierende API-Pfade, lokale Pfade, Exportbeispiele und historischer Whitespace offen |
| Integration | INTEGRATION_REQUIRED | API-/Scopeentscheidung gegenüber fix/c27-acceptance-exports offen; Live-master nicht verifiziert |
| PR-Vorbereitung | READY_FOR_USER_APPROVAL | vollständiger Entwurf und explizite Gruppen/Pfade; offene Entscheidungen konkret vorgelegt, keine Ausführungserlaubnis |
| R09-C27-Codequalität | READY_FOR_PR (übernommen) | begrenzte technische Validierung des unveränderten Arbeitsstands; ersetzt Scope-/Integrationsreview nicht |
| Historische sechs Fälle | ALL_RESOLVED | R09 6/6 unveränderte Assertions, kein neuer Lauf |
| F04 | VERIFIED_FIXED | definierter R08/R09-Exportvertrag, 75 URLwerte und konkrete Canarybelege; keine allgemeine Freitextgarantie |
| R08-CAP | PASS_INHERITED | 23/23 Regressionen + 1 Canary, frischer echter lokaler CLI mit FakeLLM Exit 0, nicht addieren |
| Pattern-/Inhaltsprüfung | NO_ACTUAL_CREDENTIAL_IDENTIFIED; PUBLICATION_REVIEW_OPEN | synthetische Negativproben, kommentierter api_key=anything-Democode; keine tatsächlichen Credentials erkannt |
| Rohdaten-/Temporärschutz | PASS_FOR_EXPLICIT_62 | keine identischen bekannten Rohdaten, keine privaten Caches/venvs unter Kandidaten; kein universeller Inhaltsbeweis |
| Diff-Whitespace | TRACKED_DIFF_PASS; W01_OPEN | unversioniertes historisches Markdown mit sechs trailing spaces vom git diff --check nicht erfasst |
| Globale Typprüfung | NOT_GREEN | 6.104 geerbte Mypy-Diagnosen, keine neue globale Prüfung |
| CS50P Week 0 | PARTIAL | TXT erfolgreich; vollständiges HTML am Chunklimit, Material-/Fachfreigabe offen |
| Multiweek/Multicourse | PLANNING_ONLY | eigene Budget-/Resume-/Kursmatrixgates fehlen weiterhin |
| Produktion | NOT_APPROVED | kein Produktions-/Betriebs-/Restore-/Releasegate erfüllt oder autorisiert |
| Dauerhafte Repositoryintegration | PENDING | aktueller Auftrag verbietet alle Gitaktionen/Worktreeänderungen; /tmp muss separat gesichert werden |
| Cleanup | NOT_PERFORMED; RETAIN_REQUIRED | keine neuen Git-Artefakte, vorhandene Branches/Worktrees/Handoffs erhalten |

## Scope-/Publikationsfragen

I01, P01, S01 und W01 sind Reviewentscheidungen, keine neue Behauptung eines Produktdefekts. S01 betrifft ausschließlich die Veröffentlichung der alten exportierten Beispielartefakte: relative Fixtureidentitäten sind nach R08 zulässig, eine strengere Veröffentlichung ohne lokale Pfade ist im wiederhergestellten R10-Zwischenstand offen. F04 wird dadurch nicht wieder geöffnet. Absolute Pfade in historischen Logs sind keine Credentials, erfordern aber bewusste Publikationswahl. Historische Originalbelege nicht still verändern; gegebenenfalls separate publizierbare Fassung mit eigener Provenienz und eigenem Manifest beauftragen.

F06–F14 behalten die R09-Zuordnung: fehlende/gesperrte Materialien und UI-Abdeckung (F06), dauerhafte Sicherung/Defaultbranchintegration (F07), vollständige HTML-Segmentierung (F08), ZIP-Quellenmapping (F09), vollständige Week 0 (F10), fachliche/echte Providerabnahme (F11), Kursbudget/bezahltes Resume (F12), spätere CS50x-/Web-Matrix (F13), Produktionsfreigabe (F14). Keine Umklassifizierung zu neu nachgewiesenen Codefehlern.

## Abschlussgrenze

READY_FOR_USER_APPROVAL bezeichnet ausschließlich die vorliegende überprüfbare Entscheidungsunterlage. Es ist keine Erlaubnis zur Durchführung von Git-Aktionen. Ein offener Git-/Integrationslebenszyklus ist ausdrücklich dokumentiert, kein vollständiger Projektabschluss. Keine Netzaufrufe oder Änderungen bestehender Handoffs, Rohdaten, des Indexes oder Produktworktrees. Die spezifische /tmp-Ausnahme des Auftrags hat Vorrang vor den allgemeinen Sicherungs-/Commitregeln der übergeordneten AGENTS.md.

Erhaltungsprüfung: **PASS_WITH_PLATFORM_METADATA_DRIFT**. Nur mtime/ctime der drei belegten leeren Read-only-tmpfs-Mountwurzeln `.agents`, `.aws`, `.codex` weichen plattformseitig ab; keine pauschale Ausblendung von Dateien. Alle anderen geschützten Metadaten und Gitdaten stimmen überein. Details in `preservation.json`.
