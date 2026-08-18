# Skills

Self-contained skills — each one a folder that bundles instructions and any supporting files needed to perform a task.

## What belongs here

A skill is a reusable capability: a set of instructions (plus optional scripts, templates, or reference files) that an LLM-based assistant can load to do something well and repeatably.

## Shape

```
skills/
  my-skill/
    SKILL.md        # what it does, when to use it, and the instructions
    ...             # any supporting files the skill references
```

Keep each skill in its own folder, name the folder in `kebab-case`, and make `SKILL.md` describe the skill's purpose, expected inputs, and steps. Avoid hard dependencies on a specific provider or model.

## Shared references

Cross-skill reference files live in `skills/_shared/` — a folder with no `SKILL.md`, so it is not itself a skill. A skill states the essential rule inline and links to the shared file for the full detail: the skill still reads on its own, while the exhaustive version stays single-sourced and cannot drift between copies. Current shared references:

- [`_shared/human-facing-artifacts.md`](_shared/human-facing-artifacts.md) — the no-process-leak / no-personal-info rule for anything a human reads (PR text, committed source, handoff docs); used by `code-delivery`, `code-polishing`, and `session-handoff`.
- [`_shared/review-conduct.md`](_shared/review-conduct.md) — the change ethos, authoring/reviewing modes, and review delivery structure; used by `python-code-review` and `cpp-code-review`.
- [`_shared/naming-and-comments.md`](_shared/naming-and-comments.md) — language-agnostic naming, clarity-over-comments, and comment doctrine; used by `python-code-review` and `cpp-code-review`.
