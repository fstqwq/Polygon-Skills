# Codeforces Style

Use this style when the user explicitly asks for a more direct statement, no story, or Codeforces style.

Reference examples: `<skills>/polygon-statement/styles/codeforces_excerpts.md`

## Core approach

- Enter the formal problem immediately.
- State the objects, operations, and goal in direct algebraic language.
- Keep every sentence compact and information-dense.
- Favor the standard Codeforces rhythm: object -> operation -> objective.

## Rules

- Do not add a story unless the user explicitly asks for one.
- Do not force abstract objects into a concrete scenario.
- Open quickly with forms like "You are given..." and "Find...".
- If the property is easier to name than to repeat, define it directly: "An array is called ... if ...".
- Introduce the legal move early with forms like "In one operation, ...", "You can perform the following operation ...", or "You have to perform exactly $k$ operations."
- State the goal in one short imperative sentence. Typical verbs: "Find", "Determine", "Calculate", "Construct", "Output".
- Use highly standardized output conventions when they fit:
  - "If there are multiple answers, print any of them."
  - "If no such answer exists, print $-1$."
  - "You do not need to minimize the number of operations."
- Use bullets only when the condition or operation is easier to scan as a short list. Otherwise, keep the statement in prose.
- Define custom operations, structures, and terms before using them.
- Input/Output sections are format-only.
- Do not explain why the task matters. Do not add motivation, characters, or scene-setting.

## Micro-templates

### Minimum operations

> You are given [object].
>
> In one operation, you can [operation].
>
> Find the minimum number of operations needed to [target].

### Property definition

> A [structure] is called [property] if [condition].
>
> You are given [structure].
>
> Determine whether it is possible to make it [property].

### Construction

> You are given [parameters].
>
> Construct [object] such that [conditions].
>
> If there are multiple answers, print any of them. If no such answer exists, print $-1$.

### Exact number of operations

> You are given [object] and an integer $k$.
>
> You have to perform exactly $k$ operations.
>
> In one operation, you may [operation].
>
> Calculate the maximum possible [value].

## What good output feels like

- The statement becomes clear within the first one or two sentences.
- There are no decorative characters, settings, or motivations.
- The problem reads like a standard Codeforces house statement.
- The task is fully specified without any narrative padding.
