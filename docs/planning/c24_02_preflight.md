# C24-02: Historische Vorprüfung vor Merge der Architektur

**Fortsetzung 18.10.2026:** #83 ist inzwischen gemergt; Implementierungsbasis
`2d7a813ed8c668b3d73dd62119d3ca24330d76cb`. Der folgende unveränderte
Vorprüfungsnachweis beschreibt ausschließlich die damalige Blockierung. Aktuelle
[Implementierung und Abnahme](../architecture/index_projection_implementation.md).

18.10.2026. Geprüfter Remote-Master:
`95c4c40c1ab738ce1d75ac9ed554a46613419133` (nach #82).
Eigener Branch `feat/c24-02-deterministic-index-projection`.

## Status und verbindliche Arbeitsgrenze

**Nur konfliktfreie Vorprüfung abgeschlossen; C24-02 ist nicht implementiert.**
[PR #83 / C24-01](https://github.com/rf-data/Personal_Assistant/pull/83)
ist bei dieser Prüfung offen und nicht gemergt, Head
`b001388e2f05472cea2e1054c2713c6c434c9de9`. Die drei neuen Architekturdateien
`retrieval_indexing_adr.md`, `index_record_contract.md` und
`c24_implementation_plan.md` sind auf dem geprüften Master nicht vorhanden.
Der Entwurf im offenen PR wurde gelesen, aber nicht als gemergter Vertrag übernommen.

Der C24-02-Auftrag bestimmt für diesen Fall: „Dokumentiere die fehlenden
Voraussetzungen und beschränke Änderungen auf konfliktfreie Vorarbeiten.“
Daher keine alternative Architektur, keine neuen Indexmodelle, kein Projektor
und kein C24-02-Implementierungs-PR. Der Abschluss des beauftragten Projektors
bleibt bis zum Merge bzw. einem ausdrücklichen geänderten Auftrag blockiert.
Keine Änderung von Issue-/Project-/Milestonestatus; [Governance](governance.md).

## Tatsächlich geprüfte vorhandene Schnittstellen

| Bestehender Baustein | Unverändert wiederverwendbar / zu beachten |
| --- | --- |
| [Modelle](../../src/content_store/models.py) | ContentBlock, ContentLocator, Source-/Parsed-Versionen, ParserConfiguration; canonical/fingerprint und ursprüngliche deterministische IDs. Nullzeiten unterscheiden known/unknown/not_applicable |
| [Store](../../src/content_store/store.py) | _authorize prüft Course plus Owner/read-Grant; _parsed prüft publizierten Status und gebundene Payload-/Projektions-/Raw-/Bindingbytes. Maintenance-/DBlocks geben eine konsistente Lesetransaktion |
| [Reader](../../src/content_store/reader.py) | Zusätzliche SourceVersion-/Artefaktquarantäneprüfung, typed redacted DTOs, Keyset-/Cursorvertrag. Keine beliebigen lokalen JSONdateien als Sourceersatz |
| [B-Adapter](../../src/content_store/adapters.py) | Persistierte Materialaggregation_units/excluded_blocks/alternative_views; SRT-Projektion über Cuepointer. Keine neue Auswahlheuristik nötig |
| [C10-Handoff](../../src/tools_lecture/material_handoff.py), [Mapping](../../src/tools_materials/mapping.py) | Exakte Originalzeichenfenster; TOC-/Link-/PDFtabellen-/code_view-Ausschlüsse. Bestehende Defaultfenster 2.000 Zeichen; keine Code-/Formelreparatur |
| [Publikation](../../src/content_store/publication.py) | Persistierte SRT-Block-ID bindet content_cue_v1, ParsedVersion und original_segment_id; Projektions-Cue-ID und finale SQL-ID nicht verwechseln |
| [Embeddings](../../src/tools_rag/cs50_embeddings.py) | offset_windows erhält Originaloffsets, benötigt aber Embeddingkonfiguration/Tokenizer. Timed-Mapping verlangt echte Cuezeiten; kein ungeprüfter Universalchunker |
| [C23-06](../cs50/evaluation/c23_real_material_evaluation.md) | Versioniertes Inventar/Review und technische Fixturetests; kein bestätigter Realgoldbestand und keine Freigabe historischer Sources |

`ContentStore.list_content_blocks` ist keine vollständige Exportpagination:
limit höchstens 100, Cursor abgewiesen und mehr als limit Blöcke ergeben
Unavailable. Der spätere Projektor darf nicht nur die erste Seite verwenden.
Der vorhandene Reader bietet paginierte redigierte öffentliche Projektionen;
eine über viele Einzelrequests zusammengesetzte Ausgabe ersetzt keinen gemeinsamen
Snapshot für vollständige private Indexanker. Die konkrete Erweiterung folgt
nach Merge ausschließlich dem dann maßgeblichen C24-01-Vertrag.

## Ausgeführte Prüfung

Nur vorhandene synthetische Fixtures und isolierte temporäre Teststores,
keine privaten Datenverzeichnisse untersucht. Tatsächlicher Aufruf:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest \
 -q --disable-warnings -p no:cacheprovider \
 tests/test_content_store_models.py tests/test_content_read_contracts.py \
 tests/test_cs50_material_evaluation.py --basetemp=/tmp/c2402-preflight-tests
```

**77 passed / 0 failed / 0 skipped / 0 setup errors**, 10,70 s.
25 ContentStore-Modell-, 14 Read-Vertrags- und 38 C23-06-Evaluationsfälle.
Python 3.12.12, System-Pytest 7.2.1; keine Installation/Sync. Pytest-Warnungen
werden nicht als Skips ausgegeben. Keine ganze Repositorytestsuite.
Diese Ergebnisse prüfen vorhandene Verträge, **keinen neuen C24-Projektor**.
Lokale Verweise und `git diff --check` geprüft. Keine Pythonänderung; Ruff-/
Formatprüfung geänderter Pythondateien entfällt. Neue Indexschemas existieren
noch nicht und wurden daher nicht als validiert ausgegeben.

## Fortsetzung nach erfüllter Voraussetzung

1. Merge von #83 und aktuellen Master erneut prüfen. Eigene Vorprüfung erhalten,
   Branch auf den tatsächlich gemergten Stand aktualisieren.
2. Genau die gemergten Indexmodelle-/Policy-/Hash-/Offsetverträge umsetzen;
   einen autorisierten, vollständigen Snapshot auf bestehenden Storeprimitiven
   verwenden. Weder Rawreparse noch parallele Daten-/ACLmodelle.
3. Kleine deterministische Projektion, maschinenlesbare Ausschlüsse und Manifest;
   keine FTS5-/Qdrant-/Embedding-/HTTP-/Jobintegration in diesem Auftrag.
4. Neue positive/negative Projektionstests einschließlich Prozesswiederholung,
   Berechtigungsentzug, Quarantäne, Provenienz- und Aggregationsmanipulation sowie
   betroffene Regressionen, Ruff und Schema-/Dokumentationschecks ausführen.
5. Erst dann eigenen C24-02-PR mit tatsächlicher Implementierung und Testnachweisen
   erstellen. D06/D07 und fachliche Realmaterialabnahme bleiben separat.

Eigener temporärer Testroot wird nach Prüfung entfernt. Worktree und Branch
bleiben für die blockierte Fortsetzung erhalten; Primärcheckouts, fremde
Worktrees, Originaldaten und virtuelle Umgebungen bleiben unverändert.
