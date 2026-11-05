"""Bounded static source validation for reviewed local materials; no transport."""

from src.tools_materials.inventory import CODE, official

SOURCE_FORMATS = CODE | {"zip"}


def validate_source(raw, fmt):
    if fmt not in SOURCE_FORMATS:
        raise ValueError("Unsupported explicit source-code format")
    if not raw or len(raw) > 1048576:
        raise ValueError("Source file exceeds byte limit or is empty")
    if fmt == "zip":
        # Shared path, symlink, count, size, ratio, deadline and CRC checks.
        # All members remain in bounded memory; no filesystem extraction.
        import zipfile

        from src.tools_materials.code_zip import inspect_zip

        try:
            return inspect_zip(raw)
        except (zipfile.BadZipFile, EOFError) as error:
            raise ValueError("Corrupt ZIP archive or member CRC") from error
    text = raw.decode("utf-8-sig", errors="strict")
    if (
        not text.strip()
        or "\x00" in text
        or text.lstrip()
        .lower()
        .startswith(("<!doctype html", "<html", "error:", "404 ", "access denied"))
    ):
        raise ValueError("Empty, binary or error response masquerading as source")
    return None
