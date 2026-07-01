---
name: code-polishing
description: Use whenever the user asks to review, polish, clean up, or make code PR-ready ("remove cruft", "make this PR-ready", "review pass", "clean up this mess", any pre-merge cleanup), or when a finished change has accumulated iteration artifacts to strip — LLM/conversation comments, past-PR references, dead code, stale docstrings, encapsulation violations, naming drift. Upstream of code-delivery, which packages a change and writes its commit and PR text. Owns language-agnostic structural cleanup; for style defer to python-code-review (PEP 8, typing, idioms) and cpp-code-review (clang-format, modern C++). When unsure between polishing and style, pick polishing if the ask names cleanup, artifacts, dead code, stale docs, or PR-readiness.
---

# Code Polishing

The "make it look like a human wrote it on the first try" pass. Iteration leaves traces — comments referencing past versions, helpers that aren't called anymore, docstrings that describe last week's behavior, modules reaching across module boundaries because it was easier than refactoring. This skill is the dedicated pass for stripping those traces.

## Scope

**This skill covers** (language-agnostic structural cleanup):
1. LLM / iteration conversation artifacts
2. PR / issue references that leaked into source
3. Stale docstrings, comments, and READMEs
4. Dead code (unused branches, helpers, imports, commented-out blocks)
5. Encapsulation violations (cross-module access to `_private` names)
6. Naming consistency across an API surface
7. API renames for coherence
8. Personal / sensitive / device information in committed files

**This skill does NOT cover** (language-specific — hand off):
- Formatting (Black, clang-format, PEP 8): → `python-code-review` / `cpp-code-review`
- Type hint completeness, NumPy-style docstrings, modern Python idioms: → `python-code-review`
- RAII, `std::optional`, `constexpr`, modern C++ idioms: → `cpp-code-review`
- Algorithmic improvements or API redesign

If the request blends both layers ("polish and modernize"), run polishing first (this skill), then the language-specific review. Polishing reduces noise; style review on a noisy codebase wastes both passes.

**Relationship to `code-delivery`.** Polishing and delivery are stages of one pipeline, not competitors. This skill changes the *content* of the code — removing artifacts, dead code, stale docs, encapsulation and naming drift; `code-delivery` packages and ships whatever change exists, running the gates, authoring the branch, commit, and PR text, and invoking git. Trigger cue: "clean this up" is polishing; "fix this" or "open a PR" is delivery. When a request spans the whole arc ("clean it up **and** ship it"), run the stages in order — **polish** (this skill, content cleanup) → **language-style pass** (`python-code-review` / `cpp-code-review`, only when style work is wanted) → **deliver** (`code-delivery`, last, since it packages the finished result). Follow `code-delivery` for the commit-message and PR-text conventions; polishing adds only the `[polish]` prefix and the "no behavioral change" line.

## Process

Polishing is read-heavy and edit-light. Most of the work is finding things to delete or fix; the actual edits are usually one-liners.

### 1. Read before editing

Walk the whole package before touching a single file. Build a list per category. The list will be longer than you expect — surfaces like docstrings hide drift that grep won't catch.

Two reading passes:
- **First pass — grep-driven.** Run the detection patterns below across the codebase. Capture every hit with file:line.
- **Second pass — eyes-driven.** Open each public-facing file and read the docstrings against the signatures. Read the comments against the code blocks they sit on. Grep can't find a docstring that says "returns a list" when the function returns a dict.

### 2. Categorize

Group findings by the seven categories above. The category determines the commit; the commit determines the review effort and blast radius.

### 3. One commit per category, ordered least-risky to most-risky

The order matters because each commit must leave the tree green for the next:

1. **Pure deletions** — LLM artifacts, PR refs, personal/device info (Category 8), dead comments. Diff is removal-only. Zero behavior change. Almost no review needed.
2. **Stale-doc fixes** — docstring/comment updates. Still no behavior change, but the reviewer has to confirm the new wording matches the code.
3. **Dead-code removal** — unused imports, branches, helpers. Behavior unchanged *if you're right that it's dead*. Reviewer has to confirm.
4. **Encapsulation fixes** — replace cross-module `_private` access with a proper API. May involve adding a small public function. Tests should pass without changes.
5. **Renames** — API renames for coherence. Touches caller sites. Highest blast radius; do last.

Don't combine categories. Don't sneak a behavioral fix into a polishing commit. If you find a real bug during polishing, note it and address it in a separate non-polishing commit (and probably a separate PR).

### 4. Verify after every commit

Run the full test suite, lint, and type-check after each commit. State the result in the commit body: `the suite passes; no behavior change.` This is the contract that makes a polishing PR easy to review.

Two traps specific to polishing edits:
- **A comment-only change to a compiled language (C/C++/Cython) still needs a rebuild.** "It's just a comment" is exactly when a stray edit to a `//` line slips into code, or the file fails to recompile. Rebuild and confirm the object code is unchanged (a comment edit must not move a single instruction).
- **Deletions and renames perturb formatting.** Removing the last function in a file can leave a trailing blank line; renaming to a longer identifier can push a call past the column limit. Run the formatter (black / clang-format) as part of verification — and re-run lint after it, since the formatter's fix is itself part of the commit.

When the change is documentation-only and touches no source the test suite imports (e.g. benchmark-script docstrings), say so plainly — "the test suite is unaffected; N pass" — rather than implying the edit was exercised.

**Lint, types, and tests have blind spots; some refactors need a targeted runtime check.** They miss: forward-reference evaluation in `get_type_hints()`; import-time side effects and circular-import *order*; entry-point / plugin registration; `__all__` / re-export drift after a move; pickling of relocated classes. After a rename, an encapsulation change, or a type-alias move (Categories 5–7), add a check the gates don't give you — import the public surface and call `get_type_hints()` on the touched signatures, exercise the entry points, or run an independent review. And verify claims about *current* behavior against the code or the built artifact, not against config or naming: "this path emits no footer" / "the license file isn't in the package" are confirmed by reading the function or unpacking the artifact, never inferred from a settings list.

## Detection patterns

### Category 1: LLM / iteration artifacts

**Standard:** a docstring or comment is professional reference documentation, not a conversation between an assistant and the developer. It describes what the code *is and does* in third-person engineering prose. Anything that reads as chat — addressing the reader, narrating the authoring, editorializing — is an artifact, regardless of whether it contains a flagged keyword.

The tell-tale shapes:
- Comments addressing a past or imagined interlocutor: "as we discussed", "per your earlier note", "following our conversation", "as mentioned"
- Comments that explain *why we changed it* rather than *what the code does*: "Used to be X, but now Y because…"
- **Iteration labels on code that still exists**: naming a current function, path, or helper by its relation to an unstated change — "the pre-change route", "the old `_foo` flow", "the replaced path", "the new kernel", "…, verbatim", "which now uses Y". Especially common in benchmark/regression-check *oracles* that reproduce the un-optimized route to compare against. The reader can't resolve "pre-change"/"old"/"replaced" from the repo, and the label is often *factually* wrong — the "old path" is frequently still the current fallback.
- Iteration-suffixed names: `module_new.py`, `parse_v2`, `_old`, `_legacy` when no documented versioning policy applies
- TODOs referencing earlier turns: `# TODO: as you said, switch this to ...`
- Apologetic or stylistic noise: `# Note: this works`, `# Yes, this is intentional`, `# Sorry about the magic number here`
- Editorial / marketing flourishes and reader asides that don't describe the code: "the lever that turns X into Y", "the row that matters", "this is the clever bit", "fall back rather than guess", "you'll notice". State the mechanism plainly instead — "uses copy_file_range, which reflink filesystems complete near-metadata-only", "falls back to the materializing write".

Detection:
```bash
rg -n "as (we|i) (mentioned|discussed|noted)" --type-add 'src:*.{py,cpp,h,hpp,rs,go,js,ts}' -tsrc
rg -n "(your|our|previous|earlier|last) (note|comment|iteration|conversation)" -tsrc
rg -n "used to be" -tsrc
rg -n "\b(v2|_v2|_new|_old|_legacy|_tmp)\b" -tsrc
rg -n "pre-change|the (old|new|replaced) (path|route|flow|kernel|gate|logic)|, verbatim|now uses|which (now|previously)" -tsrc
```

Then read each hit and decide: delete, or rewrite to document the code rather than its history. Three rules sharpen the call:

- **The new-teammate test.** Would someone reading only the repo — no commits, no conversation, no chat — understand every word? If a phrase resolves only for someone who watched the change happen ("pre-change", "the replaced route", "as discussed"), it fails; rewrite it.
- **Label vs. narrative.** An iteration *label* on a thing ("the old `_foo` route") is an artifact — reword it to say what the thing *is* ("the NumPy reference route", "the general gather route", "the full-scan gate"). A self-contained *narrative* that explains a design or states what a check guards ("previously this ran an O(R log K) partition; the walk kernel replaces it, which is what this check verifies") is legitimate: it reads fine to a newcomer and documents intent. Don't strip motivation; do fix unresolvable labels.
- **Verify before relabeling.** Before "fixing" a comment that calls something old/removed, grep for the named symbol. It may still exist (then "old" is simply *wrong*, not merely iteration-flavored), or be genuinely gone (a ghost reference — see Category 3). Either way the grep tells you the correct rewrite.

Guard against false positives: don't strip legitimate technical prose just because it contains a temporal keyword. Editorial "we" in implementation comments ("so we don't import pandas at load") is normal voice. "previously", "no longer", "rewritten in place", "previously-acquired", "used to bound" are fine when they state a *fact about current behavior or a contract* ("the counters block is rewritten in place on close"; "release a previously-acquired lock"; "used to bound the copy" = *used in order to* bound) rather than narrate an edit. Trust the meaning, not the keyword.

### Category 2: PR / issue references in source

PR numbers, GitHub issue references, and reviewer names belong in commit messages and PR descriptions, not in the source tree. Source comments outlive the PR system; a comment saying "see PR #142" is opaque to a reader in five years.

Detection:
```bash
rg -n "(#|PR |issue |fixes #|closes #)[0-9]+" src/
rg -n "(per |from |see )(PR|@[a-z]+)" src/
```

Each hit: replace the reference with an in-code explanation, or delete if the surrounding code is self-explanatory. "See PR #142" → "We bound this to 4096 because larger values trigger ENOMEM on macOS" (assuming that's actually why).

### Category 3: Stale docstrings, comments, READMEs

**The highest-yield stale doc is the one a recent change just created.** When a commit changes an algorithm or behavior, the comment or docstring sitting on that code now describes the *old* mechanism. After any implementation change — yours or a prior PR in the same arc — re-read the comments in and around the diff before scanning the rest of the package. A perf change from a 64-bit division to a reciprocal multiply, for example, leaves the kernel header still claiming "the binary search replaced by one integer division". Grep the touched files for the nouns that named the old approach.

The hardest category to detect with grep. Sub-patterns:

- **Parameter names that don't match the signature.** If a docstring lists `count, value` but the function takes `n, val`, somebody renamed and didn't update.
- **Returns/Raises sections that don't match reality.** Read the function body's `return` and `raise` statements and check the docstring claims them.
- **Inline comments that lie.** Comment says "iterate from 1 because 0 is reserved" but the loop starts at 0. Trust the code, fix the comment.
- **READMEs that describe the old API.** Especially common after renames. The README is rarely covered by tests.

Detection is mostly manual reading. Some grep-level hints:
```bash
# Find docstrings that mention method names that no longer exist
rg -n "old_name_a|old_name_b" src/  # the pre-rename names
# Find sections of README that talk about removed features
git diff <merge-base> -- README.md  # see what was/wasn't updated
```

**Structural reorganization (distinct from stale-content fixing).** A document can be accurate yet disorganized — a flat run of sections, no navigation, usage interleaved with internals. Reorganizing is reorder + group + add a table of contents, and it must be **content-preserving**: diff each section body against the original to prove no silent loss. Two hazards: (a) renaming or re-leveling a heading changes its anchor — compute the new anchor (for a GitHub-rendered doc: lowercase, drop characters outside `[\w\s-]`, spaces→hyphens, `&`→`--`) and grep the repo for inbound `#anchor` links before renaming; (b) for a long document, a grouped table of contents is navigation, not decoration.

### Category 4: Dead code

Several flavors:

- **Unused imports**: ruff/pyflakes (F401) for Python; clang-tidy for C++.
- **Unused locals**: ruff F841 (Python); `-Wunused-variable` (GCC/Clang).
- **Unreachable branches**: harder to detect automatically — read coverage reports (`pytest --cov`, `gcov`) and look for branches with 0 hits across all tests.
- **Commented-out code**: ripgrep for blocks of `^\s*#` (Python) or `^\s*//` (C++) that look like code rather than prose.
- **Helpers called only by themselves or by other dead helpers**: requires reverse-call-graph inspection. For a small codebase, grep each helper's name; if it appears once (the definition), it's dead.
- **Helpers orphaned by a migration**: after a consolidation or API move, a helper whose callers all switched to the new path is dead even though it looked load-bearing last month — a per-script `main()` driver once every script adopts the shared harness, a `best_time` primitive once the wrappers that called it are gone. The function still looks reasonable in isolation; only a repo-wide caller grep reveals it has none.
- **Stale section headers**: a banner comment like `# ---- Script driver and store context managers ----` left standing after the context managers moved to another module. The header now over-promises. Update it, or drop it with the code it described.
- **Conditional branches that can't be reached**: e.g., `if version not in {1}: raise ...` followed by a `match version` that handles only version 1.
- **Format-string artifacts**: Python f-strings with no `{}` interpolation (ruff F541). Just use a regular string.

Detection:
```bash
ruff check src/ --select F401,F841,F541  # Python dead-code rules
rg -n "^\s*(#|//) .{0,40}[(){};:=]" src/  # heuristic for commented-out code
```

Always confirm "this looks dead" by grepping for callers across the whole repo — tests, benchmarks, examples, **and the defining module's own internal use**. A helper can be unused by every other file yet still called within its own module; conversely a re-exported name may have zero external callers but be exercised by a test. The reliable signal: the symbol appears only at its definition (and its `__all__`/export entry) and nowhere else. When you remove such a name, remove its `__all__`/export entry in the same commit — a dangling export of a deleted name breaks import.

### Category 5: Encapsulation violations

Symptom: module A reaches into module B's `_private` attribute. Usually a sign that B should have a small public function exposing the value, and A should call it.

Detection:
```bash
# Imports of single-underscore names from other modules
rg -n "from \S+ import _[a-zA-Z]" src/
# Attribute access to single-underscore names on another module
rg -n "\b[a-z_]+\._[A-Z_]+\b" src/  # tweak per language
```

The fix is rarely "make the attribute public". It's usually "extract a function that exposes the *behavior* the caller actually needs". This is structural, not cosmetic — easier to do as a dedicated polishing commit than mixed into something else.

### Category 6: Naming consistency

Read the public API surface together. Pairs and series should follow one pattern:

- Verbs for similar operations: `read_X` vs `load_X` vs `fetch_X` — pick one
- Inverse pairs: `to_X` / `from_X`, `open_X` / `close_X`, `acquire_X` / `release_X`
- Plural vs. singular: `users` is a collection, `user` is one
- Boolean prefixes: `is_X`, `has_X`, `should_X`

There's no grep for "your verb choice is inconsistent" — this is a reading-and-judgment task. List the public functions in a flat file, look for the inconsistency, propose a rename.

### Category 7: API renames

Often falls out of category 6 — once you've spotted the inconsistency, the rename is the fix. Make the rename in one commit per API surface (don't bundle unrelated renames). Touch every call site, including tests, benchmarks, examples, and docs.

### Category 8: Personal / sensitive / device information

A committed file — source, **test**, config, docstring, comment, or doc — ships to everyone who clones the repo, so none of it should carry the developer's personal or device details:

- **Personal identifiers** — a real name, username, handle, or email, or a value derived from one (a home-directory path, an env or fixture name built from a username).
- **Device / environment specifics** — absolute machine paths, hostnames, IPs, or the developer's specific machine/hardware configuration (CPU model, filesystem, exact specs). Keep performance prose generic — "the local dev machine", "the target node" — never the hardware model. A benchmark that prints host details at *runtime* is fine; baking them into a docstring or comment is not.
- **Secrets** — tokens, API keys, passwords, credentials.

Replace with neutral placeholders (`/path/to/project`, `$HOME`, `example.com`, a generic `user`). Maintainer-approved attribution (a `LICENSE` holder, a chosen `pyproject` author field) is exempt; when unsure whether a value is approved, ask before shipping.

**Hardware *identity* vs measurement *parameter*.** Scrub what identifies the machine or author — CPU model/brand, hostname, username, home-directory paths. Do **not** scrub a quantity a stated claim depends on — a thread/core count, row count, byte size, or iteration count that makes a number or ratio interpretable. A comment like "8 vs 64 threads ≈ 6× slower" becomes meaningless if the counts are replaced with "the full thread count". Test: would deleting the value make a quantitative claim unverifiable? Then it is a parameter — keep it. The hardware that *produced* a number is identity; the number's *parameters* are not.

This is read-and-judgment work, not a fixed pattern — scan paths, fixtures, and prose for anything that identifies the author or their machine, rather than relying on a brittle keyword list (and never hard-code the developer's identifiers into the scan or this skill). It is removal-only and behavior-neutral, so it rides in the same first commit as the other artifact removals (Category 1/2).

## Commit message style for polishing

Follow `code-delivery`'s commit-message conventions — imperative `[scope]` subject, short-or-absent body, a file list when more than two files change. Polishing adds only two things on top:

- **Subject prefix `[polish]`** (or `chore:` under Conventional Commits) — the signal to reviewers: "no behavior change, light review".
- **A body line stating the no-change contract**, one of:
  - "No behavioral change. <N> tests pass."
  - "Behavior unchanged; <briefly describe the structural change and why>."

Example (from a real polishing pass):

````markdown
[polish] Drop module-private access from exporter to store

`exporter.py` reached into `store._HEADER_OFFSET` to compute the
header position. That coupling broke encapsulation: a store-internal
constant became part of the exporter's contract.

Replaced with `store.read_header(fp)` / `store.write_header(fp, ...)`
helpers that own the offset arithmetic inside the store module.
The exporter now never sees the on-disk layout.

No behavioral change. The suite passes; lint/format/type-check clean.

Files:
  * src/<pkg>/store.py       (+ read_header, write_header)
  * src/<pkg>/exporter.py    (use the new helpers)
````

The phrase "no behavioral change" is the reviewer's permission to skim. Earn it: don't sneak a behavior fix into a `[polish]` commit. If you spot a bug while polishing, note it separately.

## Hand-off to language-specific skills

After polishing, the codebase is *structurally* clean but may still want a *style* pass. Hand off:

| Language | Skill | Covers |
|---|---|---|
| Python | `python-code-review` | PEP 8, type hints, NumPy-style docstrings, Pythonic idioms, dead code (ruff rules) |
| C / C++ | `cpp-code-review` | clang-format, modern C++ (smart pointers, `std::optional`, RAII), const correctness, header hygiene |
| (other) | corresponding skill | their style/idiom layer |

Don't try to do both layers in one pass. Polishing reduces noise; the style review then catches actual style issues instead of being drowned in artifacts.

**Related, but not polishing:** if the cleanup is really about making a *suite* of test/benchmark scripts consistent — unifying CLI flag names, sharing fixture builders, a common timing harness, standard output — that's **behavioral** work (renaming a flag breaks the old one) and belongs in the `test-benchmark-harmonization` skill as its own `[chore]` PR, not a `[polish]` commit. Polishing then cleans up only the no-behavior-change residue that migration leaves behind (dead helpers, stale section headers, oracle docstrings labeled "the old route").

## Example: how this skill played out in practice

A 6-commit polishing PR on a Python+C++ package:

| # | Commit | Category | What it did |
|---|---|---|---|
| 1 | `drop_artifacts` | LLM artifacts | Removed iteration-conversation comments; renamed `_v2` helpers to proper names |
| 2 | `drop_pr_refs` | PR refs | Replaced `# see PR #142` comments with in-code explanations |
| 3 | `fix_stale_docs` | Stale docs | Updated docstrings that described old return types after a prior refactor |
| 4 | `dead_code_fstrings` | Dead code | Removed unused branches, f-strings with no interpolation, one orphan helper |
| 5 | `drop_private_access` | Encapsulation | Caller no longer reached into `store._HEADER_OFFSET`; added `store.read_header` |
| 6 | `rename_materialize` | Renames | `to_array` → `array`, `to_dict` → `dict`, `to_records` → `records`, `to_frame` → `frame` |

The suite passed after each commit. Per-commit zips delivered with the PR (see `code-delivery` skill). Each commit body said "no behavioral change" — the reviewer could skim 1-4 in minutes and focus attention on 5-6 where the structure genuinely changed.

## Quick checklist before sending a polishing PR

- [ ] Two reading passes done: grep-driven + eyes-driven
- [ ] Docstrings/comments read as professional reference prose — no conversational artifacts, reader asides, editorial flourishes, or edit-history narration (Category 1)
- [ ] No personal/sensitive/device info in any committed file — identifiers, machine/hardware specs, host paths, secrets (Category 8)
- [ ] Findings categorized; one commit per category
- [ ] Commits ordered least-risky → most-risky
- [ ] Full test suite + lint + type-check pass after each commit
- [ ] Each commit body says "no behavioral change" (or explicitly describes the structural change)
- [ ] No bug fixes smuggled into polishing commits
- [ ] Hand-off to the appropriate language-specific skill noted in the PR description, if a style pass should follow
