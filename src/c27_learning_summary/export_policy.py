"""Offline public metadata contract. No DNS, I/O from catalogs, or secret logging.

Approval is exact (canonical host/path), independent of syntactic eligibility.
Only this module decides which URLs and structured metadata can be exported.
"""

import ipaddress
import json
import re
import unicodedata
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

WITHHELD = "[withheld metadata]"
_METRIC_KEYS = {
    "input_tokens",
    "output_tokens",
    "known_input_tokens",
    "known_output_tokens",
    "max_output_tokens",
}
_MARKERS = {
    "token",
    "tokens",
    "session",
    "sessions",
    "sessionid",
    "jsessionid",
    "accesstoken",
    "authtoken",
    "refreshtoken",
    "clientsecret",
    "secret",
    "secrets",
    "password",
    "passwords",
    "passwd",
    "signature",
    "authorization",
    "auth",
    "credential",
    "credentials",
    "apikey",
    "accesskey",
    "privatekey",
    "bearer",
    "jwt",
    "sid",
    "phpsessid",
    "sessionkey",
    "authkey",
}


def _credential_marker(value: str) -> bool:
    # Split CamelCase before folding, and also recognize joined conventional names.
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    words = re.findall(r"[a-z0-9]+", separated.lower())
    return bool(set(words) & _MARKERS) or "".join(words) in _MARKERS


def _public_host(host: str) -> bool:
    host = host.removesuffix(".").lower()
    if not host or not host.isascii() or "%" in host:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        labels = host.split(".")
        return (
            len(host) <= 253
            and len(labels) >= 2
            and all(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x) for x in labels
            )
            and re.fullmatch(r"[a-z]{2,63}", labels[-1]) is not None
            and labels[-1]
            not in {
                "localhost",
                "local",
                "internal",
                "lan",
                "home",
                "invalid",
                "test",
                "onion",
            }
            and host != "home.arpa"
            and not host.endswith(".home.arpa")
            and not any(_credential_marker(x) for x in labels)
        )
    return (
        address.is_global
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_private
        and not (isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped)
    )


def source_url_key(value: object) -> tuple[str, str] | None:
    """Syntax/security check only. Decode once for comparison, never for output."""
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 4096
        or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)
        or any(c in value for c in "\\?#")
    ):
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or not url.hostname
            or not _public_host(url.hostname)
            or "@" in url.netloc
            or "%" in url.netloc
            or re.fullmatch(
                r"(?:\[[0-9a-fA-F:.]+\]|[A-Za-z0-9.-]+)(?::[0-9]+)?", url.netloc
            )
            is None
            or url.port not in {None, 443}
        ):
            return None
        segments = url.path.split("/")
        if any(not segment for segment in segments[1:-1]):
            return None
        decoded_segments = []
        for segment in segments:
            if re.search(r"%(?![0-9a-fA-F]{2})", segment):
                return None
            decoded = unquote(segment, errors="strict")
            if (
                re.fullmatch(r"[A-Za-z0-9._~-]*", decoded) is None
                or decoded in {".", ".."}
                or _credential_marker(decoded)
            ):
                return None
            decoded_segments.append(decoded)
        return url.hostname.lower().removesuffix("."), "/".join(decoded_segments)
    except (ValueError, UnicodeError):
        return None


@dataclass(frozen=True)
class ExportPolicy:
    approved: frozenset[tuple[str, str]]

    @classmethod
    def from_config(cls, data: object) -> "ExportPolicy":
        """Trusted, code-reviewed configuration only. Invalid config fails closed."""
        try:
            if (
                not isinstance(data, dict)
                or set(data) != {"schema_version", "sources"}
                or data["schema_version"] != 1
            ):
                raise ValueError
            sources = data["sources"]
            if not isinstance(sources, list) or not 1 <= len(sources) <= 128:
                raise ValueError
            keys = set()
            ids = set()
            for source in sources:
                if not isinstance(source, dict) or set(source) != {
                    "id",
                    "review",
                    "urls",
                }:
                    raise ValueError
                if not all(
                    isinstance(source[k], str)
                    and re.fullmatch(r"[a-zA-Z0-9._-]{1,120}", source[k])
                    for k in ("id", "review")
                ):
                    raise ValueError
                if (
                    source["id"] in ids
                    or not isinstance(source["urls"], list)
                    or not 1 <= len(source["urls"]) <= 4096
                ):
                    raise ValueError
                ids.add(source["id"])
                for url in source["urls"]:
                    key = source_url_key(url)
                    if key is None or key in keys:
                        raise ValueError
                    keys.add(key)
            return cls(frozenset(keys))
        except (ValueError, TypeError, KeyError):
            raise ValueError("Invalid public source approval configuration") from None

    def source_url(self, value: object) -> str | None:
        key = source_url_key(value)
        return value if isinstance(value, str) and key in self.approved else None


def _load_policy() -> ExportPolicy:
    try:
        return ExportPolicy.from_config(
            json.loads(Path(__file__).with_name("public_sources.v1.json").read_bytes())
        )
    except (OSError, ValueError):
        # Missing/broken approvals cannot make every otherwise-public host approved.
        return ExportPolicy(frozenset())


POLICY = _load_policy()

# Every RFC scheme is subject to approval, including opaque URIs without //.
# Whitespace around a colon is deliberately treated as ambiguous URI syntax.
_URI = re.compile(r"(?:[a-zA-Z][a-zA-Z0-9+.-]*\s*:\s*|//)[^\s<>\"'`]*")
_IDENTITY_FIELDS = {
    "course_id",
    "week_id",
    "lecture_id",
    "unit_id",
    "material_id",
    "source_id",
    "parser_version",
    "artifact_id",
    "block_id",
    "selected_material_ids",
    "summary_selection",
}
_LOCAL_ID = re.compile(
    r"(?:resource|source|material|material_block|material_doc|material_unit|week_material):[a-f0-9]{64}"
    r"|synthetic:(?:transcript|notes|code|slides)"
    r"|processed:(?:transcript|notes|code|slides):[0-9]+"
    r"|(?:cue|notes|code):[0-9]+"
    r"|[a-f0-9]{64}:[A-Za-z0-9_.-]{1,120}"
)


def _approved_metadata_uris(value: str) -> bool:
    candidates = _URI.findall(value)
    return bool(candidates) and all(
        exportable_source_url(uri.rstrip("),.;")) is not None for uri in candidates
    )


def exportable_source_url(value: object) -> str | None:
    return POLICY.source_url(value)


def metadata_text(value: str) -> str:
    """Inspect bounded decoded views; return original bytes or a constant marker.

    This applies to metadata only. Learning excerpts/claims never enter here.
    An entire field is withheld if any embedded URL is unsafe or unreviewed.
    """
    if len(value) > 12000 or any(ord(c) < 32 and c not in "\n\t" for c in value):
        return WITHHELD
    view = unicodedata.normalize("NFKC", unescape(value))
    for _ in range(4):
        if "%" not in view:
            break
        if re.search(r"%(?![0-9a-fA-F]{2})", view):
            return WITHHELD
        try:
            view = unquote(view, errors="strict")
        except UnicodeError:
            return WITHHELD
    view = unicodedata.normalize("NFKC", unescape(view))
    if (
        "%" in view
        or "\\" in view
        or re.search(r"(?:^|\s)/(?:home|tmp|etc|root|var)/", view)
    ):
        return WITHHELD
    # Credential assignments and path/name markers, including joined spellings.
    if any(_credential_marker(word) for word in re.split(r"[\s/:=?&#;]+", view)):
        return WITHHELD
    if _URI.search(view) or "//" in view:
        if "\n" in view or "\t" in view:
            return WITHHELD
        if not _approved_metadata_uris(view) or not _approved_metadata_uris(value):
            return WITHHELD
    return value


def metadata(value: Any) -> Any:
    """Bounded metadata traversal: depth 8, 4096 nodes, 128 keys, 1024 items.

    Unknown types/overflow become a constant. Keys that need withholding are
    dropped. Callers select schema fields first; no arbitrary model serialization.
    """
    remaining = 4096

    def visit(item: Any, depth: int, identity: bool = False) -> Any:
        nonlocal remaining
        remaining -= 1
        if depth > 8 or remaining < 0:
            return WITHHELD
        if item is None or type(item) in {bool, int, float}:
            return item
        if isinstance(item, str):
            # These are existing local identity grammars, never URL approvals.
            # Scalar internal identities retain their R06 representation;
            # public projections pass mappings with designated identity fields.
            if (
                (identity or depth == 0)
                and _LOCAL_ID.fullmatch(item)
                and not any(_credential_marker(word) for word in item.split(":"))
            ):
                return item
            return metadata_text(item)
        if isinstance(item, (list, tuple)):
            if len(item) > 1024:
                return WITHHELD
            return [visit(x, depth + 1, identity) for x in item]
        if isinstance(item, dict):
            if len(item) > 128:
                return WITHHELD
            return {
                k: visit(v, depth + 1, k in _IDENTITY_FIELDS)
                for k, v in item.items()
                if isinstance(k, str) and (k in _METRIC_KEYS or metadata_text(k) == k)
            }
        return WITHHELD

    return visit(value, 0)
