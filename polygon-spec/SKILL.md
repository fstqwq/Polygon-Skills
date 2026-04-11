---
name: polygon-spec
description: "Problem repository schema and file format contracts for competitive programming problem authoring. Defines the canonical repo layout, JSON schemas, draft conventions, and git conventions shared by all polygon-* skills. This background skill is automatically referenced when any polygon-* skill needs schema or layout context."
user-invocable: false
---

# Problem Repository Schemas

## Repository Layout

```
config/
  problem.json          # judging mode and resource limits
  build.json            # component source references
checkers/               # checker sources (standard or custom)
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
    interaction.tex     # interaction protocol (interactive only)
tests/
  spec.json             # ordered test specification
  manual/               # manual test input files
  answers/              # committed answer files
draft/
  statement.md          # problem statement draft (Markdown)
  solution.md           # solution sketch and algorithm notes
  notes.md              # free-form working notes
temp/                   # throwaway test files (not committed, gitignored)
```

- `attachments/` is git-tracked and included in ICPC package export. Contents are distributed to contestants.
- `temp/` is for local testing scratch files (e.g. testing tool test programs). Not committed  --  add to `.gitignore`.
- `draft/` is git-tracked but excluded from the zip package.

## Language Model

### Directory structure

Each language is a subdirectory under `statement-sections/`. The directory name is the language token (lowercase, e.g. `english`, `chinese`, `japanese`).

```
statement-sections/
  english/              # priority 0 â€?always sorted first
  chinese/              # priority 1 â€?sorted second
  japanese/             # alphabetical among remaining languages
  russian/              # alphabetical among remaining languages
```

### Priority and defaults

Languages are sorted with a fixed priority: **english** first, **chinese** second, then all others alphabetically. The first language in this sorted order is the default when no explicit language is selected (e.g. when a user first opens the preview page).

### Shared resources

All languages share one set of template files in `statement/`:
- `statements.ftl` â€?document preamble and structure
- `problem.tex` â€?per-problem rendering template
- `olymp.sty` â€?LaTeX style macros

These files are NOT language-specific. The same template compiles all languages.

### Adding a new language

Create the directory and populate it with the full set of section files:
```
statement-sections/<language>/
  name.tex
  legend.tex
  input.tex
  output.tex
  notes.tex
  interaction.tex
```

All files start empty (or with the problem title for `name.tex`).

### LaTeX engine selection

The system auto-detects the LaTeX engine from the rendered `main.tex` content:
- If `\usepackage{fontspec}` or `\usepackage{xeCJK}` is present â†?**XeLaTeX**
- Otherwise â†?**pdfLaTeX**

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
- The `draft/` directory is committed â€?it is part of the authoring history.

## Reference Files

For detailed schemas and reference data, read the following files in this skill directory:

- `config.md` â€?default values and full field tables for `problem.json` and `build.json`
- `tests.md` â€?full `spec.json` schema, `solutions/*.desc` format, and `draft/` conventions
- `checkers.md` â€?standard testlib checker catalog
- `review.py` â€?standalone validator; run from repo root to check all config files
