#!/usr/bin/env python3
"""R02-T032 - bounded redirect-chain verification for three Food & Drink APIs.

The checker resolves redirect chains explicitly with ``http.client`` so every
hop is budgeted, recorded and checked.  It resolves each destination once,
validates every returned address, and then connects directly to one of those
validated addresses.  The original host name is retained for the HTTP ``Host``
header, TLS SNI and certificate host name verification, so connection
establishment cannot silently re-resolve the host to a different address.  It
never sends credentials, never follows redirects into private networks (unless
a local mock server is explicitly allowed by the offline self-test), and never
downloads more than a small HTML snippet.

Commands::

    python3 tools/course_checks/r02-t032.py --self-test
    python3 tools/course_checks/r02-t032.py --live

The target list is fixed in ``TARGETS`` below.  There is deliberately no CLI
option for checking an arbitrary URL.
"""

import argparse
import hashlib
import http.client
import ipaddress
import json
import platform
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

TASK_ID = "R02-T032"
ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = ROOT / "work" / TASK_ID
README_PATH = ROOT / "README.md"

USER_AGENT = (
    "public-apis-course-checker/1.0 "
    "(R02-T032 educational redirect verifier; "
    "+https://github.com/S-AI-Projects/public-apis)"
)

ALLOWED_SCHEMES = ("http", "https")
DEFAULT_PORTS = {"http": 80, "https": 443}
FOLLOW_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
TRANSIENT_HTTP_STATUSES = (408, 425, 429)
AUTH_STATUSES = (401, 403)

MAX_REDIRECTS_DEFAULT = 5
CONNECT_TIMEOUT_DEFAULT = 5.0
READ_TIMEOUT_DEFAULT = 5.0
SELF_TEST_MAX_REDIRECTS = 2
MAX_BODY_BYTES = 32 * 1024
MAX_URL_LENGTH = 8192
MAX_REDIRECTS_LIMIT = 20

# The only URLs this tool is allowed to request.  README line numbers are
# resolved at runtime so the evidence stays accurate without hard-coded line
# numbers drifting when unrelated rows are added.
TARGETS = [
    {
        "name": "BaconMockup",
        "url": "https://baconmockup.com/",
        "auth": "No",
        "https": "Yes",
        "cors": "Yes",
        "description": "Resizable bacon placeholder images",
    },
    {
        "name": "CalorieNinjas",
        "url": "https://calorieninjas.com/api",
        "auth": "`apiKey`",
        "https": "Yes",
        "cors": "Yes",
        "description": "Nutrition and calorie data for foods and recipes",
    },
    {
        "name": "Chomp",
        "url": "https://chompthis.com/api/",
        "auth": "`apiKey`",
        "https": "Yes",
        "cors": "Unknown",
        "description": "Data about various grocery products and foods",
    },
]

CLASSIFICATION_DESCRIPTIONS = {
    "OK": "The original URL answered with a valid 2xx status; no redirects were followed.",
    "MOVED": "One or more redirects ended at a valid 2xx destination.",
    "REDIRECT_LOOP": "A redirect destination repeated an already-visited URL.",
    "REDIRECT_LIMIT": "The configured redirect budget was exhausted before a terminal response.",
    "TIMEOUT": "A DNS wait, connect, TLS, send, read or required HTML body read exceeded its timeout.",
    "DNS_FAILURE": "The host name could not be resolved.",
    "CONNECTION_ERROR": "The connection failed, closed before a valid HTTP response, or failed while reading a required HTML body.",
    "TLS_ERROR": "TLS negotiation or certificate verification failed.",
    "TRANSIENT_FAILURE": "A temporary HTTP or network failure (for example 429 or 5xx).",
    "AUTH_WALL": "A login/identity provider, HTTP 401/403, or an explicit login page was observed.",
    "HTTP_ERROR": "A definitive HTTP error or an unexpected 3xx response.",
    "INVALID_URL": "The URL is syntactically invalid or unsafe (including malformed Location).",
    "UNSUPPORTED_SCHEME": "Only http:// and https:// destinations are followed.",
    "BLOCKED_TARGET": "A loopback, private, link-local or otherwise non-global destination was refused.",
}

# Login/identity-provider heuristics are deliberately narrower than "any URL
# containing login":
# - Redirect destinations are checked for known login/identity-provider paths.
# - Every 2xx HTML response is inspected for explicit login forms.
# - This applies to both direct and redirected responses.
# Path segments must look like a login endpoint rather than a documentation page.
IDP_EXACT_HOSTS = {
    "accounts.google.com",
    "login.microsoftonline.com",
    "login.live.com",
    "login.yahoo.com",
    "appleid.apple.com",
    "duosecurity.com",
    "onelogin.com",
}
IDP_HOST_SUFFIXES = (
    ".okta.com",
    ".auth0.com",
    ".onelogin.com",
    ".duosecurity.com",
    ".pingidentity.com",
)
LOGIN_PATH_RE = re.compile(
    r"(?:^|/)(?:login|log-in|log_in|signin|sign-in|sign_in|sign_on|"
    r"signon|sso|saml|authorize)(?:[/.?]|$)",
    re.IGNORECASE,
)
IDP_PATH_RE = re.compile(
    r"(?:^|/)(?:authorize|login|log-in|log_in|sso|saml|oauth2?|"
    r"signin|sign-in|sign_in)(?:[/.?]|$)",
    re.IGNORECASE,
)
LOGIN_SPECIAL_PATHS = (
    re.compile(r"(?:^|/)users/sign_in(?:[/.?]|$)", re.IGNORECASE),
    re.compile(r"(?:^|/)account(?:s)?/login(?:[/.?]|$)", re.IGNORECASE),
    re.compile(r"(?:^|/)oauth2?/authorize(?:[/.?]|$)", re.IGNORECASE),
    re.compile(r"(?:^|/)wp-login\.php(?:[?]|$)", re.IGNORECASE),
)


class CheckFailure(Exception):
    """Raised when an offline check does not meet its expectation."""


class PeerAddressMismatch(Exception):
    """Raised when a connected socket is not the validated destination."""


def require(condition, message):
    """Explicit check that is not disabled by ``python3 -O``."""

    if not condition:
        raise CheckFailure(message)


def utc_now():
    """Return a UTC timestamp with a trailing Z."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def write_json(path, payload):
    """Write deterministic, human-readable JSON evidence."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def display_path(path):
    """Show repository-relative paths in console/evidence output."""

    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def short_text(value, limit=300):
    """Collapse whitespace and bound a diagnostic string."""

    text = " ".join(str(value).split())
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def validate_url(url):
    """Return ``(normalized_url, error)`` for a candidate URL.

    ``error`` is ``None`` or a dict containing classification, error_type and
    message.  Fragments are removed because they are never sent to a server.
    Credentials in URLs are rejected rather than forwarded.
    """

    if not isinstance(url, str):
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL must be a string",
        }

    url = url.strip()

    if not url:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL is empty",
        }

    if len(url) > MAX_URL_LENGTH:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "url_too_long",
            "message": "URL exceeds %d characters" % MAX_URL_LENGTH,
        }

    if any(ord(char) < 0x20 or char.isspace() for char in url):
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL contains whitespace or control characters",
        }

    if "\\" in url:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL contains a backslash",
        }

    try:
        parts = urlsplit(url)
    except ValueError as exc:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": short_text(exc),
        }

    scheme = (parts.scheme or "").lower()

    if not scheme:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL has no scheme",
        }

    if scheme not in ALLOWED_SCHEMES:
        return None, {
            "classification": "UNSUPPORTED_SCHEME",
            "error_type": "unsupported_scheme",
            "message": "Unsupported URL scheme: %s" % scheme,
        }

    if parts.username is not None or parts.password is not None:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "credentials_not_allowed",
            "message": "URLs containing credentials are not requested",
        }

    try:
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_port",
            "message": short_text(exc),
        }

    if not host:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_url",
            "message": "URL has no host",
        }

    try:
        ascii_host = host.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_host",
            "message": short_text(exc),
        }

    default_port = DEFAULT_PORTS[scheme]
    if port is not None and not 1 <= port <= 65535:
        return None, {
            "classification": "INVALID_URL",
            "error_type": "invalid_port",
            "message": "Port is outside 1-65535",
        }

    if ":" in ascii_host:
        netloc = "[%s]" % ascii_host
    else:
        netloc = ascii_host

    if port is not None and port != default_port:
        netloc = "%s:%d" % (netloc, port)

    path = parts.path or "/"
    normalized = urlunsplit((scheme, netloc, path, parts.query, ""))
    return normalized, None


def loop_key(url):
    """Canonical key used only for repeated-URL detection."""

    parts = urlsplit(url)
    port = parts.port
    if port is None:
        port = DEFAULT_PORTS.get(parts.scheme.lower())
    return (
        parts.scheme.lower(),
        (parts.hostname or "").lower(),
        port,
        parts.path or "/",
        parts.query,
    )


def login_url_reason(url):
    """Return a short reason when a URL looks like a login destination."""

    try:
        parts = urlsplit(url)
    except ValueError:
        return None

    host = (parts.hostname or "").lower()
    path = parts.path or "/"

    if host in IDP_EXACT_HOSTS:
        return "identity provider host: %s" % host

    if host.startswith(("login.", "sso.", "idp.")):
        return "login-style host: %s" % host

    if LOGIN_PATH_RE.search(path):
        return "login path: %s" % path

    for pattern in LOGIN_SPECIAL_PATHS:
        if pattern.search(path):
            return "login path: %s" % path

    for suffix in IDP_HOST_SUFFIXES:
        if (host == suffix[1:] or host.endswith(suffix)) and IDP_PATH_RE.search(
            path
        ):
            return "identity provider host: %s" % host

    return None


def looks_like_login_body(body):
    """Conservative login-page detection using a small HTML snippet."""

    if not body:
        return False

    text = body.decode("utf-8", "replace").lower()

    has_form = "<form" in text
    has_password_input = (
        'type="password"' in text
        or "type='password'" in text
        or 'name="password"' in text
        or "name='password'" in text
    )

    if has_form and has_password_input:
        return True

    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.DOTALL)
    if not title_match:
        return False

    title = " ".join(title_match.group(1).split())
    login_titles = ("sign in", "log in", "login", "authentication required")
    return has_form and any(
        title.startswith(prefix) for prefix in login_titles
    )


def resolve_addresses(host, port, timeout, resolver=None):
    """Resolve a host with a bounded caller wait.

    The wait is enforceable: the caller stops waiting after ``timeout`` and
    returns a TIMEOUT result.  Python's resolver API has no cancellation hook,
    so the daemon worker thread may remain alive until the operating-system
    resolver call returns.  The result of a timed-out worker is ignored.  A
    later connection never resolves the host name again; it connects directly
    to an address returned by this one resolution.
    """

    result = {}
    resolver = resolver or socket.getaddrinfo

    def worker():
        try:
            result["infos"] = resolver(
                host, port, type=socket.SOCK_STREAM
            )
        except OSError as exc:
            result["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return None, {
            "classification": "TIMEOUT",
            "error_type": "dns_timeout",
            "message": (
                "DNS lookup wait exceeded %.1fs; the resolver thread cannot "
                "be cancelled and its late result is ignored" % timeout
            ),
        }

    if "error" in result:
        exc = result["error"]
        return None, {
            "classification": "DNS_FAILURE",
            "error_type": "dns_failure",
            "message": short_text(exc),
        }

    infos = result.get("infos") or []
    if not infos:
        return None, {
            "classification": "DNS_FAILURE",
            "error_type": "dns_failure",
            "message": "No addresses returned for %s" % host,
        }

    return infos, None


def _literal_address_infos(host, port):
    """Build one getaddrinfo-shaped tuple without any resolver call."""

    literal = ipaddress.ip_address(host)
    if literal.version == 6:
        family = socket.AF_INET6
        sockaddr = (str(literal), port, 0, 0)
    else:
        family = socket.AF_INET
        sockaddr = (str(literal), port)
    return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]


def _address_allowed(ip, allow_loopback_for_self_test):
    """Return whether an address is permitted under the current mode."""

    if allow_loopback_for_self_test:
        return ip.is_loopback
    return ip.is_global


def prepare_destination(
    url, allow_loopback_for_self_test, timeout, resolver=None
):
    """Resolve and validate one destination before any connection.

    Every address returned for the host is checked.  A single non-global
    address rejects the whole destination before a socket is opened.  In
    self-test mode the only permitted non-global addresses are loopback
    addresses, because the offline fixture server listens on 127.0.0.1.
    """

    normalized, error = validate_url(url)
    if error:
        return None, error

    parts = urlsplit(normalized)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port or DEFAULT_PORTS[scheme]

    try:
        infos = _literal_address_infos(host, port)
    except ValueError:
        infos, resolve_error = resolve_addresses(
            host, port, timeout, resolver=resolver
        )
        if resolve_error:
            return None, resolve_error

    candidates = []
    seen = set()

    for info in infos:
        if len(info) < 5:
            return None, {
                "classification": "DNS_FAILURE",
                "error_type": "dns_failure",
                "message": "Resolver returned an incomplete address record",
            }

        family, socktype, proto, _canonname, sockaddr = info[:5]
        if not sockaddr:
            continue

        address = str(sockaddr[0])
        plain_address = address.split("%", 1)[0]

        try:
            ip = ipaddress.ip_address(plain_address)
        except ValueError:
            return None, {
                "classification": "BLOCKED_TARGET",
                "error_type": "blocked_destination",
                "message": "Unparseable resolved address: %s" % address,
            }

        if not _address_allowed(ip, allow_loopback_for_self_test):
            if allow_loopback_for_self_test:
                reason = (
                    "Non-loopback destination refused by offline fixture "
                    "policy: %s" % address
                )
            else:
                reason = "Non-global destination refused: %s" % address
            return None, {
                "classification": "BLOCKED_TARGET",
                "error_type": "blocked_destination",
                "message": reason,
            }

        candidate = {
            "family": family,
            "socktype": socktype or socket.SOCK_STREAM,
            "proto": proto or socket.IPPROTO_TCP,
            "sockaddr": sockaddr,
            "address": plain_address,
        }
        key = (family, str(sockaddr))
        if key not in seen:
            seen.add(key)
            candidates.append(candidate)

    if not candidates:
        return None, {
            "classification": "DNS_FAILURE",
            "error_type": "dns_failure",
            "message": "No usable addresses returned for %s" % host,
        }

    return {
        "normalized": normalized,
        "scheme": scheme,
        "hostname": host,
        "port": port,
        "candidates": candidates,
    }, None


def check_destination(
    url, allow_loopback_for_self_test, timeout, resolver=None
):
    """Return the destination-validation error, or ``None`` when allowed."""

    _target, error = prepare_destination(
        url,
        allow_loopback_for_self_test,
        timeout,
        resolver=resolver,
    )
    return error


def ensure_peer_address(expected_address, peer_address):
    """Require the actual connected peer to equal the validated address."""

    try:
        expected = ipaddress.ip_address(
            str(expected_address).split("%", 1)[0]
        )
        actual = ipaddress.ip_address(str(peer_address).split("%", 1)[0])
    except ValueError as exc:
        raise PeerAddressMismatch(
            "Could not compare validated and connected addresses: %s"
            % short_text(exc)
        ) from exc

    if expected != actual:
        raise PeerAddressMismatch(
            "Connected peer %s does not match validated address %s"
            % (actual, expected)
        )


class RedirectResolver:
    """Resolve one URL with an explicit, bounded redirect chain."""

    def __init__(
        self,
        max_redirects=MAX_REDIRECTS_DEFAULT,
        connect_timeout=CONNECT_TIMEOUT_DEFAULT,
        read_timeout=READ_TIMEOUT_DEFAULT,
        max_body_bytes=MAX_BODY_BYTES,
        allow_loopback_for_self_test=False,
        user_agent=USER_AGENT,
        dns_resolver=None,
    ):
        self.max_redirects = max_redirects
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_body_bytes = max_body_bytes
        self.allow_loopback_for_self_test = allow_loopback_for_self_test
        self.user_agent = user_agent
        self.dns_resolver = dns_resolver
        self.ssl_context = ssl.create_default_context()

    @staticmethod
    def map_exception(exc, phase):
        """Map a transport exception to a classification and error type."""

        if isinstance(exc, (socket.timeout, TimeoutError)):
            return {
                "classification": "TIMEOUT",
                "error_type": "%s_timeout" % phase,
                "message": short_text(exc),
            }

        if isinstance(exc, PeerAddressMismatch):
            return {
                "classification": "BLOCKED_TARGET",
                "error_type": "peer_address_mismatch",
                "message": short_text(exc),
            }

        if isinstance(exc, socket.gaierror):
            return {
                "classification": "DNS_FAILURE",
                "error_type": "dns_failure",
                "message": short_text(exc),
            }

        if isinstance(exc, http.client.InvalidURL):
            return {
                "classification": "INVALID_URL",
                "error_type": "invalid_url",
                "message": short_text(exc),
            }

        if isinstance(exc, ssl.SSLCertVerificationError):
            return {
                "classification": "TLS_ERROR",
                "error_type": "tls_certificate_error",
                "message": short_text(exc),
            }

        if isinstance(exc, ssl.SSLError):
            return {
                "classification": "TLS_ERROR",
                "error_type": "tls_error",
                "message": short_text(exc),
            }

        if isinstance(exc, http.client.RemoteDisconnected):
            return {
                "classification": "CONNECTION_ERROR",
                "error_type": "remote_disconnected",
                "message": short_text(exc),
            }

        if isinstance(exc, ConnectionRefusedError):
            return {
                "classification": "CONNECTION_ERROR",
                "error_type": "connection_refused",
                "message": short_text(exc),
            }

        if isinstance(exc, ConnectionResetError):
            return {
                "classification": "CONNECTION_ERROR",
                "error_type": "connection_reset",
                "message": short_text(exc),
            }

        if isinstance(exc, (ConnectionError, http.client.HTTPException, OSError)):
            return {
                "classification": "CONNECTION_ERROR",
                "error_type": "connection_error",
                "message": short_text(exc),
            }

        return {
            "classification": "TRANSIENT_FAILURE",
            "error_type": "unknown_error",
            "message": short_text(exc),
        }

    def _open_validated_socket(self, target, timeout):
        """Connect directly to a validated address, never a host name.

        TCP connection attempts across all validated addresses share one
        deadline.  The actual peer address returned by the kernel must equal
        the address that was validated before the socket was opened.
        """

        deadline = time.monotonic() + timeout
        candidates = target["candidates"]
        last_error = None

        for index, candidate in enumerate(candidates):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if last_error is not None:
                    raise last_error
                raise socket.timeout(
                    "Connection attempts exceeded %.1fs" % timeout
                )

            attempts_left = len(candidates) - index
            attempt_timeout = max(0.001, remaining / attempts_left)
            sock = None

            try:
                sock = socket.socket(
                    candidate["family"],
                    candidate["socktype"],
                    candidate["proto"],
                )
                sock.settimeout(attempt_timeout)
                sock.connect(candidate["sockaddr"])
                peer_address = sock.getpeername()[0]
                ensure_peer_address(candidate["address"], peer_address)
                sock.settimeout(max(0.001, deadline - time.monotonic()))
                return sock, candidate
            except PeerAddressMismatch:
                if sock is not None:
                    sock.close()
                raise
            except OSError as exc:
                if sock is not None:
                    sock.close()
                last_error = exc

        if last_error is not None:
            raise last_error
        raise socket.timeout("No validated address could be connected")

    def _request_once(self, url, destination):
        """Perform exactly one GET without following redirects.

        The HTTP connection object keeps the original host name, so it is used
        for the ``Host`` header, TLS SNI and certificate verification.  Only
        the socket creation step is replaced so it connects to an address that
        was already resolved and validated for this hop.

        Every ``2xx`` HTML response body (direct or redirected) is inspected
        up to ``max_body_bytes`` so a direct login wall is classified the same
        way as one reached through a redirect.  Bodies of ``204``/``205``,
        non-HTML responses and non-``2xx`` responses are not read.
        """

        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        host = parts.hostname or ""
        port = parts.port or DEFAULT_PORTS[scheme]
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query

        host_header = "[%s]" % host if ":" in host else host
        if port != DEFAULT_PORTS[scheme]:
            host_header += ":%d" % port

        headers = {
            "Host": host_header,
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }

        connection = None
        phase = "connect"
        selection = {}
        validated_address = destination["candidates"][0]["address"]
        peer_address = None

        def create_validated_connection(
            _address, timeout, _source_address
        ):
            sock, candidate = self._open_validated_socket(
                destination, timeout
            )
            selection["candidate"] = candidate
            return sock

        try:
            if scheme == "https":
                connection = http.client.HTTPSConnection(
                    host,
                    port,
                    timeout=self.connect_timeout,
                    context=self.ssl_context,
                )
            else:
                connection = http.client.HTTPConnection(
                    host, port, timeout=self.connect_timeout
                )

            connection._create_connection = create_validated_connection
            connection.connect()

            candidate = selection.get("candidate")
            if candidate is None:
                raise ConnectionError(
                    "Socket creation did not use a validated address"
                )

            validated_address = candidate["address"]
            if connection.sock is None:
                raise ConnectionError(
                    "Connection did not expose a connected socket"
                )

            peer_address = connection.sock.getpeername()[0]
            ensure_peer_address(validated_address, peer_address)
            connection.sock.settimeout(self.read_timeout)

            phase = "send"
            connection.request("GET", target, headers=headers)

            phase = "read"
            response = connection.getresponse()

            status = response.status
            location = response.getheader("Location")
            content_type = response.getheader("Content-Type") or ""
            server = response.getheader("Server") or ""
            body = b""
            body_error = None
            body_inspected = False
            body_truncated = False
            body_timeout = False
            body_read_failed = False

            should_inspect_body = bool(
                200 <= status <= 299
                and status not in (204, 205)
                and "text/html" in content_type.lower()
            )

            if should_inspect_body:
                body_inspected = True
                try:
                    content_length_header = response.getheader("Content-Length")
                    content_length = None
                    if (
                        content_length_header
                        and content_length_header.strip().isdigit()
                    ):
                        content_length = int(content_length_header)

                    body = response.read(self.max_body_bytes)

                    if content_length is not None:
                        if content_length > self.max_body_bytes:
                            body_truncated = True
                        elif len(body) < content_length:
                            body_truncated = True
                            body_read_failed = True
                            body_error = (
                                "body_read_error: incomplete HTML body "
                                "(%d of %d bytes)"
                                % (len(body), content_length)
                            )

                    if len(body) >= self.max_body_bytes:
                        body_truncated = True
                except (socket.timeout, TimeoutError) as exc:
                    body_timeout = True
                    body_error = "body_read_timeout: %s" % short_text(exc)
                except (OSError, http.client.HTTPException) as exc:
                    body_read_failed = True
                    body_error = "body_read_error: %s" % short_text(exc)

            return {
                "status": status,
                "location": location,
                "content_type": content_type,
                "server": server,
                "login_body": looks_like_login_body(body),
                "body_error": body_error,
                "body_inspected": body_inspected,
                "body_truncated": body_truncated,
                "body_timeout": body_timeout,
                "body_read_failed": body_read_failed,
                "peer_address": peer_address,
                "validated_address": validated_address,
                "host_header": host_header,
            }

        except Exception as exc:  # noqa: BLE001 - mapped explicitly below
            return {
                "exception": exc,
                "phase": phase,
                "peer_address": peer_address,
                "validated_address": validated_address,
                "host_header": host_header,
            }

        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def resolve(self, url, label=None):
        """Resolve one URL and return a JSON-serialisable result."""

        started = time.monotonic()
        redirects = []
        current_peer_address = None
        current_validated_address = None
        current_host_header = None
        current_body_inspected = False
        current_body_truncated = False
        current_body_timeout = False

        def finish(
            classification,
            final_url=None,
            http_status=None,
            request_count=0,
            reason=None,
            error_type=None,
            auth_evidence=None,
            server=None,
            content_type=None,
            body_error=None,
            body_inspected=False,
            body_truncated=False,
            body_timeout=False,
            peer_address=None,
            validated_address=None,
            host_header=None,
        ):
            if peer_address is None:
                peer_address = current_peer_address
            if validated_address is None:
                validated_address = current_validated_address
            if host_header is None:
                host_header = current_host_header
            if not body_inspected:
                body_inspected = current_body_inspected
            if not body_truncated:
                body_truncated = current_body_truncated
            if not body_timeout:
                body_timeout = current_body_timeout

            redirect_target = None
            for item in reversed(redirects):
                if item.get("to_url"):
                    redirect_target = item["to_url"]
                    break

            return {
                "label": label,
                "original_url": url,
                "classification": classification,
                "final_url": final_url,
                "redirect_target": redirect_target,
                "http_status": http_status,
                "request_count": request_count,
                "redirect_count": len(redirects),
                "redirects": list(redirects),
                "error_type": error_type,
                "message": reason,
                "auth_wall_evidence": auth_evidence,
                "server": server,
                "content_type": content_type,
                "body_inspected": body_inspected,
                "body_truncated": body_truncated,
                "body_read_timeout": body_timeout,
                "body_read_error": body_error,
                "peer_address": peer_address,
                "validated_address": validated_address,
                "host_header": host_header,
                "elapsed_ms": int(round((time.monotonic() - started) * 1000)),
                "observed_at": utc_now(),
            }

        normalized, error = validate_url(url)

        if error:
            return finish(
                error["classification"],
                final_url=None,
                request_count=0,
                reason=error["message"],
                error_type=error["error_type"],
            )

        current = normalized
        visited = {loop_key(current)}
        request_count = 0
        max_requests = self.max_redirects + 1
        last_url = None
        last_status = None
        last_server = None
        last_content_type = None
        last_body_error = None

        while True:
            if request_count >= max_requests:
                return finish(
                    "REDIRECT_LIMIT",
                    final_url=current,
                    http_status=last_status,
                    request_count=request_count,
                    reason="Request budget of %d exhausted" % max_requests,
                    error_type="redirect_limit",
                    server=last_server,
                    content_type=last_content_type,
                    body_error=last_body_error,
                )

            destination, destination_error = prepare_destination(
                current,
                self.allow_loopback_for_self_test,
                self.connect_timeout,
                resolver=self.dns_resolver,
            )

            if destination_error:
                if request_count == 0:
                    return finish(
                        destination_error["classification"],
                        final_url=None,
                        request_count=0,
                        reason=destination_error["message"],
                        error_type=destination_error["error_type"],
                    )

                return finish(
                    destination_error["classification"],
                    final_url=last_url,
                    http_status=last_status,
                    request_count=request_count,
                    reason="Redirect destination refused: %s"
                    % destination_error["message"],
                    error_type=destination_error["error_type"],
                    server=last_server,
                    content_type=last_content_type,
                    body_error=last_body_error,
                )

            request_count += 1
            response = self._request_once(current, destination)

            if "exception" in response:
                mapping = self.map_exception(
                    response["exception"], response["phase"]
                )
                return finish(
                    mapping["classification"],
                    final_url=current,
                    request_count=request_count,
                    reason=mapping["message"],
                    error_type=mapping["error_type"],
                    server=last_server,
                    content_type=last_content_type,
                    body_error=last_body_error,
                    peer_address=response.get("peer_address"),
                    validated_address=response.get("validated_address"),
                    host_header=response.get("host_header"),
                )

            status = response["status"]
            server = response["server"]
            content_type = response["content_type"]
            body_error = response["body_error"]
            current_peer_address = response.get("peer_address")
            current_validated_address = response.get("validated_address")
            current_host_header = response.get("host_header")
            current_body_inspected = response.get("body_inspected", False)
            current_body_truncated = response.get("body_truncated", False)
            current_body_timeout = response.get("body_timeout", False)
            last_url = current
            last_status = status
            last_server = server
            last_content_type = content_type
            last_body_error = body_error

            if status in FOLLOW_REDIRECT_STATUSES:
                location = response["location"]
                entry = {
                    "from_url": current,
                    "status": status,
                    "location": location,
                    "to_url": None,
                }
                redirects.append(entry)

                if location is None or not location.strip():
                    return finish(
                        "HTTP_ERROR",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Redirect status %d without a Location header"
                            % status
                        ),
                        error_type="missing_location",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                raw_location = location.strip()

                try:
                    next_url = urljoin(current, raw_location)
                except ValueError as exc:
                    return finish(
                        "INVALID_URL",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason="Malformed Location header: %s"
                        % short_text(exc),
                        error_type="malformed_location",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                next_normalized, next_error = validate_url(next_url)

                if next_error:
                    entry["to_url"] = next_url
                    return finish(
                        next_error["classification"],
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason="Invalid redirect destination: %s"
                        % next_error["message"],
                        error_type=next_error["error_type"],
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                entry["to_url"] = next_normalized

                auth_reason = login_url_reason(next_normalized)
                if auth_reason:
                    return finish(
                        "AUTH_WALL",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Redirect destination looks like a login wall "
                            "(%s)" % auth_reason
                        ),
                        error_type="login_redirect",
                        auth_evidence=auth_reason,
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                next_key = loop_key(next_normalized)

                if next_key in visited:
                    return finish(
                        "REDIRECT_LOOP",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Redirect repeated an already-visited URL: %s"
                            % next_normalized
                        ),
                        error_type="redirect_loop",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                if len(redirects) > self.max_redirects:
                    return finish(
                        "REDIRECT_LIMIT",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Redirect budget of %d exceeded"
                            % self.max_redirects
                        ),
                        error_type="redirect_limit",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                visited.add(next_key)
                current = next_normalized
                continue

            if status in AUTH_STATUSES:
                return finish(
                    "AUTH_WALL",
                    final_url=current,
                    http_status=status,
                    request_count=request_count,
                    reason="HTTP %d authentication/access denial" % status,
                    error_type="http_%d" % status,
                    auth_evidence="HTTP %d response" % status,
                    server=server,
                    content_type=content_type,
                    body_error=body_error,
                )

            if 200 <= status <= 299:
                if response["body_timeout"]:
                    return finish(
                        "TIMEOUT",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Timed out reading the HTML body needed for "
                            "login-wall classification"
                        ),
                        error_type="body_read_timeout",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                if response["body_read_failed"]:
                    return finish(
                        "CONNECTION_ERROR",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "Failed to read the HTML body needed for "
                            "login-wall classification"
                        ),
                        error_type="body_read_error",
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                if response["login_body"]:
                    return finish(
                        "AUTH_WALL",
                        final_url=current,
                        http_status=status,
                        request_count=request_count,
                        reason=(
                            "HTML page contains an explicit login form"
                        ),
                        error_type="login_page",
                        auth_evidence=(
                            "password input field on HTML page"
                        ),
                        server=server,
                        content_type=content_type,
                        body_error=body_error,
                    )

                classification = "MOVED" if redirects else "OK"
                if redirects:
                    reason = "Redirect chain ended at HTTP %d" % status
                else:
                    reason = "HTTP %d success" % status

                return finish(
                    classification,
                    final_url=current,
                    http_status=status,
                    request_count=request_count,
                    reason=reason,
                    server=server,
                    content_type=content_type,
                    body_error=body_error,
                )

            if status in TRANSIENT_HTTP_STATUSES or 500 <= status <= 599:
                return finish(
                    "TRANSIENT_FAILURE",
                    final_url=current,
                    http_status=status,
                    request_count=request_count,
                    reason="Temporary HTTP status %d" % status,
                    error_type="http_%d" % status,
                    server=server,
                    content_type=content_type,
                    body_error=body_error,
                )

            if status >= 400:
                error_type = "http_%d" % status
            else:
                error_type = "unexpected_status_%d" % status

            return finish(
                "HTTP_ERROR",
                final_url=current,
                http_status=status,
                request_count=request_count,
                reason="HTTP status %d" % status,
                error_type=error_type,
                server=server,
                content_type=content_type,
                body_error=body_error,
            )


class MockServerHandler(BaseHTTPRequestHandler):
    """Deterministic local HTTP fixtures for the offline self-test."""

    protocol_version = "HTTP/1.0"
    server_version = "R02T032Mock/1.0"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        path = urlsplit(self.path).path

        if path.startswith("/status/"):
            try:
                status = int(path.rsplit("/", 1)[1])
                if not 100 <= status <= 599:
                    raise ValueError("status outside 100-599")
            except ValueError:
                self._send(400, b"bad status fixture")
                return
            self._send(status, b"status fixture")
        elif path == "/ok":
            self._send(200, b"ok")
        elif path == "/html-ok":
            self._send(
                200,
                b"<html><head><title>Fixture</title></head>"
                b"<body>ordinary HTML</body></html>",
                content_type="text/html; charset=utf-8",
            )
        elif path == "/docs-html":
            self._send(
                200,
                b"<html><head><title>API documentation</title></head>"
                b"<body><h1>Documentation</h1>"
                b"<form><input type='text' name='q'></form>"
                b"</body></html>",
                content_type="text/html; charset=utf-8",
            )
        elif path == "/ok204":
            self._send(204)
        elif path == "/redirect301":
            self._redirect(301, "/ok")
        elif path == "/redirect302":
            self._redirect(302, "/ok")
        elif path == "/redirect303":
            self._redirect(303, "/ok")
        elif path == "/redirect307":
            self._redirect(307, "/ok")
        elif path == "/redirect308":
            self._redirect(308, "/ok")
        elif path == "/relative":
            self._redirect(302, "ok")
        elif path == "/multi1":
            self._redirect(302, "/multi2")
        elif path == "/multi2":
            self._redirect(301, "/ok")
        elif path.startswith("/chain/"):
            try:
                remaining = int(path.rsplit("/", 1)[1])
            except ValueError:
                self._send(400, b"bad chain value")
                return
            if remaining > 0:
                self._redirect(302, "/chain/%d" % (remaining - 1))
            else:
                self._send(200, b"chain-end")
        elif path == "/loop-a":
            self._redirect(302, "/loop-b")
        elif path == "/loop-b":
            self._redirect(302, "/loop-a")
        elif path == "/self-loop":
            self._redirect(302, "/self-loop")
        elif path == "/missing-location":
            self._redirect(302, None)
        elif path == "/malformed-location":
            self._redirect(302, "http://[::1")
        elif path == "/unsupported-scheme":
            self._redirect(302, "ftp://example.com/file")
        elif path == "/login-redirect":
            self._redirect(302, "/login?next=/")
        elif path == "/login":
            self._send(
                200,
                b"<html><head><title>Sign in</title></head><body>"
                b"<form><input type='password' name='password'>"
                b"</form></body></html>",
                content_type="text/html; charset=utf-8",
            )
        elif path == "/identity-provider":
            self._redirect(
                302,
                "https://accounts.google.com/o/oauth2/v2/auth?client_id=fixture",
            )
        elif path == "/portal-redirect":
            self._redirect(302, "/portal")
        elif path == "/portal":
            self._send(
                200,
                b"<html><head><title>Account portal</title></head><body>"
                b"<form><input type='password' name='password'>"
                b"</form></body></html>",
                content_type="text/html; charset=utf-8",
            )
        elif path == "/redirect-query":
            self._redirect(302, "/ok?from=redirect")
        elif path == "/redirect-204":
            self._redirect(302, "/ok204")
        elif path == "/redirect-html-ok":
            self._redirect(302, "/html-ok")
        elif path == "/redirect-404":
            self._redirect(302, "/404")
        elif path == "/redirect-401":
            self._redirect(302, "/401")
        elif path == "/redirect-403":
            self._redirect(302, "/403")
        elif path == "/redirect-500":
            self._redirect(302, "/status/500")
        elif path == "/redirect-private":
            self._redirect(302, "http://10.0.0.1/")
        elif path == "/slow-body-redirect":
            self._redirect(302, "/slow-body")
        elif path == "/slow-body":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", "4096")
            self.end_headers()
            try:
                self.wfile.write(b"<html><body>")
                self.wfile.flush()
                time.sleep(1.2)
                self.wfile.write(b"slow body</body></html>")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif path == "/truncated-body":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", "4096")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(b"<html><body>partial")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
        elif path == "/401":
            self._send(401, b"unauthorized")
        elif path == "/403":
            self._send(403, b"forbidden")
        elif path == "/404":
            self._send(404, b"not found")
        elif path == "/429":
            self._send(429, b"too many requests")
        elif path == "/500":
            self._send(500, b"server error")
        elif path == "/not-modified":
            self._send(304)
        elif path == "/timeout":
            time.sleep(1.2)
            try:
                self._send(200, b"late")
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif path == "/close":
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.connection.close()
            except OSError:
                pass
        else:
            self._send(404, b"unknown fixture")

    def _send(self, status, body=b"", headers=None, content_type=None):
        self.send_response(status)
        if content_type:
            self.send_header("Content-Type", content_type)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if status not in (204, 304):
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and status not in (204, 304):
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _redirect(self, status, location):
        headers = {}
        if location is not None:
            headers["Location"] = location
        self._send(status, headers=headers)


def start_mock_server():
    """Start the local fixture server and return (server, base_url)."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), MockServerHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, "http://%s:%d" % (host, port)


SELF_TEST_RESOLVER_DEFAULTS = {
    "max_redirects": SELF_TEST_MAX_REDIRECTS,
    "connect_timeout": 1.0,
    "read_timeout": 0.5,
    "max_body_bytes": 4096,
    "allow_loopback_for_self_test": True,
}


def build_self_test_cases(base):
    """Fixed offline cases and their expected observations."""

    return [
        {
            "name": "direct-200",
            "url": base + "/ok",
            "expect": {
                "classification": "OK",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/ok",
                "error_type": None,
                "auth_evidence_present": False,
            },
        },
        {
            "name": "direct-204",
            "url": base + "/ok204",
            "expect": {
                "classification": "OK",
                "http_status": 204,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/ok204",
            },
        },
        {
            "name": "direct-201-created",
            "url": base + "/status/201",
            "expect": {
                "classification": "OK",
                "http_status": 201,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/status/201",
            },
        },
        {
            "name": "direct-206-partial",
            "url": base + "/status/206",
            "expect": {
                "classification": "OK",
                "http_status": 206,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/status/206",
            },
        },
        {
            "name": "direct-non-html-not-inspected",
            "url": base + "/ok",
            "expect": {
                "classification": "OK",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/ok",
                "body_inspected": False,
                "body_read_timeout": False,
            },
        },
        {
            "name": "direct-login-html",
            "url": base + "/portal",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/portal",
                "error_type": "login_page",
                "auth_evidence_contains": "password",
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "direct-ordinary-html",
            "url": base + "/html-ok",
            "expect": {
                "classification": "OK",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/html-ok",
                "auth_evidence_present": False,
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "direct-html-without-login-indicators",
            "url": base + "/docs-html",
            "expect": {
                "classification": "OK",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/docs-html",
                "auth_evidence_present": False,
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "direct-html-body-timeout",
            "url": base + "/slow-body",
            "expect": {
                "classification": "TIMEOUT",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/slow-body",
                "error_type": "body_read_timeout",
                "body_inspected": True,
                "body_read_timeout": True,
            },
        },
        {
            "name": "direct-html-body-read-error",
            "url": base + "/truncated-body",
            "expect": {
                "classification": "CONNECTION_ERROR",
                "http_status": 200,
                "request_count": 1,
                "redirect_count": 0,
                "final_path": "/truncated-body",
                "error_type": "body_read_error",
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "redirect-301",
            "url": base + "/redirect301",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "redirect_statuses": [301],
                "final_path": "/ok",
            },
        },
        {
            "name": "redirect-302",
            "url": base + "/redirect302",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "redirect_statuses": [302],
                "final_path": "/ok",
            },
        },
        {
            "name": "redirect-303",
            "url": base + "/redirect303",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "redirect_statuses": [303],
                "final_path": "/ok",
            },
        },
        {
            "name": "redirect-307",
            "url": base + "/redirect307",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "redirect_statuses": [307],
                "final_path": "/ok",
            },
        },
        {
            "name": "redirect-308",
            "url": base + "/redirect308",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "redirect_statuses": [308],
                "final_path": "/ok",
            },
        },
        {
            "name": "relative-redirect",
            "url": base + "/relative",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "last_location": "ok",
                "final_path": "/ok",
            },
        },
        {
            "name": "multiple-redirects",
            "url": base + "/multi1",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 3,
                "redirect_count": 2,
                "redirect_statuses": [302, 301],
                "final_path": "/ok",
            },
        },
        {
            "name": "redirect-query",
            "url": base + "/redirect-query",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/ok",
                "final_query": "from=redirect",
            },
        },
        {
            "name": "redirect-204",
            "url": base + "/redirect-204",
            "expect": {
                "classification": "MOVED",
                "http_status": 204,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/ok204",
            },
        },
        {
            "name": "within-budget",
            "url": base + "/chain/2",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 3,
                "redirect_count": 2,
                "final_path": "/chain/0",
            },
        },
        {
            "name": "budget-exhausted",
            "url": base + "/chain/3",
            "expect": {
                "classification": "REDIRECT_LIMIT",
                "http_status": 302,
                "request_count": 3,
                "redirect_count": 3,
                "final_path": "/chain/1",
                "redirect_target_path": "/chain/0",
                "error_type": "redirect_limit",
            },
        },
        {
            "name": "redirect-loop",
            "url": base + "/loop-a",
            "expect": {
                "classification": "REDIRECT_LOOP",
                "http_status": 302,
                "request_count": 2,
                "redirect_count": 2,
                "final_path": "/loop-b",
                "redirect_target_path": "/loop-a",
                "error_type": "redirect_loop",
            },
        },
        {
            "name": "self-loop",
            "url": base + "/self-loop",
            "expect": {
                "classification": "REDIRECT_LOOP",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/self-loop",
                "redirect_target_path": "/self-loop",
            },
        },
        {
            "name": "missing-location",
            "url": base + "/missing-location",
            "expect": {
                "classification": "HTTP_ERROR",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/missing-location",
                "last_location": None,
                "error_type": "missing_location",
            },
        },
        {
            "name": "malformed-location",
            "url": base + "/malformed-location",
            "expect": {
                "classification": "INVALID_URL",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/malformed-location",
                "last_location": "http://[::1",
                "error_type": "malformed_location",
            },
        },
        {
            "name": "unsupported-scheme-redirect",
            "url": base + "/unsupported-scheme",
            "expect": {
                "classification": "UNSUPPORTED_SCHEME",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/unsupported-scheme",
                "error_type": "unsupported_scheme",
            },
        },
        {
            "name": "http-401",
            "url": base + "/401",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 401,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_401",
                "auth_evidence_contains": "401",
            },
        },
        {
            "name": "http-403",
            "url": base + "/403",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 403,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_403",
                "auth_evidence_contains": "403",
            },
        },
        {
            "name": "login-path-redirect",
            "url": base + "/login-redirect",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/login-redirect",
                "redirect_target_path": "/login",
                "error_type": "login_redirect",
                "auth_evidence_contains": "login path",
            },
        },
        {
            "name": "identity-provider-redirect",
            "url": base + "/identity-provider",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/identity-provider",
                "redirect_target_path": "/o/oauth2/v2/auth",
                "error_type": "login_redirect",
                "auth_evidence_contains": "identity provider",
            },
        },
        {
            "name": "login-page-body",
            "url": base + "/portal-redirect",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/portal",
                "error_type": "login_page",
                "auth_evidence_contains": "password",
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "redirect-html-ok",
            "url": base + "/redirect-html-ok",
            "expect": {
                "classification": "MOVED",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/html-ok",
                "auth_evidence_present": False,
                "body_inspected": True,
                "body_read_timeout": False,
            },
        },
        {
            "name": "redirect-404",
            "url": base + "/redirect-404",
            "expect": {
                "classification": "HTTP_ERROR",
                "http_status": 404,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/404",
                "error_type": "http_404",
            },
        },
        {
            "name": "redirect-401",
            "url": base + "/redirect-401",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 401,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/401",
                "error_type": "http_401",
            },
        },
        {
            "name": "http-404",
            "url": base + "/404",
            "expect": {
                "classification": "HTTP_ERROR",
                "http_status": 404,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_404",
            },
        },
        {
            "name": "http-500",
            "url": base + "/500",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 500,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_500",
            },
        },
        {
            "name": "http-429",
            "url": base + "/429",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 429,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_429",
            },
        },
        {
            "name": "http-408",
            "url": base + "/status/408",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 408,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_408",
            },
        },
        {
            "name": "http-425",
            "url": base + "/status/425",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 425,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_425",
            },
        },
        {
            "name": "http-503",
            "url": base + "/status/503",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 503,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "http_503",
            },
        },
        {
            "name": "redirect-403",
            "url": base + "/redirect-403",
            "expect": {
                "classification": "AUTH_WALL",
                "http_status": 403,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/403",
                "error_type": "http_403",
                "redirect_statuses": [302],
            },
        },
        {
            "name": "redirect-500",
            "url": base + "/redirect-500",
            "expect": {
                "classification": "TRANSIENT_FAILURE",
                "http_status": 500,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/status/500",
                "error_type": "http_500",
                "redirect_statuses": [302],
            },
        },
        {
            "name": "unexpected-300",
            "url": base + "/status/300",
            "expect": {
                "classification": "HTTP_ERROR",
                "http_status": 300,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "unexpected_status_300",
            },
        },
        {
            "name": "unexpected-304",
            "url": base + "/not-modified",
            "expect": {
                "classification": "HTTP_ERROR",
                "http_status": 304,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "unexpected_status_304",
            },
        },
        {
            "name": "redirected-html-body-timeout",
            "url": base + "/slow-body-redirect",
            "expect": {
                "classification": "TIMEOUT",
                "http_status": 200,
                "request_count": 2,
                "redirect_count": 1,
                "final_path": "/slow-body",
                "error_type": "body_read_timeout",
                "body_inspected": True,
                "body_read_timeout": True,
            },
        },
        {
            "name": "redirect-private-blocked",
            "url": base + "/redirect-private",
            "expect": {
                "classification": "BLOCKED_TARGET",
                "http_status": 302,
                "request_count": 1,
                "redirect_count": 1,
                "final_path": "/redirect-private",
                "redirect_target_path": "/",
                "error_type": "blocked_destination",
            },
        },
        {
            "name": "read-timeout",
            "url": base + "/timeout",
            "expect": {
                "classification": "TIMEOUT",
                "http_status": None,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "read_timeout",
            },
        },
        {
            "name": "connection-closed",
            "url": base + "/close",
            "expect": {
                "classification": "CONNECTION_ERROR",
                "http_status": None,
                "request_count": 1,
                "redirect_count": 0,
                "error_type": "remote_disconnected",
            },
        },
        {
            "name": "dns-failure",
            "url": "http://r02-t032-does-not-exist.invalid/",
            "resolver_options": {"connect_timeout": 2.0},
            "expect": {
                "classification": "DNS_FAILURE",
                "http_status": None,
                "request_count": 0,
                "redirect_count": 0,
                "final_path": None,
                "error_type": "dns_failure",
            },
        },
        {
            "name": "invalid-url",
            "url": "not-a-url",
            "expect": {
                "classification": "INVALID_URL",
                "http_status": None,
                "request_count": 0,
                "redirect_count": 0,
                "final_path": None,
                "error_type": "invalid_url",
            },
        },
        {
            "name": "credentials-in-url",
            "url": "http://user:pass@example.com/",
            "expect": {
                "classification": "INVALID_URL",
                "http_status": None,
                "request_count": 0,
                "redirect_count": 0,
                "error_type": "credentials_not_allowed",
            },
        },
        {
            "name": "unsupported-scheme-input",
            "url": "ftp://example.com/file",
            "expect": {
                "classification": "UNSUPPORTED_SCHEME",
                "http_status": None,
                "request_count": 0,
                "redirect_count": 0,
                "error_type": "unsupported_scheme",
            },
        },
        {
            "name": "blocked-loopback",
            "url": base + "/ok",
            "resolver_options": {"allow_loopback_for_self_test": False},
            "expect": {
                "classification": "BLOCKED_TARGET",
                "http_status": None,
                "request_count": 0,
                "redirect_count": 0,
                "final_path": None,
                "error_type": "blocked_destination",
            },
        },
        {
            "name": "blocked-private-10",
            "url": "http://10.0.0.1/",
            "resolver_options": {"allow_loopback_for_self_test": False},
            "expect": {
                "classification": "BLOCKED_TARGET",
                "request_count": 0,
                "final_path": None,
                "error_type": "blocked_destination",
            },
        },
        {
            "name": "blocked-link-local",
            "url": "http://169.254.169.254/latest/meta-data",
            "resolver_options": {"allow_loopback_for_self_test": False},
            "expect": {
                "classification": "BLOCKED_TARGET",
                "request_count": 0,
                "error_type": "blocked_destination",
            },
        },
        {
            "name": "blocked-ipv6-loopback",
            "url": "http://[::1]/",
            "resolver_options": {"allow_loopback_for_self_test": False},
            "expect": {
                "classification": "BLOCKED_TARGET",
                "request_count": 0,
                "error_type": "blocked_destination",
            },
        },
        {
            "name": "blocked-localhost",
            "url": "http://localhost/",
            "resolver_options": {"allow_loopback_for_self_test": False},
            "expect": {
                "classification": "BLOCKED_TARGET",
                "request_count": 0,
                "error_type": "blocked_destination",
            },
        },
    ]


def derive_actual(result, key):
    """Derive a comparable field from a resolver result."""

    if key == "redirect_count":
        return len(result.get("redirects") or [])

    if key == "final_path":
        final_url = result.get("final_url")
        return urlsplit(final_url).path if final_url else None

    if key == "final_query":
        final_url = result.get("final_url")
        return urlsplit(final_url).query if final_url else None

    if key == "redirect_target_path":
        target = result.get("redirect_target")
        return urlsplit(target).path if target else None

    if key == "redirect_statuses":
        return [item["status"] for item in result.get("redirects") or []]

    if key == "last_location":
        redirects = result.get("redirects") or []
        return redirects[-1].get("location") if redirects else None

    if key == "auth_evidence_present":
        return bool(result.get("auth_wall_evidence"))

    return result.get(key)


def compare_case(case, result):
    """Return a list of human-readable mismatches for one case."""

    failures = []

    for key, expected in case["expect"].items():
        if key == "auth_evidence_contains":
            evidence = (result.get("auth_wall_evidence") or "").lower()
            passed = expected.lower() in evidence
            if not passed:
                failures.append(
                    "%s: expected evidence containing %r, got %r"
                    % (key, expected, result.get("auth_wall_evidence"))
                )
            continue

        actual = derive_actual(result, key)
        if actual != expected:
            failures.append(
                "%s: expected %r, got %r" % (key, expected, actual)
            )

    return failures


def run_resolver_case(case):
    """Run one offline case and package its result."""

    options = dict(SELF_TEST_RESOLVER_DEFAULTS)
    options.update(case.get("resolver_options") or {})
    resolver = RedirectResolver(**options)
    result = resolver.resolve(case["url"], label=case["name"])
    failures = compare_case(case, result)

    return {
        "name": case["name"],
        "passed": not failures,
        "expected": case["expect"],
        "actual": result,
        "failures": failures,
    }


def find_readme_rows():
    """Locate each assigned row and its active level-3 category."""

    rows = {target["name"]: [] for target in TARGETS}

    if not README_PATH.exists():
        return rows

    lines = README_PATH.read_text(encoding="utf-8").splitlines()

    for target in TARGETS:
        needle = "[%s](%s)" % (target["name"], target["url"])
        for line_number, line in enumerate(lines, start=1):
            if needle not in line:
                continue

            category = None
            for prior in range(line_number - 2, -1, -1):
                match = re.match(r"^\s{0,3}###\s+(.+?)\s*$", lines[prior])
                if match:
                    category = match.group(1).strip()
                    break

            cells = [
                cell.strip()
                for cell in line.strip().strip("|").split("|")
            ]
            rows[target["name"]].append(
                {
                    "line": line_number,
                    "category": category,
                    "row": line,
                    "cells": cells,
                }
            )

    return rows


def make_check(name, failures, details=None):
    """Build a consistency-check record."""

    return {
        "name": name,
        "passed": not failures,
        "failures": failures,
        "details": details or [],
    }


def check_readme_rows():
    """Verify the three assigned rows and their metadata are untouched."""

    rows = find_readme_rows()
    failures = []
    details = []

    for target in TARGETS:
        matches = rows[target["name"]]

        if len(matches) != 1:
            failures.append(
                "%s: expected exactly one README row, found %d"
                % (target["name"], len(matches))
            )
            continue

        match = matches[0]
        cells = match["cells"]

        if match["category"] != "Food & Drink":
            failures.append(
                "%s: expected category 'Food & Drink', got %r"
                % (target["name"], match["category"])
            )

        if len(cells) != 5:
            failures.append(
                "%s: expected 5 table cells, got %d"
                % (target["name"], len(cells))
            )
            continue

        expected_cells = {
            "description": target["description"],
            "auth": target["auth"],
            "https": target["https"],
            "cors": target["cors"],
        }
        actual_cells = {
            "description": cells[1],
            "auth": cells[2],
            "https": cells[3],
            "cors": cells[4],
        }

        for key, expected in expected_cells.items():
            if actual_cells[key] != expected:
                failures.append(
                    "%s: %s expected %r, got %r"
                    % (
                        target["name"],
                        key,
                        expected,
                        actual_cells[key],
                    )
                )

        details.append(
            "%s: line %d, category %s"
            % (target["name"], match["line"], match["category"])
        )

    return make_check("readme-food-drink-rows", failures, details)


def check_target_scope():
    """Prove the checker is fixed to the three assigned entries."""

    failures = []
    expected_names = ["BaconMockup", "CalorieNinjas", "Chomp"]
    expected_urls = [
        "https://baconmockup.com/",
        "https://calorieninjas.com/api",
        "https://chompthis.com/api/",
    ]

    if [target["name"] for target in TARGETS] != expected_names:
        failures.append("Target names changed")
    if [target["url"] for target in TARGETS] != expected_urls:
        failures.append("Target URLs changed")
    if len(TARGETS) != 3:
        failures.append("Target list must contain exactly three entries")

    for target in TARGETS:
        if not target["url"].startswith("https://"):
            failures.append(
                "%s: assigned URL is not HTTPS" % target["name"]
            )
        normalized, error = validate_url(target["url"])
        if error:
            failures.append(
                "%s: target URL invalid: %s"
                % (target["name"], error["message"])
            )
        elif normalized != target["url"]:
            failures.append(
                "%s: normalized URL %r differs from assigned URL %r"
                % (target["name"], normalized, target["url"])
            )

    return make_check("fixed-target-scope", failures)


def check_login_heuristics():
    """Exercise positive and negative login/identity-provider detection."""

    positives = [
        "https://example.com/login",
        "https://example.com/sign-in?next=/",
        "https://example.com/log_in?next=/",
        "https://example.com/users/sign_in",
        "https://example.com/oauth2/authorize?client_id=x",
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://login.microsoftonline.com/tenant/oauth2/v2.0/authorize",
        "https://example.okta.com/login",
        "https://example.auth0.com/authorize",
        "https://sso.example.com/",
    ]
    negatives = [
        "https://example.com/api",
        "https://example.com/login-docs",
        "https://auth0.com/docs",
        "https://example.com/documentation/authentication",
        "https://example.com/oauth",
    ]

    failures = []

    for url in positives:
        if not login_url_reason(url):
            failures.append("expected login/IdP match: %s" % url)

    for url in negatives:
        reason = login_url_reason(url)
        if reason:
            failures.append(
                "unexpected login/IdP match: %s (%s)" % (url, reason)
            )

    return make_check("login-heuristics", failures)


def check_login_body_detection():
    """Exercise conservative HTML login-form detection."""

    password_form = (
        b"<html><body><form>"
        b"<input type='password' name='password'>"
        b"</form></body></html>"
    )
    ordinary_html = (
        b"<html><head><title>API documentation</title></head>"
        b"<body>Endpoints and examples</body></html>"
    )
    title_only_form = (
        b"<html><head><title>Sign in</title></head>"
        b"<body><form></form></body></html>"
    )

    failures = []

    if not looks_like_login_body(password_form):
        failures.append("password form was not detected")
    if looks_like_login_body(ordinary_html):
        failures.append("ordinary HTML was misclassified as a login page")
    if not looks_like_login_body(title_only_form):
        failures.append("sign-in title with a form was not detected")
    if looks_like_login_body(b""):
        failures.append("empty body was misclassified")

    return make_check("login-body-detection", failures)


def check_exception_mapping():
    """Exercise transport exception mapping without network access."""

    cases = [
        (
            PeerAddressMismatch(
                "connected peer 203.0.113.9 does not match "
                "validated address 203.0.113.10"
            ),
            "connect",
            "BLOCKED_TARGET",
            "peer_address_mismatch",
        ),
        (
            http.client.InvalidURL("invalid request target"),
            "send",
            "INVALID_URL",
            "invalid_url",
        ),
        (
            ssl.SSLCertVerificationError("certificate verify failed"),
            "connect",
            "TLS_ERROR",
            "tls_certificate_error",
        ),
        (
            ssl.SSLError("handshake failed"),
            "connect",
            "TLS_ERROR",
            "tls_error",
        ),
        (
            socket.gaierror(-2, "Name or service not known"),
            "connect",
            "DNS_FAILURE",
            "dns_failure",
        ),
        (
            socket.timeout("timed out"),
            "read",
            "TIMEOUT",
            "read_timeout",
        ),
        (
            ConnectionRefusedError(61, "Connection refused"),
            "connect",
            "CONNECTION_ERROR",
            "connection_refused",
        ),
        (
            OSError("generic socket failure"),
            "send",
            "CONNECTION_ERROR",
            "connection_error",
        ),
        (
            ValueError("unexpected"),
            "read",
            "TRANSIENT_FAILURE",
            "unknown_error",
        ),
    ]

    failures = []

    for exc, phase, classification, error_type in cases:
        mapped = RedirectResolver.map_exception(exc, phase)
        if mapped["classification"] != classification:
            failures.append(
                "%s: expected classification %s, got %s"
                % (
                    type(exc).__name__,
                    classification,
                    mapped["classification"],
                )
            )
        if mapped["error_type"] != error_type:
            failures.append(
                "%s: expected error_type %s, got %s"
                % (type(exc).__name__, error_type, mapped["error_type"])
            )

    return make_check("exception-mapping", failures)


def check_dns_timeout():
    """Prove the caller stops waiting when a resolver call hangs."""

    def slow_resolver(_host, _port, **_kwargs):
        time.sleep(0.4)
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 80),
            )
        ]

    infos, error = resolve_addresses(
        "slow-resolver.r02-t032.test",
        80,
        0.05,
        resolver=slow_resolver,
    )
    failures = []

    if infos is not None:
        failures.append("slow resolver unexpectedly returned addresses")
    if not error:
        failures.append("slow resolver did not produce an error")
    else:
        if error["classification"] != "TIMEOUT":
            failures.append(
                "expected TIMEOUT, got %s" % error["classification"]
            )
        if error["error_type"] != "dns_timeout":
            failures.append(
                "expected error_type dns_timeout, got %s"
                % error["error_type"]
            )
        if "cannot be cancelled" not in error["message"]:
            failures.append(
                "DNS timeout message does not state the cancellation limit"
            )

    return make_check(
        "dns-timeout",
        failures,
        ["caller wait was bounded; resolver thread is not cancellable"],
    )


def check_validated_connect(base):
    """Prove connect uses the validated address without a second lookup."""

    parts = urlsplit(base)
    fixture_port = parts.port
    fake_host = "validated-target.r02-t032.test"
    resolver_calls = []

    def fake_resolver(host, port, **_kwargs):
        resolver_calls.append((host, port))
        if len(resolver_calls) > 1:
            raise OSError("unexpected second DNS resolution")
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", port),
            )
        ]

    resolver = RedirectResolver(
        connect_timeout=1.0,
        read_timeout=0.5,
        max_body_bytes=4096,
        allow_loopback_for_self_test=True,
        dns_resolver=fake_resolver,
    )
    url = "http://%s:%d/ok" % (fake_host, fixture_port)
    result = resolver.resolve(url, label="validated-connect")
    expected_host_header = "%s:%d" % (fake_host, fixture_port)
    failures = []

    if result["classification"] != "OK":
        failures.append(
            "expected OK, got %s (%s)"
            % (result["classification"], result["message"])
        )
    if result["request_count"] != 1:
        failures.append(
            "expected one request, got %d" % result["request_count"]
        )
    if len(resolver_calls) != 1:
        failures.append(
            "expected exactly one DNS resolution, got %d"
            % len(resolver_calls)
        )
    if resolver_calls and resolver_calls[0][0] != fake_host:
        failures.append(
            "resolved unexpected host name: %s" % resolver_calls[0][0]
        )
    if result["validated_address"] != "127.0.0.1":
        failures.append(
            "validated_address was %r" % result["validated_address"]
        )
    if result["peer_address"] != "127.0.0.1":
        failures.append("peer_address was %r" % result["peer_address"])
    if result["host_header"] != expected_host_header:
        failures.append(
            "Host header was %r, expected %r"
            % (result["host_header"], expected_host_header)
        )

    return make_check(
        "validated-connect",
        failures,
        [
            "host name: %s" % fake_host,
            "resolved/validated address: 127.0.0.1",
            "actual peer: %s" % result["peer_address"],
            "Host header: %s" % result["host_header"],
        ],
    )


def check_peer_address_guard():
    """Exercise the connected-peer versus validated-address comparison."""

    failures = []

    try:
        ensure_peer_address("127.0.0.1", "127.0.0.1")
    except PeerAddressMismatch as exc:
        failures.append("matching peer was rejected: %s" % exc)

    try:
        ensure_peer_address("::1", "::1")
    except PeerAddressMismatch as exc:
        failures.append("matching IPv6 peer was rejected: %s" % exc)

    try:
        ensure_peer_address("127.0.0.1", "127.0.0.2")
    except PeerAddressMismatch as exc:
        mapped = RedirectResolver.map_exception(exc, "connect")
        if mapped["classification"] != "BLOCKED_TARGET":
            failures.append(
                "mismatched peer expected BLOCKED_TARGET, got %s"
                % mapped["classification"]
            )
        if mapped["error_type"] != "peer_address_mismatch":
            failures.append(
                "mismatched peer expected peer_address_mismatch, got %s"
                % mapped["error_type"]
            )
    else:
        failures.append("mismatched peer address was accepted")

    return make_check("peer-address-guard", failures)


def check_tls_verification():
    """Ensure certificate and host name verification remain enabled."""

    context = RedirectResolver().ssl_context
    failures = []

    if context.verify_mode != ssl.CERT_REQUIRED:
        failures.append(
            "TLS verify_mode is not CERT_REQUIRED (%r)" % context.verify_mode
        )
    if context.check_hostname is not True:
        failures.append(
            "TLS check_hostname is not enabled (%r)" % context.check_hostname
        )

    return make_check("tls-verification", failures)


def check_ssrf_guard():
    """Verify non-global destinations are refused before requests."""

    blocked = [
        "http://127.0.0.1/",
        "http://localhost/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/",
    ]

    failures = []

    for url in blocked:
        error = check_destination(url, False, 1.0)
        if not error:
            failures.append("expected SSRF block: %s" % url)
        elif error["classification"] != "BLOCKED_TARGET":
            failures.append(
                "%s: expected BLOCKED_TARGET, got %s"
                % (url, error["classification"])
            )

    global_error = check_destination("http://8.8.8.8/", False, 1.0)
    if global_error:
        failures.append(
            "global literal address was blocked: %s"
            % global_error["message"]
        )

    allowed_local = check_destination("http://127.0.0.1/", True, 1.0)
    if allowed_local:
        failures.append(
            "explicit self-test allowance did not permit loopback"
        )

    allowed_ipv6_local = check_destination("http://[::1]/", True, 1.0)
    if allowed_ipv6_local:
        failures.append(
            "explicit self-test allowance did not permit IPv6 loopback"
        )

    private_under_fixture_policy = check_destination(
        "http://10.0.0.1/", True, 1.0
    )
    if not private_under_fixture_policy:
        failures.append(
            "fixture allowance incorrectly permitted a private address"
        )

    public_under_fixture_policy = check_destination(
        "http://8.8.8.8/", True, 1.0
    )
    if not public_under_fixture_policy:
        failures.append(
            "fixture allowance incorrectly permitted a public address"
        )

    def mixed_resolver(_host, _port, **_kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 80),
            ),
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("10.0.0.1", 80),
            ),
        ]

    mixed_error = check_destination(
        "http://mixed-addresses.r02-t032.test/",
        False,
        1.0,
        resolver=mixed_resolver,
    )
    if not mixed_error:
        failures.append(
            "mixed public/private resolution was not rejected"
        )
    elif mixed_error["classification"] != "BLOCKED_TARGET":
        failures.append(
            "mixed resolution expected BLOCKED_TARGET, got %s"
            % mixed_error["classification"]
        )

    return make_check("ssrf-guard", failures)


def check_url_validation():
    """Exercise URL validation and normalization edge cases."""

    failures = []

    checks = [
        (
            "ftp://example.com/file",
            "UNSUPPORTED_SCHEME",
            "unsupported_scheme",
        ),
        (
            "http://user:pass@example.com/",
            "INVALID_URL",
            "credentials_not_allowed",
        ),
        ("not-a-url", "INVALID_URL", "invalid_url"),
        ("http://", "INVALID_URL", "invalid_url"),
        ("http://[::1", "INVALID_URL", "invalid_url"),
        (
            "http://example.com:99999/",
            "INVALID_URL",
            "invalid_port",
        ),
    ]

    for url, classification, error_type in checks:
        normalized, error = validate_url(url)
        if normalized is not None:
            failures.append("%s: expected validation failure" % url)
            continue
        if error["classification"] != classification:
            failures.append(
                "%s: expected %s, got %s"
                % (url, classification, error["classification"])
            )
        if error["error_type"] != error_type:
            failures.append(
                "%s: expected error_type %s, got %s"
                % (url, error_type, error["error_type"])
            )

    normalized, error = validate_url("https://example.com/path#frag")
    if error or normalized != "https://example.com/path":
        failures.append("fragment was not removed correctly")

    normalized, error = validate_url("http://example.com:80/")
    if error or normalized != "http://example.com/":
        failures.append("default port was not removed correctly")

    normalized, error = validate_url("http://example.com:8080/")
    if error or normalized != "http://example.com:8080/":
        failures.append("non-default port was not preserved")

    normalized, error = validate_url("http://[::1]/")
    if error or normalized != "http://[::1]/":
        failures.append("IPv6 literal was not preserved")

    return make_check("url-validation", failures)


def run_consistency_checks(base):
    """Return all offline consistency checks, including the mock fixture."""

    return [
        check_readme_rows(),
        check_target_scope(),
        check_login_heuristics(),
        check_login_body_detection(),
        check_exception_mapping(),
        check_dns_timeout(),
        check_validated_connect(base),
        check_peer_address_guard(),
        check_tls_verification(),
        check_ssrf_guard(),
        check_url_validation(),
    ]


def git_value(*args):
    """Return a short git value, or None when git is unavailable."""

    try:
        completed = subprocess.run(
            ["git"] + list(args),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if completed.returncode != 0:
        return None

    return completed.stdout.strip() or None


def readme_sha256():
    """Return the README digest used for evidence reproducibility."""

    if not README_PATH.exists():
        return None

    try:
        return hashlib.sha256(README_PATH.read_bytes()).hexdigest()
    except OSError:
        return None


def build_inputs_payload():
    """Build inputs.json from the fixed target constants."""

    rows = find_readme_rows()
    targets = []

    for target in TARGETS:
        matches = rows.get(target["name"]) or []
        match = matches[0] if len(matches) == 1 else None
        targets.append(
            {
                "name": target["name"],
                "url": target["url"],
                "auth": target["auth"],
                "https": target["https"],
                "cors": target["cors"],
                "description": target["description"],
                "readme_line": match["line"] if match else None,
                "readme_category": match["category"] if match else None,
                "readme_row": match["row"] if match else None,
            }
        )

    return {
        "task": TASK_ID,
        "assignment": "2 of 10",
        "section": "Food & Drink",
        "readme_commit": git_value("rev-parse", "HEAD"),
        "readme_sha256": readme_sha256(),
        "fixed_targets_only": True,
        "targets": targets,
        "parameters": {
            "default_max_redirects": MAX_REDIRECTS_DEFAULT,
            "self_test_max_redirects": SELF_TEST_MAX_REDIRECTS,
            "self_test_connect_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "connect_timeout"
            ],
            "self_test_read_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "read_timeout"
            ],
            "live_connect_timeout_seconds": CONNECT_TIMEOUT_DEFAULT,
            "live_read_timeout_seconds": READ_TIMEOUT_DEFAULT,
            "self_test_max_body_bytes": SELF_TEST_RESOLVER_DEFAULTS[
                "max_body_bytes"
            ],
            "live_max_body_bytes": MAX_BODY_BYTES,
            "follow_redirect_statuses": list(FOLLOW_REDIRECT_STATUSES),
            "allowed_schemes": list(ALLOWED_SCHEMES),
            "user_agent": USER_AGENT,
            "dns_timeout_policy": (
                "caller_wait_is_bounded_resolver_thread_is_not_cancellable"
            ),
            "connection_timeout_policy": (
                "all_validated_address_attempts_share_one_connect_deadline"
            ),
            "body_inspection_policy": (
                "all_2xx_html_inspected_timeout_is_failure"
            ),
        },
        "safety": [
            "No API keys or credentials are sent.",
            "No authenticated API calls, form submissions or writes are made.",
            "Only the three fixed targets are requested by the live mode.",
            "Loopback, private, link-local and other non-global destinations are refused in live mode.",
            "Self-test mode permits only loopback fixture addresses, not private or public addresses.",
            "Each destination is resolved once; every returned address is validated before a socket is opened.",
            "The socket connects to a validated numeric address, while the original host name is used for Host, TLS SNI and certificate verification.",
            "The actual connected peer address is compared with the validated address.",
            "Every 2xx HTML response body, direct or redirected, is read only up to 32 KiB for login-form detection. A body read timeout is reported as TIMEOUT and a body read error as CONNECTION_ERROR. Non-HTML and 204/205 bodies are not read.",
        ],
    }


def build_expected_payload(cases, consistency_checks):
    """Build expected-results.json from the fixed offline cases."""

    return {
        "task": TASK_ID,
        "mode": "offline-self-test",
        "generated_at": utc_now(),
        "parameters": {
            "max_redirects": SELF_TEST_MAX_REDIRECTS,
            "connect_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "connect_timeout"
            ],
            "read_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "read_timeout"
            ],
            "max_body_bytes": SELF_TEST_RESOLVER_DEFAULTS["max_body_bytes"],
            "allow_loopback_for_self_test": True,
            "dns_timeout_policy": (
                "caller_wait_is_bounded_resolver_thread_is_not_cancellable"
            ),
            "connection_timeout_policy": (
                "all_validated_address_attempts_share_one_connect_deadline"
            ),
            "body_inspection_policy": (
                "all_2xx_html_inspected_timeout_is_failure"
            ),
        },
        "resolver_cases": [
            {"name": case["name"], "expected": case["expect"]}
            for case in cases
        ],
        "consistency_checks": [
            {"name": check["name"], "expected": "pass"}
            for check in consistency_checks
        ],
    }


def environment_text():
    """Return reproducible environment information without hostnames."""

    lines = [
        "R02-T032 - tool versions and environment",
        "=========================================",
        "",
        "Generated (UTC): %s" % utc_now(),
        "Python: %s" % sys.version.replace("\n", " "),
        "Python implementation: %s" % platform.python_implementation(),
        "Operating system: %s %s (%s)"
        % (platform.system(), platform.release(), platform.machine()),
        "Git commit: %s" % (git_value("rev-parse", "HEAD") or "unknown"),
        "Git branch: %s"
        % (git_value("rev-parse", "--abbrev-ref", "HEAD") or "unknown"),
        "Git version: %s" % (git_value("--version") or "unknown"),
        "README SHA-256: %s" % (readme_sha256() or "unknown"),
        "",
        "Checker dependencies: Python standard library only",
        "Imports: argparse, http.client, ipaddress, json, platform, re,",
        "         socket, ssl, subprocess, sys, threading, time,",
        "         datetime, http.server, pathlib, urllib.parse",
        "",
    ]
    return "\n".join(lines)


def print_case_result(record, kind="case"):
    """Print one PASS/FAIL line with failure details."""

    status = "PASS" if record["passed"] else "FAIL"
    actual = record.get("actual") or {}
    suffix = ""

    if kind == "case":
        suffix = " [%s" % actual.get("classification", "unknown")
        if actual.get("http_status") is not None:
            suffix += ", HTTP %s" % actual["http_status"]
        suffix += "]"

    print("[%s] %s%s" % (status, record["name"], suffix))

    for failure in record.get("failures") or []:
        print("       %s" % failure)


def run_self_test():
    """Run the complete deterministic offline self-test."""

    print("R02-T032 offline self-test")
    print(
        "Parameters: max_redirects=%d, connect_timeout=%.1fs, "
        "read_timeout=%.1fs, allow_loopback_for_self_test=True"
        % (
            SELF_TEST_MAX_REDIRECTS,
            SELF_TEST_RESOLVER_DEFAULTS["connect_timeout"],
            SELF_TEST_RESOLVER_DEFAULTS["read_timeout"],
        )
    )
    print("")

    server, base = start_mock_server()
    resolver_results = []
    consistency_results = []
    cases = []

    try:
        cases = build_self_test_cases(base)
        print("Resolver fixtures (%d cases):" % len(cases))

        for case in cases:
            record = run_resolver_case(case)
            resolver_results.append(record)
            print_case_result(record, kind="case")

        print("")
        print("Consistency checks:")

        consistency_results = run_consistency_checks(base)
        for record in consistency_results:
            print_case_result(record, kind="check")

    finally:
        server.shutdown()
        server.server_close()

    resolver_passed = sum(1 for item in resolver_results if item["passed"])
    consistency_passed = sum(
        1 for item in consistency_results if item["passed"]
    )
    all_passed = (
        resolver_passed == len(resolver_results)
        and consistency_passed == len(consistency_results)
    )

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    write_json(WORK_DIR / "inputs.json", build_inputs_payload())
    write_json(
        WORK_DIR / "expected-results.json",
        build_expected_payload(cases, consistency_results),
    )

    actual_payload = {
        "task": TASK_ID,
        "mode": "offline-self-test",
        "generated_at": utc_now(),
        "python": sys.version.split()[0],
        "parameters": {
            "max_redirects": SELF_TEST_MAX_REDIRECTS,
            "connect_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "connect_timeout"
            ],
            "read_timeout_seconds": SELF_TEST_RESOLVER_DEFAULTS[
                "read_timeout"
            ],
            "max_body_bytes": SELF_TEST_RESOLVER_DEFAULTS["max_body_bytes"],
            "allow_loopback_for_self_test": True,
            "dns_timeout_policy": (
                "caller_wait_is_bounded_resolver_thread_is_not_cancellable"
            ),
            "connection_timeout_policy": (
                "all_validated_address_attempts_share_one_connect_deadline"
            ),
            "body_inspection_policy": (
                "all_2xx_html_inspected_timeout_is_failure"
            ),
        },
        "summary": {
            "resolver_cases": len(resolver_results),
            "resolver_passed": resolver_passed,
            "consistency_checks": len(consistency_results),
            "consistency_passed": consistency_passed,
            "all_passed": all_passed,
        },
        "resolver_cases": resolver_results,
        "consistency_checks": consistency_results,
    }

    write_json(WORK_DIR / "actual-results.json", actual_payload)
    (WORK_DIR / "environment.txt").write_text(
        environment_text(), encoding="utf-8"
    )

    print("")
    print(
        "Summary: %d/%d resolver cases passed; %d/%d consistency checks "
        "passed."
        % (
            resolver_passed,
            len(resolver_results),
            consistency_passed,
            len(consistency_results),
        )
    )
    print(
        "Expected results: %s"
        % display_path(WORK_DIR / "expected-results.json")
    )
    print(
        "Actual results:   %s"
        % display_path(WORK_DIR / "actual-results.json")
    )
    print("Overall: %s" % ("PASS" if all_passed else "FAIL"))

    return 0 if all_passed else 1


def live_limitations(max_redirects):
    """Document the limits of a single automated live observation."""

    return [
        "A single automated GET is not proof that an API is unavailable "
        "and must never be used on its own to remove a README entry.",
        "No API keys, tokens or authenticated calls were used.",
        "The assigned README URLs are landing/documentation pages; no "
        "documented API endpoint was called.",
        "CORS was not inferred from the fact that a browser can open a URL.",
        "Every 2xx HTML response body, direct or redirected, is inspected "
        "up to %d bytes to look for an explicit login form; a body read "
        "timeout is reported as TIMEOUT and a body read error as "
        "CONNECTION_ERROR." % MAX_BODY_BYTES,
        "A login form beyond that %d-byte inspection prefix may not be seen; "
        "non-HTML and 204/205 bodies are not inspected." % MAX_BODY_BYTES,
        "DNS resolution uses one lookup per hop with a bounded caller wait. "
        "The underlying resolver call cannot be cancelled; a late result is "
        "ignored, and the connection uses only the addresses already "
        "validated from that lookup.",
        "TCP connection attempts across the validated addresses share one "
        "connect deadline. There are no request retries.",
        "Redirect following is limited to %d redirects and %d requests per "
        "URL." % (max_redirects, max_redirects + 1),
        "HTTP, DNS, TLS and bot-protection behaviour is a point-in-time "
        "observation and can vary by network, geography and CDN.",
        "AUTH_WALL includes HTTP 401/403 and login/identity-provider "
        "redirects; it is not evidence that an API has disappeared.",
    ]


def run_live(args):
    """Perform a small, sequential live check of the fixed targets."""

    rows = find_readme_rows()
    started_at = utc_now()
    results = []

    print("R02-T032 live verification")
    print(
        "Parameters: max_redirects=%d, connect_timeout=%.1fs, "
        "read_timeout=%.1fs, sequential=True"
        % (args.max_redirects, args.connect_timeout, args.read_timeout)
    )
    print("")

    for target in TARGETS:
        print("Checking %s: %s" % (target["name"], target["url"]))
        resolver = RedirectResolver(
            max_redirects=args.max_redirects,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
            max_body_bytes=MAX_BODY_BYTES,
            allow_loopback_for_self_test=False,
        )
        result = resolver.resolve(target["url"], label=target["name"])

        result["name"] = target["name"]
        result["auth"] = target["auth"]
        result["https"] = target["https"]
        result["cors"] = target["cors"]
        result["description"] = target["description"]

        matches = rows.get(target["name"]) or []
        result["readme_line"] = matches[0]["line"] if len(matches) == 1 else None
        result["readme_row"] = matches[0]["row"] if len(matches) == 1 else None

        results.append(result)

        print(
            "  -> %s (HTTP %s, requests=%d, redirects=%d, %d ms)"
            % (
                result["classification"],
                result["http_status"]
                if result["http_status"] is not None
                else "n/a",
                result["request_count"],
                result["redirect_count"],
                result["elapsed_ms"],
            )
        )

        for item in result["redirects"]:
            print(
                "     %s %s -> %s"
                % (
                    item["status"],
                    item["from_url"],
                    item["to_url"] or item["location"],
                )
            )

        if result["final_url"]:
            print("     final observed URL: %s" % result["final_url"])
        if result["message"]:
            print("     note: %s" % result["message"])
        print("")

    finished_at = utc_now()
    counts = {}
    for result in results:
        key = result["classification"]
        counts[key] = counts.get(key, 0) + 1

    definitive = sum(
        1 for result in results if result["classification"] in ("OK", "MOVED")
    )
    inconclusive = len(results) - definitive

    payload = {
        "task": TASK_ID,
        "mode": "live",
        "observed_at_start": started_at,
        "observed_at_end": finished_at,
        "observation_date": datetime.now(timezone.utc).date().isoformat(),
        "readme_commit": git_value("rev-parse", "HEAD"),
        "readme_sha256": readme_sha256(),
        "parameters": {
            "max_redirects": args.max_redirects,
            "connect_timeout_seconds": args.connect_timeout,
            "read_timeout_seconds": args.read_timeout,
            "max_body_bytes": MAX_BODY_BYTES,
            "allow_loopback_for_self_test": False,
            "dns_timeout_policy": (
                "caller_wait_is_bounded_resolver_thread_is_not_cancellable"
            ),
            "connection_timeout_policy": (
                "all_validated_address_attempts_share_one_connect_deadline"
            ),
            "body_inspection_policy": (
                "all_2xx_html_inspected_timeout_is_failure"
            ),
            "sequential": True,
            "authenticated_requests": False,
            "retries": 0,
            "user_agent": USER_AGENT,
            "follow_redirect_statuses": list(FOLLOW_REDIRECT_STATUSES),
        },
        "summary": {
            "targets": len(results),
            "classification_counts": counts,
            "definitive_success": definitive,
            "inconclusive_or_failed": inconclusive,
        },
        "targets": results,
        "limitations": live_limitations(args.max_redirects),
    }

    output = args.output if args.output else WORK_DIR / "live-results.json"
    write_json(output, payload)

    print(
        "Summary: %d target(s); %d definitive success; %d inconclusive or "
        "failed." % (len(results), definitive, inconclusive)
    )
    print("Live results: %s" % display_path(output))
    print(
        "Reminder: a failed or inconclusive observation is not sufficient "
        "evidence to remove a README entry."
    )

    return 0 if inconclusive == 0 else 2


def build_parser():
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "R02-T032 bounded redirect-chain checker for the three assigned "
            "Food & Drink APIs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "The target list is fixed in the script. There is no option to "
            "check an arbitrary URL.\n\n"
            "Exit codes:\n"
            "  0  self-test passed, or all live targets were OK/MOVED\n"
            "  1  self-test or usage failure\n"
            "  2  live run completed with inconclusive/non-success results\n"
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the deterministic offline fixture suite",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="check only the three fixed official URLs sequentially",
    )
    parser.add_argument(
        "--max-redirects",
        type=int,
        default=MAX_REDIRECTS_DEFAULT,
        help=(
            "maximum redirects to follow per URL "
            "(default: %d)" % MAX_REDIRECTS_DEFAULT
        ),
    )
    parser.add_argument(
        "--connect-timeout",
        type=float,
        default=CONNECT_TIMEOUT_DEFAULT,
        help=(
            "connection timeout in seconds "
            "(default: %.1f)" % CONNECT_TIMEOUT_DEFAULT
        ),
    )
    parser.add_argument(
        "--read-timeout",
        type=float,
        default=READ_TIMEOUT_DEFAULT,
        help=(
            "read timeout in seconds (default: %.1f)" % READ_TIMEOUT_DEFAULT
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "optional path for live-results.json "
            "(default: work/R02-T032/live-results.json)"
        ),
    )
    return parser


def print_targets():
    """Print the fixed scope and available commands without networking."""

    print("R02-T032 - fixed redirect-check targets")
    print("")
    for target in TARGETS:
        print("- %s: %s" % (target["name"], target["url"]))
    print("")
    print("Commands:")
    print("  python3 tools/course_checks/r02-t032.py --self-test")
    print("  python3 tools/course_checks/r02-t032.py --live")
    print("")
    print("No network request is made unless --live is supplied.")
    print("Classifications: %s" % ", ".join(sorted(CLASSIFICATION_DESCRIPTIONS)))


def main(argv=None):
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test and args.live:
        parser.error("--self-test and --live are mutually exclusive")

    if args.max_redirects < 0 or args.max_redirects > MAX_REDIRECTS_LIMIT:
        parser.error(
            "--max-redirects must be between 0 and %d"
            % MAX_REDIRECTS_LIMIT
        )

    if not 0 < args.connect_timeout <= 30:
        parser.error("--connect-timeout must be greater than 0 and <= 30")

    if not 0 < args.read_timeout <= 30:
        parser.error("--read-timeout must be greater than 0 and <= 30")

    if args.self_test:
        return run_self_test()

    if args.live:
        return run_live(args)

    print_targets()
    return 0


if __name__ == "__main__":
    sys.exit(main())



