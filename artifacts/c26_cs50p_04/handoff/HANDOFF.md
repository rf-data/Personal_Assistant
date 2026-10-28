# C26-CS50P-04: geprüfte Patchübergabe

**HOLD**. Keine Produktionsfreigabe, keine echte Installation oder Kursdownloads.
Basis: `81db9ed3f5fc7e0c3d6952b438f015ae6521af3c`, lokal und live auf
`feat/c26-cs50p-mvp` gesichert. Dieser bereitgestellte Worktree ist Detached HEAD.
Gitmetadata ist explizit read-only; ausschließlich neue Taskdateien und eine
geprüfte Patchhülle, kein Commit/Push/PR/Defaultbranchmerge in dieser Umgebung.

[Betreiberablauf](../../../docs/deployment/cs50p_download_only_operator_guide.md),
[Validierung und offene Gates](../../../docs/deployment/cs50p_download_only_validation.md).

`delivery-files.txt` ist die vollständige eigentliche Lieferdateiliste. Der Patch
enthält Source, Tests, Dokumentation, finale Test-/Basisbelege und statische
Handoffdateien. Patchhülle, Prüfsummen und `package-validation.json` liegen
außerhalb ihres eigenen Patches. `install-tests.xml` ist ein lokaler Zwischenlauf
und gehört nicht zur dauerhaften Lieferung. Der finale Lauf hat 102 passed /
1 externen Skip. Keine Neuinterpretation des offenen SQLitebefunds.

READ-ONLY, im bestehenden Taskworktree:

```sh
git status --short --branch
git rev-parse HEAD
sha256sum -c artifacts/c26_cs50p_04/handoff/checksums.sha256
sha256sum -c artifacts/c26_cs50p_04/handoff/source-checksums.sha256
cat artifacts/c26_cs50p_04/handoff/package-validation.json
```

Alle neuen Dateien sind hier bereits vorhanden: **Patch nicht erneut anwenden**.
Der Validator hat ihn gegen einen neuen Archivexport der exakten Basis tatsächlich
vorwärts angewendet, Bytes und Executable-Modi verglichen und Reversecheck geprüft.
Keine Testfixture mit Gitinit, keine Gitmetadataänderung erforderlich.

CHANGE, später in einem sauberen beschreibbaren Taskbranch/Worktree auf derselben
Basis, nach normalem Review; Effekt: dieselben Dateien dort anlegen. Prüfsummen
vorher prüfen, Patchpfad absolut setzen. Bei vorhandenen Lieferdateien nicht applyen.

```sh
git apply --check --whitespace=error-all /ABSOLUTE/c26-cs50p-04.patch
git apply --whitespace=error-all /ABSOLUTE/c26-cs50p-04.patch
git add --pathspec-from-file=artifacts/c26_cs50p_04/handoff/delivery-files.txt
git diff --cached --check
git diff --cached --stat
git commit -m "feat(cs50p): prepare offline download-only installation pilot"
```

Vorher muss der Index leer sein; nur eigene Lieferdateien stagen. Exakten neuen
Commit regulär sichern, PRreview und Defaultbranchintegration nach `master`
durchführen, Schutzregeln beachten. Kein Squash/Commitvergleich allein als
Integrationsbeweis; reale Dokument- und Sourceinhalte prüfen. Der Patchvalidator
kann nach Integration nicht unverändert erneut laufen, weil er die Ausgangsbasis
und ausschließlich neue Dateien prüft.

Dieser Auftrag erzeugte keine temporären Gitbranches oder zusätzlichen Worktrees.
Der bereitgestellte Worktree und der fremd ausgecheckte Featurebranch werden
wegen ausstehender Integration vollständig erhalten. Keine anderen Artefakte,
Stashes, Daten, Venvs oder historischen Branches löschen. Abschluss des gesamten
Repository-Lifecycles bleibt bis zur Integration pending. Positiver Frozeninstall
und echter Ubuntu-/systemd-255-Test fehlen; auch ein Commit allein hebt HOLD nicht auf.
