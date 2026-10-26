# C24-R1 Search HTTP

Übernommen aus geprüftem Featurecommit `4259187` (DEV-01A), ohne dessen
Governancevorfahren. Führender DTO-/Routenvertrag:
[content_search_v1.md](../api/content_search_v1.md), Schema unter
`docs/api/examples/content_search_v1.schema.json`.

`Application` authentifiziert vor Routing. `SearchHTTP` ruft ausschließlich
`ContentIndex.search_lexical` auf; `SearchResultPage`/Source-/Parsed-/Block-/Locator-
DTOs bleiben erhalten. Ohne explizite SearchSettings bleibt die Capability aus.
`--search-config` benötigt `--content-config`. Keine implizite Initialisierung.
Course/Owner/Source werden live im kanonischen ContentStore geprüft, auch nach
Revocation. Der SearchReply hält den vorhandenen Guard bis zur HTTPauslieferung;
direkte Adapterbenutzer müssen close() im finally aufrufen.

Query: 512 Codepoints/2048 Bytes, acht literale Terme mit höchstens 64 Zeichen.
Limit 1–100, Cursor höchstens 1600 Zeichen und an Actor, Query, Filter, Limit,
Generation, Revision und TTL gebunden. Literale FTSterme vermeiden freie
MATCH-Syntax; deterministisches source_rrf_v1 bleibt bestehen. SQLite-/Dateilocks,
I/O-/Zeit-/Matchlimits und redigierte Fehler verwenden die bestehende Fassade.
Keine Treffertexte in Logs/Fehlern. Leerer initialisierter Index liefert eine
leere Seite; beschädigte Generationen fail-closed.

Tests: `tests/test_content_search_http.py` prüft echte synthetische ContentStore/
FTS5-Integration einschließlich ACL, Cursor, Fehler, Locator und Wiederöffnung.
Ein eigener Test startet den tatsächlichen Loopback-HTTPserver als Prozess.
Aktuelle Ausführung und Sandboxgrenzen sind ausschließlich im
[Validierungsbericht](c24r_integration_validation.md) maßgeblich; übernommene
DEV-Validierungsberichte sind historische Belege, keine aktuellen Testergebnisse.
