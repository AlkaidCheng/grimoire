# Chat-surface packaging mechanics

Companion reference to the code-delivery skill (`SKILL.md`), for the **chat surface** only: no direct repository access, so a code change ships as **inline fenced blocks** or as **zipped packages** surfaced through the platform's file-presentation tool. Everything not chat-surface-specific stays in `SKILL.md`: pre-delivery checks, the PR-draft text artifacts ("Mode 3", identical on every surface), the human-facing-artifact rules, and the coding-agent path. Read this file only when packaging for the chat surface.

## Choosing the format: inline vs. zip vs. PR draft

| Situation | Format |
|---|---|
| Single change <= ~40 lines, one file, or a copy-paste helper | **Inline**: fenced block tagged with the file's language (`python`, `cpp`, `bash`, ...) |
| Change spans multiple files, includes binaries, needs a build, or the user said "package this up" | **Zip**: drop into the output directory and surface with the platform's file-presentation tool |
| User said "draft a PR", "open a PR", "prepare commits", or anything naming commits/branches/PRs | **PR draft**: the multi-block text-artifact format in `SKILL.md` (Mode 3), with per-commit zips from this file |

When in doubt between inline and zip: if you'd otherwise paste more than two code blocks for a single change, zip it: long inline diffs are hard to apply by hand.

## Cleaning up before zipping

Strip build artifacts that shouldn't ship:

```bash
rm -f src/<pkg>/*.so          # built extensions
rm -rf bld build dist *.egg-info
rm -rf .pytest_cache .mypy_cache .ruff_cache
rm -f src/cython/*.cpp        # generated, never check in
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

Then `zip -r <name>.zip <folder> -x '*.pyc' -x '*/__pycache__/*'` and confirm with `unzip -l` or `du -h` that the size looks reasonable (a clean Python package is tens-to-low-hundreds of KB, not MB).

## Mode 1: Inline

A fenced code block tagged with the file's actual language so it renders with syntax highlighting:

````
```python
def normalize_records(...):
    ...
```
````

Don't use `markdown` as the tag for actual source code; that's reserved for commit messages and PR descriptions (the Mode 3 text artifacts in `SKILL.md`). Show the change in context if the file is large enough that the user might lose their place. Below the block, one line of verification: "Builds clean on Linux, the tests pass." Don't preface with "Here is the code:" or close with "Hope this helps."

## Mode 2: Zipped package

**Deliver the focused fix zip only. Add a refreshed cumulative zip solely when the user asks for one**: unprompted, it's a second, larger archive to tell apart from the one that matters.

- **Focused fix zip** *(the default deliverable)*: only the files that changed, at paths relative to the repository root (no wrapping repo-name directory), so it drops in with `unzip -o <focused-fix>.zip -d .` from the repo root, followed by `git add .` (see "Per-commit zips" for the layout).
- **Refreshed cumulative zip** *(only on request)*: the whole package with the fix applied, for someone who'd rather diff against their last full snapshot.

Call the platform's file-presentation tool with the focused zip; if a cumulative zip was requested, present the focused zip first so it stays the first thing the user sees.

Follow up with a short body:
- What was wrong (one paragraph, concrete: quote the error or symptom)
- What changed (one paragraph, with the key code excerpt if small)
- Verification (one line)
- A suggested commit message in a ```` ```markdown ```` block, wrapped in outer quad backticks so any inner triple-backticks render

Don't restate file paths the user can see in the zip listing. Don't apologize for the bug.

## Per-commit zips

Each commit gets its own zip. **The zip's internal paths must be relative to the repository root, with no leading repo-name directory.** Files sit at their exact repo paths (`src/<pkg>/reader.py`, `tests/test_foo.py`) so the user unpacks each commit in sequence from the repo root:

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

**Do not** wrap the files in a top-level package/repo directory: a zip containing `<repo-name>/src/<pkg>/reader.py` would extract to `<repo>/<repo-name>/src/...`, the wrong place. Build from a staging dir whose top level *is* the repo root:

```bash
mkdir -p stage/src/<pkg> stage/tests
cp <working>/src/<pkg>/reader.py stage/src/<pkg>/reader.py
cp <working>/tests/test_foo.py       stage/tests/test_foo.py
( cd stage && zip -r /mnt/user-data/outputs/pr_<branch>/commit_1_<slug>.zip src tests )
```

Verify with `unzip -l` that the first entries are `src/...` / `tests/...`, never `<repo-name>/...`.

## Deletions in zips

A zip cannot express a deletion: extracting only adds or overwrites files. (The universal rule, which is to list every removed path and mark it `(removed)` in the commit's file list, lives in `SKILL.md`.) If a commit removes files, call them out explicitly in chat with the exact removal commands, run from the repo root, alongside that commit's unzip step:

```bash
cd <repo>
unzip -o commit_3_<slug>.zip -d .          # adds/updates files
git rm src/<pkg>/old_module.py src/cpp/dead_kernel.cpp   # removals the zip can't carry
git add .
git commit -F <commit-3-message-saved-to-file>
```

Stage the per-commit zips somewhere predictable, e.g. `/mnt/user-data/outputs/pr_<branch>/commit_<N>_<slug>.zip`, and pass all of them to the platform's file-presentation tool in one call after all the code blocks.

## Worked examples

**Inline fix example.** The MSVC `__restrict__` to `__restrict` swap was small (one header + six call sites in one .cpp) but spanned two files, so it shipped as a focused fix zip, not inline: a zip applies more reliably than copying two code blocks into the right files. Rule of thumb: **if applying the change touches more than one file, zip it.**

**Iterative fix example (Mode 2).** The four-file Windows lock-offset fix: make the change; run build + tests + lint/type checks in one combined call; clean artifacts; build the focused fix zip (just the four files; no cumulative zip, none requested); present it with the platform's file-presentation tool; then a body with the diagnosis table, root cause with doc citation, the fixes, verification numbers, and a quad-backtick commit message at the end.

**What NOT to do:**
- Don't dump a 200-line file inline when a focused zip would do it.
- Don't ship the refreshed cumulative zip unprompted: the focused fix zip is the whole deliverable unless the cumulative one was asked for.

## Checklist: zip mechanics

- [ ] Build artifacts cleaned out of the zip
- [ ] Focused fix zip present (and listed first if a cumulative zip was also requested)
- [ ] Refreshed cumulative zip included only if the user asked for one
- [ ] Per-commit zips alongside each commit message
- [ ] **Every zip's internal paths are repo-root-relative** (top-level entries are `src/...`, `tests/...`, not `<repo-name>/...`); verified with `unzip -l`, and unpacks via `unzip -o <file> -d .` from the repo root then `git add .`
- [ ] **Deletions are spelled out in the chat with explicit `git rm <paths>` commands** from the repo root (zips can't carry deletions)
