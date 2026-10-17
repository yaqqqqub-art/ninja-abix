"""modsec.py - MOD SECURITY (pure python, game ar security server duitai use kore).

  hash_mod(folder)   : mod folder er SHA-256 (sob file)
  check_mod(folder)  : file security + code scan -> (manifest, problems)
Mod = ekta folder:  mod.json  +  main.py  (+ png/jpg/txt/json)
"""
import ast
import hashlib
import json
import os
import re

ALLOWED_IMPORTS = {"math", "random", "time", "colorsys", "itertools", "functools", "collections", "string"}
ALLOWED_EXT = {".py", ".json", ".txt", ".md", ".png", ".jpg", ".jpeg"}
MAX_FILE = 300 * 1024
MAX_FILES = 60
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\- ]{0,31}$")

BAD_NAMES = {"eval", "exec", "compile", "open", "__import__", "input", "breakpoint", "getattr", "setattr",
             "delattr", "vars", "globals", "locals", "dir", "type", "help", "exit", "quit", "memoryview",
             "classmethod", "staticmethod", "property"}
BAD_ATTRS = {"format", "format_map", "mro", "gi_frame", "gi_code", "f_globals", "f_locals", "f_back",
             "f_builtins", "cr_frame", "tb_frame", "ag_frame"}


def iter_files(folder):
    out = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            out.append((os.path.relpath(full, folder).replace(os.sep, "/"), full))
    return sorted(out)


def hash_mod(folder):
    h = hashlib.sha256()
    for rel, full in iter_files(folder):
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        with open(full, "rb") as f:
            h.update(f.read())
        h.update(b"\0")
    return h.hexdigest()


def scan_source(src, filename="main.py"):
    """Code scan: danger kisu thakle problem list e ashe."""
    probs = []
    try:
        tree = ast.parse(src, filename)
    except SyntaxError as e:
        return [f"{filename}: syntax error line {e.lineno}"]

    def bad(node, msg):
        probs.append(f"{filename}:{getattr(node, 'lineno', '?')} {msg}")

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    bad(n, f"import '{a.name}' not allowed")
        elif isinstance(n, ast.ImportFrom):
            if n.level or not n.module or n.module.split(".")[0] not in ALLOWED_IMPORTS:
                bad(n, f"import from '{n.module}' not allowed")
        elif isinstance(n, ast.Name):
            if n.id in BAD_NAMES or (n.id.startswith("__") and n.id != "__name__"):
                bad(n, f"'{n.id}' not allowed")
        elif isinstance(n, ast.Attribute):
            if n.attr.startswith("__") or n.attr in BAD_ATTRS:
                bad(n, f".{n.attr} not allowed")
        elif isinstance(n, ast.keyword):
            if n.arg and n.arg.startswith("__"):
                bad(n, "dunder keyword not allowed")
        elif isinstance(n, ast.While):
            bad(n, "while loop not allowed (use for)")
        elif isinstance(n, (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor, ast.AsyncWith)):
            bad(n, "async not allowed")
        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            r = n.right
            if not (isinstance(r, ast.Constant) and isinstance(r.value, (int, float)) and abs(r.value) <= 64):
                bad(n, "power ** only with small constant")
    return probs


def check_mod(folder):
    """-> (manifest dict | None, problems list)"""
    probs = []
    files = iter_files(folder)
    if not files:
        return None, ["empty folder"]
    if len(files) > MAX_FILES:
        probs.append(f"too many files ({len(files)} > {MAX_FILES})")
    real_root = os.path.realpath(folder)
    for rel, full in files:
        if os.path.islink(full) or not os.path.realpath(full).startswith(real_root):
            probs.append(f"{rel}: link/outside file")
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext not in ALLOWED_EXT:
            probs.append(f"{rel}: file type '{ext or 'none'}' not allowed")
            continue
        try:
            if os.path.getsize(full) > MAX_FILE:
                probs.append(f"{rel}: file too big")
                continue
        except OSError:
            probs.append(f"{rel}: unreadable")
            continue
        if ext == ".py":
            try:
                with open(full, "r", encoding="utf-8") as f:
                    probs += scan_source(f.read(), rel)
            except (OSError, UnicodeDecodeError):
                probs.append(f"{rel}: not utf-8 text")
    manifest = None
    mp = os.path.join(folder, "mod.json")
    try:
        with open(mp, "r", encoding="utf-8") as f:
            m = json.load(f)
        name = str(m.get("name", ""))
        entry = str(m.get("entry", "main.py"))
        if not NAME_RE.match(name):
            probs.append("mod.json: bad 'name' (letters/numbers/space, max 32)")
        if os.path.basename(entry) != entry or not entry.endswith(".py") or not os.path.isfile(os.path.join(folder, entry)):
            probs.append("mod.json: bad 'entry' (must be a .py file in the mod folder)")
        manifest = {"name": name, "version": str(m.get("version", "1.0"))[:16],
                    "author": str(m.get("author", "?"))[:32], "entry": entry,
                    "description": str(m.get("description", ""))[:120]}
    except (OSError, ValueError, AttributeError):
        probs.append("mod.json missing or broken")
    return manifest, probs
