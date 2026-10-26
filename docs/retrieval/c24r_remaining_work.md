# C24-R verbleibende Arbeit und Übergabe

## Technische Nachprüfung

1. In einer autorisierten lokalen Umgebung mit erlaubten Loopbacksockets die
   beiden Tests `test_content_search_http.py::test_real_local_http_server_and_process_restart`
   und `test_c24r_integration.py::test_actual_loopback_job_to_search` ausführen.
   Zusätzlich die bestehende `test_content_http.py`-Suite erneut prüfen. EPERM
   wurde auf unverändertem `4c057ae` reproduziert; hier kein Socketerfolg behauptet.
2. Die 43 Socket-Fixtureerrors gemäß
   [Validierungsprotokoll](c24r_integration_validation.md) in derselben freigegebenen
   lokalen HTTPumgebung nachprüfen; keine Timeout-/Securitylockerung. Alle übrigen
   590 ausgewählten Fälle einschließlich nativer PDF-Lifecyclefälle bestanden.
3. Nach Bereitstellung passender Offlinepakete im vollständigen Rootlockprofil
   reproduzieren. Die verwendete Cachevenv erlaubt keine Behauptung vollständiger
   Sync-/Installationsreproduzierbarkeit.
4. Cross-Repo-UIintegration auf dem tatsächlich gewählten Backendziel prüfen.
   API-/Schemaänderungen sind dokumentiert, UIcode wurde nicht verändert.

## Loviscach

Betreiberfreigabe für ausgewählte Originaldateien und private Rootzuordnung,
Source-/Materialversionen/Hashes und unabhängige Reviewer erforderlich. Die
konkreten Freigabelücken stehen im
[Inventar](../evaluation/loviscach_gold_candidate_inventory.md). Danach operative
Loviscach-Kursbindung festlegen, höchstens 30 thematisch vielfältige Kandidaten
aus Originalen annotieren, Validator/Reviewexport verwenden und Menschen prüfen
lassen. Erst danach vorhandene C23-/C24-/C11-Verträge auswerten. Keine automatischen
Goldlabels, Qualitätsraten, Downloads oder Realimports aus diesem Auftrag ableiten.

## Manuelle Gitübergabe

Der gemeinsame Git-Speicher ist read-only. Unter `/tmp/c24r-delivery/` liegen
`c24r-completion.patch`, `files.sha256`, `artifacts.sha256`, die drei Teilpatches
und deren Überprüfungsprotokoll. Der Basiscommit steht in jedem Übergabebeleg.
Die Patchdateien enthalten ausdrücklich auch alle neuen Dateien. Das Lieferpaket
ist ein separates Artefakt und enthält sich nicht selbst rekursiv.

Bei später erlaubtem Git-Schreibzugriff ausschließlich im C24-R-Worktree bzw.
einem dafür neu vorgesehenen sauberen Checkout vorgehen. Vor Anwendung Basis
`4c057ae33d41ba98e227879cc8a51283338e4a0b`, leeren Status und fehlenden
Zielbranchkonflikt prüfen. Bestehende bearbeitete C24-R-Dateien nicht doppelt
patchen. Vollpatch oder Teilpatchfolge verwenden, niemals beides.

```sh
# Im sauberen C24-R-Checkout mit oben geprüftem Basiscommit:
git switch -c feat/c24-retrieval-completion
git apply --check /tmp/c24r-delivery/01-search-http.patch
git apply /tmp/c24r-delivery/01-search-http.patch
git add scripts/job_control.py src/content_store/search_http.py \
  src/content_store/search_models.py src/job_control/http.py \
  tests/test_content_search_http.py docs/api/content_search* \
  docs/architecture/content_fts_implementation.md
git add -f -- docs/api/examples/content_search_v1.schema.json \
  docs/api/examples/content_search_v1.synthetic.json
git commit -m 'feat: expose authorized C24 search through C16'
git apply --check /tmp/c24r-delivery/02-index-jobs.patch
git apply /tmp/c24r-delivery/02-index-jobs.patch
# Ausschließlich die Dateien des zweiten Teilpatches stagen und lokal committen.
git apply --check /tmp/c24r-delivery/03-candidates-validation.patch
git apply /tmp/c24r-delivery/03-candidates-validation.patch
sha256sum -c /tmp/c24r-delivery/files.sha256
# Ausschließlich die übrigen manifestierten Dateien stagen und lokal committen.
```

Alternativ Vollpatch in einem Schritt anwenden und vollständig manifestierte
Änderung nach Review lokal committen. Bevor ein Review-PR ausdrücklich autorisiert
wird, Tests/Status/Dateimanifest prüfen und gegen den aktuellen Zielbranch die
bereits gemergten #124/#125 berücksichtigen: diese Funktionen nicht doppelt
cherry-picken. Kein Push/PR/Issueupdate, Merge, Force-Push oder Produktionsschritt
wurde ausgeführt. Keine fremden Worktrees löschen oder bereinigen. C26 HOLD.
