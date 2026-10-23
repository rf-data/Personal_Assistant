# Coolify 4.4.7: konkreter Kompatibilitätsbefund

Backend **Application / Dockerfile**, UI **Application / Docker Compose** und
beide **Manual deployments only** sind jetzt Betreiberbefunde. Backend-Base-
Directory/Dockerfile-Location und UI-Base-Directory/Compose-Location bleiben
unbelegt. Gezeigter UI-Inhalt und tatsächliches Pfadfeld sind getrennte Belege.

Die vorhandene C22-Namespacekopplung bleibt erhalten. Die
[Compose-Spezifikation](https://docs.docker.com/reference/compose-file/services/#network_mode)
erlaubt `service:api-gateway`; am API-Service darf dann kein eigenes `networks`
stehen. Das ist ein Composevertrag, keine Zusicherung für eine konkrete
Coolify-Transformation.

## Versionsgebundene Quellprüfung und minimale Korrekturen

Der [4.4.7-Application-Parser](https://github.com/coollabsio/coolify/blob/v4.4.7/bootstrap/helpers/parsers.php#L1236)
berücksichtigt `network_mode`, ergänzt aber bei normalen Diensten eigene Netze
und verarbeitet Bindmounts. Sein Long-Bind-Validator akzeptiert einfache
`${VAR}`-Quellen; die vorherige `:?`-Fehlermeldung in `source` passt nicht in
diesen erlaubten Variablenfall. Die Vorlage benutzt deshalb einfache Quellen,
behält Pflichtwerte über `x-required-paths` und `create_host_path: false` bei.
Dies ist eine aus dem Quellcode abgeleitete Kompatibilitätskorrektur.

Der [Raw-Parser im Application-Modell](https://github.com/coollabsio/coolify/blob/v4.4.7/app/Models/Application.php#L1951)
belässt die Netzdefinition, ergänzt aber Managementlabels durch Listenanhänge
und bereitet Bindpfade vor. Daher jetzt Label-Liste statt Mapping; sonst kann
das Anhängen gemischte Schlüssel erzeugen. Raw ist kein nebenwirkungsfreier
Passthrough und kein lesender Previewaufruf.

Der [4.4.7-Deploymentjob](https://github.com/coollabsio/coolify/blob/v4.4.7/app/Jobs/ApplicationDeploymentJob.php#L747)
wählt Raw separat. Er enthält Pull-, Stop-, Netz-/Proxy- und Startoperationen,
auch bei Raw. Ein inaktives Composeprofil verhindert deshalb nicht jede
Nebenwirkung eines Coolify-Deploys. Einen solchen Aufruf jetzt nicht ausführen.
Die [aktuelle Dokumentation](https://coolify.io/docs/applications/builds/docker-compose)
beschreibt den Raw-Application-Pfad; ausschlaggebend bleibt das tatsächlich
installierte Rendering mit bestätigter Application-ID.

## Tatsächlich ausgeführte lokale Prüfung

Nur `docker compose config`, **Compose 5.0.2**, mit neuem leerem Docker-
Konfigurationsverzeichnis und absichtlich nicht existierendem lokalem
Daemon-Socket. Keine Container, Builds, Pulls, Mounts oder echten TLSdateien.
Alle Werte waren `example.invalid` bzw. nicht gemountete synthetische Pfade.

- Ohne gesetzte Pflichtwerte: Fehler.
- Ohne aktiviertes Profil: null Services.
- Mit `c26-runtime-approved`: exakt Gateway, API und Kapazitätsworker.
- Jeder der sechs leeren Pflichtpfade: Fehler.
- Namespacekopplung, Worker ohne Netz, keine Hostports, Traefik deaktiviert und
  keine automatische Hostpfadanlage: im lokalen Rendering bestätigt.

Die sechs statischen/Verweigerungstests prüfen zusätzlich die finale Vorlage.
Der lokale Composeversionsstand ist **nicht** der belegte Hetznerstand. PHP-
Parser, Coolifyinstanz, Caddyimage und echte Cgroups wurden nicht ausgeführt.
Quellenprüfung und lokales Rendering belegen keinen produktiven Namespace.

## Späteres Ziel und verbleibender Implementierungsschritt

Bestehende Backend-Application kontrolliert von Dockerfile auf Compose adoptieren,
Raw als Kandidat, die drei Rollen der bestehenden Vorlage, keine Domains/Ports
und kein zusätzlich injiziertes Netz an der API. Base Directory Repositoryroot
und `deployment/coolify.runtime-bootstrap.compose.yaml` sind **Vorschläge**, keine
bestätigten Coolifyfelder. Images vorab an SHA/Digest binden; die Vorlage baut
nichts. Alle Variablen einschließlich der sechs Pflichtpfade müssen im späteren
freigegebenen Deployment explizit gebunden werden; nicht auf automatische
Erkennung der `x-`-Erweiterung in der Coolify-Oberfläche vertrauen.

Vor dieser Umstellung die tatsächliche Ressourcenadoption und endgültige
gerenderte Konfiguration in einer separat freigegebenen Testumgebung prüfen.
Genau dieser Scope muss vom bestehenden #148-Gate über einen realen Driver
kontrolliert werden. Ohne Beleg: **NO-GO**, keine zweite Application als Ausweg.
