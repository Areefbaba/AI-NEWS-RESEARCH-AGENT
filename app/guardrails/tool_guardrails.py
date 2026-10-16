"""Tool and network guardrails: SSRF protection and destination validation."""

import ipaddress
import socket
import urllib.parse
from typing import Tuple


class SSRFProtectionError(ValueError):
    """Raised when an outbound URL violates SSRF safety boundaries."""
    pass


FORBIDDEN_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal",
    "instance-data", "169.254.169.254"
}


def is_safe_url(url_str: str) -> Tuple[bool, str]:
    """Verify that URL destination does not target internal IPs or cloud metadata."""
    if not url_str:
        return False, "URL is empty."

    try:
        parsed = urllib.parse.urlparse(url_str.strip())
    except Exception:
        return False, "Malformed URL syntax."

    # Enforce safe HTTP/HTTPS schemes
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Forbidden URL scheme '{parsed.scheme}'. Only http and https are permitted."

    host = parsed.hostname
    if not host:
        return False, "URL missing host name."

    host_lower = host.lower()
    if host_lower in FORBIDDEN_HOSTS or host_lower.endswith(".internal"):
        return False, f"Host '{host}' is prohibited by SSRF guardrail."

    # Check if host is an explicit IP address
    try:
        ip = ipaddress.ip_address(host_lower)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False, f"IP address '{host}' belongs to a private or reserved network range."
    except ValueError:
        # Not a direct IP literal, check if it resolves to loopback/private
        # Note: In production or strict environments, DNS resolution can be checked.
        if host_lower.startswith("127.") or host_lower.startswith("10.") or host_lower.startswith("192.168."):
            return False, "Prohibited local IP address notation."

    return True, "URL destination is safe."


def validate_outbound_url(url_str: str) -> str:
    """Validate URL, returning cleaned URL or raising SSRFProtectionError."""
    is_safe, reason = is_safe_url(url_str)
    if not is_safe:
        raise SSRFProtectionError(f"SSRF violation blocked: {reason}")
    return url_str.strip()
