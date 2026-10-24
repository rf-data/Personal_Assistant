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
pytest 9.1.…615 tokens truncated…n-App auf
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
