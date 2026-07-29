"""Resilient official-source logo discovery for AtlasFind v1.0.4.

The crawler never uses search engines and never tries to defeat bot protection.
It retries transient failures, probes standard web-app asset endpoints, and falls
back to other official URLs already stored in the AtlasFind catalog.
"""
from __future__ import annotations

import ipaddress
import json
import socket
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 512 * 1024
TIMEOUT_SECONDS = 12
USER_AGENT = "AtlasFindBrandingBot/1.1 (+https://atlasfind.org)"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)

STANDARD_ASSET_PATHS = (
    "/site.webmanifest",
    "/manifest.webmanifest",
    "/manifest.json",
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
    "/favicon.svg",
    "/favicon.png",
    "/favicon.ico",
)


class _LimitedRedirect(HTTPRedirectHandler):
    max_redirections = 5


@dataclass(frozen=True)
class LogoCandidate:
    url: str
    source_page: str
    source_type: str
    relation: str
    score: int
    requires_review: bool = True
    declared_sizes: str | None = None
    declared_purpose: str | None = None
    discovery_method: str = "html"

    def to_dict(self) -> dict:
        return asdict(self)


class _HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag.lower() == "link":
            self.links.append(values)
        elif tag.lower() == "meta":
            self.meta.append(values)


def _ascii_safe_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
        quote(parts.query, safe="=&?/:;+,%@!$'()*-._~"),
        quote(parts.fragment, safe="-._~"),
    ))


def _is_public_hostname(hostname: str | None) -> bool:
    if not hostname or hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    except OSError:
        return False
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return bool(addresses)


def validate_remote_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and _is_public_hostname(parsed.hostname)


def _read_url(
    url: str,
    *,
    accept: str,
    max_bytes: int,
    retries: int = 2,
) -> tuple[bytes, str, str]:
    safe_url = _ascii_safe_url(url)
    if not validate_remote_url(safe_url):
        raise ValueError("Remote URL must be public HTTPS")

    last_error: Exception | None = None
    agents = (USER_AGENT, BROWSER_USER_AGENT)
    for attempt in range(max(1, retries + 1)):
        request = Request(
            safe_url,
            headers={
                "User-Agent": agents[min(attempt, len(agents) - 1)],
                "Accept": accept,
                "Accept-Language": "en-US,en;q=0.8",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with build_opener(_LimitedRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
                final_url = _ascii_safe_url(response.geturl())
                if not validate_remote_url(final_url):
                    raise ValueError("Redirected to a blocked address")
                content_type = response.headers.get_content_type()
                declared = response.headers.get("Content-Length")
                if declared and declared.isdigit() and int(declared) > max_bytes:
                    raise ValueError("Remote response is too large")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise ValueError("Remote response exceeded the size limit")
                return body, content_type, final_url
        except HTTPError as exc:
            last_error = exc
            # Permanent access controls are not bypassed. Alternate official
            # URLs and direct standard asset paths are tried by the caller.
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.75 * (attempt + 1)
            time.sleep(min(delay, 4.0))
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    if last_error:
        raise last_error
    raise ValueError("Remote request failed")


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _same_site(candidate: str, official: str) -> bool:
    a, b = _host(candidate), _host(official)
    return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))


def _candidate_score(
    relation: str,
    same_site: bool,
    url: str,
    *,
    declared_sizes: str | None = None,
    source_type: str = "official_product_site",
) -> int:
    relation = relation.lower()
    score = 0
    if "manifest" in relation:
        score += 95
    elif "apple-touch-icon" in relation:
        score += 90
    elif "mask-icon" in relation:
        score += 86
    elif "icon" in relation:
        score += 80
    elif "og:image" in relation:
        score += 40
    if same_site:
        score += 20
    if source_type in {"official_brand_kit", "official_app_store", "official_repository"}:
        score += 15
    lowered = url.lower()
    if any(token in lowered for token in ("logo", "icon", "brand", "app")):
        score += 10
    if lowered.endswith((".svg", ".webp", ".png")):
        score += 8
    if declared_sizes:
        numeric = []
        for token in declared_sizes.lower().replace("x", " ").split():
            if token.isdigit():
                numeric.append(int(token))
        if numeric and max(numeric) >= 128:
            score += 12
        elif numeric and max(numeric) >= 64:
            score += 6
    return score


def _add_candidate(
    candidates: dict[str, LogoCandidate],
    *,
    url: str,
    source_page: str,
    source_type: str,
    relation: str,
    sizes: str | None = None,
    purpose: str | None = None,
    method: str = "html",
) -> None:
    absolute = _ascii_safe_url(url)
    if not validate_remote_url(absolute):
        return
    candidate = LogoCandidate(
        absolute,
        source_page,
        source_type,
        relation,
        _candidate_score(
            relation,
            _same_site(absolute, source_page),
            absolute,
            declared_sizes=sizes,
            source_type=source_type,
        ),
        declared_sizes=sizes,
        declared_purpose=purpose,
        discovery_method=method,
    )
    previous = candidates.get(absolute)
    if previous is None or candidate.score > previous.score:
        candidates[absolute] = candidate


def _parse_manifest(
    manifest_url: str,
    *,
    source_page: str,
    source_type: str,
    candidates: dict[str, LogoCandidate],
) -> None:
    raw, manifest_type, manifest_final = _read_url(
        manifest_url,
        accept="application/manifest+json,application/json,text/plain;q=0.8",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    if manifest_type not in {"application/json", "application/manifest+json", "text/plain", "application/octet-stream"}:
        return
    payload = json.loads(raw.decode("utf-8-sig"))
    icons = payload.get("icons", []) if isinstance(payload, dict) else []
    for icon in icons:
        if not isinstance(icon, dict) or not icon.get("src"):
            continue
        _add_candidate(
            candidates,
            url=urljoin(manifest_final, str(icon["src"])),
            source_page=source_page,
            source_type=source_type,
            relation="manifest-icon",
            sizes=str(icon.get("sizes") or "") or None,
            purpose=str(icon.get("purpose") or "") or None,
            method="manifest",
        )


def _discover_from_html(
    page_url: str,
    *,
    source_type: str,
    candidates: dict[str, LogoCandidate],
) -> str:
    html, content_type, final_url = _read_url(
        page_url,
        accept="text/html,application/xhtml+xml",
        max_bytes=MAX_HTML_BYTES,
    )
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(f"Official page returned unsupported content type: {content_type}")
    parser = _HeadParser()
    parser.feed(html.decode("utf-8", errors="replace"))

    for item in parser.links:
        rel = " ".join(item.get("rel", "").lower().split())
        href = item.get("href", "")
        if not href:
            continue
        if "manifest" in rel:
            try:
                _parse_manifest(
                    urljoin(final_url, href),
                    source_page=final_url,
                    source_type=source_type,
                    candidates=candidates,
                )
            except (OSError, ValueError, json.JSONDecodeError, HTTPError, URLError):
                pass
        if "icon" in rel:
            _add_candidate(
                candidates,
                url=urljoin(final_url, href),
                source_page=final_url,
                source_type=source_type,
                relation=rel or "icon",
                sizes=item.get("sizes") or None,
                method="html-link",
            )

    for item in parser.meta:
        prop = (item.get("property") or item.get("name") or "").lower()
        content = item.get("content", "")
        if prop in {"og:image", "twitter:image", "twitter:image:src"} and content:
            _add_candidate(
                candidates,
                url=urljoin(final_url, content),
                source_page=final_url,
                source_type=source_type,
                relation="og:image",
                method="html-meta",
            )
    return final_url


def _url_variants(url: str) -> list[str]:
    parsed = urlparse(url)
    if not parsed.hostname:
        return [url]
    variants = [url]
    host = parsed.hostname
    alternate = host[4:] if host.startswith("www.") else "www." + host
    alt_netloc = alternate + (f":{parsed.port}" if parsed.port else "")
    variants.append(parsed._replace(netloc=alt_netloc).geturl())
    # Root is useful when an official deep link loops or returns a huge page.
    variants.append(parsed._replace(path="/", params="", query="", fragment="").geturl())
    return list(dict.fromkeys(_ascii_safe_url(item) for item in variants if validate_remote_url(_ascii_safe_url(item))))


def _probe_standard_assets(
    page_url: str,
    *,
    source_type: str,
    candidates: dict[str, LogoCandidate],
) -> None:
    parsed = urlparse(page_url)
    root = f"{parsed.scheme}://{parsed.netloc}/"
    for path in STANDARD_ASSET_PATHS:
        asset_url = urljoin(root, path)
        try:
            if "manifest" in path:
                _parse_manifest(
                    asset_url,
                    source_page=page_url,
                    source_type=source_type,
                    candidates=candidates,
                )
            else:
                # Candidate remains unverified until the import preflight opens it.
                _add_candidate(
                    candidates,
                    url=asset_url,
                    source_page=page_url,
                    source_type=source_type,
                    relation="standard-endpoint-icon",
                    method="standard-endpoint",
                )
        except (OSError, ValueError, json.JSONDecodeError, HTTPError, URLError, StopIteration):
            continue


def discover_logo_candidates(
    official_url: str,
    alternative_official_urls: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Discover candidates and return a detailed attempt log.

    Alternate URLs must already be present in the AtlasFind catalog as official
    sources. No search engine or anti-bot bypass is used.
    """
    sources: list[tuple[str, str]] = [(official_url, "official_product_site")]
    for source in alternative_official_urls or []:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "")
        source_type = str(source.get("source_type") or "official_documentation")
        if url and validate_remote_url(_ascii_safe_url(url)):
            sources.append((url, source_type))

    candidates: dict[str, LogoCandidate] = {}
    attempts: list[dict] = []
    seen_pages: set[str] = set()
    for source_url, source_type in sources:
        for variant in _url_variants(source_url):
            if variant in seen_pages:
                continue
            seen_pages.add(variant)
            try:
                final_url = _discover_from_html(
                    variant,
                    source_type=source_type,
                    candidates=candidates,
                )
                attempts.append({"url": variant, "status": "success", "final_url": final_url, "source_type": source_type})
                _probe_standard_assets(final_url, source_type=source_type, candidates=candidates)
            except Exception as exc:  # logged per source; other official sources continue
                attempts.append({"url": variant, "status": "error", "error": str(exc), "source_type": source_type})
                _probe_standard_assets(variant, source_type=source_type, candidates=candidates)

    sorted_candidates = [
        item.to_dict()
        for item in sorted(candidates.values(), key=lambda x: (-x.score, x.url))
    ]
    return sorted_candidates, attempts
