# C26-B6: Multi-Week und Multi-Course, Phase A

Stand: 22.10.2026. Entwurf auf `master` / `e581e201ef6b3d6c06aca14de845e0687d213b37`.
**Implementierungs- und Produktionsstatus: ausstehend.** Dieser Review enthält
Bestandsaufnahme, Architektur, Pilotmatrix und Testplan. Er implementiert weder
einen Preflight noch eine Mehrwochen-CLI und verändert keine B5-Modelle.

## Verifizierte Voraussetzung und Phasengrenze

| Grundlage | Tatsächlicher Stand | Bedeutung für B6 |
|---|---|---|
| [B5, PR #150](https://github.com/rf-data/Personal_Assistant/pull/150) | Offen, kein Draft, nicht gemergt; `c6415d3c3f0f77f457b4b461f6841a385e827d5c` | Wochenmodelle liegen außerhalb von Master; keine konkurrierende Modellimplementierung |
| [HTML-Aggregation, PR #149](https://github.com/rf-data/Personal_Assistant/pull/149) | Offen, Draft; `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb` | Neue Link-/Listenprojektion und Quality v2 sind noch keine integrierte Voraussetzung |
| [Deployment-Gate, PR #148](https://github.com/rf-data/Personal_Assistant/pull/148) | Offen, Draft; `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Offline-Kern, noch kein produktiv abgenommener Coolify-Treiber |
| [Issue #146](https://github.com/rf-data/Personal_Assistant/issues/146) | Offene Deployment-Abhängigkeit | Größere produktive Verarbeitung bleibt ohne nachgewiesenen Wechsel-/Annahmeschutz gesperrt |

Live-Master und B5-Branch wurden über GitHub geprüft. Die neun B5-Dateien und die
Dateilisten der beiden anderen PRs überlappen nicht; daraus folgt keine semantische
Kompatibilität nach zukünftigen Änderungen. B5 enthält einen dokumentierten
Kompatibilitätslauf auf dem exakten #149-Head. Dieser wurde jetzt nicht wiederholt.
Der GitHub-Testmerge einer offenen PR ist keine Integration in Master.

Das B5-Bundle wurde verifiziert und ausschließlich in die lokale Git-Objektdatenbank
eingelesen. Alle 1.044 Dateien des gesicherten Quellarchivs stimmen mit dessen
Commit-Baum überein. Die fünf dokumentierten Quellfingerprints passen ebenfalls.
Zwei neue lesende Offline-Prüfungen bestätigen 17 Ressourcen/24 Varianten aus
Fixtures und 21/28 mit den gelieferten Exporten. Alle sechs Exporthashes passen.
Weitere Prüfergebnisse und Grenzen stehen im [Validierungsbericht](multi_course_validation.md).

Historische Branches namens B5/B6/B7 enthalten andere frühere Arbeitspakete. Deren
Existenz ersetzt die Integration von PR #150 nicht. Fremde Änderungen und die
zwei Konflikte im alten Integrationsworktree bleiben erhalten. B6 benutzt eine
eigene Arbeitskopie und einen eigenen Dokumentationsbranch.

Phase B beginnt mit einer erneuten Prüfung der tatsächlich integrierten B5-Dateien,
Modelle, Dokumente und Tests. Vor diesem Schritt werden hier keine parallel
inkompatiblen Verträge eingeführt. Auch nach B5-Integration bleibt jede konkrete
Ausführung an ihren eigenen aktuellen Preflight gebunden.

## Bestehende Verträge und Festcodierungen

Pfade beziehen sich auf die Master-Basis, sofern ausdrücklich als B5 markiert.

| Bereich / Modul | Vorhandener Vertrag | Gezielter Erweiterungsbedarf |
|---|---|---|
| `src/model_discovery/cs50.py` | Geschlossener `CourseId` für sechs CS50-Kurse; `CourseDiscovery` mit Harvard/CS50; Sections, Ressourcen, Parents, Provenienz | Kursprofile und Adapter registrieren; MIT erfordert ein eigenes Schema-/ACL-Review, nicht nur eine neue URL |
| `src/model_course.py`, `src/job_control/models.py` | ContentCourseId und C16-Kursrechte bauen auf dem geschlossenen Katalog auf | Neue Kurs-ID in Discovery, Content, Principal, Katalog und Workflow konsistent zulassen; keine Umwandlung aller Felder in beliebige Strings |
| `src/tools_lecture/prepare_cs50.py:discover_fixture_courses` | Hash-/manifestgebundene Index- und Week-Overview-Snapshots; keine allgemeine rekursive Erfassung | Bestehenden Adapter versionieren; zusätzliche genehmigte Aufgabenübersichten explizit einbinden |
| `src/tools_materials/processing.py:make_plan` | Material-/Lecture-Bindung aus demselben Discoverygraphen | Derselbe Graph muss im Planer, Bundle und Worker reproduziert werden |
| B5 `src/model_materials/week.py` | `WeekRequest`/`WeekReport` Schema 1, Literal `cs50_python`, numerische Woche, höchstens acht ausgewählte Materialien | Nach Integration kompatible Versionierung für mehrere Sections/Kurse; v1 weiterhin lesen |
| B5 `src/tools_materials/week.py` | `plan_week`, HTML/PDF-/Transcript-Batchvorbereitung, CS50P-PSet-Pfad und Week-0-Aufgabenliste | Quellenmuster und erwartete Aufgaben in abgenommene Profile verlagern; kein Week-0-Sonderzweig im allgemeinen Planer |
| `src/tools_materials/transcripts.py` | Nur CS50P, Section `0`, genau eine Lecture, bekannte SRT/TXT-Rollen, maximal zwei Inputs; Lecture-Nummer `0` | Gebundene Lecture/Section aus dem Profil und Discoverygraphen übernehmen; Importer und Zeitsemantik erhalten |
| `src/tools_materials/batch.py` | `Batch`, `SourceApproval`, `Approvals`, `plan`, `approval`, `seal`; konkrete Material-/Source-/Kurs-/URL-/Schrittbindung | Wiederverwendbare Richtlinie darf nur konkrete bestehende Einzelgrants ableiten; Ablauf/Widerruf fehlen als maschinenprüfbare Felder |
| `src/workflows/{models,definition,service}.py` | Versionierte C18-Bundles, höchstens drei Definition-Sources, bestehender C16-Controller | Kleine bestehende Workflows verwenden, keine Kurs-Sammelausführung und keine zweite Queue |
| `src/tools_materials/{quality,mapping,media_evidence}.py` | Bestehende Hash-/Receipt-/Parser-/Handoff-Prüfung | Mit integrierter Aggregationsrevision nachprüfen; Parsererfolg genügt nicht als fachlicher Abschluss |
| `src/tools_materials/capacity.py`, `src/job_control/registry.py` | Dateibudgets, Reserve, Guardian; Workflow 90 s/60 CPU-s/768 MiB, bestehende Queue | B5 strengere Grenzen erhalten: mindestens 5 GiB Reserve, acht Materialien, 1 MiB/Quelle, 8 MiB Raw gesamt, Parser 512 MiB, ein paralleler Auftrag und eine belegbare Queueposition |

Die fünf B5-Aufgaben-IDs sind belegt, aber noch nicht im bisherigen C18-Bundle
rekonstruierbar. `assignment_child_c18_adapter_not_integrated` darf durch B6 nicht
verschwinden, bevor eine versionierte, opt-in Discovery-/Bundle-Erweiterung den
genehmigten Übersichtssnapshot mit Hash trägt und im Worker dieselben Child-IDs
ableitet. Alte v1-Bundles und Resource-IDs bleiben unverändert. Vier zusätzliche
Aufgabeninhalte liegen nicht lokal vor; deren Links sind keine Downloadfreigabe.

## Zielarchitektur und Konfiguration

Der allgemeine Planer verarbeitet eine explizite Liste von Kurs-/Section-Scope und
Materialtypen. Die Liste kann über mehrere begrenzte Pläne beliebig viele Wochen
abdecken. Ein einzelner Request, Report, Batch und Job bleibt größenbegrenzt.
Konkrete Grenzen werden vor Phase B mit B5 und dem bestehenden Controller fixiert;
ein großer Scope wird sichtbar abgelehnt oder explizit paginiert, niemals gekürzt.

```mermaid
flowchart LR
  P[Kursprofil und gehashte Snapshots] --> D[Registrierter Discoveryadapter]
  D --> W[Bestehende Wochenplanung]
  W --> C[Kursplan mit Ressourcenbeziehungen]
  C --> F[Obligatorischer Batch-Preflight]
  F --> B[Kleine bestehende Materialbatches]
  B --> Q[Vorhandener C16 und C18]
  Q --> R[Verifizierte Artefakte und Kursreport]
  R --> F
```

Nach Integration die vorhandenen B5-Module erweitern, keinen parallelen Planer
mit eigenen Material-, Job- oder Quality-Modellen einführen. Vorgeschlagene neue
Hüllen sind ein `CourseProfile`, ein begrenzter `CourseProcessingRequest`, ein
`CourseProcessingReport` mit bestehenden Wochenreports und ein `PreflightReport`.
Diese Namen sind Entwurf, keine importierbaren Klassen. Requests und Reports
tragen Schema-, Profil-, Adapter-, Parser-, Plan- und Quelldigests. Reihenfolge
folgt den expliziten Section-Ordnungen, nicht aus URL oder Kursnamen geratenen Zahlen.

Beispiel eines **noch nicht ausführbaren** Profils:

```yaml
profile_version: 1
course_id: cs50_python
discovery_adapter: cs50_navigation_v1
weeks: [1, 2, 3]
processing:
  mode: plan
  material_types: [html, pdf, transcript]
acquisition:
  code_index: manual_only
  source_approval_required: true
```

Ein gültiges Profil braucht darüber hinaus geprüfte Snapshotbindungen, Struktur-
und Rollenmerkmale, erwartete Pflichtressourcen, explizite zugelassene Origins,
Versionen und zugehörige Referenzabnahme. Das Beispiel allein erteilt keine Rechte.
Strukturell unbekannte Sections werden blockiert; fehlende Sollinformationen
bleiben als unbestimmte Discovery-Vollständigkeit sichtbar.

### Adapterklassen und Identität

1. Bekannte CS50-Struktur: vorhandene Parser mit registriertem Profil, gehashten
   Snapshots und geprüften Strukturmerkmalen wiederverwenden.
2. Ähnliche Harvard-Struktur: Abweichungen explizit konfigurieren und mit eigenen
   Fixtures abnehmen. Gleiche Domain reicht nicht; unerwartete Navigation oder
   Pflichtrollen führen zur Adapterprüfung.
3. MIT OCW: eigenständige Adapterklasse und vorerst synthetische Fixtures. Noch
   keine unterstützte Course-ID, Controller-/Contentfreigabe oder Quelle behaupten.

Adapter geben vorhandene ResourceCandidate-/Section-/Provenienz-Verträge zurück,
soweit deren Kurskatalog dies erlaubt. Eine spätere Katalogmigration muss gleiche
bestehende ID-Tupel und URL-Darstellung erhalten. Kurs, Rolle, URL, Sprache und
Parent bestimmen weiterhin die Resource-ID. Gleiche URL mit anderer Rolle, anderem
Parent oder Kurs wird nicht pauschal verschmolzen. Gleiche Material-ID über mehrere
Wochen erzeugt eine gemeinsame Ausführungsreferenz mit allen Wochenzuordnungen;
abweichende Bindungen oder Hashes sind ein Konflikt. Medienvarianten bleiben
getrennt. Original-URLs, DOM-Locators und Quellenhashes bleiben im Report erhalten.

### Unveränderliche Code-Policy

Die B5-Policy wird vor der generischen Parserauswahl und erneut unmittelbar vor
Batchübergabe geprüft. Codeindex, PY, ZIP/Archive und rekursive Codepfade bleiben
`manual_only`/`explicit_import_only`, auch bei `all`, `complete`, irreführendem
HTML-Format, Notes-Rolle oder vollständigen Grants. Es gibt kein rekursives Folgen,
keine automatische Codeausführung und keinen Fallback auf generisches HTML.
Code-PDF wird als PDF separat behandelt. Ein späterer manueller Import benutzt
den bereits getrennten Importworkflow und eine gesonderte konkrete Freigabe.

## Wiederverwendbare Quellenfreigaben

SourceApproval v1 enthält konkrete Identität, Belegreferenzen und Download-/Process-
Flags, aber keine prüfbare Ablaufzeit oder aktuelle Widerrufsentscheidung.
Eine textuelle `revocation_reference` beweist keinen aktuellen Nichtwiderruf.
B6 darf dieses Modell daher nicht als bereits ausreichend für Serienfreigaben
ausgeben oder durch eine Domain-Whitelist ersetzen.

Vorgesehen ist eine versionierte Richtlinienhülle über bestehenden Grants mit
Policy-ID/Revision, Zweck, exaktem Kurs-/Section-Scope, Origins, erlaubten Rollen
und Formaten, Schritten, Gültigkeitszeitraum und verifizierbarem Widerrufsstand.
Lizenz-/Nutzungs-/Zugriffsbedingungen tragen einen geprüften Bezug und Digest.
Neue Domain, Redirect-Origin, Materialtyp, Zweck oder abweichende Bedingungen
erfordern ein eigenes Review. Keine Freigabe beliebiger zukünftiger Downloads.

Für jeden geplanten Batch werden daraus ausschließlich konkrete SourceApproval-
Einträge für die beobachteten Ressourcen abgeleitet. Zu protokollieren sind
Policy-ID/Revision/Hash, Auswertungszeit, geprüfter Widerrufsstand, resultierender
Grant-Digest und Materialbindung. Rohdateihashes müssen bei lokalem Processing
konkret vorliegen. Bereits vorhandene v1-Einzelgrants bleiben lesbar und erhalten
keine still erfundenen Gültigkeitsangaben. Ohne den neuen überprüfbaren Kontext
ist eine wiederverwendbare Serienfreigabe blockiert.

Die Prüfung erfolgt vor jeder tatsächlichen Beschaffung bzw. Submission erneut.
Ein früher gültiger Report ist kein Execution-Token. Bei Widerruf bleiben alte
Artefakte unverändert; weitere Verarbeitung wird blockiert und Aufbewahrung/Zugriff
folgen der expliziten Betreiberentscheidung.

## Entwurf des obligatorischen Batch-Preflights

Jeder Check liefert `pass`, `fail`, `unknown` oder begründet `not_applicable`,
Pflichtkennzeichen, Belegreferenz/Hash, Zeit, zulässiges Alter und betroffenen Scope.
Kein boolesches Operatorfeld allein ersetzt eine aktuelle Betriebsbeobachtung.
Der Report bindet Plan, Quellen, Profile, Adapter, Parser, Schema, Grants und
Betriebsrevision. Änderungen invalidieren die Freigabe; Queue-/Kapazitätszustand
wird vor jedem Dispatch innerhalb der vorhandenen Koordination erneut geprüft.

| Prüffamilie | Pflichtbedingungen / Beleg |
|---|---|
| Scope und Quellen | Registrierter Kurs/ACL, gültige Ressourcen-/Lecture-/Parentbindung, expliziter Scope, Pflichtressourcen und Strukturmerkmale, zulässige Original- und Redirect-Origins |
| Rechte und Policy | Konkreter SourceApproval, Zweck, Schritt, Lizenz-/Zugriffsprüfung, Ablauf, frischer Widerrufsstand; Codepolicy vor Routing |
| Rohdaten | Expliziter sicherer Pfad, keine Symlink-Flucht, Byte-/Summenlimit, erwarteter SHA und Receipt; Beschaffung nur über gesondert freigegebenen bestehenden Pfad |
| Verarbeitung | Registrierter Prozessor, exakte Parser-/Adapter-/Schema-/Konfigurationsversion, C18-Rekonstruierbarkeit, erforderliche Test-/Referenzabnahme |
| Reuse und Qualität | Bestehende Evidence-/Receipt-/Plan-/Handoff-Prüfung, Ausgabedateihashes, Code/Textabdeckung, Link-/Listenstruktur, keine stale oder unvollständige Publikation |
| Kapazität und Ablage | Tatsächliches Dateisystem der persistenten Raw-/Catalog-/Job-/Report-/Scratchroots; Reserve plus zusätzliche Ausdehnung; CPU/RAM/Wallclock gemäß Registry, Parserbudget separat |
| Worker und Queue | Richtiger vorhandener Worker, aktuelle Heartbeat-/Lock-/Guardianbelege, freie Queueposition und serialisierte Annahme; fehlende Queue nie als leer behandeln |
| Deployment | Nachgewiesener Wechsel-/Annahmeschutz, zugehörige Revision/Instanz; keine Annahme, dass #146 oder ein offener Gate-PR bereits produktiv ist |

Entscheidungsreihenfolge:

- `blocked`: mindestens ein fehlgeschlagener, unbekannter, veralteter oder nicht
  belegbarer Pflichtcheck. Gilt auch für fehlende Freigaben, fehlenden Scope und
  fehlende Produktions-/Deploymentbelege. Keine Warnung schwächt dies ab.
- `operator_action_required`: ausschließlich für einen lesenden Plan, dessen
  anwendbare Pflichtprüfungen bestanden sind, aber gesonderte manuelle Referenz-
  oder Importarbeit ausgewiesen ist. Dies ist ausdrücklich kein Processing-Ready.
  Ein Ausführungsrequest mit fehlender Pflichtentscheidung bleibt `blocked`.
- `ready_with_warnings`: alle Pflichtchecks bestanden; ausschließlich nicht
  blockierende Hinweise zu explizit ausgeschlossenen optionalen Referenzen.
- `ready`: alle anwendbaren Pflichtchecks bestanden, keine offenen Hinweise.

Ein Offline-Report bezeichnet seine Umgebung ausdrücklich als `offline`; nicht
anwendbare Produktionsprüfungen machen niemals eine Produktionsfreigabe daraus.
Für produktive Requests sind Betriebs-/Deploymentprüfungen immer Pflicht.
Die aktuelle Bestandsaufnahme ergibt **keinen ausführungsfähigen B6-Preflight**.

## Pilotentscheidungsmatrix

| Kategorie | Nachgewiesene Veränderung | Erforderliche Abnahme zusätzlich zum stets obligatorischen Preflight |
|---|---|---|
| 1 | Weitere Section desselben Profils; Adapter-, Struktur-, Material-, Parser- und Schemaverträge unverändert | Bestandene Referenz-/Regressionstests und gültige Rechte; kein neuer vollständiger Infrastrukturpilot |
| 2 | Neuer Kurs, nachweislich kompatibles Quellenformat, neuer explizit zugelassener Kurs-/ACL-Scope | Begrenzte inhaltliche Stichprobe und Profil-/Adapterabnahme |
| 3 | Neuer Adapter, unbekannte Struktur oder neuer Materialtyp | Gezielter Offline-Pilot mit repräsentativen Fixtures und negativen Strukturfällen |
| 4 | Geänderter Parser, Handoff oder persistiertes Schema | Gezielte Migration-/Regressionstests, begrenzter Verarbeitungspilot bei veränderter Semantik |
| 5 | Neue Infrastruktur, Queue-/Workerarchitektur oder Deploymentverhalten | Vollständiger betrieblicher Preflight und gesonderte Infrastrukturabnahme |

Die Entscheidung vergleicht dokumentierte Digests/Merkmale mit einer abgenommenen
Referenz, nicht Kursnamen oder Domain. Mehrere Änderungen kumulieren erforderliche
Prüfungen. Unbekannte Merkmale blockieren die Einstufung. Eine neue Kurs-ID allein
beweist keine neue Infrastruktur; unveränderter Kursname beweist keine Kompatibilität.
Offline-Pilotfreigabe und spätere Produktionsfreigabe werden getrennt erfasst.

## Mehrwochenplanung, Fortsetzung und Reporting

Der Kursplan enthält pro Woche den bestehenden Wochenreport und einen begrenzten
Graph aus Abhängigkeiten und Materialreferenzen. Übergreifende Pflichtfehler halten
den betroffenen Batch an. Ein lokaler Materialfehler kann unabhängige, vollständig
geprüfte Materialien bestehen lassen; strukturelle Adapterfehler, Integritätsfehler,
Widerruf oder ausgeschöpfte Gesamtkapazität stoppen alle davon abhängigen Wochen.
Die gewählte Stop-/Fortsetzungspolitik steht ausdrücklich im Plan.

Die Ausführung delegiert kleine HTML/PDF-Batches an die vorhandenen
`batch.plan`/`seal`- und C18-/C16-Schnittstellen. SRT/TXT verbleiben im bestehenden,
zunächst zu generalisierenden Transcript-Adapter; Medien benötigen weiterhin ihren
eigenen Zweck-/Evidenceplan. Ein Plan erzeugt keine neue Workerinstanz. Eine
zusätzliche Queue, Jobdatenbank, ungebremste Medienparallelität oder ein gesamter
Kurs in einem Job sind ausgeschlossen.

Fortsetzung benutzt bestehende Controller-/Workflowzustände und explizit benannte
Receipts. Derselbe Material-/Raw-/Parser-/Config-/Approval-/Schema-Digest mit
verifizierter Quality darf ohne neue Submission referenziert werden. Ein laufender
Job wird nur referenziert; ein geänderter Digest ist stale und benötigt einen neuen
geprüften Plan. Unvollständige oder unterbrochene Publikationen werden nicht
automatisch repariert oder als fertig übernommen. Gleichzeitige Wiederholung
muss unter den vorhandenen Locks ohne doppelte Submission enden.

Kursreports zeigen pro Kurs und Woche entdeckte Ressourcen, Materialvarianten,
unterstützte Prozessoren, vorhandene und hashverifizierte Rawdateien, verifizierte
Processingergebnisse, Reuse, manuelle Ausschlüsse, Blocker, Quality, Pilotstatus und
offene Betreiberentscheidungen. Wochensummen und globale Unique-Zähler werden
getrennt geführt; eine geteilte Ressource darf nicht zweimal als verarbeitet zählen.
Zähler werden aus den referenzierten Zeilen abgeleitet, nicht frei hochgezählt.

Snapshots/URL/Parents, Originalhashes, Ergebnis-/Receipt-Digests, konkrete genutzte
Grants, Versionen und Änderungen bleiben nachvollziehbar. Discovery-Vollständigkeit
bezieht sich auf den belegten Snapshot-Scope; technische Vollständigkeit auf den
nichtleeren expliziten Processing-Scope; fachliche Vollständigkeit benötigt eine
gesonderte Inhaltsprüfung. Fehlende Pflichtressourcen, verlorene Codeblöcke,
ungültige Links/Listen, gebrochene Provenienz oder Strukturdrift dürfen keine
vollständige Woche erzeugen.

## CLI, Migration und nächster Integrationsschritt

Vorhandene Einstiegspunkte bleiben `scripts.cs50_batch` und nach Integration
`scripts.cs50_week`. Eine spätere Erweiterung um Kursplan-/Preflight-/Process-
Unterbefehle ruft dieselben Python-Funktionen auf; Streamlit verwendet dieselbe
API. Die im Auftrag genannten `personal-assistant courses ...` sind weiterhin
konzeptionell, keine existierenden Befehle. Process verlangt einen aktuellen
gebundenen Preflight und explizite Bestätigung; keine UI-eigene Downloadlogik.

1. B5 reviewen und tatsächlich integrierte Verträge verifizieren. Nach Änderungen
   die B5-Regressions- und #149-Kompatibilitätsbelege erneut erheben.
2. In einem gesonderten kompatiblen Review Discovery-/C18-Aufgabenbindung,
   Transcript-Generalisation und versionierte Policy-/Widerrufshülle abnehmen.
   Bestehende v1-Reader, Receipts, IDs und alte Week-0-Artefakte erhalten.
3. Auf dieser Basis Kursprofile, begrenzte Kursplanung, Preflight und Reporting
   in den vorhandenen Modulen implementieren; Testmatrix im Validierungsbericht
   abarbeiten. Keine neue Dependency vorgesehen.
4. Für einen ersten CS50P-Mehrwochenpilot explizite lokale Snapshots der gewählten
   Wochen, Referenz-/Strukturabnahme, konkrete Scope-/Quellenfreigaben und aktuelle
   Worker-/Queue-/Ablage-/Kapazitätsbelege bereitstellen. Kein neuer Download ist
   durch diesen Entwurf freigegeben.
5. Für Multi-Course zusätzlich Kurskatalog/ACL/Profil und Bedingungen prüfen;
   MIT erst nach eigenständigem Adapter-/Schema-Review. Für produktive Serienläufe
   vorher #146 samt realem Deploymenttreiber und Annahmeschutz abnehmen.

Kein Auto-Merge oder Deployment. Eigener Branch und Worktree bleiben wegen des
offenen Reviews erhalten. Dokumente im Reviewbranch sind noch nicht in Master
integriert; B6 ist damit vorbereitet, aber als Gesamtimplementierung ausstehend.
