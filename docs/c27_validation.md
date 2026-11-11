# C27 – Implementierung und automatisierte Prüfung

24.10.2026. Isolierte C27-Arbeitsstände auf Backend `e502aa9` und UI `e4be7a2`.
Diese Lieferung ist ein lokaler benutzbarer MVP; keine Produktionsfreigabe.

**Aktueller Stand nach der Diskvergrößerung:** Git-/uv-/pytest-Smokes und alle
90 C27-/Rootpolicyfälle sowie weitere 308 Backendregressionsfälle erneut
bestanden (1 optionaler Backend-Skip); vollständige UI-Suite erneut
157 bestanden/25 opt-in Skips. Vorhandene Python-3.12-Umgebungen wurden ohne
Paketinstallation wiederverwendet. Die echte Loviscach-Mock-Demo funktioniert
wieder in CLI und Streamlit-AppTest einschließlich beider Downloads. Der neue
Nachweis steht unter „Ergänzung: erneute Prüfung nach Diskvergrößerung“ am Ende.
Die früheren RAM-Läufe und die zwischenzeitliche Blockade bleiben als historische
Nachweise getrennt erhalten.

## A. Implementierung

`src/lecture_summary/` enthält versionierte Summary-/Auswahl-/Provenienzmodelle,
begrenzte Source Collection, gemeinsamen Mock-/LLM-Service, Quality Gate,
isolierten JSON-Cache und Markdown-/vollständigen LaTeX-Export.
`scripts/lecture_summary.py` registriert ausdrücklich eine lokale Quelle,
inventarisiert read-only oder erzeugt Exporte. Bestehende Transkript-, Material-,
Knowledge-, ContentLocator-, Hash-, LLM-Budget- und Storagekomponenten werden
wiederverwendet. `tools_materials.storage` wird um registrierte Lese-/Schreibroots
erweitert; der globale C16-/C26-Schreibvertrag bleibt unverändert streng.

UI: vorhandener `app_admin.py`, Anmeldung und Rollen, neue lokale Summarizer-
Ansicht, abgesicherter Core-Adapter mit scalar/JSON-Schnittstelle. Kein zweiter
Streamlit-Server, öffentlicher Endpunkt oder produktiver Jobstart. Keine
Dependencies oder Lockdateien im Produkt geändert.

Details, Startanleitung, tatsächliche Inventur und der zehnteilige Vorschlag
zur späteren Storageharmonisierung: [C27-Anleitung](c27_lecture_summary.md).
Die Änderungen gehören ausschließlich in separate C27-Draft-PRs beider Repos.
Lieferung: [Backend-Draft #158](https://github.com/rf-data/Personal_Assistant/pull/158)
und [UI-Draft #21](https://github.com/rf-data/personal-assistant-ui/pull/21).

## B. Demonstration

Die tatsächlich vorhandene Loviscach-Lektion `mathe_1 / 01.01.1` wurde rein lokal
mit `mock-extractive-v1` verarbeitet. Eingang:

`loviscach/mathe_1/transcripts/01.01.1_drei_Arten_Mathematik.json`

- 25.028 Bytes, 102 Segmente, 5.112 Textzeichen.
- SHA256 `95f20e193b0f7ebe30d9171f785f070fb05eeb69f490bcb527d55985f640ea87`.
- Vorher-/Nachherhash identisch; kein Modellaufruf oder Upload.
- CLI erzeugte Markdown, vollständiges LaTeX und Summary-JSON in der privaten
  temporären Demo `/dev/shm/c27-loviscach-demo`.
- Auch der kanonische Streamlit-AppTest wählte diese echte Quelle aus,
  generierte die Mock-Zusammenfassung und prüfte beide Downloadbuttons.
- Ergebnisstatus `needs_review`; keine fachliche oder mathematische Abnahme.

Die privaten Exporte/Transkripttexte werden nicht eingecheckt. Die RAM-Demo ist
temporär; für den normalen Betrieb die Anleitung zur erneuten lokalen
Registrierung verwenden. Alle automatisierten Tests verwenden synthetische
Quellen. Das vorhandene synthetische Importbeispiel wird ausdrücklich so bezeichnet.

## C. Qualität und Nachweisgrenzen

Abschließende Läufe (überlappen; Zahlen nicht addieren):

| Lauf | Ergebnis |
|---|---|
| C27-Backendfälle | 56 eigenständige Fälle, einschließlich des abschließenden Abbruchtests bestanden |
| Finaler Fokus: C27, Rootpolicy und Material-E2E | 94 bestanden, keine Fehler/Skips |
| Zusätzlich exakte Backend-Lockpins: C27 und Rootpolicy einschließlich abschließendem Abbruchtest | 90 bestanden, keine Fehler/Skips |
| Erweiterte Backendregression: Lecture/Discovery/Course, Transcript, Material, C18, C26, Rootpolicy und C27 | 384 bestanden, 1 opt-in Skip; zunächst 3 fehlende PyMuPDF-Dependencyfälle, danach im finalen Fokuslauf bestanden |
| Vollständige UI-Suite einschließlich C27-AppTests | 182 Fälle ausgeführt: 157 bestanden, 25 vorhandene opt-in E2E-Skips |
| C27-Streamlit-Fälle | Alle 6 bestanden; sind in den 157 UI-Erfolgen enthalten |
| Reale Loviscach-Mock-Demo über CLI und Streamlit-AppTest | Bestanden, beide Exporte verfügbar, Eingang unverändert |
| Ruff check/format und Git diff check für geänderte Dateien | Bestanden |
| Optionaler realer LuaLaTeX-Kompilierungssmoke | Nach 30 Sekunden abgebrochen; keine erfolgreiche PDF-/Engineabnahme behauptet |

Der Backend-Skip stammt aus `test_cs50_course.py`: Betreiberoriginale für den
optionalen Realmateriallauf sind nicht ausdrücklich bereitgestellt. Historische
CS50-Pilotdaten wurden nicht dafür geöffnet. Die 25 UI-Skips benötigen separate
`C16_REPO/C16_PYTHON`- bzw. `REVIEW_BACKEND_REPO/REVIEW_BACKEND_PYTHON`-Konfiguration.
Sie sind keine als bestanden ausgegebenen produktiven Integrationsnachweise.

Prüfumfang umfasst Einzel-/Dreifachauswahl, Auswahlgrenzen, fehlende/ungültige
Quellen und IDs, widersprüchliche Metadaten, gemeinsame Materialien, Mock-LLM und
Mock-HTTP, ein begrenzter Aufruf/keine Retries, defekte/verweigerte/trunkierte
Modellantworten, Abbruch vor/nach Dispatch, Quellen-/Formelunsicherheit,
Cachehit/-Invalidierung/-Korruption, Sourceänderungen während Generierung,
Unicode/TeX-Escaping, sichere Downloadnamen und keine Eingangsänderungen.
Storagefälle prüfen unterschiedliche Roots/Storage-IDs mit identischen
Inhaltsidentitäten, Traversal, Symlinks, fehlende Mounts, read-only,
verschachtelte Mounts und den unveränderten C16-/C26-Schreibvertrag.
Die Inventur wird an einem ausdrücklich künstlichen Provider-/Kursverzeichnis
mit echten Dateien und separat fehlenden Metadatenreferenzen demonstriert.

Die erste breite UI-Prüfung erkannte den direkten Backendimport in einer
Admin-Komponente. Die lokale Bindung wurde in den authentifizierten Core-Adapter
verlagert; der vorhandene Architekturtest bleibt unverändert und besteht.
Ein früherer Backendlauf mit bloßem `PYTHONPATH` hatte 17 Guardianfehler, weil
bereinigte Kindprozesse keine Dependencies fanden. Das echte isolierte Venv
behebt den Testaufbau, ohne Guardian-/Produktionsregeln zu ändern.

### Testumgebung

Python 3.12.12; Streamlit 1.65.0 und alle UI-Abhängigkeiten exakt aus `uv.lock`.
Zusätzliche Backend-Testpakete ebenfalls aus dessen Lock mit SHA256-Wheelprüfung:
pytest 9.1.1, PyMuPDF 1.28.2, BeautifulSoup 4.15.0, soupsieve 2.9.2 u.a.
HTTPX 0.28.1, pydantic-settings 2.15.0. In der kombinierten UI-Umgebung wird
Pydantic 2.14.0/core 2.50.0 aus dem UI-Lock genutzt; der Backend-Lock pinnt
2.13.4/core 2.46.4. Beide erfüllen den Backend-Dependencyvertrag. Zusätzlich wurden
alle 56 C27-Fälle und die 34 Rootpolicyfälle mit den exakten Backendpins geprüft:
90 bestanden, keine Fehler/Skips. Es bleibt keine Pydantic-Pinabweichung in diesem
zusätzlichen Backendnachweis; die kombinierte UI-Prüfung verwendet deren eigene Pins.

`uv sync`/pip/Git und schreibende Testfixtures scheiterten lokal wiederholt mit
ENOSPC, obwohl `df` freie Bytes zeigte. Es wurden keine alten Dateien, Worktrees,
Venvs oder Daten bereinigt. Der sichere Testaufbau liegt deshalb ausschließlich
unter `/dev/shm/c27-*`: hashgeprüfte gelockte Wheels, echtes Venv und private
synthetische Fixtures. Es wurden keine schweren Systempakete installiert.
Der Compiler-Smoke verwendete die vorhandene Engine, `-no-shell-escape`,
Zeit-/Speicher-/Dateigrößenlimits und private RAM-Ausgabepfade. Das Produkt
kompiliert kein PDF und benötigt keinen TeX-Dienst.

Reproduzierbare Testauswahl im normal eingerichteten Backend:

```bash
uv run pytest tests/test_lecture_summary.py tests/test_lecture_summary_contract.py \
  tests/test_runtime_paths.py tests/test_cs50_material_e2e.py
```

Breiter Lauf zusätzlich: `test_cs50_material_contracts`, `test_cs50_material_mapping`,
`test_cs50_material_html`, `test_official_transcript_import`,
`test_transcript_unknown_time`, `test_cs50_workflows`, `test_c26_storage_preflight`,
`test_c26_copy_inventory`, `test_cs50_selection`, `test_c26_integrated_pipeline`,
`test_cs50_multiformat`, `test_cs50_lecture_adapter`, `test_cs50_course`,
`test_cs50_discovery` (jeweils `tests/<name>.py`).

Reale didaktische Modellsynthese, Inhaltsvollständigkeit und mathematische
Richtigkeit bleiben fachlich ungeprüft. Ein gültiges JSON, korrekt zitierte
Quellen-ID oder syntaktisch gültiges LaTeX ersetzt keinen inhaltlichen Beleg.
Der Mock ist bewusst eine Extraktdemo. Andere Legacy-JSON-Formate und alle
Nicht-CS50-Dateien wurden nicht pauschal fachlich oder strukturell abgenommen.
Tatsächlich verfügbare Kurse/Dateien und ihre Voraussetzungen stehen in der
Inventurtabelle der Anleitung; Metadatenverweise sind getrennt von vorhandenen
Dateien ausgewiesen.

## D. Nächste Schritte und Lifecycle

Vor einer späteren produktiven Integration fehlen insbesondere ein freigegebener
authentifizierter Summary-Service-/Jobvertrag, Source-/Course-ACLs, kontrollierte
Quellenregistrierung/Kopien, konkrete Serverroots/Mountidentitäten, Betriebs- und
Modellbudgets, Cancellation/Audit und die gesonderte C16-/C26-/Deploymentfreigabe.
Danach bieten sich visuelle Formelprüfung, weitere explizite Materialien,
hierarchische Verarbeitung großer Quellen, geprüfte didaktische Evaluation und
separat versioniertes Quellen-Enrichment an. Keine dieser Erweiterungen wurde
automatisch aktiviert.

Geschützte Drafts sind read-only geprüft: Backend #148/#149/#156/#157 und UI #20.
Abschließender API-Vergleich: alle fünf Head-SHAs, Beschreibungen und Draftzustände
stimmen mit der ersten C27-Inventur überein; sämtliche Drafts blieben unverändert.
Keine SSH-/Hetzner-/Coolifyaktion, keine Produktivqueue/-datenbank, kein Download,
kein externer Quellenbezug, kein Merge/Ready/Auto-Merge und keine Migration.

Aufgabenartefakte bleiben wegen offener Draftreviews erhalten: die beiden
`feat/c27-lecture-summarizer`-Branches und die C27-Arbeitsstände. Normale lokale
Git-Metadaten meldeten ENOSPC; reguläre Commits werden deshalb über die getrennten
`/dev/shm/c27-backend-git/.git` und `/dev/shm/c27-ui-git/.git` mit den C27-
Arbeitsverzeichnissen erstellt. Diese Metadaten sind temporär; Remote-Draftbranches
sichern die Commits dauerhaft. Bestehende Primärcheckouts und sämtliche fremden
Artefakte bleiben unverändert. Integration der Dokumentation in master/main
bleibt bis zu einem separat freigegebenen Merge ausdrücklich ausstehend.

## Ergänzung: Speicherstatus und begrenzte Fortsetzung

Die Betreibermeldung nennt Btrfs auf `/dev/vdc`, 32 GB, nach eigener Bereinigung
27 GB belegt / 4,9 GB verfügbar / 85 %. Browsercachebereinigung und Pruning von
zehn verwaisten Worktree-Registrierungen wurden vom Betreiber vorgenommen,
nicht durch C27. Der gemeldete Fehler beim Ersetzen von `/var/lib/dpkg/status`
und der `tzdata`-Status `reinstreq` sind Betreiberbeobachtungen. APT/dpkg wurden
in dieser Fortsetzung weder aufgerufen noch repariert. Die ENOSPC-Ursache bleibt
unbewiesen; es liegen keine belastbaren Quota-/Btrfs-Metadatennachweise vor.

Aktuelle eigene read-only Beobachtung in der Standard-Codex-Sandbox:
`df -hT /tmp /home/robfra/0_Portfolio_Projekte` bestätigt für beide Pfade Btrfs,
32G / 27G / 4,9G / 85 %. `findmnt -T /tmp` zeigt
`/dev/vdc[/lxd/storage-pools/default/containers/penguin/rootfs/tmp]`, Btrfs,
unter anderem `rw,nosuid,nodev,idmapped,discard,space_cache=v2`.
Das sind Mountinformationen, kein Quotanachweis oder Beweis fehlerfreier Writes.

### Damaliger Zustand und tatsächlich wiederholte Prüfungen

- Beide Remote-Drafts und ihre damaligen Heads waren vollständig vorhanden:
  Backend `0f4d8af400b9f6e755a5f58c38d8ec67b8eb978a`,
  UI `c055927f464a0e709c2d2d01869afb05fec85452`.
- Alle 23 veröffentlichten C27-Dateien wurden vor diesen reinen
  Dokumentationsänderungen über Git-Blob-SHAs bytegenau mit den lokalen Dateien
  verglichen: alle identisch. Kein unvollständiger C27-Produktcode festgestellt.
- `/dev/shm` ist inzwischen leer. Die früheren RAM-Git-Metadaten, Venvs,
  Roh-Testlogs und die frühere Demo sind nicht mehr vorhanden. Die Ursache ihres
  Wegfalls wurde nicht untersucht. Die gesicherten Remotecommits bleiben erhalten.
- Der lokale Git-Index steht deshalb weiterhin auf der jeweiligen ursprünglichen
  Basis; `M`/untracked in diesen Arbeitsverzeichnissen bedeuten hier nicht, dass
  die veröffentlichten C27-Dateien verloren oder nur lokal vorhanden wären.
  Kein Indexreset, keine neue große Arbeitskopie und keine Bereinigung durchgeführt.
- Mit bereits vorhandenen Paketen wurde ausschließlich
  `tests/test_lecture_summary_contract.py` erneut ausgeführt: **21 bestanden**,
  1,63 Sekunden. Python 3.12.12, Pydantic 2.14.1/core 2.50.1, HTTPX 0.28.1;
  diese verbliebene Umgebung ist ausdrücklich kein erneuter exakter Locknachweis.
  Bytecode-/pytest-Cache waren deaktiviert, `--capture=sys`, `-x` und ein neues
  kleines Fixtureverzeichnis unter `/tmp/c27-followup-contract-20261024-a` gesetzt.
- Die bereits verwendete echte Loviscach-Lektion wurde mit diesen vorhandenen
  Dependencies nochmals per Mock-CLI registriert und exportiert. Neue private
  Ausgabe: `/tmp/c27-followup-demo-20261024-a`; Markdown 47.512 Bytes,
  LaTeX 48.809 Bytes, Summary-JSON 153.409 Bytes. Status `needs_review`,
  102 Quellenblöcke; Eingangs-SHA256 unverändert wie oben. Keine Medien-/PDFkopien,
  kein Modellaufruf, kein Upload, keine neue Materialbeschaffung.
- Bei diesen kleinen neuen Schreib- und Testoperationen trat **kein neues ENOSPC**
  auf. Das ist keine Freigabe für große Git-/uv-/pip-Operationen.

**In dieser Zwischenphase nicht wiederholt / blockiert:** vollständige UI-/C18-/C26-/Material-
Regressionen, UI-Start und UI-Demo sowie erneuter Test mit exakt gelocktem Venv,
weil deren nachgewiesene RAM-Umgebung entfallen ist und kein Neuaufbau erfolgt.
Die früheren bestandenen Läufe bleiben historische Nachweise für den identischen
Code; ihre flüchtigen Rohlogs sind aktuell nicht erneut verfügbar. Optionale
E2E-Skips, Live-Modell-/Fachprüfung und der nicht bestandene optionale PDF-Smoke
bleiben wie oben ausgewiesen. Der alte Helfer `/tmp/c27-start-demo.sh` erkennt
das fehlende RAM-Setup und ist **kein aktuell nutzbarer UI-Schnellstart**.

### Historische ENOSPC-Operationen und Beleggrenzen

Diese Fehler stammen aus der ersten C27-Entwicklung, nicht aus einem neuen
Installationsversuch nach der Betreibermeldung:

| Operation | Betroffener Pfad / genaue Meldung | Ausführung und Zustand |
|---|---|---|
| `git worktree add` | Backend: `fatal: couldn't set 'refs/heads/feat/c27-lecture-summarizer'`; UI: `.git/config: No space left on device` | Standard-Codex-Sandbox; Backendversuch zusätzlich mit `require_escalated`. Keine geschützten Branches geändert; UI-Arbeitsdateien wurden angelegt |
| Isolierter `git clone --shared --no-checkout` | C27-`.git/config`: `No space left on device`; weiterer separater Versuch: `unable to move new alternates file into place: No space left on device` | Standard-Sandbox bzw. beim Alternatesversuch `require_escalated`; keine nachträgliche Bereinigung fremder Git-Daten |
| `uv sync --locked --no-dev` | Ziel `/tmp/c27-backend-venv`, Cache `/tmp/c27-uv-cache`; `error: No space left on device (os error 28)` ohne genaueren Fehlerpfad | Standard-Sandbox; nicht als erfolgreich eingerichtete Umgebung verwendet |
| Isolierte pip-Installation | `/tmp/c27-python-deps/lib/python3.12/site-packages/urllib3-2.8.0.dist-info/METADATA`; später `/tmp/c27-core-deps/.../pygments/formatters` und `.../annotated_types-0.8.0.dist-info/INSTALLER*.tmp` → `INSTALLER`: jeweils `Errno 28` | `require_escalated`; unvollständige Paket-/Installationsmetadaten blieben als solche erkannt, nicht als vollständiges Venv abgenommen |
| pytest-Fixtures | `/tmp/pytest-of-unknown/pytest-0/.../l1.txt`: `OSError: [Errno 28] No space left on device` | Codex-Exec mit `require_escalated`; synthetische Fixtures teilweise leer/unvollständig, Lauf fehlgeschlagen, keine Originalquelle geändert |
| Sandbox-Initialisierung | synthetische Bubblewrap-Mounttargets `/home/robfra/0_Portfolio_Projekte/.git` bzw. `/tmp/.agents`: `No space left on device (os error 28)` | Fehler vor dem Start des eigentlichen Befehls innerhalb der separaten Codex-Sandbox; Exit 101 |

Damals wurde `df -h` mit 32G / 29G / 3,1G / 91 % erfasst, jedoch nicht zu
jedem Fehler ein eigenes `df -hT` für den exakten Pfad. Diese fehlenden
Zeitpunktbelege werden nicht nachträglich als gemessen ausgegeben. Es gibt keinen
Beleg für eine konkrete Quota- oder Metadatenursache und keine nachträgliche
Diagnose allein aus den freien Bytes oder den Btrfs-Inodeangaben.

Für jede weitere ENOSPC-Operation gilt: betroffenen Vorgang abbrechen, Pfad,
Fehlermeldung, `df -hT`, Sandboxkontext und belegte Mount-/Quotainformationen
festhalten; Partialdateien/Indexzustand nennen und die betroffene Fortsetzung als
blockiert ausweisen. Keine stillen großen Installationswiederholungen und keine
eigenständige Systemreparatur. Produktivbetrieb und alle C16-/C26-Drafts bleiben
außerhalb der C27-Änderungen.

## Ergänzung: erneute Prüfung nach Diskvergrößerung

24.10.2026, nach der Betreibermeldung zur vergrößerten Crostini-Disk. Eigene
Messung vor dem Lauf: `/dev/vdc`, Btrfs, 34G gesamt / 28G belegt / 5,4G verfügbar,
84 %; später 5,2G verfügbar / 85 %. Dies sind eigene zeitpunktbezogene Messwerte,
keine Bestätigung einer bestimmten Btrfs-/Quotaursache. Alle neuen Schreib- und
Testoperationen liefen in der normalen Codex-Sandbox auf dem lokalen Btrfs unter
`/tmp`, nicht im früheren RAM-Ausweichsetup. Kein neues ENOSPC.

### Kleine Git-/uv-/pytest-Smokes

- Neues, kleines Repository `/tmp/c27-recovery-smoke-20261024`: `git init`,
  lokale Git-Konfiguration, zwei erfolgreiche Commits, `git mv`, atomarer Replace,
  `git fsck --no-reflogs` und abschließend sauberer Index. Keine vorhandenen
  Git-Daten oder Worktrees verändert oder gelöscht.
- uv 0.9.15 erkannte das vorhandene CPython 3.12.12 und erzeugte mit
  `uv venv --offline --python <vorhandener Interpreter>` ein kleines neues Venv.
  `uv run --offline --no-project --python <vorhandenes Test-Venv> python -B -m
  pytest ...` bestand den synthetischen Schreib-/Replace-Smoke: **1 bestanden**.
  Keine Dependencyinstallation oder große Synchronisation wurde ausgeführt.
- Der erste uv-Interpreterlistenaufruf scheiterte beim Öffnen von
  `/home/robfra/.cache/uv/sdists-v9/.git` mit `Read-only file system (os error 30)`.
  Das ist die Sandbox-Schreibgrenze des Standardcaches. Mit dem neuen expliziten
  `UV_CACHE_DIR=/tmp/c27-recovery-uv-cache` liefen die Prüfungen erfolgreich;
  dies war kein erneutes ENOSPC.

### Tatsächlich erneut ausgeführte C27-/UI-Prüfungen

| Lauf | Neues Ergebnis |
|---|---|
| C27-Service-/Export-/Storagefälle und Vertragsfälle | 56 bestanden |
| Bestehende `test_runtime_paths.py` | 34 bestanden; gemeinsam mit C27 **90 bestanden in 2,32 s** |
| Zusätzliche Lecture-/Material-/C18-/C26-Regression, 15 Testdateien | **308 bestanden, 1 opt-in Skip**, 323,47 s; zusammen mit dem disjunkten C27-/Rootlauf **398 bestanden, 1 Skip** |
| Vollständige UI-Suite `unittest discover -s tests -q` | **182 ausgeführt: 157 bestanden, 25 opt-in Skips**, 63,236 s; alle 6 C27-AppTests enthalten |
| Echte Loviscach-CLI mit Mock und unveränderter Quelle | Bestanden, Markdown/LaTeX/JSON erneut geschrieben |
| Echte Loviscach-Lektion im kanonischen Streamlit-AppTest | Bestanden, beide Downloadbuttons, keine Jobaktion und kein Netzwerk |
| Git-Diffprüfung und Syntaxprüfung des temporären Starthelfers | Bestanden |

Backendtests verwenden unverändert das vorhandene
`Personal_Assistant-c26b6-planning-results/test-env/bin/python`: Python 3.12.12,
pytest 9.1.1, Pydantic 2.14.1/core 2.50.1, HTTPX 0.28.1. Das erfüllt den
Backend-Dependencyvertrag, ist aber **kein neuer Nachweis mit exakten Backend-
Lockpins**. Die frühere exakte Prüfung mit 2.13.4/core 2.46.4 bleibt historisch.
Keine Pakete in dieser fremden Umgebung ergänzt oder geändert.

UI/CLI/Demo verwenden unverändert das vorhandene
`personal-assistant-ui-c26b/.venv/bin/python`: Python 3.12.12, Streamlit 1.65.0,
Pydantic 2.14.0/core 2.50.0, pydantic-settings 2.15.0. Alle 52 installierten
Lockpakete wurden mit `uv.lock` verglichen: keine Versionsabweichung. Die virtuelle
Projektwurzel ist kein installiertes Paket; das Python-Paket `tzdata` ist laut
Lock nur für Windows/Emscripten erforderlich und fehlt unter Linux erwartbar.
Dies ist keine Aussage über den separat vom Betreiber reparierten dpkg-Zustand.
Es wurde keine vorhandene C26-Umgebung umgebaut.

Der zusätzliche Lauf umfasst `test_cs50_material_contracts`,
`test_cs50_material_mapping`, `test_cs50_material_html`,
`test_official_transcript_import`, `test_transcript_unknown_time`,
`test_cs50_workflows`, `test_c26_storage_preflight`, `test_c26_copy_inventory`,
`test_cs50_selection`, `test_c26_integrated_pipeline`, `test_cs50_multiformat`,
`test_cs50_lecture_adapter`, `test_cs50_course`, `test_cs50_discovery` und
`test_cs50_material_e2e`. Der Skip ist weiterhin der ausdrücklich opt-in
Originalmaterialtest in `test_cs50_course`; keine Originalfreigabe ergänzt.

Testfixtures liegen klein und isoliert unter
`/tmp/c27-recovery-smoke-20261024`; bei direkten Aufrufen sind Bytecode und pytest-Cache deaktiviert,
optionale pytest-Plugins nicht automatisch geladen. Keine produktiven Dienste
gestartet oder historischen CS50-Pilotdaten geöffnet. Die UI-Skips benötigen
weiterhin gesonderte C16-/Review-Backendkonfiguration und sind nicht bestanden.

### Erneute reale Demo und begrenzte Inventur

Die oben dokumentierte echte Loviscach-Datei wurde ausdrücklich erneut registriert
unter `/tmp/c27-recovery-demo-20261024/summary.json`. Markdown 47.512 Bytes,
LaTeX 48.809 Bytes und JSON 153.409 Bytes liegen in dessen `exports/`.
Summary-ID und Eingangs-SHA256 stimmen mit der früheren Demo überein; Vorher- und
Nachherhash des Transkripts identisch. Status bleibt `needs_review`.

Auf diesem Rechner startet
`bash /tmp/c27-recovery-start-ui-20261024.sh` die bestehende Admin-App auf
Loopback mit Operator-Demoanmeldung und `JOB_BACKEND=disabled`. Der Helfer prüft
Interpreter und Konfiguration; er installiert nichts. Er verwendet die oben
genannte vorhandene UI-Umgebung und beide C27-Checkouts. Helfer, Konfiguration und
Exporte sind temporär und kein Bestandteil der Repositorylieferung. Eine neue
HTTP-Serversitzung wurde hierfür nicht gestartet; der funktionale Nachweis
erfolgte über den echten Streamlit-AppTest. Keine Browserinstallation nötig.

Die erneute Inventur am echten Google-Drive-Mount lief read-only mit
`--max-entries 4000`: **3.920 tatsächlich vorhandene Dateien, 4.000 besuchte
Einträge, `truncated=true`, 4 übersprungene Einträge**. Der private JSON-Bericht
liegt unter `/tmp/c27-recovery-smoke-20261024/inventory.json` (1.696.551 Bytes).
Dies ist keine vollständige Inventur; nicht besuchte Metadatenreferenzen bleiben
unverifiziert. Keine Medien/PDFs geöffnet, kopiert oder verschoben.

Der erfasste Teil enthält bei Loviscach `mathe_1` 607 Transkript-JSON,
538 Untertitel-VTT, 28 PDF-Dokumente und 578 Knowledge-JSON; außerdem u.a.
`info_1`, `info_2_c#` und LAKBB-Kurse mit Transkripten und teils geparsten Skripten.
Verzeichniskandidaten ohne bestätigte Metadatenzuordnung werden weiterhin nicht
als gesicherte Course-/Lectureidentitäten ausgegeben. Die ältere detaillierte
Verfügbarkeitstabelle und der Storage-/Migrationsvorschlag stehen in der Anleitung.

### Verbleibende Nachweisgrenzen

Die zuvor fehlende UI-/Mock-Demoumgebung blockiert diese Prüfungen nicht mehr.
Ein neuer exakter Backend-Locklauf, optionale C16-/Review-E2E-Tests,
Live-Modellgenerierung und fachliche/formelbezogene Abnahme wurden nicht
ausgeführt. Der optionale PDF-/LuaLaTeX-Smoke wurde nicht wiederholt; vollständige
`.tex`-Exporte sind geprüft. Keine APT-/dpkg-Reparatur, Bereinigung, großen
Installationen, SSH-Verbindung, Produktivänderung, Migration, Merge oder Deployment.
Die eigenen Branches/Arbeitsstände bleiben wegen der ungemergten Draft-PRs
erhalten; Dokumentation ist dort reviewbar und noch nicht in master/main integriert.

## Ergänzung: Vorbereitung der manuellen Abnahme

24.10.2026, nach dem erfolgreichen Recovery-Lauf. Keine erneute vollständige
Regression. Änderungen ausschließlich für die lokale C27-Abnahme:

- Versionierter UI-Starthelfer `scripts/lecture_summary_local.py`, vorhandene
  Admin-App auf Loopback, explizite lokale Anmeldung/Operatorrolle,
  `JOB_BACKEND=disabled`, Prüfmodus ohne Serverstart, keine Installation.
- Expliziter Backend-Katalogaufbau `scripts/lecture_summary_acceptance.py`,
  Wiederverwendung der bisherigen Registrierung, Storagegrenze und Modelle.
  Privater persistenter Workspace statt notwendiger `/tmp`-Helfer.
- Request-Payload aus dem bisherigen Provider unverändert extrahiert, damit
  die Offline-Budgetprüfung exakt denselben Request prüft. `offline_only` am
  bestehenden Loader verweigert Live-Konfiguration vor HTTP-Client/Keyzugriff.
- [Bedienungs-/Abnahmeanleitung](c27_manual_acceptance.md), drei belegte Fälle
  mit Segmentstellen, Fingerprints, Prüfformeln und fachlicher Checkliste;
  [separater Live-Testvorschlag](c27_live_test_proposal.md), nicht ausgeführt.

Gezielt tatsächlich ausgeführt:

| Prüfung | Ergebnis |
|---|---|
| Neue Katalog-/Preflightfälle plus bestehende C27-Service-/Vertragsfälle | **63 bestanden**, 3,57 s (7 neu + 56 bestehend) |
| Neue Launcherfälle plus bestehende C27-Streamlit-Fälle | **13 bestanden**, 6,464 s (7 neu + 6 bestehend) |
| Versionierter Launcher `--check` am echten privaten Katalog | Bestanden, kein Server/Modellaufruf |
| Tatsächlicher Start/Health/Stopp der bestehenden Streamlit-App | Bestanden auf `127.0.0.1:8501`, HTTP 200/`ok`, nur eigener Prozess beendet |
| Alle drei tatsächlichen Loviscach-Auswahlen mit Mock, MD/TeX/JSON | Bestanden; alle vier Eingangs-SHA256 unverändert |
| Offline-Modellbudget am tatsächlichen vollständigen Request | Fall A 15.396/passt; B 30.929 und C 47.186/Abbruch vor HTTP bei Limit 30.000 |
| Python-Syntax, Diffcheck und Dokumentations-/Katalogfingerprints | Bestanden |

Der erste Socketversuch scheiterte in der normalen Codex-Sandbox bereits bei
`socket.socket()` mit `PermissionError: [Errno 1] Operation not permitted`.
Für den anschließenden begrenzten Loopback-Smoke wurde `require_escalated`
verwendet. Es wurde kein fremder Server beendet, kein öffentlicher Listener und
kein kostenpflichtiger Request gestartet. Der geprüfte eigene Server ist wieder
gestoppt. Funktionale UI-Prüfung erfolgt zusätzlich über die sechs AppTests.

Die drei echten Mock-Demos liegen unter
`/home/robfra/0_Portfolio_Projekte/c27-local-mvp/mock-export-{text,formulas,group}`;
der private Cache und die Konfiguration liegen im gleichen Workspace.
Ein kleiner zuvor vorbereiteter Zwischenkatalog `c27-local-acceptance` bleibt
unverändert erhalten; benötigt wird ausschließlich `c27-local-mvp`. Keine
Bereinigung alter Worktrees, Projektdateien, Venvs oder Hilfsartefakte.

Die Eingangsabschätzung von Fall A verwendet die kürzere vorhandene Fortsetzung
01.01.2; der alte 01.01.1-Text überschritt das Modellbudget. Die Formel- und
Gruppenfälle sind nur für Offline-/Bedienungs-/Provenienztests freigelegt;
ihre vollständige Live-Synthese bleibt unter den unveränderten Grenzen blockiert.
Das wird nicht als bestandener fachlicher Test ausgegeben. Das einzelne vorhandene
Vektorrechnungs-PDF wurde begrenzt read-only geprüft: Lückentext, kein vollständiger
Formelbeleg. Es wurde nicht als zusätzliche Summaryquelle registriert oder kopiert.

Keine neue Dependency, kein Live-LLM-Aufruf, keine API-Keyabfrage, kein Upload,
kein neues ENOSPC, keine Änderung an C16-/C26-Produktion, keine Migration,
keine Merges/Ready-Umstellung/Deployments. Die früheren 398 Backend-/157 UI-Erfolge
sind der vorherige vollständige Recovery-Nachweis und wurden hier nicht als
erneut ausgeführte Vollregression ausgegeben. Branches/Arbeitsstände bleiben für
die ungemergten Draft-PRs erhalten.

## C27-B Legacy Compatibility

24.10.2026, Ausgangspunkt Backend-Draft `4fedf844`, isolierter neuer Worktree
`Personal_Assistant-c27b`, Branch `feat/c27b-legacy-catalog`. Vollständiger
[Code-/Inventur-/Adapterbericht und GO-/NO-GO](c27b_legacy_catalog.md).
UI #21 unverändert `bb5742cc`; beide PRs bleiben Drafts. Keine Merges oder Deployment-
und Produktionsänderungen. Dokumentation wartet im Draft auf gesondertes Review;
keine Integration in den Defaultbranch behauptet. Arbeitsstände bleiben erhalten.

Tatsächlich ausgeführte zielgerichtete Läufe, keine Summierung über Wiederholungen:

| Prüfung | Ergebnis / Geltungsbereich |
|---|---|
| Erster neuer Adapterlauf | 30 bestanden / 1 fehlgeschlagen; Test deckte eine Variable auf, die den Evidence-Chunk-Fingerprint mit einem nativen Knowledge-Dict überschrieb. Korrigiert, danach alle betroffenen Tests erfolgreich |
| C27/Storage nach Korrektur | 128 bestanden: 31 damalige neue Legacy-Fälle, 63 bestehende C27-Fälle, 34 `test_runtime_paths.py`; 0 Skips |
| C27 nach Erweiterung der Knowledge-/Exportprovenienz | 97 bestanden: 34 damalige neue Legacy-Fälle plus dieselben 63 C27-Fälle; 0 Skips |
| Abschließender Adapterstand | 38 bestanden, 0 Skips; Schemaerkennung, native/fehlende/widersprüchliche IDs, doppelte Keys/Chunks/Items, Parent-Provenienz/Segmente/Zeiten, Kopien/Rootunabhängigkeit, sichere Pfade, Links/Mounts, fehlende Roots, PermissionError, simuliertes ENOSPC ohne Retry, CLI-Roundtrip und unveränderte Quellen |
| Aktueller master `29114d2e` + C27/C27-B | 125 bestanden / 1 optionaler Skip: 38 Legacy-Fälle, 63 C27-Fälle, 25 HTML-/Hierarchie-/Referenzfälle aus #149. Skip: `test_optional_original_python_notes_read_only`, Original-Notes-Artefakte nicht bereitgestellt. Kein Download als Ersatz |
| Finale Adapter-Metadaten im gleichen master-Snapshot | Abschließende 38 Legacy-Fälle erneut bestanden; keine Wiederholung der ganzen Regression |
| UI + dauerhafter Starthelfer | 13 bestanden, zusätzlich 6 Subtests bestanden; vorhandene AppTests/Auth-/Operator-/kein-Job-/Download-/Fehler-Guards und Launcherfälle |
| Echter Kandidat, finaler Adapter | Fünf vorhandene Loviscach-JSONs akzeptiert, keine Review-Ablehnung; Kataloginhalt identisch zum vorbereiteten Kandidaten |
| Offline-UI-Startvorprüfung | Versionierter Launcher mit `--backend Personal_Assistant-c27b --config .../c27b-legacy-candidate-20261024/summary.json --check`: OFFLINE-DEMO / Mock; kein Server/Modellaufruf |
| Reale End-to-End-Demo | Vorhandenes 01.01.2-Transcript plus TranscriptKnowledgeDocument: 43 Evidenceblöcke, davon 18 Knowledge; MD/TeX/JSON, `needs_review`; fünf Original-SHA vor/nach Verarbeitung unverändert |
| Offline-Requestbudget des neuen Kandidaten | Text mit Knowledge 21.043/passt; Formeln 30.929 und Gruppe 47.186/Abbruch vor HTTP bei Limit 30.000. Nur Request-Aufbau/RequestBudget, keine Clienterstellung oder Übertragung |
| Read-only-Gesamtinventur | Zwei abgeschlossene Läufe: je 9.348 Einträge / 8.779 Dateien; final 4.806 Metadatenreferenzen, 2.861 vorhandene Dateiverweise, 93 fehlende, 1.852 ohne lokalen Verweis. 45 Metadaten-JSONs gelesen, 5 >2 MiB begrenzt nicht gelesen. Dateiabdeckung vollständig, Metadateninterpretation/Identitäten ausdrücklich nicht vollständig |

Die Quelle des aktuellen-master-Checks ist ein eigener Quellcodesnapshot unter
`/tmp/c27b-master-compat-20261024` aus lokal vorhandenen Git-Objekten `29114d2e` plus
den C27-/C27-B-Dateien. Kein Git-Merge, keine Änderung fremder Worktrees oder
Produktivdaten. GitHub-master wurde zusätzlich read-only mit diesem SHA abgeglichen.
Er enthält bereits #156 und #149; C27-B hängt nicht von einem laufenden C16-/C26-
Worker ab und ändert dessen Verträge nicht.

Backendbefehle (vorhandenes Python 3.12.12, pytest 9.1.1):

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=.
/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python -B -m pytest \
  -q -p no:cacheprovider tests/test_lecture_summary_legacy.py \
  tests/test_lecture_summary.py tests/test_lecture_summary_contract.py \
  tests/test_lecture_summary_acceptance.py tests/test_runtime_paths.py
```

Die Tabelle benennt die tatsächlich gewachsenen Testsammlungen während der
Entwicklung; der obige Sammelbefehl enthält am Ende 135 Fälle, die nicht nochmals
als ein zusätzlicher Gesamtbestand ausgeführt wurden. Der master-Check ergänzte
`tests/test_cs50_material_html.py` und `tests/test_cs50_material_html_semantics.py`
und ließ die unveränderten Runtime-Path-Fälle weg. Letzter Adapterlauf nur das neue
Testmodul, nach Änderungen an dessen Guards und CLI-Roundtrip.

Backend verwendet Pydantic 2.14.1/core 2.50.1 statt der im Lockfile festgelegten
2.13.4/core 2.46.4; keine heimliche Neuinstallation. UI-Python aus
`personal-assistant-ui-c26b/.venv` verwendet Streamlit 1.65.0, Pydantic 2.14.0/core
2.50.0. Dieses UI-Venv hat kein pytest: direkter Versuch `-m pytest` scheiterte
entsprechend. Für den erfolgreichen UI-Lauf wurde pytest über `site.addsitedir`
aus dem vorhandenen Backend-Test-Venv ergänzt, ohne Installation oder Änderung
der bestehenden Umgebungen; UI-Pakete behalten Suchpfadpriorität:

```python
import site
site.addsitedir('/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/lib/python3.12/site-packages')
import pytest
raise SystemExit(pytest.main([
    '-q', '-p', 'no:cacheprovider',
    'tests/test_lecture_summary_ui.py', 'tests/test_lecture_summary_local_start.py',
    '--basetemp=/tmp/c27b-ui-validation',
]))
```

Ausführung im UI-Checkout, UI-Python, `PYTHONPATH=<C27-B-Backend>:.`, Plugin-Autoload
und Bytecode ausgeschaltet. Die obigen bereits verwendeten Temp-Verzeichnisse
werden nicht zur Bereinigung bestehender Daten erneut beansprucht.

Zusätzlich Python-AST/Syntax, Diff-/Whitespace-/EOF-/Dateigrößenprüfung und lokale
Dokumentlinks. Keine neuen Dependencies, Browser oder schweren Testartefakte.
Ruff/Pre-commit nicht installiert; vorhandener Git-Hook verweist auf ein nicht
verfügbares altes Projekt-Venv. Kein bestandener Hooklauf behauptet, Veröffentlichung
über einen normalen einzelnen Git-Daten-Commit ohne Merge/Force-Update. Automatische
mathematische Prüfung, Live-LLM, PDF-Kompilation, vollständige UI-Browserabnahme,
Full-Lock-Neuinstallation und produktive Integration bleiben ausdrücklich offen.

Kein erneutes ENOSPC bei Worktree-, Quellcode-, Test- oder Berichtsschreibvorgängen.
`df -hT` im Workspace während C27-B: Btrfs `/dev/vdc`, 34 GB gesamt, etwa 5 GB frei.
Keine APT-/dpkg-Reparatur, keine Cache-/Worktree-/Datenlöschung durchgeführt.

## C27-C Hierarchische Verarbeitung

24.10.2026, Basis Backend-Draft `117aa841` und UI-Draft `bb5742cc`.
[Architektur, Grenzen, Kosten, Startbefehle und fachliche Risiken](c27c_hierarchical_summary.md).
Separate eigene Worktrees `Personal_Assistant-c27c` und `personal-assistant-ui-c27c`,
Branches `feat/c27c-hierarchical-summary` / `feat/c27c-hierarchy-status`.
Die Änderungen werden den bestehenden Drafts #158/#21 hinzugefügt. Keine Merges,
Ready-Umstellung, Deployments oder Produktivänderungen. Dokumente und Arbeitsstände
bleiben bis zum gesonderten Review/Merge im Draft; keine Defaultbranch-Integration behauptet.

| Tatsächlich ausgeführte Prüfung | Ergebnis |
|---|---|
| Neue kontrollierte Backendfälle, Abschlussstand | 39 bestanden, 0 Skips, 29,14 s; Netzwerk gesperrt, HTTP ausschließlich MockTransport |
| Entwicklungslauf neue/bestehende C27-/Legacy-/Runtime-Path-Fälle | 170 bestanden, 1 fehlgeschlagen bei 171 Fällen. Der neue 160-Block-Test erwartete fälschlich nur zwei finale Mock-Zitate; bei zwei Abschnitten sind es vier. Erwartung auf vollständige Verarbeitung und explizite Abschnitts-/Zitierabdeckung korrigiert; neue Fälle danach vollständig bestanden |
| Aktueller master `e6827520` plus C27/C27-B/C27-C | 164 bestanden, 1 optionaler Skip, 40,62 s: neue 39 Hierarchiefälle, bestehende 63 C27-Fälle, 38 C27-B-Fälle und 25 HTML-/Referenz-/Hierarchiefälle. Skip: nicht bereitgestellte optionale Original-Python-Notes, kein Ersatzdownload |
| UI / versionierter Starthelfer | 16 bestanden, zusätzlich 6 Subtests, 27,11 s; darin drei neue Fälle für sichtbaren Plan/Downloads, Budgetablehnung und unvollständige Läufe; Auth-/Operator-/kein-Job-Guards weiterhin geprüft |
| UI nach finaler Cache-Envelope-Ergänzung | Nur die drei betroffenen Hierarchiefälle erneut bestanden; sechs andere AppTests abgewählt, keine Vollregression |
| Versionierter lokaler UI-Helfer `--check` | Neue hierarchische Mock-Konfiguration erfolgreich geladen, kein Server und kein Modellaufruf |
| Reale Offline-Demo | Alle drei vorhandenen Loviscach-Fälle in einfachem und hierarchischem Mock-Modus, je MD/TeX/JSON. Hierarchie: 25/90/145 Originalblöcke verarbeitet, 2/2/3 Aufrufe, alle `needs_review`; vier Quell-SHA unverändert, 0 bezahlte API-Aufrufe |
| Reproduzierbarer Setup-/Demo-/Cachetest | Teil der neuen 39 Fälle: synthetische explizite Lecture-Dateien, drei Fälle, sechs TeX-Exporte, Wiederholung ohne neue Providerdispatches und ohne HTTP-Clienterstellung; keine Überschreibung vorhandener Workspaces |

Die master-Kompatibilität wurde in einem eigenen kleinen Quellcodesnapshot unter
`/tmp/c27c-master-compat-20261024` geprüft, nicht durch einen Git-Merge. Während
C27-C wurde master von `29114d2e` auf `e6827520` weitergeführt: ausschließlich
extern gemergte Auditdokumentation aus #159, keine neuen Produktivcodeänderungen.
Der Snapshot enthält den tatsächlichen neuen master plus die C27-Dateien.
Vorhandene fremde Worktrees wurden nicht verändert. Die frühere komplette
398-/157-Test-Recovery-Regression wurde nicht wiederholt.

Neue Fälle umfassen zusätzlich: maximal 160 Blöcke ohne Eingangssampling,
unbekannte Originalzeitstempel ohne zeitbasiertes Chunking, deterministic ordering,
unbekannte Aliase/erfundene Belege, fehlende oder veränderte Quellen,
unveränderte technische Obergrenzen, Kostenannahmen vor Live-Dispatch,
überdimensionierte Zwischenstände/Reduce-Requests, Formula-Unsicherheit und
Konfliktvarianten in MD/TeX, keine automatische Formelverifizierung,
Cacheinvalidierung/Modell-/Promptmetadaten, exklusives Reservieren bei Konkurrenz,
Abbruch zwischen validierten Stufen und gesperrter Retry nach unklarem Teilfehler.

Backend mit vorhandener Umgebung:

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=.
/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python -B -m pytest \
  -q -p no:cacheprovider tests/test_lecture_summary_hierarchy.py
```

Für den master-Lauf wurden im Snapshot zusätzlich
`test_lecture_summary.py`, `test_lecture_summary_contract.py`,
`test_lecture_summary_acceptance.py`, `test_lecture_summary_legacy.py`,
`test_cs50_material_html.py` und `test_cs50_material_html_semantics.py` ausgeführt.
`test_runtime_paths.py` bestand bereits im oben benannten Entwicklungslauf.
Backend: Python 3.12.12, pytest 9.1.1, Pydantic 2.14.1/core 2.50.1; weiterhin
abweichend vom Backend-Lock 2.13.4/core 2.46.4. Kein Neuaufbau der Umgebung.

UI mit Python aus `personal-assistant-ui-c26b/.venv`, Streamlit 1.65.0,
Pydantic 2.14.0/core 2.50.0; pytest weiterhin nur über `site.addsitedir` aus dem
vorhandenen Backend-Test-Venv ergänzt (Suchpfad nach UI-Paketen), keine Installation.
Ausführung analog zum C27-B-Befehl mit C27-C-PYTHONPATH, AppTest und Starthelfer.

Zusätzlich wurde nun ein bereits vorhandener Ruff-0.16.0-Formatter im
Pre-commit-Cache entdeckt und verwendet: Formatierung und Ruff-Checks aller
geänderten Pythondateien in beiden Repositories erfolgreich, keine Installation.
Das ist ein neuer C27-C-Nachweis und ändert die historische C27-B-Aussage nicht.
Der vollständige Pre-commit-Manager/Git-Hooklauf wurde nicht als bestanden behauptet.
AST, Whitespace/EOF, Dateigrößen und lokale Dokumentlinks werden ebenfalls geprüft;
veröffentlichte Git-Trees werden mit den lokal gestagten Trees verglichen.

Finale private Demo: `c27c-local-demo-final-20261024/comparison.json`,
Konfiguration/Cache: `c27c-local-mvp-20261024`, jeweils unter
`/home/robfra/0_Portfolio_Projekte`. Frühere eigene Probe-/Demoartefakte bleiben
erhalten. Gegenüber dem einfachen Requestbudget 15.396 / 30.929 / 47.186 liegen
die hierarchischen konservativen **Gesamt**reservierungen beim inerten Modelllabel
bei 32.005 / 42.988 / 62.279, mit 18.000 reservierten Reduce-Inputeinheiten.
Diese Einheiten sind keine gemessene Usage oder verifizierte aktuelle Preisauskunft.
Tatsächliche Kosten 0; keine API-Keyabfrage für die Mock-Demos, keine Übertragung.

Fachliche Risiken bleiben offen: repräsentative Inhaltsauswahl, Herleitungen,
Notation, Quelleninterpretation und visuelle Mathematikprüfung. Die reale Mock-Demo
erfindet keine Formeln; Formelgates wurden mit ausdrücklich synthetischen Fällen
getestet. TeX wurde gerendert, nicht mit einer Engine kompiliert. Keine manuelle
fachliche Abnahme, keine neue Browserinstallation oder vollständige Browserabnahme,
kein Live-LLM, keine Produktions-/DB-/Queue-/Serveränderungen, keine Migration.
Storage-/Collection-Sicherheitslimits unverändert. Kein ENOSPC; Btrfs meldete
zuletzt rund 4,9 GB frei. Keine Bereinigung bestehender Dateien/Worktrees/Venvs.

## C27 nach erster funktionaler Betreiberabnahme

### Betreiberbericht, 24.10.2026

Der Betreiber meldet die manuelle funktionale Abnahme von Loviscach `mathe_1 /
01.01.2` als **8/8 erfolgreich**. Dies ist der erhaltene Betreiberbericht, keine
von Codex nachträglich behauptete manuelle Browserprüfung:

| Prüfpunkt | Betreiberergebnis |
|---|---|
| Lokaler UI-Start | erfolgreich |
| Lektionenauswahl | erfolgreich |
| Anzeige der ausgewählten Quelle | erfolgreich |
| Quellenprovenienz | erfolgreich |
| Mock-Generierung | erfolgreich |
| Kennzeichnung `needs_review` | erfolgreich |
| Markdown-Download | erfolgreich |
| LaTeX-Download | erfolgreich |

Freigegeben ist ausschließlich die technische MVP-Basis für weitere lokale Tests.
**Keine fachliche Freigabe, keine Merge-/Ready-/Deploymentfreigabe.** Die unten
beschriebenen Darstellungsänderungen folgen auf diese Abnahme und wurden gezielt
automatisiert geprüft. Sie sind kein zusätzlicher manueller Abnahmebericht.

### Gezielte Änderungen und tatsächlich ausgeführte Prüfungen

- Quellenverzeichnis standardmäßig nur für im Dokument zitierte Belegblöcke.
  Q-Labels bleiben auf die ursprüngliche vollständige Evidenzfolge bezogen;
  auch zitierte Formelvarianten aus Zwischenständen behalten ihre Quellen.
  In der UI ist die vollständige technische Evidenz optional einsehbar und als
  Summary-JSON herunterladbar. Der Schalter löst keine Generierung aus. Backend:
  `render(..., include_all_evidence=True)` erlaubt die explizite technische Fassung.
- Zeiten nur in der Darstellung auf höchstens zwei Nachkommastellen gerundet.
  Raw-Lokatoren, SHA256, native Segmentbezüge und Source-IDs unverändert; unbekannte
  Zeiten werden weiterhin als unbekannt behandelt, niemals als Null ersetzt.
- Mock bleibt unverändert begrenzt: einfach kompakt zwei/ausführlich vier
  Ausschnitte je Lektion, hierarchisch zwei je Abschnitt. 01.01.2 hat weiterhin
  25 eingelesene/versionierte Segmente, von denen der kompakte Mock Q1/Q2 zitiert.
  **2/25 beabsichtigt**, keine künstliche Abdeckung. Unvollständige wörtliche
  Ausschnitte sind in Export und UI als Demonstrationsmaterial ausgewiesen;
  keine vollständige didaktische Synthese oder fachliche Bewertung behauptet.
- TeX-v2: sichere Umbruchstellen in langen Hash-/Evidence-Datentokens, weiterhin
  TeX-Escaping; deutsche Babel-Locale und Flattersatz. v1-Datei bleibt erhalten.
  Die neue Templateversion invalidiert einfache Cachekeys; keine historischen
  Cachedateien gelöscht/überschrieben, keine Eingangsdateien geändert.
- **87 Backendtests bestanden** in 28,97 s: `test_lecture_summary.py` (35),
  `test_lecture_summary_acceptance.py` (8), `test_lecture_summary_hierarchy.py`
  (39), `test_lecture_summary_presentation.py` (5). Das sind gezielte Export-,
  Quellen-, Cache-, Quality-Gate-, Hierarchie-/Formel-/Resume- sowie Preflighttests,
  keine erneute vollständige Recovery-Regression.
- **10 UI-AppTests plus drei Subtests bestanden** in 25,09 s. Einschließlich
  optionalem Evidenz-/JSON-Schalter ohne erneute Generierung, Standarddownloads,
  Auswahl, Fehler, Authentifizierung/Operatorrolle und deaktiviertem Jobbackend.
- Ruff 0.16.0: Formatierung und Checks aller geänderten Pythondateien aus vorhandenem
  Pre-commit-Cache, keine Installation. Vollständiger Pre-commit-Manager/Hooklauf
  weiterhin nicht als erfolgreich behauptet.

Backendtestbefehl im neuen eigenen `Personal_Assistant-c27-review`-Worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python -B -m pytest \
  -q -p no:cacheprovider tests/test_lecture_summary_presentation.py \
  tests/test_lecture_summary.py tests/test_lecture_summary_acceptance.py \
  tests/test_lecture_summary_hierarchy.py \
  --basetemp=/tmp/c27-review-backend-20261024-01
```

UI im eigenen `personal-assistant-ui-c27-review`-Worktree: dieselbe vorhandene
UI-Umgebung wie zuvor, `PYTHONPATH` auf den neuen Backend-Worktree und UI-Root;
pytest über `site.addsitedir` nach den UI-Paketen ergänzt. Nur
`tests/test_lecture_summary_ui.py`, `-p no:cacheprovider`, eigener Basetemp.
Dependencies unverändert gegenüber C27-C: Python 3.12.12, pytest 9.1.1;
Backend-Pydantic 2.14.1/core 2.50.1, UI 2.14.0/core 2.50.0, Streamlit 1.65.0.
Die bereits dokumentierte Backend-Lockabweichung 2.13.4/core 2.46.4 bleibt bestehen.

### Tatsächliche LuaLaTeX-Kompilation und Originaldatei

Vorhanden: `/usr/bin/lualatex`, LuaHBTeX 1.15.0, TeX Live 2022/Debian,
Systemformat und Pakete `fontspec`, `babel`, `amsmath`, `amssymb`, `geometry`.
`ngerman.ldf` ist nicht vorhanden; v2 verwendet vorhandene deutsche Babel-
Locale-Daten. Kein TeX-Paket, Font oder Systempaket wurde installiert.

Erster isolierter Versuch mit leerem Schriftcache: nach 40 s kontrolliert am
Zeitlimit beendet. Ein folgender Diagnoseversuch mit deaktiviertem Fontscan fand
die Namen-Datenbank im eigenen Schreibcache nicht; kein PDF. Daraufhin wurden
**3.521.847 Bytes vorhandene Latin-Modern-/Schriftnamen-Cachedateien** in den
eigenen Prüfbereich übernommen. Kein Neuaufbau einer Systemumgebung. Frühere
Versuche bleiben als Diagnoseartefakte erhalten. Erste erfolgreiche Kompilationen
zeigten noch Überbreiten; nach Flattersatz in v2 nochmals gezielt kompiliert:

| Finale Fassung für echte 01.01.2-Mock-Summary | Ergebnis |
|---|---|
| `summary-final.tex`, zwei zitierte Belege | Exit 0, PDF mit 2 Seiten |
| `technical-evidence-final.tex`, alle 25 Belege | Exit 0, PDF mit 5 Seiten |
| Beide finale Logs | 0 `Overfull \\hbox`, 0 fehlende Zeichen, keine TeX-Fehler |

Kompilation ausschließlich im eigenen privaten Exportverzeichnis, Argumentliste
ohne Shell, `-no-shell-escape -interaction=nonstopmode -halt-on-error -recorder`,
40-s-Walltimeout, CPU 25 s, Adressraum 1 GiB, Dateigröße 10 MiB, private Cache- und
Ausgabepfade, keine Auto-Formatgenerierung/Live-Fontscans. Keine Compilerintegration
in den UI-Download und kein produktiver TeX-Dienst. PyMuPDF hat die erzeugten PDFs
zusätzlich geöffnet; Q1 in der Normalfassung, Q25 nur in der technischen Fassung,
Demo-Kennzeichnung vorhanden. Das beweist Exportfähigkeit, keine fachliche Qualität.

Privater Prüfbereich:
`/home/robfra/0_Portfolio_Projekte/c27-review-evidence-20261024/`;
finale PDFs und Logs unter `tex-final/`. Keine Quelle oder private Summary im Git.
Der reale SourceCollector-/Mock-Lauf wurde mit gesperrtem `socket.connect` und
verbotenem `httpx.Client` ausgeführt. Alle 25 Evidence-Records blieben erhalten,
Status `needs_review`, Original-SHA256 vor/nach Generierung identisch:
`79a5dd28560679324fdfb3ab0b90307148add6e83267018235157dd718e756ce`.

### Kontrollierter Live-Test nur vorbereitet

Der [aktualisierte separate Vorschlag](c27_live_test_proposal.md) legt
`gpt-6-luna`, genau eine einfache Anfrage für 01.01.2, vollständige 25 Segmente
mit 1.813 Textbytes, maximal 2.000 Ausgabetokens und ein vorgeschlagenes
Betreiberbudget von **0,01 USD** fest. Vollständiger JSON-Request: 13.348 Bytes;
plus 2.048 Framingreserve **15.396 Inputeinheiten**, gesamt **17.396** reserviert.
Prompt, Schema, Optionen und alle Quellenmetadaten im Payload berücksichtigt.
Preflight reproduzierbar mit `inspect --case text`, ohne HTTP-Client/Keyzugriff.
Private vollständige Requestdatei und Fingerprint zur lokalen Durchsicht vorhanden;
keine Live-Konfiguration aktiviert. Die Geldgrenze ist eine tarifabhängige
Betreiberbudgetplanung, kein implementierter Dollar-Hardcap im einfachen Provider.

Offen: fachliche und visuelle Quellen-/Formelprüfung, tatsächlicher Modellzugang,
Kompatibilität einer Live-Antwort, Usage/Kostenabrechnung und gesonderte spätere
Upload-/Kostenfreigabe. Kein Live-Aufruf, kein neuer Browserlauf, keine vollständige
398-/157-Testregression. Kein ENOSPC, keine Installation, Löschung, Migration,
Produktions-/Serveränderung oder neue Portfreigabe. Backend #158 und UI #21 bleiben
Drafts. Die beiden neuen eigenen Branches/Worktrees bleiben wegen des untersagten
Merges fürs Review erhalten; Dokumente liegen im Draft, nicht in master/main.
