"""Behavior checks for non-destructive package discovery and installation."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import IO, Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> ModuleType:
    """Load a package script for direct, isolated behavior tests.

    Parameters
    ----------
    name : str
        Unique module name.
    path : Path
        Python script to load.

    Returns
    -------
    ModuleType
        Imported script module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_module("installer", ROOT / "install.py")
doctor = load_module("doctor", ROOT / ".github/skills/doc-agent/scripts/check_environment.py")


class InstallationTests(unittest.TestCase):
    """Ensure installation preserves unrelated and conflicting user content."""

    def setUp(self) -> None:
        """Create a minimal package and destination inside a temporary root."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source package"
        self.destination = self.root / "user home/.copilot"
        self.agent = self.source / ".github/agents/doc-agent.agent.md"
        self.skill = self.source / ".github/skills/doc-agent/SKILL.md"
        self.agent.parent.mkdir(parents=True)
        self.skill.parent.mkdir(parents=True)
        self.agent.write_text("agent\n")
        self.skill.write_text("skill\n")

    def test_dry_run_does_not_create_destination(self) -> None:
        """A dry-run reports files without making a directory."""
        self.assertEqual(len(installer.install_files(self.source, self.destination)), 2)
        self.assertFalse(self.destination.exists())

    def test_install_idempotent_and_preserves_unrelated_files(self) -> None:
        """Applying twice keeps prior content and unrelated settings unchanged."""
        self.destination.mkdir(parents=True)
        unrelated = self.destination / "settings.json"
        unrelated.write_text('{"custom": true}')
        first = installer.install_files(self.source, self.destination, True)
        mtimes = {p: p.stat().st_mtime_ns for p in self.destination.rglob("*") if p.is_file()}
        self.assertEqual(len(first), 2)
        self.assertEqual(installer.install_files(self.source, self.destination, True), [])
        self.assertEqual(unrelated.read_text(), '{"custom": true}')
        self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in mtimes})

    def test_conflict_prevents_any_partial_install(self) -> None:
        """A conflict late in the plan leaves earlier missing files unwritten."""
        conflicting = self.destination / "skills/doc-agent/SKILL.md"
        conflicting.parent.mkdir(parents=True)
        conflicting.write_text("user content")
        with self.assertRaises(ValueError):
            installer.install_files(self.source, self.destination, True)
        self.assertFalse((self.destination / "agents").exists())
        self.assertEqual(conflicting.read_text(), "user content")

    def test_symlink_destination_is_rejected(self) -> None:
        """A destination link cannot redirect writes outside the selected folder."""
        outside = self.root / "outside"
        outside.mkdir()
        self.destination.parent.mkdir(parents=True)
        self.destination.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install_files(self.source, self.destination, True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_parent_file_is_rejected(self) -> None:
        """A file occupying an expected directory fails before any writes."""
        self.destination.mkdir(parents=True)
        (self.destination / "skills").write_text("keep")
        with self.assertRaises(ValueError):
            installer.install_files(self.source, self.destination, True)
        self.assertFalse((self.destination / "agents").exists())

    def test_missing_source_is_rejected(self) -> None:
        """An incomplete archive cannot install only a role or only a skill."""
        self.skill.unlink()
        with self.assertRaises(ValueError):
            installer.install_files(self.source, self.destination, True)
        self.assertFalse(self.destination.exists())

    def test_dependencies_are_not_copied(self) -> None:
        """Installed Node dependencies and runtime caches stay out of installs."""
        dependency = self.skill.parent / "tooling/node_modules/package/private.txt"
        dependency.parent.mkdir(parents=True)
        dependency.write_text("exclude")
        installer.install_files(self.source, self.destination, True)
        self.assertFalse((self.destination / "skills/doc-agent/tooling/node_modules").exists())

    def test_source_symlink_is_rejected(self) -> None:
        """A packaged symlink cannot pull unrelated content into an installation."""
        outside = self.root / "private.txt"
        outside.write_text("not package content")
        (self.skill.parent / "linked.txt").symlink_to(outside)
        with self.assertRaises(ValueError):
            installer.install_files(self.source, self.destination, True)
        self.assertFalse(self.destination.exists())

    def test_write_failure_rolls_back_only_new_content(self) -> None:
        """A filesystem failure removes new files and preserves prior data."""
        self.destination.mkdir(parents=True)
        keep = self.destination / "keep.txt"
        keep.write_text("keep")
        original_open = Path.open

        def fail_second(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
            """Raise an I/O failure during the second destination write."""
            if path.name == "SKILL.md" and mode == "xb":
                raise OSError("simulated disk failure")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", fail_second), self.assertRaises(OSError):
            installer.install_files(self.source, self.destination, True)
        self.assertEqual(list(self.destination.iterdir()), [keep])
        self.assertEqual(keep.read_text(), "keep")


class DiscoveryTests(unittest.TestCase):
    """Check bounded, non-executing project inspection."""

    def setUp(self) -> None:
        """Make an isolated project for every test."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_commands_are_listed_without_executing_or_printing_bodies(self) -> None:
        """Only a safe script invocation is reported, never its arbitrary body."""
        sentinel = self.root / "MUST_NOT_EXIST"
        manifest = self.root / "package.json"
        manifest.write_text(
            json.dumps(
                {
                    "packageManager": "pnpm@10.0.0",
                    "scripts": {
                        "docs:build": f"touch {sentinel}; echo PRIVATE_TOKEN",
                        "start": "other",
                    },
                }
            )
        )
        before = manifest.read_bytes()
        report = doctor.inspect_project(self.root)
        self.assertFalse(sentinel.exists())
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(report["commands"][0]["argv"], ["pnpm", "run", "docs:build"])
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(report))

    def test_malformed_manifest_is_reported(self) -> None:
        """Bad JSON is a limitation, not a traceback or inferred command."""
        (self.root / "package.json").write_text("{invalid")
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"], [])
        self.assertTrue(report["warnings"])

    def test_wrong_manifest_shapes_are_reported(self) -> None:
        """Unexpected JSON types cannot crash command discovery."""
        for value in ([], {"scripts": []}, {"scripts": {"docs": None}}):
            with self.subTest(value=value):
                (self.root / "package.json").write_text(json.dumps(value))
                self.assertEqual(doctor.inspect_project(self.root)["commands"], [])

    def test_excluded_and_deep_directories_are_not_scanned(self) -> None:
        """Dependency caches and excessive depth do not inflate the inventory."""
        for name in ("node_modules/pkg", ".git/sub", "a/b/c/d"):
            folder = self.root / name
            folder.mkdir(parents=True)
            (folder / "package.json").write_text('{"scripts":{"docs":"anything"}}')
        self.assertEqual(doctor.inspect_project(self.root)["configs"], [])

    def test_linked_configuration_is_not_read(self) -> None:
        """A manifest symlink is identified and not parsed."""
        outside = self.root / "private.txt"
        outside.write_text('{"scripts":{"docs":"SECRET"}}')
        (self.root / "package.json").symlink_to(outside)
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"], [])
        self.assertIn("Skipped symlink", report["warnings"][0])

    def test_missing_optional_tools_do_not_fail(self) -> None:
        """Documentation work is still possible without optional validators."""
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.inspect_project(self.root)
        self.assertTrue(all(value is None for value in report["tools"].values()))

    def test_workspace_inherits_ancestor_package_manager(self) -> None:
        """A nested package uses the selected workspace's declared manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "packages/docs"
        child.mkdir(parents=True)
        (child / "package.json").write_text('{"scripts":{"docs:build":"build"}}')
        report = doctor.inspect_project(self.root)
        self.assertEqual(report["commands"][0]["argv"], ["yarn", "run", "docs:build"])

    def test_workspace_inherits_lockfile(self) -> None:
        """Lockfile evidence is inherited when no declaration exists."""
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: 9")
        child = self.root / "docs"
        child.mkdir()
        (child / "package.json").write_text('{"scripts":{"build":"build"}}')
        self.assertEqual(doctor.inspect_project(self.root)["commands"][0]["argv"][0], "pnpm")

    def test_nearest_declaration_wins(self) -> None:
        """An explicitly configured nested project keeps its own manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "docs"
        child.mkdir()
        (child / "package.json").write_text(
            '{"packageManager":"bun@1.0.0","scripts":{"build":"build"}}'
        )
        self.assertEqual(doctor.inspect_project(self.root)["commands"][0]["argv"][0], "bun")

    def test_manager_discovery_stays_inside_explicit_root(self) -> None:
        """An unrelated parent manifest is not used to guess a manager."""
        (self.root / "package.json").write_text('{"packageManager":"yarn@4.0.0"}')
        child = self.root / "selected-project"
        child.mkdir()
        (child / "package.json").write_text('{"scripts":{"build":"build"}}')
        self.assertIsNone(doctor.inspect_project(child)["commands"][0]["argv"])

    def test_conflicting_lockfiles_do_not_guess_manager(self) -> None:
        """Conflicting evidence is reported instead of choosing a tool arbitrarily."""
        (self.root / "yarn.lock").write_text("")
        (self.root / "package-lock.json").write_text("{}")
        (self.root / "package.json").write_text('{"scripts":{"build":"build"}}')
        command = doctor.inspect_project(self.root)["commands"][0]
        self.assertIsNone(command["argv"])
        self.assertIn("conflicting", command["package_manager_evidence"])

    def test_invalid_project_is_rejected(self) -> None:
        """A missing root returns a meaningful input error."""
        with self.assertRaises(ValueError):
            doctor.inspect_project(self.root / "missing")


if __name__ == "__main__":
    unittest.main()
