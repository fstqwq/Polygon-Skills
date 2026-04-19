# Standard Testlib Checkers

Standard checkers are used by copying from `<skills>/polygon-checker/standard/` into `checkers/` and setting `checker_source` in `build.json`. Judging always uses the repository file named by `checker_source`; `std::...` names are only UI/documentation labels derived from content. The checker name is the filename without `.cpp` (e.g. `wcmp`).

| Situation | Checker | Notes |
|-----------|---------|-------|
| Unique answer, whitespace flexible | `wcmp` | **Default choice.** Token-by-token comparison. |
| Single integer | `icmp` | Single signed 32-bit integer. |
| Sequence of integers, ordered | `ncmp` | 64-bit integers, token by token. |
| Sequence of integers, unordered | `uncmp` | Multisets must match exactly. |
| Huge integer (arbitrary precision) | `hcmp` | Single big signed integer. |
| YES or NO | `yesno` | Case-insensitive. |
| Multiple YES/NO answers | `nyesno` | One per line, case-insensitive. |
| Floating point, tolerance 10⁻⁴ | `rcmp4` | Absolute or relative error. |
| Floating point, tolerance 10⁻⁶ | `rcmp6` | Absolute or relative error. |
| Floating point, tolerance 10⁻⁹ | `rcmp9` | Absolute or relative error. |
| Single float, absolute error only | `acmp` / `rcmp` | Max absolute error ≤ 1.5×10⁻⁶. |
| Single float, abs or relative err | `dcmp` | Max error ≤ 10⁻⁶. |
| Sequence of floats, absolute only | `rncmp` | Max absolute error ≤ 1.5×10⁻⁵. |
| Line-by-line, tokens within line | `lcmp` | Ignores extra whitespace within lines. |
| Line-by-line, exact string match | `fcmp` | Entire line must match exactly. |
| `Case N:` format, one integer | `caseicmp` | Format: `Case 1: <n>` |
| `Case N:` format, integer sequence | `casencmp` | Format: `Case 1: <n1> <n2> ...` |
| `Case N:` format, token sequence | `casewcmp` | Format: `Case 1: <tok1> <tok2> ...` |
| Partial scoring | `pointscmp` / `pointsinfo` | Example templates only; usually needs customization. |
| Multiple valid answers | Write a custom checker | Use the `polygon-checker` skill. |
| Interactive problem | No checker source | Use `interactor_source` via the `polygon-interactor` skill instead. |
