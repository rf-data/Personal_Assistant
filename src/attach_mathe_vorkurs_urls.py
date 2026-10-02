from __future__ import annotations

import json
import re
from pathlib import Path


def load_url_mapping(
    mapping_path: str | Path,
) -> dict[str, dict]:
    mapping_path = Path(mapping_path)

    with mapping_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_playlist_index_from_filename(
    path: str | Path,
) -> str | None:
    """
    Examples:
        001_001_Grundrechenarten_Teilen_durch_Null.json -> "001"
        003_003_004_erste_zweite_...json               -> "003"
    """
    path = Path(path)

    match = re.match(r"^(\d{3})(?:_|$)", path.stem)

    return match.group(1) if match else None


def attach_urls_to_transcripts(
    transcript_folder: str | Path,
    mapping_path: str | Path,
    *,
    overwrite: bool = False,
    write_youtube_id: bool = True,
    dry_run: bool = True,
) -> dict[str, int]:
    """
    Adds provenance.source_url to transcript JSON files.

    Matching strategy:
        first three digits of transcript filename == playlist index
        e.g. 003_...json -> mapping["003"]

    Existing non-empty values are preserved unless overwrite=True.
    Optionally also fills provenance.youtube_id.

    Returns simple processing statistics.
    """
    transcript_folder = Path(transcript_folder)
    mapping = load_url_mapping(mapping_path)

    stats = {
        "found": 0,
        "matched": 0,
        "updated": 0,
        "skipped_existing": 0,
        "unmatched": 0,
    }

    for path in sorted(transcript_folder.glob("*.json")):
        stats["found"] += 1

        playlist_index = get_playlist_index_from_filename(path)

        if playlist_index is None:
            print(f"[NO INDEX] {path.name}")
            stats["unmatched"] += 1
            continue

        entry = mapping.get(playlist_index)

        if entry is None:
            print(f"[NO MAPPING] {path.name} (playlist_index={playlist_index})")
            stats["unmatched"] += 1
            continue

        stats["matched"] += 1

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if hasattr(data, "transcript_url"):
            data["transcript_url"] = entry["url"]

        provenance = data.get("provenance")

        if not isinstance(provenance, dict):
            provenance = {}
            data["provenance"] = provenance

        old_url = provenance.get("source_url")
        old_youtube_id = provenance.get("youtube_id")

        changed = False

        if overwrite or not old_url:
            provenance["source_url"] = entry["url"]
            changed = True
        elif old_url != entry["url"]:
            print(
                f"[URL CONFLICT] {path.name}\n"
                f"  existing: {old_url}\n"
                f"  mapping:  {entry['url']}"
            )

        if write_youtube_id:
            if overwrite or not old_youtube_id:
                provenance["youtube_id"] = entry["video_id"]
                changed = True
            elif old_youtube_id != entry["video_id"]:
                print(
                    f"[ID CONFLICT] {path.name}\n"
                    f"  existing: {old_youtube_id}\n"
                    f"  mapping:  {entry['video_id']}"
                )

        if not changed:
            stats["skipped_existing"] += 1
            continue

        print(f"[MATCH] {path.name}\n  {entry['title']}\n  {entry['url']}")

        if not dry_run:
            with path.open("w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )

        stats["updated"] += 1

    return stats


if __name__ == "__main__":
    from src.core.config import folder_env_vars

    stats = attach_urls_to_transcripts(
        transcript_folder=(
            folder_env_vars.data_lectures / "loviscach/mathe_vorkurs/knowledge"
        ),
        mapping_path=Path(
            "/home/robfra/0_Portfolio_Projekte/gmp_compliance/src/mathe_vorkurs_2013_urls.json"
        ),
        dry_run=False,
    )

    print(stats)
