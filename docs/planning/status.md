# PM-01 – aktueller Implementierungs- und GitHub-Abgleich

**19.10.2026, Europe/Berlin.** Backend `master`
`4c057ae33d41ba98e227879cc8a51283338e4a0b`, Tree
`59fd44fb68d0da8b8d01eb5db75e4944dc827d49`; UI `main`
`90816a1578bcf67739ee9acaa483c1635aa0c44b`, Tree
`e693f1d1975544319458d0772a054630406bc782`.
Live REST-Abfragen der Default-Heads, vollständigen Issue-/PR-Listen und
Repositoryrechte über den GitHub-Connector; anschließend versionierte Verträge
und erste Merge-Parents im eigenen PM-Worktree geprüft. Keine Runtimeabnahme.

## C23–C24: belegter Lieferumfang

| Paket | Integrierter PR | Tatsächlicher Umfang / verbleibende Grenze |
| --- | --- | --- |
| C23-01 | [#75](https://github.com/rf-data/Personal_Assistant/pull/75) | SQLite/Blobs-ADR und Wiederverwendung; PostgreSQL keine noch ausstehende Pflicht |
| C23-02A/B/C | [#76](https://github.com/rf-data/Personal_Assistant/pull/76), [#77](https://github.com/rf-data/Personal_Assistant/pull/77), [#78](https://github.com/rf-data/Personal_Assistant/pull/78) | Core, verifizierte Adapter und Recovery/Backup; [Implementierung](../architecture/content_store_implementation.md), [Betriebsvertrag](../operations/content_store_recovery.md). Kein Produktions-Verbundbackup |
| C23-03 | [#79](https://github.com/rf-data/Personal_Assistant/pull/79) | Explizite Reimportversuche/Sourceinventar; historische SRT-Pfadbindung bleibt D06-gesperrt |
| C23-04 | [#80](https://github.com/rf-data/Personal_Assistant/pull/80) | [Autorisierte Content-Read-API](../api/content_read_v1.md); keine allgemeine Such-API |
| C23-05 | [#81](https://github.com/rf-data/Personal_Assistant/pull/81) | Unknown-Time-Modell/Importer/Timed-Guards; vollständiger TXT-ContentStore-Publikationsadapter bleibt Folgearbeit |
| C23-06 | [#82](https://github.com/rf-data/Personal_Assistant/pull/82) | [Technisches Inventar-/Goldframework](../cs50/evaluation/c23_real_material_evaluation.md); null vollständige freigegebene Realbundles/konfirmiertes Gold, Realabnahme offen |
| C24-01/02 | [#83](https://github.com/rf-data/Personal_Assistant/pull/83), [#84](https://github.com/rf-data/Personal_Assistant/pull/84) | ADR und [deterministische Projektion](../architecture/index_projection_implementation.md) |
| C24-03 | [#85](https://github.com/rf-data/Personal_Assistant/pull/85) | [FTS5/Generationen/interne Suche](../architecture/content_fts_implementation.md), entspricht geplantem 02-B/03-A; **kein HTTPsearch und keine C16-Indexjobs** |
| C24-04 | [#86](https://github.com/rf-data/Personal_Assistant/pull/86) | [Content-Vektoradapter](../architecture/content_vector_implementation.md) mit FakeEmbedder/Transport. Kein tatsächlicher E5-/Qdrant-/Hybridnachweis |
| C24-05-A | [#87](https://github.com/rf-data/Personal_Assistant/pull/87), Merge 18.10.2026 | [A-Evaluator und unabhängige Goldverträge](../cs50/evaluation/content_retrieval_evaluation.md); keine synthetischen Werte als Realqualität |
| C24-05-B1 | [#90](https://github.com/rf-data/Personal_Assistant/pull/90), Merge 18.10.2026 | [Reviewpersistenz/API](../api/human_review_v1.md), explizite Rechte, C16-Principal, Revisionen/Goldexport/Reports/Abnahme. Keine globale Dataset-/Reportinventur behaupten |
| C24-05-B2 | [UI #7](https://github.com/rf-data/personal-assistant-ui/pull/7), Merge 19.10.2026 | [Bestehende Streamlit-Reviewansicht](https://github.com/rf-data/personal-assistant-ui/blob/90816a1578bcf67739ee9acaa483c1635aa0c44b/docs/human_review_ui.md). Vertragsgebundene UI, keine allgemeine Suchseite und keine reale Humanabnahme |
| C24-05-C2 | [#91](https://github.com/rf-data/Personal_Assistant/pull/91), Merge 19.10.2026 | [Synthetische Review/Gold/FTS5/A-Integration](../cs50/evaluation/c24_authorized_pilot_integration.md), übernommene #89-Metadaten. Reale Ausführung weiter blocked/not_evaluable |
| C24-06-A | laufender separater Auftrag | Branch `feat/c24-06a-local-review`, kein veröffentlichter PR im abgefragten Bestand. Lokale synthetische Umgebung/Humanabnahme ist in Bearbeitung; PM-01 prüft/ändert deren Dateien, Prozesse und Tests nicht |

C23/C24-Parents bleiben **technisch integriert, fachlich offen**; kein allgemeines
Done. Search-HTTP/DTOs und Indexjobs sind die vorhandenen Restpakete 03-B/02-C,
keine neue Suche oder Queue. C25–C32 sind geplant; C26 benötigt eigene Betreiber-
und Zielabnahme. B2-Renderer/Client/Security bei C25 wiederverwenden.

## Offene PRs und erhaltenswerter Umfang

| PR / Branch / Head | Inhalt / Abhängigkeiten | Abgleich und Empfehlung, keine Aktion |
| --- | --- | --- |
| [#72](https://github.com/rf-data/Personal_Assistant/pull/72), `feat/c21q-qdrant-transcript-pilot`, `3a42b1675dffe823edc179a347fa97dd1a096fd0` | Qdrant-/Auth-/Healthvorbereitung, read-only Pilotinventur und C21-Q.1-Pfadbefund. Modell/Instanz/Transport und D06 separat | Optionaler vorhandener Pilot, nicht durch FTS5 oder Fake-Vektoradapter abgeschlossen. Guards/Runbooks und historische Evidenz erhalten; kein Merge/Close |
| [#88](https://github.com/rf-data/Personal_Assistant/pull/88), `feat/c24-05b-human-review-workflow`, `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` | Review-ADR + Plannachtrag, keine Runtime | A-/B-Implementierungsblockade ist überholt durch #87/#90/UI #7. Architekturbegründungen als historische Designentscheidungen erhalten und gegen B1-Vertrag abgleichen; keinen zweiten Reviewworkflow planen |
| [#89](https://github.com/rf-data/Personal_Assistant/pull/89), `feat/c24-05c-real-corpus-pilot`, `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d` | CorpusManifest/GoldDataset, Readiness r1/r2, Pilot-/Übergabeplan; keine Runtime | Metadaten bereits in #91 übernommen, frühere B-Blockade überholt. Unveränderte r1/r2 und nachvollziehbare Übergabe erhalten; r3/#91 ist aktueller technischer Stand. D06/D07 und Realabnahme nicht überholt |

Diese Inhaltsprüfung verwendet die erhaltenen Draft-Heads bzw. deren bereits
integrierte Artefakte und den [C2-Draftaudit](../cs50/evaluation/c24_authorized_pilot_integration.md).
Offene historische Backend-PRs #6/#9/#10/#11 bleiben ebenfalls unverändert;
[früherer Review](../cs50/operations/historical_pr_review.md). #81 ersetzt keine
ungeprüfte komplette Übernahme des alten #9-Patches.

## GitHub-Issues, Rechte und Project

Vor Erstellung des eigenen PM-01-PR: REST `issues?state=all&per_page=100` und `pulls?state=all&per_page=100` lieferten
Backend **89**, UI **7** Einträge, jeweils weniger als eine volle Seite. Sämtliche
Issue-Endpunkt-Einträge besitzen `pull_request`: **0 eigenständige Issues** offen
oder geschlossen. Backend 7 offene PRs (#6/#9/#10/#11/#72/#88/#89), darunter drei
Drafts; UI keine offenen PRs zum Snapshot. Vollständiger Deduplizierungsbestand,
kein Schluss aus bloßen Titelsuchen.

Der authentifizierte Account ist `rf-data`, Profilname `rf_data`; beide Repos
melden admin/maintain/push/triage/pull. Das bestätigt **keine** Projectrechte.
Der Eigentümer benennt [User-Project #1](https://github.com/users/rf-data/projects/1).
Name/Node-ID/Views/Felder/Items/Workflows/Permissions sind nicht auslesbar;
[Inventartabelle](project.md). Connector weist Owner-/Repo-Projects, GraphQL,
Milestone- und Label-Inventar mit `INVALID_ARGUMENT` zurück. `gh` fehlt. Auch
öffentlicher Webabruf konnte das Project nicht öffnen (Cache miss). Kein Token
oder Projekt-Envfile gelesen, keine App/Dependency installiert.

PM-01 ist die ausdrückliche Freigabe für nichtdestruktive Planung; die alte D01-
Planfreigabe fehlt **nicht** mehr. Die zusätzliche Startbedingung „Project und
Berechtigungen tatsächlich bestätigt“ ist für Issue-/Projectmutationen noch offen.
Deshalb **keine** Issues/Labels/Milestones/Items/Views/Automatisierungen verändert;
nur separater Dokumentations-PR. [Nächste konkrete Schritte](github_execution.md).
Die Projectübersicht ist damit noch nicht operativ konsolidiert.

## Nachweistiefe

Technische Funktionen aus Default-Code/PRs geprüft; historische Pakettests nicht
neu ausgeführt oder summiert. Fachliche Realabnahme und produktiver Go-live bleiben
ungeprüft/blockiert. [PM-01-Validierung](pm01_validation.md),
[unveränderte Aufnahme vom 17.10.2026](status_c230_2026-10-17.md).
