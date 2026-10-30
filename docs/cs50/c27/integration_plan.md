# C27 Fortsetzung: gezielter Integrationsplan

Stand 2026-10-29, Ausgangs-HEAD a8af1d9, vorhandener Worktree
`Personal_Assistant-c27-cs50-learning`, Branch `feat/c27-cs50-learning-pipeline`.
Die Bestandsaufnahme aus Phase 0 bleibt gültig. `GATE_0_FAILED` wird für diese
Fortsetzung durch unabhängige Gates A (Verträge), B (Summarizer) und C
(Echtdaten) ersetzt. Gate C blockiert weder B noch die Rolloutplanung.

1. Lokales Reviewverzeichnis ausschließlich lesen; Inventare/Pläne und alle
   berichteten Rohdaten-/Snapshot-Hashes vergleichen. Keine Downloadfreigabe aus
   Planvorlagen ableiten.
2. Übergabepatch C26-LS-01 SHA-256
   `dd11706ba7575e31ae786e5df860fc51f7c34ddbf50c9f3c35a5e644f4aa3f57`
   prüfen. Vollständiges `git apply --check` scheitert ausschließlich an
   `.gitignore:303`: Kontext enthält CS50P-07-Ausnahmen, während C27 bei PM-02
   endet. Kein semantischer Widerspruch zwischen Ignore-Regeln.
3. Isolierten Datei-Export von C27 unter `/tmp` erstellen (kein Git-Worktree,
   keine Branches). Patch mit `--exclude=.gitignore` prüfen/anwenden. Nur den
   zehnzeiligen C26-LS-01-Block ergänzen; alle C27-Regeln unverändert erhalten.
4. Alle 27 übrigen Übergabedateien gegen `handoff-files.json` bytegenau prüfen;
   `.gitignore` als einzige geplante Abweichung separat nachweisen. Offline-
   Summarizer-Smoke im isolierten Stand; dann denselben Stand in C27 anwenden.
5. CS50P-07/08-Komponenten nur selektiv übernehmen, wenn im C27-Vertrag nötig.
   Download-/Runtime-/Deployment-Änderungen nicht pauschal übernehmen. Lokale
   Verifikation → vorhandene Parser → vorhandener Qualitäts-Handoff → Summary-
   Katalog testen. ContentBlock, ContentLocator, NormalizedDocument,
   TranscriptDocument und MaterialBinding unverändert weiterverwenden.
6. Unit-, UI-AppTest-, Offline-Integrations- und optionale echte lokale Week-0-
   Tests mit Netzwerkguard; kein LLM-Provider, Download, Push, Merge oder Betrieb.
7. Abnahmebericht, Integrationsnachweis, Testmatrix, Pilot-/Rollout- und
   Übergabeanleitung unter `docs/cs50/c27/` sichern. Reale Rohdaten und lokale
   Ausgaben bleiben extern. Default-Branch-Integration/Cleanup bleiben wegen
   explizitem Push-/Mergeverbot offen; vorhandenen Branch/Worktree behalten.
