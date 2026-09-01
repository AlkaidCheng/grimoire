---
name: code-polishing
description: Use whenever the user asks to review, polish, clean up, or make code PR-ready ("remove cruft", "make this PR-ready", "review pass", "clean up this mess", any pre-merge cleanup), or when a finished change has accumulated iteration artifacts to strip: LLM/conversation comments, past-PR references, dead code, stale docstrings, encapsulation violations, naming drift. Upstream of code-delivery, which packages a change and writes its commit and PR text. Owns language-agnostic structural cleanup; for design decisions (abstraction, coupling, whether to refactor first) use software-design; for style defer to python-code-review (PEP 8, typing, idioms) and cpp-code-review (clang-format, modern C++). When unsure between polishing and style, pick polishing if the ask names cleanup, artifacts, dead code, stale docs, or PR-readiness.
---

# Code Polishing

The "make it look like a human wrote it on the first try" pass: strip the traces iteration leaves (comments referencing past versions, uncalled helpers, stale docstrings, cross-module reaches). The pass serves maintainability: every artifact stripped is noise the next maintainer no longer pays for.

## Scope

**Covers** (language-agnostic structural cleanup):
1. LLM / iteration conversation artifacts
2. PR / issue references that leaked into source
3. Stale docstrings, comments, and READMEs
4. Dead code (unused branches, helpers, imports, commented-out blocks)
5. Encapsulation violations (cross-module access to `_private` names)
6. Naming consistency across an API surface
7. API renames for coherence
8. Personal / sensitive / device information in committed files
9. Docstring minimalism (user-facing reference content only)

**Does NOT cover** (hand off): formatting, type hints, docstring style, and language idioms belong to `python-code-review` / `cpp-code-review`; algorithmic improvements, API redesign, and structural-complexity reduction to `software-design`. A function tripping the complexity measures (cyclomatic, cognitive, Halstead — [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md)) is a refactoring finding, not a polishing one: restructuring control flow can change behavior, so note it and hand it off rather than let it ride a `[polish]` commit. A blended request ("polish and modernize") runs polish first, then the language review: style review on a noisy codebase wastes both passes, so one layer per pass.

**Relationship to `code-delivery`.** Stages of one pipeline: this skill changes the *content* of the code; `code-delivery` packages and ships it (gates, branch, commit and PR text, git). "Clean this up" is polishing; "fix this" / "open a PR" is delivery. Full arc: polish, then language review, then deliver. `code-delivery` owns commit/PR conventions; polishing adds only the `[polish]` prefix and the no-behavioral-change line.

**Related, but not polishing:** making a *suite* of test/benchmark scripts consistent (unifying CLI flags, sharing fixtures, a common harness) is **behavioral** work (renaming a flag breaks the old one) and belongs in `test-benchmark-harmonization` as its own `[chore]` PR. Polishing then cleans only the no-behavior residue the migration leaves (dead helpers, stale section headers, oracle docstrings naming "the old route").

## Process

Read-heavy, edit-light: most of the work is finding what to delete or fix.

1. **Read before editing.** Walk the whole package first; build a per-category list in two passes: grep-driven (the detection patterns below, every hit with file:line) and eyes-driven (docstrings against signatures, comments against the code they sit on; grep can't find a docstring that says "returns a list" when the function returns a dict).
2. **Categorize.** The category determines the commit; the commit determines review effort and blast radius.
3. **One commit per category, least-risky first**, each leaving the tree green: pure deletions (Categories 1, 2, 8: removal-only, zero behavior change), then stale-doc fixes, then dead-code removal (behavior unchanged *if you're right that it's dead*), then encapsulation fixes, then renames (caller sites; highest blast radius). Never combine categories, and never sneak a behavioral fix into a polishing commit: a real bug found while polishing goes in its own non-polishing commit (and probably its own PR).
4. **Verify after every commit**: full test suite, lint, type-check; state the result in the commit body.

Polishing-specific verification traps:

- **A comment-only change to a compiled language (C/C++/Cython) still needs a rebuild**: exactly when a stray edit slips into code. Confirm the object code is unchanged; a comment edit must not move a single instruction.
- **Deletions and renames perturb formatting** (trailing blank lines, an identifier pushed past the column limit). Run the formatter as part of verification and re-run lint after it: the formatter's fix is part of the commit.
- When the change is documentation-only and touches no source the suite imports, say so plainly ("the test suite is unaffected; N pass") rather than implying the edit was exercised.
- **Lint, types, and tests have blind spots.** They miss forward-reference evaluation in `get_type_hints()`, import-time side effects and circular-import *order*, entry-point registration, `__all__`/re-export drift after a move, and pickling of relocated classes. After a rename, an encapsulation change, or a type-alias move (Categories 5-7), add a check the gates don't give: import the public surface and call `get_type_hints()` on the touched signatures, or exercise the entry points. Verify claims about *current* behavior against the code or the built artifact, never against config or naming: "the license file isn't in the package" is confirmed by unpacking the artifact.

## Detection patterns

### Category 1: LLM / iteration artifacts

**Standard:** a docstring or comment is professional reference documentation, third-person engineering prose describing what the code *is and does*. Anything that reads as chat (addressing the reader, narrating the authoring, editorializing) is an artifact, regardless of whether it contains a flagged keyword. (Rule 1 of [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md) applied to committed source.)

Tell-tale shapes:

- Addressing an interlocutor ("as we discussed", "per your earlier note") or TODOs referencing earlier turns.
- Explaining *why we changed it* rather than *what the code does* ("Used to be X, but now Y because...").
- **Iteration labels on current code**: naming a function or path by its relation to an unstated change ("the pre-change route", "the old `_foo` flow", "the new kernel", "..., verbatim"). Common in benchmark/regression oracles reproducing the un-optimized route; the reader can't resolve the label from the repo, and it is often factually wrong (the "old path" is frequently still the current fallback). Iteration-suffixed names too: `parse_v2`, `_old`, `_legacy` without a documented versioning policy.
- Apologetic or stylistic noise ("# Note: this works", "# Sorry about the magic number") and editorial flourishes or reader asides ("the clever bit", "you'll notice", "the lever that turns X into Y"). State the mechanism plainly instead.
- **Text organized around an absent alternative**: counterfactual justification ("an empty mapping would construct a client that can never serve a request", "which is what the registry exists to prevent"), correction-of-the-past ("not a separate final tier", "no longer wraps the payload", "instead of always the first column"), and "X rather than Y, because..." apologies on private helpers. State the contract or current behavior positively and stop; the argument and the contrast belong in the commit, changelog, or PR that made the change.

**Treat removed code as if it never existed.** Nothing in source, docstrings, or tests may be organized around an absence:

- **History-defensive tests** are artifacts: `assert not hasattr(obj, 'removed_method')`, a `pytest.raises` on a deleted option, a parametrization proving formerly-reserved names are "ordinary now". Delete them; a fresh author would never write them. (A test of a *replacement behavior* is fine; a test of an *absence* is not.)
- Tests named or docstringed by the transition ("TestLegacyOptionRemoved") get present-tense identities describing the current contract.
- The removal narrative lives in exactly three places: the commit message, the changelog entry, and the PR/MR description. Everywhere else, write as if the current design is the only one that ever existed.

Detection:
```bash
rg -n "as (we|i) (mentioned|discussed|noted)|(your|our|previous|earlier|last) (note|comment|iteration|conversation)" -tsrc
rg -n "used to be|\b(v2|_v2|_new|_old|_legacy|_tmp)\b" -tsrc
rg -n "pre-change|the (old|new|replaced) (path|route|flow|kernel|gate|logic)|, verbatim|now uses|which (now|previously)" -tsrc
rg -n "would (construct|break|crash|refuse|silently)|exists to prevent|rather than .*because" -tsrc
rg -n "not a |no longer|instead of (always|the old)|replacing the" -tsrc   # then apply the meaning test
rg -n "hasattr.*not|not hasattr|Removed\b|_is_gone|is_removed" tests/
```

Read each hit; delete, or rewrite to document the code rather than its history:

- **The new-teammate test.** Every word must resolve for someone reading only the repo: no commits, no conversation.
- **Label vs. narrative.** An iteration *label* ("the old `_foo` route") is reworded to what the thing *is* ("the NumPy reference route"). A self-contained *narrative* explaining a design or what a check guards is legitimate; don't strip motivation, do fix unresolvable labels.
- **Verify before relabeling.** Grep for the symbol a comment calls old/removed: it may still exist (then "old" is simply wrong) or be gone (a ghost reference; Category 3). The grep tells you the correct rewrite.
- **False-positive guard.** Editorial "we" ("so we don't import pandas at load") is normal voice; "previously", "no longer", "rewritten in place" are fine when they state a fact about current behavior or a contract ("release a previously-acquired lock") rather than narrate an edit. Trust the meaning, not the keyword.

### Category 2: PR / issue references in source

PR numbers, issue references, and reviewer names belong in commit messages and PR descriptions, not the source tree: "see PR #142" is opaque in five years. Replace with the in-code reason ("bounded to 4096 because larger values trigger ENOMEM on macOS", if that is actually why), or delete when the code is self-explanatory.

```bash
rg -n "(#|PR |issue |fixes #|closes #)[0-9]+" src/
rg -n "(per |from |see )(PR|@[a-z]+)" src/
```

### Category 3: Stale docstrings, comments, READMEs

**The highest-yield stale doc is the one a recent change just created.** After any implementation change, re-read the comments in and around the diff before scanning the rest of the package, and grep the touched files for the nouns that named the old approach.

Mostly manual reading: parameter names against the signature; Returns/Raises against the body's `return`/`raise` statements; inline comments that lie ("iterate from 1 because 0 is reserved" over a loop starting at 0 — trust the code, fix the comment); READMEs describing the pre-rename API. Grep hints: the pre-rename names in `src/`, and `git diff <merge-base> -- README.md` for what wasn't updated.

**Structural reorganization** (distinct from stale-content fixing) is reorder + group + add a table of contents, and must be **content-preserving**: diff each section body against the original to prove no silent loss. Renaming or re-leveling a heading changes its anchor; compute the new anchor (GitHub rendering: lowercase, drop characters outside `[\w\s-]`, spaces to hyphens, `&` to `--`) and grep for inbound `#anchor` links first.

**Changelog entries follow `code-delivery`'s standard** (one user-facing sentence naming the surface); mechanism enumerations and per-site lists are PR-description material that leaked, trimmed at write time before they accumulate.

### Category 4: Dead code

Flavors:

- **Unused imports and locals**: ruff F401/F841 (Python); clang-tidy, `-Wunused-variable` (C/C++).
- **Format-string artifacts**: f-strings with no `{}` interpolation (ruff F541); use a regular string.
- **Unreachable branches**: coverage reports (`pytest --cov`, `gcov`) show 0 hits across all tests; contradictory guards too, e.g. `if version not in {1}: raise ...` followed by a `match version` that handles only version 1.
- **Commented-out code**: blocks that look like code rather than prose.
- **Helpers called only by themselves or by other dead helpers**: for a small codebase, grep each helper's name; one hit (the definition) means dead.
- **Helpers orphaned by a migration**: every caller switched to the new path (a per-script `main()` driver once every script adopts the shared harness); the helper still looks load-bearing, and only a repo-wide caller grep reveals it has no callers.
- **Stale section headers**: a banner comment like `# ---- Script driver and store context managers ----` left standing after the context managers moved. Update it, or drop it with the code it described.

```bash
ruff check src/ --select F401,F841,F541
rg -n "^\s*(#|//) .{0,40}[(){};:=]" src/  # commented-out code heuristic
```

Confirm "dead" by grepping callers across the whole repo — tests, benchmarks, examples, **and the defining module's own internal use**. The reliable signal: the symbol appears only at its definition (and its `__all__`/export entry). Remove that export entry in the same commit; a dangling export of a deleted name breaks import.

### Category 5: Encapsulation violations

Module A reaches into module B's `_private` attribute. The fix is rarely "make the attribute public"; usually "extract a function exposing the *behavior* the caller needs". Structural, not cosmetic: a dedicated polishing commit.

```bash
rg -n "from \S+ import _[a-zA-Z]" src/
rg -n "\b[a-z_]+\._[A-Z_]+\b" src/  # tweak per language
```

### Categories 6 and 7: Naming consistency, and the renames that fix it

Read the public API surface together; pairs and series follow one pattern: one verb per operation kind (`read_X` vs `load_X` vs `fetch_X`), inverse pairs (`to_X`/`from_X`, `acquire_X`/`release_X`), plural for collections, boolean prefixes (`is_X`, `has_X`, `should_X`). No grep finds an inconsistent verb choice: list the public functions and read them. The rename lands as one commit per API surface (never bundle unrelated renames), touching every call site including tests, benchmarks, examples, and docs.

### Category 8: Personal / sensitive / device information

A committed file (source, **test**, config, docstring, or doc) ships to everyone who clones the repo: no real names, usernames, emails, host paths, hostnames, IPs, machine/hardware specs, or secrets; neutral placeholders instead. Scrub hardware *identity* (CPU model, hostname, home paths) but keep a measurement *parameter* a claim depends on (the thread count that makes "6x slower" interpretable). Full rule, with the identity-vs-parameter test and the maintainer-attribution exception, in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md). Read-and-judgment work; removal-only, so it rides in the same first commit as Categories 1/2.

### Category 9: Docstring minimalism

Three standards, applied to every docstring, public and private:

1. **Document what a user of the API needs**: what the thing does, parameters/returns/raises, essential usage constraints. Cut anything only useful to someone editing the implementation.
2. **Implementation details do not surface**, with one exception: a *non-trivial* detail a user must know to use the API correctly stays ("the returned object is a copy", "a None key is refused"). Internal mechanics (which helper does the work, merge orders, resolution walk-throughs) go.
3. **Reference prose only** (Category 1 applied to docstrings): no design arguments, essays, reader asides, or provenance; third person throughout.

Calibration: a one-sentence docstring is ideal, not underdone. A 30-line docstring on a private helper is an essay wearing a docstring's clothes; compress to its behavioral facts and keep every fact. Framework/base-class docstrings legitimately carry more contract detail when the contract *is* the user-facing API (an override hook's obligations, a key grammar users write against). Where the project builds API docs from docstrings, run that build as this category's formatting gate, and prove a docstring-only edit with a docstring-stripped AST comparison rather than by eyeballing the diff.

## Commit message style for polishing

Follow `code-delivery`'s conventions; polishing adds two things: the **subject prefix `[polish]`** (or `chore:` under Conventional Commits), the reviewer signal for "no behavior change, light review"; and **a body line stating the no-change contract** ("No behavioral change. <N> tests pass." or "Behavior unchanged; <the structural change and why>.").

````markdown
[polish] Drop module-private access from exporter to store

`exporter.py` reached into `store._HEADER_OFFSET`, making a
store-internal constant part of the exporter's contract. Replaced
with `store.read_header(fp)` / `store.write_header(fp, ...)`, which
own the offset arithmetic.

No behavioral change. The suite passes; lint/format/type-check clean.

Files:
  * src/<pkg>/store.py       (+ read_header, write_header)
  * src/<pkg>/exporter.py    (use the new helpers)
````

"No behavioral change" is the reviewer's permission to skim. Earn it.

## Quick checklist before sending a polishing PR

- [ ] Two reading passes done: grep-driven + eyes-driven
- [ ] Docstrings/comments read as professional reference prose: no conversational artifacts, reader asides, editorial flourishes, or edit-history narration; no text organized around removed code (Category 1)
- [ ] No personal/sensitive/device info in any committed file: identifiers, machine/hardware specs, host paths, secrets (Category 8)
- [ ] Findings categorized; one commit per category
- [ ] Commits ordered least-risky to most-risky
- [ ] Full test suite + lint + type-check pass after each commit
- [ ] Each commit body says "no behavioral change" (or explicitly describes the structural change)
- [ ] No bug fixes or control-flow restructuring smuggled into polishing commits; complexity findings noted and handed off
- [ ] Hand-off to the appropriate language-specific skill noted in the PR description, if a style pass should follow
