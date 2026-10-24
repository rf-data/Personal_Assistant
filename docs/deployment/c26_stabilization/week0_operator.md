# Betreiber-Checkliste CS50P Week 0

**GO: vorhandene Belege prüfen und reine Preflights ausführen.
NO-GO: Download, ZIP-Import oder Pilotdispatch ohne separate konkrete Freigabe.**
Alle Variablen unten müssen auf bestätigte, bereits vorhandene private Pfade
zeigen. Die Rezepte wurden nicht auf einem Produktionshost ausgeführt.

- [ ] Producer und Worker auf dieselbe genehmigte SHA/Image-Digest-Version
  binden. Für die fünf PSet-Children muss #155 auf beiden Seiten vorhanden sein;
  Overview-Snapshot-Opt-in, URL, stabiler Provenienzlabel und Rawhash müssen gleich
  sein. [Bindungsvertrag](../c26_final/assignment_snapshots.md) verwenden.
- [ ] Zielmount und Kapazität frisch messen. Mindestreserve **5 GiB**, ein
  konkreter Ein-Material-C18-Batch derzeit mindestens **7.022 GiB frei**, inklusive
  bestehendem 2-GiB-Jobbudget. Auf dem tatsächlichen Ziel prüfen, nicht auf Drive
  oder anhand der lokalen Codex-Messung. Inodes und Linux-/WAL-Eignung bestätigen.

  ```sh
  : "${C26_PYTHON:?Vorhandene passende Pythonumgebung}"
  : "${C26_TARGET_PARENT:?Bestaetigter existierender Zielmount}"
  : "${C26_BATCH:?Gepruefter bestehender Ein-Material-Batch}"
  df -h "$C26_TARGET_PARENT"
  df -i "$C26_TARGET_PARENT"
  "$C26_PYTHON" -m scripts.c26_storage_preflight \
    --target-parent "$C26_TARGET_PARENT" --purpose week-pilot --batch "$C26_BATCH"
  ```

  Exit 3 = blockiert, Exit 4 = weitere Betreiberprüfung; kein Exit ist eine
  Ausführungserlaubnis. Limits nicht absenken und nichts automatisch bereinigen.
- [ ] Bestehende SourceApprovals privat prüfen: exakte Material-/Source-ID,
  Kurs `cs50_python`, Original-URL, tatsächlicher Raw-SHA256, Prozessrecht und
  aktuelle Approval-/Usage-/License-/Robots-/Retention-/Revocationreferenzen.
  B6-Policyprüfung benötigt außerdem gültigen Zeit-/Scope-/Widerrufsstatus.
  Die versionierten Beispiele enthalten **keine produktiven Grants**;
  Laufzeitkatalog/Grants wurden nicht bereitgestellt. Fehlendes als
  `operator_action_required` belassen, keine Freigaben aus Links erzeugen.
- [ ] Vorhandene Rohdaten/Receipts ausschließlich lesen und eindeutig binden:
  echte Notes-/PSet-Exporte sind belegt; die fünf Aufgabenlinks ersetzen keine
  genehmigten Aufgaben-Rawdateien. Vollständige zusätzliche Aufgabeninhalte,
  PDF-Originale und SRT/TXT-Transcripts sowie deren Receipts/Grants fehlen im
  bereitgestellten Abnahmebestand. Fehlende Daten als Lücke dokumentieren und
  separat bereitstellen lassen. Zehn manuelle ZIPs bleiben unverändert; dieser
  Auftrag startet keinen Import. Medien bleiben im bestehenden Media-last-Pfad.
- [ ] Bestehende B6-/C18-Prüfungen auf den expliziten vorhandenen Konfigurationen
  ausführen; Ausgabe privat auswerten. Kein `probe`, `execute`, `resume`,
  `download`, `seal`, Workerstart oder `--confirm`:

  ```sh
  : "${C26_COURSE_REQUEST:?Gepruefter bestehender B6-Request}"
  : "${C26_APPROVALS:?Bestehende aktuelle Freigabedatei}"
  : "${C26_CONFIG:?Bestehende C16-Konfiguration}"
  : "${C26_TOKEN_FILE:?Bestehende individuelle private Token-Datei}"
  : "${C26_SOURCE_REF:?Explizites bereits genehmigtes Workflowbundle}"
  "$C26_PYTHON" -m scripts.cs50_course preflight \
    --request "$C26_COURSE_REQUEST" --approvals "$C26_APPROVALS"
  "$C26_PYTHON" -m scripts.deployment check --config "$C26_CONFIG"
  "$C26_PYTHON" -m scripts.cs50_workflow preview \
    --config "$C26_CONFIG" --token-file "$C26_TOKEN_FILE" \
    --source-ref "$C26_SOURCE_REF"
  ```

  C16-Check allein nutzt nur seinen allgemeinen Mindestplatz; er ersetzt den
  C26-Kapazitätscheck nicht. Pending/blocked/operator_action_required, Stale,
  Hash-/Grantfehler, Quarantäne oder fremde laufende Arbeit stoppen den Ablauf.
- [ ] Erst danach separate Betreiberentscheidung für **genau ein benanntes
  bereits vorliegendes HTML-Material**: vorgeschlagen sind die Lecture-0-Notes
  (`https://cs50.harvard.edu/python/notes/0/`, vorhandener Export mit 71,718 Bytes).
  Die belegten IDs und der Raw-SHA256 stehen in `pilot_candidate.v1.json`;
  diese Datei ist ausdrücklich keine SourceApproval. Einen dazu passenden
  Ein-Quellen-Batch, einen C16/C18-Job,
  Parallelität 1, Queuegrenze 1, bestehende Parser-/Zeit-/Byte-/Speicherlimits und
  unveränderte 5-GiB-Reserve. Freigabe muss SHA/Digest, Batchhash, Grantreferenzen,
  Zielroot, Verantwortlichen, Zeitfenster und Abbruchkriterien nennen. Kein
  automatischer Folgebatch oder Retry. Quarantäne, SQLite-/Kapazitätsfehler oder
  unerwartete Ergebnisse stoppen; Rohdatei → Normalisierung → Quality → Handoff
  samt Job-/Stagejournal abnehmen. **Aktuell bleibt dieser Pilot NO-GO.**
