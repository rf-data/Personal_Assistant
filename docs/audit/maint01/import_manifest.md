# MAINT-01 – Provenienz der einzigen Dokumentübernahme

19.10.2026. Zielbasis Backend `master` `4c057ae33d41ba98e227879cc8a51283338e4a0b`.
Repositoryidentität durch origin-URL, gemeinsames Git-Verzeichnis und Commitgraph
bestätigt. MAINT-01 autorisiert sichere Dokumentkopien; Quelle ist die versionierte
öffentliche technische Dokumentation des vom Auftraggeber benannten Repositories.
Keine uncommitteten Nutzerbytes, Geheimnisse oder Originalmaterialien kopiert.

| Quelle | Branch / Commit | Originalpfad | SHA256 / Bytes | Ziel | Bewertung |
| --- | --- | --- | --- | --- | --- |
| [rf-data/Personal_Assistant #88](https://github.com/rf-data/Personal_Assistant/pull/88) | `feat/c24-05b-human-review-workflow` / `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` | `docs/architecture/human_review_workflow_adr.md` | `3ef6f647fc5730ed9e357e565a9f9aa33f5e9148c0d90b4d7943f0aca5c6b6c2` / 17436 | `docs/architecture/human_review_workflow_adr.md` | Historische Architekturvorbereitung, unveränderte Bytes; keine aktuelle A-/B1-/B2-Blockade daraus ableiten |


Die Datei wird **unverändert am ursprünglichen, bisher fehlenden Architekturpfad**
erhalten. Ihr Datum/Entwurfsstatus ist historisch: A/#87, B1/#90 und UI-B2/#7 sind
inzwischen integriert. Aktuell maßgeblich sind der [B1-API-Vertrag](../../api/human_review_v1.md)
und die [B2-Dokumentation](https://github.com/rf-data/personal-assistant-ui/blob/90816a1578bcf67739ee9acaa483c1635aa0c44b/docs/human_review_ui.md).
Der Import ist keine neue Reviewimplementierung, kein Merge von #88 und keine
Übernahme seines veralteten Plannachtrags. Kein vorhandenes Zieldokument ersetzt.

SHA/Größe stimmen mit Commitblob, vorab erfasster Dokumentversion und Zielbytes
überein. Text auf erkennbare Secret-/Raw-/Personendaten geprüft; kein solcher
Importbefund. Source-Worktree und offener Draft bleiben unverändert.
