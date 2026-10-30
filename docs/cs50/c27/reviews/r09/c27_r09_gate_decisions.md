# C27-R09 – Technische Gateentscheidungen

| Gegenstand | Entscheidung | Tragende Evidenz |
|---|---|---|
| Sechs historische Fälle | **ALL_RESOLVED** | Sechs exakte historische Node-IDs, bytegleiche Testquellen, sechs neue JUnit-Erfolge mit Originalassertions |
| F04 | **VERIFIED_FIXED** | Zwölf ursprüngliche R07-Verletzungen im Exportvertrag geschlossen; elf R08-Erfolge plus frischer CAP-CLI-Canary; 75 URLwerte erhalten |
| C27-Codeintegration | **READY_FOR_PR** | Alle sechs historischen Evidenzlücken geschlossen; 23/23 CAP-Regressionen, frischer Canary und realer CLI erfolgreich; keine nachgewiesene neue Produktregression |
| CS50P Week 0 | **PARTIAL** | Lokale TXT-Auswahl erfolgreich; beide vollständigen HTML-Selektionen am Chunklimit; Materialvollständigkeit und Fachabnahme fehlen |
| Multiweek/Multicourse | **PLANNING_ONLY** | Keine echte Mehrwochen-/Mehrkursabnahme; Budget-/Resume-/Kursmatrixnachweise weiterhin offen |
| Produktion | **NOT_APPROVED** | Kein Produktionsgate, keine Betriebs-/Restore-/Releasefreigabe und keine entsprechende Autorisierung |

`READY_FOR_PR` ist ausschließlich die technische Bereitschaft des vorgefundenen C27-Arbeitsstands für den regulären Reviewprozess. R08-CAP hielt C27 wegen exakt der sechs jetzt geschlossenen historischen Evidenzlücken BLOCKED. Für diese Codeintegration ist damit kein verbleibender nachgewiesener PR-Blocker aus dem geprüften R07/R08-Vertrag belegt. Es handelt sich um eine begrenzte unabhängige Validierung auf bestehender Evidenz, keinen neuen vollständigen Security-/Produktionsreview und keine Behauptung eines vollständig grünen Repositorys.

Der Arbeitsstand enthält weiterhin bereits vor R09 vorhandene modifizierte und unversionierte Dateien auf `feat/c27-cs50-learning-pipeline`, HEAD/Basis `a8af1d9372eb435d3e1331c33b047d21120d57c2`. Alle 62 C27-Manifestdateien entsprechen R08 und der vollständige Worktree entspricht CAP. Keine Commits, Pushes, PR-Erstellung, Merges, Rebases oder Resets durchgeführt. READY_FOR_PR autorisiert keinen dieser Schritte.

F04 wird für den dokumentierten Metadaten-/Provenienzvertrag öffentlicher JSON-/Markdown-/UI-/CLI-Exporte verifiziert geschlossen. Private Originalprovenienz bleibt absichtlich privat erhalten; fachliche Quell-/Claimtexte sind laut Vertrag kein allgemeiner Secretscanner. Bereits früher publizierte Exporte werden nicht rückwirkend verändert oder als automatisch bereinigt ausgegeben. Die ursprüngliche R07-Recovery versiegelt den bei Recovery gesicherten Stand und beweist keine rückwirkende Integrität seit dem alten Sitzungsende; diese Einschränkung bleibt erhalten. R08- und CAP-Nachweise schließen die konkrete technische Exportlücke.

Globale Mypy-Diagnosen: **6.104 unverändert**, kein globaler PASS. Der gesicherte R06→R08-Vergleich weist null neue und null entfernte Diagnosen aus. Diese bekannte technische Schuld wird nicht als neue C27-Regression oder als grüner Typstatus ausgegeben. Die beiden bestehenden Regression-Skips bleiben sichtbar. Innerhalb des ausdrücklich begrenzten R09-Prüfumfangs wird daraus kein neuer PR-Blocker abgeleitet.

## F06–F14 bleiben den vorhandenen späteren Gates zugeordnet

Verbindliche Quellen: R05 `c27_r05_findings.json`, `c27_r05_gate_decisions.md` und übernommene R03-Befunddefinitionen unter dem manifestverifizierten R07-Vorgängerbestand. R05 bezeichnet sie ausdrücklich als bekannte Einschränkungen/spätere Gates. Es gibt im geprüften Stand keine konkrete neue Regression, die ihre Umklassifizierung zu PR-Blockern rechtfertigt.

| Befund | Weiterhin offenes Thema | Zuständiges Gate |
|---|---|---|
| F06 | Katalog und UI verlieren bekannte blockierte bzw. fehlende Materialien | Week-0-Material-/UI-Abdeckung; späteres Rollout |
| F07 | Gesamtpatch ist reproduzierbar, aber nur temporär gesichert | Dauerhafte Sicherung und spätere reguläre PR-/Defaultbranchintegration |
| F08 | Vollständige echte HTML-Auswahl überschreitet bestehende Chunkgrenze | Week-0-HTML-Segmentierung/Chunkgrenze; späteres Rollout |
| F09 | ZIP-Member sind technisch geprüft, aber ohne Summary-Quellenmapping | Week-0-ZIP-Quellenmapping; späteres Rollout |
| F10 | Vier Rohdateien belegen keine vollständige Week 0 | Week-0-Materialvollständigkeit; späteres Rollout |
| F11 | Keine fachliche Summary-Abnahme und kein echter Provider-Nachweis | Fachabnahme und realer Provider-Nachweis; späteres Rollout |
| F12 | Kein persistentes Kurs-/Wochenbudget und kein bezahltes Abschnitts-Resume | Multiweek-/Multicourse-Budget und bezahltes Resume |
| F13 | Rolloutplan konkretisiert spätere CS50x-/CS50-Web-Abnahme nicht | Eigene spätere Kurs-/Abnahmematrix |
| F14 | Eigene Produktionsfreigabe fehlt als konkretes Rolloutgate | Gesonderte Produktionsfreigabe |

F07 bedeutet insbesondere: bestehende Home-Sicherungen ersetzen keine spätere reguläre Integration in `master`. Die neue R09-Ablage ist temporär. Die auftragsspezifischen Grenzen untersagen hier sämtliche Gitintegration; Dokumentation im Defaultbranch und dauerhafte Übernahme bleiben getrennt autorisierte Folgearbeit. Dies ist kein zusätzlich erfundener technischer PR-Blocker und keine Behauptung eines vollständigen Projektabschlusses.

## Erhaltung und Sicherung

`preservation.json` bestätigt identische Gitdaten einschließlich Indexhash, Branch, HEAD, Refs und Worktreezuordnung; identische 1.355 Worktreeeinträge; identische 17 reguläre Rohdateien plus Verzeichnis; identische 68.864 Einträge im gesamten vorhandenen Home-Handoff. Modi, Linkziele und vorhandene Caches werden mitgeprüft; Symlinks nicht verfolgt und FIFOs nicht geöffnet. R08/R08-CAP/R07-Manifeste sind vor und nach der Prüfung gültig.

Keine eigenen Git-Artefakte angelegt oder entfernt. Vorhandener Branch, Worktree, Audits und Caches bleiben erhalten. Neue Testausgaben, Berichte und Prüfhilfen bleiben ausschließlich unter `/tmp/c27-review-r09.rb0c0se8`. Der bevorzugte Homepfad liegt außerhalb der erlaubten Schreibwurzeln; daher erlaubter /tmp-Fallback. /tmp ist kein dauerhaftes Backup. Keine Freigabeanforderung oder Integration wird aus dieser technischen Entscheidung abgeleitet.
