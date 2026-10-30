# C26-LS-01 – Lecture Summarizer & Learning Dashboard

Lokaler, quellengebundener Streamlit-MVP auf Basis
`1584a2807c8f9d75604ab17a4ea239d8f4a0882b`.

- [Architektur und wiederverwendete Funktionen](architecture.md)
- [Betreiber-/Entwickleranleitung, Datenfluss, Adapter und Grenzen](operations.md)
- [Validierung und Abnahme](validation.md)
- [Beispielzusammenfassung mit Originalreferenzen](example-summary.md)
- [Strukturiertes Beispiel einschließlich separater Review-Ereignisse](example-summary.json)
- [Reproduzierbarer Offline-End-to-End-Report](offline-report.json)

```bash
python -m streamlit run lecture_summarizer_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Der synthetische Week-0-Kurs enthält Lecture, Short, Transcript, Notes, Python-Code
und ausdrücklich fehlende Folien. Kein externer Kursinhalt wird heruntergeladen.
Fake-Modell ist Standard; Laden, Navigation und Quellenansicht lösen keine
LLM-Anfrage aus. Ein realer Adapter verwendet `src.llm.model_litellm.LLMClient` erst
nach einem expliziten Start.

## Bekannte Einschränkungen

1. Extraktive Zusammenfassung: Aussagen bleiben wörtliche Ausschnitte. Keine freie
   sprachliche Verdichtung oder Ergänzung fehlenden Wissens. Titel und Kategorien
   sind Gliederungshilfen, keine unabhängig bewiesenen fachlichen Aussagen.
2. Deduplizierung nur exakter Ausschnitte; Konflikthinweise für gleiche Modellthemen
   und einfache Negationen. Keine vollständige semantische Widerspruchserkennung;
   Aussagen bleiben erhalten und benötigen menschliche Quellenprüfung.
3. Formeln: beschränkte vorhandene Syntaxgrammatik, keine Wahrheits-/Äquivalenzprüfung.
   Code: Python-Syntaxprüfung, keine Ausführung oder Korrektheitsgarantie.
4. Zeichenbasierte Slices können Sätze oder Code teilen. Unsichere/ungültige
   Ergebnisse werden markiert, nicht automatisch repariert. Kleinere Quellenauswahl
   oder passende Chunkgröße wählen. Maximal 32 Abschnitte je Run.
5. Synchroner Single-User-Betrieb mit lokaler Dateisperre. Kein persistenter
   Hintergrundworker, kein verteilter Betrieb, kein harter Prozessabbruch für
   Fremdadapter, die ihren Timeout missachten. Abgebrochene Teilruns werden bei
   Wiederholung nicht automatisch fortgesetzt.
6. Quellenprüfung zeigt gespeicherten Ausschnitt, Originalhash und genaue
   Zeit-/Seiten-/DOM-/Zeilenreferenz. Direkter Dateisprung und lokale Videowiedergabe
   sind noch nicht integriert. Unbekannte Zeiten bleiben ausdrücklich unbekannt.
7. Nur synthetische Offline-Abnahme. Echte CS50P-Materialien müssen unabhängig
   geprüft als lokaler Katalog übergeben werden. Kein Zugriff auf ungesicherte
   C08-Ergebnisse und keine generelle Freigabe fremder Materialien durch den Adapter.
8. Reale LiteLLM-SDK-/Provider-Ausführung ist optional und hier nicht gegen einen
   Dienst getestet. Der vorhandene Abstraktionsaufruf wurde mit SDK-Doppel geprüft.
   Kosten werden nur aus gemeldeten Tokens und explizit konfigurierten Preisen
   geschätzt; bei unbekanntem Verbrauch bleibt die Schätzung unbekannt.
9. Browser-/HTTP-Start ist in dieser Sandbox wegen verbotener Sockets nicht möglich.
   Der vollständige Einstieg wurde mit echtem Streamlit-AppTest ausgeführt.
   Manueller Loopback-Browser-Smoke bleibt Teil des lokalen Reviews.
10. Kein ACL-/Mehrbenutzerbetrieb. Store und Katalog sind vertrauenswürdige lokale
    Operator-Dateien; Hashprüfung erkennt Beschädigung, ersetzt aber keine Signatur.
    Rohantworten können Quelltext enthalten und bleiben lokal privat.

## Übergabe und Branch-Lebenszyklus

Keine automatischen Pushes, Merges oder Produktionsinstallationen. C16-Quarantäne,
Download-, Hetzner- und Coolify-Gates bleiben unverändert. Alle Änderungen liegen
im vorgesehenen Feature-Worktree. Der zugehörige Patch mit SHA-256 liegt unter
`artifacts/c26_ls_01/handoff/` und wird gegen einen isolierten Checkout des
Basiscommits geprüft.

Branch und Worktree waren bei Sitzungsbeginn bereits vorhanden; in dieser Aufgabe
wurden keine neuen Git-Branches oder Worktrees angelegt. Sie bleiben erhalten, da
Integration ausdrücklich ausgeschlossen ist. Die dauerhaften Berichte sind in
`docs/lecture_summary/` und im Patch enthalten, aber noch nicht in `master`.
Nach dem lokalen Review ist die reguläre PR-/Review-Integration erforderlich;
Integrations- und Cleanup-Abschluss bleiben bis dahin offen. Keine MAINT-Artefakte
wurden entfernt.
