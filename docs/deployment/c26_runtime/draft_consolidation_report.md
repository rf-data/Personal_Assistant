# Bericht B – Draft Consolidation (24.10.2026)

**Drei technische MERGE_CANDIDATEs: #156, #149 und UI #20, vorbehaltlich kurzem
abschließendem Review und gesondertem Merge-/Triggersicherheitsentscheid.**
#148 und #157 bleiben HOLD. In diesem Auftrag wurde kein PR gemergt, geschlossen,
auf Ready gestellt oder auf Auto-Merge gesetzt. Keine produktive Aktivierung.

## Frische GitHub-Abfrage und Einordnung

Die Tabelle nennt die am Arbeitsbeginn nochmals abgefragten vollständigen Heads;
#157 erhält anschließend den separat getesteten Observernachtrag dieses Berichts.
Dessen veröffentlichten neuen Head nennt der PR/Veröffentlichungsbeleg; der
[Validierungsbeleg](observer_consolidation_validation.v1.json) bindet die genauen
geprüften neuen Quelldateien. Ein Dokument kann seine eigene Commit-ID nicht
enthalten. Keine Änderung der vier anderen PR-Heads durch diesen Auftrag.

Alle fünf: offen, Draft, `mergeable=true`, `mergeable_state=clean`,
`auto_merge=null`, keine eingereichten Reviews, keine Check-Runs und keine
Commitstatuses. Der kombinierte Status ist `pending` mit null Einträgen, **kein
CI-Erfolg**. Hier folgt ein lokales Code-/Integrationsreview, kein unabhängiges
Vieraugenreview und keine Hosted-CI-/Produktionsabnahme.

| PR / geprüfter Head | Konflikte und getestete Abhängigkeit | Offene Defekte / Review und CI | Produktive Wirkung | Urteil und exakt nächste Maßnahme |
|---|---|---|---|---|
| [Backend #156](https://github.com/rf-data/Personal_Assistant/pull/156) `c77128b14e60b78a546fd804507ff255d4833759` | GitHub und echte lokale Simulation konfliktfrei; aktueller master `e502aa9` + #156 separat geprüft. | Drei unveränderte F821 im Master belegt; lokale Suite ist daher kein pauschal grüner Lintnachweis. Historischer SQLite-Lockhalter/Produktionsfilesystem weiter unbekannt. Unabhängiges Review/CI fehlen. | Lazy Imports und begrenztes Verbindungssetup; keine Runtimeabhängigkeit ergänzt, kein Driver nötig. Ein späterer Build übernimmt den Fix, nicht ein Merge allein. | **MERGE_CANDIDATE**. Imports/Retrydiff kurz gegenlesen, dokumentierte Altbefunde akzeptieren/zuordnen, Merge-/Triggerfreigabe einholen. Kein zusätzliches Architekturprojekt erforderlich. |
| [Backend #149](https://github.com/rf-data/Personal_Assistant/pull/149) `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb` | Konfliktfreie echte Folge master → #156 → #149; zusätzlich Gesamtstand. Keine funktionale Pflichtabhängigkeit vom Retryfix, für diese Integration aber ausdrücklich auf #156 getestet. | HTML-Lint grün. Reale Notes/PSet-Exporte inzwischen lokal geprüft; passender Gesamtplan/Receipt für eine vollständige produktive Artefaktabnahme nicht behauptet. Optionales anderes Original-Notes-Artefakt fehlt; kein neuer Download. Reviews/CI fehlen. | Handoff v2/Referenz-/Listen-/Qualitylogik; Parser und kanonische Text-/Codefenster bleiben erhalten, Legacy v1 lesbar. Kein Download/Job durch Merge. | **MERGE_CANDIDATE**. v2-Kompatibilität und aktuelle Exportnachweise reviewen; alte PR-Beschreibung „Exporte remote“ ist überholt. Danach eigene Mergefreigabe. Kein zusätzlicher Architekturauftrag nötig. |
| [Backend #148](https://github.com/rf-data/Personal_Assistant/pull/148) `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Konfliktfrei nach #156/#149; Store automatisch zusammengeführt und beide Guards erhalten. Gatefälle im Gesamtstand erneut geprüft. | Offlinekern vorbereitet; v1 bindet Gateway-/Caddyscope nicht selbst. Kein unabhängiger Koordinator, Livecollector oder echter permitpflichtiger Coolify-Driver. Reviews/CI fehlen. | Opt-in Gate greift in C16-Annahme/Dispatch ein; Legacydefault false. Dockerfile erhält Gate-CLI. Pflichtgate benötigt separat provisionierte existierende Queue und Bootstrap. | **HOLD**. Gezieltes Contractreview mit #157; v2-Approval-/Permit-/Journalstrategie entscheiden und vor Liveintegration umsetzen. Kern derzeit nicht zwischen Branches kopieren oder still erweitern. |
| [Backend #157](https://github.com/rf-data/Personal_Assistant/pull/157) `b616e29981870a7365c821106a831f5df8f90b8a` + dieser Observernachtrag | Konfliktfrei auf master → #156 → #149 → #148; unveränderte Basis plus exakt geprüfte neue Observerdateien. | Offlineobserver/Collectorvertrag vorhanden. Vertrauenswürdige Liveanbindung, v2-Gateerzwingung, Build-/Registryprovenienz, Adoptions-/Rollback-/Trigger-/Hostabnahme offen. Reviews/CI fehlen. | Deaktivierte Compose-/Controller-/Limitsvorlagen und lesende Bibliotheken; kein Runtimeimport in API/Worker, keine Aktivierung. Späterer Profil-/Buildtypwechsel ist produktiv relevant. | **HOLD**, gezielt vervollständigen. Passender bestehender Draft; kein weiterer Integrations-PR, kein künstliches Schließen/Split ohne sachlichen Gewinn. Nächste Schritte in Bericht A. |
| [UI #20](https://github.com/rf-data/personal-assistant-ui/pull/20) `6b84e3c09f877309a3fd1c6f9cbcf61bb9f46788` | Konfliktfreie echte Folge main `e4be7a2` → #20; nur `docs/c26_https.md`, +16 Zeilen. | 11 HTTPS-/OIDC- und 9 Startguardtests aktuell bestanden. Vollständiger Browser-/Container-/VPN-/IdP-/Hostnachweis nicht erneuert. Reviews/CI fehlen. | Ausschließlich Dokumentation, keine Änderung an Runtime, Lock, Dockerfile oder Compose. Laufender UI-Container bleibt durch diesen Gitvorgang unberührt; tatsächlicher externer Trigger ist separat zu sichern. | **MERGE_CANDIDATE**, unabhängig von produktiver Backendaktivierung. Kurz Dokumentationsstand und gepinnten Gateverweis prüfen; eigene Mergefreigabe, kein UI-Rollout. |

## Was konkret geprüft wurde

**#156:** `tiktoken` bleibt im optionalen Extra `lecture-worker`, nicht in der
minimalen Runtime. Session-/Settingsimports werden erst bei tatsächlicher Nutzung
optional geladener Funktionen ausgeführt. Die vorhandene frische Prozessprüfung
verweigert vorzeitige Session-/Tokenizer-/Settingsinitialisierung. Die drei
ursprünglichen Batchfälle werden ohne installiertes `tiktoken` ausgeführt.

SQLite-Retry ausschließlich für `SQLITE_BUSY` (inklusive primärem Code aus
Extendedcodes), Verbindung schließen und vor Transaktion/Body begrenzt neu
öffnen; Zwei-Sekunden-Setupbudget. Kein Retry von `BEGIN`, Body, Commit oder Jobs.
Deterministische echte Locks decken vorübergehenden/persistenten Busy, andere
Setupfehler und einmalige Bodyausführung/Rollback ab. Persistent Busy verweigert;
keine Quarantäneheilung oder Jobwiederholung. RAM-Läufe beweisen keine Heilung
historischer Btrfs-/SQLiteprobleme. Die drei F821 wurden direkt im unveränderten
master reproduziert; dessen zusätzlicher I001 in path_helper ist durch #156
bereinigt. Die F821 sind Altdefekte, keine neue Fehlermeldung verschwiegen.

**#149:** v1/v2-Handoffs und Reports, eindeutige DOM-/Source-Linkbindung,
ambige/exkludierte Referenzen, Listeneltern/-tiefe/-reihenfolge/Nummerierung,
fehlende/doppelte Referenzen und Text-/Codeverlust geprüft. Festfingerprints der
fünf eingecheckten Snapshots bleiben erhalten. Rein lesender Vergleich mit den
bereits freigegebenen lokalen Originalexporten: Notes 237 Blöcke/34 Codeblöcke,
PSet 28 Blöcke/10 Links, darunter genau fünf belegte Aufgabenverweise; sämtliche
alten/neuen Aggregationseinheiten und DOM-Codeblöcke identisch. Keine vollständigen
Child-Inhalte heruntergeladen und keine SourceApprovals erzeugt.

**UI #20:** genau eine Dokumentationsänderung. Gepinnter Link auf #148 ist
unabhängig von späterer Branchlöschung auflösbar. Vorbereitetes HTTPS/OIDC und
historische lokale Ergebnisse sind ausdrücklich von Produktionsfreigabe getrennt.
Die neue Backend-Runtime-/Observerdokumentation wird über
[Bericht A](runtime_observer_report.md), [Driververtrag](driver_contract.md) und
[Rollout](rollout.md) eingeordnet; UI #20 enthält selbst noch keinen direkten
Verweis auf den nachfolgend entstandenen #157-Observer. Das ist ein optionaler
Dokumentationsnachtrag, keine Backend-/Runtimeabhängigkeit dieses reinen Docs-PRs.
Keine frische vollständige Browserkette behauptet; kein Container gestartet.

**#148/#157:** gemeinsame Produktdatei `deployment/Dockerfile` wird regulär
zusammengeführt: sowohl `scripts/deployment_gate.py` als auch
`scripts/c26_runtime_preflight.py` werden übernommen. Store behält Gatepflicht
und SQLite-Setupretry. #149 verändert andere Materialmodule; kein konkurrierender
Parser-/Queue-/Driverersatz. Die Observerergänzung liegt ausschließlich in #157,
Gatekern #148 bleibt unverändert. Keine technisch erzwungene neue Aufteilung.

## Tatsächliche Integrationssimulation und Tests

Isolierte neue RAM-Kopien, keine produktiven oder lokalen Zielbranches verändert:

| Stufe | Tatsächlich erzeugter lokaler Mergecommit |
|---|---|
| master + #156 | `e6490b5a81f236f2af81d86d2c0630807dd97f8f` |
| + #149 | `a4d4ca6f278646adf9d983e15aa21543e9f61667` |
| + #148 | `3d95b04ee3d7bd38e727819df0b5a3dcc91115f3` |
| + #157 Ausgangshead | `449847aa7313f3a25af1dd4183f1b2416bd6620d` |
| UI main + #20 | `4e7928cacf36103728aebb99353ef6e11f9c46ea` |

Die zunächst geerbte shallow-History blockierte den letzten Merge; nach regulärem
lesendem Nachladen der fehlenden Eltern gelang er ohne Konflikt und ohne
`allow-unrelated-histories`. Die neue Observerquelle ist zusätzlich im integrierten
Stand getestet und wird nach ihrem regulären Commit nochmals regulär lokal
zusammengeführt; der Beleg nennt den resultierenden Commit. Keine angenommenen
GitHub-Mergeergebnisse und keine Changesets aus PR-Beschreibungen rekonstruiert.

- **#156 separat: 105 passed / 1 skip**, einschließlich der drei ursprünglichen
  Batchfälle ohne tiktoken und deterministischer SQLitefälle.
- **#156+#149 separat: 162 passed / 1 skip**; beide echten lokalen HTMLexporttests
  mit gesetztem `CS50_WEEK0_QUALITY_EXPORT` erfolgreich.
- **Gesamtkombination: 604 passed / 1 skip**, darunter 66 Gatefälle sowie
  Readclient-/Runtime-/C16-/C18-/Material-/Scheduleprüfungen.
- Letzte Observerhärtungen (Repository-Credentials und tatsächliche Settings je
  API-/Workerrolle): **135 finale gezielte Fälle passed, kein Skip**, darunter
  66 neue Observer- und 69 bestehende Readclientfälle. Der breite Lauf verwendet
  den separat gepinnten vorherigen Observer. Bestehender Produktcode unverändert.
  Läufe überlappen und werden nicht addiert.
- **UI: 11 HTTPS-/OIDC- plus 9 Produktionsguardtests bestanden** auf main+#20.
- Offene Skips: originales importiertes SRT-Pilotartefakt beziehungsweise ein
  anderes originales Notes-Artefakt. Keine davon betrifft die nun geprüften
  beiden Week-0-HTMLexporte.
- Neuer Observer und HTML-Diff: Ruff grün; Stabilisierung: drei nachgewiesene
  unveränderte F821. Keine pauschal grüne Gesamtlintprüfung behauptet.

Genutzte Backendumgebung: Python 3.12.12/SQLite 3.50.4, Paketliste im Beleg.
Sie entspricht **nicht vollständig** `deployment/runtime/uv.lock`: insbesondere
Pydantic/Typer/dotenv/Tenacity/PyMuPDF abweichend, pydantic-settings/returns fehlen.
Ein zusätzlicher Offlineversuch der gepinnten Umgebung scheiterte bereits am
uv-Interpretercache-Rename mit lokalem ENOSPC; keine neuen Pakete oder Images
installiert. Exakte Runtime-/Imageprüfung bleibt eine konkrete Freigabebedingung.
Lokale 32-GB-Btrfs-/RAM-Kapazität ist kein Hetznernachweis. Keine automatische
Bereinigung, keine gelöschten Worktrees/Venvs/Gitobjekte oder versteckten roten Tests.

## Integrationsreihenfolge und nächster Freigabeschritt

1. **#156** nach kurzem Code-/Testreview und eigener Mergefreigabe integrieren.
2. **#149** auf diesem Stand reviewen/integrieren; Exportlücke der alten
   PR-Beschreibung ist jetzt für den gezielten Vergleich geschlossen.
3. **UI #20** separat integrieren; keine Voraussetzung für aktiven Backendbetrieb
   und keine Freigabe für ein neues UI-Image. Kann parallel zu 1/2 erfolgen.
4. **#148 → #157** offen halten und Gate-/Collector-/Driververtrag koordiniert
   vervollständigen. Nach erneuter Prüfung kann später gesondert über technische
   Integration deaktivierter Funktionen entschieden werden. Produktivfreigabe
   bleibt davon unabhängig.

Damit können nach den drei ausdrücklich freizugebenden manuellen Integrationen
fünf aktive Drafts auf zwei reduziert werden. **Aktuell sind weiterhin fünf offen.**
Kein PR wird ohne vollständige Übernahme als überholt geschlossen, kein Branch
oder Worktree gelöscht.

Vor jedem späteren Merge gesondert freizugeben: abschließendes Reviewergebnis,
bewusst akzeptierte fehlende Hosted-CI/abweichende Runtime-Testumgebung und
verbleibende Altbefunde; außerdem tatsächlich begrenzter Merge-/Deploytriggerpfad.
Manual deployments only und Previewanzeige None sind `operator_observed`; API-
Akteure, weitere Webhooks, Registry/Scheduler, ausstehende Deployments und exklusive
Koordination bleiben offen. Ein Merge gilt nicht als Erlaubnis, diese Endpunkte
aufzurufen oder zu deployen. Keine echten API-/Webhooktests in diesem Auftrag.

**A. Kurz reviewbar und technisch mergeempfohlen:** #156, #149, UI #20 unter den
obigen konkreten Bedingungen. Kein zusätzliches Architekturprojekt erforderlich.

**B. Offen bleiben:** #148 und #157 wegen fehlender wirksamer Mehrrollen-
Approval-/Permitbindung und vertrauenswürdiger Livebelege/Koordination; kein
produktiver Driver. Offlineerfolge ersetzen diese Voraussetzungen nicht.

**C. Nächster technischer Schritt auf Variante A:** den unabhängigen Collector-
Transport samt read-only Feld-/Ressourcenrechten festlegen und reale, redigierte
Image-/Build-/Mount-/Trigger-/Writerbelege gewinnen. Die jetzige Observer-
Implementierung dagegen prüfen, anschließend v2-Gateerzwingung und den einzelnen
permitpflichtigen Coolify-Driver umsetzen. Erst nach eigenen Betreiberfreigaben
folgen Backup/Adoption, geschlossener Kaltbootstrap, HTTPS/VPN/OIDC-Abnahme und ein
kleiner source-approved Pilot. Keine neue Transportarchitektur oder Queue nötig.

Aufbewahrung: eigene isolierte Arbeitskopien/Simulationscommits und gesicherte
Quell-/Testergebnisse bleiben wegen Merge-/Löschverbots erhalten. Integration der
Berichte in den tatsächlichen Defaultbranch steht bis zum regulären Merge aus.
