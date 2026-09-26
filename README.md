# Doc Agent for VS Code Copilot

Write and maintain documentation that helps its intended reader understand and succeed. Doc Agent applies *Docs for Developers*, second edition, with three priorities: consistent language, sufficient relevant detail, and explanations that connect facts to useful understanding.

## Install

Requirements: a current VS Code with GitHub Copilot access, and Python 3.11 or newer for the installer and environment checker. The agent itself uses Copilot's selected model and available tools.

Clone the repository:

```sh
git clone https://github.com/RoryGlenn/doc-agent.git
cd doc-agent
```

From the repository root, preview and then install for your user:

```sh
python3 install.py --user
python3 install.py --user --apply
```

This adds `~/.copilot/agents/doc-agent.agent.md` and `~/.copilot/skills/doc-agent/`. It does not change editor settings, model choice, permissions, or existing project instructions. Existing identical files are skipped; any different destination file stops installation before copying begins. The installer never overwrites an existing file.

To install in a specific project instead:

```sh
python3 install.py --project /path/to/project
python3 install.py --project /path/to/project --apply
```

This adds the corresponding `.github/agents/` and `.github/skills/` files. Choose one scope for the same work to avoid duplicate entries. Resolve later update conflicts by reviewing and backing up your changes before replacing package-owned files; this first version does not silently merge upgrades.

Windows: use `py -3` if that is your Python launcher. The installer uses platform-independent paths. The optional tooling guide includes a PowerShell environment-variable example. Python 3.11+ is also available in Ubuntu 24.04's normal Python environment; keep the project's established runtime and package manager.

## Use in VS Code

Select **Copilot** as the session target, then select **Doc Agent** from the agent dropdown. You can also use **Configure Chat → Agents** or `/agents` to find it. Select **Skills** or use `/skills` to inspect `doc-agent`.

Example requests:

Writing:

> Improve this getting-started guide for developers who are new to the product. Help them reach a first successful result and understand the important choices.

Review:

> Review these docs for missing prerequisites, confusing explanations, irrelevant detail, inconsistent terminology, and unsupported claims. Give findings without editing.

Maintenance:

> Update the affected documentation for this release. Preserve guidance for supported versions and verify safe examples where possible.

The skill can also be invoked with `/doc-agent` in supported Copilot chat. If a customization is missing, check the selected session target and installation scope in the Agent Customizations view. Do not enable deprecated location settings or broad terminal auto-approval to fix discovery. Account access and the tools shown in that session still determine what can run.

## Included capabilities

- A native Copilot agent with read, search, edit, execution, web, and browser tool sets, where available.
- Portable writing, review, planning, and maintenance instructions, with conditional references.
- Optional [project context](.github/skills/doc-agent/assets/project-context.template.md) and [example-check](.github/skills/doc-agent/assets/example-check.template.md) templates.
- A [read-only environment checker](.github/skills/doc-agent/scripts/check_environment.py) that discovers relevant configuration and commands without executing them.
- Optional [Vale, Markdown, link, and browser/accessibility checks](.github/skills/doc-agent/tooling/README.md).
- [Behavior evaluation fixtures](.github/skills/doc-agent/evals/README.md) for future changes.

No service, database, API key, mandatory MCP connector, new site generator, or automated publishing hook is required. The optional Node tools have a lockfile and install only when requested. The package contains original book-derived guidance, not the copyrighted EPUB.

For Codex, the same `SKILL.md` and references follow the Agent Skills format. This installer targets Copilot; it does not create or modify a Codex installation. Copilot invocation uses its dropdown or `/doc-agent`. A separate Codex installation of the skill uses `$doc-agent`.

## Validate the package

From the package directory:

```sh
python3 -m unittest discover -s tests -v
python3 .github/skills/doc-agent/scripts/check_environment.py --project . --json
```

The tests cover installation conflicts, idempotency, rollback, symlinks, preservation of unrelated content, and bounded discovery without executing project commands. Optional lint/type checks use the root `pyproject.toml`:

```sh
ruff check install.py .github/skills/doc-agent/scripts tests
ruff format --check install.py .github/skills/doc-agent/scripts tests
mypy
```

The behavior fixtures evaluate content and decisions separately. Static package checks do not establish that Copilot has loaded the agent, that the account is signed in, or that every documentation task will succeed. Check discovery in VS Code and run a representative task.

[VALIDATION.md](VALIDATION.md) records the independent verification performed on the initial package, including the tested environment and its limits. Rerun the commands above, and the optional checks in the [tooling guide](.github/skills/doc-agent/tooling/README.md) where installed, after making further changes; that record does not cover changes made after repository publication.

## Platform references

- [VS Code custom-agent files and locations](https://code.visualstudio.com/docs/agent-customization/custom-agents)
- [VS Code skill discovery and invocation](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Copilot tools](https://code.visualstudio.com/docs/agents/reference/tools-reference)

Implementation and validation target the installed VS Code 1.137.0 with bundled Copilot Chat 0.65.0. Older versions and other Copilot surfaces may differ. Use each host's supported customization locations and tool availability.
