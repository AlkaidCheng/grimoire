---
name: code-delivery
description: Use whenever the user asks for any code change (bug fix, feature, refactor, follow-up fix, or PR draft), even a terse "fix this" or "implement X". Governs how the change is delivered (direct edits plus git operations on the coding-agent surface; inline or zipped packages on the chat surface) and how the PR text artifacts (branch name, commit messages, PR title, PR description) are written. For design or structural decisions use software-design; for pre-merge structural cleanup use code-polishing; for language-specific style use python-code-review or cpp-code-review.
---

# Code Delivery

How to package and present code changes so the user can apply them quickly. Two delivery surfaces:

- **The chat surface**: no repository access. Code ships as inline fenced blocks or zipped packages surfaced through the platform's file-presentation tool; three modes: inline, zipped package, PR draft. Packaging mechanics live in [`chat-packaging.md`](chat-packaging.md); read it when packaging for this surface.
- **The coding-agent surface**: direct repository access. Code is delivered by editing files in the repo. Git operations are never run unprompted; offer them and wait for the user's go-ahead.

The PR-draft *text artifacts* (branch name, commit messages, PR title, PR description) and their writing style are identical on both surfaces; human reviewers read them regardless of how the change was produced. Sections marked with a surface name are surface-specific; everything else applies to both.

**Pipeline position.** `code-polishing` transforms the *content* of a change (iteration artifacts, dead code, stale docs, encapsulation and naming drift); the language reviews (`python-code-review` / `cpp-code-review`) apply the style standard; this skill runs **last**, packaging whatever change exists: gates, branch, commits, PR text. A bare "fix this" or "draft a PR" is delivery; "clean this up" is polishing. When the user asks to *see* the change as a rich HTML review page, produce it with `annotated-diff-html` into the active coding agent's own diff directory (e.g. `.claude/diffs/`); it accompanies the PR text, never replaces it.

## Surface: coding agent (direct edits and git operations)

The deliverable is the edited working tree; the text artifacts are written in chat.

- **Edits** go directly into the repo files. Never paste a full edited file back into chat; short clarifying excerpts are fine.
- **Every command shown to the user gets a one-line summary above it**, so it can be judged without parsing (e.g. "Push the branch and open the PR:").
- **Git operations require authorization.** Never run `git checkout -b`, `git add`, `git commit`, `git push`, or `git rm` unprompted. After the edits and pre-delivery checks, offer the git steps and wait for an explicit yes.
- **On yes, the agent itself commits**, surfacing what ran (branch, staged files, commit SHAs): `git commit -F -` with the message piped in applies the authored text verbatim. Write all the commits, then pause for review; pause after each individual commit only when the user asks to review them one by one. If the user declines auto-commit, write out the full ordered sequence (branch, stage, commit via `git commit -F -` or a heredoc, any `git rm`, push), each block pasteable as is.
- **The user's own commands are handed back explicitly**: the push (`git push -u origin <branch>`) and any PR-open step, each in its own copy-pasteable block with the literal branch name filled in. Push reveals the change externally; unless durably authorized, hand it back rather than running it.
- **A created or updated PR is surfaced as its canonical URL**, verified to name the intended base and head branches, as a clickable link in the final handoff.
- **Deletions are real**: remove files with `git rm <path>` in the authorized run, never as instructions for later, and mark them `(removed)` in the commit's file list.

## Pre-delivery checks

Run the gates the project has configured before producing any deliverable, even unasked — and only those. Discover them from the project itself rather than assuming a toolset: the test suite, the tools declared in `pyproject.toml` / `setup.cfg` (pytest, ruff, black, mypy sections), a `Makefile` / `CMakeLists.txt` target that bundles checks, or the CI workflow's steps; for C/C++, a clean rebuild watching `-Wall -Wextra`. A check the project has not adopted produces noise, not evidence (`mypy --strict` against an untyped codebase reports nothing actionable).

Report results in one or two lines ("the suite passes in 1.5s; ruff/black/mypy clean"); show any failure verbatim, never a wall of output. These handoff results reach the PR description only when they give the reviewer material evidence host checks don't already convey. When a change provably cannot affect a gate (docs-only; a script the suite never imports), say so with the reason instead of running for show — claim "unaffected" only when you can point at why.

## PR draft (text artifacts)

Produce **each text artifact — the branch name, each commit message, the PR title, the PR description — in its own fenced code block**, in the order the user would use them. The code travels alongside: per-commit zips on the chat surface ([`chat-packaging.md`](chat-packaging.md)); the already-edited working tree plus the authorization offer on the coding-agent surface.

**Language tags:** branch name and PR title in plain untagged fences (bare strings); commit messages and the PR description in `markdown`-tagged blocks (they *describe* code rather than being code). When a block contains inner fenced examples, wrap it in quad backticks so the inner triple-backticks render.

Response structure:

1. One-paragraph framing of what the PR does (prose, outside any block)
2. **Branch name**
3. **Per commit, in order**: a `### Commit N: short description` heading, the commit message block, and the surface's code delivery for that commit
4. **PR title**, starting with its type tag
5. **PR description**
6. A final summary table of the deliverables (chat surface: branch, each zip; coding-agent surface: branch, per-commit file list, any deletions)

### One PR at a time

When the work decomposes into multiple PRs, deliver ONLY the first, name the planned follow-ups in a line or two each, and end the turn. Later PRs build on the state the user actually accepted: never pre-generate their patches, zips, branch names, or text (they go stale the moment PR 1 is amended); fold the user's response in first, then prepare the next PR on the accepted state. Up-front *analysis* of later PRs is fine; the deliverables come one per turn.

**Stacked PRs.** Open a PR that builds on an unmerged one with `--base <that-branch>` so its diff shows only the delta, noting it retargets when the base merges. After the base merges, rebase with `git rebase --onto <main> <old-base> <branch>`, which replays only your commits whether the base landed as a merge or a squash (a plain `git rebase <main>` can replay already-merged commits and conflict). Generate review diffs with the three-dot range (`base...head`) so they match the host's PR view after the base advances.

## Audience: write every artifact for its human readers

Branch names, commit messages, PR titles and descriptions (and committed docstrings and comments) are read by teammates with **no knowledge of how the change was produced**; PR descriptions are also a durable public record. Three hard rules, checked on every delivery:

- **No process leak**: no internal tooling/skill names, decomposition labels, assistant references (including any `Co-Authored-By: <assistant>` trailer), conversation references ("as discussed"), or generation meta-commentary. The substance is often legitimate; rephrase it in plain engineering terms. Committed docstrings and comments are professional third-person prose, never a conversation or an edit history. Test: would a new teammate reading only the repo understand every word?
- **No personal/sensitive/device info**: no real names, usernames, emails, host/device paths, hostnames, IPs, machine/hardware specs, or secrets in any committed file (tests and configs included); use neutral placeholders. Scrub hardware *identity* but keep a measurement *parameter* a claim depends on; maintainer-approved attribution (a `LICENSE` holder) is exempt.
- **Public and audience-relevant**: a PR body is not a private maintainer handoff. Include what helps users understand behavior and compatibility, developers understand ownership and lasting constraints, and reviewers assess motivation, risk, and evidence; omit confidential operations, private repository details, conversation-only instructions, maintainer-only setup, and never credentials.

The full rule (forbidden-reference list, rephrase example, identity-vs-parameter test) is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md).

## PR title style

**The title begins with a bracketed type tag**, no exceptions; the tag names the *type* of work (distinct from a commit's `[scope]` component prefix):

| Tag | Use for |
|---|---|
| `[fix]` | Bug fixes: wrong output, crashes, regressions |
| `[feat]` | New features or capabilities |
| `[perf]` | Performance optimization (no behavior change) |
| `[doc]` | Documentation only |
| `[test]` | Test-only changes: new coverage, flaky-test fixes |
| `[refactor]` | Restructuring with identical behavior |
| `[chore]` | Build, CI, tooling, dependency bumps, maintenance |

Pick the tag for the primary intent (a performance fix that also corrects results is `[fix]`; correctness dominates); a repository's established tag set wins where it differs. After the tag, one imperative phrase, under ~70 characters in total.

**Apply the host's labels** when the repository defines them (`gh label list` / `glab label list`): the type label matching the tag, plus component/scope/breaking-change labels the change genuinely belongs to. Skip labels that fit any PR; leave priority, status, and triage to the maintainers. Without host access, name the intended labels in the handoff.

## Commit message style

**Commits are logical development steps.** Split the work into self-contained steps a reviewer can follow — a refactor preparing the ground, the behavior change, its documentation — and never squash everything into a single commit (nor scatter one step across several).

**Every commit ships with its own message in its own `markdown` block** — N commits, N blocks; a delivery without them is incomplete. Never fold two commits' text into one block or let the PR description stand in for a commit message (`git log` and the review page serve different readers).

**Commit messages are scan targets, not essays.** The subject carries the message; the body is short or absent. Deep material (root cause, verbatim errors, ruled-out alternatives, benchmarks) goes in the PR description.

- `[scope]` (or `scope:`) prefix, then an imperative subject under ~70 chars that alone answers "what does this commit do?"
- Body only when the subject can't stand alone: one or two short lines of why or a non-obvious constraint.
- A file list at the bottom when more than two files are touched, each with a terse note; deletions marked `(removed)`.
- No "This commit..." preambles, no marketing language, nothing the diff or PR description already says, and no AI/assistant co-author trailer.

Example:

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

## PR/MR description style

A PR/MR description is a public, durable account of the change, useful to users, maintainers, and reviewers. Write for the least familiar relevant reader: plain-language behavior and impact first, technical detail where it improves understanding. A strong description is:

- **Clear:** the opening says what changed and why it matters, in concrete behavior rather than implementation shorthand.
- **Concise:** each paragraph or bullet answers one question; no repeated claims, diff narration, or routine status.
- **Complete:** every material behavior, compatibility concern, migration, risk, and validation gap, not only the headline change.
- **Accurate:** verify claims about affected callers, compatibility, performance, and coverage; state uncertainty instead of guessing.
- **Proportionate:** a small change may need three short sections; a breaking or high-risk change may need examples, migration guidance, evidence, and rollback.

**Write like a reference book.** The register to aim for is a senior engineer writing an introductory book or a user manual: authoritative, technical, concise, clean — and easy to follow. Sentences carry their technical content in natural order ("two config options common to all plot classes", not "behind two config options shared by every plot class"); a comparison is spelled out ("compared with fitting each side separately") rather than compressed into a colon clause; a failure is given its concrete consequence ("growing the figure for one panel would push the others out of place"), not just its mechanism name. This is not conversational license: no chat, no hedging, no anthropomorphism, no lost precision. When a description reads badly, the fix is rephrasing, not trimming.

### Adapt the content to the change

| Change type | Lead with | Add when it improves understanding |
|---|---|---|
| Feature | The new capability and who it is for | A minimal usage example, limits, configuration, interaction with existing behavior |
| Behavior or API change | A concrete before/after and the affected surface | Compatibility, migration, breakage, failure mode, verified downstream impact |
| Bug fix | The symptom, trigger, and user impact | A minimal reproducer, actual vs expected, non-obvious root cause, regression coverage |
| Performance | The affected workload and practical consequence | Baseline and new result, workload size, units, method, worst case, tradeoffs |
| Refactor / maintenance | The developer or operational outcome and the behavior preserved | Scope boundaries, risk, ownership, lasting constraints |
| Dependency / packaging | What changes for installation, environments, or artifacts | Version constraints, compatibility, security rationale, rollback |
| Docs / build / CI | The workflow or audience affected | Exact commands or configuration, compatibility, rollout |

For a mixed change, combine the relevant rows and lead with the primary outcome. Do not invent a user demo for an internal change or force a root-cause section onto a feature.

### Use only useful sections

Match the repository's PR/MR template when one exists; otherwise choose from these and omit any that would be empty or repetitive:

- `## Summary`: a short, stand-alone account of the change and why it matters.
- `## Motivation`: the need, symptom, limitation, or measured problem behind the change.
- `## Impact / Compatibility`: affected users and callers, preserved behavior, breakage, migration, and whether failure is loud or silent.
- `## Changes`: one material behavior, contract, or operational fact per bullet; implementation only when it explains a guarantee, constraint, or risk. Testing stays out of this section.
- `## Example / Demo`: the shortest realistic input, API call, command, output, screenshot, or before/after that makes behavior easier to understand. For a new or changed API surface, show actual code in code blocks — the call site as it was and as it is now, and the shortest realistic usage of each new argument or method — rather than describing the code in sentences.
- `## Reproducer`: for a reproducible bug, the exact minimal input plus actual and expected results, with the before result taken from the base revision (preferably a worktree), not reconstructed from memory. If reproduction is impractical, describe the trigger and limitation precisely.
- `## Performance`: workload, scale, baseline, new result, units, method; typical behavior separated from a material worst case.
- `## Testing`: material evidence (regression coverage, compatibility checks, visual verification, an important validation gap); never routine lint/type/CI success the host already shows.
- `## Risk / Rollout`: concrete residual risk, deployment or migration order, monitoring, rollback, known limitation.
- `## Related Issues`: issue links, dependent changes, follow-up work with public meaning.

**Headers name kinds of content.** Each header names the kind of content its section holds — `## Summary`, `## Performance`, `## Migration`, or any other section the change warrants. A change with several parts lists them as bullets inside `## Changes`, each phrased as the change itself, so the parts stay scannable without multiplying sections.

Keep one coherent story from motivation to behavior to evidence; a compact change may need only `## Summary`, `## Changes`, and `## Testing`. Use tables, code, screenshots, or benchmark tables only when they communicate more clearly than a short paragraph. Make the description stand alone without narrating the diff, and do not restate the docstrings: parameter-by-parameter semantics live in the code the diff carries; the description covers behavior, impact, and evidence. Avoid dense internal vocabulary, editorial flourish, design advocacy, and rejected alternatives unless they expose a lasting constraint or material tradeoff.

## Changelog entry style

When the repository keeps a changelog, a user-facing change adds one entry under the unreleased section in the matching category (Added / Changed / Deprecated / Removed / Fixed), citing the PR/MR number.

**An entry is one user-facing sentence naming the surface the user touches** (option, command, class, method) — just enough to recognize the change. Mechanism, rationale, option enumerations, migration walkthroughs, and verification notes belong in the PR/MR description the cited number links to. One entry per independent change; a breaking change states what breaks and its replacement, still in one sentence; a second short sentence is acceptable only when the change isn't recognizable without it.

Wrong (a review summary): "Rework the HTTP client's retry handling: each request now routes through a RetryPolicy object resolving per-host limits [...], a new send_with_retry() wraps the request [...]".
Right: "Retry failed HTTP requests with capped exponential backoff, configurable per host through a new `retry_policy` option. (#123)"

## Formatting pitfalls

- Never put a commit message or PR description in a block without a language tag; use `markdown` so it renders as formatted text, with an outer quad-backtick fence when the body contains its own triple-backtick excerpts.
- Don't append a closing summary that restates the body; the deliverables and their explanation are the response.

Chat-surface worked examples (an inline fix and an iterative zipped fix) are in [`chat-packaging.md`](chat-packaging.md).

## Quick checklist before sending

Universal:

- [ ] No artifact reveals the toolchain, the conversation, or the assistant; every term resolves for a teammate who only sees the repo
- [ ] Committed docstrings and comments read as professional reference prose
- [ ] No personal/sensitive/device info anywhere in the delivery; neutral placeholders used
- [ ] The description's opening fits the change type; impact and compatibility are explicit and verified; the body covers the full material diff, explains why (not only how), and serves users, developers, and reviewers without needing the conversation or a line-by-line diff read
- [ ] Sections match the host's PR template when one exists; empty, repetitive, or routine-validation sections omitted; illustration and evidence proportionate to the change
- [ ] Headers are content types; changes are one reader-facing fact per bullet inside `## Changes`; testing stays in `## Testing`
- [ ] An API change shows actual code: the before/after call site and the shortest realistic usage of each new argument, in code blocks
- [ ] Prose reads like a reference manual: technical, concise, easy to follow, no editorial argument
- [ ] Pre-delivery checks ran and passed (or failures are surfaced); routine gate results stay out of the description
- [ ] Commits are logical development steps, each with its own concise `markdown` message block in its own fence; deletions marked `(removed)`; PR title starts with its type tag; applicable host labels applied
- [ ] Changelog entry (when the repo keeps one): one user-facing sentence in the matching category, citing the PR/MR
- [ ] Only ONE PR delivered this turn; follow-ups named, not produced

Chat surface (zip mechanics): see the checklist in [`chat-packaging.md`](chat-packaging.md).

Coding-agent surface:

- [ ] Edits applied directly in the repo; no full file dumped into chat
- [ ] No git write ran before the user authorized it; after authorization the agent committed itself (`git commit -F -`), surfacing branch and SHA(s), pausing for review after the commits (per commit only when asked)
- [ ] The user's own commands (push, any PR-open step) handed back as copy-pasteable blocks with one-line summaries and the literal branch name
- [ ] A created or updated PR verified and linked by its canonical URL
