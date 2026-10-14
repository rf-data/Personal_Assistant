# A02 – Dauerhaftes Budgetjournal

Basis: master de4ac38, A01/PR #26 ist integriert. Neue Ausführungswrapper
BudgetIdentity/BudgetState/Attempt ergänzen, ersetzen aber keine Knowledge-Modelle.
Ein expliziter Scope-Digest und eine unveränderliche Liste erlaubter Job-IDs binden
Request-/Tokenobergrenzen. Ein kurzer POSIX-flock schützt jede Transaktion;
kein Netzwerk läuft unter dem Budgetlock. Atomare fsync-Publikation übernimmt A01.

Reservierungsschlüssel = Digest von Job-ID und Chunk-ID. Jeder Schlüssel darf nur
einmal reserviert werden. Requestzahl und Tokenverbrauch werden aus den dauerhaften
Attempt-Einträgen abgeleitet; kein rücksetzbarer Prozesszähler. Tokens werden
konservativ vollständig reserviert, auch bei 429/5xx/Timeout/unknown. Tatsächliche
Usage wird zusätzlich erfasst, führt aber nicht zu automatischen Rückerstattungen.
Ein noch reserved oder unknown gebliebener Attempt wird niemals erneut dispatched.

budget.contract.v1.json ist exklusiv und unveränderlich; budget.v1.json wird
unter Lock atomar ersetzt. Fehlendes/beschädigtes Journal bei vorhandener
Identitätsdatei ist ein Konflikt, kein neues Budget. Andere Limits/Scopes und
fremde Jobs sind Konflikte. Symlinks werden abgelehnt. Ein gelöschter kompletter
Workspace ist keine Resume-Quelle; der Lecture-Runner muss zusätzlich die
Budgetreferenzen in A01-Receipts kontrollieren.

Schnittstelle: vor Transport erst BudgetJournal.reserve(job_id, chunk_id,
reservation), dann CheckpointStore.reserve mit dessen budget_id/attempt_id.
Scheitert Schritt zwei, bleibt die Reservierung verbraucht und es darf kein
Transport stattfinden. Nach verifiziertem Abschluss finish(..., status='done',
usage=...), bei ungewissem Ausgang unknown. Kein automatisches Retry/Reset.

Tests: test_cs50_budget.py (Neustart, Limits, Korruption, zwei gleichzeitige
Prozesse, tatsächlicher Fake-HTTP-Dispatch mit 429/500/Timeout) und unveränderte
A01-Tests. Der begrenzte Pilot wird in diesem PR nicht umgebaut; Integration
in den separaten Lecture-Runner folgt in B01.
