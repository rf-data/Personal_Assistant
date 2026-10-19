# MAINT-01-Delta und Dokumenterhalt

MAINT-01 ist ein datierter Snapshot, keine Sollzahl. Seine Dateien unter
[docs/audit/maint01](../maint01/README.md) und
[Unresolved-Metadaten](../../_unresolved_imports/maint01/README.md) bleiben unverändert.
Aktuelle Basis: Backend `ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0`, UI
`90816a1578bcf67739ee9acaa483c1635aa0c44b`.

| Bestand | MAINT-01 | MAINT-02 vor Eigenzugang |
| --- | ---: | ---: |
| Lokale Branches | 112 | 114 |
| Live Remote-Branches | 33 | 33 |
| Branchzeilen | 145 | 147 |
| Registrierungen | 44 | 46 |
| Gültige / ungültige Worktrees | 34 / 10 | 36 / 10 |
| Cached Trackingrefs | 44 | 46 |
| Zwei Backend-Stashes / UI | 2 / 0 | 2 / 0 |
| Historische Dokumentversionstupel | 452 | 452 wiederverwendet |

Lokale Neuzugänge: `docs/maint01-inventory-consolidation` und
`docs/pm02-project-operationalization`, jeweils mit eigenem gültigem Worktree.
Remote neu: PM-02; Remote weggefallen seit MAINT-01: PM-01. Kein solcher Ref wurde
von MAINT-02 entfernt. Unter unverändert benannten Branchzeilen änderte sich nur
live Backend `master`: `4c057ae33d41ba98e227879cc8a51283338e4a0b` →
`ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0` nach externen Merges #92/#93.
Alle ursprünglichen lokalen Branch-SHAs unverändert.

Die alten fünf `active`-Zeilen heißen jetzt `protected_active`; zusätzlich sind
Primärcheckout, dirty HTML-Parser, Completion-Audit, neuer MAINT-01-Branch und
PM-02-Scopes geschützt. Alte effektive `unmerged_unique_work=24` wird 23, weil
`fix/cs50-html-semantics` wegen dirty Worktree geschützt ist; sein intrinsischer
Graphbefund bleibt sichtbar. Stale 8 → 7 wegen dirty Completion-Audit. Die 41
`merged_with_extra_commits` bleiben 41; ihre genaue Identität steht im TSV.

## Commit, Patch, Tree und Bedeutung getrennt

41 effektive Branchzeilen besitzen Zusatzcommits trotz gemergtem zugeordnetem PR.
33 haben denselben Tree wie dessen **tatsächlicher gemergter Head**, acht einen
abweichenden Tree. Bei 34 Zeilen findet `git cherry <live-default> <head>` mindestens
einen `-`-Patch, bei sieben keinen. Das heißt nicht, dass alle Zusatzcommits einer
Zeile patchäquivalent sind; sämtliche `+`/`-`-Commit-IDs stehen im Branch-TSV.
PRs mit Squash/abweichender Historie können einen nicht-ancestralen Head besitzen;
`merged_head_in_default=false` bleibt deshalb ausdrücklich erhalten.

Historische funktionale Relevanz ist `not_assessed`, ebenso welche eigenständigen
Dateien fachlich behalten werden müssen. Keine heutige Obsoleszenz allein aus
Tree-/Patchgleichheit behauptet. `paths_absent_from_live_default` ist ein
Treeunterschied, kein Beweis einer verlorenen oder einzigartigen Datei. Ein späteres
Archiv muss Commitidentitäten und fachlich benötigte Fassungen erhalten.

## Dokumente und sensible Metadaten

452 historische Versionstupel: 293 byteidentische (279 gleicher, 14 anderer Pfad),
136 abweichende vorhandene Pfade und 23 damals fehlende Pfade. Diese historischen
Vergleiche werden **nicht** als neue Live-Semantikprüfung ausgegeben. BR-Zeilen
verknüpfen alte B-/D-IDs, Pfad/SHA und Status. Vier untracked Dokumentmetadaten,
neun Envfamilienmetadaten und 35 Unresolved-Fälle bleiben erhalten; keine Inhalte
neu eingelesen und keine weiteren Dokumente importiert.

- Historischer ADR aus #88: aktueller Default-Gitblob identisch zum Draftursprung.
  [ADR](../../architecture/human_review_workflow_adr.md), MAINT-01-SHA256
  `3ef6f647fc5730ed9e357e565a9f9aa33f5e9148c0d90b4d7943f0aca5c6b6c2`,
  17.436 Bytes. Seine historischen Statusaussagen nicht als heutigen Runtimevertrag
  umdeuten. Draft #88 bleibt offen.
- Acht #89-JSONdateien in r1/r2: gleiche Gitblobs wie aktuell integriert. Keine neue
  Kopie und keine Realabnahme; Draft #89 bleibt offen.
- PM-01: #92 gemergt; eigener Bestand und Worktree bleiben geschützt. MAINT-01:
  #93 gemergt, aber ebenfalls kein Löschauftrag für dessen Arbeitsumgebung.
- #72: eigenes Draftbundle und offene Quellbindungs-/Realpilotfragen behalten.
  Nicht aufgrund heutiger Implementierungen als erledigt schließen oder entfernen.
- C24-06-A inklusive UI-Abhängigkeit unverändert; fünf untracked Backenddateien
  nicht öffnen, umbenennen, kopieren oder als gesichert behaupten.

Exakt die bereits bekannten acht Backend-Envfamiliennamen und UI-`.env` erneut nur
per Dateimetadaten/Tracking geprüft: vorhanden und Modus `0644`; UI-`.env` versioniert.
Keine Inhaltsprüfung, kein Secretfund behauptet. Separate Betreiberprüfung zu
Zugriffsrechten, Versionshistorie und zulässigem Ablageort empfehlen; keine
Credentialrotation oder chmod/löschen durch MAINT-02. Historische Gitbackups können
sensible Inhalte enthalten und benötigen einen privaten autorisierten Speicherort.

## Tracking und Stashes

46 Cachezeilen: 30 live gleich, zwei verschieden (alte Defaulttrackingrefs), 14
nicht in der Live-Branchliste. MAINT-01: 44 = 30 gleich + 2 verschieden + 12 nicht
live. Kein Trackingref gefetcht/pruned/aktualisiert. Upstreamkonsumenten pro TR-ID.

Unverändert, ohne Inhalt zu öffnen:

- Backend `de887a419c73719e00fdbe1c80bfe5e4de9f7d84`, 13.10.2026 20:35:21 +02:00.
- Backend `660622b548f13f98a5aa1246d543409ce00ec0a2`, 30.07.2026 17:53:25 +02:00.
- UI: keine Stashes. Kein Drop/Apply/Pop oder Inhaltsimport.
