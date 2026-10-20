# MAINT-04 – Sechs Einzelreviews, keine Bereinigung

19.10.2026, Europe/Berlin. Status: **`review_prepared – awaiting_operator_approval`**.
Git-/GitHub-Bezug: Backend `master` `b6fc464ef5217e3c1641e504d9f9c37989e0c4b1`; UI `main`
`af95415071e85a461579c0a1650fdd0efe6c25b9`. Der Gitgraphnachweis ist keine
Betreiberentscheidung. Keine Sicherung, Wiederherstellung oder Bestandslöschung
wurde genehmigt oder ausgeführt.

## Vergleich vor Einzelentscheidung

| ID | Scope / Ref | Beobachteter SHA = Erwartung | Ahead / Behind master | Historische Dokumentvarianten | Empfehlung / effektiv |
| --- | --- | --- | --- | ---: | --- |
| BR001 | Branch / `refs/heads/add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` | 0 / 171 | 3 | Review / Keep bis Einzelgate |
| BR011 | Branch / `refs/heads/docs/cs50-archive` | `8ba519ed04c04c92573594ebe74b69a3c00aab1b` | 0 / 104 | 9 | Review / Keep bis Einzelgate |
| BR107 | Remote-Ref / `refs/heads/add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` | 0 / 171 | 3 | Review / Keep bis Einzelgate |
| BR109 | Remote-Ref / `refs/heads/add_local_LLM` | `b3b59b66942e4470475cc41657f4caf515338c67` | 0 / 171 | 3 | Review / Keep bis Einzelgate |
| BR110 | Remote-Ref / `refs/heads/add_organizer` | `b3b59b66942e4470475cc41657f4caf515338c67` | 0 / 171 | 3 | Review / Keep bis Einzelgate |
| BR111 | Remote-Ref / `refs/heads/add_runpod` | `d35c43fb698a5f015e56b067fa9f22ad8c459edf` | 0 / 189 | 2 | Review / Keep bis Einzelgate |

BR001 und BR107 bleiben getrennte Objekte trotz identischem Namen und Commit.
Die vier Bindungen an `b3b59b6` sind keine gemeinsame Freigabe. Alle sechs
`ready_for_removal=false`; das ursprüngliche 239er-Inventar und dessen 103 Keep /
103 Review / 33 Archive werden weder umnummeriert noch umgestuft.

- [Einzelanalysen und objektgebundene Freigabeformulare](candidate_reviews.md)
- [Sechs maschinenlesbare Entscheidungsvorlagen](approval_matrix.tsv)
- [Sicherungs-/Restoreplan, ausschließlich Vorschlag](backup_restore_plan.md)
- Führende Historie: [MAINT-01](../maint01/README.md),
  [Dokumentversionen](../maint01/document_versions.tsv), [MAINT-02](../maint02/README.md),
  [239 unveränderte Ausführungszeilen](../maint02/execution_plan.tsv),
  [MAINT-03](../maint03/README.md) und [Betreiberentscheidungen](../maint03/operator_decisions.md).

## Tatsächliche Prüfung und Beweisgrenzen

Repository-origin `https://github.com/rf-data/Personal_Assistant.git`, Common-Gitdir
`$WORKSPACE/gmp_compliance/.git`, vollständiger lokaler Gitgraph (nicht shallow).
UI-origin und getrenntes Common-Gitdir `$WORKSPACE/personal-assistant-ui/.git`
verifiziert. `$WORKSPACE` bezeichnet den vom Betreiber bereitgestellten Workspace;
keine neuen Daten- oder Sicherungswurzeln abgeleitet.

Die beiden lokalen Refs per `for-each-ref`, die vier Remoterefs **per
`git ls-remote --exit-code --heads origin`** einschließlich tatsächlichem master
geprüft. Alle sechs SHAs entsprechen dem Auftrag. Drei unterschiedliche Commits
lokal vorhanden; lokale `merge-base`/`rev-list` gegen den bekannten Masterstand
`d654f05` ergeben jeweils Mergebase = Kandidat und null eigene Commits.
Der aktuelle master ist lokal nicht als Objekt vorhanden. Deshalb zusätzlich
**drei exakte authentifizierte GitHub-Commitvergleiche Kandidat...b6fc464**:
`behind_by=0`, Mergebase = Kandidat, 171 / 104 / 189 neuere Defaultcommits.
Ahead/Behind in obiger Tabelle sind in Kandidatenrichtung angegeben. Kein Fetch,
kein Trackingupdate; keine bloße Fortschreibung alter Behindwerte.

95 Backend-PRs und 115 Issue-Endpunktdatensätze vollständig paginiert gelesen
(95 PRs, 20 eigenständige Issues; PM-03-Anlagen bereits enthalten).
Heads und Bases sowie exakte Head-SHAs geprüft. Keine offene direkte PRbindung
an die sechs Refs. Ein historischer SHAbezug auf gemergten #4 ist von einer
namensgleichen Branchbindung getrennt; #38 nennt die BR011-Basis historisch.
Literalabgleich in diesen Issue-/PRtexten ist kein vollständiger Nachweis gegen
externe Links, fremde Klone, Jobs oder absichtlich anders benannte Aufgaben.

Registrierte Worktrees beider Repositories gelesen: kein Kandidatenref angehängt.
Nur Prozess-CWD-Symlinkmetadaten gelesen, keine Argumente, Environ- oder
Open-File-Inhalte. Keine Zuordnung zu einem Kandidatenworktree gefunden; da keiner
registriert ist, beweist dies keine Nichtnutzung. Betreiber-/Fremdhostnutzung bleibt
**not_verified**. Kein temporärer Checkout zur Inhaltsprüfung erzeugt.

MAINT-01-Versionstupel mit lokalem Commit/Blob und SHA256 verifiziert; gegen die
vollständige Gitblobiliste von master abgeglichen. Nur Dokumentpfade gelten als
mögliche Dokumentduplikate: ein leeres README wird nicht wegen identischer leerer
Pythondateien als archiviert gewertet. Vier gezielte Überschrifteninspektionen
(Checkpointvertrag, Pipelineabschluss, Integrationsstatus, alte Loggernotizen)
belegen historische Themen, keine fachliche Entbehrlichkeit. Volltexte und
möglicherweise vertrauliche alte Inhalte werden nicht kopiert. Aktuelle anders
benannte Fassungen sind ohne Bytegleichheit keine Ersatzbelege.

Ohne angehängten Kandidatenworktree gibt es keinen zugehörigen Datenroot zur
Freigabe. Die abgefragten Primär-Gitstatus sind sauber; Inhalte
ignorierter/privater Dateien wurden nicht gelesen und ihre Entbehrlichkeit nicht geprüft. Ein Ref speichert keine
untracked/ignorierten Daten. Kein unbekannter Datenbestand wird als entbehrlich
bewertet. Beide Backend-Stashes und alle fremden Worktrees bleiben erhalten.

## Validierung und Integration

Geprüft: exakt die sechs vorgegebenen IDs und Identitäten, vollständige Commit-/
Tree-SHAs, SHAgleichheit, Graphbelege, Dokumenthashes, getrennte BR001/BR107-Gates,
UTF-8/LF-TSV, JSONzellen, lokale Dokumentverweise und Whitespace. Finale
Read-only-Nachprüfung vergleicht Refs, Registrierungen, Primär-HEADs/-Status und
Stash-IDs mit dem Eingangssnapshot. Keine Anwendung geändert; keine Ruff-,
Pytest-, Bundle-, Restore- oder Löschtests behauptet.

Vier ausschließlich neue Dokumentationsdateien, eigener Remote-Dokumentationsbranch
`docs/maint04-first-candidate-review`; kein lokaler Branch oder Worktree angelegt.
**Die Anweisung „Keine PRs schließen oder mergen“ bleibt maßgeblich:** Bericht
über regulären PR vorlegen, Integration in master bis Betreiberreview offen lassen.
Der eigene Branch bleibt bis zum tatsächlich verifizierten Merge erhalten.
Danach ist ausschließlich sein eigener Lifecycle zulässig; keinerlei Freigabe
für die sechs Bestandsrefs oder andere MAINT-Objekte. Offener PR ist keine
Integration. Der Abschlussstatus bezeichnet nur die vorbereiteten Einzelreviews.

Unverändert geschützt: übrige 233 Inventarobjekte, zehn ungültige Registrierungen,
beide Stashes, alte Backup-/Recoverydaten, Primärcheckouts, C24-06-A mit UI,
Drafts #72/#88/#89, aktive PM-Aufträge, MAINT-02-Branch/-Worktree und beide
`docs/agent-documentation-lifecycle`-Remoterefs. Keine globale Bereinigung.
