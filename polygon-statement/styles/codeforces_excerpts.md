# Codeforces Writing Style Reference Excerpts

These excerpts and notes illustrate the target Codeforces style.

## Writing-style cues

- The object comes first.
- The legal operation appears early.
- The goal is short and imperative.
- Definitions are embedded directly in prose.
- Output conventions are standardized and terse.
- There is almost never narrative padding.

---

## Example 1: Pure operation + optimization target

> You are given an array $a$ of $n$ integers.
>
> In one operation, you choose an index $i$ ($1 \le i \le n$) and set $a_i := a_i + 1$ or $a_i := a_i - 1$.
>
> Find the minimum number of operations needed to make all elements of the array equal.

**Traits**: canonical "You are given ..." opening, operation defined immediately, objective stated in one short sentence, no story or motivation.

---

## Example 2: Property-first definition

> An array is called stable if for every $i$ ($1 \le i < n$), $|a_i - a_{i+1}| \le 1$.
>
> You are given an array $a$ of length $n$.
>
> In one operation, you may choose an index $i$ and increase $a_i$ by $1$.
>
> Determine whether it is possible to make the array stable using at most $k$ operations.

**Traits**: defines a property before the main task, then reuses the term directly; typical "Determine whether it is possible ..." phrasing.

---

## Example 3: Exact number of operations

> You are given an array $a$ of $n$ positive integers and an integer $k$.
>
> You have to perform exactly $k$ operations.
>
> In one operation, you choose two distinct indices $i$ and $j$, remove $a_i$ and $a_j$ from the array, and add $\left\lfloor \frac{a_i}{a_j} \right\rfloor$ to your score.
>
> Calculate the maximum possible score.

**Traits**: uses the very CF-like "exactly $k$ operations" phrasing, defines a fully procedural move, and ends with a compact optimization target.

---

## Example 4: Construction + "print any answer"

> You are given two integers $l$ and $r$.
>
> Find an integer $x$ such that:
>
> - $l \le x \le r$;
> - all digits of $x$ are distinct.
>
> If there are multiple answers, print any of them. If no such integer exists, print $-1$.

**Traits**: hallmark constructive-task phrasing, terse bullet conditions, and one of the most standardized CF output conventions.

---

## Example 5: Outputting an explicit sequence of operations

> You are given a string $s$ of length $n$, consisting only of characters `B` and `W`.
>
> In one operation, you choose an index $i$ ($1 \le i < n$) and invert both $s_i$ and $s_{i+1}$. That is, each of them changes from `B` to `W` or from `W` to `B`.
>
> Find any sequence of at most $3n$ operations that makes all characters of the string equal, or determine that it is impossible.

**Traits**: constructive wording that asks for a witness, explicit operation semantics, and a standard "find any sequence ... or determine that it is impossible" ending.

---

## Example 6: Canonical object -> operation -> objective skeleton

> You are given a tree with $n$ vertices.
>
> In one operation, you may choose an edge and remove it.
>
> Find the minimum number of operations needed to make every connected component contain exactly one marked vertex.

**Traits**: clean structural template, starts directly with the mathematical object, and shows that CF style applies just as naturally to graphs as to arrays.

---

## Key rules extracted

1. The dominant rhythm is object -> operation -> objective.
2. The statement usually becomes clear within the first one or two sentences.
3. If a property is easier to name than to repeat, define it directly and reuse the term.
4. Standardized output phrases are a feature, not a flaw.
5. Story, scene, and motivation are normally absent.
