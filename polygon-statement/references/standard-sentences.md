# Standard Statement Sentences

Use these templates when their semantics match the problem. Keep the English and Chinese versions equivalent. Do not introduce multiple test points, guarantees, output branches, or interaction rules merely to use a template.

## Terminology

| English | Chinese |
|---|---|
| test case | 测试点 |
| subsequence | 子序列 |
| subsegment of a sequence | 子段 |
| subarray of an array | 子数组 |
| substring of a string | 子串 |

## Input

### Single test point

| English | Chinese |
|---|---|
| The first line contains an integer $n$ ($1 \le n \le 10^5$). | 第一行包含一个整数 $n$（$1 \le n \le 10^5$）。 |
| The first line contains two integers $n$ and $m$ ($1 \le n, m \le 10^5$). | 第一行包含两个整数 $n$ 和 $m$（$1 \le n, m \le 10^5$）。 |
| The second line contains $n$ integers $a_1, a_2, \ldots, a_n$ ($1 \le a_i \le n$). | 第二行包含 $n$ 个整数 $a_1, a_2, \ldots, a_n$（$1 \le a_i \le n$）。 |
| Each of the next $m$ lines contains two integers $x$ and $y$ ($1 \le x, y \le n$). | 接下来的 $m$ 行中，每行包含两个整数 $x$ 和 $y$（$1 \le x, y \le n$）。 |
| The $i$-th of the next $m$ lines contains two integers $x_i$ and $y_i$ ($1 \le x_i, y_i \le n$). | 接下来的 $m$ 行中，第 $i$ 行包含两个整数 $x_i$ 和 $y_i$（$1 \le x_i, y_i \le n$）。 |

### Multiple test points

Use these only when the input already contains multiple test points. Do not add $t$ by default.

| English | Chinese |
|---|---|
| The first line contains an integer $t$ ($1 \le t \le 10^4$), the number of test cases. The description of the test cases follows. | 第一行包含一个整数 $t$（$1 \le t \le 10^4$），表示测试点的数量。接下来是各测试点的描述。 |
| The first line of each test case contains an integer $n$ ($1 \le n \le 10^5$). | 每个测试点的第一行包含一个整数 $n$（$1 \le n \le 10^5$）。 |
| It is guaranteed that the sum of $n$ over all test cases does not exceed $10^5$. | 保证所有测试点中 $n$ 的总和不超过 $10^5$。 |

State a cross-test sum bound only when the input actually has that bound.

## Guarantees and Deduced Facts

| Meaning | English | Chinese |
|---|---|---|
| The input is constructed to satisfy a condition. | It is guaranteed that ... | 保证…… |
| A fact follows from the stated conditions. | It can be shown that ... | 可以证明，…… |
| Every valid input has a solution. | It can be shown that an answer always exists. | 可以证明，答案总是存在。 |
| The input edges are a tree. | It is guaranteed that the given edges form a tree. | 保证给定的边构成一棵树。 |

Do not use “It is guaranteed that” for a theorem that contestants can derive. Do not use “It can be shown that” to hide an input restriction.

## Output

| English | Chinese |
|---|---|
| For each test case, output an integer — the answer to the problem. | 对于每个测试点，输出一个整数，表示问题的答案。 |
| For each test case, output two integers $x$ and $y$. | 对于每个测试点，输出两个整数 $x$ 和 $y$。 |
| Output the minimum possible value of ... | 输出……的最小可能值。 |
| Output the maximum possible value of ... | 输出……的最大可能值。 |
| If there are multiple solutions, output any of them. | 如果有多个解，输出任意一个即可。 |
| If there is no solution, output $-1$. | 如果无解，输出 $-1$。 |
| For each test case, output \texttt{YES} if the answer exists, and \texttt{NO} otherwise. | 对于每个测试点，如果答案存在，输出 \texttt{YES}；否则输出 \texttt{NO}。 |
| You can output the answer in any case. For example, \texttt{yEs}, \texttt{yes}, \texttt{Yes}, and \texttt{YES} are all accepted as positive responses. | 你可以使用任意大小写形式输出答案。例如，\texttt{yEs}、\texttt{yes}、\texttt{Yes} 和 \texttt{YES} 均会被视为肯定回答。 |
| Your answer is considered correct if its absolute or relative error does not exceed $10^{-9}$. | 如果答案的绝对误差或相对误差不超过 $10^{-9}$，则认为答案正确。 |

Use `~---` for an English prose dash in LaTeX. Chinese usually reads more naturally with a comma.

## Definitions and Lists

Always write “as follows”, never “as follow”, regardless of the subject.

| English | Chinese |
|---|---|
| The operation is defined as follows. | 该操作定义如下。 |
| The rules are as follows. | 规则如下。 |
| The answer is calculated as follows. | 答案按如下方式计算。 |

## Problem Versions

| English | Chinese |
|---|---|
| This is the easy version of the problem. The difference between the versions is that in this version, ... | 这是本题的简单版本。两个版本的区别在于，本版本中…… |
| This is the hard version of the problem. The difference between the versions is that in this version, ... | 这是本题的困难版本。两个版本的区别在于，本版本中…… |

## Interactive Problems

### Mandatory introduction and flush block

Use the following block verbatim in an English interactive statement:

```latex
\textit{This is an interactive problem.} Remember to flush the output buffer after every print. To flush your output, you can use:
\begin{itemize}
    \item \texttt{fflush(stdout)} or \texttt{cout.flush()} in C/C++;
    \item \texttt{System.out.flush()} in Java and Kotlin;
    \item \texttt{sys.stdout.flush()} in Python.
\end{itemize}
```

Use the following equivalent block in a Chinese interactive statement:

```latex
\textit{这是一道交互题。} 请记得在每次输出后刷新输出缓冲区。你可以使用以下方式刷新输出：
\begin{itemize}
    \item C/C++ 中的 \texttt{fflush(stdout)} 或 \texttt{cout.flush()}；
    \item Java 和 Kotlin 中的 \texttt{System.out.flush()}；
    \item Python 中的 \texttt{sys.stdout.flush()}。
\end{itemize}
```

| English | Chinese |
|---|---|
| This is an interactive problem. | 这是一道交互题。 |
| After outputting each query, output the end of line and flush the output. | 输出每次询问后，请输出换行符并刷新输出缓冲区。 |
| If you read $-1$ instead of valid data at any stage of the interaction, your program must terminate immediately. | 如果在交互过程中的任何阶段读到 $-1$ 而不是合法数据，你的程序必须立即结束。 |
| Otherwise, your program may receive an arbitrary verdict because it will continue reading from a closed stream. | 否则，程序会继续从已经关闭的输入流中读取数据，并可能得到任意评测结果。 |

Include the complete block only in interactive statements. Keep any additional language-specific flushing guidance in the interaction section or interactor guidance rather than duplicating it elsewhere.
