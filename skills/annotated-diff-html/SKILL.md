---
name: annotated-diff-html
description: Generate a self-contained, themed HTML review page from a git diff — a line-numbered table diff, inline per-block reviewer notes pinned to specific lines, a change summary, a per-file Copy button, and a day/night/auto theme toggle — read live from git and stored in the active coding agent's repository-local diff directory. Use when the user wants a rich or visual HTML diff, a "pretty" or annotated diff to eyeball before merging, or a shareable review page for a PR/MR. Driven by a small `REVIEW.json` config and one bundled Python script.
---

# Annotated Diff HTML

Turn a `git diff` into a rich, self-contained HTML review page — one file, inline CSS/JS, no assets, no server. It reads the diff live from git (always reflecting the current branch or working tree) and carries a day/night theme toggle, line numbers, a `git --stat` change summary, an overall summary card, per-block reviewer notes pinned to specific lines, GitHub-style character-level highlighting of the exact changed spans within a modified line, and a per-file Copy button. Use it when the user asks for a "rich HTML diff", "visual diff", "pretty diff", "annotated diff", or a review page for a change / PR / MR — or when a `code-delivery` hand-off wants a review artifact alongside the PR text.

## The tool

`scripts/gen_diff_html.py` (bundled with this skill) is a single Python file — no dependencies beyond `git` and Python 3.9+. Run it from the **repository root** (it shells out to `git` in the current directory):

```
python <this-skill>/scripts/gen_diff_html.py REVIEW.json   # render one review page
python <this-skill>/scripts/gen_diff_html.py --index <agent-dir>/diffs
```

It writes the HTML to the config's `output` path — when `output` is omitted, the config's `.json` suffix becomes `.html`, keeping the page beside its input — and rebuilds an `index.html` in that directory.

## The REVIEW.json config

A small JSON file drives each page. Every key is optional:

| key | meaning | default |
|---|---|---|
| `title` | page heading + crumb label | the branch name |
| `base` | git ref to diff against | `main` |
| `head` | git ref for the right side | the working tree |
| `branch` | display label for the diffed ref | current branch |
| `base_label` | display label for the base | the base ref |
| `output` | output path | the `REVIEW.json` path with an `.html` suffix |
| `files` | restrict the diff to these paths | all changed paths |
| `summary` | overall summary card, HTML allowed | none |
| `notes` | inline callouts — see below | none |
| `editor` | editor scheme for the clickable line links: `vscode` / `vscode-insiders` / `cursor` / `windsurf` / `zed` / `idea` / `pycharm` / `sublime`, or `none` to omit | `vscode` |
| `editor_url` | custom deep-link template with `{path}`/`{line}`/`{col}` placeholders, overriding `editor` | none |
| `repo_root` | absolute dir the diff paths resolve against for the links | git toplevel |

The diff is taken as `base...head` (three-dot / merge-base) when `head` is a ref — so it matches the host's PR view even after the base branch advances — or `base` vs the working tree when `head` is omitted. `scripts/REVIEW.example.json` is a ready-to-edit template.

## Clickable line numbers

Each new-side line number deep-links to the file at that line in the configured editor; Alt-clicking a code line does the same. Removed lines carry no link. The default `vscode://` handoff works when the page is **viewed in a standalone browser** (Chrome / Safari / Firefox), where the OS can route the URI to VS Code — editor webviews commonly block custom protocols. Set `editor` to `cursor` (etc.) for a different scheme, provide an `editor_url` template for another editor, or use `none` to omit the links.

## Inline notes: annotate intent, not mechanics

`notes` is the point of the tool. Each note is `{file, needle, title, why}`: it renders as a callout **right below the first added line in `file` whose text contains `needle`** — inline comments in place, not per-file prose the reader must map back onto code. Annotate the **design-bearing** lines — an invariant being enforced, why a guard exists, a review-fix and what it prevents, an algorithm or dtype choice, a subtle edge case. Leave purely mechanical lines unannotated; a note on every line is noise. Keep the per-file summary short and let the inline notes carry the "why here". A note whose `needle` never matches is reported on stderr, so a typo'd anchor is caught.

## Where the output lives

- Use the **active coding agent's repository-local directory**: `.codex/diffs/` for Codex, `.claude/diffs/` for Claude Code, or the equivalent directory owned by another coding agent. Never put one agent's review artifacts in another agent's directory merely because that directory already exists.
- Copy `scripts/REVIEW.example.json` into that directory and name it for the change. Omitting `output` makes the renderer place the HTML beside the config automatically.
- **Name each page by its change number**: `pr<NNN>_<slug>.html` for a GitHub PR, `mr<NNN>_<slug>.html` for a GitLab MR. The tool auto-rebuilds `<agent-dir>/diffs/index.html` — a table of every `pr`/`mr` page ordered by number, with titles pulled from each page. For a not-yet-opened PR/MR, use the next number and rename if the assigned number differs.
- **Keep each `REVIEW.json` next to the page it produced**, named to match (`pr<NNN>_<slug>.json` → `pr<NNN>_<slug>.html`). The index scans only `*.html`, so JSON inputs do not affect it.

## Viewing

Open the `.html` in a **real browser** (Chrome / Safari / Firefox), where text selection, right-click, and keyboard copy all work. Restricted webviews — an editor's built-in "simple browser" preview, for instance — lock down the clipboard and context menu, so manual copy fails there; the per-file **Copy button** (clipboard API with an `execCommand` fallback) is the reliable path in those.

## Example

A minimal, complete `REVIEW.json` (see `scripts/REVIEW.example.json` for the annotated template):

```json
{
  "title": "Add exponential backoff to the retry path",
  "base": "main",
  "summary": "<p>Replaces the fixed 200 ms retry delay with capped exponential backoff and full jitter, so a downstream outage no longer produces synchronized retry storms.</p>",
  "notes": [
    {"file": "client/retry.py", "needle": "def _sleep", "title": "Full jitter, not equal jitter", "why": "Equal jitter still synchronizes the low bits across clients; full jitter (uniform 0..cap) decorrelates them, which is the point of the change."}
  ]
}
```

For Codex, save it as `.codex/diffs/pr42_retry-backoff.json` and run the render command above from the repo root.

## Relationship to `code-delivery`

An optional **review artifact** produced alongside the PR text that `code-delivery` authors, not a replacement for it: `code-delivery` still owns the branch, commit message(s), PR title, and PR description. When delivering a change and the user asks to *see* the diff as a rich page, generate it with this skill and point them at the active agent's `<agent-dir>/diffs/` output.
