# C24-05-B1: tatsächlicher synthetischer Backendnachweis

18.10.2026. Runtimebasis Master `d2b5e05e732ef677fe8e8b4ccbb4d76c6d532e60`.
Eigener Branch `feat/c24-05b1-review-backend`. #87 integriert; #88/#89 bei erneuter
GitHubprüfung weiterhin ungemergt. Architektur aus #88 am dokumentierten Head
`f3fae9ef6d2c919adb12b08242bf84819f2b42f2` geprüft, kein fremder Worktree übernommen.

## Implemented

Lauffähiges Paket `src/evaluation_store`, tatsächliche Gatewayintegration und
expliziter `--review-config`-Opt-in. Separate private SQLitepersistenz, geprüfte
Revisions-/Auditkette, CAS und Idempotenz, explizite Subject-/Dataset-/Sourcepolicy,
Assignments, Drafts/Korrekturen/Entscheidungen, separat bestätigter Reviewpool,
direkter Export in vorhandene A-/C23-Modelle, bestehender A-Evaluator und gebundene
manuelle Abnahme. [API-/Betriebsvertrag](../../api/human_review_v1.md).

Keine neue Dependency, Authentifizierung, Serveranwendung, Metrik, Parserpipeline
oder UI. ContentStore-Runtime, Schema und Originaldaten bleiben unverändert. Die
einzige Änderung an einem vorhandenen Testhelper erlaubt explizite synthetische
Codebytes für Emoji/Combining/CRLF; sein bisheriger Default bleibt bytegleich.

## Passed

Umgebung: Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, vorhandenes System-Pytest
7.2.1, Ruff 0.16.0. Keine Installation/Downloads. Pytest-7-AST-Warnungen unter
Python 3.12 sind keine Skips. Sämtliche Tests offline, ausschließlich neue
synthetische Quellen/private temporäre Stores, keine produktiven Instanzen.

Tatsächliches gemeinsames Präfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
  -q --disable-warnings -p no:cacheprovider
```

| Lauf | Ergebnis | Dauer |
| --- | --- | --- |
| Neue Store-/Workflow-/API-Suite, `/tmp/c2405b1-final` | **45 passed, 0 failed, 0 skipped** | 131,68 s |
| A-/Content-/ACL-/FTS-/Gatewayregression, `/tmp/c2405b1-regression` | **278 passed, 0 failed, 0 skipped** | 304,69 s |
| Abschließende gezielte Prüfung, `/tmp/c2405b1-last-check` | **4 passed, 0 failed, 0 skipped, 41 deselected** | 11,89 s |

Neue Suite: `tests/test_evaluation_store.py`. Der abschließende Lauf desselben
Moduls wählt mit `-k 'verified_bundle_api_restart or security_failure or sigkill or
unanchored_and_undetermined'` genau die vier betroffenen Bereiche aus. Nach dem
45er-Lauf wurden ausschließlich die Kontextkennzeichnung unanchored-Parsingbefunde,
das current-Flag negativer Abnahmen bei Sicherheitssperre und der SIGKILL-Test auf
einen tatsächlichen Auditappend präzisiert. Diese vier Fälle wurden danach komplett
erfolgreich ausgeführt; kein erneuter gemeinsamer 45er-Lauf nach diesen begrenzten
Präzisierungen behauptet. Die Läufe überlappen und werden nicht addiert.

Regressionsumfang mit obigem Präfix und eigenem `--basetemp`:

```sh
tests/test_content_retrieval_evaluation.py \
tests/test_content_retrieval_integration.py \
tests/test_content_store_models.py tests/test_content_store_adapters.py \
tests/test_content_read_contracts.py tests/test_content_index_projection.py \
tests/test_content_fts.py tests/test_job_control.py
```

Die 278 Fälle enthalten 66 A-Fälle, 25 Contentmodelle, 49 Adapter-, 14 Read-,
41 Projektions-, 47 FTS- und 36 Gatewayfälle. Keine Gesamtrepositorysuite,
optionale SDK-/Modell-/native PDFparserprüfung oder vollständige UIabnahme.

Nachgewiesene neue Prüfbereiche:

- Explizites Init/Reopen, private Rechte, No-Overwrite, unbekanntes Schema,
  SQLrollback, echte überlappende Threads/CAS, Idempotenz, manipulierte Revision.
- Separater Prozess wird während eines uncommitteten Audit-/Headappends per
  SIGKILL beendet; SQLite stellt beim Reopen den letzten Commit wieder her.
  Kein selbst implementierter Replay und keine manuelle Journallöschung.
- Normale Read-Grants und Operatorrolle erteilen keine Reviewrechte. Zuweisung,
  Annotation und Bestätigung separat; ausdrücklich beauftragter synthetischer
  Viewer kann unabhängig bestätigen, andere Revieweridentität nicht einschleusen.
- Fremde/bekannte Tasks liefern dieselbe redigierte Antwort; Listen zeigen nur
  zugewiesene Tasks bzw. ausdrücklich verwaltbare Aufgaben. Fehlender Course,
  fehlender Beleg, falsche IDs/Hashes/Locatoren und invalide Zustände sperren.
- Grantentzug nach initialem Reviewlesen vor Contentguard verhindert Export.
  Tatsächlicher Contentwriteversuch unmittelbar vor Reviewappend wird unter
  gehaltenem Contentguard Busy. Quarantäne/Tombstone sperren vorhandene Exports.
- Vorannotation kann sich auch nach Umbenennung nicht bestätigen. Negative
  Relevanz 0 bleibt bestätigt; Poolvollständigkeit braucht separate berechtigte
  Coveragebestätigung und wird bei Korrekturen stale.
- Tatsächlich verifiziertes synthetisches Codebundle mit Emoji, Combiningzeichen
  und CRLF, exakte Codepoint-/Rawbytes; unknown-Zeitmodell bleibt null und kann
  nicht als abweichender Locator in einen bestehenden timed/anderen B-Anker
  eingeschleust werden. Kein gültiges unknown-SRT-Bundle fingiert.
- Parsingvollblockgold ist separat; explizite C23-Entry-ID bleibt erhalten.
  Unverankerbare/undetermined-Befunde bleiben im Audit, ohne gültiges Retrievalgold
  oder entscheidbare Parsingreferenz zu erzeugen.
- Bestätigte Sicherheitsverletzung sperrt positive Abnahme, auch wenn ein späterer
  Bericht sie auslässt. Eine dokumentierte negative Entscheidung bleibt lesbar.
- Tatsächlicher bestehender `handler_for` verarbeitet HTTPbytes über MemorySocket:
  authentifizierte Task-/Rawroute, No-Store/Nosniff/Attachment und unveränderte
  Originalbytes. Das ist derselbe Handler wie im Gateway, kein zweiter Testserver.

Der Haupttest führt aus:

`Verified B Bundle → ContentStore → Task → Draft → Confirm → neuer Gateway/Storehandle
→ Correction Revision → Confirm → separate Poolbestätigung → Goldexport → A Evaluation
→ manuelle synthetische Abnahme mit Limitierungen`.

Er prüft originale Workspace-/Receipt-/Parsedbytes im Bundle und das gesamte
ContentStore-Byte-/Modusinventar vor/nach dem Ablauf. Die autoritative Quelle bleibt
unverändert. Neuer Code führt keine extrahierten Codezeilen aus.

## Tatsächlich aufgezeichnete Beispiele

[API-Aufzeichnung](c24_05b1/api_examples.v1.json): fünf unverändert aufgezeichnete
Request-/Responsepaare von Draft/Confirm, Reopenread und Correction/Confirm aus
einem weiteren tatsächlichen Durchlauf des Haupttests. Das sind ausgewählte
Schritte, kein ohne Dataset-/Taskvorbereitung ausführbares Curlskript. Der vollständige
reproduzierbare Ablauf steht im genannten Test und `tests/review_support.py`.
Keine Authheader/Tokendigests, Hostroots oder behaupteten realen Menschen enthalten.

[Tatsächlicher A-Bericht](c24_05b1/evaluation_report.v1.json),
[exaktes Dateihashmanifest](c24_05b1/manifest.json).
Berichtsdigest `717c16f55dc609026f737607308d85a0eaee73f9d315cbd4e952ed752a910ea4`.
Die direkte A-Auswertung und die Review-API liefern denselben Reportdigest.
Synthetisches Testkonstrukt: k=4, ein relevanter Codeanker, ein bestätigter
negativer Kontextanker; Precision 1/4, Recall/MRR/nDCG jeweils 1 mit dem tatsächlichen
A-Nenner. **Keine Modell- oder Realmaterialqualitätsbehauptung.** Sicherheitsfälle
sind in diesem Beispiel not_checked; die manuelle Entscheidung benennt diese
synthetische Begrenzung und setzt `automatic_release=false`.

Ruff check und format --check für `src/evaluation_store`,
`src/job_control/http.py`, `scripts/job_control.py`, `tests/review_support.py`,
`tests/test_evaluation_store.py`, `tests/content_adapter_support.py`; anschließend
`git diff --check`. Keine Lint-/Installationshooks mit Netzwerk ausgeführt.
Modelle/Reportdigest und Dateihashes der Beispiele sowie lokale Dokumentationslinks
werden vor Publikation nochmals separat geprüft.

Frühere Entwicklungsläufe: `/tmp/c2405b1-first` **28 passed / 6 failed**, 101,36 s;
`/tmp/c2405b1-second` **41 passed / 3 failed**, 111,69 s. Korrigierte neue Defekte:
Gateway-Identity-/Principalvergleich, wiederverwendeter Key im Ablehnungstest,
Tuple-/JSONserialisierung einer Abnahme sowie Vollblocktest ohne finalen LF.
Ein weiterer `/tmp/c2405b1-release`-Lauf war bereits **45 passed**, 170,97 s;
danach kamen Source-/Entrybindung und die persistente Sicherheitssperre hinzu,
nachgewiesen im finalen 45er-Lauf. Keine Entwicklungsläufe als zusätzliche Abnahme
addiert, keine neuen Fehler als historische Baseline ausgegeben.

## Not checked / Blocked / Out of scope

`not_checked`: reale Reviewerentscheidungen, reale Quellen/Bundles/Gold, Browser,
UI, echter Netzwerk-/Proxytransport, produktive Host-/UID-/Last-/Kapazitätsfreigabe,
Reviewbackup/Restore, privilegierte Dateisystemangreifer, vollständige native
PDF-/Modell-/SDKpipeline. MemorySocket ist kein Nachweis eines produktiven Deployments.

`blocked`: fachlicher C24-05-C-Realpilot, unabhängiges Realgold und Release bleiben
durch D06/D07 und fehlende sourcebezogene Rechte/Bundles/Reviewfreigaben offen.
Realreviews und alle Writes sind ohne bewusste private Konfiguration standardmäßig
gesperrt. Diese Implementierung bestätigt keine echte menschliche Quellenfreigabe.
Eine echte UIintegration muss den nun konkreten Backendvertrag getrennt integrieren.

`out_of_scope`: zweites Frontend/Login/API, Parseränderung, Retrievaltuning,
Qdrant-/Embedding-/LLMaufrufe, Originalmigration, automatische Indexierung,
Publikation oder Deployment. Keine Änderungen an fremden Worktrees oder Primärdaten.

Bewusste v1-Grenzen: actorgebundener A-Export, begrenzte private Evidenceexports,
vollständige Hashprüfung statt Cache, manuell verantwortete Coverage-/Securitybelege,
kein Read-only-Dateisystemmodus der ReviewDB und kein C22-Verbundbackup. Vollständig
fehlende Dokumente ohne verifizierbaren Kontextblock benötigen einen separaten
Originalbefundvertrag; keine erfundene Blockbindung als Ersatz.

Eigene temporäre synthetische Testroots/Beispielroots und erzeugte Caches werden
nach Prüfung entfernt; Logs außerhalb des Repositories bleiben erhalten. Der eigene
Worktree und Branch bleiben für den offenen PR erhalten. Keine Bereinigung anderer
Worktrees, privaten Originale oder virtuellen Umgebungen; kein Merge.
