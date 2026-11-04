"""Composes a Python project from the base (`python/`) and one or more modules (`fastapi/`, `taskiq/`).

    python3 scripts/compose.py <dest> <module>[:<package>]...

    python3 scripts/compose.py /tmp/shop fastapi taskiq            # api/ and worker/
    python3 scripts/compose.py /tmp/shop fastapi fastapi:hooks     # two APIs from one module: api/ and hooks/

Kanboto applies the same algorithm when it scaffolds a repository; keep both in step. Standard library only.

1. Copy `python/` into `<dest>`, which must not exist or be empty (caches, `.venv` and `.env` left out).
2. For each `<module>[:<package>]`, in order, read `<module>/module.toml`:
   - `package`: the module's package; it is copied as `<package>` when one is given, under its own name
     otherwise. The target name must be a Python identifier, not taken in `<dest>`, and not `common`,
     `migrations` or `tests`.
   - copy `<module>/<package>/` to `<dest>/<target>/` and `<module>/tests/<package>/` to
     `<dest>/tests/<target>/`;
   - `files`: other paths of the module, copied as is (an existing path is an error); `{package}` in a path
     stands for the module's package at the source and for the target name at the destination;
   - `extra`: appended to the exec-form `RUN ["uv", "sync", ...]` line of the Dockerfile as
     `"--extra", "<extra>"`, once per extra;
   - `[dockerfile].copy`: one `COPY <path> ./<path>` line each, inserted after the last `COPY` line before
     the final `FROM` (the build stage), after the lines of the previous modules;
   - `[dockerfile].cmd`: the `CMD` line, set by the first module only (Kubernetes sets each component's);
   - `[env]`: `KEY=value` lines appended to `.env.example`, unless the key is already there;
   - `[rename].files`: globs, relative to `<dest>`, of the only files where the package name is rewritten,
     when the target name differs: see `rename()`.
   In `copy`, `cmd` and `[rename].files`, `{package}` stands for the target name. A module can be added
   several times under different names: its package keeps its state (settings, metrics registry, loggers)
   to itself.

A module's package imports itself relatively and never spells its own name, so renaming its folder is enough;
its tests import it by name, hence the rewrite.
"""

import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "python"
IGNORE = shutil.ignore_patterns("__pycache__", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".env")
RESERVED = {"common", "migrations", "tests"}


def rename(text: str, old: str, new: str) -> str:
    """Rewrites the package name `old` as `new` where it names the module, never elsewhere:
    - an absolute import at the start of a line: `from api import x`, `from api.main import y`, `import api`;
    - a module path in a string: `"api"`, `"api.main:create_app"`, `"api.access"` (a logger);
    - a command line: `python -m api`.
    `from worker import worker` becomes `from jobs import worker`: the imported submodule keeps its name."""
    name = re.escape(old)
    text = re.sub(rf"^(\s*(?:from|import)\s+){name}(?=[.\s,]|$)", rf"\g<1>{new}", text, flags=re.MULTILINE)
    text = re.sub(rf"(?<=[\"']){name}(?=[.:\"'])", new, text)
    return re.sub(rf"(?<=-m ){name}\b", new, text)


def copy_base(dest: Path) -> None:
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"{dest} is not empty")
    shutil.copytree(BASE, dest, ignore=IGNORE, dirs_exist_ok=True)


def edit_dockerfile(path: Path, extra: str, copies: list[str], cmd: list[str] | None) -> None:
    lines = path.read_text().splitlines()
    run = next(i for i, line in enumerate(lines) if line.startswith('RUN ["uv", "sync"'))
    args = json.loads(lines[run].removeprefix("RUN "))
    if ("--extra", extra) not in zip(args, args[1:], strict=False):
        args += ["--extra", extra]
    lines[run] = "RUN " + json.dumps(args)
    runtime = max(i for i, line in enumerate(lines) if line.startswith("FROM "))
    last_copy = max(i for i, line in enumerate(lines[:runtime]) if line.startswith("COPY "))
    lines[last_copy + 1 : last_copy + 1] = [f"COPY {c} ./{c}" for c in copies]
    if cmd is not None:
        at = next(i for i, line in enumerate(lines) if line.startswith("CMD "))
        lines[at] = "CMD " + json.dumps(cmd)
    path.write_text("\n".join(lines) + "\n")


def add_env(path: Path, env: dict[str, str]) -> None:
    text = path.read_text()
    known = set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=", text, flags=re.MULTILINE))
    added = [f"{key}={value}" for key, value in env.items() if key not in known]
    if added:
        path.write_text(text + ("" if text.endswith("\n") or not text else "\n") + "\n".join(added) + "\n")


def add_module(dest: Path, spec: str, first: bool) -> None:
    module, _, target = spec.partition(":")
    manifest: dict[str, Any] = tomllib.loads((ROOT / module / "module.toml").read_text())
    source: str = manifest["package"]
    target = target or source
    if not target.isidentifier() or target in RESERVED or (dest / target).exists():
        sys.exit(f"{spec}: {target!r} is not a free package name")

    def fill(value: str) -> str:
        return value.replace("{package}", target)

    shutil.copytree(ROOT / module / source, dest / target, ignore=IGNORE)
    shutil.copytree(ROOT / module / "tests" / source, dest / "tests" / target, ignore=IGNORE)
    for name in manifest.get("files", []):
        to = dest / fill(name)
        if to.exists():
            sys.exit(f"{spec}: {fill(name)} already exists in {dest}")
        to.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / module / name.replace("{package}", source), to)

    docker = manifest.get("dockerfile", {})
    cmd = [fill(arg) for arg in docker["cmd"]] if first and "cmd" in docker else None
    edit_dockerfile(dest / "Dockerfile", manifest["extra"], [fill(c) for c in docker.get("copy", [])], cmd)
    add_env(dest / ".env.example", manifest.get("env", {}))

    if target != source:
        for pattern in manifest.get("rename", {}).get("files", []):
            for path in sorted(dest.glob(fill(pattern))):
                path.write_text(rename(path.read_text(), source, target))


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        sys.exit(__doc__)
    dest = Path(argv[0]).resolve()
    copy_base(dest)
    for index, spec in enumerate(argv[1:]):
        add_module(dest, spec, first=index == 0)
    print(f"composed {dest}: {', '.join(argv[1:])}")


if __name__ == "__main__":
    main(sys.argv[1:])
