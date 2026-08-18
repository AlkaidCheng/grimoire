# Skills

Self-contained skills: each one a folder that bundles instructions and any supporting files needed to perform a task.

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

## House style

A skill is read by whichever assistant loads it, so it is written for any of them:

- **Vendor-neutral vocabulary.** Never name a specific assistant, model, or vendor tool as though it were the only one. Describe the capability instead. Two surfaces recur across these skills and have fixed names: the **chat surface** (a conversation with no repository access, where a change ships as pasted code or an attached archive) and the **coding-agent surface** (direct access to the working tree, where the agent edits files and runs git). A concrete product or directory name is fine only as an example of a generically stated rule, for example `.codex/diffs/` and `.claude/diffs/` illustrating "the active coding agent's repository-local diff directory".
- **Printable ASCII, no em-dashes**, per [`_shared/human-facing-artifacts.md`](_shared/human-facing-artifacts.md) (Rule 3). It applies to the skill files themselves, not only to the artifacts they produce.

## Shared references

Cross-skill reference files live in `skills/_shared/`, a folder with no `SKILL.md`, so it is not itself a skill. A skill states the essential rule inline and links to the shared file for the full detail: the skill still reads on its own, while the exhaustive version stays single-sourced and cannot drift between copies. Current shared references:

- [`_shared/human-facing-artifacts.md`](_shared/human-facing-artifacts.md): the no-process-leak / no-personal-info rule for anything a human reads (PR text, committed source, handoff docs); used by `code-delivery`, `code-polishing`, and `session-handoff`.
- [`_shared/review-conduct.md`](_shared/review-conduct.md): the change ethos, authoring/reviewing modes, and review delivery structure; used by `python-code-review` and `cpp-code-review`.
- [`_shared/naming-and-comments.md`](_shared/naming-and-comments.md): language-agnostic naming, clarity-over-comments, and comment doctrine; used by `python-code-review` and `cpp-code-review`.
