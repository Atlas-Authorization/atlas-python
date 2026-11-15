"""Web Bot Auth: verify who is behind an automated request.

A bot signs its requests with an Ed25519 key (RFC 9421 HTTP Message Signatures, tag ``web-bot-auth``)
and names the place its public keys live in the ``Signature-Agent`` header. The key is found in the
directory served at ``<Signature-Agent>/.well-known/http-message-signatures-directory`` and the
signature's ``keyid`` is the RFC 7638 JWK thumbprint of that key.

    from atlas_backend import WebBotAuthVerifier

    verifier = WebBotAuthVerifier(allow=[{"directory": "https://bot.example", "name": "Example bot"}])
    decision = verifier.verify(method="GET", url=str(request.url), headers=request.headers)
    if decision.decision == "block": ...

Runs locally: no call to Atlas, directories cached in memory. The default directory fetch resolves the
host once, refuses every non-global address (loopback, private, link-local, cloud metadata, ULA,
multicast), connects to the vetted address only, never follows a redirect and caps time and size.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import re
import socket
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, quote, urlsplit

WEB_BOT_AUTH_TAG = "web-bot-auth"
WEB_BOT_AUTH_DIRECTORY_PATH = "/.well-known/http-message-signatures-directory"
WEB_BOT_AUTH_DIRECTORY_MEDIA_TYPE = "application/http-message-signatures-directory+json"
WEB_BOT_AUTH_DEFAULT_SKEW_SECONDS = 30
WEB_BOT_AUTH_DEFAULT_MAX_LIFETIME_SECONDS = 3600

_KEY_RE = re.compile(r"[a-z*][a-z0-9_.*-]*")
_TOKEN_CHARS = re.compile(r"[A-Za-z0-9:/!#$%&'*+\-.^_`|~]")
_DERIVED = frozenset(["@method", "@authority", "@path", "@target-uri", "@scheme", "@query", "@request-target"])


# -- encoding ---------------------------------------------------------------------------------


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def base64url_to_bytes(value: str) -> bytes | None:
    if not re.fullmatch(r"[A-Za-z0-9_-]*", value):
        return None
    return _b64_to_bytes(value.replace("-", "+").replace("_", "/"))


def _b64_to_bytes(value: str) -> bytes | None:
    if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", value):
        return None
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4))
    except ValueError:
        return None


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def ed25519_jwk_thumbprint(jwk: Mapping[str, Any]) -> str:
    """RFC 7638 thumbprint (base64url SHA-256) of an Ed25519 public JWK: the web-bot-auth ``keyid``."""
    canonical = f'{{"crv":"Ed25519","kty":"OKP","x":"{jwk["x"]}"}}'
    return _b64u(hashlib.sha256(canonical.encode()).digest())


def ed25519_jwk_bytes(jwk: Any) -> bytes | None:
    """The raw 32-byte public key of a JWK, or ``None`` when it is not a well-formed Ed25519 key."""
    if not isinstance(jwk, Mapping) or jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519" or not isinstance(jwk.get("x"), str):
        return None
    raw = base64url_to_bytes(jwk["x"])
    return raw if raw is not None and len(raw) == 32 else None


def parse_directory(doc: Any) -> list[dict[str, Any]]:
    """The usable Ed25519 keys of a directory document (a JWK Set); at most 20 are kept."""
    keys = doc.get("keys") if isinstance(doc, Mapping) else None
    if not isinstance(keys, list):
        return []
    return [dict(k) for k in keys if ed25519_jwk_bytes(k) is not None][:20]


# -- structured fields (the subset RFC 9421 headers use) -----------------------------------------


def _split_top(s: str, sep: str) -> list[str]:
    out: list[str] = []
    depth, quoted, start, i = 0, False, 0, 0
    while i < len(s):
        c = s[i]
        if quoted:
            if c == "\\":
                i += 1
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == sep and depth == 0:
            out.append(s[start:i])
            start = i + 1
        i += 1
    out.append(s[start:])
    return [m.strip() for m in out if m.strip()]


def _read_string(s: str, i: int) -> tuple[str, int] | None:
    if i >= len(s) or s[i] != '"':
        return None
    out: list[str] = []
    j = i + 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            n = s[j + 1] if j + 1 < len(s) else None
            if n not in ('"', "\\"):
                return None
            out.append(n)
            j += 1
        elif c == '"':
            return "".join(out), j + 1
        elif ord(c) < 0x20 or ord(c) > 0x7E:
            return None
        else:
            out.append(c)
        j += 1
    return None


def _parse_params(text: str) -> dict[str, Any] | None:
    out: dict[str, Any] = {}
    i = 0
    while i < len(text):
        if text[i] != ";":
            return None
        i += 1
        key = ""
        while i < len(text) and re.match(r"[a-z0-9_.*-]", text[i]):
            key += text[i]
            i += 1
        if not _KEY_RE.fullmatch(key):
            return None
        if i >= len(text) or text[i] != "=":
            out[key] = True
            continue
        i += 1
        c = text[i] if i < len(text) else None
        if c == '"':
            st = _read_string(text, i)
            if not st:
                return None
            out[key], i = st
        elif c == ":":
            close = text.find(":", i + 1)
            if close < 0:
                return None
            raw = _b64_to_bytes(text[i + 1 : close])
            if raw is None:
                return None
            out[key], i = raw, close + 1
        elif c == "?":
            b = text[i : i + 2]
            if b not in ("?0", "?1"):
                return None
            out[key], i = b == "?1", i + 2
        elif c is not None and re.match(r"[-0-9]", c):
            n = ""
            while i < len(text) and re.match(r"[-0-9.]", text[i]):
                n += text[i]
                i += 1
            if not re.fullmatch(r"-?\d{1,15}(\.\d{1,3})?", n):
                return None
            out[key] = float(n) if "." in n else int(n)
        elif c is not None and re.match(r"[A-Za-z*]", c):
            t = ""
            while i < len(text) and _TOKEN_CHARS.match(text[i]):
                t += text[i]
                i += 1
            out[key] = t
        else:
            return None
    return out


@dataclass
class _ParsedInput:
    label: str
    components: list[tuple[str, dict[str, Any]]]
    params: dict[str, Any]
    raw: str


def parse_signature_input(header: str) -> list[_ParsedInput] | None:
    """Parse a ``Signature-Input`` field. ``None`` when any member is malformed."""
    out: list[_ParsedInput] = []
    for member in _split_top(header, ","):
        eq = member.find("=")
        if eq <= 0:
            return None
        label, raw = member[:eq].strip(), member[eq + 1 :].strip()
        if not _KEY_RE.fullmatch(label) or not raw.startswith("("):
            return None
        close, quoted, i = -1, False, 1
        while i < len(raw):
            c = raw[i]
            if quoted:
                if c == "\\":
                    i += 1
                elif c == '"':
                    quoted = False
            elif c == '"':
                quoted = True
            elif c == ")":
                close = i
                break
            i += 1
        if close < 0:
            return None
        components: list[tuple[str, dict[str, Any]]] = []
        inner, i = raw[1:close], 0
        while i < len(inner):
            if inner[i] == " ":
                i += 1
                continue
            st = _read_string(inner, i)
            if not st:
                return None
            name, i = st
            ptext = ""
            while i < len(inner) and inner[i] != " ":
                if inner[i] == '"':
                    q = _read_string(inner, i)
                    if not q:
                        return None
                    ptext += inner[i : q[1]]
                    i = q[1]
                else:
                    ptext += inner[i]
                    i += 1
            params = _parse_params(ptext)
            if params is None:
                return None
            components.append((name, params))
        params = _parse_params(raw[close + 1 :])
        if params is None:
            return None
        out.append(_ParsedInput(label, components, params, raw))
    return out or None


def parse_signature_header(header: str) -> dict[str, bytes] | None:
    """Parse a ``Signature`` field into label -> signature bytes. ``None`` when malformed."""
    out: dict[str, bytes] = {}
    for member in _split_top(header, ","):
        m = re.fullmatch(r"([a-z*][a-z0-9_.*-]*)=:([A-Za-z0-9+/=]*):", member)
        if not m:
            return None
        raw = _b64_to_bytes(m.group(2))
        if raw is None:
            return None
        out[m.group(1)] = raw
    return out or None


def normalize_directory(value: str) -> str | None:
    """Canonical form of a directory reference: ``https://host[:port][/path]``. A bare host gets ``https://``.
    ``None`` for anything that is not an https URL without credentials, query or fragment."""
    s = value.strip()
    if not s:
        return None
    if not re.match(r"[a-z][a-z0-9+.-]*://", s, re.I):
        s = f"https://{s}"
    try:
        u = urlsplit(s)
        host, port = u.hostname, u.port
    except ValueError:
        return None
    if u.scheme != "https" or u.username or u.password or u.query or u.fragment or "#" in s or "?" in s or not host:
        return None
    netloc = f"[{host}]" if ":" in host else host
    if port and port != 443:
        netloc += f":{port}"
    return f"https://{netloc}{u.path.rstrip('/')}"


def parse_signature_agent(value: str, label: str | None = None) -> str | None:
    """The directory a ``Signature-Agent`` value names, normalised. Accepts a quoted string, a bare URL, or
    the dictionary form (``sig1="https://bot.example"``; the member for ``label`` wins, else the first)."""
    v = value.strip()
    if not v:
        return None
    if re.match(r"[a-z*][a-z0-9_.*-]*=", v):
        members = _split_top(v, ",")
        pick = next((m for m in members if label is not None and m.startswith(f"{label}=")), members[0])
        v = pick[pick.index("=") + 1 :].strip()
    if v.startswith('"'):
        st = _read_string(v, 0)
        if not st or st[1] != len(v):
            return None
        v = st[0]
    return normalize_directory(v)


def directory_url_for(directory: str) -> str:
    return f"{directory}{WEB_BOT_AUTH_DIRECTORY_PATH}"


# -- signature base (RFC 9421 section 2.5) ---------------------------------------------------------


def header_value(headers: Mapping[str, Any], name: str) -> str | None:
    """A header's value as RFC 9421 reads it: fields of one name joined with ``", "``, whitespace trimmed."""
    lower = name.lower()
    parts: list[str] = []
    for k, v in headers.items():
        if str(k).lower() != lower or v is None:
            continue
        parts.extend(str(i).strip() for i in (v if isinstance(v, (list, tuple)) else [v]))
    return ", ".join(parts) if parts else None


def _escape(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def serialize_component_id(name: str, params: Mapping[str, Any] | None = None) -> str:
    """The component identifier as written in ``Signature-Input`` and the signature base: ``"name";param=value``."""
    out = _escape(name)
    for k, v in (params or {}).items():
        if v is True:
            out += f";{k}"
        elif v is False:
            out += f";{k}=?0"
        elif isinstance(v, str):
            out += f";{k}={_escape(v)}"
        elif isinstance(v, (int, float)):
            out += f";{k}={v}"
        else:
            out += f";{k}=:{_b64(v)}:"
    return out


def _sf_bare_item(text: str, i: int) -> tuple[str, int] | None:
    c = text[i] if i < len(text) else None
    if c == '"':
        st = _read_string(text, i)
        return (text[i : st[1]], st[1]) if st else None
    if c == ":":
        close = text.find(":", i + 1)
        if close < 0 or _b64_to_bytes(text[i + 1 : close]) is None:
            return None
        return text[i : close + 1], close + 1
    if c == "?":
        b = text[i : i + 2]
        return (b, i + 2) if b in ("?0", "?1") else None
    if c is not None and re.match(r"[-0-9]", c):
        m = re.match(r"-?\d{1,15}(\.\d{1,3})?", text[i:])
        if not m:
            return None
        if m.group(1) is None:
            return m.group(0), i + len(m.group(0))
        fixed = f"{float(m.group(0)):.3f}".rstrip("0")
        return (fixed + "0" if fixed.endswith(".") else fixed), i + len(m.group(0))
    if c is not None and re.match(r"[A-Za-z*]", c):
        j = i
        while j < len(text) and _TOKEN_CHARS.match(text[j]):
            j += 1
        return text[i:j], j
    return None


def _sf_params(text: str, i: int) -> tuple[str, int] | None:
    out = ""
    while True:
        j = i
        while j < len(text) and text[j] in " \t":
            j += 1
        if j >= len(text) or text[j] != ";":
            return out, i
        j += 1
        while j < len(text) and text[j] == " ":
            j += 1
        m = _KEY_RE.match(text[j:])
        if not m:
            return None
        key = m.group(0)
        j += len(key)
        out += f";{key}"
        if j < len(text) and text[j] == "=":
            v = _sf_bare_item(text, j + 1)
            if not v:
                return None
            out += f"={v[0]}"
            j = v[1]
        i = j


def _sf_item(text: str) -> str | None:
    t = text.strip()
    if t.startswith("("):
        depth, quoted, close, k = 0, False, -1, 0
        while k < len(t):
            ch = t[k]
            if quoted:
                if ch == "\\":
                    k += 1
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    close = k
                    break
            k += 1
        if close < 0:
            return None
        members = []
        for m in _split_top(re.sub(r"\s+", " ", t[1:close]), " "):
            canon = _sf_item(m)
            if canon is None:
                return None
            members.append(canon)
        body: tuple[str, int] | None = ("(" + " ".join(members) + ")", close + 1)
    else:
        body = _sf_bare_item(t, 0)
    if not body:
        return None
    params = _sf_params(t, body[1])
    if params is None or t[params[1] :].strip() != "":
        return None
    return body[0] + params[0]


def _sf_dictionary(text: str) -> list[tuple[str, str]] | None:
    out: list[tuple[str, str]] = []
    for member in _split_top(text, ","):
        m = _KEY_RE.match(member)
        if not m:
            return None
        key, rest = m.group(0), member[m.end() :]
        value = _sf_item(rest[1:]) if rest.startswith("=") else _sf_item("?1" + rest)
        if value is None:
            return None
        out.append((key, value))
    return out or None


def _sf_serialize(text: str) -> str | None:
    members = _split_top(text, ",")
    if members and all(re.match(r"[a-z*][a-z0-9_.*-]*(=|;|$)", m) for m in members) and any(
        re.match(r"[a-z*][a-z0-9_.*-]*=", m) for m in members
    ):
        d = _sf_dictionary(text)
        if d is None:
            return None
        return ", ".join(
            k if v == "?1" else (f"{k}{v[2:]}" if v.startswith("?1;") else f"{k}={v}") for k, v in d
        )
    items = [_sf_item(m) for m in members]
    return ", ".join(items) if items and all(i is not None for i in items) else None  # type: ignore[arg-type]


def _component_value(name: str, params: Mapping[str, Any], method: str, url: Any, headers: Mapping[str, Any]) -> str | None:
    keys = list(params)
    path = url.path or "/"
    query = f"?{url.query}" if url.query else ""
    if name == "@query-param":
        if len(keys) != 1 or not isinstance(params.get("name"), str):
            return None
        found = [v for k, v in parse_qsl(url.query, keep_blank_values=True) if k == params["name"]]
        return quote(found[0], safe="~-_.") if len(found) == 1 else None
    if name.startswith("@"):
        if keys:
            return None
        host = (url.hostname or "").lower()
        authority = f"[{host}]" if ":" in host else host
        if url.port and url.port != {"https": 443, "http": 80}.get(url.scheme.lower()):
            authority += f":{url.port}"
        return {
            "@method": method.upper(),
            "@authority": authority,
            "@path": path,
            "@target-uri": f"{url.scheme}://{authority}{path}{query}",
            "@scheme": url.scheme.lower(),
            "@query": query or "?",
            "@request-target": f"{path}{query}",
        }.get(name)
    raw = header_value(headers, name)
    if raw is None:
        return None
    if not keys:
        return raw
    # Header-field parameters: at most one of sf, key (with a string value) or bs.
    if len(keys) != 1:
        return None
    if params.get("sf") is True:
        return _sf_serialize(raw)
    if isinstance(params.get("key"), str):
        member = next((v for k, v in (_sf_dictionary(raw) or []) if k == params["key"]), None)
        return member
    if params.get("bs") is True:
        return f":{_b64(raw.encode())}:"
    return None


def build_signature_base(
    method: str,
    url: str,
    headers: Mapping[str, Any],
    components: Sequence[str | tuple[str, Mapping[str, Any]]],
    signature_params: str,
) -> tuple[str | None, str | None]:
    """The RFC 9421 signature base: ``(base, None)`` or ``(None, reason)`` where the reason is
    ``unsupported_component``, ``component_missing`` or ``bad_request``. A component is a name or
    ``(name, params)`` for the parameterised forms (``sf``, ``key``, ``bs``; ``@query-param`` with ``name``)."""
    try:
        u = urlsplit(url)
        u.port  # noqa: B018 (validates the port)
    except ValueError:
        return None, "bad_request"
    if not u.scheme or not u.hostname:
        return None, "bad_request"
    seen: set[str] = set()
    lines: list[str] = []
    for entry in components:
        name, params = (entry, {}) if isinstance(entry, str) else (entry[0], dict(entry[1]))
        if name != name.lower():
            return None, "unsupported_component"
        if name.startswith("@") and name not in _DERIVED and name != "@query-param":
            return None, "unsupported_component"
        cid = serialize_component_id(name, params)
        if cid in seen:
            return None, "unsupported_component"
        seen.add(cid)
        if not all(k in ("sf", "key", "bs", "name") for k in params):
            return None, "unsupported_component"
        if name.startswith("@") and name != "@query-param" and params:
            return None, "unsupported_component"
        v = _component_value(name, params, method, u, headers)
        if v is None or "\r" in v or "\n" in v:
            return None, "component_missing"
        lines.append(f"{cid}: {v}")
    lines.append(f'"@signature-params": {signature_params}')
    return "\n".join(lines), None


# -- verification -------------------------------------------------------------------------------


@dataclass
class WebBotAuthResult:
    #: True when the request carried a signature header at all.
    signed: bool
    verified: bool
    #: ``no_signature``, ``no_web_bot_auth_signature``, ``malformed``, ``missing_signature_agent``,
    #: ``bad_signature_agent``, ``bad_params``, ``unsupported_algorithm``, ``unsupported_component``,
    #: ``component_missing``, ``components_not_covered``, ``bad_request``, ``not_yet_valid``, ``expired``,
    #: ``lifetime_too_long``, ``directory_unavailable``, ``key_not_found``, ``bad_signature``, ``replayed``.
    reason: str | None = None
    #: The normalised directory the signer claims (trust it only when ``verified``).
    directory: str | None = None
    key_id: str | None = None
    label: str | None = None
    created: int | None = None
    expires: int | None = None
    nonce: str | None = None


GetKeys = Callable[[str, bool], "list[dict[str, Any]] | None"]


def verify_web_bot_auth(
    method: str,
    url: str,
    headers: Mapping[str, Any],
    *,
    get_keys: GetKeys,
    now_ms: int | None = None,
    skew_seconds: int = WEB_BOT_AUTH_DEFAULT_SKEW_SECONDS,
    max_lifetime_seconds: int = WEB_BOT_AUTH_DEFAULT_MAX_LIFETIME_SECONDS,
    claim_nonce: Callable[[str, int], bool] | None = None,
) -> WebBotAuthResult:
    """Verify the web-bot-auth signature on a request. Never raises on bad input.

    ``get_keys(directory_url, refresh)`` returns the directory's Ed25519 JWKs (``None`` = unavailable);
    ``refresh`` asks for a fresh copy because the key was not in the cached one. ``claim_nonce(key,
    expires_at_ms)`` is the replay guard: ``True`` the first time a nonce is seen."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    input_header = header_value(headers, "signature-input")
    sig_header = header_value(headers, "signature")
    if input_header is None or sig_header is None:
        return WebBotAuthResult(False, False, "no_signature")

    def fail(reason: str, **extra: Any) -> WebBotAuthResult:
        return WebBotAuthResult(True, False, reason, **extra)

    inputs = parse_signature_input(input_header)
    sigs = parse_signature_header(sig_header)
    if not inputs or not sigs:
        return fail("malformed")
    chosen = next((i for i in inputs if i.params.get("tag") == WEB_BOT_AUTH_TAG and i.label in sigs), None)
    if chosen is None:
        return fail("no_web_bot_auth_signature")
    signature = sigs[chosen.label]
    p = chosen.params
    created, expires, key_id, nonce = p.get("created"), p.get("expires"), p.get("keyid"), p.get("nonce")

    def is_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    if (
        not is_int(created)
        or not is_int(expires)
        or not isinstance(key_id, str)
        or not 0 < len(key_id) <= 128
        or (nonce is not None and (not isinstance(nonce, str) or len(nonce) > 512))
    ):
        return fail("bad_params", label=chosen.label)
    base = {"label": chosen.label, "key_id": key_id, "created": created, "expires": expires}
    if p.get("alg") is not None and p["alg"] != "ed25519":
        return fail("unsupported_algorithm", **base)

    now_s = (int(time.time() * 1000) if now_ms is None else now_ms) // 1000
    if expires <= created:
        return fail("bad_params", **base)
    if expires - created > max_lifetime_seconds:
        return fail("lifetime_too_long", **base)
    if created > now_s + skew_seconds:
        return fail("not_yet_valid", **base)
    if expires < now_s - skew_seconds:
        return fail("expired", **base)

    # Coverage: the signature must bind the host, and the directory claim it relies on.
    names = [n for n, _ in chosen.components]
    agent_header = header_value(headers, "signature-agent")
    if agent_header is None:
        return fail("missing_signature_agent", **base)
    agent_params = next((pr for n, pr in chosen.components if n == "signature-agent"), None)
    if "@authority" not in names or agent_params is None:
        return fail("components_not_covered", **base)
    # Covered as a dictionary member (`;key="m"`): the directory must come from that member, or an
    # uncovered one could be swapped in.
    agent_key = agent_params.get("key") if isinstance(agent_params.get("key"), str) else None
    if agent_key is not None and not any(m.startswith(f"{agent_key}=") for m in _split_top(agent_header, ",")):
        return fail("bad_signature_agent", **base)
    directory = parse_signature_agent(agent_header, agent_key or chosen.label)
    if not directory:
        return fail("bad_signature_agent", **base)
    with_dir = {**base, "directory": directory}

    sig_base, err = build_signature_base(method, url, headers, chosen.components, chosen.raw)
    if sig_base is None:
        return fail(err or "bad_request", **with_dir)

    dir_url = directory_url_for(directory)

    def find(keys: list[dict[str, Any]] | None) -> dict[str, Any] | None:
        return next((k for k in keys or [] if ed25519_jwk_thumbprint(k) == key_id), None)

    keys = get_keys(dir_url, False)
    jwk = find(keys)
    if jwk is None:
        keys = get_keys(dir_url, True)
        jwk = find(keys)
    if jwk is None:
        return fail("directory_unavailable" if keys is None else "key_not_found", **with_dir)
    pub = ed25519_jwk_bytes(jwk)
    ok = False
    if pub is not None and len(signature) == 64:
        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(signature, sig_base.encode())
            ok = True
        except (InvalidSignature, ValueError):
            ok = False
    if not ok:
        return fail("bad_signature", **with_dir)
    if claim_nonce is not None and isinstance(nonce, str):
        if not claim_nonce(f"{directory}|{key_id}|{nonce}", expires * 1000 + skew_seconds * 1000):
            return fail("replayed", **with_dir)
    return WebBotAuthResult(True, True, nonce=nonce if isinstance(nonce, str) else None, **with_dir)


def sign_web_bot_auth_request(
    *,
    method: str,
    url: str,
    signature_agent: str,
    private_key: bytes,
    created: int,
    expires: int,
    headers: Mapping[str, str] | None = None,
    nonce: str | None = None,
    label: str = "sig1",
    components: Sequence[str | tuple[str, Mapping[str, Any]]] = ("@authority", "signature-agent"),
) -> dict[str, str]:
    """Produce the three headers (``signature-agent``, ``signature-input``, ``signature``) for a request.
    ``private_key`` is the 32-byte Ed25519 seed; ``components`` must include ``@authority`` and ``signature-agent``."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.from_private_bytes(private_key)
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    key_id = ed25519_jwk_thumbprint({"x": _b64u(pub)})
    agent_header = f'"{signature_agent}"'
    ids = " ".join(serialize_component_id(*((c, None) if isinstance(c, str) else c)) for c in components)
    params = f'({ids});created={created};keyid="{key_id}";alg="ed25519";expires={expires}' + (
        f';nonce="{nonce}"' if nonce else ""
    ) + f';tag="{WEB_BOT_AUTH_TAG}"'
    all_headers = {**(headers or {}), "signature-agent": agent_header}
    sig_base, err = build_signature_base(method, url, all_headers, components, params)
    if sig_base is None:
        raise ValueError(f"Cannot sign: {err}.")
    return {
        "signature-agent": agent_header,
        "signature-input": f"{label}={params}",
        "signature": f"{label}=:{_b64(key.sign(sig_base.encode()))}:",
    }


# -- directory cache, decision, local verifier -----------------------------------------------------


class WebBotAuthDirectoryCache:
    """A small in-memory directory cache. ``fetch_json(url)`` returns the parsed document or ``None``."""

    def __init__(
        self,
        fetch_json: Callable[[str], Any],
        *,
        ttl_ms: int = 600_000,
        failure_ttl_ms: int = 60_000,
        refresh_cooldown_ms: int = 60_000,
        max_entries: int = 1000,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._fetch, self._ttl, self._fail_ttl = fetch_json, ttl_ms, failure_ttl_ms
        self._cooldown, self._max = refresh_cooldown_ms, max_entries
        self._now = now or (lambda: int(time.time() * 1000))
        self._entries: dict[str, tuple[list[dict[str, Any]] | None, int, int]] = {}
        self._lock = threading.Lock()

    def get_keys(self, url: str, refresh: bool) -> list[dict[str, Any]] | None:
        t = self._now()
        with self._lock:
            hit = self._entries.get(url)
        if hit:
            keys, at, fetched_at = hit
            ttl = self._ttl if keys else self._fail_ttl
            if t - at < ttl and not (refresh and t - fetched_at >= self._cooldown):
                return keys
        try:
            doc = self._fetch(url)
            parsed = parse_directory(doc) if doc is not None else []
            fresh: list[dict[str, Any]] | None = parsed or None
        except Exception:
            fresh = None
        # A failed refresh keeps serving the last good copy rather than dropping a working directory.
        kept = fresh if fresh is not None else (hit[0] if hit else None)
        with self._lock:
            if len(self._entries) >= self._max and url not in self._entries:
                self._entries.pop(next(iter(self._entries)))
            self._entries[url] = (kept, t, t)
        return kept

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


@dataclass
class WebBotAuthDecision:
    verified: bool
    #: Who signed: set only when ``verified``, because an unverified claim proves nothing.
    agent: dict[str, str] | None
    #: ``allowed``, ``blocked``, ``verified`` or ``unverified``.
    tier: str
    #: ``allow``, ``block`` or ``unknown``.
    decision: str
    reason: str | None = None


def decide_web_bot_auth(
    result: WebBotAuthResult,
    *,
    allow: Sequence[Mapping[str, str]] = (),
    block: Sequence[Mapping[str, str]] = (),
) -> WebBotAuthDecision:
    """Turn a verification result into a decision. Only a VERIFIED directory can be allowed or blocked: an
    unsigned or failed request is ``unknown``, never trusted and never attributed to the directory it
    claimed. A block entry beats an allow entry."""
    if not result.verified or not result.directory or not result.key_id:
        return WebBotAuthDecision(False, None, "unverified", "unknown", result.reason)

    def match(entries: Sequence[Mapping[str, str]]) -> Mapping[str, str] | None:
        return next((e for e in entries if normalize_directory(e["directory"]) == result.directory), None)

    blocked = match(block)
    allowed = None if blocked else match(allow)
    entry = blocked or allowed
    name = (entry or {}).get("name", "").strip() or (urlsplit(result.directory).hostname or "")
    return WebBotAuthDecision(
        True,
        {"directory": result.directory, "key_id": result.key_id, "name": name},
        "blocked" if blocked else "allowed" if allowed else "verified",
        "block" if blocked else "allow" if allowed else "unknown",
    )


_DIRECTORY_MAX_BYTES = 64 * 1024


def _public_address(host: str) -> str | None:
    """Resolve ``host`` once; ``None`` unless EVERY answer is a global (publicly routable) address."""
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        return None
    addrs = [i[4][0] for i in infos]
    if not addrs:
        return None
    for a in addrs:
        ip = ipaddress.ip_address(a.split("%")[0])
        if getattr(ip, "ipv4_mapped", None):
            ip = ip.ipv4_mapped  # type: ignore[assignment]
        if not ip.is_global or ip.is_multicast:
            return None
    return addrs[0]


def default_directory_fetch(url: str) -> Any:
    """Fetch a directory document: https only, the host resolved once and every non-global address refused,
    connected to the vetted address only (the TLS name stays the host's), no redirects, 5 s, 64 KB."""
    import httpx

    u = urlsplit(url)
    host = u.hostname or ""
    if u.scheme != "https" or not host or "." not in host or host.endswith(".localhost") or ":" in host:
        return None
    try:
        ipaddress.ip_address(host)
        return None  # a literal address
    except ValueError:
        pass
    addr = _public_address(host)
    if addr is None:
        return None
    pinned = f"[{addr}]" if ":" in addr else addr
    netloc = pinned + (f":{u.port}" if u.port else "")
    with httpx.Client(timeout=5.0, follow_redirects=False) as client:
        res = client.get(
            f"https://{netloc}{u.path}",
            headers={"accept": WEB_BOT_AUTH_DIRECTORY_MEDIA_TYPE, "host": u.netloc},
            extensions={"sni_hostname": host},
        )
    if not res.is_success or len(res.content) > _DIRECTORY_MAX_BYTES:
        return None
    return json.loads(res.content)


class WebBotAuthVerifier:
    """A verifier that runs inside your own server: no call to Atlas, directories cached in memory.

    Args:
        allow / block: lists of ``{"directory": url_or_host, "name": label}``.
        fetch_json: replaces the default pinned directory fetch (it must refuse private addresses itself).
        reject_replays: refuse a signature whose nonce was seen before (in memory, per process). Off by
            default: some bots reuse one signed request until it expires.
    """

    def __init__(
        self,
        *,
        allow: Sequence[Mapping[str, str]] = (),
        block: Sequence[Mapping[str, str]] = (),
        fetch_json: Callable[[str], Any] | None = None,
        ttl_ms: int = 600_000,
        refresh_cooldown_ms: int = 60_000,
        skew_seconds: int = WEB_BOT_AUTH_DEFAULT_SKEW_SECONDS,
        max_lifetime_seconds: int = WEB_BOT_AUTH_DEFAULT_MAX_LIFETIME_SECONDS,
        reject_replays: bool = False,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._allow, self._block = allow, block
        self._now = now or (lambda: int(time.time() * 1000))
        self._cache = WebBotAuthDirectoryCache(
            fetch_json or default_directory_fetch, ttl_ms=ttl_ms, refresh_cooldown_ms=refresh_cooldown_ms, now=self._now
        )
        self._skew, self._lifetime = skew_seconds, max_lifetime_seconds
        self._seen: dict[str, int] = {}
        self._reject = reject_replays
        self._lock = threading.Lock()

    def _claim(self, key: str, expires_at_ms: int) -> bool:
        with self._lock:
            t = self._now()
            if len(self._seen) > 5000:
                for k in [k for k, e in self._seen.items() if e <= t]:
                    del self._seen[k]
            if len(self._seen) > 20_000:
                return False  # fail closed rather than grow without bound
            if self._seen.get(key, 0) > t:
                return False
            self._seen[key] = expires_at_ms
            return True

    def verify(self, *, method: str, url: str, headers: Mapping[str, Any]) -> WebBotAuthDecision:
        """Verify and decide. Never raises."""
        result = verify_web_bot_auth(
            method,
            url,
            headers,
            get_keys=self._cache.get_keys,
            now_ms=self._now(),
            skew_seconds=self._skew,
            max_lifetime_seconds=self._lifetime,
            claim_nonce=self._claim if self._reject else None,
        )
        return decide_web_bot_auth(result, allow=self._allow, block=self._block)

    def clear_cache(self) -> None:
        self._cache.clear()
