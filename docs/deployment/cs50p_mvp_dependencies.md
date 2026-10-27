# CS50P-MVP: Abhängigkeiten

## C26-CS50P-03: Runtime-Nachtrag

Aktuelle Basis: Featurecommit 2f2b410; Installations-/Closuregrenzen und
versionierte Runtimepfade im [Installationsplan](cs50p_hetzner_installation.md).
Der native ssh-runtime benötigt keine C16-Bearertoken; der folgende ältere
Tokenhinweis betrifft den früheren MVP-/v2-Pfad. Das Lockprofil bleibt unverändert.
Eine positive Neuinstallation des vollständigen Runtimeprofils ist weiterhin offen.

Basis: `6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d` plus gesicherter MVP-Patch;
Dateiintegrität über Übergabemanifest. Kein neuer freigegebener Liefercommit vorhanden.

Python 3.12, Linux mit `renameat2(RENAME_NOREPLACE)`, lokales ext4/xfs/btrfs mit
funktionierenden flock/fsync/SQLite-WAL; Ubuntu 24.04 ist Ziel, kein hier getesteter Host.
Systemd mit cgroup v2; systemd 252 ist lokale Syntaxprüfumgebung. Der Zielhost benötigt
funktionierende CA-Zertifikate, DNS und Uhrzeit. Keine GPU/FFmpeg/Whisper/yt-dlp nötig.

Der bestehende `deployment/runtime/pyproject.toml` und dessen `uv.lock` bleiben
unverändert. `deployment/cs50p-mvp/requirements.txt` wurde daraus frozen/offline
mit uv 0.9.15 exportiert: alle transitiven Abhängigkeiten und SHA-256 enthalten.
Direkt: pydantic 2.13.4, pydantic-settings 2.15.0, httpx 0.28.1,
beautifulsoup4 4.15.0, typer 0.26.8, python-dotenv 1.2.3, PyYAML 6.0.3,
returns 0.29.0, tenacity 9.1.4, PyMuPDF 1.28.2. HTTPcore 1.0.9 ist im Lock;
SNI-Extension und TLS-Verifikation werden ausdrücklich getestet. Kein SDK für LLMs,
Frontend, Modelle oder ML-Stack wird über dieses Profil installiert.

READ-ONLY, lokale Reproduktion des Exports (Ausgabe nach stdout):
```sh
uv export --project deployment/runtime --frozen --offline --no-dev --no-emit-project --format requirements-txt
```

CHANGE, ausschließlich später manuell und nach Freigabe: Pythonvenv anlegen und
hashgeprüfte Wheels installieren (Wheelhouse muss separat, passend zu CPython 3.12
und Hetznerarchitektur bereitgestellt und geprüft sein):
```sh
sudo python3.12 -m venv /opt/cs50p/venv
sudo /opt/cs50p/venv/bin/python -m pip install --no-index --only-binary=:all: --find-links=/opt/cs50p/wheelhouse --require-hashes -r /opt/cs50p/app/deployment/cs50p-mvp/requirements.txt
```
Seiteneffekt: ausschließlich neue Laufzeit unter `/opt/cs50p`; Rückweg: Dienste
stoppen, bisherige Laufzeit verwenden; Venv/Wheelhouse erhalten, nicht automatisch löschen.
Kein Resolver-/Installations-/Wheelclosureerfolg behauptet: keine Pakete heruntergeladen
oder installiert. Positiver Neuinstallationstest steht aus und blockiert reale Ausführung.

Umgebung: feste PYTHONNOUSERSITE/PYTHONDONTWRITEBYTECODE/PYTHONUNBUFFERED;
HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE; HOME auf eigenem Cache. Kein benötigtes APIsecret,
keine .env-Datei, kein Proxy, keine TLS-Abschaltung. Operator-C16-Token bleibt eine private
0600-Datei, wird niemals als Argumentinhalt, Environment oder Ausgabe übergeben.

Die verwendete bestehende Testvenv hat Python 3.12.12 und die konkret benötigten
Pydantic/HTTPX/BeautifulSoup/PyMuPDF-Versionen. `pydantic-settings` und `returns`
sind dort nicht installiert; kein vollständiger Runtimeclosurebeweis. Details in
`test-environment.json` der Übergabe. Der Lockexport selbst wurde ohne Resolver
oder Paketinstallation erzeugt.
