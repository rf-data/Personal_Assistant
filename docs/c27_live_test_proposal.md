# C27 – Vorschlag für einen einzelnen kontrollierten Live-Test

**Nur vorbereitet, nicht ausgeführt.** Der aktuelle Katalog und die Startanleitung
bleiben im Mock-Modus. Dieser Vorschlag erteilt keine jetzige Kosten-/Uploadfreigabe.
Keine API-Abfrage zur Kontoverfügbarkeit und keine private Quelle wurden übertragen.

## Auswahl und Modell

Nur Abnahmefall A: `loviscach / mathe_1 / 01.01.2`, die vorhandene Fortsetzung
„Drei Arten Mathematik“, 25 Segmente. Kompakt, Standardfokus. Ziele: sinnvolle
Zusammenfassung des Modellierungsbegriffs, valide Provenienz und Exporte. Keine
mathematische Leistungsbewertung aus diesem Fließtextfall ableiten.

**Konkreter erster Test: `gpt-6-luna`, einfacher Modus, genau ein Request,
höchstens 2.000 Ausgabetokens, vorgeschlagenes Laufbudget 0,01 USD.** Keine
Hierarchie, keine zweite Lektion und kein automatischer Zweitversuch. Dies ist
eine vorbereitete Auswahl, keine erteilte Upload-/Kostenfreigabe.

Ein kostenbewusster **Kandidat** ist `gpt-6-luna`. Die offizielle Modellseite
nennt Chat Completions und Structured Outputs sowie regulär 0,10 USD/1 Mio.
Inputtoken und 0,50 USD/1 Mio. Outputtoken. Vor dem späteren Test Modellstatus,
Kontozugriff, aktuelle Parameterkompatibilität und Preise nochmals prüfen;
der Alias ist kein unveränderlicher Snapshot. Der bestehende Adapter nutzt
JSON-Objektmodus und keine Tools. Keine Modellumstellung oder Providererweiterung
ist für diese Vorbereitung erfolgt. [OpenAI Docs: GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
Die Modell- und [Preisseite](https://developers.openai.com/api/docs/pricing)
wurden am 24.10.2026 erneut geöffnet. Der Kandidat aus dem bisherigen Vorschlag
bleibt bestehen. Kontoberechtigung und eine erfolgreiche Antwort sind ungeprüft;
keine Models-API oder andere API wurde dafür abgefragt.

Der Adapter konfiguriert aktuell keine modellabhängige Reasoning-Stufe. Bei einem
Reasoning-Modell kann das kleine Ausgabevolumen bereits für interne Tokens
aufgebraucht werden. Eine abgeschnittene/fehlende JSON-Ausgabe ist ein erwartbarer
negativer Testausgang, kein Anlass für eine automatische Fortsetzung oder ein
größeres Budget. Die Modellseite ist eine Kompatibilitätsgrundlage, kein bereits
erbrachter Nachweis einer erfolgreichen C27-Liveantwort.

## Private Konfiguration erst nach gesonderter Freigabe

Die bestehende private `summary.json` bleibt unverändert. Später eine separate
`summary-live.json` im gleichen privaten Workspace erstellen, bestehende
`catalog`, `storage_roots` und `cache` übernehmen und ausdrücklich den einfachen
Modus wählen. Erst nach späterer Freigabe diese Werte setzen:

```json
{
  "model": "gpt-6-luna",
  "allow_source_upload": true,
  "strategy": "simple"
}
```

Dies ist ein **Patchbeispiel**, keine vollständige ladbare Konfiguration. Weitere
Felder aus der Mock-Datei sind erforderlich. Kein Secret gehört in diese Datei.
`OPENAI_API_KEY` ausschließlich für den späteren Testprozess setzen, etwa durch
eine verdeckte Terminaleingabe oder den vorhandenen Secretmechanismus. Kein
`.env` aus einem produktiven Dienst übernehmen. Der Starthelfer installiert nichts;
Anmeldung/Operatorrechte und `JOB_BACKEND=disabled` gelten unverändert.

Für genau einen Test den bestehenden Backend-CLI-Prozess verwenden und den
Live-Modus nicht gleichzeitig im Browser öffnen. Dadurch vermeiden wir weitere
Generierungen durch erneute Klicks. Vorher Preflight über die unveränderte
Mock-Konfiguration ausführen (siehe Abnahmeanleitung), ausgewählte Datei und
SHA256 sowie die private Zielablage kontrollieren. Ein neues leeres privates
Exportverzeichnis anlegen. Erst nach separater Freigabe etwa:

```bash
cd "$c27_backend"
# summary-live.json und API-Key werden erst nach Freigabe privat bereitgestellt.
mkdir -m 700 "$c27_workspace/live-export-01"
"$c27_python" -B -m scripts.lecture_summary generate \
  --config "$c27_workspace/summary-live.json" \
  --provider loviscach --course mathe_1 --lecture 01.01.2 \
  --detail compact --output "$c27_workspace/live-export-01"
```

Diese Befehle wurden nicht ausgeführt. Existiert das Exportverzeichnis bereits,
keine Dateien löschen oder ersetzen; einen neuen ausdrücklich benannten Testlauf
vorbereiten. Vorhandene Cachetreffer gesondert als solche protokollieren; ein
Cachetreffer ist kein Live-Nachweis. Caches nicht zum Erzwingen eines Requests löschen.

## Übertragung und Budget

Nur dieses tatsächlich vorhandene abgeleitete Transkript:

```text
loviscach/mathe_1/transcripts/01.01.2_weiter_drei_Arten_Mathematik.json
SHA256: 79a5dd28560679324fdfb3ab0b90307148add6e83267018235157dd718e756ce
Artefakt: lecture-artifact:2f230be05c452e56af6f1b9d3114c13354ea3f7e1796a32d87a6b12d15954689
```

Alle **25 Segmente** (`seg_id` 0–24, Zeitumfang 0–123,88 s), zusammen **1.813
UTF-8-Textbytes**, werden übertragen. Der Mock zeigt Q1/Q2; der echte Request
enthält alle 25 Segmenttexte mit ihren vollständigen Evidence-IDs. Ausdrücklich
ausgeschlossen ist der vorhandene Knowledge-Extrakt dieser Lektion sowie jedes
andere Lecture-Artefakt. Eine Transkriptstelle ist kein visuell verifizierter
Formelbeweis.

Gesendet werden nur ausgewählte Transkriptsegmenttexte, interne Source-IDs,
Lecture-ID, Warnungen, Generierungsoptionen, Systemprompt und Ergebnisschema an
den im bestehenden Adapter festgelegten HTTPS-Chat-Completions-Endpunkt.
Keine Audios, Videos, PDFs, sonstigen Kataloglektionen oder Quell-Hostpfade.
Kein Enrichment. `store=false` ist gesetzt. Das bedeutet **keine Zusage einer
vollständigen Nicht-Speicherung beim Anbieter**: Die offiziellen Angaben nennen
standardmäßig mögliche Abuse-Monitoring-Logs bis zu 30 Tagen und getrennte
Freigaben für Zero Data Retention. [OpenAI Docs: Data controls](https://developers.openai.com/api/docs/guides/your-data).

Der vorhandene RequestBudget begrenzt diesen Provider auf **einen Request**,
30.000 konservativ geschätzte Inputeinheiten und `max_completion_tokens=2000`;
Gesamtreservierung maximal 64.000. Die Eingangsabschätzung basiert auf UTF-8-
JSONbytes plus 2.048 für Framing, nicht auf einem tatsächlichen Tokenizer oder
einer Abrechnungsantwort. Die erneute Prüfung nach der Betreiberabnahme benutzt
exakt `SummaryProvider.request_payload`, einschließlich vollständigem Prompt,
Ergebnisschema, aller Quellen-IDs/-texte/-warnungen und Optionen:

| Bestandteil / Grenze | Offline geprüft |
|---|---:|
| Quellblöcke / Collector-Limit | 25 / 160 |
| Quelltextbytes / Collector-Limit | 1.813 / 26.000 |
| Systemprompt, diagnostischer Teilwert | 1.318 UTF-8-Bytes |
| Sources-JSON, diagnostischer Teilwert | 6.513 UTF-8-Bytes |
| Draft-Schema, diagnostischer Teilwert | 4.097 UTF-8-Bytes |
| Vollständiges serialisiertes Request-JSON | 13.348 UTF-8-Bytes |
| Zusätzliche konservative Framingreserve | 2.048 |
| Gesamter Inputbound / Sicherheitslimit | **15.396 / 30.000** |
| Reservierter Output | **2.000** |
| Gesamtreservierung / Limit | **17.396 / 64.000** |
| Modellrequests | **höchstens 1**, keine Retries |

Die drei diagnostischen Teilwerte sind wegen JSON-Escapes/verschachtelter
Serialisierung **nicht additiv**. Ausschlaggebend ist das vollständige Payload
plus Reserve. Auch die 2-MiB-Dateigrenze besteht unverändert; der Collector liest
die registrierte Quelle vor der Budgetprüfung sicher und prüft deren SHA256.
Payload-Fingerprint (RequestBudget-Serialisierung, UTF-8):
`e4562eec5ab0322554a9a0d34d26254f1d145eff68320076530d31d8962b24f7`.
Dies ist kein behaupteter HTTP-Wire-Fingerprint oder tatsächlicher Tokenverbrauch.
Die großen Fälle B/C sind nur im einfachen Modus über Budget; C27-C kann sie
hierarchisch offline verarbeiten. Sie gehören nicht zu diesem ersten Live-Test.

Reproduzierbar ohne HTTP-Client, Keyzugriff, Cacheänderung oder Aufruf:

```bash
cd "$c27_backend"
"$c27_python" -B -m scripts.lecture_summary_acceptance inspect \
  --config "$c27_workspace/summary.json" --model gpt-6-luna --case text
```

Die Konfiguration muss weiterhin Mock sein. `--case text` liest nur die eine
ausgewählte Quelle, auch wenn weitere Lectures im Katalog registriert sind.
Privates Prüfartefakt auf diesem Rechner:
`/home/robfra/0_Portfolio_Projekte/c27-review-evidence-20261024/live-request-prepared-only.json`.
Es enthält das vollständige zu sendende Payload zur lokalen Durchsicht, keinen Key;
es ist **nicht** eingecheckt oder gesendet. `offline-report.json` hält die Grenzen
und den unveränderten Quellhash fest. Die vorbereitete Mock-Konfiguration wurde
nicht geändert und keine aktivierbare Live-Konfiguration angelegt.

Mit den oben dokumentierten Standardpreisen ergibt die maximale lokale
30.000/2.000-Abschätzung rechnerisch **0,004 USD** ohne Steuern/weitere Aufschläge;
für Fall A rechnerisch **0,0025396 USD**. Bei konservativem 30-Minuten-Cache-
Schreibpreis von 0,125 USD/1 Mio. Inputeinheiten wären es **0,0029245 USD**;
mit 10 % Preisreserve rund **0,00322 USD**. Selbst mit dem dokumentierten
12-Stunden-Schreibpreis 0,25 USD läge dieser konkrete Request einschließlich
10 % bei rund **0,00534 USD**. Kein Cache-Rabatt wird benötigt.
Vorgeschlagenes **Laufbudget: 0,01 USD**, nur Standardverarbeitung ohne weitere
Tools, automatisches Caching-Opt-in oder Premium-/Fast-Tier. Vor Freigabe die
Projektvoreinstellung beim Betreiber prüfen; der Adapter setzt keine Service-Tier
und diese Vorbereitung prüft keine Kontoeinstellungen. Bei geänderten Preisen,
Scope, Modell, Prompt, Optionen oder Projekt-Tier erneut offline rechnen und bei
Überschreitung nicht starten. Der derzeitige einfache Provider implementiert keinen
separaten Dollarzähler: die Grenze wird hier durch genau einen freigegebenen
Prozess, den unveränderten Payloadbound und das Outputlimit begrenzt. Die 0,01 USD
sind ein vorgeschlagenes Betreiberbudget und **kein
anbieterübergreifender Geld-Hardcap**. Preise, tatsächliche Tokenisierung und
Kontobedingungen sind vor Ausführung zu prüfen. Kein automatisches Nachladen,
keine Tools, kein Batch, keine Wiederholungen. Der Ein-Request-Zähler gilt pro
Providerinstanz; neue Prozesse/UI-Reruns können neue Budgets erhalten. Daher
genau einen freigegebenen CLI-Lauf protokollieren.

## Timeout, Fehler und Speicherung

- HTTPX: 20 s Timeout für die jeweiligen Verbindungs-/Schreib-/Lesephasen,
  keine garantierte 20-s-Gesamtlaufzeit. Keine automatischen Retries, Redirects
  oder Nutzung von Proxy-Umgebungsvariablen. Antwort maximal 100.000 Bytes.
- HTTP-Fehler, Timeout, Refusal, abgeschnittene Ausgabe oder ungültiges Schema:
  Abbruch. Keine teilweise Antwort als Summary verwenden. Kein erneuter kosten-
  pflichtiger Versuch ohne neue ausdrückliche Freigabe. Auch Fehler können
  abrechenbar sein; Rohantwort/Key nicht in Logs oder PRs kopieren.
- Inhaltliches Quality Gate zusätzlich zum Schema. `failed`: keine Exporte,
  kein neuer erfolgreicher Cacheeintrag. Valide automatische Ergebnisse bleiben
  `needs_review`; technische Validität beweist keine fachliche Richtigkeit.
- Erfolgreicher Lauf: privates Summary-JSON im versionierten Cache, Markdown,
  vollständiges `.tex` und JSON im ausdrücklich benannten Exportverzeichnis.
  Kein PDF-Compiler und keine Datenbankmigration. Cache enthält Quelltext und
  muss privat bleiben. Original-SHA256 vor/nach Verarbeitung vergleichen.
- Protokoll: Zeitpunkt, freigegebener Scope/Modellname, Source-SHA256,
  Summary-ID/Promptversion, Status/Fehler, Cachetreffer oder tatsächlicher Request,
  tatsächliche Kosten aus der Betreiberabrechnung und manuelle Befunde. Der
  aktuelle Summaryadapter speichert keine verlässliche Usage-/Kostenauswertung
  aus der Providerantwort; keine erfundenen Kostenwerte in den Summaryrecord schreiben.

Erst danach anhand der [fachlichen Checkliste](c27_manual_acceptance.md#fachliche-checkliste-und-protokoll)
entscheiden, ob ein weiterer separat begrenzter Test sinnvoll ist. Dieser Auftrag
endet bei der Vorbereitung; es wurde kein Live-Modus eingeschaltet.
