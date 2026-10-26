# C24-R: ContentStore-Lock im HTTP-Integrationstest

Untersuchung und Fixturekorrektur vom 26.10.2026, Branch
`feat/c24r-retrieval_completion`. Ausschließlich synthetische temporäre Testdaten.
Bestehende C24-R-Änderungen bleiben erhalten. C26 bleibt HOLD; kein Merge.

## Gesicherte Ursache und Nachweisgrenze

Die Loopback-Fixture verwechselt den Empfang des vollständigen HTTP-Bodys mit
dem Abschluss des serverseitigen Handlers. Zwischen beiden Ereignissen kann
der Hauptthread bereits `env.content.set_source_grants()` ausführen, während
der Serverthread den Leselock seiner Statusantwort noch berechtigt hält.
Die unabhängigen File Descriptors kollidieren auch innerhalb desselben Prozesses.
`LOCK_EX | LOCK_NB` liefert deshalb unmittelbar `Busy: content lock held`.

Der neue deterministische Test
`test_status_body_can_arrive_before_handler_releases_lock` belegt diese Abfolge
ohne Socket und ohne Worker:

1. Der echte HTTP-Handler läuft in einem zweiten Thread über Byte-Streams.
2. Ein Event hält ihn am Eintritt in `SearchReply.close()` an, nachdem sein
   vollständiger Statusbody geschrieben wurde. Die Probe prüft Content-Length
   gegen die tatsächlich vorhandenen Bytes und liest den Status als JSON.
3. Sowohl ein exklusiver Lockversuch direkt auf `.content-db.lock` als auch
   `set_source_grants()` schlagen im Hauptthread mit genau diesem `Busy` fehl.
4. Nach Freigabe des Events beendet der Handler sein reguläres Cleanup;
   derselbe ACL-Schreibzugriff gelingt mit unveränderter erwarteter Revision 0.
5. Die Jobliste ist leer. Ein Indexworker ist für diesen Konflikt nicht nötig.

Gesichert sind damit der Fixturefehler, der konkrete kollidierende Lock und
seine reguläre Freigabe. Die Zuordnung des ursprünglich außerhalb der Sandbox
beobachteten Fehlers zu genau diesem Threadinterleaving ist eine durch diesen
Nachweis gestützte Erklärung; der ursprüngliche externe Lauf wurde hier nicht
getraced. Ein natürlicher Socket-Roundtrip und der korrigierte Sockettest bleiben
wegen `EPERM` lokal nachzutesten. Die Threadprobe gilt ausdrücklich nicht als
gleichwertiger HTTP-Socketnachweis.

## Konkreter Codepfad und Lock-Lebenszyklus

| Schritt | Code | Lebensdauer |
|---|---|---|
| Status autorisieren und lesen | `index_jobs.status()`, insbesondere Zeilen 261–348 | Indexkatalog-SH-Lock, Maintenance-SH-Lock und Content-DB-SH-Lock umfassen das `yield answer` |
| Antwort übergeben | `IndexHTTP.request()`, `stack.enter_context(status(...))` und `SearchReply(..., stack=stack.pop_all())` | Der Kontext bleibt absichtlich über die Rückkehr aus `request()` hinaus aktiv |
| Body ausliefern | `handler_for().Handler.handle_request()`, `Content-Length`, danach `wfile.write(...)` | Der Client kann bereits nach Empfang dieser Byteanzahl zurückkehren |
| Antwort bereinigen | `handle_request()` im `finally`: `response.close()` | `SearchReply.close()` schließt den übernommenen ExitStack |
| Verbindung und Lock schließen | `ContentStore._connection()`, Zeilen 210–255; `_Artifacts.lock()`, Zeilen 109–128 | Transaktion committen/rollbacken, SQLite schließen, dann Lock-FD per `os.close(fd)` schließen |
| ACL schreiben | `ContentStore.set_source_grants()`, Zeilen 398 ff. | Neue Verbindung verlangt DB-EX-Lock mit `LOCK_NB`; vor dem vorherigen Cleanup entsteht `Busy` |

Die Lockdatei bleibt auf dem Dateisystem bestehen. Ihre Existenz zeigt keinen
gehaltenen Lock an; der Kernel-Lock hängt am geöffneten File Descriptor.
`ContentStore` hält im Leerlauf keine SQLiteverbindung: Konstruktor und Methoden
verwenden begrenzte Verbindungskontexte. Die Cleanup-Probe weist keinen Lock
über das Handlerende hinaus nach.

Auch der Workerpfad wurde geprüft: `adapter_worker.execute_scoped()` ruft
`index_jobs.run()` auf. Export und atomare Aktivierung in `ContentIndex.build()`
verwenden begrenzte Content-Verbindungskontexte; diese sind vor der Rückkehr
geschlossen. Der Guardian setzt den terminalen Jobstatus erst nach
`supervise()` und bestätigtem Payload-/Prozessgruppenende. Für einen vom
abgeschlossenen Worker zurückgelassenen Content-DB-Lock gibt es hier keinen
Nachweis. Die deterministische Reproduktion ohne Job grenzt diesen zudem als
notwendige Ursache aus.

Der direkte Handler-Test B kehrt erst nach `handle_request()` einschließlich
`response.close()` zurück. Im ursprünglichen Sockettest A fehlt diese
Synchronisation zwischen dem Client und seinem im selben Prozess betriebenen
Serverthread. Das erklärt den Unterschied trotz gemeinsamer `exercise()`.

## Korrektur und geänderte Dateien

- `tests/test_c24r_integration.py`: Der lokale `CompletionServer` setzt nach
  `HTTPServer.process_request()` ein Event, also nach Handler und
  Request-Cleanup. Jeder sequenzielle `exchange()` löscht das vorherige Event,
  führt den echten HTTP-Request aus und wartet begrenzt auf dieses Abschlussereignis,
  bevor `exercise()` direkt ACLs verändert. Zusätzlich Threadende prüfen.
  Neue Threadprobe und optionaler Ausgabestream im bestehenden Handler-Testhelfer.
- `docs/retrieval/c24r_content_lock_fix.md`: dieser Ursachen-/Übergabebericht.

Es gibt keine Produktionsänderung. Keine Sleeps oder Busy-Retries hinzugefügt;
die Event-Waits synchronisieren auf ein tatsächliches Lifecycleereignis und
schlagen bei ausbleibendem Abschluss fehl. `LOCK_NB`, ACL-Regeln, Quarantäne,
atomare Indexaktivierung und Sicherheitsgrenzen bleiben unverändert.
`pyproject.toml` und `uv.lock` werden per SHA-256 mit ihrem bereits lokal
geänderten Ausgangszustand verglichen. Der bestehende getrackte Diff wird
ebenfalls unverändert erhalten.

## Tests und Patchprüfung

Python 3.12.12, SQLite 3.50.4, Pytest 9.1.1, httpx 0.28.1,
Pydantic 2.13.4; vorhandene `.venv`, kein Sync/Download und keine Lockänderung.
Tatsächlicher Lauf aller vier angeforderten Dateien:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
UV_CACHE_DIR=/tmp/c24r-lock-investigation/uv-cache \
uv run --offline --no-sync python -m pytest \
  -q -o addopts= -p no:cacheprovider --tb=short \
  tests/test_c24r_integration.py tests/test_content_search_http.py \
  tests/test_content_http.py tests/test_content_index_jobs.py
```

| Datei | Passed | Failed (fachlich) | Blocked (Socket-EPERM) |
|---|---:|---:|---:|
| `tests/test_c24r_integration.py` | 4 | 0 | 1 |
| `tests/test_content_search_http.py` | 49 | 0 | 1 |
| `tests/test_content_http.py` | 0 | 0 | 43 |
| `tests/test_content_index_jobs.py` | 19 | 0 | 0 |
| `tests/test_content_store_concurrency.py` (Zusatzlauf) | 4 | 0 | 0 |
| `tests/test_content_store_store.py` (Zusatzlauf) | 34 | 0 | 0 |
| Summe unterschiedlicher Fälle | 110 | 0 | 45 |

Kein grüner Gesamtlauf: Der unveränderte Pytest-Rohstatus für die vier
angeforderten Dateien lautet **2 failed, 72 passed, 43 errors**, 190,94 s,
Exitcode 1. Sämtliche 45 Problemtracebacks wurden geprüft: ausschließlich
`PermissionError: [Errno 1] Operation not permitted` bei `socket.socket()`.
Die zwei Failed betreffen den C24-R-Loopbacktest und
`test_real_local_http_server_and_process_restart`; die 43 Errors entstehen im
Content-HTTP-Fixture vor dem eigentlichen Test. Diese Fälle wurden weder
übersprungen noch als bestanden gewertet. Der ursprüngliche Einzellauf A
scheiterte hier ebenfalls bereits an `socket()`, vor jeder Statusabfrage.

Der ergänzende Lauf mit denselben Umgebungsvariablen/Optionen und
`tests/test_content_store_concurrency.py tests/test_content_store_store.py`
ergab **38 passed**, 77,19 s. Die neue Threadprobe ist in den vier bestandenen
Integrationsfällen enthalten. Getrennte Entwicklungsläufe werden nicht addiert.
Die vollständige Repositorysuite wurde nicht ausgeführt.

Ruff check, Ruff format --check und `git diff --check` sind erfolgreich.
SHA-256-Prüfung von `pyproject.toml`/`uv.lock` und Bytevergleich des gesamten
bereits vorhandenen getrackten Diffs gegen die Ausgangssicherung erfolgreich.

Der gemeinsame Git-Speicher liegt laut `.git` unter
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant/.git/worktrees/Personal_Assistant-c24r`,
außerhalb der freigegebenen Schreibwurzeln. Deshalb kein Staging/Commit und
kein Schreibversuch in anderen Worktrees. Lieferung als inkrementeller Patch:

- `/tmp/c24r-lock-investigation/c24r-content-lock-fix.patch`
- `/tmp/c24r-lock-investigation/patch-verification.txt`
- `/tmp/c24r-lock-investigation/artifacts.sha256`
- Testprotokolle: `required-tests.log` und `store-tests.log` im selben Verzeichnis.

Patchbasis ist der zu Beginn vorgefundene **uncommittete C24-R-Stand**, nicht
`master` oder der nackte Branch-HEAD. Insbesondere existierte die dort noch
ungetrackte Integrationstestdatei bereits. Der Patch enthält ausschließlich
deren zusätzlichen Fix und diesen neuen Bericht. Prüfung in einer unabhängigen
temporären Dateikopie: `git apply --check --whitespace=error-all`, Anwendung,
Bytevergleich beider Ergebnisdateien, Reversecheck, Rückanwendung und exakte
Wiederherstellung der Ausgangsdatei. Im bereits korrigierten Worktree den Patch
nicht nochmals vorwärts anwenden.

## Exakte lokale Nachtests außerhalb der Socket-Sandbox

Aus der vorhandenen, passend provisionierten Projektumgebung, ohne Sync:

```bash
cd ~/0_Portfolio_Projekte/Personal_Assistant-c24r
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
uv run --no-sync python -m pytest \
  -x -vv -o addopts= -p no:cacheprovider \
  tests/test_c24r_integration.py::test_actual_loopback_job_to_search

PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
uv run --no-sync python -m pytest \
  -q -o addopts= -p no:cacheprovider \
  tests/test_c24r_integration.py \
  tests/test_content_search_http.py \
  tests/test_content_http.py \
  tests/test_content_index_jobs.py
```
