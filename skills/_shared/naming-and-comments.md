# Naming, clarity, and comments

The canonical doctrine for names, structural clarity, and comments, independent of language. Referenced by `python-code-review` and `cpp-code-review`; each keeps its language-specific rules (casing and loop variables; getters, template parameters, Doxygen) inline.

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

## Comments

Comment only what the code cannot say; every comment can rot into a lie.

- **Why, not what**: "Retry with backoff because the upstream service rate-limits aggressively" is useful; "Increment counter" is noise.
- **Delete commented-out code**: version control keeps it.
- **TODOs carry context**: `TODO(username): Remove after migration to v2 API (tracked in PROJ-1234)`. Orphan TODOs with no owner or ticket are clutter.
