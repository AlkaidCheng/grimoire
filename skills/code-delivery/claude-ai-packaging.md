# Claude.ai packaging mechanics

Companion reference to the code-delivery skill (`SKILL.md`), for the **Claude.ai** surface only.

On Claude.ai there is no direct repository access, so a code change ships as **inline fenced blocks** or as **zipped packages** surfaced through `present_files`. This file holds the packaging mechanics for that surface: choosing inline vs. zip, cleaning a package before zipping, the inline and zip modes, per-commit zips, expressing deletions a zip cannot carry, worked examples, and the zip-mechanics checklist.

Everything that is **not** Claude.ai-specific stays in `SKILL.md`: the pre-delivery checks, the PR-draft *text artifacts* (branch name, commit message(s), PR title, PR description — identical on every surface, "Mode 3"), the human-facing-artifact rules, and the entire Claude Code (direct-edit) path. Read this file only when the deliverable is being packaged for Claude.ai.

## Choosing the format: inline vs. zip vs. PR draft

Choose how to package the deliverable:

| Situation | Format |
|---|---|
| Single change ≤ ~40 lines, one file, or a copy-paste helper | **Inline** — fenced code block tagged with the file's language (`python`, `cpp`, `bash`, …) |
| Change spans multiple files, includes binaries, needs a build, or the user said "package this up" | **Zip** — drop into the output directory and surface with `present_files` |
| User said "draft a PR", "open a PR", "prepare commits", or anything that names commits/branches/PRs | **PR draft** — the multi-block text-artifact format in `SKILL.md` (Mode 3), with per-commit zips from this file |

When in doubt between inline and zip: if you'd otherwise be pasting more than two code blocks for a single change, zip it. Long inline diffs are hard to apply by hand.

## Cleaning up before zipping

Strip build artifacts that shouldn't ship:

```bash
rm -f src/<pkg>/*.so          # built extensions
rm -rf bld build dist *.egg-info
rm -rf .pytest_cache .mypy_cache .ruff_cache
rm -f src/cython/*.cpp        # generated, never check in
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

Then `zip -r <name>.zip <folder> -x '*.pyc' -x '*/__pycache__/*'` and confirm with `unzip -l` or `du -h` that the size looks reasonable (a clean Python package should be tens-to-low-hundreds of KB, not MB).

## Mode 1: Inline

A fenced code block, tagged with the file's actual language so it renders with syntax highlighting and the user knows what they're looking at:

````
```python
def normalize_records(...):
    ...
```
````

````
```cpp
template <typename T>
void merge_sorted(...) { ... }
```
````

````
```bash
PYTHONPATH=src python3 -m pytest tests/ -q
```
````

Don't use `markdown` as the tag for actual source code — that's reserved for things like commit messages and PR descriptions (the PR-draft text artifacts in `SKILL.md`, Mode 3). Show the change in context if the file is large enough that the user might lose their place. Below the block, one line of verification: "Builds clean on Linux, the tests pass."

Don't preface with "Here is the code:" or close with "Hope this helps." The block speaks for itself.

## Mode 2: Zipped package

**Deliver the focused fix zip only. Add a refreshed cumulative zip solely when the user asks for one** — shipping it unprompted just adds a second, larger archive the user has to tell apart from the one that matters, which is noise rather than help.

- **Focused fix zip** *(the default deliverable)* — only the files that changed, at paths relative to the repository root (no wrapping repo-name directory), so it drops in with `unzip -o <focused-fix>.zip -d .` run from the repo root, followed by `git add .` (see "Per-commit zips" for the exact layout and why the wrapping directory is wrong).
- **Refreshed cumulative zip** *(only on request)* — the whole package with the fix applied, for someone who'd rather diff against their last full snapshot than apply the focused fix on top.

Call `present_files` with the focused zip. If a cumulative zip was requested, present the focused zip first so it stays the first thing the user sees.

Follow up with a short body that explains:
- What was wrong (one paragraph, concrete — quote the error or symptom)
- What changed (one paragraph, with the key code excerpt if it's small)
- Verification (one line)
- A suggested commit message in a ```` ```markdown ```` block, wrapped in outer quad backticks so the commit body's own triple-backticks (if any) render correctly

Don't restate file paths the user can see in the zip listing. Don't apologize for the bug.

## Per-commit zips

Each commit gets its own zip. **The zip's internal paths must be relative to the repository root — no leading repo-name directory.** The files sit at the exact paths they occupy in the repo (`src/<pkg>/reader.py`, `tests/test_foo.py`), so the user can unpack them from the repo root and have them land in place:

```bash
cd <repo>                       # repository root
git checkout -b <branch-name>
unzip -o commit_1_<slug>.zip -d .   # -o overwrites without prompting; -d . = repo root
git add .                           # *.zip is gitignored, so the archive itself is never staged
git commit -F <commit-1-message-saved-to-file>
unzip -o commit_2_<slug>.zip -d .
git add .
git commit -F <commit-2-message-saved-to-file>
# ...
```

This is why each commit's files must be self-contained and repo-root-relative: the user extracts them in sequence onto a clean tree with `unzip -o ... -d .` and stages with `git add .`. **Do not** wrap the files in a top-level package/repo directory inside the zip — a zip containing `<repo-name>/src/<pkg>/reader.py` would extract to `<repo>/<repo-name>/src/...`, the wrong place. Build the zip from a staging dir whose top level *is* the repo root:

```bash
mkdir -p stage/src/<pkg> stage/tests
cp <working>/src/<pkg>/reader.py stage/src/<pkg>/reader.py
cp <working>/tests/test_foo.py       stage/tests/test_foo.py
( cd stage && zip -r /mnt/user-data/outputs/pr_<branch>/commit_1_<slug>.zip src tests )
```

Verify with `unzip -l` that the first entries are `src/...` / `tests/...`, never `<repo-name>/...`.

## Deletions in zips

A zip cannot express a deletion — extracting it only adds or overwrites files. (The universal rule — list every removed path, and mark it `(removed)` in the commit's file list — lives in `SKILL.md`.) If a commit removes files, you must call them out explicitly in the chat with the exact removal commands, run from the repo root, alongside the unzip step for that commit:

```bash
cd <repo>
unzip -o commit_3_<slug>.zip -d .          # adds/updates files
git rm src/<pkg>/old_module.py src/cpp/dead_kernel.cpp   # removals the zip can't carry
git add .
git commit -F <commit-3-message-saved-to-file>
```

Stage the per-commit zips somewhere predictable, e.g. `/mnt/user-data/outputs/pr_<branch>/commit_<N>_<slug>.zip`, and pass all of them to `present_files` in one call after all the code blocks.

## Worked examples

### Inline fix example
The MSVC `__restrict__` → `__restrict` swap was small (one header + six call sites in one .cpp), but it spanned a header + source file. We zipped it (focused fix zip) rather than inlining because the user was going to apply it across a build boundary and a focused zip is more reliable than copying two code blocks into the right files. Rule of thumb: **if applying the change touches more than one file, zip it.**

### Iterative fix example (Mode 2)
The Windows lock-offset fix touched four files (`locking.py`, `writer.py`, `compactor.py`, `store.py`). Pattern:
1. Made the change
2. Ran Linux build + tests + ruff + black + mypy (one combined `bash_tool` call)
3. Cleaned artifacts
4. Built the focused fix zip `win_lock_fix.zip` (just the four files) — no cumulative zip, since none was requested
5. Called `present_files` with it
6. Wrote a body with: diagnosis table, root cause with doc citation, the two independent fixes, verification numbers, expected-after-merge table, and a quad-backtick commit message at the end

### What NOT to do
- Don't dump a 200-line file inline when a focused zip would do it.
- Don't ship the refreshed cumulative zip unprompted — the focused fix zip is the whole deliverable unless the user asked for the cumulative one.

## Checklist — zip mechanics

- [ ] Build artifacts cleaned out of the zip
- [ ] Focused fix zip present (and listed first if a cumulative zip was also requested)
- [ ] Refreshed cumulative zip included only if the user asked for one
- [ ] Per-commit zips alongside each commit message
- [ ] **Every zip's internal paths are repo-root-relative** (top-level entries are `src/…`, `tests/…`, not `<repo-name>/…`); verified with `unzip -l`, and unpacks via `unzip -o <file> -d .` from the repo root then `git add .`
- [ ] **Deletions are spelled out in the chat with explicit `git rm <paths>` commands** from the repo root (zips can't carry deletions)
