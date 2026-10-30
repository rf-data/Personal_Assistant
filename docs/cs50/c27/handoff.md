# C27 Übergabe und Wiederholung

Die Implementierung und Berichte liegen ausschließlich im vorhandenen C27-
Worktree/Branch. Kein Push, Merge, Default-Branch-Update, externer LLM-Aufruf,
neuer Kursdownload oder Produktionswechsel wurde ausgeführt.

## Einstieg

- [Status und Ergebnis](README.md)
- [Konflikt-/Integrationsplan](integration_plan.md)
- [Architektur und selektierte 07/08-Komponenten](architecture_and_components.md)
- [Testmatrix](test_matrix.md) und [Validierung](validation.md)
- [Phasen 3/4, Week 1, Weeks 2–9, Kursadapter und CS50 AI](rollout_plan.md)
- [Realdatennachweis ohne Rohdaten](real_data_acceptance.v1.json)
- [Summarizer-Herkunft](summarizer_integration.v1.json)
- [Dateimanifest des C27-Stands](handoff-files.v1.json)

Die Originalübergabe unter `docs/lecture_summary/` bleibt als historische
C26-LS-01-Evidenz erhalten; deren Testzahlen sind nicht die neuen C27-Ergebnisse.
Die nachträgliche Fake-Label-Korrektur ist im C27-Nachweis ausgewiesen.

## Reproduzierbare lokale Prüfung

Ein geeigneter Python-3.12-Interpreter braucht das Offline-Testprofil und für
AppTests zusätzlich Streamlit. In dieser Sandbox verwendet `/tmp/c27-test-env`
eine eigene venv mit ausschließlich lesenden `.pth`-Verweisen auf vorhandene
Paketinstallationen. Fremde venvs wurden nicht verändert. Für einen dauerhaften
Reviewer-Lauf eine eigene geprüfte Umgebung bereitstellen; die `/tmp`-Umgebung
ist kein deploybares Paket und keine neue Dependency-Lockdatei.

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/c27-test-env/bin/python -m pytest \
  -p tests.offline_guard tests/test_lecture_summary.py \
  tests/test_lecture_summary_ui.py tests/test_c27_reviewed_week.py -q
```

Ohne Opt-in wird der echte lokale Test übersprungen. Expliziter reiner
Offline-Echtdatenlauf (hier durch den Auftrag autorisiert):

```bash
PYTHONDONTWRITEBYTECODE=1 \
C27_WEEK0_REVIEW_ROOT=/home/OPERATOR/cs50p-week0-review-RbZ8OQqe \
/tmp/c27-test-env/bin/python -m pytest -p tests.offline_guard \
  tests/test_c27_reviewed_week.py --run-external -q
```

CLI-Verarbeitung aller vier lokalen Rohdateien mit ausdrücklich ausgewähltem
Functions-Transkript für den Fake-Smoke:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/c27-test-env/bin/python -m scripts.c27_reviewed_week \
  --review-root /home/OPERATOR/cs50p-week0-review-RbZ8OQqe \
  --output /tmp/c27-real-week0-acceptance \
  --fake-summary \
  --material-id week_material:191f887faf9bf853e27e6e3bbdeedf2744f0629150c757b7f617589ed82ee0ab
```

Der Ausgaberoot darf nicht mit dem Reviewroot überlappen. Bestehende Ausgaben
müssen privat und konsistent sein; keine Rechte werden automatisch repariert.
Wiederholung prüft Eingabe- und Ausgabehashes. Quellcodeänderungen erzeugen einen
neuen Verarbeitungsschlüssel; alte Ausgaben bleiben als Historie erhalten.
Ohne `--fake-summary` wird ausschließlich lokal verarbeitet. Ohne `--material-id`
werden alle verarbeiteten Quellen ausgewählt; bei den realen HTML-Units greift
das Chunk-Limit, und der Bericht meldet dies als Blocker pro Unit. Keine Auswahl
wird heimlich gekürzt. Die CLI bietet keinen echten Provider-/Downloadmodus.

Der integrierte Streamlit-Einstieg ist `lecture_summarizer_app.py`; Konfiguration
und Bedienung stehen in `docs/lecture_summary/operations.md`. Ein manueller
Browserlauf wurde in dieser Fortsetzung nicht ausgeführt.

## Ergebnisse, Aufbewahrung und Integration

Verarbeitungssnapshots/Kataloge/Quittungen: unter
`/tmp/c27-real-week0-acceptance/processing/<input-und-revision-hash>/`.
Fake-Läufe, Rohantworten, Reviewstatus und Exporte: unter
`/tmp/c27-real-week0-acceptance/summaries/runs/<run-id>/`.
Diese Ausgaben und etwaige frühere Fehlversuche sind lokale Testdaten,
keine Produktionsartefakte. Private Rohdaten werden nicht ins Repository gepackt.
Die Integrationstestkopie unter `/tmp/c27-summary-isolation-*` ist ein Datei-
Export, kein Git-Worktree. Testumgebung und temporäre Ausgaben bleiben für
Nachprüfung erhalten; ihre Löschung ist nicht Teil des Git-Cleanups.

**Integrationsabschluss ausstehend:** AGENTS.md verlangt dauerhafte Berichte in
`master` über den regulären PR-/Reviewprozess. Das task-spezifische Push-/Merge-
Verbot verhindert diesen Schritt. Deshalb keine Behauptung einer abgeschlossenen
Integration in `master` und keine Branch-/Worktree-Bereinigung. Auch Live-Git/PR-
Status wurde hier nicht abgefragt. Der bestehende C27-Branch und Worktree bleiben
notwendig erhalten; alle fremden/historischen Worktrees, Branches und Stashes
bleiben bestehen. Es wurden keine temporären Git-Artefakte angelegt oder entfernt.

Nächster erlaubnispflichtiger Integrationsschritt außerhalb dieses Auftrags:
C27-Diff und Berichte reviewen, unter gesonderter Autorisierung committen/PR
vorbereiten und den erforderlichen Reviewprozess einhalten. Erst nach erlaubter,
verifizierter Integration entscheidet die Lifecycle-Regel über task-eigene
Artefakte; vorbestehende MAINT-Bestände benötigen weiterhin Einzelprüfung.

Ein reviewbarer Gesamtdiff wird zusätzlich unter
`/tmp/c27-learning-handoff.patch` bereitgestellt, mit benachbarter `.sha256`-
Datei. Er basiert auf `a8af1d9` und enthält Code, Fixtures und dauerhafte Berichte.
Das Dateimanifest bindet die Inhalte unabhängig von temporären Dateinamen.
