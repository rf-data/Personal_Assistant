# Betreiber-Checkliste HTTPS/VPN

**Nächster Schritt GO: ausschließlich lesende Bestandsaufnahme auf dem bereits
zugänglichen Host. NO-GO: Merge, Triggeränderung, Bootstrap oder Deployment.**
Private Ergebnisse lokal halten und nur redigierte Rollen-/Netz-/Queuealiase
weitergeben. Diese Checkliste wurde von Codex nicht auf Hetzner ausgeführt.

- [ ] In der bestehenden Coolify-Oberfläche für Backend, UI und jeden Worker
  Version, Ressourcen-ID, Buildtyp, Quellrepository/-branch und aktuelle
  Deployments lesen. Tatsächlichen Auto-/Preview-/Git-/Webhook-/Registry-/API-/
  Schedulertrigger und wartende Deployments dokumentieren. Für jeden Auslöser
  festhalten, ob ein Master-/Main-Merge oder Reviewbranch-Push produktiv wirkt.
  Keine Schalter betätigen und keinen Trigger testweise aufrufen.
- [ ] Bestehende Containerrollen identifizieren und je Rolle nur diese Metadaten
  lesen. `C26_CONTAINER_ID` privat aus dem bestätigten Bestand setzen:

  ```sh
  df -h
  df -i
  docker container ls --format '{{.ID}}\t{{.Status}}'
  : "${C26_CONTAINER_ID:?Bestehende Rolle privat zuordnen}"
  docker container inspect --format \
    '{{.Image}} {{.State.Running}} {{.RestartCount}}' "$C26_CONTAINER_ID"
  C26_IMAGE_ID=$(docker container inspect --format '{{.Image}}' "$C26_CONTAINER_ID")
  docker image inspect --format \
    '{{json .RepoDigests}} {{index .Config.Labels "org.opencontainers.image.revision"}}' \
    "$C26_IMAGE_ID"
  ```

  Revision/Digest mit vorhandenem Build-/Deploymentnachweis verbinden; fehlende
  Labels oder RepoDigests bleiben unknown. Kein Pull oder Container-`exec`.
- [ ] Mountquelle/-ziel, private Jobroots, UID, SQLite/WAL/Locks und exakt
  zuständige Queue/Worker privat zuordnen. Bestehende authentifizierte
  Nur-Lese-Anzeigen für Queue, Heartbeat, laufende Jobs und Quarantäne nutzen.
  Unabhängige Import-/Pilotroots gesondert berücksichtigen. Keine Store-
  Initialisierung, kein Probejob, keine Lockdatei löschen. Bestehende Volumes
  weder verschieben noch kopieren.
- [ ] Bestehende Domain/DNS, Traefik-Router/TLS-Port, Zertifikat/Renewal,
  VPN-Verfahren/Geräte/Routen, private API-Erreichbarkeit, Socketpeer-/RemoteAddr-
  Allowlist sowie UI-Origin/WebSocket-Regeln lesen. OIDC-Issuer, exakten Callback,
  individuelle Subjects/Rollen/Kurse und Widerruf dokumentieren; Secrets nicht
  ausgeben. Keine vollständigen Inspect-/Env-/Compose-/Logausgaben teilen.
- [ ] Vorhandenen letzten Backup-/isolierten Restorebeleg, vorige SHA/Digest-
  Version, Rollbackweg und Rettungszugang zuordnen. Keine laufende SQLite blind
  kopieren, keinen Restore ausführen. Verantwortlichen und Wartungsfenster nennen.
- [ ] Redigierte Inventur mit `../c26_final/operator_inventory.template.v1.json`
  abgleichen. Unknowns, unkontrollierte Trigger, Quarantäne oder unklare
  Queue-/Mountzuordnung ergeben **NO-GO für Merge/Deployment**. Erst nach belegtem
  Bestand separat über Triggerkontrolle, Driver, Drain/Bootstrap, exakten Rollout,
  echte HTTPS-/VPN-/OIDC-Negativtests und Rollback/Resume entscheiden.
