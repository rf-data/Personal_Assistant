# CS50P-MVP: Downloadpolicy

**Default deny.** Kandidateneintrag ist keine Freigabe. Jede Quelle benötigt die
vorhandene `SourceApproval` mit exakter URL, material_id/source_id/course_id,
Download-/Processfreigaben und konkreten Referenzen zu Zweck, Lizenz, robots,
Aufbewahrung und Widerruf. Keine Freigaben werden durch dieses Paket erteilt.

MVP: ausschließlich Kurs `cs50_python`, HTML/PDF, exakte ausgewählte offizielle
HTTPS-URLs auf `cs50.harvard.edu/python/…` oder `cdn.cs50.net/python/…`, Port 443.
Maximal drei Materialien aus dem hashgebundenen Snapshotmanifest; kein rekursives
Nachladen von HTMLlinks, Bildern, CSS oder Skripten. Keine freien Nutzer-URLs,
Querystrings, Fragmente, Credentials, externen Domains, Authentifizierungscookies,
YouTube-/edX-/Drivequellen oder Medien-/ZIPdownloads. URLpfade werden auf Traversal
und doppelte Kodierungen geprüft; Dateinamen stammen aus Materialhashes, nie aus
Content-Disposition oder URLpfaden. Fremder Code wird nicht ausgeführt.

DNS-Antworten müssen vollständig öffentlich sein. Loopback, RFC1918, Link-local,
Metadata (auch 100.100.100.200), CGNAT, reservierte/Multicastadressen und IPv6-
Transitionen werden verworfen. TCP verbindet zur geprüften numerischen IP,
während Host und TLS-SNI/Zertifikatsname die Originaldomain bleiben. Keine zweite
Auflösung der Kursdomain beim Connect; pro Anfrage neue Prüfung, keine Poolwiederverwendung,
keine Umgebungsproxies. Alle Redirects werden abgelehnt, deren Ziel wird nie kontaktiert.
TLSprüfung bleibt aktiv; Authorization/Cookie/Proxy-Authorization werden entfernt.

Grenzen: 1 MiB pro Material (Batchvertrag), maximal drei Materialien seriell;
6 MiB akzeptierte Response-Payload pro Aufruf über alle Versuche, einschließlich
Fehlversuchen. Ein überschreitender Transportchunk kann bereits im Speicher sein,
wird nicht an den Dateischreiber weitergegeben; dies ist keine Netzwerkbytequota für
TLS/HTTPheader. Höchstens ein automatischer Retry (429/5xx/Transportfehler),
Backoff 1 s; keine Retries für 403/404/Redirects/Inhaltsfehler. Intermaterialabstand
1–60 s nach bestehendem Approvalvertrag; Standard 2 s. 10 s IOtimeout, 45 s Downloaddeadline,
600 s systemd-Limit für den gesamten Dienst inklusive DNS. Der synchrone OSresolver
hat keinen eigenen abbrechbaren Python-Timeout; der Diensttimeout ist die harte Grenze.

Content-Type, Transferencoding, Größenlimit, exakte Content-Length (falls vorhanden),
Nichtleere, SHA-256 und PDF-Signatur werden geprüft; erwarteter Betreiberhash vor Raw-
Veröffentlichung. Ohne vorher bekannten Hash ist SHA-256 eine lokale Integritätsbindung,
kein unabhängiger Beweis der Herausgeberschaft. Parser und C10 prüfen danach Semantik.
HTML wird als Dokument geparst, kein Browser oder JavaScript gestartet.

Temporäre Dateien liegen in `raw/.incoming/`, validierte unter `raw/source`.
Linux-Rename übernimmt exklusiv/atomar; unbekannte bestehende Dateien werden nie ersetzt.
Receipt mit Write-ahead-Hash ermöglicht kontrollierte Recovery nach Publikationsverlust.
Geprüfte identische Dateien werden nach Hashprüfung übersprungen. Kein Range-Resume;
Teilreste nach SIGKILL bleiben Beweismittel und blockieren den MVP bis zur manuellen
Untersuchung. SIGTERM schreibt einen interrupted-Report und entfernt eigene aktive Temps.
Erneuter Versuch benötigt bei ausgewählten/fehlgeschlagenen Receipts `--retry-failed`.
Keine Löschung oder automatische Wiederholung unterbrochener Verarbeitungsjobs.

Reports enthalten exakte bereits geprüfte URL, Quellenidentität, UTC-Zeit, Status,
Dateigröße und SHA-256; Receipts/Versuchsreports bleiben privat. Fehler nur als Klassen,
keine Exceptiontexte, Cookies, Tokens, Header oder Umgebungsdump.

## Quellen- und Nutzungsprüfung am 27.10.2026

Die offizielle [CS50P-Lizenz](https://cs50.harvard.edu/python/license/) nennt
CC BY-NC-SA 4.0: Namensnennung, nichtkommerzielle Nutzung und ShareAlike bei
Weitergabe bearbeiteter Inhalte. [Offizieller Kurseinstieg](https://cs50.harvard.edu/python/)
bietet freies OpenCourseWare; das ist keine pauschale Freigabe für jeden eingebundenen
Drittinhalt oder beliebige automatisierte Abrufe. Lizenz/Attribution pro Material
im Approval referenzieren, Original-URL und Änderungsprovenienz erhalten.

`https://cs50.harvard.edu/robots.txt` war über das Recherchewerkzeug nicht abrufbar;
keine erfolgreiche robots-Prüfung behauptet. CDNrobots/konkrete CDNmaterialbedingungen
nicht bestätigt. Betreiber muss beides für tatsächlich gewählte URLs dokumentieren,
bevor download/process=true gesetzt wird. Keine Zugangsbeschränkungen umgehen;
403/429/Sperren respektieren, kein Cookieimport, keine Schutzmechanismen umgehen.
Die Recherche las nur öffentliche Informationsseiten; keine Kursmaterialdownloads
und kein Zugriff auf Hetzner wurden durchgeführt.
