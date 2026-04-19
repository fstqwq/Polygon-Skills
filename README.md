# Polygon Skills

Agent skills for competitive programming problem authoring with [Polygon-Replica](../Polygon-Replica/).

## Installation

### Claude Code

Symlink or copy into your workspace's `.claude/skills/`:

```powershell
# Windows (run as admin or with dev mode enabled)
New-Item -ItemType Junction -Path .claude\skills\polygon -Target skills

# Or copy
Copy-Item -Recurse skills\polygon-* .claude\skills\
```

Skills are auto-discovered from `.claude/skills/*/SKILL.md`.

### Codex

Same structure under `.codex/skills/`:

```powershell
New-Item -ItemType Junction -Path .codex\skills\polygon -Target skills

# Or copy
Copy-Item -Recurse skills\polygon-* .codex\skills\
```

### Manual reference

If your agent doesn't support skill directories, add to `CLAUDE.md` or `AGENTS.md`:

```markdown
## Problem Authoring Skills

When the user asks to create, edit, or review a competitive programming problem,
read and follow the matching skill in `skills/polygon-{name}/SKILL.md`.
Reference files in `skills/polygon-spec/` as needed.
```

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `polygon-init` | "create a new problem" | Scaffold the repo structure |
| `polygon-statement` | "write the statement" | Draft in Markdown, then convert to LaTeX |
| `polygon-validator` | "write the validator" | Testlib validator |
| `polygon-checker` | "write/pick the checker" | Select built-in or write custom checker |
| `polygon-interactor` | "write the interactor" | Interactive problem interactor + testing tool |
| `polygon-solution` | "write solutions" | Brute force -> WA traps -> std -> translations |
| `polygon-hack` | "hack the problem" | Generate targeted wrong solutions and tests that reject them |
| `polygon-generate-tests` | "create tests" | Design test plan -> implement test suite |
| `polygon-review` | "review the problem" | End-to-end audit before local zip creation |
| `polygon-local-export` | "create a local zip file" | Zip the working tree as a native zip file |
| `polygon-local-import` | "import a local zip file" | Unzip a native zip file into a local repo |

## Agent Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `polygon-agent-cli` | internal shared CLI | Cross-platform script entrypoint for all Polygon agent API workflows |
| `polygon-agent-auth` | "initialize/connect Polygon agent" | Register an agent session and request problem tokens |
| `polygon-agent-pull` | "clone/pull remote problem" | Mirror a full remote workspace into a local Git repo |
| `polygon-agent-push` | "push workspace via agent" | Atomically apply a local workspace mirror |
| `polygon-agent-verification` | "run verification via agent" | Start, wait for, and inspect verification |
| `polygon-agent-export` | "export via agent" | Start, wait for, and download exports |
| `polygon-agent-commit` | "commit via agent" | Commit and publish through the agent API |

## Typical workflow

```
polygon-init           -> scaffold the repo
polygon-statement      -> write the problem statement
polygon-validator      -> write the validator
polygon-checker        -> pick or write the checker
polygon-solution       -> write solutions (brute, WA, std)
polygon-hack           -> generate targeted wrong solutions and hack tests
polygon-generate-tests -> design and create tests
polygon-review         -> audit everything
polygon-local-export   -> create a local zip file for upload
```

## Shared resources

| Path | Purpose |
|------|---------|
| `polygon-agent-cli/references/cli.md` | Shared CLI command catalog for `polygon-agent-*` skills |
| `polygon-spec/testlib.h` | Testlib header (`-I <skills>/polygon-spec`) |
| `polygon-spec/review.py` | Structural health check script |
| `polygon-spec/compile.md` | Compilation flags reference |
| `polygon-spec/checkers.md` | Built-in checker catalog |
| `polygon-spec/config.md` | `problem.json` schema |
| `polygon-spec/tests.md` | `spec.json` schema |
| `polygon-statement/check_formulas.py` | LaTeX formula validation |
| `polygon-interactor/testing_tool.md` | Testing tool writing guide |

## Global posture

Local compile/run results are sanity checks only. Timing-sensitive results, including Python AC/TLE behavior, are relative signals from the current machine and must not be treated as final. Online Polygon-Replica Verification on the configured judgehost is authoritative for final verdicts, limits, and performance.

Skills are skeptical by default. Preserve the problem-setting standard instead of making the current local attempt pass.

- Do not modify the local runtime environment to make a check pass unless the user explicitly asks.
- Do not weaken, delete, or avoid tests because a solution fails them.
- When a solution or statement appears to pass, still look for contestant failure modes: boundary cases, overflow, precision, complexity traps, stale state across test cases, output branches, and interaction protocol mistakes.

## Conventions

- UTF-8 everywhere. Em-dashes written as ASCII ` -- `, never as a Unicode em-dash.
- Each skill is self-contained. `SKILL.md` is the entry point.
- Skills reference each other by name (e.g., "see `/polygon-solution`").
- When materializing a remote Polygon problem locally, use `./<owner>/<problem>/` as the default repo path.
  Example: `./fstqwq/a-plus-b/`, not `./a-plus-b/`.
- `draft/` is for working files (plans, reviews). Not exported.
- All local scratch, compile outputs, downloaded artifacts, generated diagnostics, and throwaway test programs must live under `temp/`. `temp/` is not exported or committed.
