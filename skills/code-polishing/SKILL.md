---
name: code-polishing
description: Use whenever the user asks to review, polish, clean up, or make code PR-ready ("remove cruft", "make this PR-ready", "review pass", "clean up this mess", any pre-merge cleanup), or when a finished change has accumulated iteration artifacts to strip: LLM/conversation comments, past-PR references, dead code, stale docstrings, encapsulation violations, naming drift. Upstream of code-delivery, which packages a change and writes its commit and PR text. Owns language-agnostic structural cleanup; for design decisions (abstraction, coupling, whether to refactor first) use software-design; for style defer to python-code-review (PEP 8, typing, idioms) and cpp-code-review (clang-format, modern C++). When unsure between polishing and style, pick polishing if the ask names cleanup, artifacts, dead code, stale docs, or PR-readiness.
---

# Code Polishing

The "make it look like a human wrote it on the first try" pass: strip the traces iteration leaves (comments referencing past versions, uncalled helpers, stale docstrings, cross-module reaches).

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

**Does NOT cover** (language-specific; hand off):
- Formatting (Black, clang-format, PEP 8): `python-code-review` / `cpp-code-review`
- Type hint completeness, NumPy-style docstrings, modern Python idioms: `python-code-review`
- RAII, `std::optional`, `constexpr`, modern C++ idioms: `cpp-code-review`
- Algorithmic improvements or API redesign

A blended request ("polish and modernize"): polish first, then the language review: style review on a noisy codebase wastes both passes.

**Relationship to `code-delivery`.** Stages of one pipeline: this skill changes the *content* of the code; `code-delivery` packages and ships it (gates, branch, commit and PR text, git). "Clean this up" is polishing; "fix this" / "open a PR" is delivery. Full arc: **polish** (this skill), then **language review** (`python-code-review` / `cpp-code-review`), then **deliver** (`code-delivery`, last). `code-delivery` owns commit/PR conventions; polishing adds only the `[polish]` prefix and the "no behavioral change" line.

## Process

Read-heavy, edit-light: most of the work is finding what to delete or fix.

### 1. Read before editing

Walk the whole package before touching a file; build a per-category list. Two passes:
- **Grep-driven.** Run the detection patterns below; capture every hit with file:line.
- **Eyes-driven.** Read each public-facing file's docstrings against the signatures and comments against the code they sit on; grep can't find a docstring that says "returns a list" when the function returns a dict.

### 2. Categorize

Group findings by the categories above: the category determines the commit; the commit determines review effort and blast radius.

### 3. One commit per category, ordered least-risky to most-risky

Each commit must leave the tree green for the next:

1. **Pure deletions**: LLM artifacts, PR refs, personal/device info (Category 8), dead comments. Removal-only; zero behavior change.
2. **Stale-doc fixes**: no behavior change; reviewer confirms the new wording matches the code.
3. **Dead-code removal**: behavior unchanged *if you're right that it's dead*.
4. **Encapsulation fixes**: may add a small public function; tests pass without changes.
5. **Renames**: touches caller sites; highest blast radius; last.

Don't combine categories. Don't sneak a behavioral fix into a polishing commit: a real bug found while polishing goes in a separate non-polishing commit (and probably a separate PR).

### 4. Verify after every commit

Run the full test suite, lint, and type-check after each commit; state the result in the commit body: `the suite passes; no behavior change.`

Polishing-specific traps:
- **A comment-only change to a compiled language (C/C++/Cython) still needs a rebuild**: exactly when a stray edit slips into code or the file fails to recompile. Confirm the object code is unchanged (a comment edit must not move a single instruction).
- **Deletions and renames perturb formatting**: trailing blank lines, an identifier pushed past the column limit. Run the formatter (black / clang-format) as part of verification, and re-run lint after it: the formatter's fix is part of the commit.
- When the change is documentation-only and touches no source the suite imports, say so plainly ("the test suite is unaffected; N pass") rather than implying the edit was exercised.
- **Lint, types, and tests have blind spots; some refactors need a targeted runtime check.** They miss: forward-reference evaluation in `get_type_hints()`; import-time side effects and circular-import *order*; entry-point / plugin registration; `__all__` / re-export drift after a move; pickling of relocated classes. After a rename, an encapsulation change, or a type-alias move (Categories 5-7), add a check the gates don't give you: import the public surface and call `get_type_hints()` on the touched signatures, exercise the entry points, or run an independent review. Verify claims about *current* behavior against the code or the built artifact, never against config or naming: "this path emits no footer" / "the license file isn't in the package" are confirmed by reading the function or unpacking the artifact.

## Detection patterns

### Category 1: LLM / iteration artifacts

**Standard:** a docstring or comment is professional reference documentation, third-person engineering prose describing what the code *is and does*. Anything that reads as chat (addressing the reader, narrating the authoring, editorializing) is an artifact, regardless of whether it contains a flagged keyword. (Rule 1 of [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md) applied to committed source.)

Tell-tale shapes:
- Addressing a past or imagined interlocutor: "as we discussed", "per your earlier note", "following our conversation", "as mentioned"
- Explaining *why we changed it* rather than *what the code does*: "Used to be X, but now Y because..."
- **Iteration labels on code that still exists**: naming a current function, path, or helper by its relation to an unstated change ("the pre-change route", "the old `_foo` flow", "the replaced path", "the new kernel", "..., verbatim", "which now uses Y"). Especially common in benchmark/regression-check *oracles* that reproduce the un-optimized route. The reader can't resolve the label from the repo, and it is often *factually* wrong: the "old path" is frequently still the current fallback.
- Iteration-suffixed names: `module_new.py`, `parse_v2`, `_old`, `_legacy` when no documented versioning policy applies
- TODOs referencing earlier turns: `# TODO: as you said, switch this to ...`
- Apologetic or stylistic noise: `# Note: this works`, `# Yes, this is intentional`, `# Sorry about the magic number here`
- Editorial / marketing flourishes and reader asides that don't describe the code: "the lever that turns X into Y", "the row that matters", "this is the clever bit", "fall back rather than guess", "you'll notice". State the mechanism plainly instead: "uses copy_file_range, which reflink filesystems complete near-metadata-only", "falls back to the materializing write".
- **Counterfactual design justification**: a docstring or comment arguing what would go wrong without the code ("an empty mapping would construct a client that can never serve a request", "a stale registration would block the name for good", "which is what the registry exists to prevent"). State the contract ("a mapping must hold at least one entry") and stop; the argument belongs in the commit or PR that introduced the rule.
- **Correction-of-the-past constructions**: text defined by negating a removed behavior ("not a separate final tier", "no longer wraps the payload", "instead of always the first column", "X, not Y"). State the current behavior positively ("matches by longest prefix, like any other rule"); the contrast belongs in the change artifacts.
- **"X rather than Y, because..." implementation apologies** on a private helper: "searched rather than derived, because a wildcard cannot be recovered". The first clause without the apology is the whole contract.

**Treat removed code as if it never existed.** Once an API, path, or default is removed, nothing in the *source, docstrings, or tests* may be organized around its absence:

- **History-defensive tests** are artifacts: a test asserting `not hasattr(obj, 'removed_method')`, a `pytest.raises(TypeError)` on a deleted constructor option, an `assert 'old_key' not in CONFIG`, or a parametrization sweeping formerly-reserved names to prove they are "ordinary now". Delete them: a fresh author would never write them, and they pin nothing a user relies on. (A test of a *replacement behavior* is fine; a test of an *absence* is not.)
- Tests named or docstringed by the transition ("TestLegacyOptionRemoved", "moved from config to settings") get present-tense identities describing the current contract.
- The removal narrative lives in exactly three places: the commit message, the changelog entry, and the PR/MR description (the artifacts whose job is describing the delta). Everywhere else, write as if the current design is the only one that ever existed.

Detection additions:
```bash
rg -n "would (construct|break|crash|refuse|silently)|exists to prevent|rather than .*because" -tsrc
rg -n "not a |no longer|instead of (always|the old)|replacing the" -tsrc   # then apply the meaning test
rg -n "hasattr.*not|not hasattr|Removed\b|_is_gone|is_removed" tests/
```

Detection:
```bash
rg -n "as (we|i) (mentioned|discussed|noted)" --type-add 'src:*.{py,cpp,h,hpp,rs,go,js,ts}' -tsrc
rg -n "(your|our|previous|earlier|last) (note|comment|iteration|conversation)" -tsrc
rg -n "used to be" -tsrc
rg -n "\b(v2|_v2|_new|_old|_legacy|_tmp)\b" -tsrc
rg -n "pre-change|the (old|new|replaced) (path|route|flow|kernel|gate|logic)|, verbatim|now uses|which (now|previously)" -tsrc
```

Read each hit; delete, or rewrite to document the code rather than its history. Three rules sharpen the call:

- **The new-teammate test.** Every word must resolve for someone reading only the repo: no commits, no conversation. "Pre-change", "the replaced route", "as discussed" fail; rewrite them.
- **Label vs. narrative.** An iteration *label* ("the old `_foo` route") is an artifact: reword to what the thing *is* ("the NumPy reference route", "the full-scan gate"). A self-contained *narrative* explaining a design or what a check guards ("previously this ran an O(R log K) partition; the walk kernel replaces it, which is what this check verifies") is legitimate. Don't strip motivation; do fix unresolvable labels.
- **Verify before relabeling.** Before "fixing" a comment that calls something old/removed, grep for the named symbol: it may still exist (then "old" is simply *wrong*) or be gone (a ghost reference; see Category 3). Either way the grep tells you the correct rewrite.

False-positive guard: don't strip legitimate technical prose over a temporal keyword. Editorial "we" ("so we don't import pandas at load") is normal voice; "previously", "no longer", "rewritten in place", "previously-acquired", "used to bound" are fine when they state a *fact about current behavior or a contract* ("the counters block is rewritten in place on close"; "release a previously-acquired lock"; "used to bound the copy" = *used in order to* bound) rather than narrate an edit. Trust the meaning, not the keyword.

### Category 2: PR / issue references in source

PR numbers, issue references, and reviewer names belong in commit messages and PR descriptions, not the source tree: "see PR #142" is opaque to a reader in five years.

Detection:
```bash
rg -n "(#|PR |issue |fixes #|closes #)[0-9]+" src/
rg -n "(per |from |see )(PR|@[a-z]+)" src/
```

Each hit: replace with an in-code explanation, or delete if the code is self-explanatory. "See PR #142" becomes "We bound this to 4096 because larger values trigger ENOMEM on macOS" (assuming that's actually why).

### Category 3: Stale docstrings, comments, READMEs

**The highest-yield stale doc is the one a recent change just created.** After any implementation change (yours or a prior PR in the same arc), re-read the comments in and around the diff before scanning the rest of the package, and grep the touched files for the nouns that named the old approach.

Hardest category to grep. Sub-patterns:

- **Parameter names that don't match the signature**: docstring lists `count, value`, function takes `n, val`.
- **Returns/Raises sections that don't match reality**: read the body's `return`/`raise` statements against the docstring.
- **Inline comments that lie**: "iterate from 1 because 0 is reserved" over a loop starting at 0. Trust the code, fix the comment.
- **READMEs that describe the old API**: common after renames; rarely covered by tests.

Detection is mostly manual reading. Grep-level hints:
```bash
# Find docstrings that mention method names that no longer exist
rg -n "old_name_a|old_name_b" src/  # the pre-rename names
# Find sections of README that talk about removed features
git diff <merge-base> -- README.md  # see what was/wasn't updated
```

**Structural reorganization (distinct from stale-content fixing).** A document can be accurate yet disorganized. Reorganizing is reorder + group + add a table of contents, and must be **content-preserving**: diff each section body against the original to prove no silent loss. Two hazards: (a) renaming or re-leveling a heading changes its anchor; compute the new anchor (GitHub rendering: lowercase, drop characters outside `[\w\s-]`, spaces to hyphens, `&` to `--`) and grep the repo for inbound `#anchor` links before renaming; (b) for a long document, a grouped table of contents is navigation, not decoration.

**Changelog entries are one user-facing sentence.** A changelog bullet names the changed surface and its user-visible effect, nothing else. Mechanism enumerations, per-site lists, colon-plus-three-clauses constructions, and em-dash justification chains are PR-description material that leaked; trim them at write time, because they otherwise accumulate until a batch cleanup is needed. If the bullet needs a colon and a list, the list belongs in the PR.

### Category 4: Dead code

Flavors:

- **Unused imports**: ruff/pyflakes (F401) for Python; clang-tidy for C++.
- **Unused locals**: ruff F841 (Python); `-Wunused-variable` (GCC/Clang).
- **Unreachable branches**: read coverage reports (`pytest --cov`, `gcov`) for branches with 0 hits across all tests.
- **Commented-out code**: ripgrep for blocks of `^\s*#` (Python) or `^\s*//` (C++) that look like code rather than prose.
- **Helpers called only by themselves or by other dead helpers**: reverse-call-graph inspection; for a small codebase, grep each helper's name: one hit (the definition) means dead.
- **Helpers orphaned by a migration**: after a consolidation or API move, a helper whose callers all switched is dead even though it looks load-bearing (e.g. a per-script `main()` driver once every script adopts the shared harness). Only a repo-wide caller grep reveals it has none.
- **Stale section headers**: a banner comment like `# ---- Script driver and store context managers ----` left standing after the context managers moved. Update it, or drop it with the code it described.
- **Conditional branches that can't be reached**: e.g. `if version not in {1}: raise ...` followed by a `match version` that handles only version 1.
- **Format-string artifacts**: f-strings with no `{}` interpolation (ruff F541); use a regular string.

Detection:
```bash
ruff check src/ --select F401,F841,F541  # Python dead-code rules
rg -n "^\s*(#|//) .{0,40}[(){};:=]" src/  # heuristic for commented-out code
```

Always confirm "this looks dead" by grepping for callers across the whole repo: tests, benchmarks, examples, **and the defining module's own internal use**. A helper unused by every other file may still be called within its module; a re-exported name with zero external callers may be exercised by a test. Reliable signal: the symbol appears only at its definition (and its `__all__`/export entry). When removing such a name, remove its `__all__`/export entry in the same commit: a dangling export of a deleted name breaks import.

### Category 5: Encapsulation violations

Symptom: module A reaches into module B's `_private` attribute; usually B should have a small public function exposing the value, and A should call it.

Detection:
```bash
# Imports of single-underscore names from other modules
rg -n "from \S+ import _[a-zA-Z]" src/
# Attribute access to single-underscore names on another module
rg -n "\b[a-z_]+\._[A-Z_]+\b" src/  # tweak per language
```

The fix is rarely "make the attribute public"; usually "extract a function that exposes the *behavior* the caller actually needs". Structural, not cosmetic: a dedicated polishing commit.

### Category 6: Naming consistency

Read the public API surface together; pairs and series should follow one pattern:

- Verbs for similar operations: `read_X` vs `load_X` vs `fetch_X`; pick one
- Inverse pairs: `to_X` / `from_X`, `open_X` / `close_X`, `acquire_X` / `release_X`
- Plural vs. singular: `users` is a collection, `user` is one
- Boolean prefixes: `is_X`, `has_X`, `should_X`

No grep for inconsistent verb choice: list the public functions in a flat file, spot the inconsistency, propose a rename.

### Category 7: API renames

Usually the fix for a Category 6 finding. One commit per API surface (don't bundle unrelated renames); touch every call site, including tests, benchmarks, examples, and docs.

### Category 8: Personal / sensitive / device information

A committed file (source, **test**, config, docstring, comment, or doc) ships to everyone who clones the repo, so none of it should carry the developer's personal or device details: real names, usernames, emails, host paths, hostnames, IPs, machine/hardware specs, or secrets. Replace with neutral placeholders. The nuance: scrub hardware *identity* (CPU model, hostname, home-directory paths) but keep a measurement *parameter* a stated claim depends on: a thread/core count that makes "6x slower" interpretable. The full rule, with the identity-vs-parameter test and the maintainer-attribution exception, is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md).

Read-and-judgment work, not a fixed pattern: scan paths, fixtures, and prose for anything identifying the author or their machine. Removal-only and behavior-neutral, so it rides in the same first commit as the other artifact removals (Category 1/2).

### Category 9: Docstring minimalism

Three standards, applied to every docstring (public and private):

1. **Document what a user of the API needs**: what the thing does, its parameters/returns/raises, essential usage constraints. Cut anything only useful to someone editing the implementation.
2. **Implementation details do not surface**, with one exception: a *non-trivial* detail a user must know to use the API correctly stays ("the returned object is a copy", "the values are cast to float and processed in sorted order", "a None key is refused"). Internal mechanics (which helper does the work, merge orders, resolution walk-throughs, why an internal branch exists) go.
3. **Reference prose only** (Category 1 applied to docstrings): no design arguments, no essays narrating intent, no reader-directed asides, no provenance ("owner ruling", review/issue references), third person throughout.

Calibration: a one-sentence docstring is ideal, not underdone; do not pad it. A 30-line docstring on a private helper is almost always an essay wearing a docstring's clothes; compress it to its behavioral facts and keep every fact. Framework/base-class docstrings legitimately carry more contract detail than leaf-class ones when the contract *is* the user-facing API (an override hook's obligations, a resolution grammar users write keys against). Where a project builds API docs from docstrings (Sphinx autodoc and kin), run that build as the formatting gate for this category, and verify the edit was docstring-only with a docstring-stripped AST comparison rather than by eyeballing the diff.

## Commit message style for polishing

Follow `code-delivery`'s conventions: imperative `[scope]` subject, short-or-absent body, file list when more than two files change. Polishing adds two things:

- **Subject prefix `[polish]`** (or `chore:` under Conventional Commits), the reviewer signal: "no behavior change, light review".
- **A body line stating the no-change contract**, one of:
  - "No behavioral change. <N> tests pass."
  - "Behavior unchanged; <briefly describe the structural change and why>."

Example:

````markdown
[polish] Drop module-private access from exporter to store

`exporter.py` reached into `store._HEADER_OFFSET` to compute the
header position, making a store-internal constant part of the
exporter's contract. Replaced with `store.read_header(fp)` /
`store.write_header(fp, ...)` helpers that own the offset arithmetic;
the exporter never sees the on-disk layout.

No behavioral change. The suite passes; lint/format/type-check clean.

Files:
  * src/<pkg>/store.py       (+ read_header, write_header)
  * src/<pkg>/exporter.py    (use the new helpers)
````

"No behavioral change" is the reviewer's permission to skim. Earn it: don't sneak a behavior fix into a `[polish]` commit; note bugs separately.

## Hand-off to language-specific skills

After polishing, the codebase is *structurally* clean but may still want a *style* pass:

| Language | Skill | Covers |
|---|---|---|
| Python | `python-code-review` | PEP 8, type hints, NumPy-style docstrings, Pythonic idioms, dead code (ruff rules) |
| C / C++ | `cpp-code-review` | clang-format, modern C++ (smart pointers, `std::optional`, RAII), const correctness, header hygiene |
| (other) | corresponding skill | their style/idiom layer |

One layer per pass: polishing reduces noise so the style review catches style issues instead of drowning in artifacts.

**Related, but not polishing:** making a *suite* of test/benchmark scripts consistent (unifying CLI flag names, sharing fixture builders, a common timing harness, standard output) is **behavioral** work (renaming a flag breaks the old one) and belongs in the `test-benchmark-harmonization` skill as its own `[chore]` PR, not a `[polish]` commit. Polishing then cleans up only the no-behavior-change residue the migration leaves behind (dead helpers, stale section headers, oracle docstrings labeled "the old route").

## Quick checklist before sending a polishing PR

- [ ] Two reading passes done: grep-driven + eyes-driven
- [ ] Docstrings/comments read as professional reference prose: no conversational artifacts, reader asides, editorial flourishes, or edit-history narration (Category 1)
- [ ] No personal/sensitive/device info in any committed file: identifiers, machine/hardware specs, host paths, secrets (Category 8)
- [ ] Findings categorized; one commit per category
- [ ] Commits ordered least-risky to most-risky
- [ ] Full test suite + lint + type-check pass after each commit
- [ ] Each commit body says "no behavioral change" (or explicitly describes the structural change)
- [ ] No bug fixes smuggled into polishing commits
- [ ] Hand-off to the appropriate language-specific skill noted in the PR description, if a style pass should follow
