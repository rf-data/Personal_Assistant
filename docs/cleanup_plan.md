# Bereinigungsplan, Referenzprüfung und Freigabeliste

Stand: 16.10.2026. [Inventar](repository_inventory.md),
[Dokumentenaudit](documentation_audit.md), [Nachweise](audit/validation.md).
Keine Pythondatei, Datenablage, Konfiguration, Branch oder Worktree wurde gelöscht.
Keine Historyoperation ist Teil der Umsetzung. Eine Inventur ersetzt kein Backup
persistenter Daten; vorhandene Git-Blobs sichern nur versionierte Inhalte.

## A — Sichere Änderungen, umgesetzt

- Hauptarbeitskopie auf neuen Audit-Branch vom exakt verifizierten aktuellen
  Master gebracht; keine lokalen Änderungen verdrängt. Benutzer-Roadmap bytegleich.
- README, Architektur, Entwicklung und Roadmap an vorhandene Material-/Lecture-/
  Knowledge-/Qualitäts-/Job-/UI-/Monitoring-/Persistenz-/Deploymentverträge angepasst.
- Aktuellen Dokumentationsindex ergänzt. C14/C17 als gemergt im UI-Repository,
  C16/C18 als gemergt im Backend und vier historische PRs weiterhin offen belegt.
- Fehlenden historischen Chat-Startpfad ausdrücklich als nicht lauffähig belegt;
  kein ungeprüfter Ersatzbefehl. C16-/C17- und C15-/C18-Aussagen korrigiert.
- V1-Parserberichte als historische Nachweise gekennzeichnet und auf v2 verlinkt.
- Maschineninventur mit Pfad-/Hashvergleich und privater Metadatenaggregation.
- Monitoring-Testfixture auf ausschließlich versionierte Konfiguration begrenzt;
  zwei zusätzliche Schutztests für Runtime-/Secretdateien und Symlinks. Keine
  bestehenden Assertions entfernt oder fachlichen Schutzbedingungen abgeschwächt.

## B — Dokumentenkonsolidierung nach Referenzprüfung, umgesetzt

| Maßnahme | Beleg / Inhaltserhaltung |
| --- | --- |
| Frühere vier Übersichtsdokumente unter `docs/archive/2026-10/repository-overview/` erhalten | Ursprungsbytes aus verifiziertem Master, Quell-/Ziel-SHA und nur Banner-/Link-/portable Beispielpfadanpassungen im [Archivmanifest](audit/archive_manifest.v1.json) |
| `docs/cs50_pipeline_completion_plan.md` auf vorhandenes Archiv verweisen lassen | vor Änderung exakt gleicher SHA-256 wie bestehender Archivplan; Dateipfad bleibt als Weiterleitung erhalten |
| `docs/cs50_pipeline_completion_audit.md` auf vorhandenes Archiv verweisen lassen | Archivvariante unterschied sich genau in einer bereits korrigierten alten Dokumentpfadreferenz; gleiche übrige Aussagen; kein historischer Befund verloren |
| Markdown-Dateiziele nach Archivkopien korrigieren | explizite relative Ziele gegen aktuelle Pfade geprüft; alte Befehle klar historisch markiert |

Kein Dokument wurde allein wegen identischem Basename ersetzt. Alte Worktree-
varianten bleiben unverändert; 49 frühere CS50-Pfade haben bereits im vorhandenen
Archivierungsmanifest konkrete Zielpfade. Neue breite Verzeichnisverschiebungen
würden vorhandene Referenzen ohne belegten Vorteil verändern und unterbleiben.

## B — Weitere Kandidaten, vorerst nur Empfehlung

| Kandidat | Referenz-/Nutzungsbefund | Nächster sicherer Schritt |
| --- | --- | --- |
| `docs/logger_notes.md` | langer alter TODO-/Kommentarentwurf; keine aktuelle Logger-Spezifikation | Verantwortlichkeit und manuelle Nutzung prüfen, dann gesondert als historischen Entwurf archivieren |
| `src/prio_list.md` | historische lokale Worktree-/Prioritätsnotiz, kein aktueller Betriebsvertrag | private Angaben und aktuelle Nutzung prüfen; erst danach geeignete Archivierung |
| alte `docs/cs50/operations/*report*.md` / generierte Previewtabellen | punktuelle Test-/Snapshotstände, weiterhin im CS50-Einstieg/Archivmanifest verlinkt | als historische Nachweise behalten; spätere Indexbereinigung nur mit Linknachweis |
| `_prototypes/` und unreferenzierte Beispiele | statische Suche allein schließt manuelle/dynamische Nutzung nicht aus | separater Kandidatenreview mit Owner und Import-/CLI-/Docker-/Testmatrix |

## C — Ausschließlich nach konkreter manueller Freigabe

| Kandidat / gewünschte Folgeänderung | Nachgewiesene Referenzen / Risiko | Freigabe muss festlegen |
| --- | --- | --- |
| `streamlit_app.py`, `frontend/pages/`, `src/run_st_*` entfernen/verschieben | `Makefile:streamlit`, Root-App und `st_admin_app.py` importieren bzw. referenzieren Legacyseiten; 25 Seitendateien | zu ersetzende Einstiegspunkte, Kompatibilität und Regression; bis dahin behalten |
| `frontend/admin_app/`, `frontend/chat_app/`, `st_admin_app.py`, `st_chat_app.py` entflechten | Adminseite, Chatseite und Services sind bytegleich zu drei historischen UI-Dateien; `st_chat_app.py` referenziert Chatfunktionen; `st_admin_app.py` enthält Integrationsnotizen | kanonischer UI-Ersatz, Import-/Startvertrag und separater UI-PR; keine automatische Verschiebung |
| allgemeine Parser `src/model_parsing/`, `src/tools_parsing/` entfernen | statische Referenzsuche findet 47 bzw. 15 Dateien im verifizierten Basisstand; UI-/Legacy-/Doclingpfade nutzen andere Verträge als CS50 | vollständige Aufrufermigration; gleichnamige HTML/PDF-Funktionen sind kein Duplikatbeweis |
| `_prototypes/` löschen | Referenzen etwa aus `frontend/pages/D_p1_pca.py` und `src/tools_eda/profile_dataset.py` | Ersetzungs-/Archivstrategie, dynamische/manuelle Aufrufe und Datenbezug |
| `src/run_mlflow_setup_test.py` entfernen/aus Tests isolieren | importiert MLflow und führt auf Modulebene Client-/Experiment-/Schreibzugriffe aus; ist kein sicherer Importsmoke | Owner, Betriebsverwendung und Ersatz durch reine Tests; im Audit nicht importiert |
| `api/Dockerfile` ändern/entfernen | Python 3.11, fehlende `api/requirements.txt` / `fastapi_main`, nicht C16; externe Deployreferenzen nicht ausgeschlossen | neuer expliziter API-/Executor-Build-/Startvertrag und separater Betriebsreview |
| `docker/docker-compose.ml.yaml` / Workerimage ändern | MLflow-Buildpfad nicht belegt; Worker-Sleep-Default und operative Make-Targets vorhanden | Mount-/Secret-/Servicekompatibilität und konkrete Deploymentfreigabe |
| doppelte `docling`-/`pymupdf`-Dependencies beseitigen | Duplikate im Root-Extra `lecture-worker`, dazu bestehende Locks/Profilprojektionen | Zielprofil, Lockdifferenz, keine ungefragten Upgrades, frischer Offline-/Importnachweis |
| unerwartete Datei `bjects -vH` entfernen | 3.611 Bytes versioniert; keine statische Referenz gefunden, Zweck unklar | Inhalt/Owner und Sicherung bestätigen; nicht als temporär gelöscht |
| `src/mathe_vorkurs.html` verschieben/löschen | 6.190.135 Bytes versionierte Quelle; keine statische Referenz gefunden, mögliche manuelle Nutzung | Herkunft/Lizenz, Datenstatus und Archivziel ausdrücklich bestätigen |
| alte Worktrees/Branches / offene PRs #6/#10/#11 bereinigen | vollständige Tree-/Hash-/Statusbilanz; teils lokale Änderungen, technische Historie nicht gleich fachlicher Ersatz | exakte Liste und Sicherungs-/Wiederherstellungsweg; #9 hat relevanten TXT-Rest |
| Daten, Transkripte, Knowledge, Modelle, DVC, DBs, Logs, `.env`, Benutzerkonfigurationen oder Volumes entfernen | sensible/persistente Benutzer-/Betriebsinhalte; nur Metadateninventar, teilweise keine Leserechte | separate explizite Daten-/Betriebsfreigabe; keine Aktion in diesem Auftrag |
| Git-History umschreiben / Force-Reset / `git clean -fdx` | nicht autorisiert und zur Konsolidierung unnötig | außerhalb dieses Auftrags; keine vorbereitete Ausführung |

Die Referenzzahlen sind statische Textfundstellen im geprüften Basisstand,
einschließlich Dokumentation und Kommentaren, keine behauptete Anzahl aktiver
Imports. Explizit vorhandene Aufrufer sind gesondert benannt.

Diese Tabelle ist eine konkrete Reviewliste, keine pauschale Zustimmungsfrage und
keine vorgemerkte automatische Ausführung nach Merge des Dokumentations-PRs.

## Zielzuständigkeit der Repositories

Backend: Modelle, Worker, Materialien/Lectures/Transkripte/Knowledge, Evaluation,
C16/C18 und Monitoringkonfiguration. UI: Streamlit-Admin, Knowledge-/Chatansichten,
API-Client, UI-Settings und UI-Deployment. Die Hauptarbeitskopie des UI-Repositories
ist älter als dessen gemergter Remoteinhalt; das Audit prüfte den treegleichen
C17-Worktree und veränderte das UI-Repository nicht. Ein späterer lokaler
UI-Abgleich oder Codeumbau bleibt eine gesonderte Aktion bzw. ein eigener PR.

## Veröffentlichung der Inventur

Die Detailinventur mit lokalen Worktree-/Status-/Pfad-/Hashmetadaten bleibt in
der ignorierten privaten Ablage `docs/_local_audit_c170/`. Der PR enthält eine
bereinigte Fassung mit ausschließlich verifizierten veröffentlichten Basispfaden,
Dokumentationsbelegen und aggregierten Ergebnissen. Lokale Detaildaten oder
unversionierte Benutzerinhalte werden nicht übertragen. Der erste lokale Audit-
Commit bleibt ausschließlich lokal erhalten; der Veröffentlichungsbranch beginnt
neu am aktuellen Remote-Master. Kein bestehender Commit/Branch wird umgeschrieben
oder gelöscht und keine private Commit-Ancestry wird veröffentlicht.
