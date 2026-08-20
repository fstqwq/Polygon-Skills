# Test construction catalog

Use this catalog after extracting the statement's legal sizes, graph direction, edge-weight range, connectivity requirements, and input conventions. Each section gives a construction method and the property it exercises.

For SPFA or Bellman-Ford candidates, inspect the actual implementation before choosing a family:

- relaxation condition;
- FIFO, deque, SLF, LLL, MCFX, or combined policy;
- tolerance formula and comparison operator;
- whether visit counts are updated on enqueue or dequeue;
- adjacency representation and iteration order;
- deterministic or randomized adjacency handling.

Derive all sizes and weights from the problem constraints. Keep intermediate distances and weight sums inside the candidate's numeric type.

## Trees

### Random recursive tree

For vertices numbered from `0`, attach each new vertex uniformly to an earlier vertex:

```cpp
vector<pair<int, int>> randomRecursiveTree(int n) {
    vector<pair<int, int>> edges;
    for (int v = 1; v < n; v++) {
        int parent = rnd.next(0, v - 1);
        edges.push_back({parent, v});
    }
    return edges;
}
```

This distribution has logarithmic height. Earlier vertices have more opportunities to receive children and tend to have larger degree.

Permuting all vertex labels after generation hides the creation order from the input. It preserves the same random recursive tree distribution.

### Uniform labeled tree / Cayley tree

Sample a Prüfer sequence uniformly, then decode it:

```cpp
vector<pair<int, int>> uniformLabeledTree(int n) {
    if (n <= 1)
        return {};

    vector<int> degree(n, 1);
    vector<int> code(max(0, n - 2));

    for (int& x : code) {
        x = rnd.next(0, n - 1);
        degree[x]++;
    }

    priority_queue<int, vector<int>, greater<int>> leaves;
    for (int v = 0; v < n; v++)
        if (degree[v] == 1)
            leaves.push(v);

    vector<pair<int, int>> edges;
    for (int x : code) {
        int leaf = leaves.top();
        leaves.pop();

        edges.push_back({leaf, x});
        if (--degree[x] == 1)
            leaves.push(x);
    }

    if (n >= 2) {
        int a = leaves.top();
        leaves.pop();
        int b = leaves.top();
        leaves.pop();
        edges.push_back({a, b});
    }

    return edges;
}
```

A uniform Prüfer sequence samples uniformly from all labeled trees. Its typical height is on the square-root scale, substantially deeper than a random recursive tree of the same size.

### Explicit structural trees

Use explicit shapes when a candidate's behavior depends on degree, diameter, depth, or decomposition.

**Star — maximum degree**

```cpp
for (int v = 1; v < n; v++)
    edges.push_back({0, v});
```

**Chain — maximum diameter and depth**

```cpp
for (int v = 1; v < n; v++)
    edges.push_back({v - 1, v});
```

**Caterpillar — long spine with shallow side branches**

Choose a spine length `s`. Build `0-1-...-(s-1)`, then attach every remaining vertex to a spine vertex. Round-robin attachment spreads the branches; concentrating attachments near one endpoint produces an asymmetric caterpillar.

```cpp
for (int v = 1; v < s; v++)
    edges.push_back({v - 1, v});
for (int v = s; v < n; v++)
    edges.push_back({(v - s) % s, v});
```

**Balanced binary tree — binary decomposition**

```cpp
for (int v = 1; v < n; v++)
    edges.push_back({(v - 1) / 2, v});
```

**Balanced ternary tree — wider recursive decomposition**

```cpp
for (int v = 1; v < n; v++)
    edges.push_back({(v - 1) / 3, v});
```

**Spider — several long arms sharing one center**

Choose arm lengths whose sum is `n-1`. For each arm, connect its first vertex to the center and continue it as a chain. Vary the number of arms and make at least one asymmetric instance.

**Broom — chain ending in a star**

Build a chain of length `s`, then attach every remaining vertex to the final chain vertex. This combines large depth with one high-degree endpoint.

**Double star — two adjacent high-degree vertices**

Connect two hubs, then split all remaining vertices between them. Include balanced and highly unbalanced splits.

**Lobster — branches two levels away from a backbone**

Build a backbone, attach intermediate branch vertices to it, then attach leaves to those branch vertices. This exercises algorithms whose state depends on more than one off-path level.

For each explicit family, consider both the natural labels and a deterministic label permutation when the candidate may accidentally rely on vertex numbering.

## Bellman-Ford

### Controlled propagation chain

Create:

```text
0 -> 1 -> 2 -> ... -> n-1
```

with every edge weight `1` and source `0`.

Emit three global edge orders:

1. `0 -> 1`, `1 -> 2`, ..., `(n-2) -> (n-1)`;
2. the exact reverse;
3. the reverse with a fixed-seed set of adjacent swaps.

Forward order propagates through the whole chain in one relaxation pass. Reverse order advances the finite distance by one vertex per pass. The lightly perturbed reverse order checks whether a candidate only survives the perfectly reversed case.

This construction concerns Bellman-Ford's global edge scan. SPFA uses per-vertex adjacency order instead.

## FIFO SPFA

### Non-negative chain driving a star

Create chain vertices `p_0 ... p_k`, a hub `h`, and `L` leaves:

```text
p_i -> p_(i+1)      weight 1
p_i -> h            weight 2(k-i)
h   -> every leaf   weight 0
```

Use `p_0` as the source. Within each `p_i` adjacency list, iterate `p_i -> h` before `p_i -> p_(i+1)`.

The chain labels are `0, 1, ..., k`. The candidate labels sent to `h` are `2k, 2k-1, ..., k`. FIFO processes the hub and its leaves before the next chain vertex lowers the hub again, so the star is scanned once per chain step.

Choose both `k` and `L` large. `k` controls the number of repeated improvements; `L` controls the cost of every improvement.

Plain SLF normally finishes the low-label chain before entering the star, so this non-negative form primarily targets FIFO SPFA and visit-count heuristics such as MCFX.

### Non-negative two-route chain

For every layer `i`, create chain vertices `v_i`, `v_(i+1)` and an auxiliary vertex `u_i`:

```text
v_i -> v_(i+1)      weight A
v_i -> u_i          weight B
u_i -> v_(i+1)      weight C
```

Choose positive weights satisfying:

```text
B + C < A
```

For FIFO, iterate the direct edge before the auxiliary edge. The direct but worse path enters the queue first and begins processing the suffix. The two-edge path later improves `v_(i+1)` and reopens the suffix.

Repeat the gadget in a chain. The construction is a DAG and uses only non-negative weights.

## Weighted grid

### Wind-back grid

Use an `R x C` grid with source at the first cell of the first row.

- Add horizontal edges in both directions with weight `1`.
- Between row `r` and row `r+1`, add a downward edge in every column.
- Give one endpoint column a downward weight of `1`.
- Give every other downward edge weight `H`.
- Alternate the cheap endpoint between the right and left ends of successive rows.
- Choose `H` larger than the cost of a complete horizontal sweep.

The high vertical edges create provisional distances across the next row. Reaching the cheap endpoint later sends an improvement back across that row. Alternating endpoints repeats the work in both directions.

Use rectangular grids as well as square grids. A small row count with long rows and a larger near-square grid exercise different queue widths.

### Grid driving a star

Start with a wind-back grid. Add a shared hub `h` and `L` leaves.

Let `e_r` be the endpoint reached after the intended sweep of row `r`. Add:

```text
e_r -> h            weight c_r
h   -> every leaf   weight 0
```

Choose a value `B` larger than the maximum increase in the shortest distance between consecutive row endpoints, then set:

```text
c_r = (R - 1 - r)B
```

All connector weights are non-negative, while the candidate label for `h` decreases from row to row. The grid produces repeated improvements and the star multiplies the scan cost of each improvement.

This combined construction reaches more queue heuristics than the grid alone. Treat it as a broad stress case rather than a universal worst case.

## SLF

### Descending chain driving a star

When negative edges are legal, create:

```text
p_i -> p_(i+1)      weight -1
p_i -> h            weight -M
h   -> every leaf   weight 0
```

Choose `M > 1`, and place the hub edge before the chain edge.

The graph is a DAG: all edges move forward along the chain or into the hub and leaves. It therefore has no negative cycle.

At `p_i`, the new hub label is smaller than the next chain label, so SLF moves the hub toward the front. Every later chain vertex lowers the hub again, and each hub visit lowers all leaves.

For Tolerance-SLF, choose `M` far enough beyond the candidate's tolerance threshold that the comparison still prioritizes the hub.

### Layered diamonds

For each layer `i`, create:

```text
v_i -> v_(i+1)      weight 0
v_i -> u_i          weight A
u_i -> v_(i+1)      weight -(A+1)
```

Iterate the direct edge before the auxiliary edge.

The one-edge path reaches the suffix first. The delayed two-edge path is shorter by `1`, so it reopens the suffix. Repeating the gadget creates nested improvements.

The construction is a DAG and has no negative cycle. Add fanout sinks from chain vertices when each reopening should scan more outgoing edges.

## Tolerance-SLF

Read the candidate's exact condition. If it pushes a label `x` to the front when:

```text
x <= queue_front_label + epsilon
```

there are two different construction strategies.

### Exploit the tolerance

Use the non-negative two-route chain:

```text
v_i -> v_(i+1)      weight A
v_i -> u_i          weight B
u_i -> v_(i+1)      weight C
```

Iterate the auxiliary edge before the direct edge and choose:

```text
B + C < A <= B + epsilon
```

Plain SLF leaves the direct vertex behind the auxiliary vertex and obtains the better path first. Tolerance-SLF accepts the larger direct label as sufficiently small, moves it to the front, and processes the suffix using a provisional distance.

Repeat enough layers that each delayed auxiliary path reopens a long suffix.

### Neutralize the tolerance

Scale the relevant label gap until it exceeds `epsilon`. The candidate then behaves like plain SLF on that decision. Combine this with the descending chain-star or layered-diamond construction.

These two strategies have opposite inequalities. Select the one that matches the candidate and the legal weight range.

## LLL

First identify the implementation. Two common versions behave differently.

### Shared trick vertex

Create a new source `s`, a sink-only trick vertex `z`, and the real construction source `r`:

```text
s -> z              weight H
s -> r              weight 0
```

Iterate `s -> z` first. Choose `H` large enough to dominate the queue average while the real construction runs, while remaining inside the legal weight and distance range.

Use the non-negative two-route chain as the real construction.

### Insertion LLL

Insertion LLL compares a newly enqueued label with the current queue average and chooses the front or back.

Within every two-route layer, iterate:

```text
v_i -> u_i          weight B
v_i -> v_(i+1)      weight A
u_i -> v_(i+1)      weight C
```

with `B+C<A`.

Without the trick vertex, the direct label `A` remains behind the cheaper auxiliary label `B`. With the inflated average, the direct label also appears small enough to enter the front, so the worse path processes the suffix prematurely.

### Rotating LLL

Rotating LLL appends normally, then rotates the queue front to the back while its label is above the queue average.

Within every layer, iterate the opposite order:

```text
v_i -> v_(i+1)      weight A
v_i -> u_i          weight B
u_i -> v_(i+1)      weight C
```

Without the trick vertex, the large direct label is above the queue average and rotates behind the auxiliary label. The trick vertex raises the average enough to prevent that rotation, allowing the worse direct path to process first.

A single phrase such as “add a large trick vertex” is incomplete. The construction must name the candidate's LLL implementation and emit its matching edge order.

## MCFX-style visit-count policies

Suppose the candidate prioritizes vertices only while their prior visit count lies in some interval.

Use the non-negative chain-star construction:

```text
p_i -> p_(i+1)      weight 1
p_i -> h            weight 2(k-i)
h   -> every leaf   weight 0
```

Choose `k` larger than the upper end of the candidate's priority interval and choose many leaves.

The hub receives a strictly improving label on every chain step. A bounded visit-count window changes where the hub is placed for some visits but does not remove the later improvements or the cost of scanning its leaves.

Also include the wind-back grid or grid-star construction when the candidate treats repeated low-degree grid vertices differently from a single high-degree hub.

## Swap-SLF

Swap-SLF compares the queue's front and back after queue changes and swaps them when the back has the smaller label.

When negative edges are legal, use the descending chain-star or layered-diamond construction. Both continually introduce labels that are smaller than the active suffix and repeatedly reopen already processed work. Endpoint swaps change the immediate order but do not remove the improvements.

When weights must be non-negative, use the wind-back grid-star construction with both forward and reverse adjacency variants. Increase the number of rows and repeat several grid-star blocks in series. Validate the construction against the exact candidate because non-negative Swap-SLF behavior is more sensitive to the queue and adjacency details.

## Edge order and adjacency representation

For every deliberate construction, emit:

1. the intended per-vertex edge order;
2. its exact reverse;
3. a lightly perturbed version using a fixed seed and a small number of adjacent swaps.

An append-based adjacency list usually iterates in input order:

```cpp
adj[u].push_back({v, w});
```

A head-inserted forward-star or linked list usually iterates the same input edges in reverse order:

```cpp
edge[++cnt] = {v, w, head[u]};
head[u] = cnt;
```

When the input graph is undirected, inspect the order in which both directed copies are inserted.

Record the intended adjacency traversal order in the generator comment. Adjust the emitted input order for the candidate's representation rather than assuming that file order equals traversal order.

## Randomized adjacency and queue variants

Use deterministic construction blocks first. Add randomization as separate variants.

- Repeat multiple independent trap blocks in series so a random order must make many blocks favorable to avoid the cost.
- Shuffle each adjacency list with an explicit seed.
- Run several seeds instead of relying on one randomized instance.
- Keep forward and reverse deterministic controls beside the shuffled cases.
- If the candidate seeds itself from time or entropy, run it repeatedly on the same legal input and record whether the result is stable.
- For lightly perturbed variants, swap a small fixed fraction of adjacent edges instead of fully erasing the deliberate order.

Randomization measures robustness. The deterministic variants preserve the explanation of why the construction works.

## Combining shortest-path constructions

Combine components by assigning each one a clear role:

- a two-route chain or wind-back grid creates repeated provisional distances;
- a star multiplies the cost of each repeated improvement;
- a huge sink-only label changes a global LLL average;
- weight scaling crosses or avoids a Tolerance-SLF threshold;
- repeated blocks reduce the chance that randomized adjacency makes every trap benign.

Keep the combined graph legal under the statement's direction, connectivity, weight, and numeric-range requirements. Verify that every negative-edge construction remains free of reachable negative cycles.
