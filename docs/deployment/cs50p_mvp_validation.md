# CS50P-MVP: Offlinevalidierung und Abschluss

## C26-CS50P-03: neuer Validierungsstand

Die folgenden ursprünglichen MVP-Nachweise bleiben unverändert historisch.
Aktuelle Läufe, neue rote SQLite-Stresstests und offene Hostnachweise stehen in
[Release Readiness](cs50p_mvp_release_readiness.md) und
[SQLite-Stabilität](cs50p_sqlite_stability.md). Native Admission ist inzwischen
als Featurecommit 2f2b410 auf GitHub gesichert. C26 bleibt HOLD.

Stand 27.10.2026, **HOLD**. Reine Paketvorbereitung. Kein Hetzner-SSH, keine
Coolify-/Firewall-/VPNänderung, keine realen Kursdownloads, keine produktiven
Daten/Jobs, keine Live-LLMs, kein Merge/Push oder C26-Go-live. C24-R und DEP-01
unverändert. Die Browserrecherche beschränkte sich auf öffentliche Informationsseiten.

## Gesicherte Basis und Lieferform

INT-02: `6e2fb1c74d9aba338b5e09cec6c8d591a3e0474d`; Parent `be03e83`.
Commitinhalt vor Implementierung exportiert und geprüft. Vorhandene INT-02-
Backend-/UI-Handoffprüfsummen vollständig bestätigt. Pilottrackedfiles unverändert.
Der bereits vorbereitete Featureworktree `Personal_Assistant-cs50p-mvp` /
`feat/c26-cs50p-mvp` ist außerhalb des beschreibbaren Bereichs. Geteilte Gitmetadaten
sind read-only. Keine Schreibgrenze durch alternative Gitmetadaten umgangen.

Deshalb vollständige Basiskopie plus Änderungen im dauerhaften
`artifacts/cs50p_mvp/source`, vollständiger anwendbarer Patch separat. Getestet
wurde **diese Exportkopie**, nicht der unveränderte Featureworktree. Nach Übernahme
sind Review und reguläre Integration weiter offen. Keine Behauptung der Integration
in master; der Nutzer untersagt diesen Merge ausdrücklich. Keine Branches oder
Worktrees angelegt, gelöscht oder bereinigt. Bestehender Featureworktree bleibt
wegen ausstehender Übernahme/Review erhalten.

## Tatsächlich ausgeführte Prüfungen

| Lauf | Ergebnis / Aussage |
|---|---|
| Erste neue Download-/TLS-/Publikationsgruppe | 58 passed, 2 failed. Bereits gepufferte HTTPX-Fixtures umgingen einen nur ausgetauschten Stream; Wrapper auf neue Responseobjekte korrigiert. Rote Logs erhalten. |
| Korrigierte Gruppe | 60 passed, keine Fehler. Kein zusätzlicher Erfolg durch Addition überlappender Läufe behauptet. |
| Breitere Regression | 112 passed, 1 deselected, keine Fehler; 72,73 s. C16-Worker/Cancel/Restart/Resume, Bestandspipeline, Kapazität, INT-02 und neue MVPfälle. |
| Finale Regression inklusive vorhandener v1/v2-Gates | 241 passed, 1 deselected, keine Fehler; 116,16 s. Anschließend reine Reportanreicherung (Quellenbindung auch bei Abbruch) im finalen CLIstand separat: 48 passed, keine Fehler; 3,24 s. Überlappende Tests nicht addiert. |
| Ruff auf allen sieben geänderten Pythondateien | Check und Formatcheck erfolgreich am finalen Quellstand. |
| systemd Originalunits | Exit 1 ausschließlich wegen hier nicht vorhandener Zielvenv `/opt/cs50p/venv/bin/python`; kein Dienst gestartet. |
| systemd Syntaxfixture | Exit 0 mit einzigem Ersatz des Interpreterpfads durch vorhandenes `/usr/bin/python3`; alle anderen Direktiven unverändert. systemd 252. Kein Ubuntu24-/cgroup-Ausführungstest. |
| Dependencyexport | Frozen/offline aus unverändertem Runtime-Lock erfolgreich, Hashrequirements enthalten. Keine Installation, kein Wheel-/Imagebuild. |
| Patch / Diff / Prüfsummen | Vollständiger Patch auf sauberer Basis angewendet: alle 19 beabsichtigten Dateien byte- und modusgleich; lesendes apply --check am vorbereiteten Featureworktree erfolgreich, Whitespaceprüfung erfolgreich. Übergabebelege in package-verification.json / HANDOFF.md; SHA-256 separat verifiziert. |

Offlineprofil blockiert Socketconnect, DNS, Listener und Infrastrukturkommandos.
HTTPX-MockTransport und synthetische Streams ersetzen lokale HTTPserver; keine echten
Quellen aufgerufen. TLSnegativtest benutzt echte SSL-Kontexte/MemoryBIO-Handshakes
mit frisch synthetisch erzeugtem, nicht vertrauenswürdigem Zertifikat. IP-Pinning,
Original-Host/SNI und DNS-Neuauflösung separat geprüft. Kein tatsächlicher
Internet-TLS-/Redirect-/DNS-/Egressbeweis und kein Hostlogouttest.

Abgedeckt: Metadaten/Batchhashes, Quellenfreigaben, Download, Content-Type/Länge/
Teilabbrüche, erwarteter SHA, Inventar/Receipt, echter vorhandener HTML-/PDFparser,
Persistenz und erneutes Lesen, Deduplizierung, HTTP 403/404/429/500, Redirects zu
Metadata/privaten Zielen (komplett verweigert), DNS-Mischantworten/Rebinding, private/
IPv6-/Metadataziele, Backoff, Payloadbudget, Dateinametraversal, SIGTERM im CLI,
expliziter Retry, paralleler Lauf-Lock und Pflichtgate-/Protokoll-Downgradeabwehr.
Ein neuer nativer Worker ohne gültige Queue/Admission muss abgewiesen werden und
darf keine Ersatzqueue/journal erzeugen. Vorhandene C16tests decken reale lokale
synthetische Guardianprozesse, Cancel/Restart/Resume und persistente Ergebnisse ab.

Ressourcenprüfung ist begrenzt: Pythonbudgetprüfungen und Unitdirektiven sind offline
getestet; CPU/RAM/PID-/tmpfs-Durchsetzung auf dem Zielhost ist nicht getestet.
Die bestehenden Gatepositivfälle sind synthetisch, keine native Produktivadmission.
Ein abgewählter externer Test wird nicht als bestanden gezählt.

CHANGE, lokale Reproduktion mit ausschließlich neuen synthetischen /tmp-Wurzeln
(erzeugt lokale Testdaten/JUnit, keine Hoständerung; Rückweg eigene Testausgaben
erhalten oder nach Prüfung löschen):
```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.venv/bin/python -m pytest -q -o addopts= -p no:cacheprovider -p tests.offline_guard -m 'not external_integration' \
  tests/test_cs50p_mvp.py tests/test_cs50_material_download.py tests/test_material_publication.py tests/test_cs50_batch_worker.py tests/test_cs50_capacity.py tests/test_cs50_material_e2e.py tests/test_c26_int_02_sqlite.py tests/test_deployment_gate.py tests/test_deployment_gate_v2.py \
  --basetemp=/tmp/cs50p-mvp-operator-NEW --junitxml=/tmp/cs50p-mvp-operator-NEW.xml
```
Venv wurde nur benutzt, nicht verändert: Python 3.12.12. Pydantic-settings und
returns fehlen in der Testvenv; die ausgeführten Pfade benötigen sie nicht. Die
Tests beweisen deshalb keine vollständige Installation des exportierten Runtimeprofils.
Python-/Dependencyversionen stehen zusätzlich in test-environment.json der Übergabe.

## Antworten auf die zehn Abschlussfragen

1. **Vorhanden:** Snapshotdiscovery, Link-/Materialinventar, Batchdownload, SHA/
   Receipts/Skip, HTML/PDF/Code, Media-last-Planung, C18/C16 mit Guardian/Cancel/Resume
   sowie Kapazitäts-/Execution-/Admissiongates. Siehe Architekturtabelle.
2. **Neu:** kleiner CS50P-CLIguard und native systemd-Profile; ausschließlich
   nachgewiesene Downloadhärtung, private Versuchsreports, Offlinefixtures und sechs
   Deploymentdokumente. Keine zweite Queue/Downloadimplementierung.
3. **Start:** CHANGE, erst nach separater Freigabe: `sudo systemctl start --no-block
   cs50p-download.service`. Seiteneffekt Download/Reports, Rückweg entsprechendes
   `systemctl stop` (CHANGE). Verarbeitung separat mit vorhandenem
   `cs50_workflow execute ... --confirm` nach gültiger Admission.
4. **Abruf:** READ-ONLY `systemctl status`, `journalctl`, private JSONreports und
   `cs50_workflow status`; originale Ergebnisdateien gemäß Reportpfad/Hash. Vollständige
   Befehle im Betreiberleitfaden.
5. **Ohne SSH:** systemd hält Prozesse unabhängig von der Sitzung am Leben. Ein
   echter Hetzner-/Chromebook-/Logouttest wurde nicht durchgeführt. Keine Bootautomatik.
6. **Quellen:** exakt freigegebene CS50P-HTML/PDF-URLs unter offiziellen `/python/`-
   Pfaden auf cs50.harvard.edu/cdn.cs50.net, HTTPS443. Aktuell keine realen Grants
   erteilt; robots/konkrete Nutzungsprüfung vor jedem ersten Quellensatz erforderlich.
7. **Limits:** Download 0,5 CPU / 256 MiB / 32 Tasks / 32 MiB tmpfs / 600 s; Worker
   1 CPU / 1 GiB / 128 Tasks / 128 MiB tmpfs / 3600 s Dienstlaufzeit. Bestehender
   C18-Job 90 s Wall / 60 s CPU / 768 MiB Adressraum, ein aktiver und ein wartender
   Job; 1 MiB/Material, drei Materialien, 6 MiB Payload/Lauf, 64 MiB Archiv,
   512 MiB Jobs, mindestens 5 GiB freie Reserve. Persistente Hostquotas stehen aus.
8. **Tests:** siehe unverrechnete Lauftabelle und Rohlogs/XML der Übergabe.
9. **Noch Hetzner:** Account/Pfade/Rechte, CPython-/Wheelclosure, Units/Quotas, DNS/CA/
   HTTPSegress, Quellenfreigaben, VPNgeräte/Schlüssel/SSH-Rückfall testen; alles nur
   manuell und nach Freigabe. Coolify unverändert lassen.
10. **Blocker:** fehlender produktiver nativer C26-Admissionvertrag (Bestand bindet
    UI/API/Worker und Container), Quellen-/robotsfreigaben, positive Runtimeinstallation/
    Hostgrenzen-/VPNabnahme sowie Patchübernahme/Review. Pflichtgates bleiben aktiv.

**HOLD**, keine eigenständige Produktionsfreigabe. Die native Admissionanpassung muss
in einem getrennten überprüften Schritt die vorhandene Zustandsmaschine verwenden;
kein Abschalten, kein synthetisches Ersatzpermit, keine neue parallele Gateengine.
