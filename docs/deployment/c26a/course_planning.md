# C26-B6 Phase B: Kursprofile, Mehrwochenplanung und Preflight

23.10.2026. Implementierungsbasis: `da9b77db0815f0c2ab65a3e819df17200e3a3897`.
Diese Erweiterung plant und prüft **offline**. Sie lädt keine Kursinhalte herunter,
submitiert keine Jobs und besitzt keinen Execute-Befehl. Ein Offline-Ergebnis
erteilt keine produktive Freigabe.

## Verifizierte Grundlage

B5 [#150](https://github.com/rf-data/Personal_Assistant/pull/150) wurde als
`a1d5caa9141b73f6378357f1743af21b64ba76d2` integriert, Phase A
[#151](https://github.com/rf-data/Personal_Assistant/pull/151) als `da9b77d`.
Die integrierten B5-Module, Inventare und Phase-A-Dokumente wurden gelesen.
Die Primärcheckouts und historischen Worktrees bleiben erhalten. Dieser Auftrag
arbeitet auf `feat/c26b6-course-planning` in einer eigenen Arbeitskopie.

Die weiterhin offenen Drafts sind unabhängig:

- HTML-Aggregation [#149](https://github.com/rf-data/Personal_Assistant/pull/149),
  Head `58aec7da3c2e3c1e9ab2bd1e1761ef8569811edb`;
- Deployment-Gate [#148](https://github.com/rf-data/Personal_Assistant/pull/148),
  Head `f98eedd671c8a9d9eb58a3b957eda1a91713844d`.

Master verwendet weiterhin Handoff v1. Die neue Planung fordert standardmäßig
mindestens v1 und prüft die tatsächlich vorhandene Version. v2 wird ausschließlich
in der isolierten #149-Kompatibilitätsprüfung vorausgesetzt. Es wird kein Teil
dieses PRs kopiert oder als in Master integriert ausgegeben. Produktionsschutz
nach [#146](https://github.com/rf-data/Personal_Assistant/issues/146) bleibt offen.

## Module und versionierte Verträge

| Modul | Inhalt |
|---|---|
| `src/model_materials/week.py` | Bestehende WeekRequest/WeekReport v1 bleiben lesbar; additive CourseProfile/SectionProfile v1 sowie ProfiledWeekRequest/ProfiledWeekReport v2 |
| `src/tools_materials/profiles.py` | `load_profile`, `validate_profile`, Adapterrevision und begrenzte Snapshotprüfung für den bestehenden CS50-Adapter |
| `src/tools_materials/week.py` | Bestehender B5-Planer verarbeitet zusätzlich v2; konfigurierbare Section-/PSet-Bindung und Sollrollen, unveränderte Identitätsberechnung |
| `src/model_materials/course.py` | CourseRequest/Report, ApprovalPolicy, ReferenceAcceptance und PreflightReport jeweils Schema 1; konkrete SourceReview und QueueObservation |
| `src/tools_materials/course.py` | `plan_course`, `preflight_course`, `plan_courses`, konkrete Policy-Grant-Vorbereitung, Pilotentscheidung und konsistente Unique-Zähler |
| `src/tools_materials/transcripts.py` | Vorhandener SRT/TXT-Import für eindeutig gebundene Sections des bestehenden geschlossenen CS50-Katalogs; weiterhin höchstens zwei Quellen eines Kurs-/Section-Scopes |
| `scripts/cs50_course.py`, `scripts/cs50_week.py` | Lesende Kurs-CLI; bestehende Wochen-CLI liest weiterhin v1 und ausdrücklich versioniertes v2 |

Discovery-, Material-, SourceApproval-, Receipt-, C16- und C18-Schemas werden nicht
ersetzt. Es gibt keine neue Queue, Datenbank oder Workerarchitektur. Projekt-
Dependencies und Lockdatei bleiben unverändert.

## Profile und Scope

`load_profile(manifest, course_id)` verwendet den vorhandenen Discoveryadapter und
den geschlossenen Kurskatalog: CS50x, CS50P, SQL, AI, Web und Cybersecurity.
Sections werden aus ausdrücklich vorhandenen Week-Overview-Snapshots übernommen,
einschließlich nichtnumerischer Schlüssel. Profile pinnen Manifest-SHA, deklarierte
Snapshot-SHAs und den tatsächlichen Adaptercode. Vor der bestehenden Manifestprüfung
wird die deklarierte Closure auf höchstens 120 Dateien, 1 MiB je Datei und 8 MiB
insgesamt begrenzt. Fehlende oder geänderte Hashes blockieren.

Gleiche Domain bedeutet keine Adapterkompatibilität. MIT OCW und abweichende
Harvard-Strukturen bleiben nicht aktivierte Adapterkandidaten; freie Kurs-IDs
werden von Discovery-/Content-/ACL-Verträgen nicht angenommen. Ein neuer Kurs mit
bekanntem Adapter braucht weiterhin eine eigene konkrete Profil-/Kursabnahme.

Die allgemeine Kursplanung kennt keine Week-0-Sonderfunktion. Der bekannte
CS50P-Week-0-Aufgabensatz steht als Referenz im Profiladapter. Die alten v1-Pfade
bleiben für die bestehende API erhalten. V2 übernimmt Übersicht und Aufgabenroots
aus dem geprüften Profil; Ursprungs-URLs, Parents, DOM-Provenienz und IDs bleiben
nach dem vorhandenen ResourceCandidate-Vertrag erhalten.

Ein Kursrequest enthält höchstens acht explizite Wochen. Jede Woche verwendet
weiterhin B5 mit höchstens acht ausgewählten Materialien, 1 MiB je Quelle und
8 MiB Rawbudget. Größere Scopes werden sichtbar blockiert, nicht gekürzt. Eine
kursweite Planung macht daraus keinen unbegrenzten C18-Job. `plan_courses`
akzeptiert höchstens sechs unterschiedliche unterstützte Kurse als getrennte Pläne.

## API und CLI

```python
from pathlib import Path
from src.model_materials.course import CourseRequest
from src.tools_materials.profiles import load_profile
from src.tools_materials.course import plan_course

manifest = Path("docs/course_sources/cs50/manifest.json").resolve()
profile = load_profile(manifest, "cs50_python")
request = CourseRequest(
    manifest=manifest, course_id="cs50_python", profile=profile,
    weeks=("0", "1", "2"), mode="plan",
    material_types=("html", "pdf", "transcript"),
)
report = plan_course(request)
```

Ohne konkrete Inputs, Grants und Referenzabnahme enthält dies eine Inventur und
einen **blockierten** Preflight. Ein automatisch erstelltes Profil ist keine
Abnahme. `week_inputs` nimmt explizite ProfiledWeekRequests mit lokalen Quellen,
Evidence und Workflowreferenzen auf. Kurs, Manifest, Profil und Source-Origin
müssen zum Kursrequest passen; einzelne Materialfehler bleiben in ihrer Woche.
Ein Fehler der gemeinsamen Manifest-/Snapshotintegrität blockiert die gemeinsame
Discoverygrundlage aller davon abhängigen Wochen.

```sh
python -m scripts.cs50_course plan --course cs50_python --weeks 0 1 2
python -m scripts.cs50_course preflight --course cs50_python --weeks 0 1 2
python -m scripts.cs50_course report --course cs50_python --weeks 0 1 2
python -m scripts.cs50_course preflight --request /explicit/private/request.json
```

Optional: `--manifest`, `--profile`, `--approvals`, `--material-types`,
`--selection types|all|complete`, `--mode` und `--environment offline|production`.
`--request` darf nicht mit Request-Bauoptionen gemischt werden. Request-/Profil-
und Approval-JSON werden begrenzt und mit den vorhandenen strikten JSON-Lesern
geprüft. Die CLI schreibt ausschließlich JSON auf stdout, keine Artefaktdateien.
`report` berechnet aktuelle Beobachtungen erneut; ein gespeicherter Bericht wird
nicht als Ausführungstoken angenommen.

Exit-Codes: 0 für einen gültigen Plan/Bericht bzw. erfolgreichen Offline-Preflight,
2 für einen ungültigen Request/Dateizugriff, 3 für blockierten Preflight oder
fehlgeschlagene Wochenplanung, 4 für erforderliche manuelle Importarbeit. Ein
gültiger Plan kann mit Code 0 einzelne Materialblocker ausweisen; die ausdrückliche
Preflight-Aktion entscheidet darüber mit Code 3. `execute` existiert nicht.

## Konkrete Approvals und wiederverwendbare Richtlinien

ApprovalPolicy v1 bündelt gemeinsame Belegreferenzen und Zweck, zulässige Origins,
Bedingungsdigest, Gültigkeitsintervall sowie datierten Widerrufsstand. Sie enthält
**konkrete SourceReviews**, keine Freigabe künftiger Ressourcen. Jeder Review pinnt
Material-ID, Resource-ID, URL, Kurs über die Policy, Sections, Rolle, Format und
den geprüften Bedingungsdigest. Download und Processing sind standardmäßig false.

`policy_grant` bereitet einen vorhandenen SourceApproval-Vertrag nur mit diesen
ausdrücklich geprüften Flags und Bindungen vor. `revoked` ist ein Pflichtfeld und wird nicht implizit
als false angenommen. Eine weitere Woche oder Quelle
erhält ohne eigenen passenden Review keine Rechte. Neue Domain, Rolle, Format,
Bedingungen, Ablauf, Widerruf und veralteter/zukünftiger Status blockieren. Für
lokales Processing müssen Raw-SHA im Review/Grant und LocalSource übereinstimmen.

Eine vorhandene individuelle SourceApproval kann über `SourceReview.grant_sha256`
unverändert attestiert werden. Dessen gesamter Digest und die expliziten Flags
müssen passen; Belegreferenzen werden nicht überschrieben. Ohne passenden aktuellen
Policykontext wird der Grant im Kursadapter nicht verwendet, auch nicht für Reuse.
Die alte B5-Einzelquellen-API bleibt davon unberührt.

Zeitprüfung erfolgt reproduzierbar gegen das ausdrücklich angegebene
`CourseRequest.evaluated_at` (UTC-Epochsekunden). Der datierte Widerrufsstand darf
höchstens seine konfigurierte Gültigkeit von maximal einer Stunde alt sein.
Diese Offline-Angaben sind Betreiberbelege, keine von Codex live recherchierte
Lizenz- oder Widerrufsauskunft. Sie dürfen später nicht ohne frische Laufzeitprüfung
zur Ausführung benutzt werden. Genutzte Grants und Policy-/Grant-Digests stehen
pro Ressource und Woche im Bericht.

## Preflight und Pilotmatrix

Jeder Check enthält Code, Scope, Pflichtkennzeichen, Status, Grund und gegebenenfalls
Belegdigest. Der Report bindet Plan-, Request-, Approval-, Profil-, Adapter- und
Processingvertragsrevisionen. `ReferenceAcceptance` bezeichnet eine explizite
abgenommene Referenz mit Profilformat, Adapter, Verträgen, Materialtypen und
Infrastrukturrevision. Eine fehlende oder nicht passende Referenz verlangt Review.

Pflichtprüfungen umfassen Identität, Snapshotbindung, Sollressourcen, konkrete
Grants und Widerruf, lokale Rohdaten/Hashes, C18-Reproduzierbarkeit, Parser,
Handoff/Quality und unveränderte vorhandene Evidence. Budgets werden zusätzlich
gegen die tatsächliche C16-Registry geprüft: 90 s, 60 CPU-s, 768 MiB Guardian,
separat 512 MiB Parser; keine automatische Limiterhöhung.

Deklarierte Speicher-/RAMangaben und optionale QueueObservation sind ausdrücklich
Planungsbeobachtungen. Bekannter Platzmangel, volle Queue, widersprüchliche
Workeranzahl oder veraltete Beobachtung blockieren. Eine fehlende Queuebeobachtung
ist offline ein Hinweis und keine behauptete leere Queue. Zulässig bleiben nur
ein vorhandener Worker und die bestehende eine Queueposition.

Entscheidungspriorität:

1. `blocked` bei fehlgeschlagenem oder unbekanntem Pflichtcheck;
2. `operator_action_required` für einen ausschließlich manuellen Referenzscope
   nach bestandenen anwendbaren Pflichtprüfungen;
3. `ready_with_warnings` bei bestandenen Offline-Pflichtprüfungen und offenen
   nicht verpflichtenden Betriebsbeobachtungen/Referenzen;
4. `ready` nur ohne solche Hinweise.

Live-Worker/Heartbeat/Queue, persistente Mounts und Deployment-Gate bleiben ohne
integrierten Live-Adapter `unknown`. Im Produktionsmodus sind sie Pflicht und
blockieren immer. `production_decision` bleibt `blocked`, `execution_supported`
bleibt false; ein gesetztes Workerflag kann dies nicht ändern.

Die Pilotentscheidung folgt den dokumentierten Merkmalen: gleiche Referenz und
bekannte Woche Kategorie 1; neuer Kurs Kategorie 2; neuer Adapter/Profilstruktur/
Materialtyp Kategorie 3; geänderte Parser-/Schema-/Handoffverträge Kategorie 4;
Infrastrukturabweichung Kategorie 5. Mehrere Änderungen behalten alle erforderlichen
Aktionen bei und melden die höchste Kategorie. Nach einer gezielten Abnahme wird
die neue Referenz ausdrücklich festgehalten; der Kursname allein reduziert nichts.

## Wiederverwendung, Reporting und verbleibende Blocker

Der Kursreport enthält bestehende Wochenreports und globale Unique-Zähler.
Gleiche Material-ID über mehrere Wochen wird einmal gezählt und in
`shared_materials` mehrfach zugeordnet. Verschiedene Ressourcen mit identischer
URL bleiben getrennt. Widersprüchliche Bindungen oder Raw-SHAs bei gleicher ID
blockieren. `blocked` zählt beobachtete Blocker, `blocked_in_scope` nur ausgewählte;
`unselected` und manuelle `excluded` bleiben separat sichtbar.

Reuse verwendet vorhandene B5-/Receipt-/Quality-Verifikation. Bei gültiger Evidence
entstehen ausschließlich `verify_existing_result`/`reuse_without_processing`.
Beschädigte oder unvollständige Artefakte, geänderte Hashes, Parserkonfigurationen
oder widerrufene Grants werden nicht übernommen. Wiederholte Planung verändert
keinen bestehenden Output. Fortsetzung braucht erneut passende Inputs und Belege;
sie erzeugt keine zweite Submission. Vorhandene Workflowreferenzen bleiben im
Wochenreport erhalten.

Die Transcript-Erweiterung erhält SRT-Zeiten und TXT-Nullzeiten. Die Modellstruktur
des TranscriptReceipt bleibt v1, aber die vorhandene codegebundene Importerrevision
ändert sich durch die Adapteränderung. Alte Transcriptreceipts mit anderer
Revision bleiben stale; keine stille Migration, Reparatur oder Überschreibung.
Für deren zukünftige Adoption ist eine gesonderte kompatible Revisionsprüfung nötig.

**Offener C18-Blocker:** Die fünf Aufgaben sind anhand des echten lokalen Exports
mit denselben B5-IDs geprüft. Sie können weiterhin nicht innerhalb unveränderter
v1-C18-Bundles aus der separaten PSet-Übersicht rekonstruiert werden und bleiben
`assignment_child_c18_adapter_not_integrated`. Hier wird keine zweite Graph- oder
Workerarchitektur eingeführt. Erforderlich bleibt ein versioniertes opt-in Bundle,
das den explizit genehmigten Übersichtssnapshot mit Hash trägt und im Worker die
identischen IDs ableitet. Vier zusätzliche Aufgabeninhalte bleiben fehlend.

Codeindex, PY, ZIP und rekursive Codepfade bleiben selbst bei `all`, `complete`,
Grants, HTML-/MIME-Hinweisen oder Wiederholung manuell. Ein Code-PDF bleibt PDF.
Medien benötigen weiterhin ihre gesonderte Pipeline; der Kursadapter verarbeitet
sie nicht. Bekannte Codeverzeichnisse werden vor generischem HTML geroutet.

Discovery-Vollständigkeit und fachliche Inhaltsvollständigkeit bleiben false.
Technische Vollständigkeit gilt ausschließlich für einen nichtleeren expliziten
Scope mit verifizierten Ergebnissen aller betroffenen Wochen. Plan-/Parsererfolg
ist keine Freigabe der gesamten Woche.

Erster späterer Produktivpilot: kleiner expliziter Scope, lokale Snapshots/Quellen,
konkrete aktuelle Freigaben, abgenommene Referenz, ausreichende reale Reserve auf
allen persistenten Roots sowie Live-Worker-/Queue-/Gateprüfung. MIT und andere
Quellenstrukturen benötigen vorher ihren eigenen Adapter-/Katalog-/ACL-Review.
Kein SSH, Download, Produktionsjob, Merge oder Deployment gehört zu diesem Auftrag.

Prüfergebnisse, Umgebungsbefunde und Aufbewahrung:
[Validierung](course_planning_validation.md).
