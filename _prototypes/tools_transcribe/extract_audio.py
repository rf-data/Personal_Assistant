## extract_audio.py
# import
import sounddevice as sd
from pydub import AudioSegment
from scipy.io import wavfile

"""
(1)
> sudo apt update && sudo apt install portaudio19-dev alsa-utils ffmpeg -y

Verwende Code mit Vorsicht.

Danach installieren Sie die benötigten Python-Bibliotheken:
> pip install sounddevice scipy pydub


(2)
Da das Skript innerhalb der Linux-Umgebung von ChromeOS läuft, müssen Sie ChromeOS mitteilen,
dass die Linux-Apps Zugriff auf Ihr Mikrofon und das Systemaudio haben dürfen:
- Öffnen Sie die ChromeOS-Einstellungen.
- Gehen Sie zu Erweitert -> Entwickler -> Linux-Entwicklungsumgebung.
- Aktivieren Sie den Schalter „Linux-Apps den Zugriff auf Ihr Mikrofon erlauben“.

Hinweis zum Systemaudio (Video-Ton): Das Aufnehmen des internen Systemtons (was aus den Lautsprechern kommt)
 von Linux kann auf manchen Chromebooks Treiber-Anpassungen (PulseAudio / pavucontrol) erfordern,
 da Linux standardmäßig primär das  physische Mikrofon sieht. Das Skript listet Ihnen beim Start alle verfügbaren
 Kanäle auf, sodass Sie die Gerätenummer im Code bei sd.rec(..., device=X) anpassen können, falls nötig.

Soll ich Ihnen zeigen, wie Sie über ein zusätzliches Linux-Tool namens PulseAudio Volume Control den Ton
Ihres Chrome-Browsers direkt intern in dieses Python-Skript umleiten können?
"""


def live_record_audio():
    # --- EINSTELLUNGEN ---
    SAMPLE_RATE = 44100  # CD-Qualität
    CHANNELS = 2  # Stereo
    TEMP_WAV = "temp_aufnahme.wav"
    OUTPUT_MP3 = "mein_meeting_ton.mp3"

    print("=" * 45)
    print(" CHROMEBOOK PYTHON AUDIO RECORDER ")
    print("=" * 45)
    print("Verfügbare Audiogeräte werden gelistet...\n")
    print(sd.query_devices())
    print("-" * 45)

    try:
        # Dauer abfragen oder manuell stoppen vorbereiten
        dauer_input = input(
            "Wie viele Minuten soll aufgenommen werden? (Oder 'm' für manuellen Stopp): "
        )

        if dauer_input.lower() == "m":
            print(
                "\n[INFO] Aufnahme startet. Drücke STRG+C im Terminal, um die Aufnahme zu BEENDEN."
            )
            # Endlos-Aufnahme (wird per Tastatur-Interrupt gestoppt)
            aufnahme = sd.rec(
                int(3600 * 4 * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
            )
            while True:
                sd.wait(1000)
        else:
            sekunden = int(float(dauer_input) * 60)
            print(f"\n[INFO] Aufnahme läuft für {dauer_input} Minute(n)...")
            aufnahme = sd.rec(
                int(sekunden * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
            )
            sd.wait()  # Warten bis die Zeit abgelaufen ist

    except KeyboardInterrupt:
        print("\n[INFO] Aufnahme manuell gestoppt.")
        # Nur die tatsächlich aufgenommenen Samples behalten
        sd.stop()
        # Findet heraus, wie viel tatsächlich aufgenommen wurde, um Stille am Ende abzuschneiden
        aufnahme = aufnahme[: sd.get_stream().time]

    except ValueError:
        print("[FEHLER] Ungültige Eingabe.")
        exit()

    # 1. Temporär als WAV speichern
    print("[Prozess] Speichere Rohdaten...")
    wavfile.write(TEMP_WAV, SAMPLE_RATE, aufnahme)

    # 2. Direkt lokal in MP3 umwandeln
    print("[Prozess] Konvertiere in MP3-Format...")
    audio = AudioSegment.from_wav(TEMP_WAV)
    audio.export(OUTPUT_MP3, format="mp3", bitrate="192k")
    # Temporäre Datei aufräumen
    if os.path.exists(TEMP_WAV):
        os.remove(TEMP_WAV)

    print(f"\n✅ FERTIG! Die Datei wurde als '{OUTPUT_MP3}' gespeichert.")

    return


def extract_audio_from_video(video_path: str, save_path):
    # Pfad zu Ihrer aufgenommenen WebM-Videodatei
    #  = "aufnahme.webm"

    # Audio aus dem Video extrahieren
    audio = AudioSegment.from_file(video_path, format="webm")

    # Als reine MP3-Audiodatei lokal abspeichern
    audio.export(save_path, format="mp3", bitrate="192k")

    print("Konvertierung erfolgreich abgeschlossen!")
