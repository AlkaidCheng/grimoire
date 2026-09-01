# grimoire

A personal collection of reusable artifacts for working with large language models: skills, prompts, agent definitions, and snippets. Provider-neutral: nothing here is tied to a single model or vendor.

## Layout

| Directory | What lives here |
|-----------|-----------------|
| `skills/` | Self-contained skills: a folder per skill, each with its own instructions and any supporting files. |
| `prompts/` | Standalone prompts and prompt templates. |
| `agents/` | Agent definitions: role, tools, and behavior. |
| `snippets/` | Small reusable fragments: system blurbs, formatting rules, few-shot examples. |

## How the skills relate

Two layers. A **standard** governs how code is written: `software-design` for structure (decomposition, coupling, abstraction) and `python-code-review` / `cpp-code-review` for language (style, types, idioms), applied while you author. A **pipeline** then readies existing code to ship: clean up, review, package. `session-handoff` stands apart.

![grimoire skills: a standards layer (software-design for structure, python-code-review / cpp-code-review for language) applied while writing, above a pipeline (code-polishing, then the language review pass, then code-delivery to a PR); session-handoff is standalone.](docs/assets/skills-workflow.svg)

- **`software-design`**: the structural standard (decomposition, interfaces, coupling, complexity). Decides *what* the design problem is and hands the fix to the others. Applied while authoring and on design review.
- **`python-code-review` / `cpp-code-review`**: the language standard (PEP 8, typing, idioms / clang-format, modern C++, RAII). Applied while writing, and again as the review pass in the pipeline.
- **`code-polishing`**: content cleanup; strip iteration artifacts, dead code, stale docs, naming drift. First pipeline pass.
- **`code-delivery`**: packages and ships whatever change exists (commit/PR text and git on the coding-agent surface, or inline/zip on the chat surface). Last pipeline pass; owns the commit/PR conventions the others defer to.
- **`session-handoff`**: standalone; a cold-start handoff document when context runs low or a session ends. Not part of the code pipeline.

Which one fires: "is this the right abstraction" / "reduce complexity" calls for `software-design`; writing or reviewing Python/C++ calls for the language review; "clean this up" calls for `code-polishing`; "fix this" / "open a PR" calls for `code-delivery`.

## Using an artifact

Each artifact is self-describing. Open its folder (or file) and read the heading; it states what the artifact does, what it expects as input, and how to drop it into your own setup. Copy what you need; there's no install step and no runtime to wire up.

## Linking the skills into a project

`scripts/link_skills.sh` links every tracked skill into a project's coding-agent skill directories, one symlink per skill, so the project's own skills (real directories) coexist beside the shared set:

```
scripts/link_skills.sh <project-dir> [<project-dir>...]
```

By default both common agent paths are populated (`.claude/skills` and `.codex/skills`); choose others with `-a`:

```
scripts/link_skills.sh -a .claude ~/work/myproject   # Claude Code only
scripts/link_skills.sh -n ~/work/myproject           # dry-run
```

The script replaces a whole-directory `skills` symlink with a real directory of per-skill links, never touches a real file or directory (a project-specific skill keeps shadowing the shared one), prunes links whose grimoire skill was removed, and is idempotent: re-run it after adding a skill to the grimoire to pick it up everywhere.

`--remove` (`-r`) takes the shared skills out again. Symlinks into the grimoire are removed; a real copy is removed only when its content hash matches the grimoire skill byte for byte, so a diverged copy — a project fork or a stale snapshot — is kept and reported; links resolving elsewhere and project-specific skills are untouched, and a skills directory left empty is cleaned up:

```
scripts/link_skills.sh -r ~/work/myproject
```

## Adding an artifact

1. Pick the directory that fits.
2. For a skill, create a new folder with a `SKILL.md` describing it; keep supporting files alongside it.
3. For everything else, a single well-named Markdown file is enough.
4. Keep it portable: avoid hard dependencies on one provider's API or model names.

## License

[MIT](LICENSE). Use it freely.
