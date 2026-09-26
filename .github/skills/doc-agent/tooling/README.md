# Optional documentation checks

Use the project's existing tools and rules first. These starter configurations require explicit invocation and do not change editor settings, install packages automatically, or run code examples. All paths below are examples: set `DOC_AGENT_TOOLS` to this installed skill's `tooling` directory.

```sh
# Personal installation on macOS or Linux; use the equivalent repository path if installed there.
DOC_AGENT_TOOLS="$HOME/.copilot/skills/doc-agent/tooling"
```

The agent package and environment checker need Python 3.11 or newer. Only the optional Node checks need Node 22 or newer. Use an existing compatible project runtime; do not replace an incompatible project's runtime globally to run these tools.

## Markdown

Install the optional development tools into this tooling directory with the bundled lockfile:

```sh
npm ci --prefix "$DOC_AGENT_TOOLS"
```

From the project root, check explicitly selected Markdown files. If the project has a Markdown configuration, run its own command instead. To opt into the supplied starter:

```sh
node "$DOC_AGENT_TOOLS/node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs" \
  --config "$DOC_AGENT_TOOLS/.markdownlint-cli2.jsonc" \
  README.md 'docs/**/*.md'
```

This checks formatting and structure, not correctness or user understanding. HTML and long lines are allowed because many documentation projects need them. It does not apply automatic fixes.

## Style and terminology

Install [Vale](https://vale.sh/) through its supported platform installation route. The starter was validated with Vale 3.23.0 and uses only the included local rules; it needs no downloaded style package.

```sh
vale --config "$DOC_AGENT_TOOLS/.vale.ini" docs/example.md
```

The three rules are suggestions for wordy alternatives. A successful exit can still contain suggestions. Review meaning before changing wording.

For project-specific terminology, extend the project's existing `.vale.ini` and rules. Approved names can be added to its vocabulary, and explicit preferred alternatives can be captured in a project-owned substitution rule. Do not disable spelling globally for a product name or apply one product's vocabulary to every repository. If no project vocabulary exists, first record agreed terms in the project-context template; turn them into checks when recurrence justifies it.

## Links and heading anchors

Install [Lychee](https://lychee.cli.rs/) through its supported platform installation route. The starter was validated with Lychee 0.24.2.

```sh
# Local files and anchor fragments; do not send external HTTP requests.
lychee --config "$DOC_AGENT_TOOLS/lychee.toml" --offline -- README.md 'docs/**/*.md'

# Include external URLs when that scope is appropriate for this task.
lychee --config "$DOC_AGENT_TOOLS/lychee.toml" -- README.md 'docs/**/*.md'
```

Inspect failures in context: private destinations may need authentication; external sites may throttle requests. Generated website slugs can differ from Markdown's heading rules, so also check the rendered site using its own routing. Do not silence all failures to obtain a passing result.

## Website preview and accessibility

Use the site's existing build and preview process. For the optional smoke test, install Node tools as above and the required Playwright browser:

```sh
npm exec --prefix "$DOC_AGENT_TOOLS" -- playwright install chromium
DOC_AGENT_BASE_URL=http://127.0.0.1:8000/ \
  npm --prefix "$DOC_AGENT_TOOLS" run test:site
```

`DOC_AGENT_BASE_URL` is the only package-specific environment variable. It names one actual page to check; no default remote site is contacted. In PowerShell, set it with `$env:DOC_AGENT_BASE_URL = 'http://127.0.0.1:8000/'` before running the npm command.

The test checks HTTP success, visible page content, and axe's detectable accessibility issues, and records a screenshot and accessibility report. It does not crawl the site, start a server, authenticate, publish, or prove comprehensive accessibility. Inspect the screenshot and try the reader's task manually. Add representative pages and interactions to the project's existing tests when needed; avoid duplicating a mature browser-test setup.

## Authoritative references

- [Vale style configuration](https://vale.sh/)
- [markdownlint-cli2 usage and configuration](https://github.com/DavidAnson/markdownlint-cli2)
- [Lychee fragment checks](https://lychee.cli.rs/recipes/anchors/)
- [Playwright accessibility testing and its limits](https://playwright.dev/docs/accessibility-testing)
