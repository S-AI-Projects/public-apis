# Course Checkers

This directory contains small, task-specific verification tools for the course
assignments. Each assignment adds its own script and its own section here.
R02-T032 is documented below; other task sections are maintained by their own
branches.

## R02-T032 — Redirect chain verification [Food & Drink]

### Purpose

`r02-t032.py` verifies redirect behaviour for exactly three assigned entries in
the `Food & Drink` section of the root `README.md`:

| API | Assigned URL | README line | Auth | HTTPS | CORS |
|---|---|---|---|---|---|
| BaconMockup | `https://baconmockup.com/` | 1220 | No | Yes | Yes |
| CalorieNinjas | `https://calorieninjas.com/api` | 1221 | `apiKey` | Yes | Yes |
| Chomp | `https://chompthis.com/api/` | 1222 | `apiKey` | Yes | Unknown |

The target list is fixed in the script. There is no command-line option for
checking an arbitrary URL. The checker never sends API keys or credentials,
never submits forms, and never performs authenticated requests.

The checker is a diagnostic tool, not an automatic deletion tool. A failed or
inconclusive automated request must never be used on its own as evidence to
remove an API entry from the README.

### Usage

```bash
# Deterministic offline self-test (no internet, no API keys)
python3 tools/course_checks/r02-t032.py --self-test

# Small, sequential live check of the three fixed official URLs
python3 tools/course_checks/r02-t032.py --live

# Show the fixed target list and commands without making a request
python3 tools/course_checks/r02-t032.py
```

Useful live options:

```bash
python3 tools/course_checks/r02-t032.py --live \
  --max-redirects 5 \
  --connect-timeout 5 \
  --read-timeout 5 \
  --output work/R02-T032/live-results.json
```

Exit codes:

| Code | Meaning |
|---|---|
| `0` | Self-test passed, or every live target was classified `OK`/`MOVED`. |
| `1` | Self-test failure, invalid arguments, or an internal error. |
| `2` | Live run completed but at least one target was inconclusive or unsuccessful. This is not a deletion signal. |

The self-test uses explicit checks rather than Python `assert` statements, so
it behaves identically under `-O` and `-OO`:

```bash
python3 -O tools/course_checks/r02-t032.py --self-test
python3 -OO tools/course_checks/r02-t032.py --self-test
python3 -m py_compile tools/course_checks/r02-t032.py
```

The current implementation passes **57/57 resolver cases** and **11/11
consistency checks** in all three modes (normal, `-O`, `-OO`). The captured
outputs are in `work/R02-T032/validation.txt`; actual JSON results are in
`work/R02-T032/actual-results.json`.

### Redirect resolution

The checker uses `http.client` directly and follows redirects explicitly. It
does not rely on a redirect-following helper that could hide the chain.

- Redirect statuses followed: `301`, `302`, `303`, `307`, `308`.
- Every request is a single `GET`; redirects are never followed implicitly.
- `Location` values are resolved with `urllib.parse.urljoin`, so relative,
  absolute-path and protocol-relative destinations are handled.
- A missing or empty `Location` is an `HTTP_ERROR` with
  `error_type = "missing_location"`.
- A malformed `Location` is an `INVALID_URL` with
  `error_type = "malformed_location"`.
- A non-HTTP(S) destination is an `UNSUPPORTED_SCHEME`.
- Every visited URL is recorded by a normalized loop key (scheme, host, port,
  path, query; fragments removed). A repeated destination is a
  `REDIRECT_LOOP`.
- A chain that reaches the configured redirect budget without repeating a URL
  is a `REDIRECT_LIMIT`. This is deliberately distinct from a loop.
- The result records every redirect status and destination, the last URL
  actually requested, and the pending redirect target when the checker stops
  before requesting it.

The default live budget is **5 redirects**, which permits at most **6
requests** per URL. Reaching a sixth redirect response is reported as
`REDIRECT_LIMIT`; it is not followed.

### Timeouts and transport behaviour

- Connection and read timeouts are separate and configurable.
- Each destination is resolved exactly once per hop. The caller waits at most
  the connection timeout for the resolver helper thread. Python cannot cancel
  a resolver call that is already running, so the daemon thread may finish
  later; its late result is ignored. This is a bounded caller wait, not a hard
  cancellation guarantee.
- After that single lookup, every returned address is validated. The socket is
  then connected directly to one of the validated numeric addresses. The
  connection path does not resolve the host name a second time.
- TCP connection attempts across all validated addresses share one connection
  deadline. TLS handshakes and subsequent reads use the configured timeouts.
- The `http.client` connection still holds the original host name, so it is
  used for the HTTP `Host` header, TLS SNI and certificate host name
  verification. Certificate verification is never disabled.
- The actual peer address reported by the connected socket is compared with
  the validated address. A mismatch is refused as `BLOCKED_TARGET`.
- Connection errors, DNS failures, TLS failures and timeouts are mapped to
  distinct classifications where practical.
- There are no retries in live mode, and requests are sequential.
- A small, honest `User-Agent` identifies the tool as an educational checker.
- Every `2xx` HTML response body, whether direct or reached through a redirect,
  is read only up to 32 KiB to look for an explicit login form. A direct login
  page is therefore classified as `AUTH_WALL`, while an ordinary direct HTML
  page remains `OK` and an ordinary redirected HTML page remains `MOVED`.
- A timeout during that required body read is reported as `TIMEOUT`, and a
  body-read failure (including an incomplete body below the advertised
  `Content-Length`) is reported as `CONNECTION_ERROR`; neither is reported as a
  successful `OK`/`MOVED`.
- `204`/`205` responses, non-HTML responses and non-`2xx` responses are not
  body-inspected. A login form beyond the 32 KiB inspection limit may be
  missed. API keys, credentials and write operations are never sent.

### Classifications

| Classification | Meaning |
|---|---|
| `OK` | The original URL answered with a valid `2xx` status; no redirect was followed. `204` and other legitimate `2xx` statuses count as success. |
| `MOVED` | One or more redirects ended at a valid `2xx` destination. A redirect is not treated as breakage. |
| `REDIRECT_LOOP` | A redirect destination repeated an already-visited URL. |
| `REDIRECT_LIMIT` | The redirect request budget was exhausted before a terminal response. |
| `TIMEOUT` | A DNS caller wait, connect, TLS, send, read or required HTML body read exceeded its timeout. |
| `DNS_FAILURE` | The host name could not be resolved. |
| `CONNECTION_ERROR` | The connection failed, closed before a valid HTTP response, or failed while reading a required HTML body. |
| `TLS_ERROR` | TLS negotiation or certificate verification failed. |
| `TRANSIENT_FAILURE` | A temporary HTTP/network condition, including HTTP `408`, `425`, `429` and `5xx`. |
| `AUTH_WALL` | HTTP `401`/`403`, a redirect to a login or identity-provider path, or an explicit login form on a direct or redirected HTML page. This is not proof that an API has disappeared. |
| `HTTP_ERROR` | A definitive HTTP error, an unexpected redirect status, or a redirect status without `Location`. |
| `INVALID_URL` | A syntactically invalid or unsafe URL, including a malformed redirect destination. |
| `UNSUPPORTED_SCHEME` | A destination other than `http://` or `https://`. |
| `BLOCKED_TARGET` | A loopback, private, link-local or otherwise non-global destination was refused before a request was sent. |

`AUTH_WALL` is intentionally conservative. A login wall, an expired key or a
bot-protection response is not evidence that an API has disappeared or that a
README row should be removed.

### Safety / SSRF policy

Before every request, including every redirect hop, the checker resolves the
destination host once, validates every returned address, and refuses
non-global addresses. Loopback, private, link-local, multicast, reserved and
unspecified addresses are blocked in live mode. This prevents a public URL
from redirecting the checker into an internal network or a cloud metadata
endpoint.

The validated address is also the address used for the socket connection. The
connection path does not re-resolve the host name, which closes the
DNS-rebinding/TOCTOU gap between validation and connection. The original host
name remains in use for the HTTP `Host` header, TLS SNI and certificate
verification, and the connected peer address is checked against the validated
address.

The offline self-test explicitly enables a local mock server on `127.0.0.1`.
That allowance is confined to the self-test code path and permits only
loopback addresses, not private or public addresses. Live mode always uses
`allow_loopback_for_self_test=False`. The checker also refuses URLs containing
credentials and does not accept URL input from the command line.

### Offline fixture design

`--self-test` starts a local `http.server.ThreadingHTTPServer` on an ephemeral
loopback port. It never contacts a live service. The fixture server provides:

- direct `200`, `201`, `204` and `206` successes;
- `301`, `302`, `303`, `307` and `308` redirects;
- a relative `Location`, a multi-hop chain and a query-preserving redirect;
- a chain within budget and a chain that exhausts the budget;
- a two-URL loop and a self-loop;
- missing and malformed `Location` headers;
- a redirect to an unsupported scheme and a redirect to a private address that
  must be revalidated and blocked before connection;
- HTTP `401`, `403`, `404`, `408`, `425`, `429`, `500` and `503`, an
  unexpected `300`/`304`, and redirected `403`/`500` responses;
- a direct password form, a direct ordinary HTML page and a direct HTML page
  with no login indicators (including a non-password input);
- a login-path redirect, an identity-provider redirect and a redirected
  password form;
- direct and redirected HTML responses whose body read times out;
- a direct HTML response whose body is shorter than its advertised
  `Content-Length` (a body-read error);
- a read timeout and a connection that closes without a response;
- a reserved `.invalid` host for DNS failure;
- invalid URLs, credentials in a URL and an unsupported scheme;
- loopback, private, link-local and IPv6-loopback destinations that must be
  blocked by the SSRF guard.

The self-test also runs consistency checks for:

- the three exact `Food & Drink` README rows and their metadata;
- the fixed target scope and URL normalization;
- positive and negative login/identity-provider detection;
- password-form detection;
- exception-to-classification mapping;
- the bounded DNS caller wait and documented lack of resolver cancellation;
- a host name resolved to a loopback address, then connected without a second
  lookup, with the original `Host` header and matching validated/peer address;
- the connected-peer address guard;
- TLS certificate and host name verification settings;
- the SSRF guard, including the loopback-only self-test allowance and a mixed
  public/private address resolution;
- URL validation and normalization.

`work/R02-T032/expected-results.json` records the expected offline outcomes and
`work/R02-T032/actual-results.json` records what actually ran. The command
prints `PASS`/`FAIL` for every case and exits `0` only when all resolver cases
and consistency checks pass.

### Live verification limitations

Live mode makes one sequential request per target, with no retries and no
credentials. It checks the assigned landing/documentation URLs, not their
documented API endpoints. A live result is a point-in-time observation that can
vary with DNS, geography, CDN behaviour, rate limiting and bot protection. It
does not establish API correctness, response schemas, authentication success or
CORS support. Every `2xx` HTML body is inspected up to 32 KiB for an explicit
login form, whether the response was direct or reached through a redirect.
Non-HTML bodies are not inspected.

CORS is not inferred from the fact that a browser can open a page. The README
CORS values are preserved unless official documentation or reliable testing
establishes a correction.

### Evidence

Inputs, parameters, expected and actual offline results, live observations,
environment details and official-documentation notes are stored in
`work/R02-T032/`:

- `README.md` — task summary, methodology and decisions;
- `inputs.json` — fixed target list, README lines and test parameters;
- `expected-results.json` — expected offline outcomes;
- `actual-results.json` — actual offline results from the latest self-test;
- `live-results.json` — dated live observations and redirect chains;
- `environment.txt` — Python, OS, git and README digest;
- `api-verification.md` — official documentation review;
- `validation.txt` — commands and summaries from the validation run.
