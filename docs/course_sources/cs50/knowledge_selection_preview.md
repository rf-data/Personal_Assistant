# CS50 Processing Preview

Offline-Dry-Run; keine ResourceTasks werden erzeugt oder ausgeführt.

## cs50x

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:91c0658a4ad3439e9c5a009bbc58715312bdd6fa867a2811e036517881630e23`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a40a9024f8d0e2ce7d6eddd39133a7623a611f76558ceef0200ab2033217ca5c`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0.mp3
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/pt/aula0.txt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/en/lecture0.txt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/es/clase0.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/en/lecture0.srt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/pt/aula0.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/0/lang/es/clase0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/es/clase0-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/lecture0-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/0/pt/aula0-720p.mp4
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/GHZzYAy4NKA
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/UuIEbpQms8o
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/nfYOp3_SyqM
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/GHZzYAy4NKA
- `lecture_video` `en/youtube/?/?`: https://youtu.be/UuIEbpQms8o
- `lecture_video` `es/youtube/?/?`: https://youtu.be/nfYOp3_SyqM

</details>

### Abschnitt 1

Vorlesung: `resource:7a75f0d6e59a66554af26d8b60b93a93c65ef2fdf85a1f0e72b3250f9a5f6273`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:0adc37339cced37f5722373b94f804accdeef93cdb5416f32c46a82c90ec9a43`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/en/lecture1.srt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/pt/aula1.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/es/clase1.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/en/lecture1.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1.mp3
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/pt/aula1.txt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/1/lang/es/clase1.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/es/clase1-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/lecture1-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/1/pt/aula1-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/7hxVvUoo-PI
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/SlqjA04_dpk
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/eepzDoovmAw
- `lecture_video` `es/youtube/?/?`: https://youtu.be/7hxVvUoo-PI
- `lecture_video` `en/youtube/?/?`: https://youtu.be/SlqjA04_dpk
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/eepzDoovmAw

</details>

### Abschnitt 2

Vorlesung: `resource:b822002b41832d5f54bea82bd22c4b350487451219b6e1b4d70abcd184de2971`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:f64259c2ae415839a7e22398386b51fe00e22093f660d786686f4ca384b3fd7d`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/pt/aula2.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/en/lecture2.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/pt/aula2.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2.mp3
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/es/clase2.srt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/es/clase2.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/2/lang/en/lecture2.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/es/clase2-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/lecture2-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/2/pt/aula2-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/G7erq8mRYdk
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/h5Gc1n8ZuU8
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/vdCJU-1mB-A
- `lecture_video` `es/youtube/?/?`: https://youtu.be/G7erq8mRYdk
- `lecture_video` `en/youtube/?/?`: https://youtu.be/h5Gc1n8ZuU8
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/vdCJU-1mB-A

</details>

### Abschnitt 3

Vorlesung: `resource:92006890aadbf41ba3bb6d2b4abc48f1b5ab32115e5a9a86b64490cc450b4f3e`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a10ae1eb6e74d9d53da63cb581349ef35df6d3889dc39347d814ea3488945c6b`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/es/clase3.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3.mp3
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/es/clase3.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/en/lecture3.srt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/pt/aula3.srt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/pt/aula3.txt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/3/lang/en/lecture3.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/es/clase3-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/lecture3-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/3/pt/aula3-720p.mp4
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/1dV61IMUwIc
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/6Svu_ae5ebk
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/zU0DbilHvYM
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/1dV61IMUwIc
- `lecture_video` `en/youtube/?/?`: https://youtu.be/6Svu_ae5ebk
- `lecture_video` `es/youtube/?/?`: https://youtu.be/zU0DbilHvYM

</details>

### Abschnitt 4

Vorlesung: `resource:e33059564d0f2a2fef12efcdb3d4bf8a8fdd28157680748f3679fe74e7ec73e1`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:8587c2d8123fcd3d7eba9f30f42d8ad2ff054e3c35ff2f7d76eef4c53048c350`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/pt/aula4.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/en/lecture4.srt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/es/clase4.txt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/en/lecture4.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4.mp3
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/es/clase4.srt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/4/lang/pt/aula4.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/es/clase4-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/lecture4-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/4/pt/aula4-720p.mp4
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/DweS4KseeDE
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/db0H0U13YsA
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/xRW70LgrEho
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/DweS4KseeDE
- `lecture_video` `en/youtube/?/?`: https://youtu.be/db0H0U13YsA
- `lecture_video` `es/youtube/?/?`: https://youtu.be/xRW70LgrEho

</details>

### Abschnitt 5

Vorlesung: `resource:eed936de053b3265331c647657155733c847b1a38cd196e5cd700f97c4a4ba5b`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:9ed86918ff2b2a3e6ecdd37dd0d74e6e893e57e59caa14e0f7dc9846a93a36cf`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/5/lang/en/lecture5.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/es/clase5.srt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/pt/aula5.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/en/lecture5.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/en/lecture5.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5.mp3
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/es/clase5.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/5/lang/pt/aula5.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/es/clase5-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/lecture5-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/5/pt/aula5-720p.mp4
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/PmAI76OGE_E
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/Q0xvQT87ekA
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/pttqNxchp9k
- `lecture_video` `en/youtube/?/?`: https://youtu.be/PmAI76OGE_E
- `lecture_video` `es/youtube/?/?`: https://youtu.be/Q0xvQT87ekA
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/pttqNxchp9k

</details>

### Abschnitt 6

Vorlesung: `resource:18417d9b05fcfe97cc69f445c627d6ec08a6b7c21d89e0a87db883ac45b58679`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:abe3ecbbf5ecfd3f46c6fec217d4b303cc9cd25612d86096a0046af41365dcb7`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/6/lang/en/lecture6.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/en/lecture6.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/en/lecture6.txt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/pt/aula6.srt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/es/clase6.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/pt/aula6.txt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/6/lang/es/clase6.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/es/clase6-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/lecture6-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/6/pt/aula6-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/N3zVFYQu3bU
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/Rl0ludWTLxs
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/iIG8j9kWlIY
- `lecture_video` `es/youtube/?/?`: https://youtu.be/N3zVFYQu3bU
- `lecture_video` `en/youtube/?/?`: https://youtu.be/Rl0ludWTLxs
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/iIG8j9kWlIY

</details>

### Abschnitt 7

Vorlesung: `resource:d446ec762fea8c2dbee6f7b592c95b4c6d2544420d5ffad8412c38f5a9a35623`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:ff8a0bb39e7c813e79eb5405df9af0d304e529c1962a509fc2aca059c3169909`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/7/lang/en/lecture7.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/es/clase7.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/pt/aula7.txt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/pt/aula7.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/es/clase7.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/en/lecture7.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/7/lang/en/lecture7.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/es/clase7-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/lecture7-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/7/pt/aula7-720p.mp4
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/Samqz7iHwPM
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/VnfMRaZUSrc
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/oqRU2So6Z2Y
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/Samqz7iHwPM
- `lecture_video` `es/youtube/?/?`: https://youtu.be/VnfMRaZUSrc
- `lecture_video` `en/youtube/?/?`: https://youtu.be/oqRU2So6Z2Y

</details>

### Abschnitt ai

Vorlesung: `resource:7bd4e5d2b56dac6ea6ec921d21629b6851f8bc4be167023ca3f1f1c32d359574`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:f5d35347214504d3decbc941e552a2d012e0ce9877682dc33b8ed15cf9903194`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/ai/lang/en/ai.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/ai.mp3
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/es/ai-es.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/pt/ai-pt.txt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/pt/ai-pt.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/es/ai-es.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/en/ai.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/ai/lang/en/ai.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/ai-720p.mp4
- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/es/ai-es-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/ai/pt/ai-pt-720p.mp4
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/-9bo8HlSxwQ
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/MTSE0ZOpyDc
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/YFzkVvjiPmM
- `lecture_video` `en/youtube/?/?`: https://youtu.be/-9bo8HlSxwQ
- `lecture_video` `es/youtube/?/?`: https://youtu.be/MTSE0ZOpyDc
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/YFzkVvjiPmM

</details>

### Abschnitt 8

Vorlesung: `resource:354fdcfc1f67be18950028e6a78c5ca996e2f0488079bb689cee951d2217e188`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:ecd576c510ac6f470c01874cde7abd17e6fc48766e4f5e75552ee69027627594`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/8/lang/en/lecture8.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/pt/aula8.srt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/es/clase8.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/pt/aula8.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8.mp3
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/es/clase8.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/en/lecture8.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/8/lang/en/lecture8.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/es/clase8-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/lecture8-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/8/pt/aula8-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/3Ph5G_sfrFM
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/i_GmZgveqpw
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/yYst7puZXjw
- `lecture_video` `es/youtube/?/?`: https://youtu.be/3Ph5G_sfrFM
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/i_GmZgveqpw
- `lecture_video` `en/youtube/?/?`: https://youtu.be/yYst7puZXjw

</details>

### Abschnitt 9

Vorlesung: `resource:e8d479f1a4c9c8ed47a4a791311d33d0adcc36e00ef95783bfd526090d1763bd`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:e3dc089b2c36b691596f5f7d16e2228a98a362dcfabc7dc014191a892dea2583`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/9/lang/en/lecture9.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9.mp3
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/pt/aula9.txt
- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/es/clase9.txt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/pt/aula9.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/es/clase9.srt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/en/lecture9.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/9/lang/en/lecture9.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/es/clase9-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/lecture9-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/9/pt/aula9-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/7Yd_xMuzPHE
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/Uddye35TNp4
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/am7POvSZ4GE
- `lecture_video` `es/youtube/?/?`: https://youtu.be/7Yd_xMuzPHE
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/Uddye35TNp4
- `lecture_video` `en/youtube/?/?`: https://youtu.be/am7POvSZ4GE

</details>

### Abschnitt 10

Vorlesung: `resource:86c1293f53071fd6c89c9fdbadf4fb700b87bab814705a61754c2b13e51f0609`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:cabacb204cba2652ba8d94b71f0b43dcd714e28e768a55d8fcf48ba94cd28959`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/2025/fall/lectures/10/lang/en/lecture10.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `es/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/es/clase10.txt
- `subtitles` `pt/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/pt/aula10.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/en/lecture10.txt
- `transcript` `pt/txt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/pt/aula10.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/en/lecture10.srt
- `subtitles` `es/srt/?/?`: https://cdn.cs50.net/2025/fall/lectures/10/lang/es/clase10.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `es/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-1080p-hdr.mp4
- `lecture_video` `es/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-1080p.mp4
- `lecture_video` `es/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-360p-hdr.mp4
- `lecture_video` `es/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-360p.mp4
- `lecture_video` `es/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-4k-hdr.mp4
- `lecture_video` `es/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-4k.mp4
- `lecture_video` `es/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-720p-hdr.mp4
- `lecture_video` `es/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/es/clase10-720p.mp4
- `lecture_video` `en/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-1080p-hdr.mp4
- `lecture_video` `en/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-1080p.mp4
- `lecture_video` `en/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-360p-hdr.mp4
- `lecture_video` `en/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-360p.mp4
- `lecture_video` `en/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-4k-hdr.mp4
- `lecture_video` `en/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-4k.mp4
- `lecture_video` `en/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-720p-hdr.mp4
- `lecture_video` `en/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/lecture10-720p.mp4
- `lecture_video` `pt/mp4/1080p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-1080p-hdr.mp4
- `lecture_video` `pt/mp4/1080p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-1080p.mp4
- `lecture_video` `pt/mp4/360p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-360p-hdr.mp4
- `lecture_video` `pt/mp4/360p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-360p.mp4
- `lecture_video` `pt/mp4/4k/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-4k-hdr.mp4
- `lecture_video` `pt/mp4/4k/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-4k.mp4
- `lecture_video` `pt/mp4/720p/hdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-720p-hdr.mp4
- `lecture_video` `pt/mp4/720p/sdr`: https://cdn.cs50.net/2025/fall/lectures/10/pt/aula10-720p.mp4
- `lecture_video` `es/cs50_player/?/?`: https://video.cs50.io/0IjFxHxs88c
- `lecture_video` `en/cs50_player/?/?`: https://video.cs50.io/ApQTgFkf8TU
- `lecture_video` `pt/cs50_player/?/?`: https://video.cs50.io/sQBEFAwdvxc
- `lecture_video` `es/youtube/?/?`: https://youtu.be/0IjFxHxs88c
- `lecture_video` `en/youtube/?/?`: https://youtu.be/ApQTgFkf8TU
- `lecture_video` `pt/youtube/?/?`: https://youtu.be/sQBEFAwdvxc

</details>

Discovery-Warnungen:

- local_embed_ignored: Browser-local iframe ignored; explicit media links retained
- local_embed_ignored: Browser-local iframe ignored; explicit media links retained
- unknown_resource_role: Unknown list context: Seminars

## cs50_python

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:4305fcd17cb0d9c50cfdd5e2718461e8369cb883189de96bda796f04cc800192`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:fde25833bbf19ce14828f9b719ded15fe02cc15f313551b1357c34f571f5e0b5`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/0/lecture0-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/JP7ITIXGpHk
- `lecture_video` `?/youtube/?/?`: https://youtu.be/JP7ITIXGpHk

</details>

### Abschnitt 1

Vorlesung: `resource:0ac32275ad6b04d5683ad2ae3dd51987f886e5620d70bf4797cec43882a2e0c6`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:c9b9f6934d21bbc711209656ee9b00d587e7dc5b98228c64e2c21e0031eaacaf`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/1/lang/en/lecture1.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/1/lang/en/lecture1.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/1/lecture1-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/_b6NgY_pMdw
- `lecture_video` `?/youtube/?/?`: https://youtu.be/_b6NgY_pMdw

</details>

### Abschnitt 2

Vorlesung: `resource:0640c3447d40324db523c13da99ca6d6a6c5de11bf73b148d937432b10b75eb5`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:ffebcd082ec15e1d3d489c2c1837a35c460d1c5491f4c2d7eb2a2ccc72e1b923`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/2/lang/en/lecture2.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/2/lang/en/lecture2.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/2/lecture2-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/-7xg8pGcP6w
- `lecture_video` `?/youtube/?/?`: https://youtu.be/-7xg8pGcP6w

</details>

### Abschnitt 3

Vorlesung: `resource:d97ecd038549fbe5efedb90ce50365a22638cfe590afcb7bafebc8821bbf7bfa`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:73bde05c233ad856c7102772b72f997df2c33690506a4304f206c3420de4fe9c`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/3/lang/en/lecture3.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/3/lang/en/lecture3.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/3/lecture3-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/LW7g1169v7w
- `lecture_video` `?/youtube/?/?`: https://youtu.be/LW7g1169v7w

</details>

### Abschnitt 4

Vorlesung: `resource:0165b5d4d2543a75889250f388a8ca88c827fbc0a81ffad0ba19c23ac131f8c4`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:32d6f17f17851f9038165291d829163621f4ea717507220d4a325bd9caf081d0`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/4/lang/en/lecture4.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/4/lang/en/lecture4.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/4/lecture4-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/MztLZWibctI
- `lecture_video` `?/youtube/?/?`: https://youtu.be/MztLZWibctI

</details>

### Abschnitt 5

Vorlesung: `resource:06f1c7a3c1e8937e625c36361c21171a1f24440b5a4ff5076c076ebdc4a4b845`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:1fef912216f964feafcc745cc7d42d7107f6f03094db66023e3f0f13693a7de4`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/5/lang/en/lecture5.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/5/lang/en/lecture5.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/5/lang/en/lecture5.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/5/lecture5-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/tIrcxwLqzjQ
- `lecture_video` `?/youtube/?/?`: https://youtu.be/tIrcxwLqzjQ

</details>

### Abschnitt 6

Vorlesung: `resource:8b508c2d60083b0668764dfc0e11967c2144597c74d66f918d140738eea827a0`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:55e91be228c9c6069f1289e0b61b2133938dc77dd3f9131a62b0fc0d4241ffec`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/6/lang/en/lecture6.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/6/lang/en/lecture6.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/6/lang/en/lecture6.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/6/lecture6-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/KD-Yoel6EVQ
- `lecture_video` `?/youtube/?/?`: https://youtu.be/KD-Yoel6EVQ

</details>

### Abschnitt 7

Vorlesung: `resource:2a64b933450c95de2a685296814d4e393853f50c1a905df75f539800249f6dd8`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:97a4613719809609b43964ba92a82074c269bf47fcdc8755e809520fa36b2166`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/7/lang/en/lecture7.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/7/lang/en/lecture7.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/7/lang/en/lecture7.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/7/lecture7-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/hy3sd9MOAcc
- `lecture_video` `?/youtube/?/?`: https://youtu.be/hy3sd9MOAcc

</details>

### Abschnitt 8

Vorlesung: `resource:0d88144c34581d4a70420382590006ceab47d9fec78282a1294562af83cb5e2d`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:9a019d0d913ca947428432232dce5732c4b02d179494fa14b26b94ebde755588`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/8/lang/en/lecture8.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/8/lang/en/lecture8.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/8/lang/en/lecture8.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/8/lecture8-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/e4fwY9ZsxPw
- `lecture_video` `?/youtube/?/?`: https://youtu.be/e4fwY9ZsxPw

</details>

### Abschnitt 9

Vorlesung: `resource:a4f57f9dac8e4e67d66d068cb7269237781c21b188587c0fccc15ccbcbc66609`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:c6bbbf62488e1ca2e54150883ed64db277dd29746876fcd8412040153f9bdc8a`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/python/2022/x/lectures/9/lang/en/lecture9.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/9/lang/en/lecture9.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/python/2022/x/lectures/9/lang/en/lecture9.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9-1080p.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9-4k.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/python/2022/x/lectures/9/lecture9-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/6pgodt1mezg
- `lecture_video` `?/youtube/?/?`: https://youtu.be/6pgodt1mezg

</details>

Discovery-Warnungen:

- local_embed_ignored: Browser-local iframe ignored; explicit media links retained
- local_embed_ignored: Browser-local iframe ignored; explicit media links retained

## cs50_sql

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:a1caea02137904aa96aa9816d68b0fa45312752479fc123c071d65790dd11fd6`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:e7ffdb3c4b381e5a9e17ba60349e6bbfca673c3c54e568ac3e7901518f6fb4b5`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/0/lang/en/lecture0.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/0/lang/en/lecture0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/0/lecture0-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/vHYeChEf2lA?screen=6UZILCexEZ4
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=vHYeChEf2lA

</details>

### Abschnitt 1

Vorlesung: `resource:0c8aa211765d9affb4fc3f3297a9b0d97dd8afb5d4105ee55564b17a0e3adc75`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:1f69fabd1a64cfd4f3463cfab6139b3cbef33009a8f9e0a4d65d05933e77026f`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/1/lang/en/lecture1.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/1/lang/en/lecture1.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/1/lecture1-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/_2t18Hy9Z0Y?screen=2OrXwf138gs
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=_2t18Hy9Z0Y

</details>

### Abschnitt 2

Vorlesung: `resource:ba78ba6245a25ad9c431b5bf42b2fd2fcd0fb05a432e63a19b521d2b6a18af44`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a1e2e2aecfc19c0d17cc7386315b8767c31f8a371240a854bbb144bd74e9b006`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/2/lang/en/lecture2.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/2/lang/en/lecture2.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/2/lecture2-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/QzRW6bfv3Fo?screen=YH12F1iGeUM
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=QzRW6bfv3Fo

</details>

### Abschnitt 3

Vorlesung: `resource:d0701b163c2fc90e73459f38bb31bf0b661b325594dc1d1cf3a1df1b1aaa8912`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a8a89584e8f1e1044da3f71e775aa1a2292e689287722121be92388b1734338a`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/3/lang/en/lecture3.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/3/lang/en/lecture3.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/3/lecture3-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/BD08USRd2M8?screen=wZP4n4UWiW8
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=BD08USRd2M8

</details>

### Abschnitt 4

Vorlesung: `resource:cb135b2b969e639f9ba4557e2200abe03ee95329d79540c43ab384339fd74725`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:2dedf5e82d09024125016ec378b3a1428d9ee21df6e4b7605190ad8bb577cb7f`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/4/lang/en/lecture4.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/4/lang/en/lecture4.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/4/lecture4-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/jZwGVuA8PMI?screen=c5fXV3WTu5Y
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=jZwGVuA8PMI

</details>

### Abschnitt 5

Vorlesung: `resource:1a6013e971c0a86a054f70e12da6ca89be79cb0d2a266b818875ee83a2447af3`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:7d4fd395bd9a70f7e2386c1ccef0f80246930c8ee09d45482e92b0166af33d4e`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/5/lang/en/lecture5.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/5/lang/en/lecture5.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/5/lang/en/lecture5.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/5/lecture5-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/qa5-mKVSQHQ?screen=0a6O0p5QANQ
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=qa5-mKVSQHQ

</details>

### Abschnitt 6

Vorlesung: `resource:d7cbc18cba0dd912415c5d0ab0e61a9a7695cb075d3bbdd0b09bfe2472f22e80`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:8f1afc6a78ba3232118eda3cfb74548b51ab25cb304cd799c4d6ee91c1815713`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/sql/2023/x/lectures/6/lang/en/lecture6.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/6/lang/en/lecture6.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/sql/2023/x/lectures/6/lang/en/lecture6.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/sql/2023/x/lectures/6/lecture6-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/jXbXGkgT2Xg?screen=Eq8bWuMA4PM
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=jXbXGkgT2Xg

</details>

Discovery-Warnungen:

- local_embed_ignored: Browser-local iframe ignored; explicit media links retained
- local_embed_ignored: Browser-local iframe ignored; explicit media links retained

## cs50_ai

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:3bbc1b2d5f7b6deb981866b3fceedbfcfe1c9f458d801c0ab51a34b793e28646`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:e6b1fee6d03d3680442eef8e35eea741f9e9f992e42000bf77bb9fc38cb52e05`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lang/en/lecture0.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lecture0.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lang/en/lecture0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lecture0-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lecture0-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lecture0-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/0/lecture0-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/WbzNRTTrX0g?screen=0Towr-pBuzw
- `lecture_video` `?/youtube/?/?`: https://youtu.be/WbzNRTTrX0g

</details>

### Abschnitt 1

Vorlesung: `resource:ed0af48a7c34bed3e70f2d5cc93844294a50bfd3047c67937171114fc3dc1a68`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:89304249a7a535f4b88bc4ed3ac50e9bb63e9cf193f59ff2bee7fa18e94c49bc`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lecture1.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lang/en/lecture1.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lang/en/lecture1.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lecture1-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lecture1-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lecture1-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/1/lecture1-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/HWQLez87vqM?screen=TpMZeDdiNN8
- `lecture_video` `?/youtube/?/?`: https://youtu.be/HWQLez87vqM

</details>

### Abschnitt 2

Vorlesung: `resource:bcb318d66abdc6e0ef791379eb04ebd11ad40c0fcb7449c037cdeca891297edd`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:480871d0d10a6ef0c9dbcbd4950c2ac7f58f82f901a5d9670a03fd398d0d4145`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lang/en/lecture2.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lang/en/lecture2.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lecture2.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lecture2-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lecture2-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lecture2-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/2/lecture2-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/D8RRq3TbtHU?screen=B8mmqm46G80
- `lecture_video` `?/youtube/?/?`: https://youtu.be/D8RRq3TbtHU

</details>

### Abschnitt 3

Vorlesung: `resource:2557704e2e7a2bf899c60f4deab3d0e843f3faac2c7816975a6f5eb5938b3c15`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:9ebd2ef85d7fa6bb33c4a1e6283f15157e137ff5f085a0846610acfd30ff78af`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lang/en/lecture3.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lecture3.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lang/en/lecture3.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lecture3-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lecture3-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lecture3-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/3/lecture3-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/qK46ET1xk2A?screen=FuiKloIZRhM
- `lecture_video` `?/youtube/?/?`: https://youtu.be/qK46ET1xk2A

</details>

### Abschnitt 4

Vorlesung: `resource:7a5aa4069ff59bd3b4a6a68c4d1acc27a9da7e25cf24abdec436e8b7555d4e36`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:fcba897c0d3a3591ddd3a8209feecd2ebf73de4832b6edad8761bb62a72c4a86`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lecture4.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lang/en/lecture4.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lang/en/lecture4.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lecture4-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lecture4-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lecture4-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/4/lecture4-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/-g0iJjnO2_w?screen=xpyjJYdb5yg
- `lecture_video` `?/youtube/?/?`: https://youtu.be/-g0iJjnO2_w

</details>

### Abschnitt 5

Vorlesung: `resource:a45f310c348b6e4fa05a92f822a99e2c557a963edadc77ccf4f4f59cb4bfe214`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:7821ff6957224b4f6875b2af55d63c1d2a21509bae89a53edb2faa6b46273391`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2020/spring/lectures/5/lang/en/lecture5.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lang/en/lecture5.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lecture5.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lang/en/lecture5.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lecture5-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lecture5-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lecture5-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2020/spring/lectures/5/lecture5-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/J1QD9hLDEDY?screen=qNDOwwNlCD0
- `lecture_video` `?/youtube/?/?`: https://youtu.be/J1QD9hLDEDY

</details>

### Abschnitt 6

Vorlesung: `resource:69bb7c1cbb94de9b59657bf409dfdc67b4a2402fe05bf75bd6f47358751f18e1`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a052a17f0d3bd2455faa93f156f8c9b08a4d69e975afd79e0d57c690d7199548`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/ai/2023/x/lectures/6/lang/en/lecture6.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lang/en/lecture6.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lang/en/lecture6.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lecture6.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lecture6-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lecture6-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lecture6-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/ai/2023/x/lectures/6/lecture6-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/QAZc9xsQNjQ?screen=ieuSvyhRv6o
- `lecture_video` `?/youtube/?/?`: https://youtu.be/QAZc9xsQNjQ

</details>

Discovery-Warnungen:

- local_embed_ignored: Browser-local iframe ignored; explicit media links retained

## cs50_web

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:d59d15b54496440b6418042391d2052a67dfb2621253eff24a12094e580b8f27`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:fee9db3adf7d090acb8096998d6d1b6c37e960ad43c9bc6b2672604747a481f7`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lecture0.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lang/en/lecture0.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lang/en/lecture0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lecture0-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lecture0-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lecture0-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/0/lecture0-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/zFZrkCIc2Oc?screen=HbCJtscq-U8
- `lecture_video` `?/youtube/?/?`: https://youtu.be/zFZrkCIc2Oc

</details>

### Abschnitt 1

Vorlesung: `resource:0f0ecf9071410cff4f4f4c3cf129ebf010b9ddc873faff843243e04737ad9228`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a79b9b606accbcae787f19af8204d1771b96e63a5bd060541fb9518cf38c7b6c`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lang/en/lecture1.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lecture1.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lang/en/lecture1.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lecture1-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lecture1-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lecture1-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/1/lecture1-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/NcoBAfJ6l2Q?screen=SU-QJbAZptI
- `lecture_video` `?/youtube/?/?`: https://youtu.be/NcoBAfJ6l2Q

</details>

### Abschnitt 2

Vorlesung: `resource:a9e7d10649756514a70cfe33db0e4b79a4076e6689d37ad79db1afd1c8dc325d`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:b212c80ea27009fca7181939c7c4e638046b901dacd38c467cbb462b1cfcb53d`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lecture2.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lang/en/lecture2.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lang/en/lecture2.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lecture2-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lecture2-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lecture2-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/2/lecture2-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/EOLPQdVj5Ac?screen=-d-WPlksFpc
- `lecture_video` `?/youtube/?/?`: https://youtu.be/EOLPQdVj5Ac

</details>

### Abschnitt 3

Vorlesung: `resource:dd88c4073786500e7f5487fb75f43dfab7d117d298318673c448c3bbf5048822`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:d594bc08a83c5ce9c493165d05efc30a412b799a83b6a96088fd94f3d5fc82e8`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lang/en/lecture3.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lecture3.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lang/en/lecture3.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lecture3-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lecture3-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lecture3-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/3/lecture3-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/w8q0C-C1js4?screen=gytX_rSwZRQ
- `lecture_video` `?/youtube/?/?`: https://youtu.be/w8q0C-C1js4

</details>

### Abschnitt 4

Vorlesung: `resource:3985888775308b75bad18ada582412210ca01572519bc16dbdfcdf98ccac9456`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:ee0e666357f655b088210511c67047e21dd2c5a616d98d00c1019436f6f30f33`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lang/en/lecture4.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lecture4.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lang/en/lecture4.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lecture4-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lecture4-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lecture4-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/4/lecture4-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/YzP164YANAU?screen=VuB5TkTL3tM
- `lecture_video` `?/youtube/?/?`: https://youtu.be/YzP164YANAU

</details>

### Abschnitt 5

Vorlesung: `resource:8d327e41bf99628f6853818cb9ba2ce9313d2859fa7624e6277937c61540c0b4`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:bdc9185106a90ec03f59ae1734fef7a185867f09416b7d6ccd773550fa38a025`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/5/lang/en/lecture5.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lecture5.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lang/en/lecture5.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lang/en/lecture5.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lecture5-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lecture5-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lecture5-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/5/lecture5-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/x5trGVMKTdY?screen=9eLagIEsBcc
- `lecture_video` `?/youtube/?/?`: https://youtu.be/x5trGVMKTdY

</details>

### Abschnitt 6

Vorlesung: `resource:0338927012dcd8513ab5a532df0b05a7eecbdd059ec8f2e936eb1279116de7f7`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:6226f9ac3ea5e74cd42c7ee21fe87a6218b563ffe0daf8abe44705a79c0aca74`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/6/lang/en/lecture6.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lang/en/lecture6.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lecture6.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lang/en/lecture6.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lecture6-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lecture6-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lecture6-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/6/lecture6-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/jrBhi8wbzPw?screen=cDbkNgg0K3U
- `lecture_video` `?/youtube/?/?`: https://youtu.be/jrBhi8wbzPw

</details>

### Abschnitt 7

Vorlesung: `resource:90976cbf91ba3cf36e6b5e1de898a499168989776a5af2277dc375bfa88807c1`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a2a586ea90f6d287e737aecbe8c3fe2e87f62c99b5c75efa4db53db8796a37c2`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/7/lang/en/lecture7.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lang/en/lecture7.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lang/en/lecture7.srt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lecture7.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lecture7-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lecture7-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lecture7-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/7/lecture7-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/WbRDkJ4lPdY?screen=NajlH6g6pW8
- `lecture_video` `?/youtube/?/?`: https://youtu.be/WbRDkJ4lPdY

</details>

### Abschnitt 8

Vorlesung: `resource:4e1225a5e9c5b5e3227b9a30f55d588f06fd86941b6e9a3611cc358eec9f2c77`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:584421c361b21b527630a972fe156c80e297e697a5441d099f7f3f1051811abc`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/web/2020/spring/lectures/8/lang/en/lecture8.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lecture8.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lang/en/lecture8.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lang/en/lecture8.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lecture8-1080p.mp4.download
- `lecture_video` `?/mp4/360p/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lecture8-360p.mp4.download
- `lecture_video` `?/mp4/4k/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lecture8-4k.mp4.download
- `lecture_video` `?/mp4/720p/?`: https://cdn.cs50.net/web/2020/spring/lectures/8/lecture8-720p.mp4.download
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/6PWTxRGh_dk?screen=QUdk3TLZ148
- `lecture_video` `?/youtube/?/?`: https://youtu.be/6PWTxRGh_dk

</details>

Discovery-Warnungen:


## cs50_cybersecurity

Policy: `{"text_strategy":"timed_knowledge","preferred_language":"en","preferred_video_resolution":"720p","prefer_sdr":true,"require_video":false,"allow_unknown_language":false,"allow_transcription":false}`

### Abschnitt 0

Vorlesung: `resource:bc8e7fad8c1067b3aebd2c8a925d003a72e8bfaa25296628128a0caeb07f8d5d`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:e685dc192180e0089426d7fac7bf7568f9bf1c3005937f911e83399b022e91d6`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lang/en/lecture0.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `transcript` `en/txt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lang/en/lecture0.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lang/en/lecture0.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/0/lecture0-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/fJYdAN4Vh5c?screen=McCLi_ltC2o
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/kUovJpWqEMk?screen=OMn51NJ5s1g
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=fJYdAN4Vh5c

</details>

### Abschnitt 1

Vorlesung: `resource:705db08ac5aab168e2a14748fb1ef45838e9a514c5a5b168b2321eceee3cd5ef`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:a50f28525c588f533ebea62552436e47668573ccc630d3d63d785ba43a456d1a`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lang/en/lecture1.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lang/en/lecture1.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lang/en/lecture1.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/1/lecture1-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/X3DVaMnl5n8?screen=wX596_AIFf8
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=X3DVaMnl5n8

</details>

### Abschnitt 2

Vorlesung: `resource:448db3d4bafff62fd5aba7827ed9020b3f5bbf4d10aeb5386053128a893d0b2b`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:8fee7ad0a514f7f77e770d269b76b3ab63a3a3143ae8e76f5ff6b5be5f91cbac`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lang/en/lecture2.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2.mp3
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lang/en/lecture2.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lang/en/lecture2.txt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/2/lecture2-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/9phdZjF8qOk?screen=fJ9GD9jOhdQ
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=9phdZjF8qOk

</details>

### Abschnitt 3

Vorlesung: `resource:842fd9b051645712ede5f16e4be6ccecbe89c2d5e44a4544451cbf645bd4c9d1`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:e3767535339f6173fe33162d81a1f730f82b87c6841cd6f9f15978ec22a06197`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lang/en/lecture3.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `audio` `?/mp3/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3.mp3
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lang/en/lecture3.txt
- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lang/en/lecture3.srt

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/3/lecture3-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/5rsKrTh3fAo?screen=HFXNKld32Cs
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=5rsKrTh3fAo

</details>

### Abschnitt 4

Vorlesung: `resource:712258fa388683dce17c3f9e12fd3ae58ed25a8c1261e997da9bbc8af096d446`

**text**: Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.

Resource-ID: `resource:2e845355b12e84e05f865b51d7851f861d5d363be92ff28bdc90fd064a34d1f4`; Rolle: `subtitles`.
URL: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lang/en/lecture4.srt
ResourceAction-Vorschlag: download, parse_subtitle

- integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.

<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `subtitles` `en/srt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lang/en/lecture4.srt
- `transcript` `en/txt/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lang/en/lecture4.txt
- `audio` `?/mp3/?/?`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4.mp3

</details>

**video**: timed_knowledge wählt keine Videos oder Transkription.


<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>

- `lecture_video` `?/mp4/1080p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-1080p-hdr.mp4
- `lecture_video` `?/mp4/1080p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-1080p.mp4
- `lecture_video` `?/mp4/360p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-360p-hdr.mp4
- `lecture_video` `?/mp4/360p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-360p.mp4
- `lecture_video` `?/mp4/4k/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-4k-hdr.mp4
- `lecture_video` `?/mp4/4k/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-4k.mp4
- `lecture_video` `?/mp4/720p/hdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-720p-hdr.mp4
- `lecture_video` `?/mp4/720p/sdr`: https://cdn.cs50.net/cybersecurity/2023/x/lectures/4/lecture4-720p.mp4
- `lecture_video` `?/cs50_player/?/?`: https://video.cs50.io/6IeqJtudKnk?screen=Zw5RQJ1B-4s
- `lecture_video` `?/youtube/?/?`: https://www.youtube.com/watch?v=6IeqJtudKnk

</details>

Discovery-Warnungen:

- multiple_lecture_media_ids: Lecture player/embed IDs differ for language unknown: fJYdAN4Vh5c, kUovJpWqEMk
