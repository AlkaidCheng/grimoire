---
name: code-delivery
description: Use whenever the user asks for any code change (bug fix, feature, refactor, follow-up fix, or PR draft), even a terse "fix this" or "implement X". Governs how the change is delivered (direct edits plus git operations on the coding-agent surface; inline or zipped packages on the chat surface) and how the PR text artifacts (branch name, commit messages, PR title, PR description) are written. For design or structural decisions use software-design; for pre-merge structural cleanup use code-polishing; for language-specific style use python-code-review or cpp-code-review.
---

# Code Delivery

How to package and present code changes so the user can apply them quickly. Two delivery surfaces:

- **The chat surface**: no repository access. Code ships as inline fenced blocks or zipped packages surfaced through the platform's file-presentation tool; three modes: inline, zipped package, PR draft. Packaging mechanics live in [`chat-packaging.md`](chat-packaging.md); read it when the deliverable is being packaged for the chat surface.
- **The coding-agent surface**: direct repository access. Code is delivered by editing files in the repo. Git operations (branch, commit, push) are never run unprompted; offer them and wait for the user's go-ahead.

**Universal across both surfaces:** the PR-draft *text artifacts* (branch name, commit messages, PR title, PR description) and the writing style for each; human reviewers read them regardless of how the change was produced. This file covers the coding-agent surface and everything universal. Sections marked **(coding-agent surface only)** / **(chat surface only)** are surface-specific; everything unmarked applies to both.

**Relationship to `code-polishing`.** Stages of one pipeline: `code-polishing` transforms the *content* of a change (iteration artifacts, dead code, stale docs, encapsulation and naming drift); this skill packages and ships whatever change exists: gates, branch, commit, and PR text. A bare "fix this" or "draft a PR" is delivery; "clean this up" is polishing. Delivery runs **last**: content cleanup (`code-polishing`), then language review (`python-code-review` / `cpp-code-review`), then delivery. This skill owns the commit-message and PR-text conventions; `code-polishing` follows them, adding only its `[polish]`-specific note.

**Relationship to `annotated-diff-html`.** When the user asks to *see* the change as a rich, visual HTML diff ("rich HTML diff", "visual / pretty diff", "annotated diff", "a review page for this PR"), produce it with the `annotated-diff-html` skill. Store its config and output in the active coding agent's repository-local diff directory (e.g. `.codex/diffs/`, `.claude/diffs/`), never in another agent's directory. It is an *optional review artifact* generated alongside the PR text, not a replacement: this skill still owns the branch, commit message(s), PR title, and description.

## Surface: coding agent (direct edits and git operations)

**(Coding-agent surface only.)** The deliverable is the edited working tree itself; the PR-draft text artifacts are written in chat.

- **Edits.** Edit the repo files directly. Do not paste a full edited file back into chat as a code block; the user has it on disk. Short clarifying excerpts are fine.
- **Every command shown to the user gets a one-line summary above it** (git, build, install, or one-off) so they can judge it without parsing the command (e.g. "Push the branch and open the PR:" above the block).
- **Git operations require authorization.** Never run `git checkout -b`, `git add`, `git commit`, `git push`, or `git rm` unprompted. After the edits and pre-delivery checks, offer the git steps and wait for an explicit yes (e.g. "Edits are in place and tests pass. I can create the branch `fix/windows-file-locking`, stage the four changed files, and commit with the message below; say the word, then I'll hand you the `git push` command.").
- **On yes, run one batch at a time** and surface what actually ran (branch created, files staged, commit SHA). Multi-commit changes pause between commits so the user can review each before the next.
- **Prefer having the agent commit.** Once authorized, the default is the agent creating the branch and committing itself: `git commit -F -` with the message piped in applies the authored text verbatim, with no copy-paste drift or truncation. Reserve hand-off-only delivery for when the user declines auto-commit or the environment blocks it. "Prefer" governs who runs the commit once the user has said yes; authorization always comes first.
- **Always surface the commands the user runs on their own side.** The push (`git push -u origin <branch>`) and any PR-open step typically remain the user's; give each in its own copy-pasteable block with its one-line summary, with the literal branch name and remote filled in. Push is a network operation that reveals the change externally; unless durably authorized, prefer handing the push command over running it.
- **Always surface a created or updated PR.** Retrieve the canonical URL from the hosting service, verify it names the intended base and head branches, and include it as a clickable link in the final handoff.
- **If auto-commit is declined, write out the full sequence**: branch, stage, commit (message via `git commit -F -` or a heredoc so it survives verbatim), any `git rm`, push. Each goes in a copy-pasteable block with its summary, pasteable top-to-bottom without editing anything but a path the user intends to change.
- **Deletions are real.** Remove files with `git rm <path>` (after authorization), never as instructions for the user to run later; spell out removed paths in the PR draft's file list.
- **The text artifacts come from "Mode 3" below**, authored in chat as `markdown`-tagged blocks so the user can paste them into `git commit -F -` or the PR template.

## Pre-delivery checks (do these before producing any deliverable)

Both surfaces. Run whatever gates the project has, even if the user didn't ask:

- Python: `pytest -q`, `ruff check`, `black --check`, `mypy --strict` on source dirs
- C/C++ extensions: rebuild from clean, look for warnings under `-Wall -Wextra`
- If a `Makefile` / `CMakeLists.txt` / `pyproject.toml` script bundles checks, prefer that

Report results in one or two lines after the deliverable ("the suite passes in 1.5s; ruff/black/mypy clean"); show any failure verbatim, never a wall of test output. These handoff results do not automatically belong in the PR description; include validation there only when it gives the reviewer material evidence status checks don't already convey.

When a change *provably cannot* affect a gate (docs-only, or a new script/benchmark the suite never imports), say so with the reason ("docs-only; the suite doesn't import this, so unaffected") instead of running for show. Claim "unaffected" only when you can point at *why*; otherwise run it.

## Mode 3: PR draft (text artifacts)

Produce **each text artifact in its own fenced code block**, in the order the user would use them. Applies to both surfaces: branch name, commit message(s), PR title, and PR description are authored identically. Only the code delivery alongside them differs:

- **Chat surface:** per-commit zips via the platform's file-presentation tool, ordered next to each commit message ([`chat-packaging.md`](chat-packaging.md), "Per-commit zips").
- **Coding-agent surface:** the edits are already in the working tree; offer the matching git operations and wait for authorization (see the surface section above).

### One PR at a time

When the work decomposes into multiple PRs (stacked or independent), deliver ONLY the first PR, then stop; later PRs must build on the state the user actually accepted, not an assumed local stack:

- Deliver PR 1 complete (branch, commit message(s), title, description, plus the surface's code delivery), name the planned follow-up PRs in a line or two each, and end the turn.
- Do not pre-generate later PRs' patches, zips, edits, branch names, or text; they go stale the moment the user amends PR 1.
- When the user responds (acceptance, edits, validated numbers, redirection), fold that in first; only then prepare the next PR, stacked on the accepted state.
- Up-front *analysis* of later PRs is fine and useful; the deliverables come one per turn.

**Stacked PRs and rebasing onto an advancing base.** Open a PR that builds on an unmerged one with `--base <that-branch>` (not the main branch) so its diff shows only the delta, and note that it retargets to the main branch when the base merges. When the base merges, rebase with `git rebase --onto <main> <old-base> <branch>`: this replays only your commits whether the base landed as a merge commit or a squash, where a plain `git rebase <main>` can replay already-merged commits and conflict. Generate the review diff with the three-dot range (`base...head`) so it matches the host's PR view even after the main branch advances past the fork point.

**Language tag per element:**

| Element | Tag | Why |
|---|---|---|
| Branch name | no tag (plain) | Just a string |
| PR title | no tag (plain) | Just a string |
| Commit message | `markdown` | Formatted text: subject, body, file list |
| PR description | `markdown` | Headers, tables, lists, code excerpts |

Use `markdown` (not the file's source language) for things that *describe* code rather than *being* code. When a block contains inner fenced examples, wrap it with quad backticks on the outside so the inner triple-backticks render.

Structure of a PR draft response:

1. One-paragraph framing of what the PR does (prose, not in a code block)
2. **Branch name**: single-line, untagged fence
3. **For each commit in order**:
   - Heading: `### Commit N: short description`
   - The commit message in a `markdown`-tagged block, **concise** (see "Commit message style"); heavy detail belongs in the PR description
   - **(Chat surface only.)** The corresponding per-commit zip via the platform's file-presentation tool, named `commit_<N>_<slug>.zip`, containing only that commit's files ([`chat-packaging.md`](chat-packaging.md))
   - **(Coding-agent surface only.)** The edits are already in the working tree. After all text artifacts are written, offer `git checkout -b <branch>` plus per-commit `git add <paths> && git commit -F -` (and `git rm` for deletions), and wait for authorization.
4. **PR title**: single-line, untagged fence; **must** start with a type tag (see "PR title style"), e.g. `[feat] Windows support: locking, MSVC compatibility, CI matrix`
5. **PR description**: `markdown`-tagged block (inner code excerpts tagged with their real languages)
6. Final summary table (outside the code blocks) listing the deliverables. Chat surface: branch, each commit zip, anything else. Coding-agent surface: branch name, changed-file list per commit, any deletions (pointing at the working tree, not attached files).

### Deletions

**Universal principle.** List every removed path: never leave a deletion implicit; the commit must actually drop the file. Mark deletions in the commit message's file list (e.g. `* src/<pkg>/old_module.py   (removed)`).

**(Coding-agent surface only.)** Remove files with `git rm <path>` as part of the authorized git run for the commit that drops them; the surface supports the real operation, so do it (after authorization).

**(Chat surface only.)** A zip cannot carry a deletion; spell it out in chat with explicit `git rm` commands ([`chat-packaging.md`](chat-packaging.md), "Deletions in zips").

## Audience: write every artifact for its human readers

Branch names, commit messages, PR titles and descriptions (and committed docstrings and comments) are read by teammates with **no knowledge of how the change was produced**. PR descriptions are also a durable public record for people who use the code. Write them so developers, reviewers, and users can understand the parts relevant to them. Three hard rules, checked on every delivery:

- **No process leak**: no internal tooling/skill names, decomposition labels ("Band A", "Phase 2"), assistant references ("as an AI", the assistant's or model's product name), conversation references ("as discussed", "per your request"), or generation meta-commentary ("auto-generated", "if wanted"). The substance is often legitimate; rephrase it in plain engineering terms. Committed docstrings and comments are professional third-person prose, never a conversation or an edit history. Test: would a new teammate reading only the repo understand every word?
- **No personal/sensitive/device info**: no real names, usernames, emails, host/device paths, hostnames, IPs, machine/hardware specs, or secrets in any committed file (**tests and configs included**); use neutral placeholders. Scrub hardware *identity*, but keep a measurement *parameter* a claim depends on; maintainer-approved attribution (a `LICENSE` holder) is exempt.
- **Public and audience-relevant**: a PR body is not a private maintainer handoff. Include information that helps users understand behavior and compatibility, developers understand ownership and lasting constraints, or reviewers assess motivation, risk, and evidence. Omit confidential operations, private repository/history details, conversation-only instructions, and setup reminders intended only for the maintainer. Never include credentials or secrets in a PR or delivery artifact. Put non-secret maintainer-only follow-up in the maintainer handoff outside the PR.

The full rule (the complete forbidden-reference list, the rephrase example, and the identity-vs-parameter test) is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md), checked the same way on every delivery.

## PR title style

**The PR title must begin with a bracketed type tag**: a strict requirement for every PR draft, no exceptions. The tag names the *type* of work; it is distinct from the `[scope]` component prefix on a commit subject (a commit `[reader] ...` can belong to a PR titled `[perf] ...`).

| Tag | Use for |
|---|---|
| `[fix]` | Bug fixes: wrong output, crashes, regressions, incorrect behavior |
| `[feat]` | New features or capabilities |
| `[perf]` | Performance optimization (no behavior change) |
| `[doc]` | Documentation only |
| `[chore]` | Build, CI, tooling, dependency bumps, refactors with no behavior change |

Pick the tag for the PR's primary intent: a performance fix that also corrects wrong results is `[fix]` (correctness dominates); a pure speedup with identical results is `[perf]`. After the tag, a single imperative phrase, under ~70 characters including the tag: `[perf] Route moderate-K multi-column reads through the column pool`.

**Apply the host's labels.** When the repository defines labels (`gh label list` / `glab label list`), label the PR/MR at creation with every label that applies and carries information: the type label matching the title's tag (`[fix]` <-> bug, `[feat]` <-> feature/enhancement, `[doc]` <-> docs, `[chore]` <-> chore/maintenance), plus the component, scope, or breaking-change labels the change genuinely belongs to. Skip labels that would fit any PR (a generic "requires code review"), and leave priority, status, and triage labels to the maintainers. When drafting without host access, name the intended labels in the handoff.

## Commit message style

**Every commit ships with its own commit message, in its own `markdown` block: a strict requirement for every PR draft and every change delivered as commits** (zips, working-tree edits, or a patch). N commits means N commit-message blocks; a single-commit change has exactly one. The commit message is the primary artifact: never deliver a branch, PR title, PR description, patch, zip, or set of edits without it; a delivery missing it is incomplete. One commit = one message: never fold two commits' text into one block, and never let the PR description stand in for a commit message (`git log` and the review page serve different readers).

**Commit messages are scan targets, not essays.** The subject line carries the message; the body is short or absent. Deep material (root-cause mechanism, verbatim errors, ruled-out alternatives, benchmark tables) goes in the **PR description**, not the commit.

Rules:
- `[scope]` (or `scope:`) prefix, then an imperative subject under ~70 chars that alone answers "what does this commit do?"
- Body only when the subject genuinely can't stand alone; then **one or two short lines** naming the why or a single non-obvious constraint. Many commits need no body.
- A short file list at the bottom when more than two files are touched, each with a terse note.
- No error messages, stack traces, design essays, or measurements in the body; that's PR-description content.

**Example (concise, preferred):**

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

The full story (the exact MSVC error, why the macro mirrors the project's existing pattern) lives in the PR description; the commit just says what it does.

Things to drop:
- "This commit..." preambles
- Marketing language ("greatly improved", "robust")
- Anything the diff or the PR description already says
- **Any AI/assistant co-author trailer**: no `Co-Authored-By: <assistant>` line; attribute the commit to the human author only (the trailer form of the "no assistant references" rule in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md)).

## PR/MR description style

A PR/MR description is a public, durable account of the change. It must be useful to people who use the code, people who maintain it, and people who review the change. Write for the least familiar relevant reader: begin with plain-language behavior and impact, then add technical detail where it improves understanding.

A strong description is:

- **Clear:** the opening says what changed and why it matters. Use concrete behavior instead of implementation shorthand.
- **Concise:** each paragraph or bullet answers one question. Remove repeated claims, diff narration, routine status, and background that does not affect use or review.
- **Complete:** cover every material behavior, compatibility concern, migration, risk, and validation gap, not only the headline change.
- **Accurate:** verify claims about affected callers, inheritance, compatibility, performance, and test coverage. State uncertainty instead of guessing.
- **Proportionate:** a small change may need three short sections; a breaking or high-risk change may need examples, migration guidance, evidence, and rollback details.

### Adapt the content to the change

| Change type | Lead with | Add when it improves understanding |
|---|---|---|
| Feature | The new capability and who it is for | A minimal usage example or demo, limits, configuration, and interaction with existing behavior |
| Behavior or API change | A concrete before/after and the affected surface | Compatibility, migration, deprecation or breakage, failure mode, and verified downstream impact |
| Bug fix | The symptom, trigger, and user impact | A minimal reproducer, actual versus expected result, non-obvious root cause, and regression coverage |
| Performance | The affected workload and practical consequence | Baseline and new result, workload size, units, method, worst-case behavior, and resource tradeoffs |
| Refactor or internal maintenance | The developer or operational outcome and the behavior preserved | Scope boundaries, risk, ownership changes, and lasting architectural constraints |
| Dependency or packaging | What changes for installation, supported environments, or distributed artifacts | Version constraints, compatibility, security rationale, generated files, and rollback |
| Documentation, build, or CI | The workflow or audience affected | Exact commands or configuration when useful, compatibility, rollout, and generated output |

For a mixed change, combine the relevant guidance and lead with its primary outcome. Do not invent a user demo for an internal change or force a root-cause section onto a feature. Let the nature and risk of the change determine the evidence and illustration.

### Use only useful sections

Match the repository's PR/MR template when one exists. Otherwise choose from these sections and omit any that would be empty or repetitive:

- `## Summary`: a short, stand-alone account of the change and why it matters.
- `## Motivation`: the need, symptom, limitation, or measured problem that prompted the change.
- `## Impact / Compatibility`: affected users and callers, preserved behavior, breaking changes, migration, and whether failure is loud or silent.
- `## Changes`: one material behavior, contract, or operational fact per bullet. Mention implementation only when it explains a guarantee, constraint, or risk. Keep testing out of this section.
- `## Example / Demo`: the shortest realistic input, API call, command, output, screenshot, or before/after comparison that makes observable behavior easier to understand.
- `## Reproducer`: for a bug that can be reproduced, the exact minimal input or command plus actual and expected results. If the fix is already committed, obtain the before result from the base revision, preferably in a worktree, rather than reconstructing it from memory. If reproduction is impractical, describe the trigger and limitation precisely.
- `## Performance`: the workload, scale, baseline, new result, units, and measurement method. Separate typical behavior from a material worst case and name relevant resource tradeoffs.
- `## Testing`: material evidence such as regression coverage, compatibility checks, visual verification, or an important validation gap. Do not list routine lint, formatting, type checking, or CI success when host checks already show it.
- `## Risk / Rollout`: concrete residual risk, deployment or migration order, monitoring, rollback, or known limitation.
- `## Related Issues`: issue links, dependent changes, and follow-up work with public meaning.

Keep one coherent story from motivation to behavior to evidence. A compact change may need only `## Summary`, `## Changes`, and `## Testing`; do not force extra headings. Use a table when several symptoms, cases, or compatibility outcomes need an exact mapping. Use code, screenshots, diagrams, or benchmark tables only when they communicate the change more clearly than a short paragraph.

Make the description stand alone without narrating the diff. Do not assume every reader will inspect the source changes. Avoid dense internal vocabulary, editorial flourish, design advocacy, and rejected alternatives unless they expose a lasting constraint or material tradeoff. Keep private operations, conversation context, credentials, and maintainer-only setup outside the PR/MR.

## Changelog entry style

When the repository keeps a changelog (`CHANGELOG.md`, Keep-a-Changelog or similar), a user-facing change adds one entry under the unreleased section in the matching category (Added / Changed / Deprecated / Removed / Fixed), citing the PR/MR number.

**An entry is minimal and user-facing: one sentence saying what changed for the user, just enough to recognize the change.** The changelog is scanned by users asking what a release means for them; it is not a review artifact. Mechanism, rationale, internals, option enumerations, migration walkthroughs, and verification notes belong in the PR/MR description the cited number links to, never in the entry.

- Name the surface the user touches (option, command, class, method), not the implementation behind it.
- One entry per independent change; neither merge unrelated changes nor split one change across entries.
- A breaking change states what breaks and its replacement, still in one sentence.
- A second short sentence is acceptable when the change isn't recognizable without it; anything needing a third goes in the PR description.

Wrong (a review summary in the changelog):

> - Rework the HTTP client's retry handling: each request now routes through a
>   RetryPolicy object resolving per-host limits from the retry table [...],
>   a new send_with_retry() wraps the request while send() remains the
>   single-attempt path, and the fixed 200 ms delay becomes capped exponential
>   backoff with full jitter [...]

Right:

> - Retry failed HTTP requests with capped exponential backoff, configurable
>   per host through a new `retry_policy` option. (#123)

## Worked examples

Chat-surface worked examples (an inline fix and an iterative zipped fix) are in [`chat-packaging.md`](chat-packaging.md).

### Equivalent fix on the coding-agent surface
The four-file Windows lock-offset fix on the coding-agent surface: edit the four files in the repo; run the project's check suite; write the text artifacts in chat (branch in a plain fence, commit message in a `markdown` block, `[fix]`-tagged title in a plain fence, description with `## Summary` / `## Reproducer` / `## Expected behavior` / `## Root cause` / `## Testing`); offer the git run and wait; on confirmation run `git checkout -b`, `git add <paths>`, `git commit -F -`, surface branch and SHA, then hand back `git push -u origin fix/windows-file-locking` in its own block with a one-line summary. The chat output is mostly the text artifacts: no large code blocks, since the edits live in the working tree.

### What NOT to do
- Don't put a commit message or PR description in a triple-backtick block without a language tag; use ```` ```markdown ```` so it renders as formatted text, with an outer quad-backtick fence if the body contains its own triple-backtick excerpts.
- Don't append a closing summary that restates the body. The deliverables, the explanation, and the suggested commit message are the response, so stop there.

## Quick checklist before sending

**Universal (applies on both surfaces):**

- [ ] **No artifact reveals the toolchain**: branch name, PR title, commit messages, and PR description contain no skill/tool names, assistant references (including any `Co-Authored-By: <assistant>` trailer), conversation references, or generation meta-commentary; every term resolves for a teammate who only sees the repo
- [ ] **Committed docstrings and comments read as professional reference prose**: what the code is and does; no conversational artifacts, edit-history narration, or toolchain/assistant/conversation references
- [ ] **No personal/sensitive/device info**: no real names, usernames, emails, home/device paths, hostnames, IPs, machine/hardware specs, or secrets in any committed file (tests, configs, docstrings/comments included), commit message, branch, or PR text; neutral placeholders used (maintainer-approved attribution excepted)
- [ ] **PR body serves all three audiences**: users can find behavior and migration, developers can find ownership and lasting constraints, and reviewers can find motivation, risk, and evidence; none needs the conversation or a line-by-line reading of the diff
- [ ] **The opening fits the change type**: capability for a feature, before/after for a behavior change, symptom for a fix, workload for performance, or developer/operator outcome for maintenance
- [ ] **Impact and compatibility are explicit and verified when applicable**: affected callers and outputs, preserved behavior, breakage, migration, failure mode, ownership, and downstream reach are accurate
- [ ] **Illustration and evidence are proportionate**: examples, reproducers, screenshots, diagrams, or benchmarks appear only when they clarify the change and include enough context to interpret or repeat them
- [ ] **PR body covers the full material diff**: every independent behavior, packaging, documentation, migration, or repository-policy change is represented without restating files line by line
- [ ] **Changes are reader-facing**: one behavior, contract, or operational fact per bullet; test coverage stays in `## Testing`; prose uses plain terms and states facts without editorial argument
- [ ] All pre-delivery checks ran and passed (or failures are surfaced)
- [ ] Body explains why the change exists and what it means, not only how it was implemented
- [ ] **Commit messages are concise**: purpose readable at a glance from the subject; no error dumps, essays, or measurements in the body (PR-description material)
- [ ] **PR/MR description uses only applicable template headers**: matches the repository's host template when present; empty, repetitive, routine-validation, maintainer-setup, and hypothetical sections are omitted rather than padded
- [ ] Suggested commit message included for non-trivial fixes
- [ ] **Every commit has its own commit message block**: N commits means N `markdown` blocks; the delivery is incomplete without them
- [ ] For PR drafts: branch name, each commit message, PR title, PR description each in their own code block
- [ ] **PR title starts with a type tag**: `[fix]` / `[feat]` / `[perf]` / `[doc]` / `[chore]`
- [ ] **Labels applied** when the host defines them: every applicable informative label (type matching the title's tag, plus component/scope); no-information and priority/status/triage labels skipped
- [ ] **Changelog entry (when the repo keeps one) is minimal and user-facing**: one sentence per change, in the matching category, citing the PR/MR; implementation detail stays in the PR description
- [ ] **Any deletions are spelled out** and marked `(removed)` in the commit's file list
- [ ] Only ONE PR delivered this turn; planned follow-up PRs are named, not produced

**Chat surface only (zip mechanics):** see the zip-mechanics checklist in [`chat-packaging.md`](chat-packaging.md).

**Coding-agent surface only (direct edits and git operations):**

- [ ] Edits applied directly to the repo with the editing tools; no full file dumped back into chat as a code block
- [ ] No `git checkout -b`, `git add`, `git commit`, `git rm`, or `git push` run before the user authorizes it; the offer is made and the response awaited
- [ ] After authorization (if granted), the agent ran the commit itself (message piped via `git commit -F -`, not left for the user to paste), with the branch name and resulting commit SHA(s) surfaced back
- [ ] The commands the user runs on their own side, namely the push (`git push -u origin <branch>`) and any PR-open step, handed back as copy-pasteable blocks, each with a one-line summary and the literal branch name filled in
- [ ] After creating or updating a PR, its canonical URL was verified and included as a clickable link in the final handoff
- [ ] If the user declined auto-commit, the full ordered command sequence (branch, then stage, then commit, then any `git rm`, then push) was written out copy-pasteable
- [ ] Multi-commit runs paused between commits so the user can review each before the next
