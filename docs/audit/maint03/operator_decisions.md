# MAINT-03 – Noch erforderliche Betreiberentscheidungen

Alle ursprünglichen 239 IDs behalten ihre MAINT-02-Vorschläge. Keine ID erhält eine
Remove-Freigabe durch diesen Auftrag. [Einzelbeobachtungen](individual_decisions.tsv),
[geprüfter Umfang und Grenzen](README.md), [vorherige Planung](../maint02/maint03_execution_plan.md).

## Erste sechs mögliche Reviewentscheidungen

Dies sind exakte, erneut SHA-geprüfte Bindungen, **keine erlaubten Löschbefehle**.

| Candidate-ID | Repository / Typ | Vollständiger Ref | Erwarteter SHA |
| --- | --- | --- | --- |
| BR001 | Backend / lokaler Branch | `refs/heads/add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` |
| BR011 | Backend / lokaler Branch | `refs/heads/docs/cs50-archive` | `8ba519ed04c04c92573594ebe74b69a3c00aab1b` |
| BR107 | Backend / Remote-Ref | `refs/heads/add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` |
| BR109 | Backend / Remote-Ref | `refs/heads/add_local_LLM` | `b3b59b66942e4470475cc41657f4caf515338c67` |
| BR110 | Backend / Remote-Ref | `refs/heads/add_organizer` | `b3b59b66942e4470475cc41657f4caf515338c67` |
| BR111 | Backend / Remote-Ref | `refs/heads/add_runpod` | `d35c43fb698a5f015e56b067fa9f22ad8c459edf` |

Je ID kann der Betreiber zunächst Keep oder einen konkreten weiteren Reviewumfang
bestätigen. Keine pauschale Gruppenfreigabe aus dieser Tabelle ableiten. Auch bei
`ahead=0` sind bestätigte Nichtnutzung, Sicherung und Restore separat nötig.
BR012 bleibt wegen untracked Completion-Audit-Dokumenten, BR101 wegen ungültigem
Completion-Worktree mit `workers`-Restverzeichnis zusätzlich gesperrt.

## Erforderlicher Einzelbeleg vor Remove

Für **jedes** ausdrücklich ausgewählte Objekt separat bereitstellen:

- Candidate-ID, Repository, Typ, voller Ref/Pfad und erwarteter vollständiger SHA.
- Namentlich verantwortliche Person und konkretes freigegebenes Zeitfenster.
- Aktuelle, tatsächlich bestätigte Nichtnutzung durch Aufgaben, Prozesse und
  Betreiber sowie Entscheidung über Dokumente und private/ignorierte/untracked Daten.
- Exakte zulässige private Backup- und Recoveryziele außerhalb beider Repositories,
  Rechte-/Scope-/Aufbewahrungsfreigabe; keine geratenen Pfade oder vorhandenen Ziele
  überschreiben. Die Benennung eines Ziels allein autorisiert noch keinen Restore.
- Bestehender Sicherungsbeleg mit Bundle-SHA256 und vollständiger Commitbindung,
  erfolgreicher tatsächlicher Restorebeleg in einem autorisierten leeren privaten
  Testrepository. Falls diese fehlen: zuerst genau diese Sicherungs-/Restoreaktion
  separat autorisieren; noch keine Löschung freigeben.
- Exakter erlaubter Einzelbefehl. Lokal erwarteten Alt-SHA, remote explizites
  SHA-Lease der Löschrefspec binden; fehlende Git-Schreibrechte separat lösen.
  Keine Commitumschreibung, pauschale Force-Push-/Prune-/Cleanfreigabe.

Vor Umsetzung trotz aller Belege vollständigen aktuellen Phase-A-Abgleich erneut
prüfen. Geänderter SHA, neue PR-/Worktreebindung oder unbekannter Zustand sperrt.
Ein Bundle enthält weder ignorierte noch untracked Daten; `bundle verify` allein
ist kein Restoretest. Vorhandene Gitobjekte ersetzen keinen Sicherungsbeleg.

## Übrige Bestände

- 103 ursprüngliche Keep-Zeilen: unverändert behalten. Primaries, C24-06-A inklusive
  UI, aktive PM-Arbeit, offene Drafts und Historie haben keinen Cleanupauftrag.
- 103 Review-Zeilen: Owner-/Nutzungs-/Dokument-/Daten-/Restorefragen offen;
  bei unbekannter Antwort Keep. Auch fehlende Live-Refs nicht aus Tabellen löschen.
- 33 Archive-Zeilen: Treegleichheit erneut bestätigt, exakte Commits/Historie bleiben
  erhalten. Fachlicher Erhaltungsumfang und Archiv-/Restoreauftrag fehlen.
- Zehn ungültige Registrierungen: Mount/Umbenennung, Reparatur, separater frischer
  committed Checkout oder eventuelle spätere Entfernung **einzeln** entscheiden.
  Kein globales Prune oder manuelles Löschen unter `.git/worktrees`.
- Beide Stashes und alle alten Backup-/Recoverydaten behalten; keine Apply/Pop/Drop-
  oder Datenbereinigungsaktion.

## Seit MAINT-02 hinzugekommene, ausgeschlossene Objekte

Diese fünf Objekte gehören nicht zu den alten 239 IDs und erhalten hier weder
neue Cleanup-ID noch Genehmigung. Sie sind historische bzw. fremde Aufträge:

| Repository / Typ | Identität | SHA |
| --- | --- | --- |
| Backend / Branch | `refs/heads/docs/maint02-cleanup-verification` | `0308217d2213b7a2d6e39b731ec22f640b8a4a3d` |
| Backend / Trackingref | `refs/remotes/origin/docs/maint02-cleanup-verification` | `0308217d2213b7a2d6e39b731ec22f640b8a4a3d` |
| Backend / Worktree | `$WORKSPACE/Personal_Assistant-maint02` | `0308217d2213b7a2d6e39b731ec22f640b8a4a3d` |
| Backend / Remote-Ref | `refs/heads/docs/agent-documentation-lifecycle` | `46a43e149b1a0ccd56dc20201b79c422d8f4df75` |
| UI / Remote-Ref | `refs/heads/docs/agent-documentation-lifecycle` | `ceacaf586a56465ccf444d852f5bca03a3e124b2` |

Das Fehlen des alten PM-02-Remoterefs ist bereits im Eingangssnapshot beobachtet.
Die Integration von PM-01/02, MAINT-01/02 und Agentenanweisungen autorisiert keine
Entfernung dieser früheren Arbeitsumgebungen durch MAINT-03.
