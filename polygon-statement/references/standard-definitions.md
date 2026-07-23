# Standard Statement Definitions

Use a definition only when the statement needs it. Keep the English and Chinese versions equivalent, and use one term consistently throughout a problem.

## Sequences, Arrays, and Strings

### Subsequence

**English:** A sequence $a$ is a subsequence of a sequence $b$ if $a$ can be obtained from $b$ by deleting several elements at arbitrary positions, possibly none or all.

**中文：** 如果可以通过删除序列 $b$ 中若干个任意位置的元素得到序列 $a$，则称 $a$ 是 $b$ 的一个子序列。删除的元素数量可以为零，也可以是全部元素。

### Subsegment

**English:** A sequence $a$ is a subsegment of a sequence $b$ if $a$ can be obtained from $b$ by deleting several elements from the beginning and several elements from the end, possibly none or all.

**中文：** 如果可以通过删除序列 $b$ 开头的若干元素和末尾的若干元素得到序列 $a$，则称 $a$ 是 $b$ 的一个子段。删除的元素数量可以为零，也可以是全部元素。

### Subarray

**English:** An array $a$ is a subarray of an array $b$ if $a$ can be obtained from $b$ by deleting several elements from the beginning and several elements from the end, possibly none or all.

**中文：** 如果可以通过删除数组 $b$ 开头的若干元素和末尾的若干元素得到数组 $a$，则称 $a$ 是 $b$ 的一个子数组。删除的元素数量可以为零，也可以是全部元素。

### Substring

**English:** A string $a$ is a substring of a string $b$ if $a$ can be obtained from $b$ by deleting several characters from the beginning and several characters from the end, possibly none or all.

**中文：** 如果可以通过删除字符串 $b$ 开头的若干字符和末尾的若干字符得到字符串 $a$，则称 $a$ 是 $b$ 的一个子串。删除的字符数量可以为零，也可以是全部字符。

### Objects distinguished by positions

When different choices of positions count as different objects, append the applicable sentence:

**English:** Two such objects are considered different if they use different sets of positions in the original sequence, array, or string.

**中文：** 如果两个这样的对象在原序列、数组或字符串中使用的位置集合不同，则认为它们不同。

### Permutation

**English:** A permutation of length $n$ is an array containing each integer from $1$ to $n$ exactly once, in arbitrary order.

**中文：** 长度为 $n$ 的排列是一个按任意顺序包含 $1$ 到 $n$ 中每个整数恰好一次的数组。

## Lexicographical Order

Use the following generic definition for strings, sequences, or arrays:

**English:** An object $a$ is lexicographically smaller than an object $b$ if either $a$ is a proper prefix of $b$, or at the first position where they differ, the element of $a$ is smaller than the corresponding element of $b$.

**中文：** 如果 $a$ 是 $b$ 的真前缀，或者在 $a$ 与 $b$ 第一个不同的位置上，$a$ 的元素小于 $b$ 的对应元素，则称 $a$ 的字典序小于 $b$。

For equal-length objects, omit the prefix case:

**English:** For objects of the same length, $a$ is lexicographically smaller than $b$ if, at the first position where they differ, the element of $a$ is smaller than the corresponding element of $b$.

**中文：** 对于长度相同的对象，如果在 $a$ 与 $b$ 第一个不同的位置上，$a$ 的元素小于 $b$ 的对应元素，则称 $a$ 的字典序小于 $b$。

For strings, compare characters by the alphabet order stated in the problem. For numerical sequences and arrays, compare element values.

## Mathematical Operations

| Concept | English | Chinese |
|---|---|---|
| Bitwise XOR | $\oplus$ denotes the bitwise XOR operation. | $\oplus$ 表示按位异或运算。 |
| Bitwise OR | $\mathbin{\vert}$ denotes the bitwise OR operation. | $\mathbin{\vert}$ 表示按位或运算。 |
| Bitwise AND | $\mathbin{\&}$ denotes the bitwise AND operation. | $\mathbin{\&}$ 表示按位与运算。 |
| GCD | $\gcd(x,y)$ denotes the greatest common divisor of $x$ and $y$. | $\gcd(x,y)$ 表示 $x$ 和 $y$ 的最大公约数。 |
| LCM | $\operatorname{lcm}(x,y)$ denotes the least common multiple of $x$ and $y$. | $\operatorname{lcm}(x,y)$ 表示 $x$ 和 $y$ 的最小公倍数。 |
| MEX | $\operatorname{mex}(S)$ denotes the smallest non-negative integer that does not belong to $S$. | $\operatorname{mex}(S)$ 表示不属于 $S$ 的最小非负整数。 |
| Remainder | $a \bmod b$ denotes the remainder when $a$ is divided by $b$. | $a \bmod b$ 表示 $a$ 除以 $b$ 所得的余数。 |

Use `\bmod` for a remainder expression:

```latex
(a, b) \longmapsto (b, a \bmod b).
```

Use `\equiv` with `\pmod` for congruence:

```latex
a^{p-1} \equiv 1 \pmod p.
```

Use lowercase names with `\operatorname` for mathematical functions unless a conventional command such as `\gcd` already exists.

## Modular Fraction Answers

Use this only when the exact answer is represented modulo a prime or modulus.

**English:** It can be shown that the exact answer can be written as an irreducible fraction $\frac{p}{q}$, where $q \not\equiv 0 \pmod M$. Output the integer $x$ ($0 \le x < M$) such that $x \cdot q \equiv p \pmod M$.

**中文：** 可以证明，精确答案可以写成最简分数 $\frac{p}{q}$，其中 $q \not\equiv 0 \pmod M$。输出整数 $x$（$0 \le x < M$），满足 $x \cdot q \equiv p \pmod M$。

## Trees

### Tree

**English:** A tree is a connected undirected graph with no cycles.

**中文：** 树是一个连通且无环的无向图。

### Rooted tree

**English:** A rooted tree is a tree with one distinguished vertex called the root.

**中文：** 有根树是一棵指定了一个特殊顶点作为根的树。

### Parent and child

**English:** The parent of a non-root vertex $v$ is the first vertex after $v$ on the simple path from $v$ to the root. The root has no parent. A vertex $u$ is a child of a vertex $v$ if $v$ is the parent of $u$.

**中文：** 对于非根节点 $v$，从 $v$ 到根的简单路径上紧邻 $v$ 的节点称为 $v$ 的父节点。根没有父节点。如果 $v$ 是 $u$ 的父节点，则称 $u$ 是 $v$ 的子节点。

### Ancestor and descendant

**English:** An ancestor of a vertex $v$ is any vertex on the simple path from the parent of $v$ to the root. A descendant of a vertex $v$ is a vertex for which $v$ is an ancestor. A vertex is not its own ancestor or descendant.

**中文：** 节点 $v$ 的祖先是从 $v$ 的父节点到根的简单路径上的任意节点。如果 $v$ 是 $u$ 的祖先，则称 $u$ 是 $v$ 的后代。节点不属于自己的祖先或后代。

### Leaf

**English:** A leaf is a vertex with no children.

**中文：** 没有子节点的节点称为叶节点。

### Subtree

**English:** The subtree of a vertex $v$ consists of $v$, all descendants of $v$, and all edges between these vertices.

**中文：** 节点 $v$ 的子树由 $v$、$v$ 的所有后代以及这些节点之间的所有边组成。

### Binary trees

**English:** A binary tree is a rooted tree in which every vertex has at most two children. A full binary tree is a rooted tree in which every vertex has either zero or two children.

**中文：** 二叉树是每个节点至多有两个子节点的有根树。满二叉树是每个节点恰好有零个或两个子节点的有根树。

Use “vertex” for graph-theoretic statements and “node” for parent-child descriptions when that reads naturally. Do not mix the terms within one problem without a reason.
