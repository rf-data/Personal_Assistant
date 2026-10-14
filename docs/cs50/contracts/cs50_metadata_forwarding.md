# A04 – Metadatenweitergabe

Abhängigkeit: portable-inputs-Branch. Der allgemeine Extraction-Konstruktor
übernimmt Sprache und TranscriptProvenance aus dem geladenen Transcript sowie
course_id aus dem vorhandenen Kontext. lecture_id wird nur übernommen, wenn der
Kontext sie tatsächlich besitzt; andernfalls bleibt sie None. Bestehende Legacy-
source_id-/URL-/media-Regeln werden hier nicht erweitert oder neu hergeleitet.

Beide Ergebniszweige der semantischen Consolidation übernehmen media_id sowie
transcript_metadata() des Eingangs. Die deterministische Consolidation tat dies
bereits und bleibt unverändert. Keine semantische LLM-Ausführung oder Änderung
von Evidence, Prompts oder Modellen.

Ausgeführt: Provenienz-, Source-ID- und Lazy-Import-Tests: **56 passed in 6,57 s**.
Die beiden bekannten Metadaten-Integrationstests bestehen ohne geänderte Assertions.
Ihre semantischen Aufrufe werden offline mit den bestehenden Test-Doubles geprüft.
