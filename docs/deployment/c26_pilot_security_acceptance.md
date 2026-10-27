# C26-PILOT-INTEGRATION – aktueller Accessvertrag

27.10.2026. **HOLD; keine Domain/öffentliche Route aktiviert.** Der UI-Code
auf main wird unverändert verwendet. Die nachfolgende vollständige
admin.franke-data.dev-Konfigurationsmatrix bleibt verbindlich. Die alten
Aussagen „Gate auf master fehlt“ gelten weiterhin für master; im lokalen
Kandidaten ist die D/E/F/G/H-Kette jetzt offline integriert.

Die UI-Standardsuite wurde neu ausgeführt: 151 bestanden, 25 erwartete
backendabhängige Skips; aktuelle IPC-Ergebnisse stehen in der
[Validierung](c26_pilot_validation.md). Die Session-/Claim-/Nonce-/Origin-/
Cookie-/WebSockettests verwenden synthetische Identitäten, keinen Live-IdP.
Owner bleibt die backendseitige Jobbeziehung, keine neu erfundene dritte Rolle.
Operator und Viewer bleiben individuelle, disjunkte OIDC-/C16-Bindungen.

Der Pilot-UIoverlay ändert ausschließlich Containerlimits, manuelle Restartpolicy
und Profilwahl im bestehenden Backend-Betreibervertrag. Keine UI-Quellen
wurden in dieses Repository kopiert. Logout ist st.logout, kein Worker-Cancel,
kein garantierter IdP-Backchannelwiderruf. Ausführung bleibt ohne gültige
C16-/Gateautorisierung gesperrt. Ein UIlogin gewährt kein Deploymentrecht.

Offen: exakter Issuer/Discovery/App/Subject, eigener Cookiekey und individuelle
C16-Tokenfiles; CA/SAN und private API-DNSidentität; tatsächlicher Traefikpeer und
VPN-Allowlist, IPv6 plus unabhängige Negativquelle; echte Browserexpiry, Logout,
WSS und Secretrotation. Leere Werte sind BLOCKED, kein Defaultfallback.

---

## Vollständige Konfigurations- und Abnahmematrix aus dem Betreiberpaket

# C26-PILOT – Authentifizierung und Sicherheitsabnahme

**HOLD.** Matrix zur späteren getrennten Betreiberfreigabe; keine Domain,
IdP-Anwendung, Identität, Route oder Firewallregel wurde angelegt.
Führende Quellen sind die vorhandenen UI-Dateien `security.py`,
`container_runtime.py`, `https_runtime.py`, `core/environment.py` und die
Backend-C16-Handler. Historische Betreiberberichte ersetzen keine Liveabnahme.

## Konfigurationsmatrix für admin.franke-data.dev

| Schlüssel / Vertrag | Exakter Zielwert oder noch einzutragender Nachweis |
| --- | --- |
| UI-Origin / `C26_UI_ORIGIN` | `https://admin.franke-data.dev`, kein Pfad, kein abschließender Slash |
| `ADMIN_AUTH_MODE` | `oidc`, kontrollierter Ersatz von `disabled`; erst vollständig konfiguriert starten |
| `APP_ENV`, `JOB_BACKEND`, `JOB_API_MODE` | `server`, `http`, `production` |
| `C22_PRODUCTION`, `C26_HTTPS` | jeweils `1` |
| `C26_ACCESS_PROFILE` | `private-https`; kein stiller Wechsel zu public-https |
| `[auth].redirect_uri` | **`https://admin.franke-data.dev/oauth2callback`**; bei IdP exakt registrieren, keine Wildcard/zweite HTTP-URL |
| Login / Logout | Streamlit `st.login()` / `st.logout()`; tatsächliche Providerredirects und Endsessionfunktion im Browser prüfen |
| Post-Logout-Rückkehr | Gewünschte Rückkehr `https://admin.franke-data.dev/`; falls IdP separat registrieren muss, ausdrücklich prüfen. Kein behaupteter implementierter OIDC-Backchannel-Logout |
| `ADMIN_OIDC_ISSUER` | Noch offen: bestätigter exakter HTTPS-`iss` des gewählten IdP; nicht aus einer E-Mail oder einem beliebigen Header ableiten |
| `[auth].server_metadata_url` | Noch offen: verifizierte HTTPS-Discovery-URL des gleichen IdP, korrekte CA/SAN und exakter Issuer |
| `[auth].client_id`, `.client_secret` | Noch offen: eigene vertrauliche OIDC-App; Secret ausschließlich privat außerhalb von Repo/Build |
| `[auth].cookie_secret` | Eigener zufälliger Schlüssel, mindestens 32 Zeichen, privat; Rotation invalidiert bestehende UIcookies |
| `[auth].expose_tokens` | `[]`; keine IdP-Tokens als C16-Bearer verwenden |
| `[auth.client_kwargs].scope` | `openid`; keine manuellen `state`, `nonce`, `verify` oder `redirect_uri`-Overrides |
| `ADMIN_OPERATOR_SUBJECTS` | JSON-Array mit genau einem **erst am IdP verifizierten** individuellen `sub`; kein hartkodierter Beispielbenutzer |
| `ADMIN_VIEWER_SUBJECTS` | `[]` im Erstpilot; weitere Identitäten benötigen eigene Freigabe und Tokenbindung |
| `ADMIN_OIDC_SESSION_MAX_AGE` | `3600`; vorhandene Grenzen 60–28800 s. Numerische `iat`/`exp`, `iat <= now < min(exp, iat+3600)` |
| `JOB_API_IDENTITIES` | Genau eine eigene Zuordnung `ui_subject`, `backend_subject`, `role=operator`, `token_file=/run/secrets/c16/<individuell>.token`; wirkliche Werte noch offen |
| Backend `identities[]` | Passender eindeutiger Backendsubject, Rolle operator, nur freigegebener Course, SHA-256 des individuellen Bearers; keine Klartexttokens in JSONreports |
| `JOB_API_URL` | Noch offen: bestätigte private DNSidentität des vorhandenen C22-Gateways, `https://<private-api-dns>:8443`; kein öffentlicher Alias/Hostport |
| `SSL_CERT_FILE` | `/run/ca/ca.crt`; vollständiges geprüftes Trustbundle, TLSprüfung immer aktiv |
| `FORWARDED_ALLOW_IPS` | Leere Zeichenkette; keine implizite Uvicorn-Forwarded-Trustkette |
| `C26_TRUSTED_PROXY_CIDRS` | Noch offen: tatsächliche Traefik-Socketpeer-IP(s) oder ausschließlich dediziertes Ingressnetz; niemals 0.0.0.0/0 oder ::/0 |
| `C26_ALLOWED_CIDRS` | Noch offen: ausdrücklich genehmigte VPN-Geräte-/Egress-IPs als /32 beziehungsweise /128; keine öffentliche Allowliste |
| `C26_ROUTE_ID` | Noch offen: eindeutige UI-Ressourcenroute; alle generierten HTTPSrouter müssen ihre private Middleware tatsächlich referenzieren |
| `C26_INGRESS_NETWORK`, `C26_BACKEND_NETWORK` | Noch offen: tatsächliches dediziertes Proxy- bzw. internes Backendnetz; bestehendes breites `coolify`-Netz genügt nicht als Beweis der Isolation |
| `C26_UI_IMAGE` | Noch offen: genehmigter Registrydigest, unabhängig zu geprüftem UI-SHA gebunden |
| `C26_UI_TOKENS`, `C26_UI_OIDC`, `C26_API_CA` | Noch offen: vorab geprüfte existierende Hostdateien/-verzeichnisse, ro-Mounts und UID 10001, siehe Runtime |

Nicht genannte Backenddigest-, CA-/TLS-, Pilotroot- und Katalogwerte stehen in der
[Runtime-Matrix](c26_pilot_runtime_matrix.md). Leere Felder sind Freigabeblocker,
keine Aufforderung, sie mit beliebigen Werten zu füllen. Keine echte `.env` oder
Secretsdatei ist Bestandteil dieses Pakets.

## Rollenvertrag und Widerruf

| Identität | Zulässige Aktionen / serverseitige Grenze |
| --- | --- |
| Unbekannt, ungültiger Issuer, fehlende/abgelaufene Claims | Kein Principal, kein fachlicher Zugriff; angemeldete aber nicht freigegebene Nutzer bleiben abgewiesen |
| Viewer | Ausschließlich authentifizierte erlaubte Leseaktionen im eigenen Course-/Sourceumfang; kein Create/Start/Cancel/Resume |
| Operator | Preview und ausdrücklich bestätigte Ausführung im erlaubten Course; Mutationen/Cancel nur gemäß bestehender Ownerprüfung |
| Owner | **Keine dritte OIDC-Rolle.** C16 kennt viewer/operator; Owner ist die Beziehung `job.initiated_by == principal.subject` für geschützte Jobaktionen |
| UI → Backend | Eigener individueller C16-Bearer je UIidentität, eindeutige Rolle/Subjects und Tokendatei; UI- und Backendsubject dürfen unterschiedlich sein, müssen explizit gebunden sein |
| Deploymentoperator/-collector | Getrennte Betriebsidentitäten und Audience; UI-Operator ist kein Coolifyadministrator und keine Deploymentfreigabe |

Role-/Course-/Sourceprüfung bleibt im Backend, nicht nur im Widget.
Unbekannter `sub`, falsche Backendrolle, doppelte Subject-/Tokenbindung,
Cross-Course-/Cross-Ownerzugriff und fehlende Tokenfiles müssen fail-closed enden.
Beim Widerruf zuerst individuelle Backendbindung/Token sperren, UIallowlist
entziehen und Sessions/Cookies nach dokumentiertem Rotationsverfahren invalidieren.
Laufende Jobs gesondert sicher abbrechen: ein IdP-Logout beendet keinen Worker.
Keine Behauptung sofortiger IdP-Rechteübernahme oder globalen SSO-Logouts.

## Ingress- und Egressgrenzen

Traefik terminiert Browser-TLS auf der genehmigten Adminroute; HTTPredirect darf
keinen fachlichen Inhalt liefern. Zwischen Traefik und UI intern HTTP/WSSupgrade,
UI → API ausschließlich geprüftes HTTPS. API lauscht nur 127.0.0.1 im gemeinsamen
Gatewaynamespace; Gateway nur internes Netz, keine APIroute am öffentlichen Proxy.

Die UI-Middleware verlangt genehmigten Socketpeer, exakte Host-/Forwarded-Host-
und HTTPSangabe. Doppelte Sicherheitsheader und fremder Origin werden abgewiesen;
WebSockets verlangen exakt einen passenden Origin. HTTPnavigation und Callback
dürfen Origin auslassen. Nur Loopback-GET auf `/_stcore/health` ist ausgenommen.
`Secure` wird auf alle Cookiefragmente gesetzt; HttpOnly/SameSite-Lax bleiben
erhalten. CORS/XSRF bleiben aktiv; Header von beliebigen Clients schaffen kein Vertrauen.

VPN/DNS sind noch **unbestätigt**. Private DNS allein ist kein Zugriffsschutz.
Traefiks IP-Allowlist muss RemoteAddr verwenden, ohne vertrauende X-Forwarded-For-
IPstrategie. Kein unbesehen erlaubter gemeinsamer NAT-/Bridgepeer. IPv4 und IPv6,
korrektes SNI zur öffentlichen Adresse, Hostaliases, fremde Geräte und entzogene
Geräte müssen unabhängig negativ getestet werden. Kein TLSfehler als bestandener
Netznegativtest. Bestehende `demo.franke-data.dev`- und `coolify.franke-data.dev`-
Router und Zertifikate bleiben unberührt.

Executor hat kein Netzwerk. UI benötigt gesondert erlaubten HTTPS-Egress zum
gewählten IdP und zur privaten API; Netzwerkmitgliedschaft allein ist kein
zielgebundener Egressfilter. Noch fehlende DNS-/IdP-/CA-/Renewalpfade dokumentieren
und abnehmen. Keine LLM-/Downloadvariablen, kein Downloadprofil, keine pauschale
Internetfreigabe. Clienttests und Python-Socketguards ersetzen keine Netzisolation.

## Abnahmeliste und Nachweise

| Nachweis | Offline | Noch erforderliche LIVE ACCEPTANCE – SEPARATE APPROVAL REQUIRED |
| --- | --- | --- |
| OIDC, Claimzeit, unbekannter Nutzer, Rollen/Owner | Vorhandene Unit-/Handlertests | Gewählter IdP, echte unterschiedliche Testidentitäten, Cross-Owner-/Courseablehnung |
| Callback, State/Nonce, Cookie, Sessionablauf/Logout | Guard-/ASGI-/Authlibtests | Echter Browser inkl Refresh, Logout, abgelaufenem/entzogenem Zugriff; kein Token in HAR/Logs |
| CA/SAN, privates API-TLS | Konfigurationsverträge | Echter gültiger Pfad; falsche CA/SAN wird abgelehnt; niemals verify=false/curl -k |
| HTTPS/WSS, Header/Origin | Synthetische Middlewaretests | Proxyupgrade, fremder/doppelter Origin, gefälschte Forwarded-Header, Reconnect |
| VPN/IPallowlist, Portisolation | Nur Vorlagen | Zweite unabhängige Quelle, IPv4/IPv6, Public-IP mit korrektem SNI; APIports nicht erreichbar |
| Ressourcen/Storage/Cancel | Synthetische Prozesse | Isolierte Container, echte Cgroup-/UID-/Mount-/OOM-/Abbruchnachweise (#109) |
| Gate/Drain/Trigger | Auf master fehlend | Integration plus exklusive Freigabe, aktive Jobs/Idle-Races, unbekannte Zustände blockiert (#146) |

Fehlender Nachweis bedeutet HOLD. Offlineerfolg autorisiert keine C-Aktion,
Deploymentreadiness ist kein C26-GO. #110 bleibt bis echter Abnahme offen.
