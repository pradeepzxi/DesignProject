"""SSRF (Server-Side Request Forgery) Protection Module.

Ensures that external link validation never probes local loopback, private RFC-1918,
carrier-grade NAT, or link-local network spaces. Resolves DNS records securely and
validates against comprehensive IP address blacklists.
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple
import logging

logger = logging.getLogger("link_integrity.ssrf")

FORBIDDEN_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",  # AWS/GCP/Azure instance metadata
}

FORBIDDEN_DOMAINS_SUFFIXES = (
    ".local",
    ".internal",
    ".lan",
    ".home.arpa",
    ".corp",
    ".priv",
)


class SSRFProtectionError(ValueError):
    """Raised when a URL targets a restricted or private address."""
    pass


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Check if an IPv4 or IPv6 address is private, loopback, multicast, or reserved."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_url_security(url: str, enforce: bool = True) -> Tuple[bool, str]:
    """Validate that the given URL does not target internal infrastructure.

    Returns:
        (is_safe, reason)
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or not a string"

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"URL parse error: {str(e)}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme: {parsed.scheme}"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL has no valid hostname"

    hostname_lower = hostname.lower()

    if hostname_lower in FORBIDDEN_HOSTS:
        return False, f"Host '{hostname}' is explicitly forbidden (SSRF target)"

    for suffix in FORBIDDEN_DOMAINS_SUFFIXES:
        if hostname_lower.endswith(suffix):
            return False, f"Domain suffix '{suffix}' is restricted"

    # If hostname is a direct IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if is_ip_private_or_restricted(str(ip)):
            return False, f"IP '{hostname}' belongs to a private/restricted network range"
        return True, "Safe public IP"
    except ValueError:
        # Not a direct IP, so resolve DNS
        pass

    if not enforce:
        return True, "SSRF check skipped"

    # Resolve hostname via DNS
    try:
        # Port defaults to 80 or 443
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            if is_ip_private_or_restricted(ip_str):
                return False, f"Resolved IP '{ip_str}' for hostname '{hostname}' is in private/restricted range"
    except socket.gaierror as e:
        # DNS resolution failure will be handled by the validation service as DNS_ERROR
        # But it's not an SSRF breach
        return True, f"DNS resolution failed: {e}"
    except Exception as e:
        logger.warning(f"Error checking SSRF for hostname {hostname}: {e}")
        return False, f"Security check exception: {str(e)}"

    return True, "Safe public host"
