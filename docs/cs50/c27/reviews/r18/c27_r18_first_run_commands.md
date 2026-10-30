# C27-R18 – Operatorbefehle für Integration und Erstlauf

Nur Schritt 1 ist ohne neue Freigabe rein lesend ausführbar. Schritte 2–10 wurden NICHT ausgeführt. Kopieren/Staging, Commit, Einrichtung des Testbranches, Push, Bootstrapintegration und CI-Lauf benötigen jeweils die entsprechende ausdrückliche Freigabe. Ein Prüfsummenabgleich ist keine Freigabe. Platzhalter nie ungeprüft übernehmen. Keine Befehle gegen Produktivserver.

## 1. Abschließende Integritätsprüfung (rein lesend)

```bash
set -euo pipefail
C27_SOURCE=/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-cs50-learning
C27_R18=/tmp/c27-r18-ci-integration-20261030Te5nvntjh
C27_BASE=a8af1d9372eb435d3e1331c33b047d21120d57c2
cd "$C27_R18"
sha256sum --check SHA256SUMS
python3 -B "$C27_R18/operator.py" verify
git --no-optional-locks -C "$C27_SOURCE" diff --check
git --no-optional-locks -C "$C27_SOURCE" diff --cached --exit-code
git --no-optional-locks -C "$C27_SOURCE" status --porcelain=v2 --branch --untracked-files=all
```

Bei jedem Hash-/Index-/HEAD-/Statusunterschied stoppen. Nicht automatisch neu manifestieren. R12–R17-Eingangsmanifestprüfung ist in input_verification.json dokumentiert; für Wiederholung aus deren Verzeichnissen `sha256sum --check SHA256SUMS` ausführen. Das externe Paket über den in /tmp/c27-r18-ci-integration-20261030Te5nvntjh.backup-verification.json bezeichneten Archivhash verifizieren, bevor es in einen dauerhaften Handoff übernommen wird. /tmp ist kein dauerhafter Handoff.

## 2. Kontrolliertes Kopieren und Staging nach gesonderter Freigabe

Ein eigener Kandidatenworktree schützt den bestehenden C27-Worktree. Der Pfad und beide Branchnamen müssen frei sein. Keine vorhandenen Branches oder Worktrees wiederverwenden/löschen.

```bash
C27_CANDIDATE=/home/OPERATOR/0_Portfolio_Projekte/Personal_Assistant-c27-r18-operator
test ! -e "$C27_CANDIDATE"
if git -C "$C27_SOURCE" show-ref --verify --quiet refs/heads/review/c27-r18-integration; then
  echo 'STOP: Kandidatenbranch existiert bereits' >&2
  exit 1
fi
git -C "$C27_SOURCE" worktree add -b review/c27-r18-integration "$C27_CANDIDATE" "$C27_BASE"
python3 -B "$C27_R18/operator.py" copy --candidate "$C27_CANDIDATE" --apply
python3 -B "$C27_CANDIDATE/ci/c27-r18/support/verify_payload.py" \
  --manifest "$C27_CANDIDATE/ci/c27-r18/support/r16_manifest.json" \
  --expected-manifest-sha256 93cef86c8a9a61204187afacbf28064a14678f89b7a9dbff6d9f40c3543feb92 \
  --root "$C27_CANDIDATE" --scope input --allow-source-extras
python3 -B "$C27_R18/operator.py" stage --candidate "$C27_CANDIDATE" --group C1 --apply
```

Das letzte allow-source-extras gilt nur für den Kandidatencheckout mit Git-/CI-Zusatzdateien. Der CI-Empfänger verwendet weiterhin exakte Mengenprüfung. Keine --allow-source-extras-Option für eine empfangene Inputkopie.

## 3. Diff und Commitgrenzen prüfen

```bash
python3 -B "$C27_R18/operator.py" verify-index --candidate "$C27_CANDIDATE" --group C1
git -C "$C27_CANDIDATE" diff --cached --check
git -C "$C27_CANDIDATE" diff --cached --stat
git -C "$C27_CANDIDATE" diff --cached
git -C "$C27_CANDIDATE" status --short
```

C1 exakt 34, C2 exakt 30, C3 exakt 19 Dateien. C4 exakt die Payloaddateien plus 7 R18-Berichte, Anzahl im Inventar. Indexblobhashes müssen mit den geprüften Dateien stimmen. Keine Zufallsdateien, Secrets, venv, pyc, Audits oder Stashes übernehmen. Jeder Bericht unter docs/cs50/c27/test-results bleibt ausdrücklich historisch. Volle Datenschutzprüfung durchführen; der Musterscan ist kein Geheimnisfreiheitsnachweis. Nach jeder Hookänderung erneut prüfen und bei geänderten manifestierten Hashes stoppen.

## 4. Commits ausschließlich nach ausdrücklicher Freigabe

Hooks müssen bereits in einer freigegebenen Umgebung bereitstehen; beim Commit keine automatische Hook-/Paketinstallation zulassen. Ist das nicht gewährleistet, vor dem Commit stoppen. Kein automatisches --no-verify.

```bash
# Erst nach Freigabe des geprüften C1-Diffs:
git -C "$C27_CANDIDATE" commit -m 'C27: integrate reviewed learning pipeline and regression fixtures'

python3 -B "$C27_R18/operator.py" stage --candidate "$C27_CANDIDATE" --group C2 --apply
python3 -B "$C27_R18/operator.py" verify-index --candidate "$C27_CANDIDATE" --group C2
git -C "$C27_CANDIDATE" diff --cached
# STOP: C2-Diff prüfen und Commitfreigabe erhalten.
git -C "$C27_CANDIDATE" commit -m 'C27: preserve pipeline documentation and historical test evidence'

python3 -B "$C27_R18/operator.py" stage --candidate "$C27_CANDIDATE" --group C3 --apply
python3 -B "$C27_R18/operator.py" verify-index --candidate "$C27_CANDIDATE" --group C3
git -C "$C27_CANDIDATE" diff --cached
# STOP: C3-Diff prüfen und Commitfreigabe erhalten.
git -C "$C27_CANDIDATE" commit -m 'C27: preserve integration inventory and review decisions'

python3 -B "$C27_R18/operator.py" stage --candidate "$C27_CANDIDATE" --group C4 --apply
python3 -B "$C27_R18/operator.py" verify-index --candidate "$C27_CANDIDATE" --group C4
git -C "$C27_CANDIDATE" diff --cached
# STOP: C4-Diff, GitHub-Schema und Datenschutz prüfen und Commitfreigabe erhalten.
git -C "$C27_CANDIDATE" commit -m 'C27: prepare hashed offline CI profiles and first-run evidence'

git -C "$C27_CANDIDATE" status --porcelain=v2 --untracked-files=all
git -C "$C27_CANDIDATE" log --oneline "$C27_BASE..HEAD"
git -C "$C27_CANDIDATE" diff "$C27_BASE..HEAD" --check
C27_EXPECTED_SHA=$(git -C "$C27_CANDIDATE" rev-parse HEAD)
```

Die vier STOP-Zeilen sind echte Freigabegrenzen. Den Block nicht ungeprüft als Gesamtskript ausführen. Der finale Kandidatenstatus muss sauber sein; Commitzahl vier und Commitinhalt prüfen.

## 5. Isolierten CI-Testbranch einrichten

```bash
if git -C "$C27_CANDIDATE" show-ref --verify --quiet refs/heads/c27-ci/r18-first-run; then
  echo 'STOP: CI-Testbranch existiert bereits' >&2
  exit 1
fi
git -C "$C27_CANDIDATE" branch c27-ci/r18-first-run "$C27_EXPECTED_SHA"
git -C "$C27_CANDIDATE" rev-parse refs/heads/c27-ci/r18-first-run
```

Kein Branchwechsel im ursprünglichen C27-Worktree. Der neue CI-Branch enthält exakt die geprüften Commits.

Default-Branch-Bootstrap ist eine gesonderte Voraussetzung: `.github/workflows/c27-r18.yml` bytegleich aus C4 über den vorgeschriebenen regulären Review-/PR-Prozess auf master integrieren. Keine dafür nötigen Mutationen sind durch R18 freigegeben. Erst nach separat genehmigtem und nachgewiesenem Bootstrap weitermachen. Ein alleiniger Testbranchpush registriert workflow_dispatch nicht. Keine automatische Umstellung auf push oder pull_request_target.

Nach Bootstrap und GitHub-Zugriffserlaubnis rein lesend prüfen:

```bash
gh api repos/rf-data/Personal_Assistant --jq .default_branch
C27_DEFAULT_WORKFLOW_SHA=$(gh api 'repos/rf-data/Personal_Assistant/contents/.github/workflows/c27-r18.yml?ref=master' --jq .sha)
test "$C27_DEFAULT_WORKFLOW_SHA" = "$(git -C "$C27_CANDIDATE" rev-parse "$C27_EXPECTED_SHA:.github/workflows/c27-r18.yml")"
gh workflow view c27-r18.yml --repo rf-data/Personal_Assistant --ref master --yaml
```

Erstes Kommando muss master liefern. Fehlende oder abweichende Workflowdatei blockiert. Actions-Zulassung, Repositoryrechte und volle Plattform-Syntaxakzeptanz separat bestätigen; actionlint nur nutzen, falls vorhanden.

## 6. Push ausschließlich nach gesonderter Freigabe

Vorher Remoteidentität prüfen; es muss rf-data/Personal_Assistant sein. Remote-Branch darf nicht existieren. Kein Force-Push.

```bash
git -C "$C27_CANDIDATE" remote get-url origin
git -C "$C27_CANDIDATE" ls-remote --heads origin refs/heads/c27-ci/r18-first-run
# STOP, falls bereits ein Remote-Branch existiert.
git -C "$C27_CANDIDATE" push origin refs/heads/c27-ci/r18-first-run:refs/heads/c27-ci/r18-first-run
C27_REMOTE_SHA=$(git -C "$C27_CANDIDATE" ls-remote --heads origin refs/heads/c27-ci/r18-first-run | cut -f1)
test "$C27_REMOTE_SHA" = "$C27_EXPECTED_SHA"
```

## 7. Manueller Actions-Lauf nach eigener Lauffreigabe

Voraussetzung: geprüfter offizieller Linux-amd64-Image-Digest, passende Python-3.12-bookworm-Metadaten, bestätigter Workflowbootstrap, volle Schemavalidierung und überprüfter Branch-SHA. Imageabfrage/-beschaffung ist eine neue ausdrücklich zu genehmigende Netzphase; in R18 wurde kein Digest geraten oder Image geladen.

```bash
C27_IMAGE='docker.io/library/python:3.12-slim-bookworm@sha256:<REVIEWED_64_HEX_DIGEST>'
[[ "$C27_IMAGE" =~ ^docker\.io/library/python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}$ ]]
gh workflow run c27-r18.yml --repo rf-data/Personal_Assistant \
  --ref c27-ci/r18-first-run --raw-field python_image="$C27_IMAGE"
gh run list --repo rf-data/Personal_Assistant --workflow c27-r18.yml \
  --branch c27-ci/r18-first-run --event workflow_dispatch --limit 10 \
  --json databaseId,headSha,event,status,createdAt,url
```

Run-ID manuell anhand SHA, Ereignis und Startzeit auswählen; niemals blind den neuesten Lauf übernehmen.

```bash
C27_RUN_ID='<CONFIRMED_NUMERIC_RUN_ID>'
gh run view "$C27_RUN_ID" --repo rf-data/Personal_Assistant \
  --json headSha,event,headBranch,status,conclusion,url
C27_RUN_SHA=$(gh api "repos/rf-data/Personal_Assistant/actions/runs/$C27_RUN_ID" --jq .head_sha)
C27_RUN_ATTEMPT=$(gh api "repos/rf-data/Personal_Assistant/actions/runs/$C27_RUN_ID" --jq .run_attempt)
test "$C27_RUN_SHA" = "$C27_EXPECTED_SHA"
gh run watch "$C27_RUN_ID" --repo rf-data/Personal_Assistant --exit-status
```

Kein automatischer Wiederholungslauf bei Fehlern. OOM, Paketfehler, Hashabweichung oder Schemafehler anhand der vorhandenen Evidenz prüfen; keine Assertions/Selektionsliste/Limits absenken.

## 8. JUnit und Sicherheitsberichte abrufen

```bash
C27_RESULTS="$HOME/codex-logs/c27rollout/handoff/r18-first-run-$C27_RUN_ID-attempt-$C27_RUN_ATTEMPT"
test ! -e "$C27_RESULTS"
mkdir -m 700 -p "$C27_RESULTS"
gh run download "$C27_RUN_ID" --repo rf-data/Personal_Assistant --dir "$C27_RESULTS"
gh run view "$C27_RUN_ID" --repo rf-data/Personal_Assistant --log > "$C27_RESULTS/workflow.log"
```

Erwartet: drei c27-r18-<PROFILE>-<RUN_ID>-<ATTEMPT>-Verzeichnisse. In jedem Jobidentität, Jobbericht, Paket-/Installationsnachweise; je Collection-/Ausführungskontext command.json, collected.json, outcomes.json, junit.xml und Container-/Sicherheitsberichte. Namespace hat zwei Kontexte. Fehlendes Artefakt/Report gilt als INCOMPLETE. Ein Securitybericht ist kein Vulnerability-Scan.

## 9. Tatsächlich ausgeführte IDs gegen die 105 Fälle vergleichen

```bash
python3 -B "$C27_CANDIDATE/ci/c27-r18/support/compare_results.py" \
  --artifacts "$C27_RESULTS" \
  --manifest "$C27_CANDIDATE/ci/c27-r18/support/r16_manifest.json" \
  --sha "$C27_EXPECTED_SHA" --run-id "$C27_RUN_ID" --run-attempt "$C27_RUN_ATTEMPT" \
  > "$C27_RESULTS/nodeid-comparison.json"
```

Nur Exit 0 und CI_EVIDENCE_VERIFIED bestätigen den Abgleich. Das Skript prüft alle 105 Call-IDs exakt einmal, jede setup/call/teardown-Phase passed, keine Skip-/xfail-Ergebnisse, Collection, JUnit, SHA/Run-ID/Versuch und getrennt 3+4 Namespacefälle. Danach Sicherheits-/Ressourcen-/Installationsberichte menschlich prüfen. Alle Ergebnisdateien anschließend mit einem eigenen SHA256SUMS sichern; keine behauptete Testfreigabe bei bloßem Count 105 oder Collection-only.

## 10. Evidenz in Gateentscheid zurückführen

In einem separat freigegebenen Dokumentationsschritt den aktuellen Gateentscheid neu verfassen: Run-URL, Revision, Image-Digest, Profilversionen, 105-ID-Vergleich, 3+4 Namespaceergebnisse, JUnitstatus, OOM/Timeouts, Ressourcen und Hashmanifest eintragen. Bestehende R18-Vorbereitung als Historie behalten. Bei Teil-/Fehllauf betroffene Testgates offen lassen und Grund dokumentieren. Keine automatische Produktionsfreigabe.

Neue Nachweise durch regulären Reviewprozess auf master sichern. Erst nach verifizierter Integration, sauberem Kandidatenworktree und geklärter Nutzung darf ein gesonderter Cleanup ausschließlich der dann task-eigenen temporären Artefakte nach AGENTS.md erfolgen. R18 führt keine dieser Mutationen aus.
