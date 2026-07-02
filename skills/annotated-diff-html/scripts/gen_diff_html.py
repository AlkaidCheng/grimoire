"""Render a git diff as a rich, themed, annotated review page (the pre-push diff HTML).

A generic, project-agnostic tool: it reads the diff live from git in the current
repository, so the page always reflects the current branch / working tree. Drop the
script into any project's ``.claude/scripts/`` and drive it with a small JSON config.

House style: a day/night/auto theme toggle, a line-numbered table diff with inline
per-block notes, a per-file one-click Copy button, a ``git --stat`` change summary,
and an overall summary card.

Usage:
    python gen_diff_html.py REVIEW.json      # render one annotated diff
    python gen_diff_html.py --index          # rebuild only the folder index

REVIEW.json keys (all optional):
    title       crumbs + page heading label                (default: the branch name)
    base        git ref to diff against                    (default: "main")
    head        git ref for the right side                 (default: the working tree)
    branch      display label for the diffed ref           (default: current branch)
    base_label  display label for the base                 (default: the base ref)
    output      output path                                (default: .claude/diffs/<slug>_diff.html)
    files       restrict the diff to these paths           (default: all changed paths)
    summary     overall summary card, HTML allowed         (default: none)
    notes       [{file, needle, title, why}] inline callouts; each attaches to the first
                added line in `file` containing `needle`. Unused notes are reported.

The default output directory (``.claude/diffs/``) is a convention, not a requirement;
set ``output`` to write anywhere. The folder index links each ``pr<NNN>_*`` / ``mr<NNN>_*``
page (GitHub PRs / GitLab MRs) ordered by number.

Keep each REVIEW.json next to the page it produces -- in the same ``.claude/diffs/``
directory, named to match its output (``pr<NNN>_<slug>.json`` -> ``pr<NNN>_<slug>.html``)
-- so a page's input always sits beside it and is reusable. The index scans only
``*.html``, so the JSON inputs sit alongside without affecting it.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
from typing import TypeAlias

# One diff row: (kind, old_line_no, new_line_no, text). A line number is "" when it
# does not apply to that side (an added line has no old number, a removed line no new
# number). ``kind`` is one of "hunk" | "add" | "rem" | "ctx".
DiffRow: TypeAlias = tuple[str, int | str, int | str, str]
DiffFile: TypeAlias = tuple[str, list[DiffRow]]

# localStorage key for the persisted theme choice. Project-agnostic so any repo's
# pages share the preference without colliding on a project-specific name.
_THEME_KEY = "diffhtml-theme"

_CSS = """
:root{
 --bg:#fbfbfa;--fg:#24292f;--mut:#6e7781;--bd:#d8dee4;--hd:#f3f4ee;--card:#fff;
 --add:#e6ffec;--addb:#2da44e;--rem:#ffebe9;--remb:#cf222e;--hunk:#eef1ff;--hunkf:#5a6196;
 --num:#aab1bb;--accent:#5a6196;--note:#fff8e6;--noteb:#d9b441;--notef:#6b531a;
 --addn:#1a7f37;--remn:#cf222e;--link:#3a59c9;
}
:root[data-theme="dark"]{
 --bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--bd:#30363d;--hd:#161b22;--card:#0d1117;
 --add:#12261e;--addb:#2ea043;--rem:#25171b;--remb:#f85149;--hunk:#161d33;--hunkf:#9aa4e0;
 --num:#484f58;--accent:#6e77c9;--note:#1d1a12;--noteb:#9c8326;--notef:#e3cd8a;
 --addn:#3fb950;--remn:#f85149;--link:#7d8df0;
}
@media(prefers-color-scheme:dark){:root[data-theme="auto"]{
 --bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--bd:#30363d;--hd:#161b22;--card:#0d1117;
 --add:#12261e;--addb:#2ea043;--rem:#25171b;--remb:#f85149;--hunk:#161d33;--hunkf:#9aa4e0;
 --num:#484f58;--accent:#6e77c9;--note:#1d1a12;--noteb:#9c8326;--notef:#e3cd8a;
 --addn:#3fb950;--remn:#f85149;--link:#7d8df0;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
 font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
 -webkit-user-select:text;user-select:text}
a{color:var(--link)}
.wrap{max-width:1180px;margin:0 auto;padding:30px 20px 90px}
.crumbs{font-size:13px;color:var(--mut);margin-bottom:14px}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:16px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--bd)}
.sub{color:var(--mut);font-size:13px;margin-bottom:16px}
.chip{display:inline-block;padding:1px 9px;border-radius:20px;border:1px solid var(--bd);font-size:12px;margin-right:6px}
.addn{color:var(--addn)} .remn{color:var(--remn)}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
 background:var(--hd);border:1px solid var(--bd);border-radius:4px;padding:0 4px}
pre.stat{background:var(--hd);border:1px solid var(--bd);border-radius:8px;padding:13px 15px;
 font:12.5px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-x:auto;color:var(--mut)}
pre.stat b{color:var(--fg);font-weight:600}
.card{background:var(--card);border:1px solid var(--bd);border-radius:9px;padding:2px 18px;margin:14px 0}
.card p{font-size:13.5px;color:var(--fg)}
.file{border:1px solid var(--bd);border-radius:9px;margin:18px 0;overflow:hidden;background:var(--card)}
.fhead{position:sticky;top:0;background:var(--hd);border-bottom:1px solid var(--bd);padding:9px 14px;
 font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;display:flex;justify-content:space-between;
 align-items:center;cursor:pointer;z-index:1}
.fpath{font-weight:600;word-break:break-all}
.fright{display:flex;align-items:center;gap:12px;flex:0 0 auto;padding-left:12px}
.fcount{color:var(--mut);font-size:12px;white-space:nowrap}
.copybtn{border:1px solid var(--bd);background:var(--card);color:var(--mut);cursor:pointer;
 font:11px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2px 10px;border-radius:6px;white-space:nowrap}
.copybtn:hover{color:var(--fg);border-color:var(--accent)}
table{border-collapse:collapse;width:100%;font:12.5px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
td{padding:0 8px;vertical-align:top;white-space:pre-wrap;word-break:break-word}
td.n{width:1%;min-width:44px;text-align:right;color:var(--num);
 -webkit-user-select:none;-moz-user-select:none;user-select:none;
 border-right:1px solid var(--bd);background:var(--card)}
/* Render the line number as generated content so it is never part of the
   selectable/copyable text layer -- selecting a code block and copying yields
   clean code (no line numbers), in every browser, not just those that honor
   user-select:none for the clipboard. */
td.n::before{content:attr(data-n)}
/* The code column is explicitly selectable (with the vendor prefix) so manual
   selection + copy works regardless of the non-selectable gutter beside it. */
td.s{padding-left:6px;-webkit-user-select:text;user-select:text}
tr.add td{background:var(--add)} tr.add td.s{border-left:3px solid var(--addb)}
tr.rem td{background:var(--rem)} tr.rem td.s{border-left:3px solid var(--remb)}
tr.ctx td{background:var(--ctx,transparent)} tr.ctx td.s{border-left:3px solid transparent}
tr.hunk td{background:var(--hunk);color:var(--hunkf);padding:3px 8px}
td.note{background:var(--note);border-left:4px solid var(--noteb);padding:10px 14px;
 white-space:normal;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}
td.note b{color:var(--notef)}
.collapsed table{display:none}
.themebar{position:fixed;top:12px;right:16px;display:flex;border:1px solid var(--bd);border-radius:8px;
 overflow:hidden;background:var(--card);z-index:20;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.themebtn{border:0;background:transparent;color:var(--mut);
 font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:6px 11px;cursor:pointer}
.themebtn+.themebtn{border-left:1px solid var(--bd)}
.themebtn.on{background:var(--accent);color:#fff}
/* index */
table.idx{border-collapse:collapse;width:100%;font:13.5px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
table.idx th{text-align:left;color:var(--mut);font-size:12px;font-weight:600;border-bottom:1px solid var(--bd);padding:8px 10px;white-space:nowrap}
table.idx td{padding:8px 10px;border-bottom:1px solid var(--bd);vertical-align:top;white-space:normal;word-break:normal}
table.idx tr:hover td{background:var(--hd)}
table.idx td.pr{white-space:nowrap;word-break:keep-all;width:1%;text-align:right;
 font:600 13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
table.idx td.fn{white-space:nowrap;color:var(--mut);
 font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
"""

_THEMEBAR = (
    "<div class='themebar'>"
    "<button class='themebtn' data-t='auto' onclick=\"setTheme('auto')\">Auto</button>"
    "<button class='themebtn' data-t='light' onclick=\"setTheme('light')\">Day</button>"
    "<button class='themebtn' data-t='dark' onclick=\"setTheme('dark')\">Night</button>"
    "</div>"
)

# Client-side behaviour: theme switching (persisted) and per-file copy. copyDiff
# gathers the new-side code (context + added lines) of one file and writes it to the
# clipboard, falling back to a hidden-textarea execCommand copy where the async
# Clipboard API is unavailable (file:// pages, restricted webviews).
_SCRIPT = """
function setTheme(t){document.documentElement.dataset.theme=t;try{localStorage.setItem('%(key)s',t);}catch(e){}
 document.querySelectorAll('.themebtn').forEach(function(b){b.classList.toggle('on',b.dataset.t===t);});}
(function(){var t=document.documentElement.dataset.theme||'auto';
 document.querySelectorAll('.themebtn').forEach(function(b){b.classList.toggle('on',b.dataset.t===t);});})();
function _flash(btn){var o=btn.textContent;btn.textContent='Copied';setTimeout(function(){btn.textContent=o;},1200);}
function _fallbackCopy(text){var ta=document.createElement('textarea');ta.value=text;
 ta.style.position='fixed';ta.style.top='0';ta.style.opacity='0';document.body.appendChild(ta);
 ta.focus();ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);}
function copyDiff(btn,ev){ev.stopPropagation();var lines=[];
 btn.closest('.file').querySelectorAll('tr.add td.s,tr.ctx td.s').forEach(function(td){lines.push(td.textContent);});
 var text=lines.join('\\n');
 if(navigator.clipboard&&navigator.clipboard.writeText){
  navigator.clipboard.writeText(text).then(function(){_flash(btn);},function(){_fallbackCopy(text);_flash(btn);});
 }else{_fallbackCopy(text);_flash(btn);}}
"""

FOOTER = (
    "</div><script>\n" + (_SCRIPT % {"key": _THEME_KEY}) + "\n</script></body></html>"
)


def _head(title: str) -> str:
    """Return the ``<head>`` and opening ``<body>`` for a page titled ``title``."""
    return (
        "<!doctype html><html lang='en' data-theme='auto'><head><meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>Annotated diff &mdash; {html.escape(title)}</title>\n"
        "<script>(function(){try{document.documentElement.dataset.theme="
        f"localStorage.getItem('{_THEME_KEY}')||'auto';}}catch(e){{"
        "document.documentElement.dataset.theme='auto';}})();</script>\n"
        "<style>"
        + _CSS
        + "</style></head><body>\n"
        + _THEMEBAR
        + "\n<div class='wrap'>\n"
    )


def _run(args: list[str]) -> str:
    """Run a command and return its stdout; warn on a nonzero exit."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        print(f"WARNING {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout


def parse(diff_text: str) -> list[DiffFile]:
    """Parse ``git diff`` output into per-file lists of typed diff rows."""
    files: list[DiffFile] = []
    rows: list[DiffRow] | None = None
    old_no = new_no = 0
    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            rows = None
        elif line.startswith("+++ "):
            path = line[4:]
            path = path[2:] if path.startswith("b/") else path
            rows = []
            files.append((path, rows))
        elif line.startswith("@@") and rows is not None:
            match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                old_no, new_no = int(match.group(1)), int(match.group(2))
            rows.append(("hunk", "", "", line))
        elif (
            rows is not None
            and line[:1] in ("+", "-", " ")
            and not line.startswith(("+++", "---"))
        ):
            mark = line[0]
            if mark == "+":
                rows.append(("add", "", new_no, line[1:]))
                new_no += 1
            elif mark == "-":
                rows.append(("rem", old_no, "", line[1:]))
                old_no += 1
            else:
                rows.append(("ctx", old_no, new_no, line[1:]))
                old_no += 1
                new_no += 1
    return files


def render(
    files: list[DiffFile], notes: list[dict[str, str]]
) -> tuple[str, int, int, list[str]]:
    """Render parsed files to HTML, attaching each note to its first matching added line.

    Returns the HTML body, the total added / removed line counts, and the needles of
    any notes that never matched (so the caller can warn about them).
    """
    used: set[int] = set()
    out: list[str] = []
    total_add = total_rem = 0
    for path, rows in files:
        adds = sum(1 for row in rows if row[0] == "add")
        rems = sum(1 for row in rows if row[0] == "rem")
        total_add += adds
        total_rem += rems
        out.append(
            f"<div class='file'><div class='fhead' "
            f"onclick=\"this.parentNode.classList.toggle('collapsed')\">"
            f"<span class='fpath'>{html.escape(path)}</span>"
            f"<span class='fright'>"
            f"<span class='fcount'><span class='addn'>+{adds}</span> "
            f"<span class='remn'>&minus;{rems}</span></span>"
            f"<button class='copybtn' onclick=\"copyDiff(this,event)\" "
            f"title='Copy this file&#39;s new-side code'>Copy</button>"
            f"</span></div><table>"
        )
        for kind, old_no, new_no, text in rows:
            out.append(
                f"<tr class='{kind}'><td class='n' data-n='{old_no}'></td>"
                f"<td class='n' data-n='{new_no}'></td>"
                f"<td class='s'>{html.escape(text)}</td></tr>"
            )
            if kind == "add":
                for i, note in enumerate(notes):
                    if (
                        note["file"] == path
                        and note["needle"] in text
                        and i not in used
                    ):
                        used.add(i)
                        out.append(
                            f"<tr><td class='note' colspan='3'><b>{html.escape(note['title'])}"
                            f"</b> {html.escape(note['why'])}</td></tr>"
                        )
        out.append("</table></div>")
    missing = [note["needle"] for i, note in enumerate(notes) if i not in used]
    return "\n".join(out), total_add, total_rem, missing


def _colorize_stat(stat: str) -> str:
    """Render a ``git --stat`` block as HTML: green ``+`` / insertions, red ``-`` / deletions.

    Per-file lines get their ``+``/``-`` histogram bar (the run after the ``|``)
    coloured; the trailing summary line gets its insertion / deletion counts
    coloured and is bolded.
    """
    lines = stat.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        escaped = html.escape(line)
        if "|" in escaped:
            head, _, bar = escaped.partition("|")
            bar = re.sub(
                r"\++", lambda m: f"<span class='addn'>{m.group()}</span>", bar
            )
            bar = re.sub(r"-+", lambda m: f"<span class='remn'>{m.group()}</span>", bar)
            escaped = f"{head}|{bar}"
        else:
            escaped = re.sub(
                r"(\d+ insertions?\(\+\))", r"<span class='addn'>\1</span>", escaped
            )
            escaped = re.sub(
                r"(\d+ deletions?\(-\))", r"<span class='remn'>\1</span>", escaped
            )
        if i == len(lines) - 1:
            escaped = f"<b>{escaped}</b>"
        out.append(escaped)
    return "\n".join(out)


def build_index(out_dir: str = ".claude/diffs") -> int:
    """Rebuild ``index.html`` from the ``pr<NNN>_*`` / ``mr<NNN>_*`` diffs in ``out_dir``.

    Each diff's number and kind come from its filename prefix (``pr`` for a GitHub PR,
    ``mr`` for a GitLab MR) and its label from the page's ``<title>``; the index lists
    them ascending by number so the folder is traceable by change rather than by an
    alphabetical slug. Called after every diff is written, and runnable on its own with
    ``gen_diff_html.py --index``.
    """
    entries: list[tuple[int, str, str, str]] = []
    for name in os.listdir(out_dir):
        match = re.match(r"(pr|mr)0*(\d+)_.*\.html$", name)
        if not match:
            continue
        with open(os.path.join(out_dir, name), encoding="utf-8") as fh:
            text = fh.read()
        title_match = re.search(r"<title>(.*?)</title>", text, re.S)
        title = title_match.group(1) if title_match else name
        title = re.sub(r"^Annotated diff\s*(?:&mdash;|—)\s*", "", title).strip()
        entries.append((int(match.group(2)), match.group(1), name, title))
    entries.sort(key=lambda e: (e[0], e[2]))

    rows = "\n".join(
        f"<tr><td class='pr'><a href='{html.escape(name)}'>"
        f"{'!' if kind == 'mr' else '#'}{number}</a></td>"
        f"<td><a href='{html.escape(name)}'>{title}</a></td>"
        f"<td class='fn'>{html.escape(name)}</td></tr>"
        for number, kind, name, title in entries
    )
    page = (
        _head("Annotated diffs")
        + "<div class='crumbs'>Review packet &middot; pre-push annotated diffs</div>"
        + "<h1>Annotated diffs</h1>"
        + f"<div class='sub'>{len(entries)} diffs &middot; ordered by number &middot; each row "
        + "links to its annotated diff. Rebuilt automatically when a diff is generated.</div>"
        + "<table class='idx'><thead><tr><th>Ref</th><th>Title</th><th>File</th></tr></thead>"
        + f"<tbody>\n{rows}\n</tbody></table>"
        + FOOTER
    )
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    return len(entries)


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--index":
        count = build_index()
        print(f"rebuilt .claude/diffs/index.html ({count} diffs)")
        return 0
    if len(sys.argv) != 2:
        print("usage: gen_diff_html.py REVIEW.json | --index", file=sys.stderr)
        return 2
    with open(sys.argv[1]) as fh:
        config = json.load(fh)

    base = config.get("base", "main")
    head = config.get("head")
    branch = (
        config.get("branch")
        or _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    )
    title = config.get("title") or branch
    base_label = config.get("base_label", base)
    files_filter = config.get("files") or []
    notes = config.get("notes", [])
    summary = config.get("summary", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_").lower() or "diff"
    out_path = config.get("output") or f".claude/diffs/{slug}_diff.html"

    # Three-dot (merge-base) when head is a ref, so the diff matches the GitHub PR
    # view even after the base branch advances past the fork point; plain base vs
    # the working tree when head is omitted.
    diff_cmd = ["git", "diff", f"{base}...{head}" if head else base]
    stat_cmd = [*diff_cmd, "--stat"]
    if files_filter:
        diff_cmd += ["--", *files_filter]
        stat_cmd += ["--", *files_filter]
    files = parse(_run(diff_cmd))
    stat = _run(stat_cmd).rstrip("\n")
    body, total_add, total_rem, missing = render(files, notes)

    stat_html = _colorize_stat(stat)

    header = (
        f"<div class='crumbs'>Review packet &middot; {html.escape(title)}</div>"
        f"<h1>Annotated diff &middot; <code>{html.escape(branch)}</code></h1>"
        f"<div class='sub'>base <code>{html.escape(base_label)}</code> &middot; "
        f"<span class='chip'>{len(files)} files</span>"
        f"<span class='chip addn'>+{total_add}</span>"
        f"<span class='chip remn'>&minus;{total_rem}</span> &middot; "
        f"click a file header to collapse, or its Copy button to copy the code.</div>"
    )
    if summary:
        header += f"<div class='card'><p>{summary}</p></div>"
    header += f"<h2>Change summary</h2><pre class='stat'>{stat_html}</pre><h2>Annotated diff</h2>"

    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write(_head(title) + header + body + FOOTER)
    print(f"wrote {out_path} ({len(files)} files, +{total_add} -{total_rem})")
    # Keep the folder index in step: rebuild it whenever a diff is (re)generated.
    count = build_index(out_dir)
    print(f"rebuilt {os.path.join(out_dir, 'index.html')} ({count} diffs)")
    if missing:
        print("WARNING unused notes (needle not found):", file=sys.stderr)
        for needle in missing:
            print("  -", needle, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
