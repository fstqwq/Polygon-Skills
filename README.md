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
| `polygon-solution` | "write solutions" | Brute force → WA traps → std → translations |
| `polygon-generate-tests` | "create tests" | Design test plan → implement test suite |
| `polygon-review` | "review the problem" | End-to-end audit before export |
| `polygon-export` | "export / package" | Zip the working tree as a native package |
| `polygon-import` | "import a package" | Unzip into a local repo (new or overwrite) |

## Typical workflow

```
polygon-init           -> scaffold the repo
polygon-statement      -> write the problem statement
polygon-validator      -> write the validator
polygon-checker        -> pick or write the checker
polygon-solution       -> write solutions (brute, WA, std)
polygon-generate-tests -> design and create tests
polygon-review         -> audit everything
polygon-export         -> package for upload
```

## Shared resources

| Path | Purpose |
|------|---------|
| `polygon-spec/testlib.h` | Testlib header (`-I <skills>/polygon-spec`) |
| `polygon-spec/review.py` | Structural health check script |
| `polygon-spec/compile.md` | Compilation flags reference |
| `polygon-spec/checkers.md` | Built-in checker catalog |
| `polygon-spec/config.md` | `problem.json` schema |
| `polygon-spec/tests.md` | `spec.json` schema |
| `polygon-statement/check_formulas.py` | LaTeX formula validation |
| `polygon-interactor/testing_tool.md` | Testing tool writing guide |

## Conventions

- UTF-8 everywhere. Em-dashes written as ASCII ` -- `, never as a Unicode em-dash.
- Each skill is self-contained. `SKILL.md` is the entry point.
- Skills reference each other by name (e.g., "see `/polygon-solution`").
- `draft/` is for working files (plans, reviews). Not exported.
- `temp/` is local scratch. Not exported.
