# C23.0 – Dokumentations- und Konsistenzprüfung

Stand 17.10.2026. **Nur Planungsprüfung, keine Anwendungstests oder Dienste.**
Ausgangsbranches und Remote-Abfragen sind im [Snapshot](c230_snapshot.v1.json)
und [Statusabgleich](status.md) dokumentiert. C19–C22-Testzahlen wurden als
historische, konkret verlinkte Nachweise übernommen, nicht neu ausgeführt.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Default-Branch-/PR-Abgleich beider Repositories | Backend `476f0a0d`, UI `14ccfc20`; C22 in beiden gemergt, PR #72 Draft; alte #6/#9/#10/#11 offen |
| Eigenständige Issues | null in beiden vollständig gelesenen Antworten; PR-Einträge herausgefiltert; keine Neuanlage/Schließung |
| Plan-JSON | 32 eindeutige Plan-IDs: zehn Parents C23–C32 und 22 Kinder nur C23–C26; 6/5/4/7 Kinder; keine vorweggenommenen Issue-URLs |
| Abhängigkeiten | alle referenzierten Plan-IDs vorhanden, gerichteter Graph ohne Zyklus; Parent-/Repository-/Target-Zuordnung konsistent |
| Operativer Markdownentwurf | Titel, Typ und alle Akzeptanzpunkte mit JSON abgeglichen; C24-04 ausdrücklich optional, C26-01 als technische Schuld |
| Templates | drei inhaltlich identische Paare in beiden Repositories; YAML-Frontmatter parsebar, keine noch nicht vorhandenen Labels erzwungen |
| Markdown | 149 lokale Linkziele/Heading-Anker über 21 geänderte Dateien geprüft; Codefences geschlossen |
| Gültigkeitsgrenzen | C23–C32 geplant, Knowledge optional/zurückgestellt, PostgreSQL unentschieden; keine neue produktive Freigabe aus Merge/Tests |
| Änderungsumfang | ausschließlich README, Dokumentation, Issue-Templates und Ignoreausnahmen für öffentliche Planungs-JSONs; keine fachlichen Python-/Dependency-/Runtimeänderungen |
| Dateiformat | UTF-8, LF und Abschlussnewline; `git diff --check` in beiden Repositories bestanden |
| GitHub-Verwaltung | null Issues, Projects oder Milestoneobjekte angelegt/verändert/geschlossen; nur eigene Dokumentations-Review-PRs |

Die lokale Prüfung verwendet Python-JSON/Regex/Graphvalidierung und vorhandenes
PyYAML ausschließlich für Template-Frontmatter; kein Anwendungsimport, keine
Installation und keine Netzverbindung durch den Validator. Reproduktionsansatz:

```sh
python3 -m json.tool docs/planning/issue_plan.v1.json > /dev/null
python3 -m json.tool docs/planning/c230_snapshot.v1.json > /dev/null
git diff --check
# Analog im UI-Repository: git diff --check und Template-Frontmatter prüfen.
```

Zusätzlich wurden die obigen Struktur-, Link-, Anker-, Templategleichheits- und
Graphprüfungen tatsächlich durchgeführt. Die einfache JSON-Prüfung allein wäre
kein Nachweis dieser zusätzlichen Eigenschaften. Keine Ruff-/Pytest-Erfolge
behauptet: fachlicher Pythoncode wurde nicht geändert, Anwendungstests waren
nicht Teil dieses reinen Dokumentationsauftrags.

## Was diese Prüfung nicht beweist

Projects-/Milestone-Inventar ist **unbekannt**, weil Connectorendpoints fehlen;
Repositoryrechte beweisen keinen Projects-v2-Zugriff. Beispiel-`gh`-Kommandos im
[Ausführungsplan](github_execution.md) wurden mit offizieller Syntax abgeglichen,
nicht ausgeführt; tatsächliche Scopes, Feld-/Item-IDs und gespeicherte Views sind
vor Schritt B erneut zu prüfen. Keine GitHub-Issuenummer oder Project-URL erfunden.

Externe PR-/Dokumentationslinks wurden aus den abgefragten Metadaten und
bestehenden Nachweisen übernommen, nicht pauschal als live geprüfte Webseiten
gezählt. UI-Planungsänderungen hängen vom Backend-Dokumentations-PR ab; gemeinsame
Default-Branch-Links werden nach dessen Merge zum aktualisierten Plan führen.

Die [offenen Entscheidungen](governance.md) und alle C22-/Realquellen-/Fachevaluations-
Blocker bleiben sichtbar. Schritt B braucht gemäß Auftrag eine ausdrückliche
Freigabe des konkreten Planstands. Kein automatischer Merge, Deploy oder
historischer Issue-/PR-Abschluss.
