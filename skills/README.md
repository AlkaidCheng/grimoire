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
