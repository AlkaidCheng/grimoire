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

## Adding an artifact

1. Pick the directory that fits.
2. For a skill, create a new folder with a `SKILL.md` describing it; keep supporting files alongside it.
3. For everything else, a single well-named Markdown file is enough.
4. Keep it portable: avoid hard dependencies on one provider's API or model names.

## License

[MIT](LICENSE). Use it freely.
