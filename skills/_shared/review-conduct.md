# Review conduct: ethos, modes, and delivering the review

The canonical conduct for the coding-standard skills: why a change is made at all, the two working modes, and how a review is handed back. Referenced by `python-code-review` and `cpp-code-review`; each applies it through its own language's criteria and conventions.

## The ethos

Every change needs a reason: improved correctness, clarity, bug prevention, safety, performance, or reduced complexity. Never change code just to change it.

## Two modes

- **Authoring** (writing or changing code): apply the standards *as you write*; the default when implementing or modifying code. No separate review write-up.
- **Reviewing** (auditing existing code): check against the standards and return an improved version with a summary, per "Delivering the review" below.

## Delivering the review

Review mode only; when authoring, just write code that already meets the standard, with no separate write-up. Structure the response in order:

1. **Brief overall assessment**, a line or two: general quality and the single most important issue.
2. **The improved code as a complete replacement**: runnable or compilable as delivered, imports and includes included; never make the user stitch fragments together.
3. **The key changes grouped by category** (style, naming, types, structure, safety, logic, performance, as applicable), with brief reasoning. Focus on the non-obvious: don't list every rename, the diff speaks for itself. Call out anything that changes behavior, and any assumption made on the user's behalf, so the user can confirm or correct it.

If the code is mostly fine, say so plainly; not every review needs a rewrite. If the user requested a narrow change ("just add type hints", "add const"), focus on that but flag any glaring issue noticed along the way. When the code clearly belongs to a larger codebase, ask about the language version, toolchain, and project conventions (each language skill names the specifics) before proposing changes that might conflict.
