# C27-R11 – Analyse der drei Konfliktpfade

Stand 30.10.2026, rein lesende Analyse. `feat/c27-cs50-learning-pipeline` hat HEAD a8af1d9372eb435d3e1331c33b047d21120d57c2; die betrachtete Learning-Implementierung liegt **uncommittet** im Worktree. `git show` dieses Feature-HEAD enthält sie nicht. `fix/c27-acceptance-exports` ist a0d3ebf7f64d44dd843f1848e70dc70a3a3af835. Lokal gespeichertes origin/master ist a8af1d9 und enthält keinen der drei Pfade. **REMOTE_HEAD_UNVERIFIED.** Es existieren dort also keine dritte konkurrierende Implementierung und keine bereits bewiesene Live-Mergekollision.

Alle drei R10-Pfade wurden anhand tatsächlicher Worktreebytes und lokaler Gitobjekte geprüft. R10s Textproben rc=1 werden nicht erneut ausgeführt. Gemeinsame Basis e502aa915ad0e928dbe7e92eacd44fff0152912b; HEAD/fix 12/19. Schnittmenge bereits committeter Änderungen seit dieser Basis leer. Erst die unversionierten Learning-Dateien erzeugen die drei add/add-Kollisionen. Vollständiger Bytevergleich in evidence/path_comparison.json; lokale fix-Quellenkopien in evidence/fix_*.py mit denselben Zeilennummern (abschließender Zeilenumbruch normalisiert, kein Originalbyte-Archiv).

## 1. src/lecture_summary/__init__.py

Learning Zeile 1: Docstring „Local, evidence-bound summaries …“. Acceptance Zeile 1: Docstring „C27 opt-in … no worker or settings side effects“. Beide enthalten keine Funktionen, Klassen, `__all__`-Liste, Providerimporte oder Paket-Reexports. R10s Begriff Exportvertrag bezeichnet hier die Paketidentität, nicht tatsächlich implementierte Reexports. Textuell verschieden, laufzeitbezogen beide nebenwirkungsfreie Einstiege. origin/master: Pfad fehlt.

Gemeinsame Anforderung: Import darf weder Worker, Settings, echte Provider noch Dateischreibvorgänge aktivieren. Widerspruch liegt im nachgelagerten Namespace: beide würden `src.lecture_summary.models` als jeweils eigenes, inkompatibles Modellmodul laden.

Bevorzugt: Learning-Docstring bytegleich als `src/c27_learning_summary/__init__.py`; Acceptance-`__init__` bleibt ausschließlich Eigentum seiner Linie. Kein Mischdocstring als vermeintliche Konfliktlösung; kein Import-Router und keine Alias-Reexports. Falls Acceptance noch nicht auf der Zielbasis liegt, alten Paketpfad durch diesen PR gar nicht anlegen.

Risiken: übersehene direkte/dynamische Imports, Monkeypatchziele, importzeitiges Laden der Quellenkonfiguration, Testmodulnamen. Regression: kalter Import des Learning-Pakets ohne optionale SDKs unter Offlineguard; bei Koexistenz beide Importreihenfolgen prüfen, Modulidentitäten und keine unerwarteten Sideeffects kontrollieren. Nicht allein diesen Docstring testen.

Pseudodiff (nur Entwurf):
```diff
- Learning-Beitrag unter src/lecture_summary/__init__.py
+ src/c27_learning_summary/__init__.py  # Inhalt identisch
  # vorhandenes Acceptance-Paket unangetastet
```

## 2. src/lecture_summary/models.py

| Vertrag | Learning-Worktree | Acceptance/fix | origin/master |
|---|---|---|---|
| Eingabe | Catalog v2 mit origin und courses→weeks→units→materials (137–165); Course/LectureCourse, Week/Unit/LectureSection | Catalog v1 mit lectures (42–68); Lecture mit provider/course/lecture und Artifact-Versionen (20–39) | Datei fehlt |
| Materialidentität | Material/ProcessingArtifact, existierende ContentBlocks, Originalhash-/Locator-/Payloadvalidierung (72–119) | Artifact mit RegisteredStorage-ID/relativem Pfad, sha256/Format/Rolle/Parentartefakten; Evidence mit nativen IDs (89–111) | fehlt |
| Auswahl | einzelne Course/Week/Unit + Material-IDs außerhalb des Catalogmodells | Selection/Options, 1–3 explizite Lectures, keine Duplikate (71–86) | fehlt |
| Claims | Candidate/Claim: category, exakter text, 1–16 refs, topic, claim_id (255–275); Engine prüft exakte Slices | Claim: source_ids bis 32, kind, quality, optionale evidence_quote (114–120); Formula/Topic/Draft ergänzen Didaktik (123–146) | fehlt |
| Ergebnis | SummaryResult v2, run_id UUID-Hex, cache_key, Sections/Claims, Usage/Kosten und ready_for_review/needs_attention (296–325) | Summary v1, summary_id SHA, Selection/Versionen, zeitlicher Stempel, Draft/Evidence, validation_status, optional HierarchyReport (198–218) | fehlt |
| Review | ClaimReview/Review und separate append-only Storeevents (328–359) | Quality/validation_status sind technische Evidenzzustände; kein gleichwertiger append-only Human-Reviewvertrag im Modell | fehlt |
| Historie | upgrade_v1 (36–40) nur eigene v1-Familie, Provenienzvalidatoren und finale R08-Projektion | eigene v1-Familie, Cachekey bindet Adapter/Prompt/Template (221–232), HierarchyPolicy/SectionDraft/HierarchyReport (149–195) | fehlt |

Zusätzliche Funktionsprüfung: Learning `engine.bind_section` (54–85), `consolidate` (88–123), `generate` (141ff), `adapter.source_slices` (137ff), SummaryStore.result/reviews/export_json und `export.public_result/public_reviews` gehören zusammen. Acceptance `SummaryService.preflight/generate` (service.py 14–130) nutzt `collect`, `validate`, `cache_key`, revalidiert Cache und öffnet Quellen nach Generierung erneut; `validation.validate` (37–128) erlaubt didaktische/unsichere Inhalte mit explizitem Qualitätszustand, verlangt exakte Originalzitate für verified_from_source und liefert derzeit passed nicht als Erfolgspfad, sondern needs_review oder failed. `exports.render` (93–267) erzeugt Markdown/LaTeX mit Mock-/Coveragehinweisen und Escaping. Diese Funktionen brauchen Draft/Summary/Selection/Evidence/Formula, die im Learning-Modell nicht vorhanden sind.

Gemeinsam: explizite Auswahl, Originalhash und Locator, begrenzter Offlinebetrieb, konservative Quellenbindung, Cacheinvalidierung, keine technische Gleichsetzung mit Fachfreigabe. Widersprüchlich: exaktes extraktives Claimmodell gegenüber zugelassenen didaktischen Erläuterungen; ein Unitumfang gegenüber bis drei Lectures; 16 gegenüber 32 Referenzen; verschiedene v1-Schemata, Cache-/Run-/Reviewidentitäten und Exportformen. Die gleiche Zeichenfolge `schema_version=1` ist **kein** Migrationssignal zwischen diesen Familien.

Auch die Sicherheitsverträge sind verschieden: Learning hat R08-Feldprojektion und exakte HTTPS-Freigaben; Acceptance rendert eigene Evidence-URLs (exports.py 233–234). Die Analyse belegt keine äquivalente R08-URL-/Aliaspolicy in Acceptance. Eine Trennung behauptet weder dessen Sicherheitsabnahme noch eine automatische Übertragung des R09-Gates.

Bevorzugt: zwei getrennte öffentliche Modellfamilien. Learning vollständig nach `src/c27_learning_summary/`, nur Imports/Referenzen umstellen. Acceptance-Modelle, Service, Provider, Exporte und Cache unverändert lassen; keine Einfügung seiner 19 Commits in den Learning-PR. Kein Union-Catalog, keine aliasierten Claim-Klassen, kein automatischer JSONkonverter. Ein gemeinsames Frontend oder Datenaustausch wäre eigener späterer Auftrag mit explizitem Adaptervertrag. Dadurch wird keine Implementierung als fachlich maßgeblich erklärt.

Pseudodiff:
```diff
+ src/c27_learning_summary/models.py  # Learning-Vertrag identisch
- from src.lecture_summary.export_policy import ...
+ from src.c27_learning_summary.export_policy import ...
  # alle Klassenfelder/Validatoren/Schemawerte/Limits unverändert
  # src/lecture_summary/models.py gehört weiter Acceptance, falls vorhanden
```

Risiken/Regression: eigener v1→v2-Read ohne Byte-/Reviewhashänderung; fremde Catalog-/Resultpayloads müssen im jeweils falschen Modell kontrolliert scheitern; keine Statusabbildung approved↔passed; Cache-/Processingrevision kann durch Modulnamen/Quellbytes wechseln; keine automatische Umschreibung gespeicherter Runs. 16/17/24/32-Beleggrenzen, Store-/Symlink-/Hardlink-/TOCTOU-, needs_attention-/Usage- und R08-URI-/Alias-/Revocationtests bleiben Pflicht. Nebenläufige Source-Edit-/Cachevalidierung der Acceptance-Linie bleibt bei einer späteren gemeinsamen Basis ebenfalls zu prüfen. Zwei Stores niemals verbinden, keine Ergebnisse zwischen APIs routen.

## 3. tests/test_lecture_summary.py

Learning: Imports 11–32, Fixture/Course-Scope 35–37; Cache/Force und Source-/Konfigurationsinvalidierung 135–190; exakte Belege/Formel/Code/Konflikte 199–255; Fehler/Secrets/Crash/Lock/Bounds 257–305; append-only Reviews/Integrität/Exports 343–387; SDK-Stubs/Offline-E2E/Materialhandoff 390–451; ungültige Claims, Chunkoffsets, Reviewblocker, Retry und unbekannte Usage 454–601. `SECRET_MUST_NOT_BE_SAVED` ist absichtlicher Testwert, kein Credential.

Acceptance: Imports 10–26; RegisteredStorage-Fixture/Selection 37–68; 1/3-Lecture-Verarbeitung und Cache 72–162; Traversal/Storage-/Write-Gates 165–259; Coverage/Quote-/Duplikat-/Formel-/LaTeX-Gates 262–346; Contextlimit/Cancellation/MockHTTP/keine Retries 349–428; native Transcriptprovenienz 431–489; Source-Edit-/Cachekorruption 492–508; Math-/Byte-/Shared-Citationtests 511–544; lokale Konfiguration/Storage-Root-/Cancellation 547–601. origin/master enthält keine dieser beiden Dateivarianten.

Gemeinsam: deterministische Fake-/Mocktests und explizite Fehlgrenzen. Unterschiede sind fachlicher Vertragsumfang, Fixtures, Provider-/Storage-APIs und Testidentitäten. Eine Datei durch die andere zu ersetzen würde ganze Sicherheits-/Exportverträge ungetestet lassen. Das Zusammenkopieren gleicher Fixture-/Testnamen in ein Modul birgt Überschreibung und falsche Fixturebindung.

Bevorzugt: Learning nach `tests/test_c27_learning_summary.py`, Assertions unverändert; Acceptance behält `tests/test_lecture_summary.py`. Learning-UI-Suite bleibt am derzeit nicht kollidierenden Pfad. Alle Learning-Import-/Monkeypatchstrings, inklusive 313 und 426, umstellen. Neue unabhängige `tests/test_c27_summary_coexistence.py` prüft Paketisolation, falsche Schemafamilien und Offlineimport. Keine kopierte Acceptance-Suite in diesem PR. Wenn Acceptance auf Zielbasis fehlt, darf deren Testlauf nicht als grün oder als erfolgreich übersprungen berichtet werden: Koexistenznachweis separat in einer gewöhnlichen temporären Dateikopie mit fix-Overlay.

Pseudodiff:
```diff
- Learning-Beitrag: tests/test_lecture_summary.py
+ tests/test_c27_learning_summary.py
- from src.lecture_summary... / monkeypatch("src.lecture_summary...")
+ from src.c27_learning_summary... / monkeypatch("src.c27_learning_summary...")
+ tests/test_c27_summary_coexistence.py
  # existierende Acceptance-Suite nicht verändern
```

Benötigte Regressionen: Learning-Suites gesammelt unter neuem Modulnamen, unveränderte Assertions und sinnvoller Collectionvergleich nach Node-ID-Pfadabbildung; Acceptance sechs eigene Suiten bei Koexistenz getrennt sammeln, keine Namens-/Fixtureverluste; beide Importreihenfolgen und Modell-Ablehnung; gemeinsamer Testprozess mit getrennten tmp-Stores. Keine Addition der Resultate zu historischen R08/R09-Gruppen. R11 hat keinen dieser Tests ausgeführt.
