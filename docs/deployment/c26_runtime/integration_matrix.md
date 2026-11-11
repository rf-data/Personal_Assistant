# PR-Integration und Freigabegrenzen

Live geprüft am 23.10.2026: Backend-Master `e502aa9…`, UI-Main `e4be7a2…`.
Alle fünf PRs offen und Draft, GitHub meldet konfliktfrei mergebar. Keine
eingereichten Reviews, keine Inline-Kommentare und keine Check-Runs in der
Eingangsprüfung. Fehlende Checks sind kein grünes CI. Die vollständigen SHAs
stehen in `validation.v1.json`; #157 erhält nur eigene Folgecommits.

| PR | Technisch reviewfähig / Git-mergefähig | Abhängigkeit und Betriebswirkung | Betriebsintegration / Deployment |
| --- | --- | --- | --- |
| #156 | Ja / ja | Optionale Imports, eng begrenzter SQLite-Setup-BUSY-Retry; kein Transaktions- oder Jobreplay | Review zuerst; ursprünglicher unklassifizierter Fehler nicht nachträglich als BUSY erklärt |
| #149 | Ja / ja | HTML-Aggregation/Quality; Outputs und Qualitätsentscheidungen können sich ändern | Nach #156 auf aktuellem Master prüfen; echte alte Pilotvergleiche nur soweit bereitgestellt, keine neuen Downloads |
| #148 | Ja / ja | Gatevertrag, Settings und zusätzliche Lease-/Queuebedingungen; bestehende Queue erforderlich | Nach #149; realer Coolifydriver und Bootstrapfreigabe fehlen weiterhin |
| #157 | Ja / ja | Bestehende drei Rollen, zwei kleine Compose-Kompatibilitätskorrekturen, gesperrte Config, Inventur und Abnahmekette; neue rein lesende Offline-Preflight-CLI, eigener Runtime-Bind, deaktivierte Ein-Job-/Ein-Materialvorlagen | Nach #148; Backend von Dockerfile auf Compose adoptieren ist eine gesonderte Änderung mit Nachweisen |
| UI #20 | Ja / ja | HTTPS-/Deploymentdokumentation; geschützter Launcher bereits in #19, laufendes Image historisch | Gesondert abstimmen, bestehende Application/Service `streamlit` erhalten; kein additives `ui`-Overlay |

Die unveränderten #156/#149/#148-Diffs sind im eigenen isolierten Worktree auf
#155 angewendet. Dessen Produktdateien bleiben unverändert; die neuen Tests
prüfen diese Kombination. Die finale lokale Composekorrektur erhält einen
gesonderten Definitionslauf. UI-Main + #20 wird separat geprüft. Ein schmutziger
Kompatibilitätsworktree oder virtuelle GitHub-Merge-SHA ist kein Deploymentcommit.

**Review-GO ist keine Mergefreigabe.** Manual deployments only ist bestätigt;
ein normaler Git-Push/Merge soll dadurch keinen Deploy auslösen. Zusätzliche
API-/Preview-/Webhook-/Registry-/Scheduler-/manuelle Auslöser und Rechte sind
noch nicht vollständig erfasst. Keine Merge-/Ready-/Auto-Merge-Aktion.

## Späterer kontrollierter Weg

1. Die drei [Betreiberpakete](operator_checks.md) lesen und redigiert zuordnen.
   Keine bestätigten Buildstrategien oder Manual-Deploy-Werte erneut erfragen.
2. Technische Restarbeit auf exakt gebundene Werte begrenzen: realer #148-Driver,
   geprüfte Backend-Application-Adoption/Rendering, unveränderliche Images und
   vorhandener UI-Service mit geschützt gebundenem privatem Zugriff. Keine neue
   Architektur oder zweite Queue.
3. Nach eigener Mergefreigabe #156 -> #149 -> #148 -> #157 integrieren; UI #20
   abgestimmt separat. Tatsächliche kombinierte SHAs neu feststellen und prüfen.
4. Separat freigegebenes Build-/Abnahmefenster mit Budget und vollständigem
   Rückweg. Erst dann die [zehn Bootstrapphasen](rollout.md): Annahmen geschlossen,
   Drain, Imagewechsel ohne Überlappung, Rollen-/Namespace-/Healthprüfung,
   VPN-/TLS-/OIDC-Negativtests, neue explizite Resume-Freigabe.
5. Pilot separat: gebundene SourceApprovals, vorhandene Raw-Artefakte und Hashes,
   frisches C18-/B6-Preflight, genau ein begrenzter Job und ausdrückliche Freigabe.
   Erfolgreiche Infrastruktur erzeugt keine Quellen- oder Pilotfreigabe.

Kein produktiver Schritt dieses Plans wurde ausgeführt. Defaultbranchintegration
bleibt wegen des ausdrücklichen Mergeverbots ausstehend. Eigene Worktrees,
Branches, Bundles und Belege bleiben erhalten; der lokale Indexfehler wird nicht
durch Reset, Clean oder Locklöschen umgangen.

## Konfigurationsfinalisierung

Die letzten Commitänderungen von #157 ergänzen ausschließlich den Offlineprüfer,
seinen COPY im vorhandenen Runtime-Dockerfile, sichere Beispiele, Mount-/Profil-
bindungen und Dokumentation/Tests. #148/#149/#156 werden unverändert kombiniert;
keine neue Runtimeabhängigkeit und kein Queue-/Gate-/Transportneuentwurf. Das
separate Workerprofil verhindert Mitstart beim alleinigen Gateway-/APIprofil.
Der neue Jobroot ist zunächst uninitialisiert; explizite Provisionierung bleibt
eine spätere Betreiberaktion. Die Mergefolge und sämtliche Verbote gelten weiter.
