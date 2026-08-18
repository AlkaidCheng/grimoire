# Human-facing artifacts: no process leak, no personal info

The canonical rule for **everything a human reads**: the PR text artifacts (branch name, commit messages, PR title, PR description), committed source (code, comments, docstrings, tests, config, docs), and handoff documents. Referenced by `code-delivery` (the text artifacts it authors), `code-polishing` (the committed source it cleans), and `session-handoff` (the handoff doc); each applies it to its own surface. Three hard rules, checked every time.

Write as the engineer who owns the change, for the engineer who will review it: someone with **no knowledge of how the change was produced**. They never saw a conversation, a prompt, a skill, or any tool; only the repository.

## Rule 1: never leak the production process

No committed file, commit message, branch name, PR title, PR description, or handoff doc may reference:

- **Internal tooling, skills, or process names**: e.g. `python-code-review`, `cpp-code-review`, `code-delivery`, "the polishing skill", "the review pass", "per the skill". A reviewer cannot resolve these names; they read as noise and expose the text as machine-generated.
- **Internal decomposition labels**: "Band A", "Phase 2", "Round 3", "the cleanup pass", "step 1 of the refactor". These leak most often because they read like natural section headers, yet a reviewer has no plan to map them onto. A PR named by its *position in your plan* ("Band A: docs cleanup") must be reworded to the *change itself* ("Remove stale docs and dead code").
- **The assistant or its nature**: no "as an AI", "I generated this", "this was produced by", the assistant's or model's product name, "the model", or any first-person-assistant framing. This includes commit metadata: **no AI co-author trailer (`Co-Authored-By: <assistant>`)**; commits are attributed to the human author only.
- **The conversation that produced the change**: no "as discussed", "as you asked", "per your request", "you wanted me to", "the user requested".
- **Meta-commentary about generation**: no "auto-generated", "drafted for you", "if wanted", "let me know if you'd like", "hope this helps".

The *substance* behind such a note is often legitimate; it's the *reference* that's forbidden. Rephrase in plain engineering terms:

> Bad: "A language-specific style pass (`python-code-review` for `utils.py`, `cpp-code-review` for `kernel.cpp`) can follow if wanted."
>
> Good: "Scope is limited to structural cleanup with no behavior change; formatting and idiom-level changes are intentionally left to a separate pass."

The good version conveys the same plan (follow-up style work is out of scope) without naming a tool only the author's toolchain knows. The same applies to branch names and titles: `polish/strip-llm-artifacts` leaks; `polish/docstrings-stale-docs-dead-helpers` describes the work.

**In committed source specifically**: docstrings and comments are permanent reference documentation read by every future maintainer. They must describe the code in professional, third-person engineering prose, never read as a conversation with a developer or a record of how the change was authored. Beyond the references above, that means no first-person "we did not expect", no editorial flourishes ("the lever that turns...", "the row that matters"), no asides addressed to the reader, and no history-narration of an edit in place of describing current behavior. Write what the code *is and does*, not what changed or why-for-you.

**The test:** would a teammate who just joined, reading only the repo, understand every word? If a term makes sense only to someone who watched the change being generated, delete it.

## Rule 2: never expose personal, sensitive, or device information

No committed file (source, **test**, config, docs), commit message, branch name, PR title, PR description, or handoff doc may contain:

- **Personal identifiers**: the developer's real name, username, handle, or email, or any value derived from them. A test path like `/envs/<username>`, a home directory like `/Users/jdoe/...`, or an env value carrying a username all leak identity.
- **Device / environment specifics**: absolute machine paths, usernames embedded in paths, hostnames, IP addresses, the developer's specific machine or hardware configuration (CPU model, filesystem, exact specs), or other host details. Keep performance notes generic ("the local dev machine", "the target node"); a benchmark printing host details at *runtime* is fine, baking them into prose is not.
- **Secrets**: tokens, API keys, passwords, credentials.

Use neutral placeholders instead: `/opt/env`, `/path/to/project`, `/data`, `example.com`, `$HOME`, a generic `user`. This applies to **test fixtures and example configs** as much as to prose: a string in a unit test ships to everyone who clones the repo. Deliberate, maintainer-approved attribution (a `LICENSE` copyright holder, a `pyproject` author field the maintainer chose) is exempt; when unsure whether a value is approved, ask before publishing.

**Hardware *identity* vs measurement *parameter*.** Scrub what identifies the machine or author: CPU model/brand, hostname, username, home-directory paths. Do **not** scrub a quantity a stated claim depends on: a thread/core count, row count, byte size, or iteration count that makes a number or ratio interpretable. A comment like "8 vs 64 threads ~6x slower" becomes meaningless if the counts are replaced with "the full thread count". Test: would deleting the value make a quantitative claim unverifiable? Then it is a parameter; keep it. The hardware that *produced* a number is identity; the number's *parameters* are not.

This is read-and-judgment work, not a fixed pattern: scan paths, fixtures, and prose for anything that identifies the author or their machine, rather than relying on a brittle keyword list (and never hard-code the developer's identifiers into the scan). It is removal-only and behavior-neutral.

## Rule 3: plain ASCII, and no em-dashes

Every artifact is written in printable ASCII. Non-ASCII typography survives round-trips badly (terminals, diffs, patch files, commit hooks, and code review tools all mangle it differently) and it is a reliable tell of machine-generated text.

- **No em-dash or en-dash.** This is a rule about sentence construction, not about find-and-replace: a `--` or a spaced hyphen standing in for an em-dash breaks it just as surely. Restructure instead. A parenthetical pair becomes commas or parentheses; a dash introducing an elaboration, a consequence, or a definition becomes a colon, a semicolon, or a second sentence. A hyphen keeps only its ordinary jobs: compound modifiers (`read-only`), numeric ranges (`1-3`), and literal code or data (CLI flags such as `--strict`, YAML `---` markers, table separator rows, diff headers).
- **Other characters**: arrows become `->` in code and a word ("to", "then", "becomes") in prose; write `...` for an ellipsis, `x` for a multiplication sign, `<=` and `>=` for the comparison glyphs, and the word "section" for a section sign. Curly quotes and non-breaking spaces become their ASCII equivalents.
- **In source files**, a non-ASCII character that is genuinely data (a test fixture asserting on Unicode input, a regex matching a real em-dash in third-party text) stays, but written as an escape (`\u2014`) so the file itself remains ASCII.

Check with `LC_ALL=C grep -nP '[^\x00-\x7F]'` over changed files, then re-read the prose for double hyphens doing a dash's job, which no character-class check will catch.
