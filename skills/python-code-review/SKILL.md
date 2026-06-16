---
name: python-code-review
description: Review and improve Python code for robustness, modularity, performance, and clarity. Use this skill whenever the user asks to review, refactor, clean up, lint, audit, improve, or critique Python code. Also trigger when the user shares Python code and asks to "make it better", "fix this", "check my code", "follow best practices", or mentions PEP 8, Black formatting, type hints, NumPy docstrings, DRY, KISS, YAGNI, caching, or code quality. Trigger for any partial improvement request too — "add type hints", "add docstrings", "make this more performant", "remove redundancy", or "make this more Pythonic". If the user pastes Python code without explicit instructions but it clearly needs cleanup, offer to review it using this skill.
---

# Python Code Review & Improvement

Review and improve Python code so it is robust, flexible, modular, clean, performant where it matters, and easy to read. Every change must have a clear justification — improve correctness, clarity, performance, or reduce complexity. Never change code just to change it.

When reviewing, work through the checklist below in order. Style and naming come first so the rest of the code is readable; types and docstrings make intent explicit; structure, performance, and safety come last because they build on the foundation.

## 1. Formatting & Style

Format all code with **Black** defaults (88-character line length) and follow **PEP 8** for everything Black does not auto-fix.

- **Imports**: Three groups separated by a blank line — standard library, third-party, local. Each group sorted alphabetically. Remove unused imports. Never use wildcard imports (`from module import *`).
- **Import only what is necessary**: Import specific names rather than whole modules when only a few names are used (`from math import sqrt, pi` rather than `import math` if `math` is used twice). Reverse this when many names are used or when the module prefix aids readability.
- **Defer heavy or optional imports**: For modules with significant import overhead (e.g., `tensorflow`, `torch`, `matplotlib.pyplot`, `pandas`) or those needed only for a specific code path, import them inside the function that uses them rather than at the top of the module. This keeps startup fast and avoids forcing users to install dependencies they will never use.
- **Whitespace**: Two blank lines before top-level definitions, one between methods. No trailing whitespace, no spaces inside brackets.

## 2. Naming

Names are the most important form of documentation. A good name removes the need for a comment.

- **Be specific, not generic**: Avoid `data`, `info`, `result`, `tmp`, `val`, `obj`, `item`, `x`, `arr`, `df`, `lst` as substantive variable names. Use `user_records`, `retry_count`, `weighted_mean`, `pending_orders` instead. Generic names are acceptable only in very short scopes (a one-line comprehension, a 2-line helper).
- **Be standard**: Use `snake_case` for functions, methods, variables, and modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level constants. Leading underscore (`_helper`) signals internal use. Never use `l`, `O`, or `I` as single-letter names.
- **Functions describe actions, starting with a verb**: `fetch_user_profile`, `validate_email`, `parse_config`, `compute_gradient`. Avoid noun-only names like `user_profile()` for a function.
- **Booleans read as questions**: `is_valid`, `has_permission`, `should_retry`, `was_modified`.
- **Match the domain vocabulary**: If the field calls it a "ledger", do not call it `record_list`. If the field calls it a "spike", do not call it `event`.
- **Loop variables**: `for user in users`, not `for u in users` or `for item in users`. Single-letter names are acceptable only for numeric indices (`for i in range(n)`) or trivially short comprehensions.

## 3. Type Hints

Add type hints to every function signature (parameters and return). They double as documentation and enable static analysis.

- **Use built-in generics on Python 3.9+**: `list[str]`, `dict[str, int]`, `tuple[int, ...]`. Import from `typing` only on older versions.
- **Use `X | None` on Python 3.10+** instead of `Optional[X]`. Same convention for unions.
- **Define `TypeAlias` at module level** for complex repeated types so signatures stay readable.
- **Annotate locals only when the type is not obvious**. The type checker can infer `count = 0`. Annotate `cache: dict[str, list[float]] = {}`.
- **Use `typing.Protocol`** for structural subtyping when the interface is small — preferred over ABCs for duck-typed APIs.

## 4. Docstrings (NumPy Style)

Add NumPy-style docstrings to all public functions, classes, and modules. Skip docstrings for trivially obvious private helpers (e.g., a 2-line `_clamp`).

```python
def calculate_metrics(
    values: list[float],
    weights: list[float] | None = None,
) -> dict[str, float]:
    """Calculate weighted summary statistics for a list of values.

    Computes mean, standard deviation, and median. When weights are
    provided, the mean and standard deviation are weighted accordingly.

    Parameters
    ----------
    values : list[float]
        Input values. Must be non-empty.
    weights : list[float] or None, optional
        Weights corresponding to each value. Must be the same length
        as `values` when provided. Defaults to equal weighting.

    Returns
    -------
    dict[str, float]
        Dictionary with keys ``"mean"``, ``"std"``, and ``"median"``.

    Raises
    ------
    ValueError
        If `values` is empty or if `weights` length does not match.

    Examples
    --------
    >>> calculate_metrics([1.0, 2.0, 3.0])
    {'mean': 2.0, 'std': 0.816..., 'median': 2.0}
    """
```

**Rules:**

- One-line summary on the same line as the opening `"""`, ending with a period.
- Blank line between summary and extended description.
- Document parameters, returns, and raised exceptions. Add `Examples` when behavior is not obvious from the signature.
- For classes, put the docstring under the class definition. Document `__init__` parameters there or in `__init__` — pick one and stay consistent within a project.

## 5. Design Principles

Each guideline below is well-known on its own, but they reinforce each other.

- **Single Responsibility Principle (SRP)**: Each function does one thing; each class represents one concept. Exception: pipeline / orchestration functions are intentionally a sequence of steps — those should still read top-to-bottom and delegate the actual work to helpers.
- **Don't Repeat Yourself (DRY)**: Extract shared logic when duplication is exact and meaningful. Do not force unrelated code into the same abstraction just because the surface looks similar — that creates fragile coupling worse than the duplication.
- **Rule of Three**: Two similar pieces of code do not require refactoring. The third occurrence is the signal to extract a function.
- **You Aren't Gonna Need It (YAGNI)**: Do not add parameters, options, or abstraction layers for hypothetical future needs. Build for the case in front of you; refactor when the second case arrives.
- **Keep It Simple, Stupid (KISS)**: Prefer the simpler implementation. A clear loop beats a clever one-liner. Reach for metaprogramming, decorators, and inheritance only when they earn their complexity.
- **Composition over inheritance**: Reuse via small composed pieces rather than deep class hierarchies, unless an inheritance relationship genuinely models an "is-a".
- **Stable, hard-to-misuse interfaces**: Use keyword-only arguments (`*,`) when a function takes multiple parameters of the same type, so callers cannot swap them by accident. Provide sensible defaults.
- **Minimize coupling**: Functions should depend on their parameters, not on global state. Pass dependencies in.

## 6. Performance & Efficiency

Optimize where it matters — hot loops, large data, and code in the critical path. Do not sacrifice readability for negligible gains, and do not optimize without measuring first.

- **Short-circuit evaluation**: In conditions, place the cheap check first and the expensive check second so the expensive one is skipped when possible. `if user is not None and expensive_validation(user):` — the `is not None` check guards the call. Use `any()` and `all()`, which short-circuit, instead of loop-and-flag patterns.
- **Cache pure functions called repeatedly with the same simple arguments** using `functools.lru_cache` or `functools.cache`. Caching only works when arguments are hashable (so simple types: `int`, `str`, `tuple`, `frozenset`) and the function is genuinely pure (same input → same output, no side effects). Do not cache functions that take large mutable objects, return generators, or depend on external state.
- **Hoist invariants out of loops**: If a value does not change inside the loop, compute it once before the loop.
- **Pick the right data structure**: `set` and `dict` give O(1) membership and lookup; `list` gives O(n). Use `collections.deque` for FIFO queues, `collections.defaultdict` to skip key-existence checks, `collections.Counter` for frequency counts, `bisect` for sorted-list operations.
- **Prefer the standard library and built-ins**: `itertools`, `functools`, `collections`, `heapq`, and `bisect` replace many hand-rolled loops with faster, clearer alternatives. `str.join()` for string assembly, never `+=` in a loop.
- **Generators for large or streaming data**: Use generator expressions or `yield` when the full sequence does not need to be materialized in memory.
- **Vectorize numerical work with NumPy** when operating on arrays of numbers — element-wise Python loops over numerical data are the most common avoidable performance bug.
- **Profile before optimizing**: For non-obvious hot paths, use `cProfile`, `timeit`, or `line_profiler`. Optimize the measured bottleneck, not the imagined one.

## 7. Dependency Discipline

- **Standard library first**: Python's standard library is large and capable. Reach for it before adding a third-party dependency. `pathlib`, `dataclasses`, `enum`, `itertools`, `functools`, `collections`, `concurrent.futures`, `argparse`, `json`, `csv`, `sqlite3`, `urllib`, `re`, `statistics`, `datetime` cover an enormous range of needs.
- **Common scientific stack is fine**: `numpy`, `pandas`, `scipy`, `matplotlib`, `scikit-learn` are de-facto standards in data and scientific work — use them freely when the task fits.
- **Justify niche dependencies**: A new third-party package introduces install burden, security surface, version compatibility risk, and possible abandonment. If it can be replaced by 20 lines of standard library code, do that instead.
- **Pin behavior, not exact versions, in libraries**: Library code should accept a reasonable range; application code can pin tightly via lockfiles.

## 8. Readability & Comments

Code is read far more often than it is written. Optimize for the reader.

- **Keep functions short and flat**. If you need a comment to separate "phases" inside a function, those phases are probably separate functions.
- **Early returns** to flatten nested conditionals. Handle invalid inputs and edge cases up front, then proceed with the main logic at the base indent level.
- **Comprehensions when they are simpler than a loop**. A 3-line comprehension with nested conditions is harder to read than the equivalent loop — use the loop.
- **Name intermediate values**: If a single expression needs a comment to explain it, break it into named intermediate variables. The variable name becomes the comment.
- **Comments only when necessary**: A comment explains *why*, not *what*. `# Retry with backoff because the upstream API rate-limits aggressively` is useful. `# Increment counter` is noise. Delete commented-out code — that is what version control is for.
- **TODOs include context**: `# TODO(alex): Remove after migration to v2 API (PROJ-1234)`. Orphan TODOs are clutter.

## 9. Error Handling

Handle what is likely, document what is possible, do not paper over bugs.

- **Validate inputs at boundaries** — public functions check arguments; private helpers trust their callers.
- **Raise specific exceptions with clear messages**: `raise ValueError(f"Expected positive integer, got {n}")`. Use `ValueError` for bad values, `TypeError` for wrong types, `FileNotFoundError` for missing files, custom exception subclasses for domain-specific errors.
- **Narrow `except` clauses**: Catch the specific exception you expect. Never bare `except:`. Use `except Exception:` only as a last resort and always log or re-raise.
- **Context managers** for resource lifecycle: `with open(...)`, `contextlib.suppress(FileNotFoundError)`, custom context managers for setup/teardown patterns. Never rely on `__del__` for cleanup.
- **Fail fast**: If something is wrong, raise immediately. Do not let bad state propagate and surface as a confusing error three layers down.
- **Do not over-engineer**: Cover plausible edge cases (empty input, `None`, off-by-one boundaries). Do not add defensive code for scenarios the function's contract rules out.

## 10. Safety & Robustness

Easy to overlook in review, critical in production.

- **No mutable default arguments**: `def f(items=[])` is the classic Python footgun. Use `None` and initialize inside.
- **Never trust external input**: Validate user input, file paths, and API responses. Use `pathlib` for path manipulation to avoid traversal bugs.
- **No secrets in code**: API keys, passwords, and tokens belong in environment variables or a secret manager.
- **Subprocess safety**: `subprocess.run(["cmd", arg])` with a list, never `shell=True` with unsanitized input.
- **`logging` over `print` in library or application code**. `print` is fine for scripts and one-off debugging.
- **Prefer immutability where it does not hurt**: tuples over lists, frozenset over set, `@dataclass(frozen=True)` for value objects. Reduces accidental mutation bugs.

---

## Worked Example

**Before:**

```python
import math, requests, numpy as np, pandas as pd, tensorflow as tf

CACHE = {}

def calc(data, t=0.5):
    # process the data
    res = []
    for d in data:
        if d['v'] > 0:
            if d['v'] > t:
                if d['name'] not in CACHE:
                    CACHE[d['name']] = math.sqrt(d['v'])
                res.append(CACHE[d['name']])
    return res
```

Issues: combined imports, eager `tensorflow` import, generic names (`calc`, `data`, `t`, `d`, `res`), hand-rolled cache as global state, deeply nested conditions, no type hints, no docstring, redundant zero-check before the threshold check.

**After:**

```python
from functools import lru_cache
from math import sqrt


@lru_cache(maxsize=1024)
def _sqrt_cached(value: float) -> float:
    return sqrt(value)


def filter_and_transform_scores(
    records: list[dict[str, float | str]],
    threshold: float = 0.5,
) -> list[float]:
    """Return the square root of each record's value above the threshold.

    Parameters
    ----------
    records : list[dict]
        Each record must contain ``"name"`` (str) and ``"value"`` (float).
    threshold : float, optional
        Records with value at or below this threshold are excluded.
        Defaults to ``0.5``.

    Returns
    -------
    list[float]
        Square roots of the values that passed the threshold, in input order.
    """
    return [
        _sqrt_cached(record["value"])
        for record in records
        if record["value"] > threshold
    ]
```

Changes: split imports and dropped unused ones; gave names that say what the values are; replaced ad-hoc dict cache with `lru_cache`; collapsed three nested `if`s into one short-circuit predicate (positivity is implied by `> threshold` when threshold is non-negative — flag the assumption to the user if it might not hold); added type hints and a NumPy-style docstring; no comments needed because the names carry the meaning.

---

## Delivering the Review

Structure responses in this order:

1. **One-line overall assessment** — quality and the single most important issue.
2. **The improved code as a complete, runnable replacement** — never make the user stitch fragments together.
3. **A brief summary of the non-obvious changes**, grouped by category (style, naming, types, structure, performance, safety). Skip trivia like "renamed `d` to `record`" — the diff speaks for itself. Call out anything that changes behavior, and any assumption made on the user's behalf (like the positivity assumption above) so they can confirm or correct it.

If the code is mostly fine, say so plainly. Not every review needs a rewrite. If the user requested a narrow change ("just add type hints"), focus on that — but flag any glaring issue in passing.

When the code clearly belongs to a larger codebase, ask about Python version, project conventions, and existing patterns before proposing changes that might conflict with the rest of the project.
