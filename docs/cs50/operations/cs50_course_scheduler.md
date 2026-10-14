# B03 – Versionierter sequenzieller Kursauftrag

Abhängigkeit: B02 (PR #32). ScheduleRequest bindet Plan-Digest, explizite Kurse,
Source-/Job-IDs und concurrency=1. prepare_schedule verlangt jede ausgewählte
geprüfte Inputbindung; fehlende/ungültige Quellen werden als PreflightFailure mit
Source/Kurs/Abschnitt und Fehlerklasse dokumentiert, ohne Providerdispatch.

run_schedule hält einen Scope-Lock, verwendet ein gemeinsames Budget und prüft
alle Quellen und Checkpoints vor Verarbeitung offener Lectures. Erfolgreiche
Lectures werden vollständig erneut validiert; nur tatsächlich offene Jobs zählen
gegen max_lectures. Keine Überspringlogik anhand bloßer Dateiexistenz. Ein
unknown/failed oder kaputtes Statusartefakt blockiert weitere Requests. Es gibt
keinen Video-/Whisper-Fallback. Status wird atomar pro Lecture persistiert;
Kursauftrag und Budgets bleiben über Neustarts gleich.

Der Invalid-Source-Test hat einen konkreten Sicherheitsfehler sichtbar gemacht:
ein vorbereiteter pending-Job wurde zuvor nicht erneut gegen zwischenzeitlich
geänderte Quelldateien geprüft. Minimal korrigiert: echte Inputrevalidierung bei
Scope-Preflight, Runnerstart und unmittelbar vor Budget-/HTTP-Dispatch. Die
unveränderte Assertion "kein Provider bei ungültiger späterer Quelle" ist der
Regressionstest. Verfügbare Providerusage bleibt auch bei unknown separat im
Budgetjournal erhalten; Reservierungen werden nicht erstattet.

Tests verwenden zehn Python-Lectures mit echten Fake-HTTP-SRT-Imports und bestehenden
Kernfunktionen: erster begrenzter Lauf, next-pending/Resume bis zehn, kein weiterer
Provider beim erneuten kompletten Lauf, ungültige letzte Quelle ohne Dispatch,
unknown und Schedulerkonkurrenz/kaputtes Status-JSON. CLI/Sechs-Kurse-Scope folgt B05.
