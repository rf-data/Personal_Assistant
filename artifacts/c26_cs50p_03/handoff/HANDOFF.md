# C26-CS50P-03 – persistente Übergabe

Status **HOLD**. Kein Produktivfix, Livebetrieb oder Merge freigegeben.
Ausgangsbasis/gesicherter Nativecommit:
`2f2b410f41cd4db4e26075b891a03c6cb1ff0cd6` auf feat/c26-cs50p-mvp.
Gitverwaltung hier schreibgeschützt; kein neuer Liefercommit/Push/PR.

Enthalten: neue SQLite-Mehrprozesstests (final 5 passed / 1 failed), zusätzlicher
Resultatabruf in einem neuen Prozess, fünf neue Betreiber-/Befunddokumente und
sechs Verweise/Nachträge in bestehenden Dokumenten. Productsrc, scripts und
Units sind unverändert. Breite Regression: 284 passed. Resume 10/10 und native
CLI 5/5 bestanden. Vorläufe und Fehlerraten siehe results.json und Rohlogs.
README gehört zum vorherigen Arbeitsstand und bleibt bytegleich unangetastet.

## Dateigrenzen und Prüfsummen

`delivery-files.txt` enthält exakt die Patchnutzlast aus Test-/Dokumentations- und
Belegdateien (ohne vorherige README-Änderung). `all-files.txt` ergänzt die
Paketmetadaten und Patchhüllen zur vollständigen Dateiliste. `source-checksums.sha256`
bindet Nutzlast und ausgewählte Metadaten, ausgenommen sich selbst. Diese Dateien sind Paketmetadaten,
keine rekursive Hashbindung. `checksums.sha256` bindet die getrennten Patches.
`package-validation.json` protokolliert tatsächliche Anwendung gegen einen
HEAD-Archivexport, Reversecheck und Bytevergleich; kein Testfixturecommit.

Patches:

- 01-sqlite-tests.patch: synthetische Diagnose-/Regressionstests, keine Änderung des Store.
- 02-native-reconnect.patch: zusätzliche Prüfung der persistenten Resultate.
- 03-documentation.patch: neue und ergänzte Betreiber-/Befunddokumente.
- 04-evidence.patch: erhaltene Test-/Umgebungs-/Git-/Syntax-/Härtungsbelege.

Rohlogs/JUnit inklusive ursprünglicher Whitespacebytes liegen zusätzlich in
`../raw-evidence.tar.gz`, gebunden an `../raw-evidence-manifest.json`. Die
unkomprimierten lokalen Belege bleiben erhalten; Git erhält das geprüfte
Binärarchiv und die kuratierten JSON-/Quellenbelege. READ-ONLY:
`tar -tzf artifacts/c26_cs50p_03/raw-evidence.tar.gz`. CHANGE, optionales Entpacken:
`tar -xzf artifacts/c26_cs50p_03/raw-evidence.tar.gz -C NEW_PRIVATE_DIRECTORY`.
Voraussetzung: neuer leerer privater Zielordner; Effekt: synthetische Belegkopien;
Rückweg: bis Review erhalten. Keine Extraktion in einen vorhandenen Datenpfad.

Patchdateien, diese Hülle, Prüfsummen und Paketvalidator werden nicht in ihre
eigenen Patches eingebettet. Rohlogs können lokale synthetische /tmp-Pfade
enthalten, keine produktiven Daten/Secrets. Der alte README-Diff ist ausschließlich
als preexisting-readme.patch gesichert, nicht auf README angewendet.
Die vier Patchdateien und checksums.sha256 bleiben als lokale Übergabehülle
erhalten; sie werden mit den folgenden Befehlen nicht zusätzlich als Textpatches
eingecheckt. Alle eigentlichen Quellen, dauerhaften Berichte, Rohbelege im
Binärarchiv und die Anwendungsvalidierung werden dagegen gestaged. So bleiben
ursprüngliche Whitespacebytes von Patchkontexten außerhalb der Quelltextprüfung.

## Betreiberbefehle im bestehenden Featureworktree

READ-ONLY, Voraussetzungen und Integrität prüfen:

```sh
cd /home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50p-mvp
git status --short --branch
git rev-parse HEAD
git remote -v
sha256sum -c artifacts/c26_cs50p_03/handoff/checksums.sha256
sha256sum -c artifacts/c26_cs50p_03/handoff/source-checksums.sha256
git diff --check
git diff -- README.md
```

Erwartet: Branch feat/c26-cs50p-mvp, Ausgangs-HEAD 2f2b410, origin
rf-data/Personal_Assistant, alle Hashes OK, README ausschließlich vorheriger Diff.
Bei anderem Stand zuerst reviewen, nicht blind apply/committen. Patches sind im
bereitgestellten Arbeitsbaum bereits angewendet: **nicht erneut anwenden**.
Ein separater sauberer Export kann sie in nummerierter Reihenfolge übernehmen;
package-validation.json weist genau diesen Test nach.

CHANGE, erst in einer Umgebung mit regulär beschreibbarer Gitverwaltung und nach
Dateireview: Staging und Commit. Voraussetzung: keine anderen gestagten Dateien;
READ-ONLY `git diff --cached --name-only` muss vorher leer sein. Effekt: nur die
kuratierte Tasklieferung und ihre Metadaten werden committed, keine README.
Rückweg vor Commit: gezielt diese Dateien mit git restore --staged entstagen;
Arbeitsbaum bleibt erhalten. Nach Commit bei Fehlern separater Korrekturcommit,
kein Reset/Forcepush.

```sh
git add --pathspec-from-file=artifacts/c26_cs50p_03/handoff/delivery-files.txt
git add artifacts/c26_cs50p_03/handoff/HANDOFF.md artifacts/c26_cs50p_03/handoff/build-package.py artifacts/c26_cs50p_03/handoff/delivery-files.txt artifacts/c26_cs50p_03/handoff/all-files.txt artifacts/c26_cs50p_03/handoff/package-validation.json artifacts/c26_cs50p_03/handoff/source-checksums.sha256
```

READ-ONLY vor Commit:

```sh
git diff --cached --check
git diff --cached --stat
git diff --cached --name-only
```

CHANGE: `git commit -m "test(cs50p): reproduce SQLite contention and prepare private Hetzner runbooks"`.
Voraussetzung: Dateiliste stimmt, README nicht gestaged; Effekt: dauerhafter
Featurecommit, weiter HOLD. Rückweg: regulärer Korrekturcommit, Arbeit erhalten.

READ-ONLY vor Push:

```sh
git log -1 --oneline
git status --short --branch
git ls-remote origin refs/heads/feat/c26-cs50p-mvp
```

CHANGE: `git push origin HEAD:refs/heads/feat/c26-cs50p-mvp`.
Voraussetzung: unveränderte Remote-Bindung, erwarteter Branch, ausschließlich
normaler Fast-forward nach Review des Commits. Effekt: GitHub-Sicherung;
Rückweg: Fehler separat korrigieren, kein Forcepush/Branchlöschen. Bei Ablehnung
anhalten und Remoteänderungen prüfen. Kein automatischer Merge auf master.

READ-ONLY: neue Commit-SHA lokal/live vergleichen. Anschließend reguläres PRreview
organisieren. Masterintegration bleibt einem späteren ausdrücklich erlaubten
Schritt vorbehalten. Vorher Branch/Worktree behalten. Task hat keine temporären
Gitbranches/Worktrees erstellt; nichts zu löschen. Synthetische Belege bleiben
bis Review erhalten. Keine fremden Arbeitsstände oder Daten bereinigen.
