# Naming, clarity, and comments

The canonical doctrine for names, structural clarity, and comments, independent of language. Referenced by `python-code-review`, `cpp-code-review`, and `software-design`; each keeps its language-specific rules (casing and loop variables; getters, template parameters, Doxygen) inline.

## Naming

Names are the most important documentation; a good name removes the need for a comment.

- **Specific, not generic**: `retry_count` not `cnt`, `user_email` not `data`, `max_connections` not `n`. Avoid `data`, `info`, `result`, `tmp`, `val`, `obj`, `item`, `x` as substantive names; use `user_records`, `weighted_mean`, `pending_orders`. Generic names only in very short scopes: a one-line comprehension or lambda, a 2-line helper.
- **Functions describe actions and start with a verb**: `fetch_user_profile`, `validate_email`, `parse_config`, not noun-only `user_profile()`.
- **Booleans read as questions**: `is_valid`, `has_permission`, `should_retry`, `was_modified`; boolean functions as predicates: `is_empty()`, `contains()`, `has_children()`.
- **Match domain vocabulary**: the field's "ledger" is not `record_list`; its "spike" is not `event`.

## Clarity that replaces comments

Code is read far more often than written; optimize for the reader.

- **Short functions doing one thing**: a comment separating "phases" inside a function means those phases are probably separate functions.
- **Early returns**: handle invalid inputs and edge cases up front so the main logic sits at base indentation; refactor past three levels of indentation.
- **Name intermediate values**: an expression complex enough to need an explanatory comment becomes named variables: the name is the comment.

## Structural complexity: three measures

The clarity moves above have measurable counterparts. When a function feels hard to follow, these name why, and each points at its fix:

- **Cyclomatic complexity**: the number of independent paths through a function; each `if`, loop, `case`, and boolean operator adds one. Its focus is control flow, which makes it the measure for planning test cases and judging coverage: every path is a case to cover. Keep functions in the single digits by extracting decision logic and collapsing redundant branches.
- **Cognitive complexity**: how difficult the code is for a person to read, understand, and maintain. Control flow contributes — a condition inside a loop inside a condition costs more than the same three in a row — but so do unclear names, missing or misleading docstrings and comments, and tangled decomposition. Its focus is human mental overhead, which makes it the measure of long-term maintainability. Reduce it with early returns and flattened nesting, names that carry their meaning, documentation that matches the code, and simpler decomposition; automated checkers count only the control-flow share.
- **Halstead difficulty**: how dense the expressions are, from the count of distinct operators and operands and how often operands repeat. A long expression juggling many symbols is hard to verify at a glance: name intermediate values and split compound expressions — the same move that replaces explanatory comments.

Write for the minimum of all three that still reads naturally: minimal structural complexity, easy to understand, and above all easy to maintain — code is written once and maintained for years, so ease of maintenance outranks cleverness and brevity. A metric is a tripwire for a refactor, not a score to chase.

## Comments

Comment only what the code cannot say; every comment can rot into a lie.

- **Why, not what**: "Retry with backoff because the upstream service rate-limits aggressively" is useful; "Increment counter" is noise.
- **Delete commented-out code**: version control keeps it.
- **TODOs carry context**: `TODO(username): Remove after migration to v2 API (tracked in PROJ-1234)`. Orphan TODOs with no owner or ticket are clutter.
