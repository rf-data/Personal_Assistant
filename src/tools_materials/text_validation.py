"""Content checks around the existing offline transcript importer; no worker."""

from bs4 import BeautifulSoup

from src.tools_lecture.execute_cs50 import validate_order
from src.tools_transcribe.import_transcript import import_transcript


def validate_html_page(path):
    main = BeautifulSoup(path.read_bytes(), "html.parser").find("main")
    if main is None or main.find("h1") is None or not main.h1.get_text(strip=True):
        raise ValueError("HTML material lacks main content/title")
    title = main.h1.get_text(" ", strip=True).lower()
    if title.startswith(("404", "403", "error", "access denied", "not found")):
        raise ValueError("HTML error page is not course material")


def validate_text_source(path, binding):
    text = path.read_text(encoding="utf-8-sig")
    lowered = text.lstrip().lower()
    if lowered.startswith(
        ("error:", "404 ", "403 ", "access denied", "not found", "forbidden")
    ):
        raise ValueError("Error response masquerading as transcript")
    if any(marker in lowered for marker in ("<!doctype html", "<html", "<body")):
        if binding.format != "html":
            raise ValueError("HTML response masquerading as transcript")
    if binding.format == "html":
        soup = BeautifulSoup(text, "html.parser")
        main = soup.select_one("main")
        if main is None or len(main.get_text(" ", strip=True)) < 40:
            raise ValueError("Empty or unusable HTML transcript")
        return
    document = import_transcript(
        path,
        language=binding.language or "en",
        original_url=binding.original_url,
        format=binding.format,
    )
    if len(document.text.strip()) < 20:
        raise ValueError("Transcript text too short for content validation")
    if binding.format in {"srt", "vtt"}:
        validate_order(document)
