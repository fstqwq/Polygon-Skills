---
name: polygon-spec
description: "Problem repository schema and file format reference."
user-invocable: false
---

# Problem Repository Schemas

## Repository Layout

```
config/
  problem.json          # judging mode and resource limits
  build.json            # component source references
checkers/               # pass-fail checker sources after configured
validators/             # input validator sources
interactors/            # interactor sources (interactive problems)
generators/             # generator sources
solutions/              # solution sources + .desc files
attachments/            # contestant-downloadable files (testing tools, templates)
statement/
  statements.ftl        # main FTL template (do not edit)
  problem.tex           # problem FTL template (do not edit)
  olymp.sty             # LaTeX style (do not edit)
statement-sections/
  <language>/           # one directory per language (see Language Model below)
    name.tex            # problem title (single line)
    legend.tex          # problem body / legend
    input.tex           # input format description
    output.tex          # output format description
    notes.tex           # notes / explanations for samples
    interaction.tex     # interaction protocol (interactive problems only)
tests/
  spec.json             # ordered test specification
  manual/               # manual test input files
  generator/            # generator command payload files
draft/
  statement.md          # problem statement draft (Markdown)
  solution.md           # solution sketch and algorithm notes
  notes.md              # free-form working notes
temp/                   # throwaway test files (not committed, gitignored)
```

- `attachments/` is git-tracked and included in ICPC package export. Contents are distributed to contestants.
- `temp/` is the only allowed place for local scratch, compile outputs, downloaded artifacts, generated diagnostics, and throwaway test programs. It must be gitignored and never committed.
- `draft/` is git-tracked but excluded from the zip package.
- Pass-fail problems start with no checker selected. Once configured, `config/build.json` `checker_source` points to a file under `checkers/`.
- Interactive problems use `interactor_source` instead and must not set `checker_source`.
- Keep `config/build.json` keys in canonical schema order: `accepted_solution_source`, `validator_source`, `checker_source`, `interactor_source`, `generator_sources`.
- Write JSON and source files with LF line endings, not CRLF.
- Do not store official answers in the source repository or package. There is no `tests/answers/` directory in the canonical layout; answers are produced by the verification/package pipeline from the accepted solution.

## Judging Posture

- Treat local compilation and local runs as advisory sanity checks only.
- Treat local timing as machine-dependent. Python AC/TLE locally is only a relative signal.
- Use online Polygon-Replica Verification as the authority for final verdicts, limits, and performance.
- Do not change compilers, packages, time limits, or runtime environment just to make a local check pass unless the user explicitly asks.
- Do not weaken tests to fit an existing solution. Fix the solution, fix the spec, or record the expected failure.

## Language Model

### Directory structure

Each language is a subdirectory under `statement-sections/`. The directory name is the language token (lowercase, e.g. `english`, `chinese`, `japanese`).

```
statement-sections/
  english/              # priority 0  -- always sorted first
  chinese/              # priority 1  -- sorted second
  japanese/             # alphabetical among remaining languages
  russian/              # alphabetical among remaining languages
```

### Priority and defaults

Languages are sorted with a fixed priority: **english** first, **chinese** second, then all others alphabetically. The first language in this sorted order is the default when no explicit language is selected (e.g. when a user first opens the preview page).

### Shared resources

All languages share one set of template files in `statement/`:
- `statements.ftl`  -- document preamble and structure
- `problem.tex`  -- per-problem rendering template
- `olymp.sty`  -- LaTeX style macros

These files are NOT language-specific. The same template compiles all languages.

### Adding a new language

Create the directory and populate it with the canonical section files:
```
statement-sections/<language>/
  name.tex
  legend.tex
  input.tex
  output.tex
  notes.tex
```

All files start empty (or with the problem title for `name.tex`).

For interactive problems only, also create:
```
statement-sections/<language>/interaction.tex
```

For pass-fail problems, `interaction.tex` must not exist.

### LaTeX engine selection

The system auto-detects the LaTeX engine from the rendered `main.tex` content:
- If `\usepackage{fontspec}` or `\usepackage{xeCJK}` is present  -- **XeLaTeX**
- Otherwise  -- **pdfLaTeX**

The default template includes `fontspec` + `xeCJK`, so new problems use XeLaTeX. Imported Polygon packages that use `fontenc`/`inputenc` continue to compile with pdfLaTeX.

**CJK font requirements** (XeLaTeX path, set in `statements.ftl`):
- Serif body: Noto Serif CJK SC (`\setCJKmainfont`)
- Sans headings: Noto Sans CJK SC (`\setCJKsansfont`)
- Mono: Noto Sans CJK SC (`\setCJKmonofont`)

**Western fonts** (set in `olymp.sty`):
- Serif: TeX Gyre Termes (`\setmainfont`)
- Sans: TeX Gyre Heros (`\setsansfont`)
- Mono: TeX Gyre Cursor (`\setmonofont`)

## Git Conventions

- Each meaningful change gets its own commit.
- Commit messages should be descriptive: `"add accepted solution"`, `"add manual tests 001-003"`, `"update statement legend"`.
- Do not commit derived/generated files.
- Do not create scratch files outside `temp/`. If a file is not source, configuration, test data, statement content, or a contestant attachment, put it under `temp/`.
- The `draft/` directory is committed  -- it is part of the authoring history.

## Reference Files

For detailed schemas and reference data, read the following files in this skill directory:

- `config.md`  -- default values and full field tables for `problem.json` and `build.json`
- `tests.md`  -- full `spec.json` schema, `solutions/*.desc` format, and `draft/` conventions
- `checkers.md`  -- standard testlib checker catalog
- `references/codeforces-testlib-style.md`  -- shared source-code rules for validators, checkers, and interactors
- `review.py`  -- standalone validator; run from repo root to check all config files
