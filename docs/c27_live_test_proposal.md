# C27 – Vorschlag für einen einzelnen kontrollierten Live-Test

**Nur vorbereitet, nicht ausgeführt.** Der aktuelle Katalog und die Startanleitung
bleiben im Mock-Modus. Dieser Vorschlag erteilt keine jetzige Kosten-/Uploadfreigabe.
Keine API-Abfrage zur Kontoverfügbarkeit und keine private Quelle wurden übertragen.

## Auswahl und Modell

Nur Abnahmefall A: `loviscach / mathe_1 / 01.01.2`, die vorhandene Fortsetzung
„Drei Arten Mathematik“, 25 Segmente. Kompakt, Standardfokus. Ziele: sinnvolle
Zusammenfassung des Modellierungsbegriffs, valide Provenienz und Exporte. Keine
mathematische Leistungsbewertung aus diesem Fließtextfall ableiten.

Ein kostenbewusster **Kandidat** ist `gpt-6-luna`. Die offizielle Modellseite
nennt Chat Completions und Structured Outputs sowie regulär 0,10 USD/1 Mio.
Inputtoken und 0,50 USD/1 Mio. Outputtoken. Vor dem späteren Test Modellstatus,
Kontozugriff, aktuelle Parameterkompatibilität und Preise nochmals prüfen;
der Alias ist kein unveränderlicher Snapshot. Der bestehende Adapter nutzt
JSON-Objektmodus und keine Tools. Keine Modellumstellung oder Providererweiterung
ist für diese Vorbereitung erfolgt. [OpenAI Docs: GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).

Der Adapter konfiguriert aktuell keine modellabhängige Reasoning-Stufe. Bei einem
Reasoning-Modell kann das kleine Ausgabevolumen bereits für interne Tokens
aufgebraucht werden. Eine abgeschnittene/fehlende JSON-Ausgabe ist ein erwartbarer
negativer Testausgang, kein Anlass für eine automatische Fortsetzung oder ein
größeres Budget. Die Modellseite ist eine Kompatibilitätsgrundlage, kein bereits
erbrachter Nachweis einer erfolgreichen C27-Liveantwort.

## Private Konfiguration erst nach gesonderter Freigabe

Die bestehende private `summary.json` bleibt unverändert. Später eine separate
`summary-live.json` im gleichen privaten Workspace erstellen, bestehende
`catalog`, `storage_roots` und `cache` übernehmen und nur diese beiden Werte setzen:

```json
{
  "model": "gpt-6-luna",
  "allow_source_upload": true
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
einer Abrechnungsantwort. Der unveränderte Fall A wurde offline mit **15.396**
ermittelt und passt. Fälle B/C passen derzeit nicht und sind ausgeschlossen.

Mit den oben dokumentierten Standardpreisen ergibt die maximale lokale
30.000/2.000-Abschätzung rechnerisch **0,004 USD** ohne Steuern/weitere Aufschläge;
für Fall A rechnerisch rund 0,00254 USD. Das ist eine Kostenabschätzung, **kein
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
