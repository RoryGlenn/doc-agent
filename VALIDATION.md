# Validation record — 26 September 2026

This records validation of the initial Copilot package before repository publication. That package contained 31 reviewed source/configuration files plus this record. Repository preparation subsequently added `.gitignore` and adjusted the README and this introduction for public use. The checks below describe the tested package; later repository changes should receive their own validation.

## Result

Independent review found no remaining material issues. All **41 distinct independent verification checks** passed after corrections, including **21 Python unit tests**, clean dependency installation, and positive/negative validator cases. A real GitHub Copilot CLI run also loaded the installed agent/skill and completed a reference-writing fixture.

The agent and skill were installed under the user's personal `~/.copilot/agents/` and `~/.copilot/skills/` directories. Their bytes match this package. Existing VS Code settings, Copilot settings/configuration, and the previous Codex Doc Agent were checked by hash and remained unchanged.

## Commands and observed results

Run package commands from the extracted package root. Optional-tool paths refer to `.github/skills/doc-agent/tooling`; actual verification used isolated clean copies and scratch tool installations.

| Check | Command or observation | Result |
| --- | --- | --- |
| Python behavior | `python3 -m unittest discover -s tests -v` | 21 tests passed |
| Python lint | `ruff check install.py .github/skills/doc-agent/scripts tests` | Passed |
| Python formatting | `ruff format --check install.py .github/skills/doc-agent/scripts tests` | Passed |
| Python types | `mypy` | No issues in two production scripts |
| Environment discovery | `python3 .github/skills/doc-agent/scripts/check_environment.py --project . --json` | Valid report; discovered scripts were not executed |
| Dependency reproducibility | `npm ci --prefix .github/skills/doc-agent/tooling` | 92 packages installed from lockfile; audit reported zero vulnerabilities at test time |
| Markdown | Documented `markdownlint-cli2-bin.mjs` command | Valid fixture passed; bad headings failed; 11 production Markdown files had zero issues |
| Vale | `vale --config <tooling>/.vale.ini --output=JSON <fixture.md>` | Three intended suggestions; inline code preserved; exit 0 as expected for suggestions |
| Links | `lychee --config <tooling>/lychee.toml --offline -- <files>` | Valid links passed; missing file/anchor failed; package local links passed |
| Browser | `DOC_AGENT_BASE_URL=<localhost-fixture> npm --prefix <tooling> run test:site` | Accessible fixture passed; unlabeled-button fixture failed with `button-name` |
| Browser evidence | Files under each Playwright test output directory | Real PNG and axe JSON persisted on both pass and fail; screenshots visually inspected |
| Installer | User/project dry-run, apply, repeat apply, conflict and I/O-failure cases | Correct files installed; conflicts stopped before writes; repeat apply preserved bytes/mtimes; new files rolled back after simulated failure |
| Package structure | YAML frontmatter, JSON/TOML parsing, local reference resolution | Passed |
| Copilot discovery | `copilot skill list` from outside the package directory | Listed `doc-agent` as a personal skill |

The initial checks identified and corrected a Markdown command that invoked a library instead of the executable, browser attachments that were not persisted, and incorrect package-manager selection in nested workspaces. Unit tests now cover ancestor inheritance, nearest overrides, conflicting evidence, and project boundaries. Package Markdown was then normalized to its included formatting rules.

## Copilot behavior evidence

The installed custom role was invoked with the existing Copilot CLI configuration. The test restricted tools to file viewing and explicitly denied shell and write operations:

```sh
copilot --agent doc-agent --available-tools=view \
  --deny-tool=write --deny-tool=shell --disable-builtin-mcps \
  --no-remote-export --add-dir "$HOME/.copilot/skills/doc-agent" \
  --silent --prompt '<read the installed skill and supplied contract; produce a complete reference>'
```

The fixture supplied four parameters with types, defaults, a numeric range, and success/error responses. The final result retained all four parameters and their supported details, left unspecified validation/behavior unasserted, and identified the installed skill and content-pattern reference it read. No live API, real user data, or human usability test was involved.

The first CLI attempt resolved the role's relative skill link from the terminal directory. The agent definition now explicitly gives personal/project locations and says to resolve the link from the agent file. The verified run supplied the correct installed skill path explicitly. A subsequent draft inferred effects from parameter names; a focused instruction correction now requires unsupported effects and constraints to remain unspecified. The final rerun followed that rule.

## Tested environment and limits

- macOS arm64; installed VS Code **1.137.0**, bundled Copilot Chat **0.65.0**; Copilot CLI **1.0.69-2**.
- Python validation environment **3.14.7**, Ruff **0.16.9**, mypy **2.3.1**; Node **26.4.0**.
- Vale **3.23.0**, Lychee **0.24.2**, markdownlint-cli2 **0.23.3**, Playwright **1.63.0**, axe Playwright integration **4.13.0**.
- The schema and standard personal/project locations were checked against installed app metadata/source and official VS Code documentation. Live selection and skill loading inside the VS Code UI remain **unverified** because native UI control repeatedly timed out. The successful native model run was in Copilot CLI.
- Browser checks used controlled localhost fixtures. External HTTP link checks were not counted as passed; an exploratory public-site check timed out.
- Ubuntu and Windows execution were not performed. The scripts use portable Python paths and require Python 3.11+, but cross-platform behavior still needs host testing.
- Optional validators were tested in scratch environments. Their binaries, browsers, and `node_modules` are not bundled or installed globally; the package includes working configurations, pinned Node dependencies, and explicit setup commands.
- Passing these checks establishes the observed fixture behavior, not universal correctness, full accessibility compliance, or human understanding for every future document.

## First use

Open a new Copilot session in VS Code and select **Doc Agent** from the agent dropdown, or inspect it under **Configure Chat → Agents**. The skill should also be available under **Skills** and as `/doc-agent`. The README describes personal and project installation and the optional checks.
