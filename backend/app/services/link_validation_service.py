"""Asynchronous Link Validation Engine.

Features:
- High-throughput asynchronous validation with httpx
- SSRF prevention blocking private RFC-1918 and internal ranges
- Bounded concurrency with async semaphores
- Per-domain rate limiting to prevent target throttling
- In-memory validation cache with configurable TTL
- Exponential backoff retry mechanism for transient network faults
- Precise taxonomy of failure modes (404, 4xx, 5xx, timeouts, DNS, redirects)
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import httpx
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.core.ssrf import validate_url_security
from backend.app.schemas.link import LinkValidationResult


def get_utc_now():
    return datetime.now(timezone.utc)


class ValidationCache:
    """Thread-safe in-memory cache for validated URLs with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Tuple[LinkValidationResult, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, url: str) -> Optional[LinkValidationResult]:
        async with self._lock:
            if url in self._cache:
                result, timestamp = self._cache[url]
                if time.time() - timestamp < self.ttl:
                    return result
                del self._cache[url]
            return None

    async def set(self, url: str, result: LinkValidationResult):
        async with self._lock:
            self._cache[url] = (result, time.time())

    async def clear(self):
        async with self._lock:
            self._cache.clear()


class LinkValidationService:
    def __init__(self):
        self.cache = ValidationCache(ttl_seconds=settings.VALIDATION_CACHE_TTL_SECONDS)
        self.global_semaphore = asyncio.Semaphore(settings.VALIDATION_MAX_CONCURRENCY)
        self.domain_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.domain_sem_lock = asyncio.Lock()

    async def _get_domain_semaphore(self, domain: str) -> asyncio.Semaphore:
        async with self.domain_sem_lock:
            if domain not in self.domain_semaphores:
                self.domain_semaphores[domain] = asyncio.Semaphore(
                    settings.VALIDATION_RATE_LIMIT_PER_DOMAIN
                )
            return self.domain_semaphores[domain]

    @staticmethod
    def classify_status(
        status_code: Optional[int],
        is_redirect: bool,
        redirect_count: int,
        error_type: Optional[str] = None,
    ) -> str:
        """Classify link health into standard research taxonomy."""
        if error_type:
            if error_type == "TIMEOUT":
                return "TIMEOUT"
            if error_type == "DNS_ERROR":
                return "DNS_ERROR"
            if error_type == "CONNECTION_ERROR":
                return "CONNECTION_ERROR"
            if error_type == "INVALID_URL":
                return "INVALID_URL"
            return "UNKNOWN"

        if status_code is None:
            return "UNKNOWN"

        # Explicit Redirects (when not automatically followed or redirected)
        if 300 <= status_code < 400 or (is_redirect and redirect_count > 0):
            return "REDIRECT"

        if 200 <= status_code < 300:
            return "VALID"

        if status_code == 404:
            return "BROKEN_404"
        if status_code == 401:
            return "UNAUTHORIZED"
        if status_code == 403:
            return "FORBIDDEN"
        if 400 <= status_code < 500:
            return "BROKEN_4XX"
        if 500 <= status_code < 600:
            return "SERVER_ERROR_5XX"

        return "UNKNOWN"

    async def validate_url(
        self,
        url: str,
        normalized_url: Optional[str] = None,
        use_cache: bool = True,
    ) -> LinkValidationResult:
        """Validate a single URL asynchronously with SSRF checks, retries, and caching."""
        target_norm = normalized_url or url

        if use_cache:
            cached = await self.cache.get(target_norm)
            if cached:
                logger.debug(f"Cache hit for URL: {target_norm}")
                return cached

        # 1. SSRF and Domain Security Check
        is_safe, sec_reason = validate_url_security(
            url, enforce=settings.SSRF_PROTECTION_ENABLED
        )
        if not is_safe:
            result = LinkValidationResult(
                url=url,
                normalized_url=target_norm,
                status="INVALID_URL",
                status_code=None,
                final_url=url,
                redirect_count=0,
                response_time_ms=0.0,
                content_type=None,
                error_message=f"SSRF Protection triggered: {sec_reason}",
                validation_timestamp=get_utc_now(),
            )
            await self.cache.set(target_norm, result)
            return result

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        domain_sem = await self._get_domain_semaphore(domain)

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with self.global_semaphore:
            async with domain_sem:
                result = await self._execute_http_validation(url, target_norm, headers)
                await self.cache.set(target_norm, result)
                return result

    async def _execute_http_validation(
        self, url: str, target_norm: str, headers: dict
    ) -> LinkValidationResult:
        """Execute HTTP request with retries, exponential backoff, and redirect inspection."""
        retries = settings.VALIDATION_MAX_RETRIES
        backoff = settings.VALIDATION_BACKOFF_FACTOR
        timeout_sec = settings.VALIDATION_TIMEOUT_SECONDS

        status_code: Optional[int] = None
        final_url = url
        redirect_count = 0
        response_time_ms: Optional[float] = None
        content_type: Optional[str] = None
        error_message: Optional[str] = None
        error_type: Optional[str] = None
        is_redirect = False

        transport = httpx.AsyncHTTPTransport(retries=0, verify=False)
        client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(timeout_sec, connect=5.0),
            follow_redirects=True,
            max_redirects=5,
            headers=headers,
        )

        try:
            for attempt in range(retries + 1):
                start_time = time.perf_counter()
                try:
                    # Attempt GET request with stream=True so large bodies aren't downloaded
                    async with client.stream("GET", url) as response:
                        duration = (time.perf_counter() - start_time) * 1000.0
                        response_time_ms = round(duration, 2)
                        status_code = response.status_code
                        final_url = str(response.url)
                        redirect_count = len(response.history)
                        content_type = response.headers.get("content-type", "").split(";")[0].strip()

                        # Check if redirects took place
                        if redirect_count > 0:
                            is_redirect = True

                        # If status is successful or clean client error, no need to retry
                        if status_code < 500:
                            break

                except httpx.TimeoutException as e:
                    duration = (time.perf_counter() - start_time) * 1000.0
                    response_time_ms = round(duration, 2)
                    error_type = "TIMEOUT"
                    error_message = f"Request timed out after {timeout_sec}s: {str(e)}"
                except (httpx.ConnectError, httpx.NetworkError) as e:
                    duration = (time.perf_counter() - start_time) * 1000.0
                    response_time_ms = round(duration, 2)
                    err_str = str(e).lower()
                    if "getaddrinfo" in err_str or "name resolution" in err_str or "dns" in err_str:
                        error_type = "DNS_ERROR"
                        error_message = f"DNS resolution failed: {str(e)}"
                    else:
                        error_type = "CONNECTION_ERROR"
                        error_message = f"Network connection failed: {str(e)}"
                except Exception as e:
                    duration = (time.perf_counter() - start_time) * 1000.0
                    response_time_ms = round(duration, 2)
                    error_type = "UNKNOWN"
                    error_message = f"Unexpected validation error: {str(e)}"

                # Exponential backoff for retry
                if attempt < retries:
                    wait_time = backoff * (2 ** attempt)
                    await asyncio.sleep(wait_time)
        finally:
            await client.aclose()

        status_classification = self.classify_status(
            status_code=status_code,
            is_redirect=is_redirect,
            redirect_count=redirect_count,
            error_type=error_type,
        )

        return LinkValidationResult(
            url=url,
            normalized_url=target_norm,
            status=status_classification,
            status_code=status_code,
            final_url=final_url,
            redirect_count=redirect_count,
            response_time_ms=response_time_ms,
            content_type=content_type,
            error_message=error_message,
            validation_timestamp=get_utc_now(),
        )

    async def validate_batch(
        self, links_data: list, use_cache: bool = True
    ) -> list:
        """Validate a batch of links concurrently."""
        tasks = [
            self.validate_url(
                url=item.get("original_url") or item.get("url"),
                normalized_url=item.get("normalized_url"),
                use_cache=use_cache,
            )
            for item in links_data
        ]
        return await asyncio.gather(*tasks)


validation_service = LinkValidationService()
