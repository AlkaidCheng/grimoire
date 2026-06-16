# grimoire

A personal collection of reusable artifacts for working with large language models — skills, prompts, agent definitions, and snippets. Provider-neutral: nothing here is tied to a single model or vendor.

## Layout

| Directory | What lives here |
|-----------|-----------------|
| `skills/` | Self-contained skills — a folder per skill, each with its own instructions and any supporting files. |
| `prompts/` | Standalone prompts and prompt templates. |
| `agents/` | Agent definitions: role, tools, and behavior. |
| `snippets/` | Small reusable fragments — system blurbs, formatting rules, few-shot examples. |

## Using an artifact

Each artifact is self-describing. Open its folder (or file) and read the heading — it states what the artifact does, what it expects as input, and how to drop it into your own setup. Copy what you need; there's no install step and no runtime to wire up.

## Adding an artifact

1. Pick the directory that fits.
2. For a skill, create a new folder with a `SKILL.md` describing it; keep supporting files alongside it.
3. For everything else, a single well-named Markdown file is enough.
4. Keep it portable — avoid hard dependencies on one provider's API or model names.

## License

[MIT](LICENSE) — use it freely.
