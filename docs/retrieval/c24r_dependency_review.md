# C24-R Dependency Review – 2026-10-26

Status: Definition/Export PASS; vollständig installierte Lockumgebung HOLD.
Eigener vorgesehener Commit: `build(c24r): expose minimal PDF and HTML extras`.

## Ausgangslage und Entscheidung

| Kategorie | Bestand / Entscheidung |
|---|---|
| Core bereits an Basis vorhanden | pydantic, python-dotenv, pyyaml, httpx, tenacity, typer; unverändert |
| Testwerkzeuge bereits vorhanden | pytest, Ruff, mypy, detect-secrets, pre-commit in `dev`; pytest bleibt dort |
| PDF-/HTML-Runtime bereits vorhanden | PyMuPDF und bs4 im großen `lecture-worker`-Extra; beautifulsoup4 bereits transitiv gelockt |
| Für diese Abnahme benötigt | PyMuPDF stellt `fitz` bereit; beautifulsoup4 stellt `bs4` bereit; bestehende PDF-/Workflowtests importieren fitz bei Collection |
| Neue schmale Extras | `pdf = [pymupdf>=1.27.2.2]`, `html = [beautifulsoup4>=4.15.0]` |
| Nur lokal | `.venv`, Caches, Testausgaben und installiertes soupsieve 3.0.4; nicht versionieren |

Der anfängliche lokale Diff verschob Pakete aus `lecture-worker`; der anfängliche
Lock führte PyMuPDF sogar als Core-Paket und kannte die neuen Extras nicht.
Beide Ausgangsdateien sind im finalen Nachweispaket als `*.before` gesichert.
Die Korrektur erhält die neuen schmalen Extras und die bisherige Abdeckung von
`lecture-worker`; nur dessen doppelte PyMuPDF-Zeile entfällt. Core wird nicht erweitert.

`uv.lock` wurde ausschließlich im Rootpaket angepasst: Core-PyMuPDF entfernt,
Root-Extra-Kanten/Requires-Dist/Provides-Extras passend ergänzt. Alle externen
Packageeinträge einschließlich Versionen, URLs und Artefakthashes sind gegenüber
dem anfänglichen Lock byteinhaltlich/strukturell unverändert. Ein separater Checker
bestätigt die genaue Übereinstimmung der Projektanforderungen und Rootmetadaten.
Dies ist eine gezielte Metadatenkorrektur, kein behaupteter erfolgreicher Resolverlauf.

## Tatsächliche Nachweise

Python 3.12.12, SQLite 3.50.4, uv 0.9.15, pytest 9.1.1, Ruff 0.16.3,
Pydantic 2.13.4, httpx 0.28.1, PyMuPDF 1.28.2, beautifulsoup4 4.15.0.
47 installierte Distributionen geprüft: einzige Versionsabweichung zum Lock ist
`soupsieve 3.0.4` statt `2.9.2`. Die Testläufe verwenden die bestehende `.venv`
mit `--no-sync`; kein vollständiger Installationsnachweis daraus ableitbar.

- PASS: TOML parsebar; Core-/Extra-Kanten und Requires-Dist entsprechen dem Projekt.
- PASS: sämtliche externen gelockten Pakete/Hashes unverändert.
- PASS: `uv export --frozen --offline --no-emit-project --group dev --extra pdf --extra html`.
- PASS: `uv sync --frozen --offline --dry-run --group dev --extra pdf --extra html`;
  einziger angekündigter Wechsel: soupsieve 3.0.4 → 2.9.2, ein Paketdownload nötig.
- HOLD: `uv lock --check --offline` verlangt fehlende Metadaten des bestehenden
  `de-core-news-sm`-URL-Extras. Identisches Ergebnis mit unveränderten Basisdateien
  in isoliertem Verzeichnis. Kein Modell heruntergeladen und kein Cache manipuliert.
- HOLD: frische Installation des exportierten Profils und anschließende Regression.

Der hashgebundene Export steht in
[c24r_acceptance_requirements.txt](c24r_acceptance_requirements.txt).
Er umfasst Core + dev + pdf + html, keine ML-/Browser-/SDK-Extras.

## Reproduktion für den Betreiber

Im Repository, in einer Umgebung mit verfügbarem Paketcache oder erlaubtem
Paketnetz. Das Zielverzeichnis muss neu sein; bestehende `.venv` bleibt erhalten:

```bash
C24R_ACCEPT_ENV=$(mktemp -d /tmp/c24r-accept-env.XXXXXX)
uv venv --python 3.12 "$C24R_ACCEPT_ENV/venv"
uv pip install --python "$C24R_ACCEPT_ENV/venv/bin/python" --require-hashes \
  -r docs/retrieval/c24r_acceptance_requirements.txt
export UV_PROJECT_ENVIRONMENT="$C24R_ACCEPT_ENV/venv"
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```

Dieser Weg installiert ausschließlich den geprüften Export und umgeht keine
Socketgrenze. Für den Resolvernachweis `uv lock --check --offline` mit bereits
vorhandenen Metadaten wiederholen; fehlende Modellmetadaten separat provisionieren,
keinen unkontrollierten Online-Resolver-/All-Extras-Lauf starten.

Integration: Der aktuelle master enthält inzwischen `test-core`, `test-offline`
(PyMuPDF, beautifulsoup4, pytest) und `test-qdrant`. Dort zunächst das bestehende
`test-offline`-Profil verwenden und nur einen belegten Runtimebedarf für zusätzliche
Extras übernehmen. Den alten C24-R-Lock niemals über den master-Lock kopieren.
