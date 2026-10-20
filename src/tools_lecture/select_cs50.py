"""Pure offline resource selection. Never creates or executes ResourceTasks."""

import re
from urllib.parse import urlsplit

from src.model_discovery.cs50 import CourseDiscovery, ResourceCandidate, ResourceRole
from src.model_discovery.cs50_selection import (
    CoursePreview,
    LecturePreview,
    SelectionDecision,
    SelectionOption,
    SelectionPolicy,
)
from src.tools_lecture.cs50_manifest import COURSE_PATHS


def _options(resources: tuple[ResourceCandidate, ...]) -> tuple[SelectionOption, ...]:
    result = []
    for resource in resources:
        if resource.variants:
            for variant in resource.variants:
                result.append(
                    SelectionOption(
                        resource_id=resource.resource_id,
                        role=resource.role,
                        original_url=variant.original_url,
                        variant_id=variant.variant_id,
                        language=variant.language or resource.language,
                        format=variant.format,
                        resolution=variant.resolution,
                        dynamic_range=variant.dynamic_range,
                    )
                )
        else:
            result.append(
                SelectionOption(
                    resource_id=resource.resource_id,
                    role=resource.role,
                    original_url=resource.original_url,
                    language=resource.language,
                    format=resource.format,
                )
            )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.resource_id,
                str(item.original_url),
                item.variant_id or "",
            ),
        )
    )


def _language_rank(option: SelectionOption, policy: SelectionPolicy) -> int | None:
    if option.language == policy.preferred_language:
        return 0
    if option.language is None and policy.allow_unknown_language:
        return 1
    return None


def _official_srt(resource: ResourceCandidate, lecture: ResourceCandidate) -> bool:
    url = urlsplit(str(resource.original_url))
    # Official CDN source plus evidence on an official course page. No HTTP check
    # or claim about subtitle contents; both must be validated during import.
    prefix = COURSE_PATHS[resource.course_id]
    expected_pages = {
        f"https://cs50.harvard.edu/{prefix}/weeks/{key}/"
        for key in lecture.section_keys
    }
    cdn_prefix = "" if resource.course_id == "cs50x" else f"{prefix}/"
    match = re.fullmatch(
        rf"/{cdn_prefix}\d{{4}}/[^/]+/lectures/([^/]+)/lang/([^/]+)/[^/]+\.srt",
        url.path,
    )
    return (
        resource.role == ResourceRole.SUBTITLES
        and resource.format == "srt"
        and url.scheme == "https"
        and url.netloc == "cdn.cs50.net"
        and match is not None
        and match[1] in resource.section_keys
        and match[2] == resource.language
        and bool(resource.section_keys)
        and set(resource.section_keys) <= set(lecture.section_keys)
        and any(str(p.original_url) in expected_pages for p in resource.provenance)
    )


def _choose_timed(
    resources: list[ResourceCandidate],
    policy: SelectionPolicy,
    ambiguous: bool,
    lecture: ResourceCandidate,
) -> SelectionDecision:
    alternatives = _options(tuple(resources))
    candidates = [
        r
        for r in resources
        if _official_srt(r, lecture)
        and r.language == policy.preferred_language
        and not r.variants
    ]
    if ambiguous or len(candidates) > 1:
        return SelectionDecision(
            purpose="text",
            alternatives=alternatives,
            reason="SRT-Angebot oder Vorlesungszuordnung ist mehrdeutig; keine Auswahl.",
            warnings=(
                "ambiguous_selection: Eindeutige offizielle SRT-Quelle erforderlich.",
            ),
        )
    if not candidates:
        return SelectionDecision(
            purpose="text",
            alternatives=alternatives,
            reason=f"Kein eindeutig zugeordnetes offizielles SRT in Sprache {policy.preferred_language}; "
            "kein TXT-, VTT-, Audio- oder Video-Fallback.",
        )
    return SelectionDecision(
        purpose="text",
        selected=_options((candidates[0],))[0],
        alternatives=alternatives,
        actions=("download", "parse_subtitle"),
        reason="Offizielles SRT in exakter bevorzugter Sprache; zeitbasierter Knowledge-Primärinput.",
        warnings=(
            "integration_pending: Offizieller SRT-Importer vorhanden; Lecture-Runner-Anbindung folgt separat.",
        ),
    )


def select_optional_txt(
    candidates: tuple[ResourceCandidate, ...],
    policy: SelectionPolicy | None = None,
) -> SelectionDecision:
    """Select explicitly scoped lecture candidates as a separate TXT supplement.

    The caller must resolve lecture ownership first. This decision never becomes
    a primary input and is never added automatically by preview_course.
    """
    policy = policy or SelectionPolicy()
    options = _options(
        tuple(
            r
            for r in candidates
            if r.role == ResourceRole.TRANSCRIPT
            and r.format == "txt"
            and r.language == policy.preferred_language
        )
    )
    decision = _choose(
        options,
        policy.model_copy(
            update={"allow_unknown_language": False, "allow_transcription": False}
        ),
        "text",
    )
    return decision.model_copy(
        update={
            "reason": "Optionale TXT-Ergänzung; kein zeitbasierter Knowledge-Primärinput. "
            + decision.reason
        }
    )


def _choose(options, policy, purpose):
    ranked = []
    for option in options:
        language_rank = _language_rank(option, policy)
        if language_rank is None:
            continue
        if purpose == "video":
            if option.format not in {"mp4", "webm"}:
                continue
            if option.resolution != policy.preferred_video_resolution:
                continue
            ranges = {"sdr": 0, "hdr": 1, None: 2}
            if not policy.prefer_sdr:
                ranges = {"hdr": 0, "sdr": 1, None: 2}
            rank = (language_rank, ranges.get(option.dynamic_range, 2))
        else:
            supported = {
                (ResourceRole.TRANSCRIPT, "txt"): 0,
                (ResourceRole.SUBTITLES, "vtt"): 1,
                (ResourceRole.SUBTITLES, "srt"): 2,
            }
            kind_rank = supported.get((option.role, option.format))
            if kind_rank is None:
                if not policy.allow_transcription:
                    continue
                if option.role == ResourceRole.AUDIO and option.format in {
                    "mp3",
                    "m4a",
                }:
                    kind_rank = 3
                else:
                    continue
            rank = (language_rank, kind_rank)
        ranked.append((rank, option))
    warnings = []
    if any(option.language is None for option in options):
        warnings.append("missing_language: Sprachangaben fehlen bei einigen Angeboten.")
    if purpose == "video" and any(option.resolution is None for option in options):
        warnings.append(
            "missing_resolution: Player/YouTube-Angebote haben keine feste Auflösung."
        )
    if not ranked:
        return SelectionDecision(
            purpose=purpose,
            alternatives=options,
            reason=(
                "Kein Angebot erfüllt Sprache, Format und exakte Auflösung; kein Qualitätsfallback."
                if purpose == "video"
                else "Kein passender TXT-/Untertitel-Link oder ausdrücklich erlaubter Audiotranskriptionspfad."
            ),
            warnings=tuple(warnings),
        )
    best_rank = min(rank for rank, _ in ranked)
    best = [option for rank, option in ranked if rank == best_rank]
    # Equivalent URLs represent one download; distinct equivalent offers are ambiguous.
    if len({str(option.original_url) for option in best}) > 1:
        return SelectionDecision(
            purpose=purpose,
            alternatives=options,
            reason="Mehrere gleichwertige URLs: keine willkürliche Auswahl.",
            warnings=(
                *warnings,
                "ambiguous_selection: Auswahl benötigt zusätzliche Metadaten.",
            ),
        )
    selected = best[0]
    actions = ("download",)
    if selected.language is None:
        warnings.append(
            "unknown_language_selected: Unbekannte Sprache ausdrücklich erlaubt."
        )
    if purpose == "video" and selected.dynamic_range is None:
        warnings.append("missing_dynamic_range: HDR/SDR unbekannt; keine SDR-Annahme.")
    if selected.role == ResourceRole.SUBTITLES:
        actions = ("download", "parse_subtitle")
        if selected.format == "srt":
            warnings.append(
                "integration_gap: Bestehender Untertitelparser unterstützt nur VTT, kein SRT."
            )
    elif selected.role == ResourceRole.TRANSCRIPT:
        warnings.append(
            "integration_gap: TXT muss vor Lecture-Verarbeitung in TranscriptDocument normalisiert werden."
        )
    elif selected.role == ResourceRole.AUDIO:
        actions = ("download", "transcribe")
    return SelectionDecision(
        purpose=purpose,
        selected=selected,
        alternatives=options,
        actions=actions,
        reason=(
            "Exakte Sprache/Auflösung; bevorzugter Dynamikumfang vor unbekanntem Umfang."
            if purpose == "video"
            else "Bevorzugte Sprache; TXT vor VTT vor SRT vor ausdrücklich erlaubter Audiotranskription."
        ),
        warnings=tuple(warnings),
    )


def preview_course(
    course: CourseDiscovery, policy: SelectionPolicy | None = None
) -> CoursePreview:
    """Select once per logical lecture; retain the complete immutable discovery graph."""
    policy = policy or SelectionPolicy()
    lectures = tuple(
        resource
        for resource in course.resources
        if resource.role == ResourceRole.LECTURE_VIDEO
    )
    section_order = {section.key: section.order for section in course.sections}
    previews = []
    for lecture in sorted(
        lectures,
        key=lambda item: (
            min((section_order[key] for key in item.section_keys), default=10**9),
            item.resource_id,
        ),
    ):
        related = []
        ambiguous = False
        for resource in course.resources:
            if resource.role not in {
                ResourceRole.TRANSCRIPT,
                ResourceRole.SUBTITLES,
                ResourceRole.AUDIO,
            }:
                continue
            if resource.parent_resource_id == lecture.resource_id:
                related.append(resource)
            elif resource.parent_resource_id is None and set(
                resource.section_keys
            ) & set(lecture.section_keys):
                owners = [
                    item
                    for item in lectures
                    if set(resource.section_keys) & set(item.section_keys)
                ]
                if len(owners) == 1:
                    related.append(resource)
                else:
                    if policy.text_strategy != "timed_knowledge" or (
                        resource.role == ResourceRole.SUBTITLES
                        and resource.format == "srt"
                        and resource.language == policy.preferred_language
                    ):
                        ambiguous = True
        timed = policy.text_strategy == "timed_knowledge"
        text = (
            _choose_timed(related, policy, ambiguous, lecture)
            if timed
            else _choose(_options(tuple(related)), policy, "text")
        )
        if ambiguous:
            text = text.model_copy(
                update={
                    "warnings": (
                        *text.warnings,
                        "ambiguous_association: Begleitmaterial ohne eindeutige Vorlesungszuordnung ausgeschlossen.",
                    )
                }
            )
        videos = _options((lecture,))
        video = (
            _choose(videos, policy, "video")
            if policy.require_video and not timed
            else SelectionDecision(
                purpose="video",
                alternatives=videos,
                reason=(
                    "timed_knowledge wählt keine Videos oder Transkription."
                    if timed
                    else "Video ist in dieser Policy nicht angefordert."
                ),
            )
        )
        if text.selected is None and policy.allow_transcription and not timed:
            fallback = video if video.selected else _choose(videos, policy, "video")
            if fallback.selected:
                text = SelectionDecision(
                    purpose="text",
                    selected=fallback.selected,
                    alternatives=(*text.alternatives, *videos),
                    actions=(
                        ("transcribe",)
                        if video.selected
                        else ("download", "transcribe")
                    ),
                    reason="Keine passende Text-/Audioquelle; ausdrücklich erlaubte Transkription der ausgewählten Videoqualität.",
                    warnings=(*text.warnings, *fallback.warnings),
                )
        previews.append(
            LecturePreview(
                resource_id=lecture.resource_id,
                section_keys=tuple(
                    sorted(
                        lecture.section_keys, key=lambda key: (section_order[key], key)
                    )
                ),
                decisions=(text, video),
            )
        )
    return CoursePreview(discovery=course, policy=policy, lectures=tuple(previews))


def render_preview(previews: tuple[CoursePreview, ...]) -> str:
    """Return Markdown only; the caller decides whether to persist it."""
    lines = [
        "# CS50 Processing Preview",
        "",
        "Offline-Dry-Run; keine ResourceTasks werden erzeugt oder ausgeführt.",
        "",
    ]
    for preview in previews:
        lines.extend(
            [
                f"## {preview.discovery.course_id}",
                "",
                f"Policy: `{preview.policy.model_dump_json()}`",
                "",
            ]
        )
        for lecture in preview.lectures:
            lines.extend(
                [
                    f"### Abschnitt {', '.join(lecture.section_keys)}",
                    "",
                    f"Vorlesung: `{lecture.resource_id}`",
                    "",
                ]
            )
            for decision in lecture.decisions:
                selected = decision.selected
                lines.extend([f"**{decision.purpose}**: {decision.reason}", ""])
                if selected:
                    lines.extend(
                        [
                            f"Resource-ID: `{selected.resource_id}`; Rolle: `{selected.role.value}`.",
                            f"URL: {selected.original_url}",
                            f"ResourceAction-Vorschlag: {', '.join(decision.actions)}",
                            "",
                        ]
                    )
                for warning in decision.warnings:
                    lines.append(f"- {warning}")
                lines.extend(
                    [
                        "",
                        "<details><summary>Verfügbare Angebote (einschließlich Auswahl)</summary>",
                        "",
                    ]
                )
                for option in decision.alternatives:
                    metadata = "/".join(
                        value or "?"
                        for value in (
                            option.language,
                            option.format,
                            option.resolution,
                            option.dynamic_range,
                        )
                    )
                    lines.append(
                        f"- `{option.role.value}` `{metadata}`: {option.original_url}"
                    )
                lines.extend(["", "</details>", ""])
        lines.extend(["Discovery-Warnungen:", ""])
        lines.extend(
            f"- {warning.code}: {warning.message}"
            for warning in preview.discovery.warnings
        )
        lines.append("")
    return "\n".join(lines)
