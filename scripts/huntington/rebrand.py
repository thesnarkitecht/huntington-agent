#!/usr/bin/env python3
r"""Re-runnable HUNTINGTON-AGENT rebrand of user-facing text.

Rewrites text inside Python string literals (never identifiers, comments or docstrings) and the
values of the locale YAML files:

- ``Hermes Agent``                        -> ``HUNTINGTON-AGENT``
- ``Nous Research`` / whole-word ``Nous`` -> ``HIP``
- whole-word ``Hermes``                   -> ``Huntington``
- a command hint ``hermes <sub>``, ``hermes --flag``, `` `hermes` `` -> ``huntington ...``
- the data directory: a ``.hermes`` path component (``~/.hermes``, ``.hermes/bin``) -> ``.huntington``,
  and on Windows ``%LOCALAPPDATA%\hermes`` -> ``%LOCALAPPDATA%\huntington`` (SOURCE_RULES)

The same path rule runs over the shell and PowerShell installers. Modules (``hermes_cli``), env vars
(``HERMES_HOME``), package names (``hermes-agent``), URLs (``NousResearch``, ``nousresearch.com``) and
lowercase ids (``nous``) are left alone. A literal that is exactly a command (``"hermes gateway run"``)
is left alone too: it may be executed. The ``hermes`` launcher keeps working next to ``huntington``.

Idempotent. ``scripts/huntington/sync-upstream.sh`` runs it after every upstream merge, and also on
both sides of a conflicted file, so a conflict that only the rebrand causes resolves itself.

    python scripts/huntington/rebrand.py            # rewrite the tree
    python scripts/huntington/rebrand.py --check    # exit 1 if anything would change
    python scripts/huntington/rebrand.py --stdin PATH   # rewrite stdin (as file PATH) to stdout
"""
from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PY_DIRS = ("hermes_cli", "agent", "gateway", "tools", "cron", "plugins", "acp_adapter", "tui_gateway",
           "providers", "tests", "pm", "hermes_platform", "scripts", "skills", "optional-skills", "evals")
SHELL_FILES = ("scripts/install.sh", "scripts/install.ps1", "scripts/install.cmd", "setup-hermes.sh",
               "setup-hermes.ps1", "activate", "activate.fish", "activate.ps1",
               # Install e2e drivers: they locate the checkout's launchers under .huntington/bin.
               "tests/install/e2e-assets/source-driver.sh", "tests/install/e2e-assets/source-driver.ps1")
PY_ROOT_GLOBS = ("*.py",)
YAML_GLOBS = ("locales/*.yaml",)
# Skill documents the agent reads and follows: their commands and paths must name this install.
MD_GLOBS = ("skills/**/*.md", "optional-skills/**/*.md")
SKIP_PARTS = {"__pycache__", "node_modules", ".venv", "web_dist"}
# The fork's own files: they already say what they mean, and its tests assert upstream names.
SKIP_FILES = {"hermes_cli/huntington.py", "tests/hermes_cli/test_huntington_policy.py", "conftest.py",
              "scripts/huntington/rebrand.py"}

_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<![\w.-])Hermes Agent(?![\w-])"), "HUNTINGTON-AGENT"),
    (re.compile(r"(?<![\w.-])Nous Research(?!\w)"), "HIP"),
    (re.compile(r"(?<![\w./-])Nous(?![\w])"), "HIP"),
    (re.compile(r"(?<![\w./-])Hermes(?![\w])"), "Huntington"),
    (re.compile(r"(?<![\w./~$\\-])(?<!setuidgid )hermes(?![ \t]+\w+=)(?=(?:[ \t]+(?:--?[a-z]|[a-z][a-z0-9-]*|\{)|`))"), "huntington"),
)
# Host-wide service identities (systemd units, launchd labels): HUNTINGTON-AGENT must not share
# them with an upstream Hermes install on the same machine, or each would adopt the other's service
# (the gateway then refuses the client with ``profile_mismatch``). Wire protocol names are shared
# with the web client and stay.
_SERVICE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<![\w.-])hermes-(gateway|serve|dashboard)(?!-ticket|-v1|-metrics|-loop|-command|r)"),
     r"huntington-\1"),
    (re.compile(r"(?<![\w-])ai\.hermes(?=[.*\"'`]|$)"), "ai.huntington"),
    # The same names written as a regex: ^hermes-(serve|dashboard)... in unit-name validators.
    (re.compile(r"(?<![\w.-])hermes-(?=\((?:\?:)?(?:serve|dashboard|gateway))"), "huntington-"),
)
_COMMAND_LITERAL = re.compile(r"^hermes(?:\s+[\w.:=/-]+)*$")
_PATH_RULE = (re.compile(r"(?<![\w-])\.hermes(?![\w-])"), ".huntington")
_WIN_PATH_RULE = (re.compile(r"(LOCALAPPDATA[%)}]?[\\/]+)hermes(?![\w-])"), r"\1huntington")
# Source shapes (Python, outside the string rules) of the install layout: the checkout directory
# <home>/hermes-agent -> <home>/huntington-agent and the Windows data root joined by argument.
_PY_SOURCE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r'(/\s*)"hermes-agent"(?=\s*[)/,\n])'), r'\1"huntington-agent"'),
    (re.compile(r'((?:local_appdata|LOCALAPPDATA"\])\s*,\s*)"hermes"(?=\s*[,)])'), r'\1"huntington"'),
    (re.compile(r'("huntington"\s*,\s*)"hermes-agent"(?=\s*[,)])'), r'\1"huntington-agent"'),
    # argparse program names are display text, never executed.
    (re.compile(r'(\bprog\s*=\s*)"hermes(?=[ "])'), r'\1"huntington'),
)
_SHELL_SOURCE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\$HERMES_HOME/hermes-agent\b"), "$HERMES_HOME/huntington-agent"),
    (re.compile(r"(HERMES_HOME|huntington)\\hermes-agent\b"), r"\1\\huntington-agent"),
    (re.compile(r"(Join-Path \$resolvedHome )'hermes-agent'"), r"\1'huntington-agent'"),
)
# Python source (not string-literal) spellings of the Windows default, per file.
SOURCE_RULES: dict[str, tuple[tuple[str, str], ...]] = {
    "hermes_constants.py": (('return base / ("hermes" + suffix)', 'return base / ("huntington" + suffix)'),),
    "pm/shell.py": (('ntpath.join(env["LOCALAPPDATA"], "hermes", "git")',
                     'ntpath.join(env["LOCALAPPDATA"], "huntington", "git")'),),
    "hermes_cli/gateway_windows.py": (('_TASK_NAME_DEFAULT = "Hermes_Gateway"', '_TASK_NAME_DEFAULT = "Huntington_Gateway"'),),
    # Exact command literals stay `hermes` (argv matchers); these three are shown to the user, or run
    # where pyproject publishes `huntington` beside `hermes`.
    "hermes_cli/config.py": (('_UPDATE_COMMAND_BY_METHOD.get(method, "hermes update")',
                              '_UPDATE_COMMAND_BY_METHOD.get(method, "huntington update")'),),
    "hermes_cli/web_routers/memory_providers.py": (('command = "hermes pm install"', 'command = "huntington pm install"'),),
    "hermes_cli/service_manager.py": (('gateway_cmd = "hermes gateway run --replace"',
                                       'gateway_cmd = "huntington gateway run --replace"'),),
    "scripts/install.sh": (
        ('"│             ☤ Hermes Agent Installer                    │"', '"│               ◆ HUNTINGTON-AGENT Installer              │"'),
        ('"│  An open source AI agent by Nous Research.              │"', '"│               A terminal AI agent by HIP.               │"'),
        ("run 'hermes setup' after install", "run 'huntington setup' after install"),
        ('install complete. Run: hermes"', 'install complete. Run: huntington"'),
    ),
    "scripts/install.ps1": (
        ('"|             * Hermes Agent Installer                    |"', '"|               * HUNTINGTON-AGENT Installer              |"'),
        ('"|  An open source AI agent by Nous Research.              |"', '"|               A terminal AI agent by HIP.               |"'),
        ('Run: hermes" }', 'Run: huntington" }'),
    ),
}


# Tests never execute a bare command literal; they assert on output that the rewritten code
# prints, so inside tests/ an exact `hermes <cmd>` literal is rebranded too (see rewrite_file_text).
_KEEP_COMMAND_LITERALS = True


def rewrite_text(text: str) -> str:
    if _KEEP_COMMAND_LITERALS and _COMMAND_LITERAL.match(text.strip()) and text.strip() == text:
        return text
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    return rewrite_paths(text)


def rewrite_paths(text: str) -> str:
    for pattern, replacement in (_PATH_RULE, _WIN_PATH_RULE, *_SERVICE_RULES):
        text = pattern.sub(replacement, text)
    return text


def _docstring_starts(source: str) -> set[tuple[int, int]]:
    """(line, col) of every docstring literal, which stays untouched."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    starts = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None) or []
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                starts.add((body[0].value.lineno, body[0].value.col_offset))
    return starts


def _string_body(token: str) -> tuple[str, str, str]:
    """Split a STRING token into (prefix+quote, body, quote)."""
    m = re.match(r"(?is)^([a-z]*)('''|\"\"\"|'|\")", token)
    if not m:
        return "", token, ""
    head = m.group(1) + m.group(2)
    quote = m.group(2)
    return head, token[len(head):len(token) - len(quote)], quote


def rewrite_python(source: str) -> str:
    edits_done = _rewrite_python_strings(source)
    return edits_done


def _rewrite_python_strings(source: str) -> str:
    docstrings = _docstring_starts(source)
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits: list[tuple[int, int, str]] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, SyntaxError):
        return source
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    for tok in tokens:
        if tok.type == tokenize.STRING:
            if tok.start in docstrings:
                continue
            head, body, quote = _string_body(tok.string)
            if "r" in head.lower() and not quote:
                continue
            new_body = rewrite_text(body)
            if new_body != body:
                start = offsets[tok.start[0] - 1] + tok.start[1]
                end = offsets[tok.end[0] - 1] + tok.end[1]
                edits.append((start, end, head + new_body + quote))
        elif fstring_middle is not None and tok.type == fstring_middle:
            start = offsets[tok.start[0] - 1] + tok.start[1]
            end = offsets[tok.end[0] - 1] + tok.end[1]
            # f"hermes {profile}auth add ...": the span stops before the replacement field, so the
            # command rule sees the `{` that follows only when it is passed along.
            follows = "{" if tok.string[-1:].isspace() and source[end:end + 1] == "{" else ""
            new = rewrite_text(tok.string + follows)
            new = new[:len(new) - len(follows)]
            if new != tok.string:
                # FSTRING_MIDDLE renders doubled braces as single ones; only rewrite brace-free spans.
                if source[start:end] == tok.string:
                    edits.append((start, end, new))
    for start, end, new in sorted(edits, reverse=True):
        source = source[:start] + new + source[end:]
    return source


def rewrite_yaml(source: str) -> str:
    out = []
    for line in source.splitlines(keepends=True):
        key, sep, value = line.partition(":")
        if sep and not line.lstrip().startswith("#"):
            out.append(key + sep + rewrite_text(value))
        else:
            out.append(rewrite_text(line) if line.startswith((" ", "\t", "-")) and not sep else line)
    return "".join(out)


def rewrite_file_text(rel: str, source: str) -> str:
    global _KEEP_COMMAND_LITERALS
    if rel in SKIP_FILES:
        return source
    _KEEP_COMMAND_LITERALS = not rel.startswith("tests/")
    for old, new in SOURCE_RULES.get(rel, ()):
        source = source.replace(old, new)
    if rel in SHELL_FILES:
        for pattern, replacement in _SHELL_SOURCE_RULES:
            source = pattern.sub(replacement, source)
        # Shell may execute a bare `hermes`, so only the capitalised wording and paths change there.
        for pattern, replacement in _RULES[:4]:
            source = pattern.sub(replacement, source)
        return rewrite_paths(source.replace("☤ HUNTINGTON-AGENT", "◆ HUNTINGTON-AGENT"))
    if rel.endswith(".py"):
        for pattern, replacement in _PY_SOURCE_RULES:
            source = pattern.sub(replacement, source)
        return rewrite_python(source)
    if rel.endswith(".md") and rel.startswith(("skills/", "optional-skills/")):
        return rewrite_text(source)
    if rel.endswith((".yaml", ".yml")) and rel.startswith("locales/"):
        return rewrite_yaml(source)
    return source


def targets() -> list[Path]:
    files: list[Path] = []
    for d in PY_DIRS:
        files += (ROOT / d).rglob("*.py")
    for g in PY_ROOT_GLOBS + YAML_GLOBS + MD_GLOBS:
        files += ROOT.glob(g)
    files += [ROOT / f for f in SHELL_FILES if (ROOT / f).is_file()]
    return sorted(f for f in files if not SKIP_PARTS & set(f.relative_to(ROOT).parts))


def main(argv: list[str]) -> int:
    if argv[:1] == ["--stdin"]:
        sys.stdout.write(rewrite_file_text(argv[1], sys.stdin.read()))
        return 0
    check = "--check" in argv
    changed = []
    for path in targets():
        rel = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new = rewrite_file_text(rel, source)
        if new != source:
            changed.append(rel)
            if not check:
                path.write_text(new, encoding="utf-8")
    if changed:
        print(f"{'would rewrite' if check else 'rewrote'} {len(changed)} files")
    return 1 if check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
