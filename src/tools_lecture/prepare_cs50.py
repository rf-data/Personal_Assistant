"""Offline CS50 index/week discovery. Linked detail pages are never opened."""

import re
from collections.abc import Callable, Iterable
from pathlib import Path
from urllib.parse import parse_qs, urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl, ValidationError

from src.model_discovery.cs50 import (
    CourseDiscovery,
    CourseId,
    DiscoveryStatus,
    DiscoveryWarning,
    MediaVariant,
    Provenance,
    ResourceCandidate,
    ResourceRole,
    SectionDiscovery,
)
from src.tools_lecture.cs50_manifest import (
    COURSE_PATHS,
    FixturePage,
    load_fixture_manifest,
)

LANGUAGES = {"english": "en", "portuguese": "pt", "spanish": "es"}
LIST_ROLES = {
    "notes": ResourceRole.NOTES,
    "slides": ResourceRole.SLIDES,
    "source code": ResourceRole.SOURCE_CODE,
    "audio": ResourceRole.AUDIO,
    "video": ResourceRole.LECTURE_VIDEO,
    "subtitles": ResourceRole.SUBTITLES,
    "transcript": ResourceRole.TRANSCRIPT,
    "transcripts": ResourceRole.TRANSCRIPT,
    "shorts": ResourceRole.SHORT,
    "section": ResourceRole.SECTION,
    "demos": ResourceRole.DEMO,
}


class CS50ParseError(ValueError):
    """The supplied page cannot be safely assigned or merged."""


def _unique[T](items: Iterable[T]) -> tuple[T, ...]:
    return tuple(dict.fromkeys(items))


def _label(node: Tag, *, skip_links: bool = False) -> str:
    """Own inline text, excluding child lists, icons and executable markup."""

    def text(part) -> str:
        if not isinstance(part, Tag):
            return str(part)
        if (
            (skip_links and part.name == "a")
            or part.name in {"ul", "ol", "i", "script", "style"}
            or "fa-li" in part.get("class", [])
        ):
            return ""
        return " ".join(text(child) for child in part.children)

    return " ".join(text(node).split())


def _locator(node: Tag) -> str:
    parts = []
    while node.name != "[document]":
        siblings = node.find_previous_siblings(node.name)
        parts.append(f"{node.name}:nth-of-type({len(siblings) + 1})")
        if not isinstance(node.parent, Tag):
            break
        node = node.parent
    return " > ".join(reversed(parts))


def _evidence(
    node: Tag, url: str, fixture: str | None, context: tuple[str, ...] = ()
) -> Provenance:
    return Provenance(
        original_url=url,
        fixture_file=fixture,
        locator=_locator(node),
        context_path=context,
    )


def _page(
    html: str, source_url: str, course_id: CourseId, index: bool
) -> tuple[BeautifulSoup, str | None]:
    prefix = COURSE_PATHS.get(course_id)
    url = urlsplit(source_url)
    pattern = rf"/{prefix}/" if index else rf"/{prefix}/weeks/([^/]+)/"
    match = re.fullmatch(pattern, url.path)
    if (
        not prefix
        or url.scheme != "https"
        or url.netloc != "cs50.harvard.edu"
        or url.query
        or url.fragment
        or not match
    ):
        raise CS50ParseError(
            f"{course_id}: invalid {'index' if index else 'week'} URL {source_url}"
        )
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("main") is None:
        raise CS50ParseError(f"{source_url}: missing main content")
    return soup, None if index else match.group(1)


def _link_url(raw: str, base: str) -> str | None:
    url = urljoin(base, raw.strip())
    if urldefrag(url)[0] == urldefrag(base)[0]:
        return None
    return str(HttpUrl(url))


def parse_course_index(
    html: str,
    source_url: str,
    *,
    course_id: CourseId,
    fixture_file: str | None = None,
) -> CourseDiscovery:
    """Read week links from navigation, retaining first-occurrence order/titles."""
    soup, _ = _page(html, source_url, course_id, index=True)
    sections: dict[str, SectionDiscovery] = {}
    pattern = rf"/{COURSE_PATHS[course_id]}/weeks/([^/]+)/"
    for link in soup.select("nav a[href]"):
        url = urlsplit(urljoin(source_url, str(link["href"])))
        match = re.fullmatch(pattern, url.path)
        if (
            url.scheme != "https"
            or url.netloc != "cs50.harvard.edu"
            or url.query
            or url.fragment
            or not match
        ):
            continue
        key = match.group(1)
        label = _label(link.find_parent("li") or link) or key
        evidence = _evidence(link, source_url, fixture_file, (label,))
        original_url = url.geturl()
        if key in sections:
            previous = sections[key]
            sections[key] = SectionDiscovery.model_validate(
                {
                    **previous.model_dump(),
                    "provenance": _unique((*previous.provenance, evidence)),
                }
            )
        else:
            sections[key] = SectionDiscovery(
                course_id=course_id,
                key=key,
                original_url=original_url,
                title=label or key,
                order=len(sections),
                provenance=(evidence,),
            )
    if not sections:
        raise CS50ParseError(f"{source_url}: navigation has no course week links")
    return CourseDiscovery(
        course_id=course_id,
        original_url=source_url,
        title=soup.title.get_text(" ", strip=True) if soup.title else None,
        status=DiscoveryStatus.PARSED,
        sections=tuple(sections.values()),
        provenance=(_evidence(soup.find("main"), source_url, fixture_file),),
    )


def _role(context: tuple[str, ...]) -> ResourceRole:
    # Nearest semantic branch wins (e.g. Lecture > Demos > a YouTube link).
    for label in reversed(context):
        label = label.casefold()
        if label in LIST_ROLES:
            return LIST_ROLES[label]
        for prefix, role in (
            ("problem set", ResourceRole.PROBLEM_SET),
            ("quiz", ResourceRole.QUIZ),
            ("project", ResourceRole.PROJECT),
        ):
            if label == prefix or label.startswith(prefix + " "):
                return role
    return ResourceRole.OTHER


def _language(context: tuple[str, ...], url: str) -> str | None:
    for label in reversed(context):
        if label.casefold() in LANGUAGES:
            return LANGUAGES[label.casefold()]
    match = re.search(r"/lang/([^/]+)/", urlsplit(url).path)
    if match:
        return match.group(1)
    match = re.search(r"/lectures/[^/]+/(pt|es)/", urlsplit(url).path)
    return match.group(1) if match else None


def _format(url: str) -> str | None:
    path = urlsplit(url).path.removesuffix(".download")
    return Path(path).suffix.lstrip(".").lower() or None


def _media_id(url: str) -> str | None:
    parsed = urlsplit(url)
    parts = parsed.path.strip("/").split("/")
    candidate = None
    if parsed.hostname in {"youtu.be", "www.youtu.be", "video.cs50.io"}:
        candidate = parts[0]
    elif parsed.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]
        elif len(parts) == 2 and parts[0] in {"embed", "shorts", "live"}:
            candidate = parts[1]
    return (
        candidate
        if candidate and re.fullmatch(r"[\w-]{11}", candidate, flags=re.ASCII)
        else None
    )


def _variant(
    url: str, context: tuple[str, ...], evidence: Provenance
) -> MediaVariant | None:
    file_type = _format(url)
    media_id = _media_id(url)
    media_type = (
        "audio"
        if file_type in {"mp3", "m4a", "wav", "ogg"}
        else "video"
        if file_type in {"mp4", "webm"} or media_id
        else None
    )
    if not media_type:
        return None
    labels = [label.casefold() for label in context]
    resolution = next(
        (label for label in reversed(labels) if re.fullmatch(r"\d+p|4k|8k", label)),
        None,
    )
    if resolution is None:
        match = re.search(
            r"-(\d+p|4k|8k)(?:-|\.)", urlsplit(url).path, flags=re.IGNORECASE
        )
        resolution = match.group(1).lower() if match else None
    dynamic_range = next(
        (label for label in reversed(labels) if label in {"hdr", "sdr"}), None
    )
    if dynamic_range is None and "-hdr." in urlsplit(url).path:
        dynamic_range = "hdr"
    host = urlsplit(url).hostname
    if media_id:
        file_type = "cs50_player" if host == "video.cs50.io" else "youtube"
    return MediaVariant(
        original_url=url,
        media_type=media_type,
        language=_language(context, url),
        format=file_type,
        resolution=resolution,
        dynamic_range=dynamic_range,
        media_id=media_id,
        provenance=(evidence,),
    )


def _merge_variants(variants: Iterable[MediaVariant]) -> tuple[MediaVariant, ...]:
    merged: dict[str, MediaVariant] = {}
    for variant in variants:
        previous = merged.get(variant.variant_id)
        if previous is None:
            merged[variant.variant_id] = variant
            continue
        data = previous.model_dump()
        for field in ("language", "format", "resolution", "dynamic_range", "media_id"):
            old, new = getattr(previous, field), getattr(variant, field)
            if old is not None and new is not None and old != new:
                raise CS50ParseError(
                    f"{variant.original_url}: conflicting variant {field}: {old} / {new}"
                )
            data[field] = old or new
        data["provenance"] = _unique((*previous.provenance, *variant.provenance))
        merged[variant.variant_id] = MediaVariant.model_validate(data)
    return tuple(merged.values())


def merge_resource_candidates(
    resources: Iterable[ResourceCandidate],
) -> tuple[ResourceCandidate, ...]:
    """Merge equal model identities, preserving weeks, variants and evidence."""
    merged: dict[str, ResourceCandidate] = {}
    for resource in resources:
        previous = merged.get(resource.resource_id)
        if previous is None:
            merged[resource.resource_id] = resource
            continue
        merged[resource.resource_id] = ResourceCandidate.model_validate(
            {
                **previous.model_dump(),
                "title": previous.title or resource.title,
                "format": previous.format or resource.format,
                "section_keys": _unique(
                    (*previous.section_keys, *resource.section_keys)
                ),
                "provenance": _unique((*previous.provenance, *resource.provenance)),
                "variants": _merge_variants((*previous.variants, *resource.variants)),
                "status": "parsed"
                if "parsed" in {previous.status, resource.status}
                else "referenced",
            }
        )
    return tuple(merged.values())


def parse_week_page(
    html: str,
    source_url: str,
    *,
    course_id: CourseId,
    fixture_file: str | None = None,
) -> CourseDiscovery:
    """Return a course fragment with one parsed week and its linked candidates.

    The main lecture is a week-URL candidate with all Video-branch variants.
    Linked notes/code/assignments remain referenced; their contents are not parsed.
    """
    soup, key = _page(html, source_url, course_id, index=False)
    main = soup.find("main")
    heading = main.find("h1")
    if heading is None:
        raise CS50ParseError(f"{source_url}: missing week heading")
    title = heading.get_text(" ", strip=True)
    if not title:
        raise CS50ParseError(f"{source_url}: empty week heading")
    match = re.match(r"Week\s+(\S+)", title)
    if match and match.group(1) != key:
        raise CS50ParseError(
            f"{source_url}: heading week {match.group(1)} contradicts URL week {key}"
        )
    section = SectionDiscovery(
        course_id=course_id,
        key=key,
        title=title,
        original_url=source_url,
        status=DiscoveryStatus.PARSED,
        provenance=(_evidence(heading, source_url, fixture_file, (title,)),),
    )
    warnings: list[DiscoveryWarning] = []
    resources: list[ResourceCandidate] = []
    primary_variants: list[MediaVariant] = []
    lecture_nodes: list[Tag] = []

    def warn(code: str, message: str, evidence: Provenance) -> None:
        warnings.append(
            DiscoveryWarning(
                course_id=course_id,
                section_key=key,
                code=code,
                message=message,
                provenance=(evidence,),
            )
        )

    def walk(list_node: Tag, context: tuple[str, ...] = ()) -> None:
        for item in list_node.find_all("li", recursive=False):
            label = _label(item, skip_links=True) or _label(item)
            path = context + ((label,) if label else ())
            if not context and label.casefold() == "lecture":
                lecture_nodes.append(item)
            for link in item.find_all("a", href=True):
                if link.find_parent("li") is not item:
                    continue
                evidence = _evidence(link, source_url, fixture_file, path)
                try:
                    url = _link_url(str(link["href"]), source_url)
                except ValidationError:
                    warn(
                        "invalid_link",
                        f"Unsupported resource URL: {link['href']}",
                        evidence,
                    )
                    continue
                if url is None:
                    continue
                role = _role(path)
                variant = _variant(url, path, evidence)
                if (
                    role == ResourceRole.LECTURE_VIDEO
                    and context
                    and context[0].casefold() == "lecture"
                    and variant
                    and variant.media_type == "video"
                ):
                    primary_variants.append(variant)
                    continue
                if role == ResourceRole.LECTURE_VIDEO:
                    warn(
                        "unrecognized_video",
                        f"Cannot identify primary video offer: {url}",
                        evidence,
                    )
                    role = ResourceRole.OTHER
                if role == ResourceRole.OTHER:
                    warn(
                        "unknown_resource_role",
                        f"Unknown list context: {' > '.join(path)}",
                        evidence,
                    )
                resources.append(
                    ResourceCandidate(
                        course_id=course_id,
                        role=role,
                        original_url=url,
                        title=link.get_text(" ", strip=True) or label or url,
                        section_keys=(key,),
                        language=_language(path, url),
                        format=_format(url),
                        variants=(variant,) if variant else (),
                        provenance=(evidence,),
                    )
                )
            for child in item.find_all(["ul", "ol"]):
                if child.find_parent("li") is item:
                    walk(child, path)

    for root in main.find_all(["ul", "ol"]):
        if root.find_parent(["ul", "ol", "details", "nav"]) is None:
            walk(root)
    if len(lecture_nodes) > 1:
        raise CS50ParseError(
            f"{source_url}: multiple Lecture branches; ambiguous primary lecture"
        )
    for iframe in main.select("iframe[data-video]"):
        ancestors = reversed(iframe.find_parents("li"))
        context = tuple(
            label
            for item in ancestors
            if (label := (_label(item, skip_links=True) or _label(item)))
        )
        context = context + ("Embed",) if context else ("Lecture", "Video", "Embed")
        evidence = _evidence(iframe, source_url, fixture_file, context)
        raw = str(iframe.get("data-src") or iframe.get("src") or "")
        if "_files/" in raw or "saved_resource" in raw:
            warn(
                "local_embed_ignored",
                "Browser-local iframe ignored; explicit media links retained",
                evidence,
            )
            continue
        try:
            url = _link_url(raw, source_url)
        except ValidationError:
            url = None
        variant = _variant(url, evidence.context_path, evidence) if url else None
        if variant and variant.media_type == "video":
            role = _role(context)
            if role == ResourceRole.LECTURE_VIDEO:
                primary_variants.append(variant)
            else:
                resources.append(
                    ResourceCandidate(
                        course_id=course_id,
                        role=role,
                        original_url=url,
                        title=str(iframe.get("title") or context[-2]),
                        section_keys=(key,),
                        language=variant.language,
                        variants=(variant,),
                        provenance=(evidence,),
                    )
                )
        else:
            warn(
                "unrecognized_embed", f"Cannot identify lecture embed: {raw}", evidence
            )
    if lecture_nodes or primary_variants:
        resources.insert(
            0,
            ResourceCandidate(
                course_id=course_id,
                role=ResourceRole.LECTURE_VIDEO,
                original_url=source_url,
                title=title,
                section_keys=(key,),
                status=DiscoveryStatus.PARSED,
                variants=_merge_variants(primary_variants),
                provenance=(
                    _evidence(
                        lecture_nodes[0] if lecture_nodes else heading,
                        source_url,
                        fixture_file,
                        ("Lecture",),
                    ),
                ),
            ),
        )
        if not primary_variants:
            warn(
                "missing_lecture_media",
                "Lecture branch has no recognized video offers",
                section.provenance[0],
            )
    else:
        warn(
            "missing_lecture",
            "No Lecture branch or recognized lecture embed",
            section.provenance[0],
        )
    return CourseDiscovery(
        course_id=course_id,
        original_url=source_url,
        status=DiscoveryStatus.PARSED,
        sections=(section,),
        resources=merge_resource_candidates(resources),
        warnings=tuple(warnings),
        provenance=(_evidence(main, source_url, fixture_file),),
    )


def combine_course_pages(
    index: CourseDiscovery, weeks: Iterable[CourseDiscovery]
) -> CourseDiscovery:
    """Keep index order/titles and promote only successfully parsed weeks."""
    sections = {section.key: section for section in index.sections}
    resources = list(index.resources)
    warnings = list(index.warnings)
    provenance = list(index.provenance)
    weeks = tuple(weeks)
    if any(
        week.course_id != index.course_id or len(week.sections) != 1 for week in weeks
    ):
        raise CS50ParseError("Week fragment contradicts index course or section count")
    weeks = sorted(
        weeks,
        key=lambda week: (
            sections[week.sections[0].key].order
            if week.sections[0].key in sections
            else len(sections)
        ),
    )
    for week in weeks:
        parsed = week.sections[0]
        original = sections.get(parsed.key)
        if (
            original is None
            or original.original_url != parsed.original_url
            or parsed.status != DiscoveryStatus.PARSED
        ):
            raise CS50ParseError(
                f"{parsed.original_url}: parsed week not present in course navigation"
            )
        sections[parsed.key] = SectionDiscovery.model_validate(
            {
                **original.model_dump(),
                "status": "parsed",
                "provenance": _unique((*original.provenance, *parsed.provenance)),
            }
        )
        resources.extend(week.resources)
        warnings.extend(week.warnings)
        provenance.extend(week.provenance)
    # Recompute absence warnings when an existing result receives more weeks.
    warnings = [
        warning for warning in warnings if warning.code != "missing_week_fixture"
    ]
    for section in sections.values():
        if section.status == DiscoveryStatus.REFERENCED:
            warnings.append(
                DiscoveryWarning(
                    course_id=index.course_id,
                    section_key=section.key,
                    code="missing_week_fixture",
                    message="Week linked in navigation but not parsed locally",
                    provenance=section.provenance,
                )
            )
    return CourseDiscovery.model_validate(
        {
            **index.model_dump(),
            "sections": tuple(sections.values()),
            "resources": merge_resource_candidates(resources),
            "warnings": _unique(warnings),
            "provenance": _unique(provenance),
        }
    )


def discover_fixture_courses(manifest_path: Path | str) -> tuple[CourseDiscovery, ...]:
    """Validate the manifest and extract only course_index/week_overview HTML."""
    manifest_path = Path(manifest_path)
    manifest = load_fixture_manifest(manifest_path)
    courses = []
    for course in manifest.courses:
        indexes = [page for page in course.pages if page.role == "course_index"]
        if len(indexes) != 1:
            raise CS50ParseError(
                f"{course.course_id}: expected exactly one course_index fixture"
            )

        index = _parse_fixture(
            indexes[0], manifest_path.parent, course.course_id, parse_course_index
        )
        weeks = [
            _parse_fixture(
                page, manifest_path.parent, course.course_id, parse_week_page
            )
            for page in course.pages
            if page.role == "week_overview"
        ]
        courses.append(combine_course_pages(index, weeks))
    return tuple(courses)


def _parse_fixture(
    page: FixturePage,
    root: Path,
    course_id: CourseId,
    parser: Callable[..., CourseDiscovery],
) -> CourseDiscovery:
    return parser(
        (root / page.file).read_text(encoding="utf-8"),
        str(page.url),
        course_id=course_id,
        fixture_file=page.file,
    )
