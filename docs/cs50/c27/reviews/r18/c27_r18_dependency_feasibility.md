# C27-R18 – Dependency-Feasibility

Entscheidung NEEDS_RUNTIME_VALIDATION. Die R17-Profile wurden wiederverwendet und gegen das unveränderte uv.lock geprüft. Keine Paketbeschaffung, keine Installation, kein Import der Zielpakete und kein pytest-Lauf wurden durchgeführt. Öffentliche Herstellerdokumentation und feste Actionmetadaten wurden ausschließlich lesend konsultiert; keine Projekt-/Server-/Paket-Remoteausführung.

| Eigenschaft | Befund |
| --- | --- |
| Python | Projekt >=3.12,<3.14; CI exakt CPython 3.12, Linux x86_64 |
| Image | docker.io/library/python:3.12-slim-bookworm@sha256:<geprüfter Digest>; noch vom Operator zu bestimmen |
| glibc | bookworm 2.36; ausgewählte manylinux-Tags bis 2.36 oder pure Python/abi3 |
| uv | lokal 0.9.15; CI benötigt kein uv, kein uv sync und kein Relock |
| PDF / Namespace | je 28 Pakete, 32275486 Byte komprimierte Wheels |
| UI | 59 Pakete, 141878277 Byte komprimierte Wheels |
| PyMuPDF | 1.28.2, echter PDFworker; kein fremdes fitz-Paket |
| Streamlit | 1.61.1 ausschließlich UI; AppTest-Importprüfung obligatorisch |
| pytest | 9.1.1; Plugin-Autoload deaktiviert |

Alle gewählten URLs, Größen, SHA-256-Werte und Versionen stimmen mit uv.lock überein. 35 / 85 / 35 aufgezeichnete aktive Dependency-Kanten sind in den jeweiligen Closures enthalten. Wheel-Tags wurden nochmals mit vorhandener packaging-Bibliothek gegen CPython-3.12-/abi3-/pure-Python-Tags auf manylinux x86_64 geprüft. Das bestätigt keine Serververfügbarkeit, keine geladene Wheel-METADATA und keine installierte Transitivität. Requires-Python, Requires-Dist, importierbare Native Libraries, mögliche Versionskonflikte und Peakressourcen bleiben bis zum echten Offline-pip-check und den Imports offen.

`requirements/*.txt` sind unveränderte R17-URLprofile. Neue `*.offline.txt` enthalten dieselben Namen, exakten Versionen und Hashes ohne URL. Ein --no-index allein würde direkte HTTPS-URLanforderungen nicht netzlos machen; deshalb wird die Installation ausdrücklich auf die neuen Profile umgestellt.

## Ausführbarer Zweiphasenpfad

1. Kontrollierte Bereitstellung: geprüften Digest mit --platform linux/amd64 beziehen. Im begrenzten Beschaffungscontainer ausschließlich die manifestierten HTTPS-URLs auf files.pythonhosted.org abrufen. Proxyvererbung und Redirects gesperrt, Dateinamen, Bytezahl und Hash sofort prüfen. Keine Sdist, kein Build, keine Dependency-Neuauflösung, kein Produktcode, keine Credentialweitergabe. Dieser Schritt braucht absichtlich Netzwerk.
2. Netzlose Phase: Wheelhouse nochmals auf exakte Dateimenge, Hash, Größe und Wheelidentität prüfen. Im selben Basisimage eine neue venv erstellen; alle Pakete mit --network none, --no-index, --find-links, --no-deps, --require-hashes und --only-binary installieren. ensurepip stammt aus dem gepinnten Image und lädt nichts nach. pip-Version wird durch den Digest festgelegt und später protokolliert. pip check muss bestehen. Danach neue Container mit read-only venv und --network none: Collection, dann Ausführung. Kein Fallback auf Nachinstallation, Aktualisierung oder entschärfte Tests.

Die Beschaffung und die Offline-Installation bekommen je ein eigenes Log, Wheelhashbericht und Containerstatus; bei Fehlern werden keine Tests gestartet. Die Originalprofile bleiben als Auditnachweis erhalten. Eine komplette Ausführung ab leerem Standardrunner ohne jegliches Netz ist praktisch nicht gegeben: Basisimage, Actions und Wheels fehlen. Mit zuvor geprüft bereitgestellten Materialien ist ausschließlich die Installations-/Testphase netzlos ausführbar. Keine Behauptung einer bereits funktionsfähigen Umgebung.

## Ressourcen

UI-Wheels ca. 135.3 MiB, PDF ca. 30.8 MiB; ausgepackte Umgebung, Imagegröße, Metadaten und Testpeaks sind ungemessen. Kein Torch, Docling, Modell- oder Provider-SDK, kein gesamtes Projektextra. Wheels und venv je Job frisch; kein persistenter Cache. Namespace verwendet das PDFprofil. Matrix sequenziell, 4-GiB-Containerlimit mit 2-GiB-work-tmpfs und 512-MiB-tmp-tmpfs innerhalb desselben cgroupbudgets. Die 1-GiB-/20-Sekunden-Workerlimits bleiben bestehen.

Admission 7 GiB physischer RAM und 10 GiB freie Disk; freie Reserve 6 GiB. Die offizielle GitHub-Dokumentation nennt für aktuelle x64-Linux-Standardrunner 4 CPU/16 GB RAM öffentlich und 2 CPU/8 GB privat, jeweils 14 GB SSD. Die Einheiten und tatsächlich verfügbare Ressourcen müssen beim Start gemessen werden; Anforderungen werden bei Knappheit nicht automatisch abgesenkt. Hetzner/Coolify sind kein Ausweichziel. 75 Minuten äußere Jobgrenze, maximal 61 Minuten begrenzte Kernphasen im Namespacejob; keine gemessene Laufzeitprognose.

[GitHub Runnerressourcen](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [pip Hashmodus und ausschließlich Wheels](https://pip.pypa.io/en/stable/topics/secure-installs/).
