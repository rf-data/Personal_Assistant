# C26-CS50P-07: Week 0, Betreiberablauf

28.10.2026. **HOLD**, C26 gesamt **HOLD**. Diese Befehle sind vorbereitet,
aber wurden weder auf Hetzner ausgeführt noch zur Beschaffung echter Kursdateien
verwendet. Keine Produktionsfreigabe, kein C16-Start, keine Coolify-Änderung.

Voraussetzungen vor allen Host-CHANGE-Schritten: positive C06-Frozen-Wheelhouse-
Installation und Hostprüfung nach dem
[C06-Leitfaden](cs50p_reproducible_runtime_operator_guide.md), C07-Code-/Quellenreview,
separat genehmigtes root-eigenes, für den Dienst nur lesbares C07-Staging unter
`/opt/cs50p-week-review/app`, unprivilegierter Benutzer `cs50p-download`, private
Archiv-/Reportverzeichnisse aus C06 und weiterhin maskierte C16-Units. Das neue
Unit-Template wird vom unveränderten C06-Installer **nicht automatisch installiert**.
Die gesonderte Installation des geprüften Templates ist eine spätere Betreiberaktion.
Kein `enable`, kein Timer, kein neuer Port.

## 1. READ-ONLY: Voraussetzungen und Belege ansehen

```bash
systemctl is-enabled cs50p-worker.service cs50p-native@.service
systemctl is-active cs50p-worker.service
systemctl status cs50p-download-only.service --no-pager
df -B1 /var/lib/cs50p-download-only
cd /opt/cs50p-week-review/app
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week --help
```

Die lokale Entwicklungsumgebung hatte weniger als 5 GiB freien Speicher. Das
Produktionslimit bleibt 5 GiB Reserve **zuzüglich** des nächsten Transfers. Keine
Budgets erhöhen und keine fremden Daten löschen, um diese Prüfung zu umgehen.

## 2. CHANGE (lokale Planungsdateien): Discovery beginnen

Discovery arbeitet offline mit ausdrücklich angegebenen HTML-Exporten. Keine
implizite Verzeichnissuche und kein rekursiver Linkdownload. Ein Einstieg mit nur
der Wochenübersicht reicht zur Planung der eigenen Short- und PSet-Seiten.

Eine private Betreiberdatei `/var/lib/cs50p-download-only/reports/input/snapshots.json`
hat diese Struktur; die Hashes müssen zu den tatsächlich geprüften Exporten passen:

```json
{
  "course_id": "cs50_python",
  "week_id": "0",
  "source_origin": "official",
  "pages": [
    {
      "url": "https://cs50.harvard.edu/python/weeks/0/",
      "path": "week-0.html",
      "sha256": "<tatsächlicher SHA-256 des vorhandenen HTML-Exports>"
    }
  ]
}
```

Nur echte Betreiberexporte als `official` deklarieren. Die Datei `week-0.html`
liegt relativ zur Snapshotdatei, ohne Symlinks oder Pfadtraversierung. Der vorhandene
historische Week-0-Snapshot kann als Startpunkt dienen, ist aber kein Nachweis des
aktuellen Live-Inhalts. Die beobachteten Browser-Metadaten unter
`docs/course_sources/cs50p_week0_review/` sind ausdrücklich **keine HTML-Exporte**.

```bash
sudo -u cs50p-download /opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week discover \
  --snapshots /var/lib/cs50p-download-only/reports/input/snapshots.json \
  --output /var/lib/cs50p-download-only/reports/week0-discovery-001.json
```

READ-ONLY: Manifest, manuelle Liste und Budgetplan ansehen:

```bash
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week show \
  --inventory /var/lib/cs50p-download-only/reports/week0-discovery-001.json
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week plan \
  --inventory /var/lib/cs50p-download-only/reports/week0-discovery-001.json
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week manual-list \
  --inventory /var/lib/cs50p-download-only/reports/week0-discovery-001.json
```

## 3. CHANGE (nach Quellenreview): genau gewählte Quellen freigeben

Der Plan ist **keine Freigabe**. Er enthält `license_reviewed: false` und zusätzliche
Planungsfelder, die der strenge Freigabevertrag zurückweist. Der Betreiber prüft
Lizenz/Nutzungsbedingungen/robots, Quelle, Typ, Maximalgröße und lokale Aufbewahrung
und schreibt selbst eine private `selection.json` als Liste der einzeln genehmigten
`SourceGrant`-Objekte. Jedes Objekt enthält genau `material_id`, `source_url`,
`source_format`, `max_bytes`, `license_reviewed: true`, `purpose`.

Für die erste Runde nur die konkret benötigten `page`-Zeilen auswählen und
`purpose: discovery` verwenden. Auch die einzelnen Aufgaben werden nach Erfassung
der PSet-Übersicht in einer weiteren begrenzten Runde sichtbar. Die Summe aller
individuellen Obergrenzen muss ins Transferbudget der Runde passen. Große Pläne
werden in mehrere ausdrücklich geprüfte Runden aufgeteilt. Keine Bulk-Freigabe
aller Referenzen und keine generierten synthetischen Produktionsfreigaben.

```bash
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week approve \
  --inventory /var/lib/cs50p-download-only/reports/week0-discovery-001.json \
  --selection /etc/cs50p-week-review/selection.json \
  --reviewed-by BETREIBER --review-reference HOST-REVIEW-TICKET \
  --transfer-bytes 33554432 --purpose discovery \
  --output /var/lib/cs50p-download-only/reports/week0-approval-001.json
```

READ-ONLY: Die Hashbindung, Quellidentitäten, Typen und Limits erneut prüfen:

```bash
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week check-approval \
  --inventory /var/lib/cs50p-download-only/reports/week0-discovery-001.json \
  --approval /var/lib/cs50p-download-only/reports/week0-approval-001.json --purpose discovery
```

## 4. CHANGE (erst nach Runtime- und Hostfreigabe): systemd-Runde

Das geprüfte Template
`deployment/cs50p-download-only/cs50p-week-download@.service` nutzt dieselben
Ressourcen-/Netzgrenzen wie der C04-Dienst. Jede Runde bekommt eine neue eindeutige
Instanz, beispielsweise `week0-001`. Kein vorhandenes Ergebnis überschreiben.
Root legt `/etc/cs50p-week-review/week0-001/` an und kopiert die **genau geprüften**
Dateien dort als `inventory.json` und `approval.json` hinein, root-eigen,
Gruppe `cs50p-download`, Modus 0640 (Verzeichnis 0750).

Für die erste Discoveryrunde enthält die root-eigene `run.env`:

```ini
CS50P_WEEK_PURPOSE=discovery
CS50P_WEEK_RETRY=
```

Nach separat genehmigter Installation des Templates:

```bash
sudo systemctl start cs50p-week-download@week0-001.service
```

READ-ONLY:

```bash
journalctl -u cs50p-week-download@week0-001.service --no-pager
systemctl show cs50p-week-download@week0-001.service -p Result -p ExecMainStatus
```

Das abschließende Manifest liegt unter
`/var/lib/cs50p-download-only/reports/week-week0-001-final.json`;
Zwischenstände liegen im gleichnamigen `-checkpoints`-Verzeichnis. Die doppelte
`week-`-Bezeichnung folgt dem Template und ist absichtlich in allen Pfaden konsistent.
Bei Abbruch den letzten tatsächlich geschriebenen Checkpoint anhand von Inhalt und
Zeit prüfen; nicht automatisch die lexikografisch letzte UUID wählen. Vorhandene
`.download-*`-Dateien blockieren den Lauf zur manuellen Untersuchung.

## 5. CHANGE (offline): neu planen, danach Materialien selektiv beschaffen

```bash
sudo -u cs50p-download /opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week discover \
  --snapshots /var/lib/cs50p-download-only/reports/input/snapshots.json \
  --previous-inventory /var/lib/cs50p-download-only/reports/week-week0-001-final.json \
  --archive /var/lib/cs50p-download-only/archive \
  --output /var/lib/cs50p-download-only/reports/week0-discovery-002.json
```

Rediscovery liest ausschließlich verifizierte Page-Receipts aus dem angegebenen
Archiv hinzu. Damit erscheinen weitere Aufgaben und alle exakten Short-Assetlinks.
Dieser Vorgang wird mit ausdrücklich genehmigten Seiten wiederholt, bis die
Discovery vollständig ist. Rediscovery erzeugt einen **neuen** Planungsstand;
bereits archivierte Bytes werden beim anschließenden Erwerb erneut über ihre
Receipts verifiziert und wiederverwendet.

Danach `plan`, Betreiberselektion, `approve` und `check-approval` mit
`--purpose download` wiederholen. Neue systemd-Instanz und passend abgelegte
Inventar-/Freigabedateien verwenden; `run.env` enthält dann
`CS50P_WEEK_PURPOSE=download`. Nur gewählte Transcript-/Subtitle-, Notes-, Slides-
und HTML-Aufgabenquellen abrufen. TXT/SRT/VTT werden vor Veröffentlichung strukturell
validiert. Schlägt ein Transcript fehl, wird die nächste Alternative im neuen
Inventar ausgewählt; **eine neue Freigabe** ist für deren Abruf notwendig.

Audio/Video werden hier niemals automatisch beschafft, auch nicht über einen
gefälschten Mediengrant. Falls beide Textquellen fehlen, ist Audio der bevorzugte
Reviewkandidat. Medien benötigen einen separaten Quellen-/Größen-/Betriebsentscheid
außerhalb dieser textorientierten Runtime. Ein Medienverweis erfüllt keinen
validierten Sprachinhalt und aktiviert keine Transkription.

## 6. CHANGE (lokaler Import): Source Code nachreichen

`manual-list` zeigt alle Angebote und die ausgewählte Pflichtdatei. Pro Lecture
oder Short wird vorzugsweise ein ZIP-Paket gewählt; Index und PDF bleiben
Alternativen. Nicht angebotener Source Code steht ausdrücklich auf
`NOT_APPLICABLE`. Unaufgelöste Hrefs müssen zuerst durch echte HTML-Exporte ersetzt
werden. Ein unbekanntes Paket lässt sich nicht unter einer erfundenen URL importieren.

```bash
sha256sum /var/lib/cs50p-download-only/reports/manual-input/src0.zip
sudo -u cs50p-download /opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week import-code \
  --inventory /var/lib/cs50p-download-only/reports/week-week0-002-final.json \
  --archive /var/lib/cs50p-download-only/archive \
  --material-id 'EXAKTE_ID_AUS_MANUAL_LIST' \
  --file /var/lib/cs50p-download-only/reports/manual-input/src0.zip \
  --sha256 'TATSAECHLICHER_SHA256' \
  --provenance 'Betreiber, Datum, offizielle Quellseite und Dateiname' \
  --output /var/lib/cs50p-download-only/reports/week0-after-manual-001.json
```

ZIPs werden auf Containererkennbarkeit geprüft, nie entpackt oder ausgeführt.
`MANUAL_VERIFIED` belegt Hash/Größe/Provenienz des gelieferten Containers, keine
fachliche Vollständigkeit seines Inhalts. Rohdateien werden niemals überschrieben.

## 7. READ-ONLY: Vollständigkeit prüfen, CHANGE: selektiv erneut versuchen

```bash
/opt/cs50p-download-only/current/venv/bin/python -m scripts.cs50p_week report \
  --inventory /var/lib/cs50p-download-only/reports/week0-after-manual-001.json \
  --archive /var/lib/cs50p-download-only/archive
```

`--output NEUER_PFAD` speichert den Bericht (CHANGE). Der Bericht prüft Hashes,
Receipts und manuelle Provenienz erneut, ohne fehlende Dateien stillschweigend
zu adoptieren. Ein unverifiziertes Statuslabel kann kein FULLY_COMPLETE erzeugen.
`FULLY_COMPLETE` betrifft nur die definierten Materialbedingungen; C26 bleibt HOLD.

Für Fehler/Unterbrechungen den erhaltenen Inventar-/Checkpointstand verwenden,
`plan` erneut ansehen, nur betroffene IDs wählen und `approve` sowie `check-approval`
mit `--retry-failed` durchführen. Eine neue Instanz, z.B. `week0-003`, erhält
`CS50P_WEEK_RETRY=--retry-failed` in ihrer `run.env`. Kein automatischer Retry,
kein Löschen von Receipts oder Beweisen. Nach jedem Lauf wieder `report` ausführen.
