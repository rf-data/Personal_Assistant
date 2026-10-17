# C21 – Ergebnisse und Grenzen

17.10.2026, Europe/Berlin. [Abnahmeplan und Reproduktion](c21_test_plan.md),
[maschineller Bericht](c21_report.v1.json), [SHA-256](c21_report.sha256),
[offene manuelle Reviewstruktur](c21_review.md).

Die synthetische technische Workflowkette ist abgenommen. Die Ergebnisse sind
keine Browser-, Produktions- oder fachliche Materialfreigabe. Kein Merge,
Deployment, Download, LLM-Aufruf oder produktiver Datenbankzugriff wurde ausgeführt.

## Ausgeführte Prüfungen

| Prüfung | Ergebnis | Tatsächlicher Nachweis |
| --- | --- | --- |
| Kanonische Streamlit-UI → echter Loopback-HTTP-Server → Queue/Guardian → fünf Stufen | passed | fünf ursprüngliche `completed`-Stufen, hashgeprüfter Reportvertrag, Artefaktmetadaten |
| Antwortverlust nach echter HTTP-202-Antwort / neue AppTest-Sitzung / gleicher Intent | passed | Wiederholung mit unverändertem Body/Key; Historie 1 |
| Erneutes Inspect / bestätigtes Resume | passed | fünf `skipped / verified_reuse`; identische Job-ID und keine weitere Ausführung |
| Echten Backend-HTTP-Prozess stoppen und auf demselben Port neu starten | passed | Ausfall wird als Fehler sichtbar; persistierte Job-ID und Historie bleiben erhalten |
| Veraltete Preview, beschädigter Normalized-Output, Stale-Propagation / Teilresume | passed | alte Bestätigung abgewiesen; erste zwei Stufen wiederverwendet, neue Run-ID; frühere Bytes erhalten |
| Source-Ref, Owner, Course | passed | tatsächliche TCP-422 beziehungsweise drei TCP-403-Antworten |
| Geänderte Quellhashes / fehlende lokale Quelldatei | passed | blockierte Preview; Resume abgewiesen mit 422 beziehungsweise 503; kein zusätzlicher Job |
| Native PDF-Verarbeitung: Cancel / Worker-Timeout / Executor-Neustart / Resume | passed | bestehende UI-/Router-Szenarien und physische C19-Prozesstests |
| Alte Outputs und physisches PDF-Cleanup | passed | vorhandene C19-Tests prüfen Prozessgruppen/PIDs und terminale Zustände; Resume erhält alte Artefakte |
| C15 Starts, Running, Success, Failure, Cancel, Dauer und Timeout | passed | echte TCP-Metriken sowie positive Serien aus tatsächlichen UI-Lifecycle-Teststores |
| Job-/Stage-/Run-/Workflow-Identitäten als Metriklabels | passed | keine solchen Labels; nur bestehende begrenzte C15-Labelmenge |
| Backend-Regressionen, jeweils letzter geprüfter Fallstand | passed / 3 skipped | **585 passed, 3 skipped**, aus breitem Erstlauf und dokumentierten gezielten Wiederholungen |
| C11 nach optionalem Import-Preflight | passed | **123 passed in 86,57 s**, unveränderte Workerlimits |
| Neue C21-Report-/Hash-/Fehler-/No-Overwrite-Tests | passed | **7 passed in 0,39 s** |
| Vollständige UI-Suite mit korrigiertem Cancel-Nachweis | passed | **115 Tests, keine Skips**, einschließlich aller optionalen externen Integrationsmethoden |
| Ruff / Format / Whitespace | passed | neue Backend-Abnahmeskripte und Tests sowie betroffener UI-Testtreiber |
| Echte lokale CS50-Python-Notes Week 5 | passed, technisch | Originalhash, HTML-v2, vorhandenes Binding, C10-Gate und Handoff; C13-Inventur |
| Reale Week-0-PDF-Originale und ursprünglicher Notes-0-Artefaktworkspace | blocked / skipped | drei optionale Originalartefakttests ohne bereitgestellte Eingaben |
| Reale mathematische Rekonstruktionsqualität | blocked | keine unabhängigen echten Original-/Gold-/Prediction-Paare |
| Menschliche Browserabnahme und fachliche Inhaltsprüfung | not tested | nur AppTest und technische Originalprüfung durchgeführt |

Die drei Skips heißen im JUnit-Nachweis
`test_optional_original_pdf_preserves_text_and_all_misclassifications`
(Slides und Source-PDF) und `test_optional_original_python_notes_read_only`.
Eine andere vorhandene echte HTML-Datei wurde separat technisch geprüft; sie
ersetzt diese fehlenden Original-/Receipt-/Normalized-Artefakte nicht.

## Fehlgeschlagene Erstläufe und gezielte Korrekturen

Es wird ausdrücklich **kein einzelner vollständig grüner Full-Erstlauf** behauptet.
Der breite Backendlauf ergab zunächst **574 passed, 10 failed, 3 skipped in
510,53 s**. Alle zehn Fehler betrafen den optionalen C11-SymPy-Worker: Eine kalte
SymPy-1.14-Initialisierung kostete hier **12,816 CPU-Sekunden** und erreichte dessen
unverändertes 2-s-Softlimit vor einer Entscheidung. Das korrekte Workerresultat
war `undetermined`, während die installierten optionalen Entscheidungsfälle
symbolische Ergebnisse erwarten. Ein normaler Import erzeugt die üblichen
Bytecodecaches; danach bestanden alle 123 Formeltests. Das Full-Profil enthält
deshalb einen expliziten, protokollierten optionalen Import-Preflight. Keine
Dependencyinstallation, keine Änderung der mathematischen Kriterien oder Limits.

Der erste UI-Gesamtlauf fand eine Timing-Annahme im Testtreiber: Nach bestätigtem
Cancel darf ein nachfolgender GET bereits `cancelled` zurückgeben. Der Test
verlangte dort ausschließlich `cancel_requested`. Der separate UI-PR prüft nun
die tatsächlich in der UI gespeicherte Cancel-Bestätigung samt Job-ID und
anschließend den zulässigen aktuellen Zustand. Die spätere Prüfung auf den
exakten terminalen Zustand, erfolgreiches explizites Resume und unveränderte alte
Artefakte bleibt bestehen. Die vollständige UI-Suite wurde danach erneut geprüft: 115 Tests, keine Skips, OK in 125,227 s. Siehe [UI-PR 4](https://github.com/rf-data/personal-assistant-ui/pull/4), Commit `7d34bf3cbf474268db6b0418fcaf938fd75c1d71`.
Keine Produktansicht oder produktive Cancellationlogik wurde verändert.

Die letzten Ergebnisse pro Backendfall ergeben 588 Fälle: 585 passed und
3 skipped. Die Formelgruppe und die sieben endgültigen C21-Tests ersetzen ihre
älteren Resultate; sie werden nicht noch einmal addiert. Die drei nativen
UI-Lifecycle-Subtests werden getrennt aufgezeichnet und nicht zusätzlich zu den
115 unittest-Methoden gezählt. Erstlauf und Wiederholungen stehen getrennt im JSON.

## Tatsächliche Realmaterialprüfung

Original: bereits versionierte Datei
`docs/course_sources/cs50/cs50_python/lecture_5.html`, URL
`https://cs50.harvard.edu/python/notes/5/`.
SHA-256: `0855465b0458067ce5b6889d5e3929a49de108aa8d01d877c25e80bea0cd8367`.
Keine weiteren Originalpfade durchsucht oder unbekannten Dateien eingelesen.
Der zuvor genannte `/tmp`-Week-0-Source-PDF-Pfad ist nicht vorhanden.

- Vorhandenes Course-Binding `cs50_python`, Section `5`, Lecture-ID
  `resource:06f1c7a3c1e8937e625c36361c21171a1f24440b5a4ff5076c076ebdc4a4b845`.
  Herkunft der Resource: `cs50_python/week_5.html` mit ursprünglichem DOM-Locator.
- HTML-v2 erzeugt 111 Blöcke: 7 Überschriften, 16 Links, 7 Listen,
  65 Absätze und 16 Codeblöcke. C10: `passed`, 23 technische Info-Befunde zu
  Referenzprojektionen, Handoff vorhanden. Das beweist keine Textvollständigkeit.
- C13: `plan_verified`, Raw-Scan `complete`, zwei zusätzliche reine Bildreferenzen
  ohne deklarierte lokale Bildartefakte. Beide liegen im ursprünglichen
  `aside/nav`-Bereich; der Parser wird deswegen nicht als fehlerhaft umgebaut.
  Zwei konkrete `not_in_normalized_images`-Warnungen bleiben im Report sichtbar.
- Originalbytes bleiben unverändert. Keine Bilder heruntergeladen, keine
  Formeln rekonstruiert, keine Knowledge-Extraktion gestartet. Semantische
  Qualitätsquoten wurden nicht berechnet.

## Separater Legacy-Befund und priorisierte Risiken

| Priorität | Status | Befund / nächster Schritt |
| --- | --- | --- |
| P1 | failed, bestehend | `test_official_transcript_import.py`: **6 failed, 33 passed in 1,92 s**. TXT-Import liefert unbekannte Zeiten (`None`), bestehender `TranscriptSegment` verlangt float. Separat beheben; keine erfundenen Zeitwerte oder Umgehung im Materialworkflow. |
| P1 | not tested | Browser-/TLS-/OIDC-/Betriebsabnahme steht aus. Die technische lokale Abnahme ist keine Freigabe produktiver Dienste. |
| P2 | blocked | Week-0-Original-PDFs/Originalartefakte und reale mathematische Goldannotation bereitstellen; anschließend C10/C11/C13 und die manuelle Reviewstruktur ausführen. |
| P2 | Ressourcenabhängigkeit | Kaltimporte und Btrfs-/ENOSPC-/tmpfs-RAM-Grenzen können Tests abbrechen. Vorhandene Limits erhalten, Preflight/Platz prüfen und Fehler ausweisen. |
| P2 | Integrationsgrenze | Der dokumentbezogene C10-Handoff ist noch kein zeitbasierter Knowledge-Import. Spätere Integration muss Referenzen erhalten und darf keine Zeitpositionen erfinden. |

## Empfehlung und Cleanup

Zuerst die kleine UI-Testkorrektur und diesen Backend-Abnahme-PR prüfen. Danach
fehlende Originalartefakte bereitstellen und eine Person die Browser-/Material-
Reviewstruktur ausfüllen lassen. Den TXT-/Zeitvertragskonflikt separat lösen.
C21-Q bleibt ein unabhängiger Parallelauftrag; dieser PR aktiviert weder Qdrant
noch einen anderen produktiven Dienst.

Disposable Entwicklungszwischenstände werden nach Prüfung entfernt. Der eigene
C21- und UI-Korrektur-Worktree bleiben bei offenen PRs erhalten. Hauptcheckouts,
ältere Worktrees, Branches, Originale und virtuelle Umgebungen bleiben bestehen.
Die abschließenden privaten Abnahmebelege und der neue Realmaterialworkspace
bleiben zur Nachprüfung verfügbar; normale Python-Bytecodecaches werden nicht
aus der vorhandenen Umgebung gelöscht. Kein `--force`, `git clean`, Reset oder
automatisches Branchlöschen.

Die UI-Korrektur ist separat in [PR 4](https://github.com/rf-data/personal-assistant-ui/pull/4) enthalten; finale Laufzeit: 125,227 s bei 115 Tests ohne Skips.
