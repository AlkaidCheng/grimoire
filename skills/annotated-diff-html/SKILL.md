---
name: annotated-diff-html
description: Generate a self-contained, themed HTML review page from a git diff — a line-numbered table diff, inline per-block reviewer notes pinned to specific lines, a change summary, a per-file Copy button, and a day/night/auto theme toggle — read live from git and written to `.claude/diffs/`. Use when the user wants a rich or visual HTML diff, a "pretty" or annotated diff to eyeball a change before merging, or a shareable review page for a PR/MR; it is the review artifact `code-delivery` reaches for when a rich diff is requested. Driven by a small `REVIEW.json` config; one bundled Python script, no dependencies beyond git and Python 3.9+.
---

# Annotated Diff HTML

Turn a `git diff` into a rich, self-contained HTML review page — the visual, annotated diff a reviewer reads before merging, rather than scrolling raw `git diff` output. The page is a single file (inline CSS/JS, no assets, no server), reads the diff live from git so it always reflects the current branch or working tree, and carries a day/night theme toggle, line numbers, a `git --stat` change summary, an overall summary card, per-block reviewer notes pinned to specific lines, GitHub-style character-level highlighting of the exact changed spans within a modified line, and a per-file Copy button.

Reach for it when the user asks for a "rich HTML diff", a "visual diff", a "pretty diff", an "annotated diff", or a review page for a change / PR / MR — or when a `code-delivery` hand-off wants a review artifact alongside the PR text.

## The tool

`scripts/gen_diff_html.py` (bundled with this skill) is a single Python file — no dependencies beyond `git` and Python 3.9+. Run it from the **repository root** (it shells out to `git` in the current directory):

```
python <this-skill>/scripts/gen_diff_html.py REVIEW.json   # render one review page
python <this-skill>/scripts/gen_diff_html.py --index        # rebuild only the folder index
```

It writes the HTML to the config's `output` path (default `.claude/diffs/<slug>_diff.html`) and rebuilds a folder `index.html` linking every page.

## The REVIEW.json config

A small JSON file drives each page. Every key is optional:

| key | meaning | default |
|---|---|---|
| `title` | page heading + crumb label (and the output slug) | the branch name |
| `base` | git ref to diff against | `main` |
| `head` | git ref for the right side | the working tree |
| `branch` | display label for the diffed ref | current branch |
| `base_label` | display label for the base | the base ref |
| `output` | output path | `.claude/diffs/<slug>_diff.html` |
| `files` | restrict the diff to these paths | all changed paths |
| `summary` | overall summary card, HTML allowed | none |
| `notes` | inline callouts — see below | none |
| `editor` | editor scheme for the clickable line links: `vscode` / `vscode-insiders` / `cursor` / `windsurf` / `zed` / `idea` / `pycharm` / `sublime`, or `none` to omit | `vscode` |
| `editor_url` | custom deep-link template with `{path}`/`{line}`/`{col}` placeholders, overriding `editor` | none |
| `repo_root` | absolute dir the diff paths resolve against for the links | git toplevel |

The diff is taken as `base...head` (three-dot / merge-base) when `head` is a ref — so it matches the host's PR view even after the base branch advances — or `base` vs the working tree when `head` is omitted. `scripts/REVIEW.example.json` is a ready-to-edit template.

## Clickable line numbers

Each new-side line number is a deep link that opens the file at that line in the configured editor; Alt-clicking a code line does the same. The default `vscode://` handoff works when the page is **viewed in a standalone browser** (Chrome / Safari / Firefox), where the OS can route the URI to VS Code. Editor webviews commonly block custom protocols, so open the page in a standalone browser to use these links. Removed lines carry no link. Set `editor` to `cursor` (etc.) for a different scheme, provide an `editor_url` template for another editor, or use `none` to omit the links.

## Inline notes: annotate intent, not mechanics

`notes` is the point of the tool. Each note is `{file, needle, title, why}`: it renders as a callout **right below the first added line in `file` whose text contains `needle`**. This is how a reviewer leaves inline comments on specific lines, in place — far more useful than one summary paragraph per file, which forces the reader to map prose back onto code.

```json
"notes": [
  {
    "file": "src/store.py",
    "needle": "def read_header",
    "title": "Why the header offset moved",
    "why": "The old layout put the header at byte 0, so a reader opening mid-write saw a torn value. It now lives after the counters block, which is written last."
  }
]
```

Annotate the **design-bearing** lines — an invariant being enforced, why a guard exists, a review-fix and what it prevents, an algorithm or dtype choice, a subtle edge case. Leave purely mechanical lines unannotated; a note on every line is noise. Keep the per-file summary short and let the inline notes carry the "why here". A note whose `needle` never matches is reported on stderr, so a typo'd anchor is caught.

## Where the output lives

- Write pages to **`.claude/diffs/`** — a conventional, gitignored review folder. Set `output` to `.claude/diffs/<name>.html`.
- **Name each page by its change number** so the folder is traceable: `pr<NNN>_<slug>.html` for a GitHub PR, `mr<NNN>_<slug>.html` for a GitLab MR. The tool auto-rebuilds `.claude/diffs/index.html` — a table of every `pr`/`mr` page ordered by number, titles pulled from each page. For a not-yet-opened PR/MR use the next number and rename if it differs when opened.
- **Keep each `REVIEW.json` next to the page it produced**, in `.claude/diffs/`, named to match (`pr<NNN>_<slug>.json` → `pr<NNN>_<slug>.html`). A page's input then sits beside it and stays reusable — don't leave it in a temp / scratch dir. The index scans only `*.html`, so the JSON inputs don't affect it.

## Viewing

Open the `.html` in a **real browser** (Chrome / Safari / Firefox), where text selection, right-click, and keyboard copy all work. Restricted webviews — an editor's built-in "simple browser" preview, for instance — lock down the clipboard and context menu, so manual copy fails there; the per-file **Copy button** (clipboard API with an `execCommand` fallback) is the reliable path in those, but a real browser is best.

## Example

A minimal, complete `REVIEW.json` (see `scripts/REVIEW.example.json` for the annotated template):

```json
{
  "title": "Add exponential backoff to the retry path",
  "base": "main",
  "output": ".claude/diffs/pr42_retry-backoff.html",
  "summary": "<p>Replaces the fixed 200 ms retry delay with capped exponential backoff and full jitter, so a downstream outage no longer produces synchronized retry storms.</p>",
  "notes": [
    {"file": "client/retry.py", "needle": "def _sleep", "title": "Full jitter, not equal jitter", "why": "Equal jitter still synchronizes the low bits across clients; full jitter (uniform 0..cap) decorrelates them, which is the point of the change."}
  ]
}
```

Run it from the repo root:

```
python <this-skill>/scripts/gen_diff_html.py .claude/diffs/pr42_retry-backoff.json
```

## Relationship to `code-delivery`

This is an optional **review artifact** produced alongside the PR text that `code-delivery` authors, not a replacement for it. When delivering a change and the user asks to *see* the diff as a rich page — to review before pushing, or to share a visual diff — generate it with this skill and point them at the `.claude/diffs/` output. `code-delivery` still owns the branch, commit message(s), PR title, and PR description; this skill just renders the change for the eye.
