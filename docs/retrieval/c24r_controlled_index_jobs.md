# C24-R2 kontrollierte Indexjobs

Geprüfte Wiederverwendung des isolierten Featurecommits `c07ed9a` aus DEV-01B;
Abhängigkeit: R1/`4259187`. Keine fremden uncommitteten Änderungen übernommen.
[API-/Katalogvertrag](../api/content_index_jobs_v1.md),
[Models](../../src/job_control/index_models.py).

`content_index_build` ist ausschließlich mit `index_jobs_enabled=true` im
vorhandenen C16-Prozesskatalog sichtbar/startbar. Kein zweites C18-Workflowmodell:
C16-Prozess, dieselben Job-/Artifactverträge und additive C18-Schemas. Expliziter
hashgeprüfter IndexJobPlan bindet Course, Content-/Indexkonfiguration, Selection
und geordnete Source-/Parsed-/Parser-/Payload-/Projektionsversionen.
HTTP nimmt Katalogreferenzen entgegen, keine Material-/Indexpfade.

Preview, Annahme, Dispatch und Build prüfen Scope/Owner und aktuelle Freigaben.
Auch das Ersetzen einer aktiven Generation verlangt Ownership aller bisherigen
Sources. Job-Initiator und Content-Owner bleiben unterschiedliche Verträge.
Status-/Input-/Job-/History-/Artifact-/Logrouten prüfen Live-ACL, Statusantworten
halten den Contentguard durch die Auslieferung. Reads führen keine Jobs aus.

Idempotenz bleibt Subject+Key+Intent aus C16. Gleicher Key führt keine erneute
Ausführung aus; bewusster Retry erfordert einen neuen Key und terminalen Parent.
Job-ID bindet Build-ID. Nach Restart keine Stagingadoption und kein automatischer
Retry: interrupted oder bei unklarem Cleanup Quarantäne. Wenn die Generation
bereits exakt aktiviert ist, verifiziert ein expliziter Retry sie vollständig
und liefert already_active. Atomarer Generationstausch erhält den letzten gültigen
Pointer bei Fehlern vor Publikation. Cancel ist kein Rollback nach Aktivierung;
latest_activation ist deshalb committed/not_committed/undetermined.

Ressourcen: vorhandener Guardian mit Prozessgruppe/Elterntod, CPU 120 s,
Prozesslaufzeit 180 s und Filelimit 64 MiB; FTS-/I/O-/Datensatzgrenzen bleiben
unverändert. Keine Timeoutverlängerung, Scheduler, Cloud oder automatische
Dateisystemüberwachung. Native Prozessproben verändern ausschließlich eigene
synthetische Testroots.

Aktueller R2-Lauf: 19/19 bestanden. Zusätzliche C24-R-Tests decken Cancel vor
Dispatch, laufenden Build unter unverändertem Guardian, API-Wiederöffnung und
Erhalt der letzten Generation ab. Vollständige Ergebnisse und Abnahmegrenzen:
[Validierung](c24r_integration_validation.md).
