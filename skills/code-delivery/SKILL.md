---
name: code-delivery
description: Use whenever the user asks for any code change — bug fix, feature, refactor, follow-up fix, or PR draft — even a terse "fix this" or "implement X". Governs how the change is delivered (direct edits plus git operations in Claude Code; inline or zipped packages on Claude.ai) and how the PR text artifacts — branch name, commit messages, PR title, PR description — are written. For design or structural decisions use software-design; for pre-merge structural cleanup use code-polishing; for language-specific style use python-code-review or cpp-code-review.
---

# Code Delivery

How to package and present code changes so the user can apply them quickly.

This skill covers two delivery surfaces:

- **Claude.ai** — no direct repository access. Code is delivered as inline fenced blocks or as zipped packages surfaced through `present_files`. Three modes: inline, zipped package, PR draft. The packaging mechanics for this surface live in [`claude-ai-packaging.md`](claude-ai-packaging.md); read that file when the deliverable is being packaged for Claude.ai.
- **Claude Code** — direct repository access. Code is delivered by editing files in the repo. Git operations (creating a branch, committing, pushing) are not run unprompted; offer them and wait for the user's go-ahead.

**What is universal across both surfaces:** the *text artifacts* of a PR draft — branch name, commit messages, PR title, PR description — and the writing style for each. These are read by human reviewers regardless of how the change was produced; the conventions below apply identically.

This file covers the **Claude Code** surface and everything universal — pre-delivery checks, the PR-draft text artifacts (Mode 3), the human-facing-artifact rules, PR title / commit / description style. Sections marked **(Claude Code only)** describe direct edits and git invocation; everything unmarked applies to both surfaces. The **(Claude.ai only)** packaging mechanics — inline/zip modes, per-commit zips, cleanup — are in [`claude-ai-packaging.md`](claude-ai-packaging.md).

**Relationship to `code-polishing`.** Delivery and polishing are stages of one pipeline, not competitors. `code-polishing` transforms the *content* of a change — stripping iteration artifacts, dead code, stale docs, encapsulation and naming drift; this skill packages and ships whatever change exists, running the gates and authoring the branch, commit, and PR text. A bare "fix this" or "draft a PR" is delivery; "clean this up" is polishing. Delivery runs **last** in the pipeline — it packages whatever the upstream passes produced: content cleanup (`code-polishing`), then any language review (`python-code-review` / `cpp-code-review`, the language standard). This skill owns the commit-message and PR-text conventions; `code-polishing` follows them, adding only its `[polish]`-specific note.

**Relationship to `annotated-diff-html`.** When the user asks to *see* the change as a rich, visual HTML diff — a themed, annotated review page to eyeball before pushing, or to share for review — produce it with the `annotated-diff-html` skill (a git-driven renderer: line-numbered table diff, inline per-block reviewer notes pinned to specific lines, a change summary, a per-file copy button; output written to `.claude/diffs/`). It is an *optional review artifact* generated alongside the PR text this skill authors, not a replacement for it — this skill still owns the branch, commit message(s), PR title, and description. Trigger cue: "rich HTML diff", "visual / pretty diff", "annotated diff", "a review page for this PR".

## Surface: Claude Code — direct edits and git operations

**(Claude Code only.)** The deliverable is the edited working tree itself, not a code block or a zip. Apply the change with the editing tools, then write the PR draft text artifacts in chat.

**Edits.** Make the changes directly on the files in the repo. Do not paste the full edited file back into chat as a code block — the user already has the file on disk. Short excerpts in chat are fine when they clarify a specific point; the full change lives in the diff.

**Commands need a one-line summary.** Whenever you show the user a shell command to run or confirm, precede it with a one-line (preferably) executive summary of what it does, so they can judge it without parsing the command itself — e.g. "Push the branch and open the PR:" above a `git push … && gh pr create …` block. This applies to every command you hand back: git, build, install, or one-off.

**Git operations require authorization.** Do not run `git checkout -b`, `git add`, `git commit`, `git push`, or `git rm` unprompted. After the edits are in place and the pre-delivery checks have passed, offer to run the git steps and wait for an explicit yes. A typical offer looks like:

> Edits are in place and tests pass. I can create the branch `fix/windows-file-locking`, stage the four changed files, and commit with the message below — say the word and I'll run it, then hand you the `git push` command for your side. Otherwise, you have everything you need to do it by hand.

If the user says yes, run the operations one batch at a time and surface what was actually run (branch created, files staged, commit SHA). If the change spans multiple commits, pause between commits so the user can review each one before the next is made.

**Prefer having the agent commit.** Once authorized, the default path is the agent creating the branch and running the commit itself — it authored the commit message, so committing directly (`git commit -F -` with the message piped in) applies that exact text with no copy-paste drift or truncation. Reserve hand-off-only delivery for when the user declines auto-commit or the environment blocks it. Authorization is still required before the first git write; "prefer" governs *who runs the commit once the user has said yes*, not whether to ask.

**Always surface the commands the user runs on their own side.** After the agent commits, some steps typically remain the user's to run — most commonly the push (`git push -u origin <branch>`), plus opening the PR if that's their workflow. Show each such command in its own copy-pasteable block with the one-line summary above it, even when the agent did everything up to that point. Never leave the user to reconstruct the branch name or remote — hand them the literal command. Push is a network operation that reveals the change externally, so unless durably authorized, prefer handing the push command over running it.

**Always surface a created or updated PR.** Retrieve the canonical URL from the hosting service, verify that it names the intended base and head branches, and include it as a clickable link in the final handoff. Never make the user search for a PR the agent created or changed.

**If auto-commit is declined, write out the full sequence.** When the user wants to run the git steps themselves, deliver the complete ordered command set as copy-pasteable blocks — branch, stage, commit (with the message via `git commit -F -` or an equivalent heredoc so the authored message survives verbatim), any `git rm` for deletions, and the push — each with its one-line summary. The goal is that the user can paste top-to-bottom without editing anything but a path they intend to change.

**Deletions are real.** Removed files come out with `git rm <path>` (after authorization), not by writing instructions for the user to run later. Spell out which paths were removed in the PR draft's file list.

**The text artifacts come from the universal section below** — branch name, commit message(s), PR title, PR description. Author them in chat using the same `markdown`-tagged blocks documented in "Mode 3: PR draft (text artifacts)", so the user can paste them into `git commit -F -` or the PR template (or hand them back as the messages to use when authorizing the git run).

## Pre-delivery checks (do these before producing any deliverable)

Applies to both surfaces. Run whatever gates the project has, even if the user didn't ask. The patterns we've seen so far:

- Python: `pytest -q`, `ruff check`, `black --check`, `mypy --strict` on source dirs
- C/C++ extensions: rebuild from clean, look for warnings under `-Wall -Wextra`
- If there's a `Makefile` / `CMakeLists.txt` / `pyproject.toml` script that bundles checks, prefer that

Mention the results in one or two lines after the deliverable. Don't pad the response with a wall of test output — `the suite passes in 1.5s; ruff/black/mypy clean` is enough. If anything failed, show the failure verbatim. These handoff results do not automatically belong in the PR description; include validation there only when it gives the reviewer material evidence that status checks do not already convey.

When a change *provably cannot* affect a gate — a docs-only edit, or a new script/benchmark file the test suite never imports — say so with the reason ("docs-only; the suite doesn't import this — unaffected") instead of running the full suite for show. Only claim "unaffected" when you can point at *why* (no imported source changed); otherwise run it.

## Mode 3: PR draft (text artifacts)

The user wants something they can paste into git and a PR template. Produce **each text artifact in its own fenced code block** so the user can copy each one independently. Order matters — give them the pieces in the order they'd use them.

**This section applies to both surfaces.** The branch name, commit message(s), PR title, and PR description are authored identically on Claude.ai and in Claude Code — they are read by a human reviewer who doesn't know how the change was produced. What *differs* by surface is only how the code itself is delivered alongside the text:

- **Claude.ai:** per-commit zips delivered via `present_files`, ordered next to each commit message. See [`claude-ai-packaging.md`](claude-ai-packaging.md) ("Per-commit zips").
- **Claude Code:** the edits are already in the working tree; offer to run the matching git operations (`git checkout -b`, `git add`, `git commit -F`, `git rm`, `git push`) and wait for authorization, as covered in "Surface: Claude Code — direct edits and git operations". The PR title and description are still authored in chat as `markdown`-tagged blocks so the user can paste them into the PR template.

### One PR at a time

When the work decomposes into multiple PRs (stacked or independent), deliver ONLY the first PR, then stop and wait. The user reviews each PR on their side — validating on the deployment machine, editing wording, or redirecting scope — and later PRs must build on the state the user actually accepted, not on an assumed local stack. Concretely:

- Deliver PR 1 complete (branch, commit message(s), title, description, and either the per-commit zips on Claude.ai or the edited working tree plus the git-operation offer in Claude Code), name the planned follow-up PRs in a line or two each, and end the turn.
- Do not pre-generate later PRs' patches, zips, edits, branch names, or text — they go stale the moment the user amends PR 1.
- When the user responds (acceptance, edits, node-validated numbers, or a change of direction), fold that in first; only then prepare the next PR, stacked on the accepted state.
- Doing the *analysis* for later PRs up front is fine and useful (so the plan is visible); the deliverables come one per turn.

**Stacked PRs and rebasing onto an advancing base.** When a PR builds on an unmerged one, open it with `--base <that-branch>` (not the main branch) so its diff shows only the delta, and note that it retargets to the main branch when the base merges. When the base *does* merge, rebase with `git rebase --onto <main> <old-base> <branch>` — this replays only your commits whether the base landed as a merge commit or a squash, where a plain `git rebase <main>` can replay the base's already-merged commits and conflict. Generate the review diff with the three-dot range (`base...head`) so it matches the host's PR view even after the main branch advances past the fork point.

**Language tag per element:**

| Element | Tag | Why |
|---|---|---|
| Branch name | no tag (plain) | Just a string |
| PR title | no tag (plain) | Just a string |
| Commit message | `markdown` | Contains formatted text — subject line, body paragraphs, file list |
| PR description | `markdown` | Contains headers, tables, lists, code excerpts |

Use `markdown` (not the file's source language) for things that *describe* code rather than *being* code. The block contents may include inner fenced examples — wrap them with quad backticks (`````` ```` ``````) on the outside so the inner triple-backticks render.

The structure of a PR draft response is:

1. One-paragraph framing of what the PR does (prose, not in a code block)
2. **Branch name** — single-line, untagged:
   ````
   ```
   feat/windows-support
   ```
   ````
3. **For each commit in order**:
   - Heading: `### Commit N: short description`
   - The commit message in a `markdown`-tagged block — **keep it concise** (see "Commit message style"); the heavy detail belongs in the PR description, not here:
     `````
     ````markdown
     [scope] subject line in imperative, under ~70 chars

     One or two short lines naming what changed and why, only if the
     subject can't carry it alone. Most commits need no body.

     Files:
       * path/to/file.py    (one-line note)
       * path/to/other.cpp  (one-line note)
     ````
     `````
   - **(Claude.ai only.)** The corresponding **per-commit zip** delivered via `present_files`, named `commit_<N>_<slug>.zip`, containing only the files touched by that commit (zip mechanics in [`claude-ai-packaging.md`](claude-ai-packaging.md))
   - **(Claude Code only.)** The edits for this commit are already in the working tree from the earlier editing step. After all commit messages, PR title, and PR description are written in chat, offer to run `git checkout -b <branch>` followed by per-commit `git add <paths> && git commit -F -` (and `git rm` for any deletions, see "Deletions"), and wait for authorization before running.
4. **PR title** — single-line, untagged fence. The title text **must** start with a type tag (see "PR title style" below):
   ````
   ```
   [feat] Windows support: locking, MSVC compatibility, CI matrix
   ```
   ````
5. **PR description** — `markdown`-tagged block containing the description (which itself may contain inner code excerpts tagged with their real languages — `python`, `cpp`, etc.)
6. Final summary table (outside the code blocks) listing the deliverables. On Claude.ai: branch, each commit zip, and anything else. In Claude Code: the branch name, the changed-file list per commit, and any deletions — pointing the reader at the working tree rather than at attached files.

### Deletions

**Universal principle.** List every removed path. Never leave a deletion implicit — the commit must actually drop the file. The commit message's file list should mark them too (e.g. `* src/<pkg>/old_module.py   (removed)`).

**(Claude Code only.)** Remove the files with `git rm <path>` as part of the authorized git run for the commit that drops them. Don't leave an instruction for the user to run later — the surface supports the real operation, so do it (after authorization).

**(Claude.ai only.)** A zip cannot carry a deletion; it must be spelled out in the chat with explicit `git rm` commands — see [`claude-ai-packaging.md`](claude-ai-packaging.md) ("Deletions in zips").

## Audience: write every artifact for a human reviewer

Branch names, commit messages, PR titles and descriptions — and committed docstrings and comments — are read by teammates who have **no knowledge of how the change was produced**. Three hard rules are checked on every delivery:

- **No process leak** — no internal tooling/skill names, decomposition labels ("Band A", "Phase 2"), assistant references ("as an AI", "Claude"), conversation references ("as discussed", "per your request"), or generation meta-commentary ("auto-generated", "if wanted"). The substance is often legitimate — rephrase it in plain engineering terms. This extends to committed docstrings and comments (professional third-person prose, never a conversation or an edit history). The test: would a new teammate reading only the repo understand every word?
- **No personal/sensitive/device info** — no real names, usernames, emails, host/device paths, hostnames, IPs, machine/hardware specs, or secrets in any committed file (**tests and configs included**); use neutral placeholders. Scrub hardware *identity*, but keep a measurement *parameter* a claim depends on; maintainer-approved attribution (a `LICENSE` holder) is exempt.
- **Public and review-relevant** — a PR body is not a private maintainer handoff. Include only information that helps a reviewer understand the motivation or behavior, assess a material part of the diff, or make a review decision. Omit confidential operations, private repository/history details, conversation-only instructions, and setup reminders intended only for the maintainer. Never include credentials or secrets in a PR or delivery artifact. Put non-secret maintainer-only follow-up in the maintainer handoff outside the PR.

The full rule — the complete forbidden-reference list, the rephrase example, and the identity-vs-parameter test — is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md), checked the same way on every delivery.

## PR title style

**The PR title must begin with a bracketed type tag** identifying the kind of change. This is a strict requirement for every PR draft — no exceptions. The tag describes the *type* of work; it is distinct from the `[scope]` component prefix on a commit subject (e.g. a commit `[reader] ...` can belong to a PR titled `[perf] ...`).

| Tag | Use for |
|---|---|
| `[fix]` | Bug fixes — wrong output, crashes, regressions, incorrect behavior |
| `[feat]` | New features or capabilities |
| `[perf]` | Performance optimization (no behavior change) |
| `[doc]` | Documentation only |
| `[chore]` | Build, CI, tooling, dependency bumps, refactors with no behavior change |

Pick the tag for the PR's primary intent. A performance fix that also corrects wrong results is `[fix]` (correctness dominates); a pure speedup that keeps results identical is `[perf]`. After the tag, a single imperative phrase: `[perf] Route moderate-K multi-column reads through the column pool`. Keep it under ~70 characters including the tag.

## Commit message style

**Every commit must ship with its own commit message, in its own `markdown` block. This is a strict requirement for every PR draft and every change delivered as commits — whether the code arrives as zips, as edits in the working tree, or as a patch.** A PR draft with N commits has N commit-message blocks; a single-commit change has exactly one. Never deliver a branch, PR title, PR description, patch, zip, or set of edits without the matching commit message(s) — the commit message is the primary artifact, not an optional extra. If a delivery would otherwise end with the commit message missing, it is incomplete; stop and add it before sending. One commit = one message; never fold two commits' text into one block, and never let the PR description stand in for a commit message (they serve different readers: `git log` vs the review page).

**Commit messages are scan targets, not essays.** A reviewer skimming `git log` should grasp each commit's purpose in one glance. So the subject line carries the message, and the body is short or absent. The deep material — root-cause mechanism, verbatim error output, ruled-out alternatives, benchmark tables — goes in the **PR description**, not the commit. Don't make the reader expand a commit to learn what it does.

Rules:
- `[scope]` (or `scope:`) prefix, then an imperative subject under ~70 chars that states the purpose plainly. The subject alone should answer "what does this commit do?"
- Body only when the subject genuinely can't stand alone — then **one or two short lines** naming the why or a single non-obvious constraint. Many commits need no body at all.
- A short file list at the bottom when more than two files are touched, each with a terse note.
- Do not paste error messages, stack traces, design essays, or measurements into the commit body. If you're tempted to, that material is PR-description content.

**Example (concise — preferred):**

`````
````markdown
[kernel] Spell __restrict__ via a portable macro for MSVC

MSVC uses __restrict (no trailing underscores); gate the spelling on
_MSC_VER so the Windows build succeeds. No behavior change elsewhere.

Files:
  * include/<pkg>/kernel.hpp     (PKG_RESTRICT macro)
  * src/cpp/kernel.cpp           (6 call sites)
````
`````

The full story — the exact MSVC error (`error C3646: 'base': unknown override specifier`), why the macro mirrors the project's existing portable-builtin pattern, the vectorization-preservation argument — lives in the PR description. The commit just says what it does.

Things to drop:
- "This commit..." preambles
- Marketing language ("greatly improved", "robust")
- Anything the diff or the PR description already says
- **Any AI/assistant co-author trailer** — no `Co-Authored-By: Claude …` (or other model/assistant) line; attribute the commit to the human author only. This is the trailer form of the "no assistant references" rule in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md).

## PR description style

The PR description is a **public review artifact**, not a transcript or a private maintainer handoff. A detail belongs only when it passes all three tests:

1. It helps a reviewer understand motivation or behavior, assess a material change, or make a review decision.
2. It is not already obvious from the diff or the host's status checks.
3. It remains appropriate if the repository and PR are public.

**Write from the product user's point of view, not as a delivery report.** For
a feature or behavior change, lead with what a user can now do and show the
normal command, API call, or observable result when one exists. Explain files,
types, and architecture afterward, and only where they clarify the public
interface, guarantees, migration, or review risk. For maintenance work with no
user-visible workflow, lead with the repository or operator outcome instead of
inventing a demo.

The body must stand on its own without the conversation or an internal project
plan. Remove status-report and decomposition language such as "this slice",
"the next gate", "the accepted plan", or references to a numbered phase that
has no public meaning. Translate legitimate scope into product terms: say what
is available in this PR and what remains unsupported. Before publishing, read
the rendered body as a new user or reviewer; if the opening describes how the
work was organized rather than why the change matters, rewrite it.

Keep the body concise without narrowing it to the headline feature. Account for every material part of the diff — including independent behavior, packaging, documentation, migration, or repository-policy changes — while avoiding a line-by-line restatement. Before finalizing, compare the body's sections with the changed-file list and diff summary; every material change needs a reviewer-facing explanation or an intentional reason to omit it.

Never include credentials or secrets in a PR or delivery artifact. Put non-secret internal operational notes, private repository/history details, release-environment setup, and conversation-only instructions in the maintainer handoff outside the PR.

**Follow a modern GitHub PR template: `##` section headers, filled only where they apply.** A reviewer should be able to jump to the relevant material without reading the whole description. Use these sections as candidates, dropping any section that has nothing substantive to say:

- `## Summary` — 1–3 sentences: what this PR does and the headline result. The first thing a reviewer reads.
- `## Motivation` — why this change exists: the bug, the failing CI, the regression, the feature need. State the symptom concretely (quote the error or the measured regression).
- `## Changes` — the high-level *what*, ideally as a short list or sub-headed blocks when there are independent pieces. Include the key code excerpt(s) when small. Don't restate the diff line by line.
- `## Root cause` *(for fixes)* — the actual mechanism, not "there was a bug". Cite a doc or spec when the behavior is surprising. This is the section the commit message deliberately omits.
- `## Testing` — include only material evidence: regression coverage for the reported failure, non-obvious platform or compatibility validation, meaningful benchmark results, or an important validation gap. Do not list routine unit tests, linting, formatting, type checking, packaging, or CI/CD success merely to say they passed; status checks already carry that information.
- `## Demo / Example` — when behavior is observable: a before/after snippet, a benchmark table, a screenshot, a repro command. Skip when there's nothing to show.
- `## Related Issues` — `Fixes #123`, `Refs #456`, links to prior PRs in a stack, or the follow-up PRs this one precedes. Skip if none.

Add or rename sections to match the project's own template if one exists in `.github/` (check for `PULL_REQUEST_TEMPLATE.md` and prefer its headers). Sections such as `## Breaking changes`, `## Migration`, `## Performance`, or `## Risk / rollback` belong only when they convey a concrete reviewer-facing decision. Never add `## Release setup` solely to carry maintainer instructions; keep those in the private handoff.

**Use tables for multi-failure or multi-symptom cases.** When one PR clears several failures or addresses multiple bugs, tabulate which fix maps to which symptom:

| Failure | Why it now passes |
|---|---|
| `test_locked_resource_blocks_writer` | Lock now at offset 2^62; reader doesn't see it. |
| 8× `os.replace` PermissionError | `lock_fd` closed before rename. |

**Be specific, not generic.** Compare:

> Bad: "Fixed Windows compatibility issues with file locking."
>
> Good: "msvcrt.locking on byte 0 blocks reads of byte 0 from any other handle, including a fresh open in the same process — that broke every reader path while a writer was active. Moved the lock to offset 1<<62; nothing reads at that offset, so the contract holds."

**Don't restate the diff.** The reviewer will read it. The description explains what the diff *doesn't* show — the mechanism, the tradeoffs, the ruled-out alternatives, the failure mode that motivated the change.

## Worked examples

Claude.ai worked examples (an inline fix and an iterative zipped fix) are in [`claude-ai-packaging.md`](claude-ai-packaging.md).

### Equivalent fix in Claude Code
Same four-file Windows lock-offset fix, on the Claude Code surface:
1. Edited the four files directly in the repo with the editing tools
2. Ran the project's check suite (`pytest -q`, `ruff check`, `black --check`, `mypy --strict`) from the repo
3. Wrote the PR draft text in chat: branch name in a plain fence, the commit message in a `markdown` block, PR title in a plain fence with `[fix]` tag, PR description in a `markdown` block with `## Summary` / `## Motivation` / `## Root cause` / `## Testing`
4. Offered: "Edits are in place and tests pass. I can create `fix/windows-file-locking`, stage the four files, and commit with the message above — say the word and I'll hand you the push command." Did not run any git commands until the user confirmed.
5. After confirmation, ran `git checkout -b`, `git add <paths>`, and `git commit -F -` with the message piped in, surfacing the resulting branch and SHA — then handed back the push command in its own block with a one-line summary: `git push -u origin fix/windows-file-locking`.

The chat output is mostly the *text artifacts* — no large code blocks, since the edits live in the working tree.

### What NOT to do
- **(Claude Code)** Don't paste the full edited file back into chat as a code block — the edits are already in the working tree; the user doesn't need a copy.
- **(Claude Code)** Don't run `git checkout -b`, `git add`, `git commit`, or `git push` before the user has authorized it.
- Don't put a commit message or PR description in a regular triple-backtick block without a language tag — use ```` ```markdown ```` so it renders as formatted text, and wrap the outer fence in quad backticks if the body contains its own triple-backtick code excerpts.
- Don't append a closing summary that just restates the body. The deliverables, the explanation, and the suggested commit message are the response — stop there.

## Quick checklist before sending

**Universal — applies on both surfaces:**

- [ ] **No artifact reveals the toolchain** — branch name, PR title, commit messages, and PR description contain no skill/tool names, assistant references (including any `Co-Authored-By: Claude …` commit trailer), conversation references ("as discussed", "you asked"), or generation meta-commentary ("if wanted", "auto-generated"); every term resolves for a teammate who only sees the repo
- [ ] **Committed docstrings and comments read as professional reference prose** — they describe what the code is and does, with no conversational artifacts (first-person "we", editorial flourishes, reader asides), no edit-history narration in place of behavior, and none of the toolchain/assistant/conversation references above
- [ ] **No personal/sensitive/device info** — no real names, usernames, emails, home/device paths, hostnames, IPs, machine/hardware specs, or secrets in any committed file (including tests, configs, and docstrings/comments), commit message, branch, or PR text; neutral placeholders used (maintainer-approved attribution excepted)
- [ ] **PR body is public-safe and review-relevant** — every detail helps explain motivation or behavior, assess a material change, or make a review decision; non-secret internal operations, private history, and maintainer-only setup remain in the maintainer handoff outside the PR; credentials and secrets appear in neither artifact
- [ ] **Behavior-changing PR body starts with the user outcome** — normal usage or observable behavior precedes implementation detail; the description stands alone without conversation context, delivery-status narration, or internal plan labels
- [ ] **PR body covers the full material diff** — every independent behavior, packaging, documentation, migration, or repository-policy change is represented without restating files line by line
- [ ] All pre-delivery checks ran and passed (or failures are surfaced)
- [ ] Body explains *what was wrong* and *why this change*, not just *what changed* — in the **PR description**, not the commit
- [ ] **Commit messages are concise** — purpose readable at a glance from the subject; no error dumps, essays, or measurements in the commit body (that goes in the PR description)
- [ ] **PR description uses only applicable GitHub template headers** — matches `.github/PULL_REQUEST_TEMPLATE.md` when present; empty, routine-validation, maintainer-setup, and hypothetical risk sections are omitted rather than padded
- [ ] Suggested commit message included for non-trivial fixes
- [ ] **Every commit has its own commit message block** — N commits ⇒ N `markdown` blocks (one each); a single-commit change still has exactly one. The delivery is incomplete without them — never ship branch/title/description/edits/zip while the commit message(s) are missing
- [ ] For PR drafts: branch name, each commit message, PR title, PR description each in their own code block
- [ ] **PR title starts with a type tag** — `[fix]` / `[feat]` / `[perf]` / `[doc]` / `[chore]`
- [ ] **Any deletions are spelled out** and marked `(removed)` in the commit's file list
- [ ] Only ONE PR delivered this turn; planned follow-up PRs are named, not produced

**Claude.ai only — zip mechanics:** see the zip-mechanics checklist in [`claude-ai-packaging.md`](claude-ai-packaging.md).

**Claude Code only — direct edits and git operations:**

- [ ] Edits applied directly to the repo with the editing tools; no full file dumped back into chat as a code block
- [ ] No `git checkout -b`, `git add`, `git commit`, `git rm`, or `git push` run before the user authorizes it — the offer is made and the response is awaited
- [ ] After authorization (if granted), the agent ran the commit itself (message piped via `git commit -F -`, not left for the user to paste), with the branch name and resulting commit SHA(s) surfaced back
- [ ] The commands the user runs on their own side — the push (`git push -u origin <branch>`) and any PR-open step — are handed back as copy-pasteable blocks, each with a one-line summary; the literal branch name is filled in, not left as a placeholder
- [ ] After creating or updating a PR, its canonical URL was verified and included as a clickable link in the final handoff
- [ ] If the user declined auto-commit, the full ordered command sequence (branch → stage → commit → any `git rm` → push) was written out copy-pasteable
- [ ] Multi-commit runs paused between commits so the user can review each before the next
