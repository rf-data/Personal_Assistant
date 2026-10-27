# C26-CS50P-MVP: Architektur und Bestandsprüfung

Stand 27.10.2026. **HOLD – Reviewpaket, keine Produktionsfreigabe.**
INT-02-Basis: `6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d` (Parent `be03e83`).
Vor Implementierung als Gitarchiv gesichert und SHA-256 geprüft; bestehende
INT-02-Handoffprüfsummen bestätigt. Kein INT-02-/UI-Patch überschrieben.

## Befund vor Implementierung

| Funktion | Bereits vorhanden | Verwendung / Grenze |
|---|---|---|
| Kursinventar, Metadaten, Links | `prepare_cs50`, `cs50_manifest`, `tools_materials.inventory`, `make_plan` | Discovery aus hashgebundenen lokalen Snapshots; kein unbeschränkter Livecrawler |
| Materialauswahl / Download | `scripts.cs50_batch plan/download`, `batch.obtain`, `MaterialDownloader`, `CS50Executor.download` | Serial, 1 MiB/Material im Batch, TLS, keine Redirects, Timeouts, Retryprimitive |
| Integrität / Wiederaufnahme | `ArtifactReceipt`, SHA-256, `validate`, `storage.locked` | Vollständige Dateien wiederverwenden; Teilstücke neu laden nach Betreiberprüfung, kein HTTP-Range |
| HTML/PDF/Code | `MaterialProcessor`, HTML-v2, PDF-v2, Code-v1 | Normalisierte Dokumente, Provenienz, Qualitätsprüfung, persistente Ergebnisse |
| Medien | SRT-/TXT-Import, Media-last-Planung, Lecture-/Transkriptpfade | Vorhanden, aber Video/Audio, yt-dlp, Whisper, ZIP und LLM nicht im MVP aktiviert |
| Katalog / Ausführung | `batch.seal`, C18-Workflow, C16-Controller/Executor/Guardian, `cs50_worker` | Keine zweite Queue oder Jobengine nötig; Status, Abbruch, Recovery vorhanden |
| Kapazität / Sicherheit | `CapacityLimits`, `CapacityExecutor`, Pfadpolicy, C22-Fence, C26-Admission | Beibehalten; Gates dürfen nicht auf false gesetzt werden |
| SSH-unabhängiger Betrieb | Bestehende Dockerprofile mit separatem Downloader/Executor | Für den einzelnen Betreiber native systemd-Dienste vorbereiten |

## Entscheidung

systemd verwaltet genau einen manuellen Downloadprozess und einen vorhandenen
C16-Worker. Keine Timer, kein Bootautostart, keine API, kein Socketlistener.
Dienststart ist unabhängig von SSH; abgemeldete Sitzung oder ausgeschaltetes
Chromebook beendet den Dienst nicht. Hostreboot startet nichts automatisch;
C16 erhält seine Daten und reconciliert unterbrochene Jobs ohne automatisches Replay.
Diese Eigenschaft folgt dem Dienstprofil; ein echter Host-/Logouttest wurde nicht ausgeführt.

Native Pythonlaufzeit unter `/opt/cs50p`, eigene Daten unter `/var/lib/cs50p-mvp`.
Damit gilt der vorhandene Vertrag für externe Arbeitsverzeichnisse; keine Ausnahme
für Repositorypfade, kein Patch an `runtime_paths`, kein Absenken von Mountprüfungen.
Der Coolify-Container mit `sleep infinity` bleibt unverändert. Die vorhandenen
Dockerfiles/Locks wurden geprüft: deren API-/Gateway-/Imageadmission würde für
diesen Pilot zusätzliche, ungeklärte Abhängigkeiten einführen. systemd vereinfacht
Prozessaufsicht, ersetzt jedoch ausdrücklich keine erforderliche C26-Admission.

Download und Verarbeitung bleiben zwei überprüfbare Phasen: Download, `seal`,
Katalog-/Controllerreview und gültige Admission, dann C16-Submit. Die dynamischen
Rawhashes erlauben keine ehrliche vorgezogene Verarbeitungsgenehmigung für unbekannte
Bytes. Kein neuer Kombinationsbefehl schaltet diese Freigabegrenze stillschweigend frei.

## Nachgewiesener Änderungsbedarf

Neu: `scripts.cs50p_mvp download` begrenzt den bestehenden Batchpfad auf CS50P,
HTML/PDF, drei Quellen und kleine Hostlimits; persistente, redigierte Versuchsreports,
SIGTERM-Behandlung, Lauf-Lock, Gesamttransferbudget. `worker` prüft Scope und zwingende
Gates vor dem unveränderten Kapazitätsworker. Bestehender Downloader bekommt
öffentliche DNS-Prüfung und IP-Pinning bei originalem TLS-SNI/Host, vollständige
Content-Length-Prüfung, erwarteten Hash vor Veröffentlichung, PDF-Signatur,
separates `.incoming` und atomaren No-replace-Move. Fehler speichern nur Klassen.
Die bestehende Linux-No-replace-Publikation ist als Dateihilfe wiederverwendet.

Kein neuer Parser, Scheduler, Webdienst, LLM-Aufruf oder neuer Persistenzvertrag.
Geänderte generische Downloaderpfade werden zusätzlich gegen Bestandstests geprüft.

## Konkreter Admissionblocker

Die Bestandsprüfung von `deployment_gate.py` / `deployment_scope.py` und
`c26d_gate_v2.md` zeigt: v2 bindet derzeit einen vollständigen UI/API/Worker-
Operationscope, Image-/Containerbelege und einen ausdrücklich synthetischen
Offlinejournalmodus. Für einen einzelnen nativen systemd-Worker gibt es in
diesem Bestand keinen nachgewiesenen produktiven Admissionpfad. Eine leere neue
Queue ohne gültiges Journal wird ebenfalls abgewiesen. Daher reicht das bloße
Setzen von execution_enabled/workflows_enabled nicht zum Start.

Eine separate, überprüfte Anpassung des bestehenden Admissionvertrags an die
vereinfachte native Runtime ist vor einem echten Verarbeitungsjob nötig. Dieses
Paket hat keine solche Freigabe oder produktive Gateerweiterung implementiert.
Es erzeugt keinen synthetischen Ersatzbeleg und entfernt keine Sperre.
