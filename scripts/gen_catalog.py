#!/usr/bin/env python3
"""Generate the long-tail Backend API / Platform API surface of ``atlas_backend``
from the public OpenAPI document.

Usage (from ``sdks/python``)::

    python3 scripts/gen_catalog.py            # regenerate from scripts/openapi.snapshot.json
    python3 scripts/gen_catalog.py --check    # exit 1 if the generated files are out of date
    python3 scripts/gen_catalog.py --report   # print what was generated

Writes (never edit by hand)::

    atlas_backend/catalog_models.py   TypedDicts for every request / response schema
    atlas_backend/_catalog.py         one namespace class per resource, one typed method
                                      per operation, ``iter_*`` cursor iterators
    atlas_backend/_acatalog.py        the async mirror (scripts/gen_async.py)

Which operations: every BAPI + PLATFORM operation whose ``METHOD path`` the
hand-written modules (every other ``atlas_backend/*.py``) do not already send.
Hand-written namespaces (``client.users`` ...) inherit the generated methods of
their resource, so ``client.users.<anything>`` works whether it was written by
hand or generated; the hand-written method wins on a name clash. The generator
adds the base class to the hand-written ``class X:`` line once (idempotent).

Published signatures are pinned: ``scripts/catalog_pins.json`` records the method
name of every generated operation, so a regeneration (or a smarter naming rule)
never renames a shipped method. New operations are added to the pins by the run.
``skip`` lists operations that do not belong in the SDK, each with a reason.

Type mapping: object with properties -> TypedDict (required keys required, the
rest optional; a key that is not a Python identifier uses the functional form),
enum / const -> Literal, anyOf / oneOf -> ``A | B``, array -> list[T], map ->
dict[str, T], anything open -> ``Any``. Wire names are kept (snake_case JSON).

Conventions: path parameters are positional, then ``body``; query parameters are
keyword-only; every write takes ``idempotency_key=``; operations that accept a
dry run take ``dry_run=``; list operations with a cursor get an ``iter_<name>``
generator over every page.
"""

from __future__ import annotations

import json
import keyword
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PKG = ROOT / "atlas_backend"
SNAPSHOT = HERE / "openapi.snapshot.json"
PINS_FILE = HERE / "catalog_pins.json"
GENERATED = {"_catalog.py", "_acatalog.py", "catalog_models.py", "aresources.py"}
METHODS = ("get", "post", "put", "patch", "delete")

sys.path.insert(0, str(HERE))
import gen_async  # noqa: E402

SPEC = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
SCHEMAS = SPEC["components"]["schemas"]
PINS = json.loads(PINS_FILE.read_text(encoding="utf-8")) if PINS_FILE.exists() else {"names": {}, "skip": {}}


# ── naming ────────────────────────────────────────────────────────────────────
def snake(s: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s)
    s = re.sub(r"[^0-9A-Za-z_]+", "_", s).strip("_").lower()
    return s or "x"


def pascal(s: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[^0-9A-Za-z]+", snake(s)) if p)


def ident(s: str) -> str:
    s = snake(s)
    if s[0].isdigit():
        s = "n_" + s
    return s + "_" if keyword.iskeyword(s) else s


def singular(w: str) -> str:
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith(("sses", "xes")):
        return w[:-2]
    if w.endswith(("ss", "us", "is")) or not w.endswith("s"):
        return w
    return w[:-1]


def plural_like(w: str) -> bool:
    return singular(w) != w


def doc(text: str, indent: int) -> str:
    text = " ".join((text or "").split()).replace("\\", "\\\\").replace('"""', "'''")
    if not text:
        return ""
    pad = " " * indent
    lines = textwrap.wrap(text, 96 - indent) or [text]
    if len(lines) == 1:
        return f'{pad}"""{lines[0]}"""\n'
    return f'{pad}"""' + f"\n{pad}".join(lines) + f'\n{pad}"""\n'


# ── schema -> type ────────────────────────────────────────────────────────────
class Models:
    def __init__(self) -> None:
        self.out: list[str] = []
        self.names: dict[str, str] = {}  # python name -> structural key
        self.by_key: dict[str, str] = {}  # inline structural key -> python name
        self.comp_done: dict[str, str] = {}

    def fresh(self, base: str, key: str) -> str:
        name, n = base, 2
        while name in self.names and self.names[name] != key:
            name, n = f"{base}{n}", n + 1
        self.names[name] = key
        return name

    def resolve(self, s: dict) -> dict:
        while "$ref" in s:
            s = SCHEMAS[s["$ref"].split("/")[-1]]
        return s

    def ty(self, s: dict | None, hint: str) -> str:
        if not s or not isinstance(s, dict):
            return "Any"
        if "$ref" in s:
            return self.comp(s["$ref"].split("/")[-1])
        if "allOf" in s:
            merged: dict = {"type": "object", "properties": {}, "required": []}
            for part in s["allOf"]:
                part = self.resolve(part)
                merged["properties"].update(part.get("properties", {}))
                merged["required"] += part.get("required", [])
            return self.obj(merged, hint)
        for k in ("anyOf", "oneOf"):
            if k in s:
                parts: list[str] = []
                for i, v in enumerate(s[k]):
                    t = self.ty(v, f"{hint}{i + 1}" if len(s[k]) > 1 else hint)
                    if t not in parts:
                        parts.append(t)
                return " | ".join(parts) if parts else "Any"
        if "enum" in s:
            vals = [v for v in s["enum"] if isinstance(v, (str, int, bool)) or v is None]
            if 0 < len(vals) <= 40 and len(vals) == len(s["enum"]):
                lit = "Literal[" + ", ".join(repr(v) for v in vals) + "]"
                return lit
        if "const" in s:
            v = s["const"]
            if isinstance(v, (str, int, bool)):
                return f"Literal[{v!r}]"
        t = s.get("type")
        if isinstance(t, list):
            parts = []
            for one in t:
                x = self.ty({**s, "type": one}, hint)
                if x not in parts:
                    parts.append(x)
            return " | ".join(parts)
        if t == "object" or (t is None and "properties" in s):
            return self.obj(s, hint)
        if t == "array":
            return f"list[{self.ty(s.get('items'), hint + 'Item')}]"
        return {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "null": "None",
        }.get(t or "", "Any")

    def comp(self, name: str) -> str:
        if name in self.comp_done:
            return self.comp_done[name]
        s = SCHEMAS[name]
        if s.get("type") == "object" and s.get("properties") or "allOf" in s:
            py = self.fresh(pascal(name), "comp:" + name)
            self.comp_done[name] = f"\x00{py}\x00"
            self.emit(py, s)
            return self.comp_done[name]
        # Not an object: inline its type (enum, array, scalar, union) under this name.
        out = self.ty(s, pascal(name))
        self.comp_done[name] = out
        return out

    def obj(self, s: dict, hint: str) -> str:
        props = s.get("properties")
        if not props:
            ap = s.get("additionalProperties")
            if isinstance(ap, dict) and ap:
                return f"dict[str, {self.ty(ap, hint + 'Value')}]"
            return "dict[str, Any]"
        key = json.dumps(s, sort_keys=True)
        if key in self.by_key:
            return self.by_key[key]
        py = self.fresh(pascal(hint), key)
        self.by_key[key] = f"\x00{py}\x00"
        self.emit(py, s)
        return self.by_key[key]

    def emit(self, py: str, s: dict) -> None:
        if "allOf" in s:
            props: dict = {}
            req: list = []
            for part in s["allOf"]:
                part = self.resolve(part)
                props.update(part.get("properties", {}))
                req += part.get("required", [])
            s = {"properties": props, "required": req, "description": s.get("description")}
        props = s.get("properties", {})
        required = set(s.get("required", []))
        fields = [
            (k, bare(self.ty(v, py + pascal(k))), (v or {}).get("description", ""))
            for k, v in props.items()
        ]
        if not all(re.fullmatch(r"[A-Za-z_]\w*", k) and not keyword.iskeyword(k) for k, *_ in fields):
            # shortcut: a key that is not an identifier forces the functional form, which cannot
            # mix required and optional keys, so every key is optional there.
            items = "".join(f"    {k!r}: {ty!r},\n" for k, ty, _ in fields)
            self.out.append(f"\n\n{py} = TypedDict(\n    {py!r},\n    {{\n{items}    }},\n    total=False,\n)\n")
            return
        req_f = [f for f in fields if f[0] in required]
        opt_f = [f for f in fields if f[0] not in required]
        text = ""
        base = "TypedDict"
        if req_f and opt_f:
            text += self.td(f"_{py}Required", req_f, "TypedDict", True, "")
            base = f"_{py}Required"
        elif req_f:
            self.out.append(self.td(py, req_f, "TypedDict", True, s.get("description") or ""))
            return
        text += self.td(py, opt_f, base, False, s.get("description") or "")
        self.out.append(text)

    @staticmethod
    def td(name: str, fields: list, base: str, total: bool, description: str) -> str:
        body = doc(description, 4)
        for k, ty, d in fields:
            first = " ".join(d.split())[:150]
            if first:
                body += f"    #: {first}\n"
            body += f"    {k}: {ty}\n"
        t = "" if total else ", total=False"
        body = body or "    pass\n"
        return f"\n\nclass {name}({base}{t}):\n{body}"


def bare(t: str) -> str:
    return t.replace("\x00", "")


def qual(t: str) -> str:
    return re.sub(r"\x00(\w+)\x00", r"cm.\1", t)


MODELS = Models()


# ── operations ────────────────────────────────────────────────────────────────
class Op:
    def __init__(self, method: str, path: str, o: dict) -> None:
        self.method, self.path, self.o = method.upper(), path, o
        self.platform = o.get("tags", [""])[0] == "PLATFORM"
        parts = path.split("/")[2:]
        if self.platform and parts[0] == "platform" and len(parts) > 1:
            parts = parts[1:]
        elif parts[0] == "migrations" and len(parts) > 1:
            parts = [parts[0] + "_" + parts[1]] + parts[2:]
        self.seg = snake(parts[0])
        self.rel = [(p[1:-1], True) if p.startswith("{") else (snake(p), False) for p in parts[1:]]

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    def ok_schema(self) -> tuple[dict | None, str | None]:
        for code, r in sorted(self.o.get("responses", {}).items()):
            if code.startswith("2"):
                content = r.get("content", {})
                if "application/json" in content:
                    return content["application/json"].get("schema"), None
                if content:
                    return None, next(iter(content))
        return None, None

    def is_list(self) -> bool:
        s, _ = self.ok_schema()
        if not s:
            return False
        s = MODELS.resolve(s)
        return s.get("type") == "array" or (
            "data" in s.get("properties", {}) and MODELS.resolve(s["properties"]["data"]).get("type") == "array"
        )

    def base_name(self) -> str:
        lits = [t for t, is_p in self.rel if not is_p]
        tail_param = bool(self.rel) and self.rel[-1][1]
        nouns = lits[:]
        if tail_param and nouns:
            nouns[-1] = singular(nouns[-1])
        m = self.method
        if m == "GET":
            verb = "get" if tail_param or not self.is_list() else "list"
            return "_".join([verb] + nouns)
        if m == "POST":
            if tail_param:
                return "_".join(["create"] + nouns)
            if not lits:
                return "create"
            if plural_like(lits[-1]):
                return "_".join(["create"] + lits[:-1] + [singular(lits[-1])])
            return "_".join([lits[-1]] + ([singular(lits[-2])] if len(lits) > 1 else []) + lits[:-2])
        verb = {"PUT": "set", "PATCH": "update", "DELETE": "delete"}[m]
        return "_".join([verb] + nouns)

    def pathparams(self, seg_sing: str) -> list[tuple[str, str]]:
        """[(wire name, python name)] in path order; ``id`` becomes ``<noun>_id``."""
        out: list[tuple[str, str]] = []
        prev = seg_sing
        for t, is_p in self.rel_full():
            if is_p:
                n = f"{singular(prev)}_id" if t == "id" else ident(t)
                out.append((t, n))
            else:
                prev = t
        return out

    def rel_full(self) -> list[tuple[str, bool]]:
        parts = self.path.split("/")[2:]
        out: list[tuple[str, bool]] = []
        for p in parts:
            out.append((p[1:-1], True) if p.startswith("{") else (snake(p), False))
        return out

    def query_params(self) -> list[dict]:
        return [p for p in self.o.get("parameters", []) if p.get("in") == "query"]


def handwritten_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    pat = re.compile(r'method="(GET|POST|PUT|PATCH|DELETE)",\s*path=f?"([^"]*)"')
    for f in sorted(PKG.glob("*.py")):
        if f.name in GENERATED:
            continue
        for m, p in pat.findall(f.read_text(encoding="utf-8")):
            pairs.add((m, re.sub(r"\{[^}]*\}", "{}", p.split("?")[0])))
    return pairs


def spec_ops() -> list[Op]:
    ops: list[Op] = []
    for path, item in SPEC["paths"].items():
        for m in METHODS:
            o = item.get(m)
            if o and o.get("tags", [""])[0] in ("BAPI", "PLATFORM"):
                ops.append(Op(m, path, o))
    return ops


def client_namespaces() -> tuple[dict[str, str], dict[str, str]]:
    """(attr -> hand-written class) for the BAPI client and for the Platform client."""
    src = (PKG / "_client.py").read_text(encoding="utf-8")
    i = src.index("class AtlasPlatformClient")
    j = src.index("class AsyncAtlasPlatformClient")
    k = src.index("class AsyncAtlasClient")
    pat = re.compile(r"self\.(\w+) = r\.(\w+)\(")
    return dict(pat.findall(src[:k])), dict(pat.findall(src[i:j]))


def class_methods() -> dict[str, set[str]]:
    src = (PKG / "resources.py").read_text(encoding="utf-8")
    out: dict[str, set[str]] = {}
    for chunk in re.split(r"(?m)^(?=class )", src)[1:]:
        name = re.match(r"class (\w+)", chunk).group(1)  # type: ignore[union-attr]
        out[name] = set(re.findall(r"(?m)^    def (\w+)", chunk)) | set(re.findall(r"self\.(\w+) = ", chunk))
    return out


# ── emission ──────────────────────────────────────────────────────────────────
def py_param_names(names: list[str], taken: set[str]) -> list[str]:
    out = []
    for n in names:
        n = ident(n)
        while n in taken:
            n += "_"
        taken.add(n)
        out.append(n)
    return out


def nullable_patch(op: Op, schema: dict | None) -> dict | None:
    """A PATCH body may send an explicit ``null`` to clear a field (the API's null-clears convention);
    an unset key is still omitted from the request. Applies to the body's own optional properties."""
    if op.method != "PATCH" or not schema:
        return schema
    s = MODELS.resolve(schema)
    props = s.get("properties")
    if s.get("type") != "object" or not props:
        return schema
    req = set(s.get("required", []))
    out = {**s, "properties": {
        k: (v if k in req or "null" in json.dumps(v.get("type", "")) or v.get("type") is None and not v.get("properties") and "enum" not in v and "$ref" not in v
            else {"anyOf": [v, {"type": "null"}]})
        for k, v in props.items()
    }}
    return out


def render(op: Op, name: str, seg_sing: str) -> tuple[str, str | None]:
    """The method source, plus the iterator's source when the op pages."""
    taken = {"self", "body", "dry_run", "idempotency_key", "content", "content_type"}
    pp = op.pathparams(seg_sing)
    pnames = py_param_names([n for _, n in pp], taken)
    pmap = dict(zip((w for w, _ in pp), pnames))
    # Path literal: segments keep their wire spelling; params become encoded f-string slots.
    path = "/" + "/".join(
        f"{{_enc({pmap[p[1:-1]]})}}" if p.startswith("{") else p for p in op.path.split("/")[1:]
    )
    dry = "x-atlas-dry-run" in op.o
    qs = [p for p in op.query_params() if not (dry and p["name"] == "dry_run")]
    qnames = py_param_names([p["name"] for p in qs], taken)
    hint = pascal(re.sub(r"^(get|post|put|patch|delete)_v1_", r"\1_", op.o["operationId"]))
    qp = [
        (n, qual(MODELS.ty(p.get("schema"), hint + pascal(p["name"]))), bool(p.get("required")), p["name"])
        for n, p in zip(qnames, qs)
    ]
    rb = op.o.get("requestBody", {}).get("content", {})
    body_t = raw_in = None
    if "application/json" in rb:
        body_t = qual(MODELS.ty(nullable_patch(op, rb["application/json"].get("schema")), hint + "Body"))
    elif rb:
        raw_in = next(iter(rb))
    body_required = bool(op.o.get("requestBody", {}).get("required"))
    schema, raw_out = op.ok_schema()
    ret = qual(MODELS.ty(schema, hint + "Response")) if schema else ("str" if raw_out else "Any")

    sig = ["self"] + [f"{n}: str" for n in pnames]
    if body_t is not None:
        sig.append(f"body: {body_t}" if body_required else f"body: {body_t} | None = None")
    if raw_in:
        sig += ["content: bytes", f"content_type: str = {raw_in!r}"]

    def kwargs(skip: str | None) -> list[str]:
        out = [f"{n}: {t}" for n, t, req, _ in qp if req and n != skip]
        out += [f"{n}: {t} | None = None" for n, t, req, _ in qp if not req and n != skip]
        return out

    kw = kwargs(None)
    if dry:
        kw.append("dry_run: bool = False")
    write = op.method != "GET"
    if write:
        kw.append("idempotency_key: str | None = None")
    all_sig = sig + (["*"] + kw if kw else [])
    summary = op.o.get("summary") or op.o.get("description") or ""
    head = f"    def {name}(\n        " + ",\n        ".join(all_sig) + f",\n    ) -> {ret}:\n"
    fp = "f" if "{_enc(" in path else ""
    call = f'        return self._t.request(\n            method="{op.method}",\n            path={fp}"{path}",\n'
    qitems = [f"{wire!r}: {n}" for n, _, _, wire in qp]
    if dry:
        qitems.append("'dry_run': True if dry_run else None")
    if qitems:
        call += "            query=_qd({" + ", ".join(qitems) + "}),\n"
    if body_t is not None:
        call += "            body=body,\n"
    if raw_in:
        call += "            content=content,\n            content_type=content_type,\n"
    if write:
        call += "            idempotency_key=idempotency_key,\n"
    if raw_out:
        call += "            raw=True,\n"
    call += "        )\n"
    method_src = head + doc(summary, 8) + call

    iter_src = None
    cursor = next((n for n, _, _, wire in qp if wire == "starting_after"), None)
    if op.method == "GET" and cursor and op.is_list() and not dry:
        item_t = "Any"
        rs = MODELS.resolve(schema or {})
        dt = rs.get("properties", {}).get("data") if rs.get("type") == "object" else None
        if dt:
            inner = qual(MODELS.ty(dt, hint + "Data"))
            item_t = inner[5:-1] if inner.startswith("list[") else "Any"
        isig = ["self"] + [f"{n}: str" for n in pnames] + ["*"] + kwargs(cursor)
        args = ", ".join(pnames + [f"{n}={n}" for n, _, _, _ in qp if n != cursor] + [f"{cursor}=cursor"])
        iter_src = (
            f"    def iter_{name}(\n        " + ",\n        ".join(isig) + f",\n    ) -> Iterator[{item_t}]:\n"
            + doc(f"Every item of :meth:`{name}`, following the cursor page by page.", 8)
            + "        cursor: str | None = None\n        while True:\n"
            + f"            page = self.{name}({args})\n"
            + '            for item in page.get("data", []):\n                yield item\n'
            + '            cursor = page.get("next_cursor")\n'
            + '            if not page.get("has_more") or not cursor:\n                return\n'
        )
    return method_src, iter_src


def pascal_ns(seg: str, platform: bool) -> str:
    return ("Platform" if platform else "") + pascal(seg)


def build() -> dict[str, str]:
    bapi_attrs, plat_attrs = client_namespaces()
    methods = class_methods()
    hw = handwritten_pairs()
    names: dict[str, str] = dict(PINS.get("names", {}))
    skip = PINS.get("skip", {})
    todo = [o for o in spec_ops() if (o.method, re.sub(r"\{[^}]*\}", "{}", o.path)) not in hw or o.key in PINS.get("generate_despite_handwritten", [])]
    todo = [o for o in todo if o.key not in skip]
    if "--report" in sys.argv:
        lits = {re.sub(r"\{[^}]*\}", "{}", p.split("?")[0]) for f in PKG.glob("*.py") if f.name not in GENERATED
                for p in re.findall(r'"(/v1/[^"]*)"', f.read_text(encoding="utf-8"))}
        hidden = [o for o in todo if re.sub(r"\{[^}]*\}", "{}", o.path) in lits]
        print(f"{len(hidden)} generated operations share a path with a hand-written one (hidden from the path-only drift gate)")
    # Operations the hand-written modules already send keep their methods; their request,
    # response and query shapes are still emitted so every field of the API has a type here.
    done = {o.key for o in todo}
    for o in spec_ops():
        if o.key not in done:
            hint = pascal(re.sub(r"^(get|post|put|patch|delete)_v1_", r"\1_", o.o["operationId"]))
            rb = o.o.get("requestBody", {}).get("content", {}).get("application/json")
            if rb:
                MODELS.ty(rb.get("schema"), hint + "Body")
            sch, _ = o.ok_schema()
            if sch:
                MODELS.ty(sch, hint + "Response")
            qp = o.query_params()
            if qp:
                MODELS.ty(
                    {
                        "type": "object",
                        "properties": {p["name"]: p.get("schema") or {} for p in qp},
                        "required": [p["name"] for p in qp if p.get("required")],
                    },
                    hint + "Query",
                )
    groups: dict[tuple[bool, str], list[Op]] = {}
    for o in todo:
        groups.setdefault((o.platform, o.seg), []).append(o)

    classes: list[str] = []
    wiring_b: list[tuple[str, str]] = []
    wiring_p: list[tuple[str, str]] = []
    links: dict[str, str] = {}  # hand-written class -> generated class name
    for (platform, seg), ops in sorted(groups.items()):
        attrs = plat_attrs if platform else bapi_attrs
        cls = pascal_ns(seg, platform)
        hw_cls = attrs.get(seg)
        taken = set(methods.get(hw_cls, set())) if hw_cls else set()
        seg_sing = singular(seg)
        body = ""
        for op in sorted(ops, key=lambda o: (o.path, o.method)):
            n = base = names.get(op.key) or ident(op.base_name())
            i = 2
            while n in taken:  # a clash with a hand-written / earlier method never overrides it
                n, i = f"{base}_{i}", i + 1
            names.setdefault(op.key, n)
            taken.add(n)
            m_src, i_src = render(op, n, seg_sing)
            body += "\n" + m_src
            if i_src:
                it = f"iter_{n}"
                if it not in taken:
                    taken.add(it)
                    body += "\n" + i_src
        classes.append(
            f"\n\nclass {cls}:\n    _t: _SyncTransport\n\n"
            f"    def __init__(self, transport: _SyncTransport) -> None:\n        self._t = transport\n{body}"
        )
        if hw_cls:
            links[hw_cls] = cls
        else:
            (wiring_p if platform else wiring_b).append((seg, cls))

    def mixin(name: str, wires: list[tuple[str, str]]) -> str:
        decl = "".join(f"    {a}: {c}\n" for a, c in wires)
        wire = "".join(f"        self.{a} = {c}(transport)\n" for a, c in wires) or "        pass\n"
        return f"\n\nclass {name}:\n{doc('Namespaces for the resources the hand-written client has no attribute for.', 4)}{decl}\n    def _wire_catalog(self, transport: _SyncTransport) -> None:\n{wire}"

    catalog = (
        '"""Generated Backend API / Platform API operations (do not edit).\n\n'
        "Produced by ``scripts/gen_catalog.py`` from the OpenAPI snapshot; the async mirror is\n"
        "``_acatalog.py``. Hand-written resources inherit the class of the same name here.\n"
        '"""\n\nfrom __future__ import annotations\n\nfrom collections.abc import Iterator\n'
        "from typing import Any, Literal\n\nfrom . import catalog_models as cm\n"
        "from ._transport import _SyncTransport\nfrom ._util import _enc, _qd\n"
        + "".join(classes)
        + mixin("CatalogClient", wiring_b)
        + mixin("CatalogPlatformClient", wiring_p)
    )
    models = (
        '"""Typed request / response shapes for the generated operations (do not edit).\n\n'
        "Produced by ``scripts/gen_catalog.py``. Wire names are kept as-is (snake_case JSON).\n"
        '"""\n\nfrom __future__ import annotations\n\nfrom typing import Any, Literal, TypedDict\n'
        + "".join(MODELS.out)
    )
    PINS["names"] = dict(sorted(names.items()))
    return {
        "_catalog.py": catalog,
        "catalog_models.py": models,
        "_acatalog.py": gen_async.convert_catalog(catalog),
        "_links": json.dumps(links),
    }


def link_resources(links: dict[str, str]) -> bool:
    """Make each hand-written class inherit its generated resource (idempotent)."""
    p = PKG / "resources.py"
    s = p.read_text(encoding="utf-8")
    orig = s
    for hw, gen in links.items():
        s = re.sub(rf"(?m)^class {hw}:", f"class {hw}(c.{gen}):", s)
    if "from . import _catalog as c" not in s:
        s = s.replace("from . import models as m\n", "from . import _catalog as c\nfrom . import models as m\n", 1)
    if s != orig:
        p.write_bytes((s).encode("utf-8"))
    return s != orig


def main() -> None:
    check = "--check" in sys.argv
    pins_before = PINS_FILE.read_text(encoding="utf-8") if PINS_FILE.exists() else ""
    if not check:
        # The links must exist before the async mirror is derived from resources.py.
        pass
    out = build()
    links = json.loads(out.pop("_links"))
    pins_text = json.dumps(PINS, indent=1, sort_keys=True) + "\n"
    files = {PKG / k: v for k, v in out.items()}
    if check:
        bad = [str(p) for p, v in files.items() if not p.exists() or p.read_text(encoding="utf-8") != v]
        if pins_text != pins_before:
            bad.append(str(PINS_FILE))
        if bad:
            print("out of date: " + ", ".join(bad) + "\nrun: python3 scripts/gen_catalog.py")
            sys.exit(1)
        return
    for p, v in files.items():
        p.write_bytes((v).encode("utf-8"))
    PINS_FILE.write_bytes((pins_text).encode("utf-8"))
    if link_resources(links):
        print("linked hand-written classes to the generated catalog; run python3 scripts/gen_async.py")
    gen_async.main()
    if "--report" in sys.argv:
        print(f"{len(PINS['names'])} generated operations, {len(MODELS.out)} models")


if __name__ == "__main__":
    main()
