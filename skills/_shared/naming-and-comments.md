# Naming, clarity, and comments

The canonical doctrine for names, structural clarity, and comments, independent of language. Referenced by `python-code-review`, `cpp-code-review`, and `software-design`; each keeps its language-specific rules (casing and loop variables; getters, template parameters, Doxygen) inline.

## Naming

Names are the most important documentation; a good name removes the need for a comment.

- **Specific, not generic**: `retry_count` not `cnt`, `user_email` not `data`, `max_connections` not `n`. Avoid `data`, `info`, `result`, `tmp`, `val`, `obj`, `item`, `x` as substantive names; use `user_records`, `weighted_mean`, `pending_orders`. Generic names only in very short scopes: a one-line comprehension or lambda, a 2-line helper.
- **Say which representation the value is.** A bare noun is the parsed data (`config`, `schema`, `records`); the raw text is `config_text`; the location of a file is `config_path`; a directory is `config_dir` or an established directory word (`workdir`, `outdir`). Never `_file`, which could mean the handle or the path, and never `_path` on a directory. A name that leaves the reader guessing between the data and where it lives (`image` for a parameter that takes a file) is wrong even when the type annotation settles it.
- **Functions describe actions and start with a verb**: `fetch_user_profile`, `validate_email`, `parse_config`, not noun-only `user_profile()`. The exception is a function that computes a value from its arguments and does nothing else (`total_price(order)`, `display_name()`): it may be named for what it returns, as a property would be. The verb is owed when the call does work the caller should notice: reads a file, runs a program, changes state.
- **One verb per kind of operation, package-wide.** Choose the verb by what the input is and keep it; a package's established vocabulary wins over this list: `parse_` takes text and returns a structure, `read_` and `write_` move between a file and the data, `format_` turns a value into display text, `make_` constructs, `require_` checks and returns its argument, `as_` and `to_` convert. `read_header` on a function that takes a string lies about its input, and two verbs for one operation (`read_config` beside `load_settings`) send the reader looking for a difference that is not there.
- **Booleans read as questions**: `is_valid`, `has_permission`, `should_retry`, `uses_cache`, `was_modified`; boolean functions as predicates: `is_empty()`, `contains()`, `has_children()`.
- **Quantities carry their unit and their statistic**: `timeout_seconds`, `peak_memory_mib`. `max_memory_mb` for a high-water mark measured in MiB is wrong twice, and `size` without a unit is a question at every call site.
- **One spelling per idea, on every surface.** When one concept appears as a command, a flag, a configuration key, a record key, a directory and an identifier, it gets one name (`--log-level`, `log_level`, `log_level`), so the reader never maps between names for the same thing. Name a step after the action the user invokes (`export`), not after the tool that performs it (`pandoc`); the tool belongs in the description.
- **The exact word, not a near one.** A name states what the code established, not an attitude or a placeholder: `unconfirmed` for what a check could not confirm, not `doubtful`; `created` for a time of creation, not `moment`; a module named for what it holds (`schema.py`), not for one verb it performs (`validate.py`). Prefer the name a reader from another project would guess first (`created_at`, `user_id`, `retry_count`) over an invented one.
- **Match domain vocabulary**: the field's "ledger" is not `record_list`; its "spike" is not `event`; and a module that handles the field's `Makefile` is `makefile.py`, not `buildscript.py`.

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
