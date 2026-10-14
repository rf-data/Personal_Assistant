# Transcript-Index: Offline-E2E-Nachweis

Basis master 4dcd3c7, integrierte Archivstruktur #38; gestapelte Index-PRs #39–#43.
Reale Executor-/Importer-/Binder-/Chunker-/Qdrant-Funktionen, ausschließlich
synthetische SRTs, MockTransport und ausdrücklich markierte Fake-Embeddings.
Physisch persistierte isolierte lokale Qdrant-Datenbank, geschlossen und neu geöffnet.
Keine produktive Verbindung, Modell-/SRT-Downloads oder LLM-/Whisperaufrufe.

Gezielter Lauf: **3 passed in 773,74 s (12:53)**, /tmp/cs50-index-e2e.xml und .log.
Eine vollständige Lecture, zehn Python-Lectures, alle sechs/50 Lectures; zwei echte
zeitbasierte Chunks je synthetischer Lecture. 2/20/100 vollständig abgeschlossene
Download-/Importtasks mit jeweils eindeutigen Task-IDs. Leere Cues ohne Embeddings.
2/20/100 eindeutige Points; alle Originalidentitäten einschließlich ai, Woche 0
und Cybersecurity media_id=None erhalten. Sources/Input-/Plan-/Vector-JSON-Roundtrip.

Kurs- und Sechs-Kurse-Lauf: tatsächliche erste vier Points geschrieben, danach
synthetischer Timeout/lost acknowledgement; failed Receipt, kein fingierter Erfolg.
Resume liest tatsächliche Points, ergänzt ausschließlich fehlende, vollständig
geprüfter Abschluss. Zweiter kompletter Resume ohne Duplikate. Filter und Treffer
gegen originale synthetische Quelldokumente geprüft. Keine Gold-/Qualitätsbehauptung;
Recall/MRR bleiben null.

Zusätzlicher Regressionstest: ein schema-gültiger alter Source-/Resource-Point
unter demselben Kursabschnitt wurde zunächst übersprungen (Test tatsächlich rot:
DID NOT RAISE). Minimal korrigiert: ausgewählte course_id/section_key-Slots prüfen
lecture_id/resource_id/source_id auch vor dem Source-ID-Filter. Ersetzte Quellen
verlangen einen expliziten neuen Index; keine alten Points heimlich zurücklassen.
Gezielter Fix + Evaluationsverträge: **4 passed in 49,64 s**. Aktualisierte
synthetisch markierte Evaluationstests: **3 passed in 22,01 s**.

Zehn tatsächliche Python-0-Referenzfenster read-only gegen vorhandene offizielle
SRT-/Importbelege validiert, Raw-SHA256 719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c.
Nur vorgeschlagene Fragen/Cue-IDs/Originalzeiten/Hashes versioniert, keine
Originaltranskripte oder lokalen Pfade. Keine Relevanzurteile erfunden.

Echte Modellgewichte fehlen, daher keine CPU-/RAM-/semantischen Rankingmessung.
Gesamtregression folgt auf dem finalen Index-Stack; die sechs bekannten TXT-Fehler
werden separat verglichen. SDK-Cache-/Fresh-sync-Voraussetzung bleibt dokumentiert.
