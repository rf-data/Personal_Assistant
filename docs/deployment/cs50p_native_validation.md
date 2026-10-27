# C26-CS50P-NATIVE-ADMISSION: Validierung und Übergabe

Gesamtstatus **HOLD** für Integration/Hostbetrieb; offline validierter Reviewkandidat.
Keine realen Downloads, produktiven Jobs, Hetzner-/Coolifyänderungen oder Deployment.
[Vertrag](cs50p_native_architecture.md), [Betriebsplan](cs50p_native_operator_guide.md).
Die maschinenlesbare finale Evidenz steht in cs50p_native_validation.v1.json.

## Phase A: tatsächlicher Stand

Die drei SHA-256-Manifeste der ursprünglichen Übergabe wurden vollständig geprüft:
checksums.sha256, candidate-files.sha256, source-tree.sha256. Basistar und vollständiger
19-Dateien-Patch gehören zur ursprünglichen INT-02-Basis
`6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d`.

Die alte Aussage „kein Featurecommit“ war inzwischen überholt: Der vorgesehene
persistente Feature-Worktree steht auf
`723a94cfd92a976fc8d85ba7d1ce568ac5db17f9`, Branch `feat/c26-cs50p-mvp`.
18 von 19 alten Kandidatdateien stimmen mit diesem Commit überein. README.md ist
bereits als lokale uncommittete Änderung vorhanden und stimmt bytegenau mit der
19. Originaldatei überein (SHA-256
`afb3982c7c222ff1bca4ae5c17069e20eb1a8def61d2a3c479e22fa3e022e37d`).
Es wurden weder diese Änderung noch der vorhandene Commit durch diesen Auftrag erstellt.

Featuredateien und gemeinsamer Git-Index liegen außerhalb der freigegebenen
Schreibpfade; effektiver Schreibzugriff ist false. Deshalb keine Übernahme,
kein neuer Commit, Push, PR oder Merge. Der neue Kandidat liegt ausschließlich im
persistent erhaltenen Export `artifacts/cs50p_native_admission/source/` des
Pilot-Worktrees. C24-R, DEP-01 und andere Worktrees wurden nicht geändert.

## Tests und Grenzen

Der finale native/Vertragslauf umfasst 167 erfolgreiche Tests, davon damals 22 neue native
Tests, 48 bisherige MVP-Tests sowie v2-Gate- und Controller-Vertragstests. Separate
C16-/v1-/Workflow-/INT-02-Regressionen sind im JSONbericht mit tatsächlichem Ergebnis
ausgewiesen. Überlappende Entwicklungsläufe werden nicht addiert. Frühere rote
Läufe samt JUnit bleiben im Export erhalten: Testvorbereitung, falscher
Receiptstatus, created-Cancelübergang, SQLite-Preflight-Metadaten sowie zwei
inzwischen korrigierte Serialisierungs-/Schemasnapshotabweichungen.

Der abschließende Runtime-Trennungslauf enthält 23 native Tests, die 48 MVP-Tests
und zwei gezielte Kompatibilitätstests. Er bestand mit **73 passed**. Details stehen im JSONbericht. Der normale CLI-/systemd-Start lehnt den offline-test-Scope grundsätzlich
ab; nur explizites --offline-test erlaubt synthetische Testausführung.

Die zusätzliche 136-Test-Regression endete mit 135 passed / 1 failed:
test_resume_after_interrupted_attempt_before_state_write scheiterte bereits beim
ersten Workflow an einer **geschlossenen Quarantäne**. Die persistierte Guardian-
Diagnose nennt sqlite_code=5 (SQLITE_BUSY), phase=begin. Derselbe Test bestand im
ersten breiten Lauf und anschließend isoliert (1 passed). Die Ursache dieser
intermittierenden SQLite-Konkurrenz ist nicht abschließend behoben. Kein Gate,
Timeout oder Quarantäneverhalten wurde für ein grünes Ergebnis abgeschwächt.
Die Diagnose und der rote Lauf bleiben erhalten. Das ist eine zusätzliche offene
Validierungsgrenze; es wird kein durchgehend grüner Gesamtlauf behauptet.

Die neuen Tests verwenden reale C16-Queue, CapacityExecutor, Guardian, Offlineadapter
und Workflowengine für Download -> Receipt-/Rohdatenintegrität -> Katalogversiegelung
-> kanonischen Review -> manuelle Freigabe -> Workerstart -> Status -> Parsing ->
hashgeprüfte Ergebnisse. Separat geprüft sind laufender Cancel mit Prozessende,
Replay, fehlender/ungültiger/abgelaufener/noch nicht gültiger Grant, geänderte
Configbytes/Settings/Limits/Inputs, falsche UID, fremder Katalog, zweiter Job,
Workerlockkonkurrenz, Crash nach Grantverbrauch, ausdrückliches Recovery und Resume,
unbekannte Lifecycle-Daten, Ergebnisbeschädigung, direkter Controller/Store/Executor/
Guardian ohne Authority, Gate-Downgrade, v2-/native-Mischung und Runtimeablehnung
synthetischen Ursprungs sowie Token-Testidentitäten.

Quellen sind ausschließlich synthetische lokale Daten mit Mock-HTTP-Transport.
Netzwerkzugriffe werden in Tests abgewiesen; der tatsächliche Adapter sperrt
Netzwerkzugriff zusätzlich selbst. Kapazitätsproben wurden auf große freie Reserve
simuliert; die Tests behaupten keinen realen 5-GiB-/Quota-Nachweis. Der Abbruchtest
startet die echte CLI in einem Kindprozess, simuliert darin nur freien Speicher und
beendet die tatsächlichen C16-Kinder über den vorgesehenen Cancelpfad.

Python 3.12.12. Testvenv unter /tmp/cs50p-native-test-venv nutzt ausschließlich
vorhandene lokale Pakete/Caches über eine eigene .pth-Datei. Ein Offlineversuch mit
uv scheiterte an Cache-/Auflösungsgrenzen; kein Netzwerkdownload wurde als Ersatz
ausgeführt. pydantic-settings und returns fehlen in dieser Testclosure; der getestete
Pfad lädt sie nicht. Kein positiver Beleg einer gefrorenen Runtimeinstallation.

Ruff check/format für alle geänderten Pythondateien erfolgreich. JSON-Schemas für
Grant/Enrollment veröffentlicht und gegen Modelle getestet, bestehender
Settings-Schemasnapshot aktualisiert. Leere native Felder werden in alten Settings
nicht serialisiert; bestehende v1-/v2-Digests und Gates bleiben überprüfbar.

systemd-analyze verify der neuen Unit mit ausschließlich auf /usr/bin/true ersetztem
ExecStart besteht. Originalprüfung nennt die hier fehlende /opt/cs50p/venv/bin/python.
Kein Nachweis von Hostlogin, SSH-/VPN-Policy, cgroups, Quotas, Netzisolation oder
vollständiger Installation. Das sind offene Betreiberabnahmen.

## Patchübernahme und Lebenszyklus

`native-admission.patch` ist der inkrementelle Patch gegen Commit 723a94c mit bereits
vorhandenem Original-README. Er berührt dieses README nicht. `complete-from-int02.patch`
enthält dagegen den vollständigen alten MVP einschließlich README plus native
Erweiterung gegen INT-02. Niemals beide nacheinander anwenden. Beide werden gegen
exakte Basen und anschließend anhand aller Kandidatbytes geprüft.

READ-ONLY im Exportpaket:

```sh
sha256sum -c checksums.sha256
sha256sum -c candidate-files.sha256
```

READ-ONLY im vorgesehenen Feature-Worktree:

```sh
cd /home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50p-mvp
git branch --show-current
git rev-parse HEAD
git status --short
sha256sum README.md
git apply --check /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-pilot/artifacts/cs50p_native_admission/native-admission.patch
```

Nur bei exakt dem oben dokumentierten Branch/HEAD und ausschließlich dem identischen
README als vorhandener Änderung fortfahren. Abweichung bedeutet HOLD und erneutes
Review; keine andere Arbeit überschreiben.

CHANGE: Das Paket enthält `apply-and-commit.sh` mit diesen Identitäts-/SHA-Prüfungen,
gewöhnlichem git apply, vollständiger Dateiprüfung und einer expliziten git add-Liste
(einschließlich des bereits vorhandenen README) sowie lokalem Commit. Vor Ausführung
Inhalt lesen. Keine force-Operation, kein Push, PR oder Merge im Skript.

```sh
CS50P_TEST_PYTHON=/tmp/cs50p-native-test-venv/bin/python bash /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-pilot/artifacts/cs50p_native_admission/apply-and-commit.sh
```

Die genannte isolierte Testvenv wurde lokal erhalten; sie ist keine Host-Runtime.
Vor Commit können Betreiber dieselben pytest-/Ruff-Befehle aus dem JSONbericht im
Feature-Worktree mit einer geeigneten Offline-Testvenv wiederholen. Danach regulären
Review-/PR-Prozess einhalten. Kein master-Merge dieses Auftrags; Dokumentintegration
in den tatsächlichen Defaultbranch master steht aus. Erst spätere verifizierte
Integration erfüllt die repositoryweite Anforderung an dauerhafte Dokumentation.

Es wurden keine Git-Branches oder Worktrees neu angelegt und keine entfernt.
Vorhandener Feature-Worktree/Branch, Pilot-Worktree/Branch, ursprünglicher MVP-Export
und neuer Kandidat bleiben erhalten, weil Review/Integration ausstehen und ihr
Entfernen Daten verlieren würde. Neue Testvenv und disposable Test-/Syntaxartefakte
unter /tmp wurden ebenfalls erhalten; sie sind keine Gitartifacts und keine
Runtimeinstallation. Es wird keine abgeschlossene Bereinigung behauptet.

## Offene Betreiberaktionen und Sicherheitsblocker

1. Prüfsummen/Patches reviewen, im erlaubten Feature-Worktree übernehmen, README
   sichern/committen, Offlinechecks wiederholen und erforderliche Reviews durchführen.
   Dokumente regulär in master integrieren; bis dahin Abschluss pending.
2. Gefrorene, hashgeprüfte Wheelclosure auf Zielarchitektur installieren/prüfen.
3. Reale Quellen-, Lizenz-, robots-, Verwendungs-/Aufbewahrungsfreigaben und
   konkreten Katalog liefern; keine Synthetic-/Dummy-Erklärungen übernehmen.
4. Reale Dienst-UID, VPN-/SSH-Schlüssel-/Hostkey-/sudo-Policy und ausschließlichen
   privaten Zugang abnehmen; kein Listener für diese Verarbeitung erforderlich.
5. Dateieigentum/-modi, persistente Datenpfade, freien Speicher, echte Diskquotas,
   CPU/RAM/Tasks/Timeout und Prozessgruppen-/Netzisolierung am Host abnehmen.
6. Intermittierende SQLite-BUSY-/Quarantäneursache reproduzieren und für die
   beabsichtigte Runtime klären; fail-closed-Verhalten unverändert erhalten.
7. Erst dann eigenen nativen Scope initialisieren und genau einen konkreten Job
   manuell reviewen/freigeben. Das Paket selbst enthält keine Runtimefreigabe.
