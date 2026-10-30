# C27-R10 – Integrationsbewertung

Entscheidung: **INTEGRATION_REQUIRED**. Das ist eine offene Entscheidung zur Koexistenz zweier Implementierungen; kein Nachweis eines Konflikts mit dem heutigen Live-Defaultbranch.

## Lokal festgestellter Gitstand

| Referenz | Commit | Bedeutung |
|---|---|---|
| `HEAD` | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | C27-Basis, alle 62 Änderungen noch uncommittet |
| `master` | `c1007efdbac3c1544020f328a3a1347e481797ba` | veralteter lokaler Branch |
| `origin/master` | `a8af1d9372eb435d3e1331c33b047d21120d57c2` | nur lokal gespeicherter Remote-Tracking-Stand |
| `fix/c27-acceptance-exports` | `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835` | lokal bekannte konkurrierende Implementierung |

HEAD und origin/master: links/rechts **0/0**. Keine der 59 unversionierten Dateien existiert in diesem gespeicherten origin/master. Der lokale master liegt **173 Commits** zurück; er ist keine belastbare aktuelle Zielbasis. `origin/HEAD` fehlt.

Der tatsächliche Defaultbranch ist laut Repositoryauftrag `master` für `rf-data/Personal_Assistant`. Sein heutiger Live-Commit, offene/geschlossene PRs, Branchschutz und aktuelle Reviews sind **nicht online verifiziert**. Es gab weder Netzwerk noch Fetch. Der ältere Audit-Snapshot in `docs/audit/remote_snapshot.v1.json` belegt nur den damaligen master-Stand `78b35a53…`, nicht den heutigen Zielstand. C26-LS-01 nennt außerdem die historische Basis `1584a2807c8f9d75604ab17a4ea239d8f4a0882b`; diese Herkunft ersetzt die aktuelle C27-Basis `a8af1d9…` nicht. R08/R09 validieren den schmutzigen C27-Arbeitsstand auf dieser Basis, keinen bereits integrierten Commit.

## Drei Pfadüberschneidungen

Gemeinsamer Commitvorfahr mit fix/c27-acceptance-exports: `e502aa915ad0e928dbe7e92eacd44fff0152912b`; Divergenz HEAD/fix: **12/19** Commits. Zwischen den ausschließlich bereits committeten Pfadänderungen gibt es keine Überschneidung. Erst die noch unversionierten C27-Kandidaten erzeugen diese drei unterschiedlichen add/add-Inhalte:

| Pfad | Bewertung |
|---|---|
| `src/lecture_summary/__init__.py` | konkurrierende Paket-/Exportverträge; keine identische Datei |
| `src/lecture_summary/models.py` | unterschiedliche Datenmodelle und API-Verträge; semantische Entscheidung nötig |
| `tests/test_lecture_summary.py` | konkurrierende zentrale Testsuiten; keine automatische Auswahl einer Suite |

Die bereits abgeschlossenen `git merge-file -p --diff3`-Proben auf reinen /tmp-Dateien lieferten jeweils rc=1 und einen Konfliktbereich. Sie wurden übernommen, nicht wiederholt. Sie bilden keine vollständige Gitintegration nach. Namespaceanalyse: Die andere Implementierung benötigt u.a. `Draft`, `Summary`, `cache_key`, `Artifact`, `Selection`, `Evidence`; diese fehlen im C27-Modell. Gleichnamige `Catalog`/`Claim` machen die APIs nicht kompatibel. Ein textuell aufgelöster Konflikt beweist keine semantische Integration.

## Erforderliche Entscheidung vor Ausführung

Der Benutzer/Architekturreview muss auswählen: diesen C27-Vertrag als eigenständigen Ersatz vorschlagen, die andere Linie separat erhalten oder eine bewusste API-/Namespaceintegration beauftragen. Kein pauschales Cherry-pick oder Überschreiben der anderen Linie. Herkunftsbelege der vier selektiv übernommenen CS50P-Komponenten bleiben erhalten; deren Objektvergleich gegen `143d3412c668bb652eba7929742a3a886031c372` ist bereits erfolgreich.

Gegen den **unveränderten lokal gespeicherten** origin/master wäre ein separater PR-Vorschlag nach Freigabe grundsätzlich möglich. Daraus folgt keine heutige Live-Mergbarkeit und keine Pflicht, alle 19 fremden Commits zu integrieren. Die Gesamtentscheidung bleibt wegen der offenen API-/Scopewahl INTEGRATION_REQUIRED. Erst ein später ausdrücklich autorisierter Abgleich des echten Zielstands kann diese Entscheidung aktualisieren. Bereits erfolgreiche Tests brauchen nur bei tatsächlicher Basis-/Inhaltsänderung gezielt ergänzt zu werden.

Keine Git-Artefakte erzeugt oder entfernt. Bestehender Branch, Worktree und konkurrierende Linie bleiben erhalten. Integration/Dokumentation auf master und Cleanup bleiben gemäß AGENTS.md ausstehend; das ausdrückliche Gitverbot dieses Auftrags hat Vorrang vor dem allgemeinen Integrationslebenszyklus.
