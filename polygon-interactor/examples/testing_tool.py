#!/usr/bin/env python3

"""
Local testing tool for Guess the Number (Deluxe ver.)

Disclaimer: This is NOT the same code used to test your solution when it is submitted.
This tool is provided as-is. Its purpose is to help with debugging the interactive
problem and it has no ambitions to extensively test all possibilities that
are allowed by the problem statement. While the tool tries to yield the same
results as the real judging system, this is not guaranteed and the result
may differ if the tested program does not use the correct formatting or
exhibits other incorrect behavior. The tool also *does not* enforce time and
memory limits that are applied to submitted solutions.

Feel free to make whatever alterations or augmentations you like.

The behavior is controlled by an input data file.
The first line of the file contains two integers: n (number of secret numbers) and seed.
The next n lines each contain one integer in [0, 100], the secret number.

Here is an example file:
3 12345
42
7
100

The testing tool is run like this::

    pypy3 guess_number_testing_tool.py <data_file> <program> <arguments>

where `arguments` are optional arguments to the program to run. The following
show examples for different languages::

    pypy3 guess_number_testing_tool.py 1.in ./myprogram
    pypy3 guess_number_testing_tool.py 1.in java -cp . MyProgram
    pypy3 guess_number_testing_tool.py 1.in pypy3 myprogram.py

The tool logs the complete interaction.
If you do not want that, pass `--quiet` (before the data file name).
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from typing import List


verbose = True
process = None


class WrongAnswer(RuntimeError):
    pass


class EndOfFile(RuntimeError):
    pass


def vprint(*args, **kwargs) -> None:
    if verbose:
        print("< ", end="")
        print(*args, **kwargs)
        sys.stdout.flush()
    if process.stdin:
        print(*args, file=process.stdin, flush=True, **kwargs)


def vreadline(optional: bool = False) -> str:
    line = process.stdout.readline()
    if verbose and line:
        print("> " + line.rstrip("\n"))
    if not line and not optional:
        raise EndOfFile()
    return line


def read_secrets(path: str) -> tuple[int, List[int], int]:
    with open(path, "r", encoding="utf-8") as f:
        tokens = f.read().strip().split()
    if not tokens:
        raise ValueError("Input file is empty.")
    
    if len(tokens) < 2:
        raise ValueError("First line must contain n and seed.")
    
    n = int(tokens[0])
    seed = int(tokens[1])
    
    if len(tokens) < 2 + n:
        raise ValueError(f"Expected {n} secret numbers, got {len(tokens) - 2}.")
    
    secrets = []
    for i in range(n):
        num = int(tokens[2 + i])
        if not (0 <= num <= 100):
            raise ValueError(f"Secret number {num} out of range [0,100].")
        secrets.append(num)
    
    return n, secrets, seed


def start_process(program: List[str], phase: str, bufsize: int | None = None) -> subprocess.Popen:
    global process
    if verbose:
        print(f"[{phase}] {' '.join(program)}")
    kwargs = {
        "shell": True,
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "text": True,
    }
    if bufsize is not None:
        kwargs["bufsize"] = bufsize
    process = subprocess.Popen(" ".join(program), **kwargs)
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Failed to open pipes.")
    return process


def run_first_run(program: List[str], n: int, secrets: List[int]) -> List[str]:
    """Run first run (r=1), return list of encoded notes."""
    start_process(program, "first run", bufsize=1)
    
    # Send input: r=1 and n
    vprint(f"1 {n}")
    
    encodings = []
    for secret in secrets:
        queries_used = 0
        while True:
            line = vreadline().strip()
            if line.startswith("?"):
                try:
                    x = int(line[2:].strip())
                except Exception:
                    raise WrongAnswer(f"Invalid query: {line}")
                if not (0 <= x <= 100):
                    raise WrongAnswer(f"Query out of range [0,100]: {x}")
                queries_used += 1
                if queries_used > 100:
                    raise WrongAnswer("More than 100 queries used for one number.")
                response = 1 if x == secret else 0
                if verbose:
                    print(f"< {response}")
                print(response, file=process.stdin, flush=True)
            elif line.startswith("!"):
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    raise WrongAnswer(f"Invalid record format: {line}")
                _, enc = parts
                if len(enc) != 8 or not all(c in '01' for c in enc):
                    raise WrongAnswer(f"Encoding must be 8-character binary string: '{enc}'")
                encodings.append(enc)
                break
            else:
                raise WrongAnswer(f"Unexpected output: {line}")
    
    process.stdin.close()
    process.wait(timeout=5)
    if process.returncode != 0:
        raise WrongAnswer(f"First run exit code {process.returncode}.")
    
    return encodings


def run_second_run(
    program: List[str],
    n: int,
    original_encodings: List[str],
    secrets: List[int],
    seed: int,
) -> None:
    """Run second run (r=2), verify outputs."""
    rnd = random.Random(seed)
    
    # Flip each note independently
    presented = [
        enc[::-1] if rnd.choice([True, False]) else enc
        for enc in original_encodings
    ]
    
    # Shuffle order
    indices = list(range(n))
    rnd.shuffle(indices)
    shuffled_notes = [presented[i] for i in indices]
    expected = [secrets[i] for i in indices]
    
    start_process(program, "second run", bufsize=1)
    
    vprint(f"2 {n}")
    
    for i in range(n):
        vprint(shuffled_notes[i])
        line = vreadline().strip()
        try:
            y = int(line)
        except Exception:
            raise WrongAnswer(f"Output #{i+1} is not an integer: {line}")
        
        if y != expected[i]:
            raise WrongAnswer(f"Note #{i+1}: expected {expected[i]}, got {y}")
    
    process.stdin.close()
    process.wait(timeout=5)
    if process.returncode != 0:
        raise WrongAnswer(f"Second run exit code {process.returncode}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [--quiet] data.in program [args...]"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Do not show interactions"
    )
    parser.add_argument("data", help="Input file that controls the behavior of the tool")
    parser.add_argument("program", nargs=argparse.REMAINDER, help="Program to run")
    args = parser.parse_args()

    global verbose
    verbose = not args.quiet

    if not args.program:
        parser.error("Must specify program to run")

    n, secrets, seed = read_secrets(args.data)

    encodings = run_first_run(args.program, n, secrets)
    run_second_run(args.program, n, encodings, secrets, seed)

    print("OK: All numbers correctly recovered.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (WrongAnswer, ValueError, EndOfFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
