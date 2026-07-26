## templates_sop.py
# import

from src.model_rag.classes_sop import (
                                    SOPChapter,
                                    SOPTemplate,
                                    SOPType
                                    )


SOP_BASE_TEMPLATE = SOPTemplate(
    sop_type=SOPType.GENERAL,
    chapters=[
        SOPChapter(
            order=5,
            # level=1,
            kind="core",
            name="Durchführung",
            knowledge_source="retrieval",
            # etreten des Herstellungsraumes",
            # text="Der Anreicher hat ,
            # beim Betreten des Herstellungsraumes die Arbeitsanweisungen AA Hygieneplan und AA Ein- und Ausschleusen von Personal einzuhalten.",
        ),
        SOPChapter(
            name="Ziel",
            order=1,
            text="",
            knowledge_source="core_chapters",
            # Beschreibung der Tätigkeiten am Arbeitsplatz des Anreichers im Herstellungsraum",
        ),
        SOPChapter(
            name="Geltungsbereich",
            order=2,
            text="",
            knowledge_source="core_chapters",
            # Abteilung Sterilherstellung",
        ),
        SOPChapter(
            name="Zuständigkeit", order=3, text="", knowledge_source="core_chapters"
        ),
        SOPChapter(name="Begriffe", order=4, text="", knowledge_source="core_chapters"),
        SOPChapter(
            name="Mitgeltende Unterlagen",
            order=6,
            text="",
            knowledge_source="core_chapters",
        ),
        SOPChapter(
            name="Änderungshistorie", order=7, text="", knowledge_source="core_chapters"
        ),
    ],
)


SOP_REVISE_TEMPLATE = SOPTemplate(
    sop_type=SOPType.GENERAL,
    chapters=[
        SOPChapter(
            order=5,
            level=1,
            kind="core",
            name="Betreten des Herstellungsraumes",
            text="Der Anreicher hat beim Betreten des Herstellungsraumes die Arbeitsanweisungen AA Hygieneplan und AA Ein- und Ausschleusen von Personal einzuhalten.",
        ),
        SOPChapter(
            order=5,
            level=2,
            kind="core",
            name="Vorbereitung der Herstellung",
            text="""
[Row #0]:
[Row #1]:		|	Der Anreicher schaltet nach Betreten des Herstellungsraumes die Lüftung der LAF-Bank ein.	|	D
[Row #2]:		|	Der Anreicher desinfiziert seinen Arbeitsplatz im Herstellungsraum und den Arbeitsplatz des Herstellers in der LAF-Bank gemäß AA Hygieneplan.	|	D
[Row #3]:		|	Sobald die LAF-Bank betriebsbereit ist, startet der Anreicher den Partikelzähler.	|	D
[Row #4]:		|	Der Anreicher entnimmt die Materialien unter Einhaltung der AA Ein- und Ausschleusen aus der Materialschleuse und ordnet AA Herstellungsanweisung / protokoll und zugehörige Materialien auf seinem Arbeitsplatz.
Bei der Zuordnung prüft er alle Materialien auf Übereinstimmung von Verfall und Chargenbezeichnung mit den jeweiligen Herstellungsprotokollen.	|	D
[Row #5]:		|	Der Anreicher stellt gemäß AA Mikrobiologisches Monitoring vor Beginn der Herstellung Sedimentationsplatten in der LAF-Bank auf.	|	D
""",
        ),
        SOPChapter(
            order=5,
            level=3,
            name="Herstellung",
            text="""
[Row #0]:
[Row #1]:		|	Der Anreicher übergibt dem Hersteller sterile Verbrauchsmaterialien, indem er sie ausgepeelt anreicht.	|	D, B
[Row #2]:		|	Der Anreicher übergibt dem Hersteller Hilfsstoffe und Arzneistoffe für die jeweilige Herstellung.	|	D, B
[Row #3]:		|	Bei Arzneimitteln und Hilfsstoffen nennt der Anreicher die jeweilige vollständige Bezeichnung und die benötigte Menge gemäß AA Herstellungsanweisung /-protokoll.	|	D, B
[Row #4]:		|	Der Anreicher überprüft die vom Hersteller wiederholten Bezeichnungen und Mengen und bestätigt diese mündlich sowie im Herstellungsprotokoll.	|	D, B
[Row #5]:		|	Vom Hersteller fertiggestellte Beutel werden vom Anreicher entgegengenommen und am Arbeitsplatz des Anreichers den Herstellungsdokumenten zugeordnet und etikettiert.
Dabei bestätigt der Anreicher die erfolgten Inprozesskontrollen im Herstellungsprotokoll.	|	D, B
[Row #6]:		|	Der Anreicher nimmt die Abfälle aus der LAF-Bank vom Hersteller entgegen und sammelt diese in einem Transportkorb.	|	D, B
[Row #7]:		|	Wiederholung der Schritte 1 bis 6 für weitere Herstellungen	|	D, B
""",
        ),
        SOPChapter(
            order=5,
            level=4,
            name="Nachbereitung der Herstellung",
            text="""
[Row #0]:
[Row #1]:		|	Hergestellte Beutel werden am Arbeitsplatz des Anreichers in Folienschläuche eingeschweißt.	|	D
[Row #2]:		|	Die hergestellten und eingeschweißten Beutel werden zusammen mit den Herstellungsdokumenten unter Einhaltung der AA Ein- und Ausschleusen von Material aus dem Herstellungsraum in den Vorbereitungsraum geschleust.	|	D, I
[Row #3]:		|	Anschließend werden die Abfälle aus dem Herstellungsraum unter Einhaltung der AA Ein- und Ausschleusen von Material aus dem Herstellungsraum in den Vorbereitungsraum überführt.	|	D, I
[Row #4]:		|	Am Ende jeder Arbeitssitzung werden die Fingerprinttests gemäß AA Mikrobiologisches Monitoring durchgeführt sowie die Sedimentationsplatten verschlossen und beschriftet.	|	D
[Row #5]:		|	Die LAF-Bank und der Partikelzähler werden ausgeschaltet.	|	D
""",
        ),
        # ],
        # support_chapter = [
        SOPChapter(
            name="Ziel",
            order=1,
            text="Beschreibung der Tätigkeiten am Arbeitsplatz des Anreichers im Herstellungsraum",
        ),
        SOPChapter(
            name="Geltungsbereich",
            order=2,
            text="Abteilung Sterilherstellung",
        ),
        SOPChapter(
            name="Zuständigkeit",
            order=3,
            text="""
[Row #0]:
[Row #1]:	prozessverantwortlich	|	PV	|	Apothekenleitung
[Row #2]:	führt durch	|	D	|	Anreicher
[Row #3]:	ist beteiligt	|	B	|	Hersteller
[Row #4]:	wird informiert	|	I	|	Vorbereiter
[Row #5]:	vertritt	|	V	|	-
""",
        ),
        SOPChapter(
            name="Begriffe",
            order=4,
            text="""
- AA: Arbeitsanweisung
""",
        ),
        SOPChapter(
            name="Mitgeltende Unterlagen",
            order=6,
            text="""
- AA Hygieneplan
- AA Ein- und Ausschleusen von Personal
- AA Ein- und Ausschleusen von Material
- AA Herstellungsanweisung / -protokoll Schmerzbeutel
- AA Mikrobiologisches Monitoring
""",
        ),
        SOPChapter(
            name="Änderungshistorie",
            order=7,
            text="""
[Row #0]:
[Row #1]:		|		|
[Row #2]:		|		|
""",
        ),
    ],
)
