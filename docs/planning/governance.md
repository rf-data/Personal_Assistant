# Pflegeprozess und noch nötige Entscheidungen

## Zuständigkeit der Artefakte

| Artefakt | Autoritative Aussage | Nicht daraus ableiten |
| --- | --- | --- |
| `docs/ROADMAP.md` | Strategie, Reihenfolge, Meilensteinziele und Akzeptanzgrenzen | täglicher Taskstatus oder automatische Deploymentfreigabe |
| GitHub Issues | operative Aufgabe, Scope, Abhängigkeiten, Akzeptanz und fachlicher Owner | pauschale Zusage aufgrund eines PR-Merges |
| gemeinsames GitHub Project | aktueller Arbeitsstatus / Priorität / Workstream / Target milestone | fachliche Wahrheit oder Ersatz für Produktionsfreigabe |
| Pull Requests | konkrete Implementierung/Dokumentation, Review und referenzierte technische Nachweise | abgeschlossene fachliche Evaluation ohne unabhängige Referenzen |
| Tests/CI | automatisierte technische Prüfung mit Daten-/Umgebungs-/Versionsbezug | Produktivfähigkeit oder Modellqualität aus bloßen synthetischen Erfolgen |

`planning/issues.md` und `issue_plan.v1.json` sind bis Schritt B ein **Entwurf**.
Nach Anlage werden die echten Issue-URLs ergänzt; danach sind Issues die einzige
operative Aufgabenquelle. Die Markdown-Vorschau bei Planänderungen aus denselben
JSON-Feldern aktualisieren; keine dauerhafte zweite Taskverwaltung pflegen.
Archive und Testberichte behalten ihren historischen Stand.

## Einfacher Pflegezyklus

1. Vor Arbeitsbeginn bestehendes Issue/PR und Scope prüfen. Akzeptanz,
   Abhängigkeiten und fehlende Freigaben aktualisieren. Ready erst bei geklärtem
   Umfang, Zuständigkeit und erfüllten Startvoraussetzungen.
2. Während Entwicklung Issue/Project auf In Progress, PR auf In Review verlinken.
   Blockierungen mit `blocked`, Grund und nächster prüfbarer Entscheidung markieren.
   Automatische Job-/Upload-/Produktionsfreigaben entstehen dadurch nicht.
3. Im PR konkrete technische Nachweise einschließlich fehlgeschlagener/übersprungener
   Fälle und Datenart dokumentieren. Meilenstein-Parents nicht mit `Closes`-Keywords
   automatisch schließen. Einzelissueabschluss erst nach seiner Akzeptanzprüfung.
4. Parentabschluss manuell prüfen: vereinbarte Pflichtkinder, fachliche Kriterien,
   offene Risiken und ausdrücklich erforderliche Operatorfreigaben. Optionales
   C24-Semantikpaket darf nach dokumentierter Zurückstellung im Backlog bleiben;
   seine Nichtabnahme wird weder als Erfolg ausgegeben noch blockiert sie den
   vereinbarten Volltextkern. Produktionsstatus separat festhalten. C26 verlangt
   den ausdrücklichen Go-live-Entscheid für Version, Host und Datenumfang.
5. Nach Meilensteinabschluss Roadmap und Einstiegsseiten aktualisieren, PR-/Issue-
   Belege und noch offene Gates verlinken. Gemergt, getestet, evaluiert und
   produktiv freigegeben getrennt pflegen.
6. Vorschlag: wöchentlich kurzer Backlogreview; monatlich und bei jedem
   Meilensteinabschluss Roadmapreview. Rhythmus und verantwortliche Person noch
   bestätigen. Keine Termine oder Assignees erfinden.

## Weitere Entscheidungen – vor abhängiger Arbeit offen

| ID | Entscheidung / empfohlene Richtung | Benötigt vor |
| --- | --- | --- |
| D01 | Schritt-B-Freigabe der 32 Issueentwürfe, Kategorien, Repositories und Reihenfolge | jeder Issue-/Project-/Milestoneverwaltung |
| D02 | Bestehendes gemeinsames Project, Owner, Zugriffsweg/Scope und einmalige Feld-/Ansichtenkonfiguration prüfen; keine Installation/Tokenausweitung ohne Freigabe | Projectverwaltung |
| D03 | Reichen Parents plus Target-milestone-Feld? Empfehlung ja; native Repo-Milestoneobjekte nur bei begründetem Zusatzbedarf nach Inventar | zusätzliche GitHub-Milestones |
| D04 | C23-Persistenz-ADR: bestehende Modelle wiederverwenden, PostgreSQL gegen Alternativen prüfen; Jobqueue nicht ersetzen | C23-02 |
| D05 | TXT-Unknown-Time-Vertrag und Verbraucherkompatibilität; keine künstlichen Zeiten | C23-05 |
| D06 | Historische Originalpfadbindung: konkrete byteidentische Übernahme in neuen Workspace oder andere explizit geprüfte Strategie aus PR #72; Originale erhalten | C23-03 / realer Pilot |
| D07 | Berechtigter Realmaterialkorpus, fehlende Bundles und unabhängige Parsing-/Formel-Goldreferenzen, Reviewer und Releaseumfang | C23-06 / C24-05 / C26 |
| D08 | Volltexttechnik und semantischer Pilotumfang; Qdrant wiederverwenden, optionaler Teil kann separat blockiert bleiben | C24-02/C24-04 |
| D09 | Geprüftes UI-Authlib/Dependencies, Images/SDKs/Modellrevisionen; eventuelle Downloads separat erlauben | Runtimeprüfungen, kein Download in C23.0 |
| D10 | Konkreter Hetzner-Host, Kostenfreigabe, Ingress/IdP, individuelle Rollen/Secrets, Zielstorage und Retention | C26; kein Serverauftrag durch diesen Plan |
| D11 | Alarmziel, Betriebsowner, Restore-/Incident-/Rollbackverantwortung und manueller Go-live | C26-05/C26-07 |
| D12 | Historische PRs #6/#10/#11 als ersetzt und #9 nach Restfix ggf. schließen – nur nach eigener Reviewentscheidung | Bereinigung, nicht Schritt-A-Automatik |
| D13 | Verantwortliche/Reviewrhythmus und Priorisierung C27–C32; keine behauptete Ressourcen-/Terminplanung | laufende Pflege / spätere Backlogverfeinerung |

C23.0 setzt keine dieser noch offenen Technik-, Daten-, Kosten- oder
Produktionsentscheidungen stillschweigend voraus. C22s gemergte Betriebsarchitektur
wird weiterverwendet; es wird kein konkurrierender Release-/Kontrollpfad geplant.
