"""Candidate Content Processing Service.

Normalizes candidate document representations, cleans HTML tags with BeautifulSoup,
and extracts domain, title, and descriptive snippets safely.
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import httpx
from backend.app.core.logging_config import logger
from backend.app.core.ssrf import validate_url_security


class CandidateContentService:
    @staticmethod
    def clean_text(html_or_text: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        if not html_or_text:
            return ""
        try:
            soup = BeautifulSoup(html_or_text, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            text = soup.get_text(separator=" ")
        except Exception:
            text = html_or_text

        # Clean excess whitespace
        clean = re.sub(r"\s+", " ", text).strip()
        return clean

    @classmethod
    async def fetch_and_process_url(cls, url: str) -> Dict[str, Any]:
        """Fetch live or local URL content safely with SSRF protection."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # SSRF Security check
        is_safe, reason = validate_url_security(url, enforce=False)
        if not is_safe:
            return {
                "title": domain,
                "snippet": f"Blocked: {reason}",
                "content_text": "",
                "domain": domain,
                "is_accessible": False,
                "http_status": 403,
            }

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                res = await client.get(url)
                body = res.text
                status = res.status_code

                soup = BeautifulSoup(body, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else domain
                clean_body = cls.clean_text(body)
                snippet = clean_body[:250].strip()

                return {
                    "title": title,
                    "snippet": snippet,
                    "content_text": clean_body,
                    "domain": domain,
                    "is_accessible": status < 400,
                    "http_status": status,
                }
        except Exception as e:
            logger.debug(f"Candidate fetch error for {url}: {e}")
            return {
                "title": domain,
                "snippet": f"Unable to fetch content: {str(e)}",
                "content_text": "",
                "domain": domain,
                "is_accessible": False,
                "http_status": None,
            }
