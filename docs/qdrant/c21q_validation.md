# C21-Q: tatsächlich ausgeführte Validierung

Stand: **17.10.2026**. Phase A ist vorbereitet und lokal teilweise geprüft,
aber **nicht vollständig bestanden**: Ein funktionierender isolierter
Qdrant-Index mit Readback und Retrieval konnte in dieser Umgebung nicht
ausgeführt werden. Phase B ist **blocked, keine Betreiberfreigabe**. Weder
Hetzner/Coolify noch eine Remote-Collection wurden angesprochen.

## Nachweise und ihre Grenzen

Finale kombinierte lokale Regression nach Übernahme des aktuellen Masters:
**61 bestanden, 1 übersprungen in 103,69 s** (62 tatsächliche `testcase`-Elemente:
20 Pilot, 8 Embedding, 28 KnowledgeInput, 6 Deployment). Anschließend bestanden
die sechs betroffenen Remote-Guards erneut in 0,35 s nach Absicherung gegen die
separate SDK-Hintergrundversionsabfrage. Diese Wiederholung ersetzt dieselben
sechs Fallstände; sie wird nicht als zusätzliche Fallzahl addiert. Der einzige
Skip ist `test_real_local_pilot`, weil dessen ursprünglicher Fixtureworkspace
nicht bereitgestellt wurde. Die ausdrücklich ausgewählte reale Quellkopie wurde
separat wie unten beschrieben geprüft. Ruff, Format, Shellsyntax und
`git diff --check` bestehen. [Maschinenlesbarer Nachweis](validation.v1.json).

| Prüfung | Beobachtetes Ergebnis | Aussagegrenze |
| --- | --- | --- |
| Neue Pilot-/CLI-Guards | 20 Tests bestanden | Synthetische lokale Fixtures, keine echte E5-Inferenz |
| Bestehende Embeddingverträge | 8 Tests bestanden | Technische Offset-/Vektor-/Quellprüfungen, keine Modellqualität |
| Deploymentguards | 6 Tests bestanden | Authdatei-Shellprüfung und Compose-Rendering, kein Containerstart |
| Gemeinsamer erster Lauf (Vorläufer) | **34 Testfälle**, 43,34 s, keine übersprungenen Fälle | Kein Server-/SDK-/E5-Nachweis |
| Abschließende SDK-freie Regression | **55 bestanden, 1 übersprungen**, 76,44 s (20 Pilot + 8 Embedding + 28 Knowledge-Input) | Der optionale Test mit bereits importiertem Originalpilot findet seine lokale Eingabe nicht; der separat dokumentierte bytegleiche Kopientest ersetzt diesen Skip nicht |
| Verschärfte Deploymentguards erneut | **6 bestanden**, 2,04 s | Zusätzlich Read-only-Mounts, Rechtehärtung, Ressourcen und unerlaubte Authzeilen geprüft |
| Qdrant-Collection/Ingestion/Retrieval/CLI-Regression | Testcollection durch fehlendes `qdrant_client` blockiert | Kein Erfolg, keine stillschweigende Überspringung |
| Reale ausgewählte Python-0-Quelle | Raw-/Transcript-/Receipthashes und bestehendes Binding in bytegleicher temporärer Kopie verifiziert; 157 zeitbasierte Chunks | Originalablage passt nicht zu Receiptpfaden; keine E5-Unit-/Vektorzahl |
| Reales Embedding | Nicht ausgeführt | SDK, SentenceTransformers und geprüfte immutable Modellgewichte fehlen |
| Qdrant-Dienst, TLS/Auth, Persistenz, Neustart, Restore | Nicht ausgeführt | Kein vorhandenes freigegebenes Image und keine Serverfreigabe |

Der ursprüngliche JUnit-Wrapper nennt im Summenattribut fälschlich 54 Tests;
die enthaltenen `testcase`-Elemente ergeben **34** (20 + 8 + 6).
Dieser Bericht verwendet die tatsächlich enthaltenen Fälle. Historische
master-Ergebnisse unter
[transcript_index_completion.md](../cs50/operations/transcript_index_completion.md)
sind ausdrücklich kein neu gemessener C21-Q-Serverlauf.

Die Offline-Prüfung lässt sich aus dem Repositoryroot wiederholen; eine
vorhandene Projektumgebung verwenden, ohne Dependencies nachzuinstallieren:

```bash
python -m pytest -q \
  tests/test_cs50_pilot.py tests/test_cs50_embeddings.py \
  tests/test_cs50_knowledge_input.py \
  deployment/qdrant/test_deployment.py
bash -n deployment/qdrant/entrypoint.sh deployment/qdrant/healthcheck.sh
ruff check --no-cache \
  scripts/cs50_transcript_index.py src/tools_rag/cs50_pilot.py \
  tests/test_cs50_pilot.py deployment/qdrant/test_deployment.py
```

Compose-Rendering benötigt die vorhandene Docker-Compose-CLI, aber keinen
Docker-Engine-Zugriff. Authentifizierungstests verwenden ausschließlich selbst
erzeugte synthetische Schlüsseldateien und entfernen ihre temporären Verzeichnisse.
Die aktuelle Laufzeitprüfung ist kein Test gegen einen erreichbaren Server;
gemockte Clientkonstruktion beweist weder TLS noch einen gültigen API-Key.

## Fehlerfälle: geprüft oder noch offen

| Fehlerfall | Ausgeführter Nachweis / ausstehende Abnahme |
| --- | --- |
| Fehlende/beschädigte Rawdatei, Transcript oder Receipt; Symlink | Offline-Inventar verweigert Binding; bestehende Dateien bleiben unverändert |
| Fehlender Herkunftsnachweis / expliziter ungebundener Kandidat | Kandidat wird nie automatisch übernommen oder zum Uploadplan erklärt |
| Nicht-HTTPS, Credentials, Pfad, Query oder Fragment im Remote-Origin | Vor SDK-/Netzwerkverwendung abgewiesen |
| TLS, Redirect und Umgebungsproxy | Clientoptionen deterministisch geprüft; echter Zertifikats-/Proxytest noch offen |
| Fehlender/ungültiger Authdateiinhalt, identische/Nullkeys, falsche Rechte, Symlink, Environmentoverride | Wrapper bricht ohne Secret-/Pfadinhalt ab; echte Qdrant-API-Authentifizierung noch offen |
| Fehlende Pflichtmounts/-instanzwerte | Compose-Rendering schlägt ohne Start oder Verzeichniserstellung fehl |
| Bestehender Inventaroutput | No-Overwrite-Guard geprüft |
| Nicht erreichbar, falscher API-Key, fehlende Collection | Echte SDK-/Serverfehlerprüfung blockiert |
| Falsche Dimension/Revision, Dubletten, beschädigte Payload, unvollständiger Readback | Vorhandene Vertrags-/Ingestiontests benötigen fehlendes SDK; aktueller vollständiger Nachweis offen |
| Unterbrochener Upload und verlorene Bestätigung | Bestehendes Resume wird wiederverwendet; reale isolierte Wiederholung noch offen |
| Voller Datenträger, Containerneustart, konsistenter Snapshot/Restore | Betriebsrunbook vorhanden; Tests an isolierter Instanz noch offen, keine fremden Daten gelöscht |

## Reale Quellen und maschinenlesbare Reports

Der [Quellfreigabebericht](real-source-approval-review.v1.json) hält eine
ausgewählte reale Lecture und eine bytegleiche Dublette auseinander. 2228 Cues,
0–6338 Sekunden und 189973 Rawbytes sind gemessen. Die bereits vorhandenen
Dateien unter `data/Harvard/...` widersprechen den vom Adapter gebundenen Pfaden
unter `data/lectures/Harvard/...`. Deshalb ist der Originalworkspace direkt
**unverified**. Nur ein expliziter privater temporärer Workspace mit denselben
drei unveränderten Dateien unter den vorhandenen Receiptpfaden wurde erfolgreich
gebunden und anschließend bereinigt. Kein produktiver Pfad wurde repariert,
kein Receipt migriert und kein neues Artefakt adoptiert.

- [Indexierungsreport](indexing.v1.json): `status=blocked`, 0 hochgeladene und
  0 verifizierte Points; Plan, Modellrevision und Vektorartefakt bleiben `null`.
- [Retrievalreport](retrieval.v1.json): `executed=false`; keine Treffer und keine
  berechneten Precision-/Recall-/MRR-Werte.
- [Ressourcenreport](resources.v1.json): lokale CPU-/RAM-/Platzvoraussetzungen;
  E5-Durchsatz, Vektorzahl, Qdrantgröße und Kursprojektion bleiben unbekannt.
- [Manuelle Reviewvorlage](manual-review.v1.json): zehn vorhandene
  source-grounded Fragen, keine unabhängigen Goldurteile oder Modellqualitätswerte.

Ein echter ausführbarer IngestionPlan lässt sich erst mit bereitgestelltem
Tokenizer und voller geprüfter Modellrevision erzeugen. Der Freigabebericht
referenziert die Quellen und die noch nötigen Entscheidungen; er ersetzt diesen
Plan nicht. Weder synthetische 100 Points noch 157 zeitbasierte Chunks dürfen als
tatsächlich erzeugte E5-Vektoren ausgegeben werden.

## Nächste abnehmbare Schritte

Zunächst vorhandenes Workerprofil/SDK und eine ausdrücklich ausgewählte lokale
E5-Revision bereitstellen; notwendige Downloads vorher gesondert freigeben.
Dann die isolierte Qdrant-Testumgebung und ihre synthetische Ingestion, alle
Points, Filter, Neustart und Recovery tatsächlich prüfen. Die Quellpfadabweichung
muss vor einem dauerhaften echten Pilot kontrolliert gelöst werden. Erst danach
einen realen Plan und Vektoren erzeugen; Phase B benötigt zusätzlich die konkrete
[Betreiberfreigabecheckliste](c21q_operations.md). Keine Entwicklungsfreigabe,
CLI-Flagkombination oder bestandener Unit-Test ersetzt diese Freigabe.
