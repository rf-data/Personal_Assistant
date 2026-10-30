# C27-C: begrenzte hierarchische Zusammenfassung

## Architekturentscheidung vor Implementierung

Der einfache Modus bleibt der Default. Keine automatische Ausweichstrategie bei
Budgetfehlern. Der vorhandene SourceCollector, SummaryService, Provider, Validator,
RegisteredStorage und die Exporter bleiben die gemeinsame Pipeline.

Trade-off: Ein zweistufiger Lauf verursacht mehrere Requests und kann beim
Komprimieren Inhalte verlieren. Deshalb partitioniert er nur an bestehenden
Quellblock-/Artefakt-/Lecture-/Seiten-/Abschnittsgrenzen, validiert jede Teilantwort,
behält Original-IDs und legt ausgelassene Belege offen. Die Konsolidierung erhält
zusätzlich zu Zwischenständen exakte, gegen die Originale geprüfte Ausschnitte.
Sie wird erneut gegen Original-Evidence validiert. Keine Synthese allein aus
komprimierten Behauptungen, keine automatische Verifizierung unsicherer Formeln.

Die technischen Grenzen bleiben: drei Lektionen, 160 Evidenceblöcke, 26.000 Bytes
Quelltext, 2 MiB je Eingangsdatei, 30.000 konservative Inputeinheiten und höchstens
2.000 Ausgabetokens pro Request, insgesamt höchstens 64.000 reservierte
Input-/Outputeinheiten. Zusätzliche explizite Strategiegrenzen beschränken Teilzahl,
Teilantwortgröße, Input je Stufe, Requests und Kosten. Alles wird vor dem ersten
Request geplant; unbekannte Reduce-Größe reserviert eine feste Obergrenze.

Bestehendes zeitbasiertes Knowledge-Chunking verlangt bekannte Zeitstempel und
verwendet Überlappungen. Es wird hier nicht aufgerufen: vorhandene ContentLocator-
Blöcke unterstützen auch unbekannte Zeiten, Dokumentseiten und abgeleitetes Wissen.
Knowledge-Consolidation bleibt ein anderer Ergebnisvertrag. Ihre Prinzipien
(versionierte Fingerprints, explizite Konflikte, Write-ahead-Receipts) werden mit
den bestehenden C27-Storageprimitiven umgesetzt; kein zweiter Knowledge-Workflow.

Zwischenergebnisse und Reservierungen werden exklusiv in einer ausdrücklich
registrierten lokalen Cache-Root gespeichert. Eine Reservierung ohne validiertes
Ergebnis ist ein unklarer/fehlgeschlagener Versuch und wird beim Resume nicht
automatisch wiederholt. Bereits validierte Abschnitte sind wiederverwendbar.
Abgebrochene Läufe erhalten einen Bericht, aber keine exportierbare Teilsynthese.

## Umsetzung und Wiederverwendung

`SummaryService(..., hierarchy=HierarchyPolicy())` aktiviert die Strategie; die
lokale Konfiguration verwendet `strategy: "hierarchical"`. Ohne diese Einstellung
bleibt die vorhandene einfache Verarbeitung einschließlich ihres Cache-Schlüssels
und Ein-Request-Providers erhalten. Es gibt keinen automatischen Fallback.

- `hierarchy.py` plant und orchestriert begrenzte Abschnitte im vorhandenen Service.
  Reihenfolge: Lecture-ID, Artefakt-ID, natürlicher JSON-Pointer (2 vor 10).
  Grenzen zwischen Lectures, Artefakten, Seiten und benannten Kapiteln bleiben
  erhalten; einzelne Evidenceblöcke werden niemals abgeschnitten. Große einzelne
  Blöcke, zu viele Abschnitte oder übergroße Sammlungen scheitern ausdrücklich.
- Bestehende `Claim`, `Formula`, `Draft`, `ContentLocator`, Quellversionen und das
  Quality Gate bleiben maßgeblich. Neu sind die kleinen versionierten Verträge
  `SectionDraft`, `HierarchyPolicy` und `HierarchyReport`.
- Original-IDs werden ausschließlich für die Providerprojektion bijektiv auf
  kurze Q-IDs abgebildet. Jede Antwort darf nur die tatsächlich an diese Stufe
  übergebenen Aliase verwenden. Vor Validierung, Cache und Ergebnis werden die
  originalen Evidence-IDs wiederhergestellt. Eine Zwischenzusammenfassung wird
  niemals zu einer erfundenen neuen Originalquelle.
- Jeder Zwischenclaim braucht einen geprüften exakten Originalausschnitt. Die
  Konsolidierung erhält Zwischenstände **und** diese Originalausschnitte, nicht
  nur komprimierte Aussagen. Jeder zitierte finale Claim braucht wiederum einen
  Ausschnitt aus diesem tatsächlich übergebenen Belegbestand. Abschließend wird
  gegen die unveränderte vollständige Original-Evidence validiert und die Quelle
  erneut gelesen/gehasht.
- Der bestehende HTTP-Client, RequestBudget und Response-Decoder werden geteilt.
  Jede einzelne Hierarchiestufe hat weiterhin ein neues Ein-Request-Budget ohne
  Retry. Die zusätzliche Orchestrierung reserviert vorher den gesamten Lauf bis
  maximal 64.000 Einheiten. Der bestehende globale RequestBudget-Vertrag wird
  nicht verändert. Kein zweiter LLM-Client oder Summarization-Framework.
- Streamlit bleibt dieselbe authentifizierte Operator-Ansicht. Sie zeigt vorab
  Modus, Abschnitts-/Aufrufzahl und Budget sowie nach Abbruch den unvollständigen
  Stand. Ergebnis/Downloads enthalten Quellenabdeckung und Formelhinweise.
  Moduswahl erfolgt ausdrücklich über die Konfigurationsdatei, nicht automatisch
  beim Wechsel auf eine längere Lektion. Auth-/Job-Grenzen bleiben unverändert.

## Ursache und unveränderte Sicherheitsgrenzen

Die vorbereiteten Fälle überschreiten nicht den reinen Quelltextgrenzwert.
Insbesondere lange Hash-IDs, wiederholte Warnungen, JSON-/Schema-/Prompt- und
Chat-Framing-Overhead treiben den vollständigen Request über die Grenze.

| Fall | Blöcke | Quelltext UTF-8 | Quellenprojektion JSON im einfachen Modus | Draft-Schema JSON | Vollständiger einfacher Request inkl. Reserve |
|---|---:|---:|---:|---:|---:|
| 01.01.2 | 25 | 1.813 Bytes | 6.513 Bytes | 4.097 Bytes | 15.396 |
| 01.06.1 | 90 | 4.086 Bytes | 21.006 Bytes | 4.097 Bytes | 30.929 |
| 01.05.1 + 01.05.2 | 145 | 9.110 Bytes | 36.370 Bytes | 4.097 Bytes | 47.186 |

Alle Requestzahlen sind konservative UTF-8-Einheiten mit der vorhandenen
2.048-Reserve, **keine gemessenen Tokenzahlen**. Das doppelte JSON-Encoding der
User-Nachricht erzeugt weiteren Overhead; die Spalten sind nicht einfach addierbar.
Die Modell-ID `gpt-6-luna` wurde dabei nur als inerte Zeichenfolge im Payload
verwendet. Es wurde kein Client für diese Messung erzeugt oder Tarif abgefragt.

| Grenze | Einordnung / Behandlung |
|---|---|
| 1–3 Lectures, 160 Original-Evidenceblöcke, 26.000 Bytes Quelltext | Bestehende technische Eingangs-/Speichergrenzen unverändert; Hierarchie umgeht sie nicht |
| 2 MiB je Eingangsdatei; registrierte Roots, kein Traversal/Links/Nested Mount | Unveränderte Storage-Sicherheitsverträge, kein neuer Resolver |
| Input maximal 30.000 / Output maximal 2.000 je Request | Bestehende harte Providerobergrenzen unverändert |
| Frischer Hierarchielauf insgesamt maximal 64.000 Input-/Outputeinheiten | Neue Aggregation innerhalb des bestehenden Sicherheitsrahmens, vor dem ersten Request reserviert |
| Teilinput 24.000, Reduce-Reserve 18.000, Teiloutput 800 | Explizite konfigurierbare Strategie-/Budgetwerte; niemals oberhalb der harten Providergrenzen |
| Maximal vier Abschnitte / fünf Aufrufe als Default | Konfigurierbar bis höchstens sechs Abschnitte / sieben Aufrufe; zusätzlich greift immer die Gesamtschranke |
| Zwischenantwort maximal 2.000 Bytes, Belegausschnitt maximal 480 Bytes | Zusätzliche technische Ergebnisgrenzen; Überschreitung führt zum Abbruch, nicht zur Kürzung |
| Inhaltliche Gewichtung, Detailgrad, repräsentative Belege | Qualitätsentscheidungen, keine Vollständigkeitsgarantie; Kompakt/Ausführlich nutzen dieselbe Pipeline |

Die Reduce-Größe ist vor den Teilantworten unbekannt. Deshalb wird die volle
konfigurierte Reduce-Reserve vorab gebucht. Nach jedem validierten Zwischenstand
wird der tatsächliche finale Request gebaut: passt er nicht, endet der Lauf
unvollständig vor der Konsolidierung. Bereits angefallene Teilkosten sind dann
möglich; es gibt keine stillschweigende Verdichtung, Erhöhung oder Wiederholung.

## Mathematik, Abdeckung und Konflikte

`Formula` behält LaTeX, Variablennotation, Voraussetzungen und die vorhandenen
Zustände `verified_from_source`, `uncertain`, `requires_visual_context`, `unsupported`.
Leere Notation/Voraussetzungen sowie fehlende Originalbelege passieren das Gate
nicht. Bei gewarnten Transcript-/Knowledge-Quellen verlangt die Hierarchie für
Formeln Visualprüfung oder `unsupported`. Eine finale Formel kann nicht allein
durch Konsolidierung sicher werden: neue/unsichere/visuell ungeklärte bzw.
unbelegte Zwischenformeln werden nicht zu verifizierten Formeln aufgewertet.
Zusätzlich gelten die bisherigen Literal-/Originalrollen-/Warnungsprüfungen.
`verified_from_source` bedeutet weiterhin keine mathematische Verifikation.

Alle Zwischenformeln bleiben im strukturierten Bericht und MD/TeX sichtbar,
auch wenn das finale Modell sie nicht übernimmt. Unterschiedliche rechte Seiten
derselben normalisierten linken Gleichungsseite erzeugen einen **möglichen**
Widerspruchs-/Notationshinweis. Dieser einfache konservative Hinweis entscheidet
weder algebraische Gleichheit noch Gültigkeitsbedingungen; Fehlalarme und nicht
erkannte fachliche Widersprüche bleiben möglich. Der Reduce-Prompt fordert das
gemeinsame Prüfen von Definitionen, Variablen, Bedingungen und Abhängigkeiten.
Es gibt keine automatische symbolische Beweis- oder Notationsangleichung.

Der Bericht trennt verarbeitete Originalblöcke, in Zwischenständen zitierte
Belege, finale Zitate sowie unzitierte Blöcke und nicht im Endergebnis repräsentierte
Abschnitte. `complete` heißt, dass die technischen Stufen abgeschlossen sind;
es beweist keine vollständige inhaltliche Abdeckung. Explizite missing-Lecture-
Angaben bleiben über das bestehende Gate und dessen Warnungen sichtbar.
Rein didaktische unbelegte Hinweise müssen `unsupported` bleiben. Aussagen,
die einen passenden Quellenstring zitieren, können trotzdem fachlich falsch oder
unvollständig paraphrasiert sein: technische Checks ersetzen keine Abnahme.

## Cache und Wiederaufnahme

Alle Dateien werden in einem vorhandenen ausdrücklich registrierten schreibbaren
Cacheverzeichnis exklusiv mit 0600 erstellt; der neue lokale Workspace ist 0700.
Keine DB, Migration, automatische Löschung oder Überschreibung.

| Präfix | Inhalt |
|---|---|
| `hp-` | Versionierter Gesamtplan, Policy, Modell und bijektive ID-Abbildung |
| `ha-` | Write-ahead-Reservierung je Plan/Stufe; exklusive Erstellung verhindert doppelte Dispatches bei Konkurrenz |
| `hs-` | Validiertes Abschnittsergebnis in Envelope mit Schema, Identität, Modell, Promptversion |
| `hr-` | Validierter finaler Draft in demselben expliziten Metadatenvertrag |
| `hreport-` | Unveränderliche vollständige/unvollständige Statussnapshots |

Schlüssel berücksichtigen Original-Evidence/Versionen, Optionen, Modell,
Prompt-/Schemavertrag und Ausgabegrenzen. Physische Hostpfade sind keine Identität.
Jeder Cache-Hit wird erneut gegen aktuelle Originalbelege und Metadaten geprüft.
Beschädigte oder falsch zugeordnete Einträge werden nicht automatisch repariert.
Gültige Abschnitte können auch in einem neuen passenden Gruppenkontext dienen.

Abbruch zwischen validierten Stufen ist wiederaufnehmbar. Bei Timeout, ungültiger
Antwort oder Crash nach Reservierung ohne validiertes Ergebnis ist der Versuch
unklar: derselbe Plan wiederholt ihn nicht. Eine Prüfung/ausdrückliche neue
Laufentscheidung ist erforderlich; kein automatischer kostenpflichtiger Retry.
Bereits angefallene Reservierungen zählen beim Resume weiter. Bericht und Export
unterscheiden historische Reservierungen, neue Aufrufe und Cache-Stufen.
Unvollständige Ausführung erzeugt keinen exportierbaren Summary-Teilerfolg.
Bestehende HTTP-Grenzen bleiben: 20 Sekunden pro HTTP-Phase, höchstens 100.000
Responsebytes, `finish_reason=stop`, kein Redirect/Retry; kein zugesicherter
Gesamt-Wallclock-Timeout eines langsam streamenden externen Anbieters.

## Tatsächliche Offline-Demonstration und Kostenvergleich

Alle drei Fälle wurden mit vorhandenen Loviscach-Transkripten aus dem bereits
explizit registrierten `c27-local-mvp` ausgeführt. Kein zusätzliches Material.
Der finale Bericht liegt lokal unter
`/home/OPERATOR/0_Portfolio_Projekte/c27c-local-demo-final-20261024/comparison.json`.
Je Fall liegen dort einfache und hierarchische MD-/TeX-/JSON-Exporte in getrennten
Unterverzeichnissen. Konfiguration/Cache:
`/home/OPERATOR/0_Portfolio_Projekte/c27c-local-mvp-20261024`.
Frühere eigene Probeläufe bleiben erhalten, werden aber nicht als finale Abnahme benutzt.

| Fall | Einfacher Request / 30.000 | Hierarchischer frischer Gesamtplan / 64.000 | Aufrufe | Alle Originalblöcke verarbeitet / finale Zitate | Ergebnis |
|---|---:|---:|---:|---:|---|
| 01.01.2 Text | 15.396 / passt | 32.005 | 2 | 25 / 2 | `needs_review` |
| 01.06.1 Skalarprodukt | 30.929 / blockiert | 42.988 | 2 | 90 / 2 | `needs_review` |
| 01.05.1 + 01.05.2 Vektoren | 47.186 / blockiert | 62.279 | 3 | 145 / 4 | `needs_review` |

Hierarchiespalte enthält alle Input- **und** Outputreservierungen, inklusive voller
unbekannter Reduce-Reserve; der einfache Wert nur den Input eines Requests.
Es ist daher kein Gleichkostenvergleich. Tatsächliche Mock-Modellzeichenfolge
`mock-extractive-v1` verursacht 8 weitere Einheiten je Map-Request gegenüber dem
inerten Modelllabel: die real ausgeführten Pläne reservierten 32.013 / 42.996 /
62.295. Tatsächliche Mock-Requestobergrenzen: Text 11.213 + 9.177;
Skalarprodukt 22.196 + 9.126; Gruppe 17.376 + 23.319 + 10.150.
Alle vier registrierten Original-SHA stimmen vor/nach dem Demo-Lauf überein.

**Wichtig:** Einfaches Mock kann auch ohne passenden Live-Request ein lokales
Ausschnittsergebnis erzeugen. Das wird nicht als erfolgreicher einfacher LLM-Lauf
ausgegeben. Beide Modi wurden offline exportiert, damit Unterschiede sichtbar sind.
Mock verwendet höchstens zwei kurze Ausschnitte je Abschnitt, konstruiert keine
Mathematik und erzeugt in diesen realen Demos keine Formelobjekte. 23 / 88 / 141
Originalblöcke sind ausdrücklich nicht im Endergebnis zitiert. Der Unterschied ist
eine technisch verarbeitbare Pipeline, kein bereits nachgewiesener didaktischer Gewinn.

Tatsächliche API-Kosten: **0**, keine Live-Aufrufe. Für spätere externe Nutzung
verlangt die Hierarchie positive explizite Preisannahmen und einen Kostenhöchstwert:
`input_microusd_per_million`, `output_microusd_per_million`, `max_cost_microusd`.
Ein Mikro-USD entspricht 0,000001 USD. Reservierte Kosten werden vorab aufgerundet
als `(Inputreserve × Inputpreis + Outputreserve × Outputpreis) / 1.000.000`
in Mikro-USD berechnet. Preise werden nicht automatisch beschafft oder behauptet.

**Nur fiktives Rechenbeispiel, keine aktuellen Anbieterpreise:** Bei 1 USD je
Million Inputtokens und 4 USD je Million Outputtokens ergeben die konservativen
Label-Pläne höchstens 0,040405 / 0,051388 / 0,073079 USD je frischem Lauf.
Tokenisierung, Modell-/Preistarif und tatsächliche Usage sind nicht live geprüft.
Cache-Hits verursachen keine neuen Dispatches; eine gültige Wiederholung aller
drei Fälle wird im automatisierten Test ohne weitere Provideraufrufe geprüft.

## Reproduzierbarer lokaler Start

Vorhandene geeignete Python-3.12-Umgebung nutzen, keine Installation erforderlich.
Hier geprüft: Backend-Test-Python
`Personal_Assistant-c26b6-planning-results/test-env/bin/python`.

```bash
cd /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27c
export PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1
python -B -m scripts.lecture_summary_hierarchy prepare \
  --config /home/OPERATOR/0_Portfolio_Projekte/c27-local-mvp/summary.json \
  --output /absolute/path/new-c27c-workspace
python -B -m scripts.lecture_summary_hierarchy demo \
  --config /absolute/path/new-c27c-workspace/summary.json \
  --output /absolute/path/new-demo-exports --model-label gpt-6-luna
```

Ausgabeverzeichnisse müssen neu sein, Eltern bereits existieren. `prepare` prüft
alle drei Auswahlen und Pläne vor dem Anlegen des Workspaces, kopiert ausschließlich
Katalogmetadaten und schreibt neue Mock-Konfigurationen. `summary.simple.json`
aktiviert ausdrücklich den bisherigen Modus, `summary.json` die Hierarchie.
Weitere Auswahlen können mit der bestehenden `scripts.lecture_summary generate`
CLI und der gewünschten Konfiguration generiert/exportiert werden.

```bash
cd /home/OPERATOR/0_Portfolio_Projekte/personal-assistant-ui-c27c
python -B scripts/lecture_summary_local.py \
  --backend /home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27c \
  --config /home/OPERATOR/0_Portfolio_Projekte/c27c-local-mvp-20261024/summary.json
```

URL `http://127.0.0.1:8501`, bestehende lokale Demo-Anmeldung mit Operatorrolle;
explizites OIDC bleibt erhalten. Mock- und Hierarchiehinweise prüfen, Kurs und
Lecture(s) wählen, Plan prüfen, generieren und MD/TeX herunterladen. Stopp Ctrl-C.
`--check` wurde erfolgreich ausgeführt, UI-Verhalten zusätzlich per AppTest.
Kein weiterer Server, öffentliches API oder Produktionsjob. Keine erneute manuelle
Browserabnahme und keine fachliche Betreiberabnahme als erledigt ausgegeben.

## Tests und Grenzen der Lieferung

Die tatsächlichen Testläufe werden im
[C27-Prüfbericht](c27_validation.md#c27-c-hierarchische-verarbeitung) protokolliert.
Neue gezielte Fälle prüfen Planung, keine stille Kürzung, Originalbelege,
Aliasgrenzen, widersprüchliche/unsichere Formeln, unveränderte Sources, Kosten-/
Requestschranken, fehlende Quellen, Teilfehler, Cache-Metadaten und Invalidierung,
konkurrierende Reservierung, unterbrochene/wiederaufgenommene Läufe und CLI-Demo.
HTTP-Tests verwenden ausschließlich `httpx.MockTransport`, sonst ist Netzwerk gesperrt.

Noch offen: fachliche Abnahme, Live-Modellqualität, angemessene Gewichtung langer
Herleitungen/Definitionen, visuelle Formelprüfung und vollständige Konflikterkennung.
Die Strategie beseitigt keine ASR-/OCR-Fehler oder fehlenden Visualkontext. Material
oberhalb der bisherigen 160-/26.000-/2-MiB-Grenzen bleibt blockiert und benötigt
später eine eigene überprüfte Erweiterung; keine heutige Grenzaufweichung.
PDF-Kompilation und produktive C16-/C26-Integration wurden nicht durchgeführt.
Backend #158 und UI #21 bleiben Drafts, keine Merges/Deployments/Datenmigrationen.
Eigene C27-C-Branches/Worktrees bleiben zum Review erhalten; Dokumentation liegt
bis zum gesonderten Merge im Draft und wird nicht als in master/main integriert behauptet.
