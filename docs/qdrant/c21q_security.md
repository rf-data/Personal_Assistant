# C21-Q: Sicherheitsgrenzen

Phase A umfasst nur lokale Vorbereitung, technische Tests und Metadateninventar.
Phase B ist **blocked**, weder SSH-/Coolify-Lesezugriff noch Deployment,
Servervolumeänderung, echte Remote-Collection, Upload oder Snapshotübertragung
wurde freigegeben oder ausgeführt. Einzelne CLI-Flags ersetzen keine Betreiberfreigabe.
Die konkrete Checkliste steht in [c21q_operations.md](c21q_operations.md).

Der versionierte Composevorschlag pinnt einen Server, veröffentlicht keine Ports,
isoliert sein Netz und verwendet persistente explizite Mounts. Authentifizierung
kommt aus einer privaten schreibgeschützt eingebundenen Datei. Rechte, UID,
Netzwerkgateway, TLS und Coolifys erzeugter Deployable Compose müssen vor einem
Start tatsächlich geprüft werden. Keine existierende Instanz/Collection wird ersetzt.
Der ehemalige `scripts/setup_qdrant.sh`-Public-Port-Starter startet nichts mehr;
er verweist mit Fehlerstatus auf den geprüften Ablauf.

Die bestehende Index-CLI verlangt `--allow-remote`, einen credentialfreien
HTTPS-Origin und einen privat gesetzten `QDRANT_API_KEY`. Upload erfordert
zusätzlich `--execute-upload` und exakt passenden Source-Scope. Dry-Run erzeugt
keinen Remoteclient. Remoteanfragen verwenden keinen Umgebungsproxy, folgen
keinen Redirects und deaktivieren keine TLS-Prüfung. Fehlermeldungen enthalten
nur Status, Stufe und Fehlerklasse, keine Responsebodies oder Schlüssel.
Die aktuelle Umgebung ohne SDK erlaubt keine reale TLS-/Authabnahme; Unit-Guards
und ausstehende Servertests sind im [Testbericht](c21q_validation.md) getrennt.

Der Uploader speichert bewusst Transcripttext und Originalchunks im Payload.
Diese Datenart muss ausdrücklich zugelassen werden; reine Vektorenfreigabe reicht
nicht. Originaldateien, lokale absolute Pfade, Credentials und interne Serverdaten
werden nicht als zusätzliche Payloadfelder ergänzt. Alle Raw-/Transcript-/Receipt-
und Provenienzhashes bleiben bindend. Bei Konflikten wird gestoppt, nicht repariert.

Inventar liest nur Adapterdateien im expliziten Workspace und optional benannte
Kandidaten darunter. Symlinks/Traversal sind ausgeschlossen. Kandidaten werden
niemals automatisch gebunden; SRT-Syntaxinspektion erzeugt weder Receipt noch
normalisierte Datei. Platzhaltermetadaten, die der vorhandene Importer intern für
eine ungebundene Syntaxprüfung verlangt, werden nicht als Provenienz ausgegeben.
Reports enthalten Hashes/relative Referenzen und echte Zeiten, keinen Transcripttext.

Secrets gehören weder in Git/Reports noch in Streamlit-Sessionstate oder Logs.
Dieses Paket berührt keine UI. Ein Admin-Key berechtigt Qdrant selbst weiterhin
zu administrativen Aktionen; die CLI ist keine allgemeine Autorisierungsschicht.
Lesekey getrennt halten, Proxyheader nicht protokollieren, Backups verschlüsseln.
Snapshots enthalten ebenfalls Texte und Vektoren und benötigen dieselbe Freigabe.

Keine Abhängigkeiten wurden hinzugefügt oder installiert; weder Modelle noch
Container wurden heruntergeladen. Kein LLM, extrahierter Code oder produktiver
Server wurde aufgerufen. Die bekannten sechs zeitlosen TXT-Modellfehler bleiben
unverändert; fehlende Zeiten werden in diesem Pilot nicht erfunden.

## Separater SDK-Versionsprobe

`qdrant-client==1.19.1` startet standardmäßig eine Hintergrund-Versionsabfrage.
Dieser Pfad verwendet einen eigenen `httpx.get` und übernimmt die für den
REST-Client gesetzte `trust_env=False`-Option nicht. Daher wird ausschließlich
`check_compatibility=False` gesetzt; TLS-Zertifikate werden weiterhin regulär
geprüft. Serverversion und Image-Digest müssen vor dem Pilot ausdrücklich über
den freigegebenen Zugriff beziehungsweise das geprüfte Image verifiziert werden.
Ein SDK-Warnhinweis ist ohnehin keine verbindliche Serverabnahme.

Versionsgebundene Primärquellen:
[QdrantRemote](https://github.com/qdrant/qdrant-client/blob/v1.19.1/qdrant_client/qdrant_remote.py),
[separate Versionsabfrage](https://github.com/qdrant/qdrant-client/blob/v1.19.1/qdrant_client/common/version_check.py).
Der Offline-Konstruktortest verlangt die deaktivierte Hintergrundabfrage; ein
realer Netzwerk-/TLS-Test bleibt bis zur SDK-/Instanzbereitstellung offen.
