"""URL Utilities for Normalization, Token Extraction, and Validation."""

import os
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Dict, Any, Optional

# Standard tracking and analytics query parameters to strip
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "_ga",
    "_gl",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
}

URL_REGEX = re.compile(
    r"^(?:http|https)://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"  # domain...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_valid_url_syntax(url: Optional[str]) -> bool:
    """Validate that the string looks like an HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False


def normalize_url(url: str, strip_tracking: bool = True) -> str:
    """Normalize URL by:

    - Trimming whitespace
    - Lowercasing scheme and hostname
    - Removing default ports (:80, :443)
    - Stripping marketing/tracking query parameters (e.g. utm_*)
    - Preserving semantic query parameters
    - Normalizing trailing slashes on empty paths
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    clean_url = url.strip()
    # Fix accidental leading/trailing quotes or punctuation often found in parsed docs
    clean_url = clean_url.strip(" '\"()[]<>.,;")

    parsed = urlparse(clean_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Malformed URL without scheme or host: {url}")

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path
    if not path:
        path = "/"

    # Clean query parameters
    query = parsed.query
    if query:
        query_pairs = parse_qsl(query, keep_blank_values=True)
        filtered_pairs = []
        for k, v in query_pairs:
            k_lower = k.lower()
            if strip_tracking and (k_lower in TRACKING_PARAMS or k_lower.startswith("utm_")):
                continue
            filtered_pairs.append((k, v))
        # Keep query parameters sorted for deterministic canonical representation
        filtered_pairs.sort(key=lambda x: x[0])
        query = urlencode(filtered_pairs)

    # Normalize url components (strip fragments for base URL comparison)
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, ""))
    return normalized


def extract_url_tokens(url: str) -> Dict[str, Any]:
    """Break a URL down into tokens (domain, path segments, filename, query keys)

    useful for context-matching and semantic candidate scoring.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path
        filename = os.path.basename(path) if path else ""

        # Path segments without empty items
        path_segments = [seg for seg in path.strip("/").split("/") if seg]

        # Extract meaningful alphanumeric terms from path & filename
        terms = re.findall(r"[a-zA-Z0-9]+", f"{domain} {path}")

        query_keys = [k for k, _ in parse_qsl(parsed.query)]

        return {
            "domain": domain,
            "path": path,
            "filename": filename,
            "path_segments": path_segments,
            "query_keys": query_keys,
            "terms": list(set(t.lower() for t in terms if len(t) > 2)),
        }
    except Exception:
        return {
            "domain": "",
            "path": "",
            "filename": "",
            "path_segments": [],
            "query_keys": [],
            "terms": [],
        }
