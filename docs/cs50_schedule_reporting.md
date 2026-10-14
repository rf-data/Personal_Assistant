# B04 – Kursweiter Quality-/Coverage-Bericht

Abhängigkeit: B03-Scheduler. aggregate_schedule verlangt den passenden Scope,
exakt die abgeschlossenen Sourcewerte, Completionidentitäten und Hashes für alle
vier Artefakte. Fremde/kaputte Quality- oder Coverage-Daten werden abgewiesen.
inspect_schedule_report revalidiert über den Scheduler im audit_only-Modus; kein
Provider wird initialisiert oder dispatched.

Bericht: geplante/abgeschlossene Lectures, pending/partial/failed/unknown/done,
erwartete und validiert verarbeitete Chunks, Statement-/Formelzahlen, Evidenzscopes,
Source-/Kurs-/Lecture-/Resource-/Media-IDs, URLs, Transcript-Hashes und relative
Abschlussreferenzen. Quality-Zahlen gelten ausdrücklich für vollständig
abgeschlossene Lectures; partielle Chunkfacts sind keine vollständigen Dokumente.

Evidenzquoten entstehen aus summierten Zählern und Nennern, niemals aus dem
Mittel von Lecturequoten. Usage wird getrennt von konservativer Tokenreservierung
berichtet; unbekannte Usage wird gezählt, nicht als tatsächlicher Nullverbrauch
behauptet. Synthetische Ergebnisse bleiben als synthetic markiert.

Der Test benutzt zwei echte Import-/Chunk-/Consolidation-Pfade mit ungleichen
Vorlesungsgrößen und überprüft eine natürliche gewichtete Evidenzquote sowie
Read-only-Revalidierung und abgewiesene geänderte Quality-Daten. Keine Goldurteile.
