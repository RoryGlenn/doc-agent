"""Install Doc Agent for Copilot without replacing existing files or settings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
IGNORED_DIRS = {"node_modules", "__pycache__", "test-results", "playwright-report", ".cache"}


def install_files(source: Path, destination: Path, apply: bool = False) -> list[str]:
    """Preflight and copy the agent and skill, preserving unrelated files.

    Parameters
    ----------
    source : Path
        Package root containing .github/agents and .github/skills.
    destination : Path
        Destination .github or .copilot directory.
    apply : bool
        Apply an installation that has passed preflight; otherwise report only.

    Returns
    -------
    list[str]
        Relative file paths that need installation.

    Raises
    ------
    ValueError
        If the source is invalid or any destination file conflicts.
    OSError
        If filesystem operations fail. Newly created files are rolled back.
    """
    if destination.is_symlink():
        raise ValueError(f"Symlink destination is not supported: {destination}")
    # Resolve system aliases such as macOS /var, while retaining the selected root.
    destination = destination.parent.resolve() / destination.name
    source_root = source / ".github"
    entrypoints = (
        source_root / "agents/doc-agent.agent.md",
        source_root / "skills/doc-agent/SKILL.md",
    )
    if not all(path.is_file() and not path.is_symlink() for path in entrypoints):
        raise ValueError("Package is missing its agent or skill entrypoint")
    roots = [entrypoints[0], source_root / "skills/doc-agent"]
    files: list[tuple[Path, Path]] = []
    for root in roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            relative = path.relative_to(source_root)
            if any(part in IGNORED_DIRS for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError(f"Package contains a symlink: {relative}")
            if path.is_file() and path.suffix != ".pyc":
                files.append((path, destination / relative))
    pending: list[tuple[Path, Path]] = []
    conflicts = []
    for src, dest in files:
        for component in (dest, *dest.parents):
            if component.is_symlink():
                conflicts.append(f"Symlink destination is not supported: {component}")
                break
            if component.exists() and component != dest and not component.is_dir():
                conflicts.append(f"Parent is not a directory: {component}")
                break
        else:
            if dest.exists():
                if not dest.is_file() or src.read_bytes() != dest.read_bytes():
                    conflicts.append(f"Existing content differs: {dest}")
            else:
                pending.append((src, dest))
    if conflicts:
        raise ValueError("No files installed. Resolve conflicts first:\n" + "\n".join(conflicts))
    planned = [str(dest.relative_to(destination)) for _, dest in pending]
    if not apply:
        return planned
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for src, dest in pending:
            missing = []
            current = dest.parent
            while not current.exists():
                missing.append(current)
                current = current.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            # Exclusive creation prevents overwriting a file created after preflight.
            with dest.open("xb") as handle:
                created_files.append(dest)
                handle.write(src.read_bytes())
    except (OSError, ValueError):
        for path in reversed(created_files):
            path.unlink(missing_ok=True)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return planned


def main() -> int:
    """Run a dry-run or explicitly applied install.

    Returns
    -------
    int
        Zero for success, two for conflicts or invalid paths.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--user", action="store_true", help="Use ~/.copilot")
    scope.add_argument("--project", type=Path, help="Existing project root")
    parser.add_argument("--apply", action="store_true", help="Install after conflict checks")
    args = parser.parse_args()
    try:
        if args.user:
            destination = Path.home() / ".copilot"
        else:
            project = args.project.expanduser().absolute()
            if not project.is_dir():
                raise ValueError(f"Project directory does not exist: {project}")
            destination = project / ".github"
        planned = install_files(PACKAGE, destination, args.apply)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    mode = "Installed" if args.apply else "Would install"
    print(f"{mode} {len(planned)} new files under {destination}")
    for name in planned:
        print(f"  {name}")
    if not args.apply:
        print("Dry-run only. Add --apply to install. Identical existing files are left unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
