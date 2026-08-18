---
name: python-code-review
description: The coding standard for Python (style, naming, type hints, NumPy docstrings, performance, and safety) to follow while writing Python and to apply when reviewing it. Use when writing, implementing, or refactoring Python, or when asked to review, lint, audit, improve, or critique it ("add type hints", "add docstrings", "make this more Pythonic", "remove redundancy", "check my code"; PEP 8, Black). If Python is pasted without instructions but clearly needs work, offer a review. For structural design (decomposition, interfaces, coupling) use software-design; for language-agnostic structural or artifact cleanup defer to code-polishing; for C++ use cpp-code-review.
---

# Python Code Review & Improvement

The coding standard for Python: how it is written and how it is reviewed. The language-agnostic conduct is defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md) and applies here in full: the change ethos (every change needs a reason; never change code just to change it) and the two working modes, **authoring** (apply the standard as you write; the default when implementing or modifying Python) and **reviewing** (audit against it and return an improved version per "Delivering the Review").

Work the criteria in order: style and naming first, then types and docstrings, then structure, performance, and safety.

## 1. Formatting & Style

Format with **Black** defaults (88-character lines); **PEP 8** for everything Black does not auto-fix.

- **Imports**: three groups separated by a blank line (standard library, third-party, local), each alphabetized. Remove unused imports. Never `from module import *`.
- **Import only what is necessary**: `from math import sqrt, pi` over `import math` when few names are used; reverse when many names are used or the module prefix aids readability.
- **Defer heavy or optional imports** (`tensorflow`, `torch`, `matplotlib.pyplot`, `pandas`, or path-specific deps) into the function that uses them: keeps startup fast, avoids forcing unused installs.
- **Whitespace**: two blank lines before top-level definitions, one between methods; no trailing whitespace, no spaces inside brackets.

## 2. Naming

The language-agnostic naming doctrine (names as the primary documentation, specific over generic, verb-led functions, booleans as questions, domain vocabulary) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). Python adds:

- **Standard casing**: `snake_case` functions/methods/variables/modules; `PascalCase` classes; `UPPER_SNAKE_CASE` module constants; leading `_` signals internal. Never `l`, `O`, or `I` as single-letter names.
- **Python-flavored generics count as generic**: `arr`, `df`, `lst` are no better than `data` or `tmp` as substantive names.
- **Loop variables**: `for user in users`, not `for u in users` or `for item in users`. Single letters only for numeric indices (`for i in range(n)`) or trivially short comprehensions.

## 3. Type Hints

Annotate every function signature (parameters and return): documentation plus static analysis.

- **Built-in generics on 3.9+**: `list[str]`, `dict[str, int]`, `tuple[int, ...]`; import from `typing` only on older versions.
- **`X | None` on 3.10+** instead of `Optional[X]`; same for unions.
- **Module-level `TypeAlias`** for complex repeated types so signatures stay readable.
- **A quoted-string `TypeAlias` must be self-contained.** When quoting a forward reference to break a circular import, inline concrete types (`"str | os.PathLike[str] | Reader"`), never another module-level alias name. `typing.get_type_hints()` (used by dataclasses, Pydantic, attrs, and doc tooling) re-evaluates the string in the *importing* module's namespace, where that alias may not exist, raising `NameError` at runtime; formatter, linter, type checker, and tests all miss it.
- **Annotate locals only when non-obvious**: `cache: dict[str, list[float]] = {}`, not `count = 0`.
- **`typing.Protocol`** for small structural interfaces; preferred over ABCs for duck-typed APIs.

## 4. Docstrings (NumPy Style)

NumPy-style docstrings on all public functions, classes, and modules; skip trivially obvious private helpers (e.g., a 2-line `_clamp`).

```python
def calculate_metrics(
    values: list[float],
    weights: list[float] | None = None,
) -> dict[str, float]:
    """Calculate weighted summary statistics for a list of values.

    Parameters
    ----------
    values : list[float]
        Input values. Must be non-empty.
    weights : list[float] or None, optional
        Per-value weights, same length as `values`. Defaults to equal
        weighting.

    Returns
    -------
    dict[str, float]
        Dictionary with keys ``"mean"``, ``"std"``, and ``"median"``.

    Raises
    ------
    ValueError
        If `values` is empty or `weights` length does not match.

    Examples
    --------
    >>> calculate_metrics([1.0, 2.0, 3.0])
    {'mean': 2.0, 'std': 0.816..., 'median': 2.0}
    """
```

**Rules:**

- One-line summary on the same line as the opening `"""`, ending with a period; blank line between summary and any extended description.
- Document parameters, returns, and raised exceptions; add `Examples` when behavior is not obvious from the signature.
- Class docstring under the class definition; document `__init__` parameters there or in `__init__`; pick one, stay consistent within a project.

## 5. Design Principles

Structural design is owned by `software-design`: Single Responsibility, DRY (the same *fact* in two places, not lookalikes), the Rule of Three, YAGNI, KISS, composition over inheritance, minimizing coupling. The Python-specific way to make an interface hard to misuse stays here:

- **Keyword-only arguments (`*,`)**: when a function takes several parameters of the same type, make them keyword-only so callers cannot swap them by accident. Provide sensible defaults.

## 6. Performance & Efficiency

Optimize hot loops, large data, and the critical path; never at readability's expense for negligible gains, and never without measuring first.

- **Short-circuit**: cheap check before expensive, as in `if user is not None and expensive_validation(user):`. Use `any()`/`all()` (which short-circuit) over loop-and-flag.
- **`functools.lru_cache`/`cache`** for genuinely pure functions repeatedly called with the same simple hashable arguments (`int`, `str`, `tuple`, `frozenset`). Not for large mutable arguments, generator returns, or external-state dependence.
- **Hoist loop invariants**: compute once before the loop.
- **Right data structure**: `set`/`dict` O(1) membership/lookup vs `list` O(n); `collections.deque` for FIFO queues, `defaultdict` to skip key checks, `Counter` for frequencies, `bisect` for sorted lists.
- **Stdlib over hand-rolled loops**: `itertools`, `functools`, `collections`, `heapq`, `bisect`; `str.join()` for string assembly, never `+=` in a loop.
- **Generators** for large or streaming data that need not be materialized.
- **Vectorize numerical array work with NumPy**: element-wise Python loops over numbers are the most common avoidable performance bug.
- **Profile before optimizing** non-obvious hot paths: `cProfile`, `timeit`, `line_profiler`; fix the measured bottleneck, not the imagined one.

## 7. Dependency Discipline

- **Standard library first**: `pathlib`, `dataclasses`, `enum`, `itertools`, `functools`, `collections`, `concurrent.futures`, `argparse`, `json`, `csv`, `sqlite3`, `urllib`, `re`, `statistics`, `datetime` cover an enormous range of needs.
- **Common scientific stack is fine**: `numpy`, `pandas`, `scipy`, `matplotlib`, `scikit-learn`; de-facto standards, use freely when the task fits.
- **Justify niche dependencies** (install burden, security surface, version risk, abandonment); if 20 lines of stdlib replaces one, write the 20 lines.
- **Pin behavior, not exact versions, in libraries**: libraries accept a reasonable range; applications pin tightly via lockfiles.

## 8. Readability & Comments

The shared clarity-and-comments doctrine (short single-purpose functions, early returns, named intermediates in place of explanatory comments; comments say *why* not *what*, no commented-out code, TODOs with owner and ticket) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). Python adds:

- **Comprehensions only when simpler than the loop**: a 3-line comprehension with nested conditions loses to the loop.

## 9. Error Handling

Handle what is likely, document what is possible, do not paper over bugs.

- **Validate at boundaries**: public functions check arguments; private helpers trust their callers.
- **Specific exceptions, clear messages**: `raise ValueError(f"Expected positive integer, got {n}")`. `ValueError` for bad values, `TypeError` for wrong types, `FileNotFoundError` for missing files, custom subclasses for domain errors.
- **Narrow `except`**: catch the specific exception expected; never bare `except:`; `except Exception:` only as a last resort, always logged or re-raised.
- **Context managers** for resource lifecycle: `with open(...)`, `contextlib.suppress(FileNotFoundError)`, custom ones for setup/teardown. Never rely on `__del__` for cleanup.
- **Fail fast**: raise immediately; do not let bad state surface as a confusing error three layers down.
- **Do not over-engineer**: cover plausible edge cases (empty input, `None`, off-by-one boundaries); no defensive code for scenarios the contract rules out.

## 10. Safety & Robustness

- **No mutable default arguments**: `def f(items=[])` is the classic footgun; use `None`, initialize inside.
- **Never trust external input**: validate user input, file paths, API responses; use `pathlib` for path manipulation to avoid traversal bugs.
- **No secrets in code**: keys, passwords, tokens go in environment variables or a secret manager.
- **Subprocess safety**: `subprocess.run(["cmd", arg])` with a list, never `shell=True` with unsanitized input.
- **`logging` over `print`** in library or application code; `print` is fine for scripts and one-off debugging.
- **Prefer immutability where it does not hurt**: tuples over lists, `frozenset` over `set`, `@dataclass(frozen=True)` for value objects.

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

Issues: combined imports with unused and eager-heavy ones (`tensorflow`); generic names (`calc`, `data`, `t`, `d`, `res`); global dict as hand-rolled cache; triple-nested conditions with a redundant zero-check; no type hints, no docstring.

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
        Square roots of the passing values, in input order.
    """
    return [
        _sqrt_cached(record["value"])
        for record in records
        if record["value"] > threshold
    ]
```

The zero-check collapsed into `> threshold` because positivity is implied when the threshold is non-negative, an assumption to flag to the user if it might not hold.

---

## Delivering the Review

**Review mode only**: the response structure (brief assessment; the improved code as a complete, runnable replacement; key changes by category) and the mostly-fine and narrow-request provisions are defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md). Flag any assumption made on the user's behalf, like the positivity assumption above, so they can confirm or correct it. For code in a larger codebase, the specifics to ask about first are the Python version, project conventions, and existing patterns.
