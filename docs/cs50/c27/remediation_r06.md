# C27-R06 – Centralized Export Security Contract

## Phase A: unabhängige Reproduktion und Ursachenanalyse vor Implementierung

Ausgang: Worktree `Personal_Assistant-c27-cs50-learning`, Branch
`feat/c27-cs50-learning-pipeline`, HEAD
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. Drei versionierte Änderungen
und 52 unversionierte Dateien gehören zum bereits vorhandenen C27/R04-Stand.
Die 55 R04-Manifestdateien wurden vor Änderungen bytegenau geprüft und gesichert.
Keine Git-Artefakte für R06 erzeugt.

Die unveränderten 16 Akzeptanzfälle aus `review-r05/test_r05_independent.py`
scheitern auch im tatsächlichen Worktree: sechs Credentialpfade, sechs
nichtöffentliche Hostfälle und vier Metadatenaliase. Nachweise und vollständige
Logs liegen im neuen Verzeichnis `/tmp/c27-remediation-r06-y9ygvamb`.
R05-Findings, Zusammenfassung, Testevidenz, Gateentscheidungen, Mypy-Bewertung,
Probequellen und konkrete Offenlegungsnachweise wurden gelesen.

Ursachen:

1. `models.exportable_source_url` zerlegt nur an `. _ ~ -`; zusammengesetzte
   Session-/Credentialnamen passieren. `is_global` allein schließt Multicast
   nicht aus; `.home.arpa` erfasst die Namespacewurzel nicht.
2. Nur `SourceProvenance.source_url` besitzt eine Schutzgrenze. Andere Metadaten
   werden ungeprüft kopiert; `withheld` verhindert ihre Ausgabe nicht.
3. Eine öffentliche Hostsyntax war bereits eine implizite Freigabe. Es fehlt eine
   vom Katalog unabhängige, explizit geprüfte Quellenkonfiguration.

Datenfluss und Exportgrenzen:

- Inventar/Downloadbericht → `reviewed_week.verify_review` (Originalhashbindung)
  → lokale Processingartefakte/Katalog (interne Originalprovenienz).
- Katalog → `adapter.source_slices`: URL, Titel, Lizenz, Attribution, source_path,
  Identitätsfelder und ContentLocator → SourceRef; Fachtext separat als `text`.
- `engine.input_snapshot` enthält interne Originalmetadaten und bindet den Cache.
  `engine.generate` → SummaryResult → private `result.json`/State/Sections/Raw.
- `store.result` prüft Originalbytes gegen den gespeicherten Hash und validiert
  erneut; `store.cached` nutzt denselben Pfad. Reviewevents binden den Originalhash.
- `store.export_json` und `export.markdown` sind die gemeinsamen öffentlichen
  Grenzen für UI-Downloads, Offline-CLI und C27-CLI. Die C27-CLI gibt zusätzlich
  einen Processingbericht mit Quellenmetadaten auf stdout zurück.
- `store.read`, input/raw/sections, Processingkatalog, normalisierte Dokumente,
  Receipts und interne Reports sind lokale Arbeits-/Beweisartefakte, keine
  öffentlichen Exporte. Sie dürfen nicht als veröffentlichungsfähig gelten.

Ungeprüfte Aliasorte im bisherigen Ergebnisschema: source_path, title, license,
attribution, Identitäts-/Versionsnamen, Locator-origin_pointer/dom/chapter_path,
Ergebnistitel, Sectiontitel, topic, Warnungen/Unsicherheiten, Konfigurationstexte
und Reviewtexte. `original_url`, provider metadata, metadata und source details
existieren zusätzlich in internen Dokument-/Ressourcenmodellen oder können als
unbekannte Felder angeliefert werden; keine vollständigen internen Modelle oder
freien Metadatenwörterbücher dürfen öffentlich durchgereicht werden.

## Vor Implementierung festgelegter Vertrag

Eine zentrale Policy prüft HTTPS-Syntax, kanonische Hosts/IP-Klassen, alle
URLbestandteile und Credentialmarker. Eine separate Konfiguration gibt nur
explizit geprüfte URLs frei. Prozentdekodierung dient ausschließlich der Prüfung;
Originalschreibweisen werden nie durch dekodierte Werte ersetzt. Mehrfachkodierung
oder unklare Syntax führt zur Zurückhaltung.

Strukturierte Quellenmetadaten sind nur die ausdrücklich im Exportschema
aufgeführten Felder. Ihre Texte sind unvertrauenswürdig und werden geprüft.
Unbekannte/dynamische Metadaten werden nicht veröffentlicht; es gibt keinen
ungeprüften Durchreichmechanismus. Fachliche `SourceRef.text` und `Claim.text`
bleiben exakte, unvertrauenswürdige Lerntexte und werden nicht als Metadaten
umgeschrieben. Das ist kein allgemeiner Geheimnisscanner für beliebigen Lerntext.
Interne Records und Rohdaten behalten Originalprovenienz und Identität.

## Implementierter Exportvertrag

`src/lecture_summary/export_policy.py` ist die einzige URL-/Metadatenpolicy.
`source_url_key` prüft Syntax und Sicherheit; `ExportPolicy.source_url` verlangt
zusätzlich eine explizite Freigabe. `models.exportable_source_url` bleibt als
kompatibler Reexport derselben Funktion erhalten, ohne zweite Implementierung.

Die Prüfung erlaubt ausschließlich HTTPS mit Standardport, ohne Userinfo,
Query oder Fragment (auch leere Delimiter sind verboten). Pfade bestehen nach
höchstens einer strikten Prozentdekodierung nur aus unreserved ASCII. Dot-Traversal,
leere innere Segmente, kodierte Trenner/Steuerzeichen und verbliebene Prozentzeichen
werden zurückgehalten. Zusammengesetzte und CamelCase-Credentialnamen werden geprüft.
Eine Freigabe umfasst genau den geprüften Host/Pfad, keine Hostwildcards oder
Pfadpräfixe. Damit sind auch zusätzliche opaque tokenartige Pfade ohne bekannten
Credentialnamen nicht implizit erlaubt. Öffentliche Videoidentifikatoren bleiben
bei expliziter Freigabe möglich; es gibt keine ungeprüfte Entropieheuristik.

Hosts werden ohne DNS-Auflösung kanonisiert: Groß-/Kleinschreibung, eine finale
DNS-Dotnotation und Standardport beeinflussen die Freigabeidentität nicht.
IPv4/IPv6 werden separat auf öffentliche Unicastsemantik geprüft, einschließlich
Multicast, Reserved, Loopback, Link-local, Private, Unspecified und IPv4-mapped IPv6.
Lokale Namespacewurzeln und Subdomains, numerische Kurz-/Oktal-/Hexschreibweisen,
Unicode-/Prozenthosts, fehlerhafte Autoritäten und IPv6-Zonen werden zurückgehalten.
Die Originalschreibweise einer erlaubten URL bleibt erhalten. Dekodierte Werte
werden niemals als Exportersatz ausgegeben.

`public_sources.v1.json` ist eine getrennte, versionierte Konfiguration neben dem
Code. Sie enthält exakt die 75 R05-kompatiblen offiziellen URLs und drei zusätzlich
explizit geprüfte öffentliche CS50P-Referenzen für historische Fixtures und
kanonische Schreibweisen. Das Format und die Implementation sind kursunabhängig.
Ein künftiger Kurs benötigt eine eigene Konfigurationsänderung mit Reviewreferenz
und expliziten URLs, getrennt von angelieferten Katalogen und Quelldokumenten.
Kein Katalogfeld, Reviewstatus, CLI-Flag oder Umgebungswert kann Quellen freigeben.
Ungültige Einträge bestehen die Konfigurationsvalidierung nicht; fehlende/defekte
Konfiguration führt zu einer leeren Freigabeliste. Auch eine Konfiguration darf
keine unsichere URLsyntax freigeben. Die konfigurierte Reviewreferenz dokumentiert
den vorgesehenen Code-Reviewprozess; sie ist keine kryptografische Signatur und
keine Produktions-/Lizenzfreigabe.

| Feldklasse | Behandlung |
|---|---|
| `SourceProvenance.source_url` | Strikte URLprüfung und explizite Freigabe; sonst `None` mit `withheld`, bei fehlendem Original `missing` |
| Titel, Lizenz, Attribution, source_path, strukturierte Identitäts-/Versionslabels | Unvertrauenswürdige Metadaten; ganzes Feld bei unsicherem/unfreigegebenem eingebettetem URLwert oder Credentialmarker durch konstantes `[withheld metadata]` ersetzen |
| ContentLocator-Textfelder | Dieselbe Metadatenprüfung; zurückgehaltener origin_pointer erhält gültigen konstanten `/withheld-metadata`-Pointer |
| Ergebnistitel, Sectiontitel, topic, Warnungen/Unsicherheiten, Konfigurations-/Reviewtexte | Dieselbe Metadatenprüfung; Statuswerte bleiben konstante Schemawerte |
| `SourceRef.text`, `Claim.text` | Fachlicher untrusted Text; exakte Zeichen bleiben erhalten, einschließlich legitimer Beispiel-URLs; keine pauschale Geheimnissuche |
| Dynamische `metadata`, `original_url`, `source_details`, Providerdaten, unbekannte Erweiterungen | Keine Freigabe durch Feldnamen: feste Adapter-/Exportschemata übernehmen sie nicht; unbekannte Felder im strikten Ergebnisschema werden kontrolliert abgelehnt |
| Interner Katalog, Inputsnapshot, Raw/Sections, Processingdokumente, Receipts und Berichte | Private Arbeits-/Provenienzartefakte; keine öffentlichen Exporte |

Die Metadatentraversierung arbeitet ausschließlich auf ausgewählten Schemafeldern,
mit maximal Tiefe 8, 4096 besuchten Knoten, 128 Dictionaryeinträgen und 1024
Listeneinträgen je Aufruf. Überlauf, unbekannte Typen und Zyklen führen zu konstanten
Platzhaltern; unbekannte Objekte werden nicht stringifiziert. Unsichere Dictionarykeys
werden verworfen. Prozentkodierte Metadatensichten werden höchstens viermal nur zur
Prüfung dekodiert; verbleibende Kodierung wird zurückgehalten. Eingebettete URLs
müssen sowohl in Original- als auch Prüfsicht zugelassen sein. Dadurch macht eine
Dekodierung keine ursprünglich gesperrte URL wieder exportfähig.

Metadatenvalidierung schützt neue Ergebnisse und erneut geladene v1-/v2-Ergebnisse.
Zusätzlich revalidieren `export.markdown` und `store.export_json` an ihrer finalen
Ausgabegrenze, einschließlich durch Konstruktion/Mutation umgangener Modelle.
Serializerdiagnosen mit Eingabewerten werden an dieser Grenze unterdrückt und
Validierungsfehler durch konstante Meldungen ersetzt; Tests prüfen ausdrücklich,
dass keine Canarywerte in Warnungen oder Exceptions erscheinen. Reviewevents werden
auf bekannte Felder projiziert und ebenfalls erneut geprüft. `source_label` schützt
seinen separaten Anzeigeweg. Die C27-CLI gibt einen ausgewählten öffentlichen
Processingbericht mit URLstatus zurück; der vollständige interne Bericht bleibt
lokal. UI- und Offline-CLI-Downloads nutzen dieselben beiden Ergebnisexporter.

Originale Quellen-URLs, Rohhashes und Identitäten bleiben im internen Material/
Inputsnapshot erhalten. Exportplatzhalter ändern weder Rohdateien noch bestehende
Storebytes, gespeicherte Ergebnis-SHA-256, Referenz-IDs oder Reviewhashbindungen.
Freigabewiderruf wirkt auch auf Cachetreffer. Neue Freigaben veröffentlichen zuvor
zurückgehaltene Cachemetadaten nicht rückwirkend aus privaten Inputsnapshots.

## Tests und Sicherheitsnachweise

Alle Tests liefen offline mit FakeLLM/Stubs, explizitem Socket-/Prozessguard,
deaktiviertem Plugin-Autoload und Bytecode, isolierten neuen basetemp-Pfaden sowie
abgeschaltetem pytest-Cache. Exakte argv, Umgebung, CWD, Exitcode und Laufzeit stehen
in den `*-command.json`-Dateien der Übergabe. Keine Installation, Netzwerkauflösung,
Downloads, echten Provideraufrufe oder Produktionsaktionen.

| Auswahl | Ergebnis |
|---|---:|
| Unveränderte 16 R05-Reproduktionen vor Änderung | 16 FAIL, erwartete Sicherheitsverletzungen |
| Unveränderte R05-Negativ-/Parentfälle nach Änderung | 93 PASS, einschließlich aller 16 Fälle |
| Sechs unveränderte R05-HTTPS-Positivfälle | 6 PASS |
| Bestehende C27-/Summarizer-/UI-/Pipelineauswahl | 676 PASS, 2 optionale SKIP |
| Historische unabhängige F01/F02/F03/F05-/Isolations-/Echtdaten-/CLI-Invarianten | 24 PASS |
| R06-Negativ-/Alias-/Cache-/Review-/Freigabe-/Lerntextprüfungen | 137 eindeutige PASS |
| Gesamt, nach Testidentität dedupliziert | **936 PASS, 2 SKIP, 0 verbleibende FAIL** |

Die R06-Zahl setzt sich aus einem vollständigen 136-Fälle-Lauf und einem finalen
Drei-Fälle-Lauf mit zwei Überlappungen und einer zusätzlichen Serializerwarnungsprobe
zusammen. Wiederholungen und frühe Läufe werden nicht addiert. JUnit-Dateien,
`test-assessment.json` und der Auswertungshelfer sichern diese Zählung.
Die beiden Skips betreffen optionale echte Notes-HTML-/Operator-Exportfixtures.
Die erwartete ZipFile-Duplikatwarnung gehört zu einem Kollisionsfixture.

Acht frühere R04-Positivfälle für ungeprüfte Beispielhosts/öffentliche IPs bleiben
vollständig als Fälle erhalten, erwarten unter R06 jedoch Zurückhaltung. Kein
negativer Test wurde entfernt oder abgeschwächt. Der frühe Lauf mit den alten
Positiverwartungen (8 FAIL/219 PASS) bleibt transparent als Zwischenlog erhalten.
Die einzelne alte R05-HTTP-Positiverwartung gehört zum ausdrücklich ersetzten
HTTP(S)-Vertrag und wurde nicht als HTTPS-Kompatibilitätsnachweis gezählt.
Alle 75 zuvor zugelassenen offiziellen URLs werden separat über Persistenz,
Hashbindung, Wiederladen, Cache, JSON und Markdown geprüft. Kanonische Varianten
bleiben durch die unveränderten sechs HTTPS-Positivfälle abgesichert.

Die R06-Suite enthält zusätzlich die exakten 16 R05-Fälle dauerhaft im Repository;
Varianten mit sessionid/accessToken, Mischschreibung, Tokenpfaden, Query/Fragment,
Kodierung bis zu mehrfachen Ebenen, lokale Host-/IPvarianten, Metadatenaliase,
Duplikate in mehreren Feldern, unbekannte und tiefe Strukturen sowie mutierte
Modelle. Öffentliche Dateien werden auf synthetische Canaries geprüft. Eine
getrennte Lerntextprobe erwartet bewusst dieselbe Beispiel-URL unverändert im
fachlichen Zitat, während die strukturierten Metadaten zurückgehalten werden.
Dies ist kein Anspruch, beliebige opaque Geheimnisse aus Lehrtexten zu entfernen.

Echte lokale Week-0-Eingaben wurden ausschließlich gelesen. Der historische
Functions-TXT-CLI-Durchlauf bestätigt weiter 18 Sections/18 Claims und Cache ohne
weitere Fakecalls. Vollständige HTML-Auswahlen bleiben an der bestehenden Chunkgrenze
blockiert; ZIP-Zuordnung, Vollständigkeit und Fachabnahme werden nicht umklassifiziert.

Ruff und Formatprüfung bestehen für alle C27-Produktionsdateien und sechs zugehörige
Testdateien (24 Pythondateien). Mypy bleibt nicht grün; der Fokusvergleich zeigt
132 → 132 bestehende Diagnosen. Der erweiterte Produktionsscope bleibt bei
200 → 200, global `src` bei 6104 → 6104. In allen drei Scopes gibt es weder
neue noch entfernte Diagnosen; sämtliche Diagnosen lassen sich identischen
Quellzeilen zuordnen. Vollständige Diagnose-/Quellzeilenvergleiche stehen in der
Übergabe. Der globale Typstand bleibt ausdrücklich nicht grün.

## Ressourcen und Erhaltung

Vor den Tests waren rund 5,1 GiB frei, vor der breiten Regression 5.426.147.328 Bytes.
Die bestehende 5-GiB-Reserve wurde weder verändert noch umgangen; die breite Auswahl
bestand ohne Capacity-Ausfälle. Mypy nutzt `--cache-dir /dev/null`, ohne Änderung der
strict-Konfiguration. Nur die eigenen explizit aufgezeichneten Testverzeichnisse
werden nach komprimierter Sicherung und Prüfung aller Datei-/Linkeinträge entfernt.
Vorher-/Nachher-Freiraum, Archivmanifest und Bereinigungsschritte sind protokolliert.
Bestehende Caches, virtuelle Umgebungen, Benutzerdaten und andere Worktrees bleiben
unangetastet. Temporäre Rekonstruktionskopien sind gewöhnliche eigene Dateikopien,
keine Git-Worktrees. Rohdaten-/Inputmanifeste werden abschließend erneut geprüft.

## Übergabe und Entscheidungen

Neue eindeutige Ablage: `/tmp/c27-remediation-r06-y9ygvamb`. Sie enthält den
C27-Gesamtpatch gegen `a8af1d9`, das separate R06-Delta gegen den vor Änderungen
hashgeprüften R04-Ausgangsstand, diesen Bericht, den R04-Gesamtpatch als zweite
Rekonstruktionsbasis, Dateimanifeste, SHA-256-Manifeste, Test-/Sicherheits-/Typnachweise,
Git-Vorher-/Nachherstatus und einen ausführbaren Offline-Rekonstruktionshelfer.
Beide Wege müssen den vollständigen beabsichtigten Dateibaum hinsichtlich Bytes,
Dateianzahl, Größen und Modi ergeben; Vorwärts-/Rückwärtsprüfungen werden protokolliert.
Ein Hashmanifest sichert Integrität, keine externe Authentifizierung.

| Entscheidung | Ergebnis |
|---|---|
| Alle 16 R05-Fälle | **CLOSED**, unverändert vor/nach reproduziert und zusätzlich als Regression gespeichert |
| F04 | **FIXED** im definierten öffentlichen Quellenmetadatenvertrag |
| Parent-Fix | **Keine Regression** |
| F01/F02/F03/F05 | **Keine Regression** im dokumentierten Prüfumfang |
| C27 | **READY_FOR_INDEPENDENT_REVIEW** |
| CS50P Week 0 | **PARTIAL**, eigenständige Abnahme weiterhin offen |
| Multiweek/Multicourse-Rollout | **PLANNING_ONLY**, eigenständiges Rolloutgate |
| Produktion | **NOT_APPROVED** |

Keine Commits, Pushes, PRs, Merges, Rebases, Resets oder neue Git-Artefakte. Der
zugewiesene bereits bestehende Branch und Worktree bleiben vollständig erhalten.
Default-Branchintegration der Änderungen und Dokumentation bleibt wegen des
expliziten aufgabenspezifischen Verbots **pending**; keine Live-Gitprüfung wegen
des Netzwerkverbots. Dieser lokale Security-Remediation-Nachweis ist keine PR-,
Merge-, Week-0-, Rollout- oder Produktionsfreigabe. Ein späterer autorisierter
regulärer PR-/Reviewprozess muss die dauerhafte Integration nach AGENTS.md prüfen.

Die gezielte `.gitignore`-Ausnahme für die geprüfte Quellenkonfiguration stellt
sicher, dass sie in beiden Patchwegen enthalten ist. Alle vorhandenen
R04-Ignore-Ausnahmen bleiben erhalten.

Die abschließende Archivprüfung umfasst 12.139 eigene Datei-/Link-/FIFO-Einträge.
Die FIFO-Einträge sind synthetische Fixtures der bestehenden Eingabesicherheitstests;
sie wurden als Spezialdateien ohne Inhaltsleseversuch geprüft. Eine zunächst langsame
nichtsequentielle gzip-Verifikation wurde vor jeder Löschung unterbrochen und durch
einen sequentiellen vollständigen Vergleich ersetzt. Sämtliche elf eigenen
basetemp-Verzeichnisse sind anschließend aus dem verifizierten Archiv rekonstruierbar.
Die gewöhnliche Mypy-R04-Kopie wurde nach vollständigem Vergleich ihrer 1.184 Dateien
mit Basis plus R04-Patch entfernt; Logs und die 55-Dateien-R04-Sicherung bleiben erhalten.
