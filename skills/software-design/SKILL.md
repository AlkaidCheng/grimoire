---
name: software-design
description: Use this skill when making or reviewing software *design* decisions: the structural layer above formatting and idiom. Trigger when decomposing a system into modules/classes/functions, designing an interface or API, judging whether an abstraction is right, weighing whether to refactor before adding a feature, or reviewing code for structural quality (coupling, cohesion, complexity) rather than lint-level issues. Fires on "design this module", "is this the right abstraction", "reduce the complexity here", "review the design, not the formatting", "should I refactor first", "this feels over-engineered / tangled", "why does every change ripple everywhere". Distilled from Ousterhout's *A Philosophy of Software Design*, Hunt & Thomas's *The Pragmatic Programmer*, McConnell's *Code Complete*, and Beck's *Tidy First?*. Defer to `python-code-review` / `cpp-code-review` for language style, `code-polishing` for iteration-artifact cleanup, and `code-delivery` for commit/PR mechanics.
---

# Software Design

How to split a system into parts, hide detail, and keep the whole cheap to change: the layer above formatting and naming. A capable model already writes reasonable names, short functions, early returns, and correct-before-fast; collected here are the design moves that are easy to skip under time pressure. Source tags: **[APOSD]** Ousterhout, **[PP]** Hunt & Thomas, **[CC]** McConnell, **[TF]** Beck.

The classic named principles, in this skill's sharper form:

- **SRP (Single Responsibility)**: if you cannot name a part without *and*, it holds two jobs; split it.
- **DRY**: remove the same *fact* written in two places, not chunks that merely look alike; merging lookalikes couples things that should change apart.
- **YAGNI / Rule of Three**: build for today's case; generalize on the third real occurrence, not the first imagined one.
- **KISS**: not a separate rule here; keeping complexity down is the whole point of the skill.
- **Composition over inheritance / low coupling**: see "Keep parts independent".

## Scope and hand-offs

This skill decides *what* the design problem is; the fix goes to its owner:

| Need | Owner |
|---|---|
| Language style, type hints, idioms | `python-code-review` / `cpp-code-review` |
| Stripping dead code, stale docs, iteration artifacts, renames | `code-polishing` |
| Commit split, "no behavior change" messages, PR text | `code-delivery` |

When a request mixes layers, do design first: fixing structure after formatting wastes the formatting.

## Spot complexity by its symptoms

The cost of software is mostly the cost of changing it; what drives that cost is coupling: how much one change forces other changes **[TF]**. Between two designs, prefer the one that leaves the system **easier to change** next **[PP]**. When reviewing, name the symptom; it points at the fix:

- **One change touches many files**: the same fact lives in several places, or a decision wasn't kept in one spot.
- **Too much to keep in your head**: a short function hiding three surprising side effects is worse than a longer, obvious one; fewer lines is not the goal.
- **You can't tell what you'd have to change**: the worst case, unclear what to touch or know to change safely. Fix by making the needed information visible where it's needed.

The two roots are always **dependencies** (code you can't understand or change on its own) and **things not being obvious** (needed information isn't in front of you). Every move below reduces one of them.

## Hide a lot behind a small interface

The interface is what a caller has to learn; aim for a lot of capability behind a small, simple one.

- The opposite: an interface almost as complicated as its implementation, such as fifteen tiny forwarding methods, or a "manager" that just passes calls along. Many tiny classes can be worse: the wiring between parts is its own complexity; more, smaller pieces is not automatically better.
- Every exposed option is something every future reader must learn; don't add one "in case someone needs it."
- Public-method test: *what it saves the caller vs. what the caller must learn*; if about equal, it is not earning its place.

## Organize modules around what they hide

Each module hides one decision (a file format, a wire protocol, a units convention), so when that decision changes, only that module changes.

- **Watch for the same knowledge in two places.** A format or convention written into two modules forces them to change together: the main reason one change spreads. Put whatever is most likely to change behind a single interface **[CC]**.
- **Don't split by execution order.** Read, then process, then write, one class each, makes the reader and writer both know the format. Split by what each part hides, not by when the steps run.
- **Absorb the mess in one place**: handle unavoidable mess once inside the module, not at every caller. Sensible defaults (caller passes nothing) beat forcing every caller to fill in every value.
- **Slightly general beats narrowly specific.** Build around the underlying capability, not today's single caller, but only slightly: no plugin system for one file format.

## Keep parts independent

Concrete moves that cut coupling:

- **Pass dependencies in.** A part reaching for globals or singletons is welded to them: unreadable, unreusable, untestable alone. Take what it needs as constructor or function parameters so the caller decides **[CC]**.
- **Hard to test is a design signal.** Heavy mocking or elaborate setup means tangled dependencies; fix the design, not the test scaffolding. Low coupling and easy testing are the same property.
- **Composition over inheritance.** Inheritance couples a subclass to the base's internals and its siblings; use it only for a genuine *is-a*, never just to share code.

## Design the error away where you can

Every error path adds a branch at each call site; the best error handling is the case removed by design. Before adding one, ask whether the behavior can be defined so the situation isn't an error:

- Deleting a range past the end of a string: clamp it, don't throw.
- Unset a variable that isn't set: do nothing; the end state is already what was asked for.
- Catch and combine errors at a boundary so the layers above never have to.

The flip side **[PP] [CC]**: when something that should never happen does happen, fail loudly and right away; don't quietly swallow it. Check untrusted input once at the edge of the system, then trust it inside.

## Sketch it twice

For an important interface, rough out two genuinely different designs before committing; even when the first idea wins, the comparison exposes its weak spots. Cheap, pays off, almost nobody does it. And know *why* your code works, not just that it happens to work today **[PP]**.

## Keep structural changes separate from behavior changes **[TF]**

Every edit is one of two kinds; mixing them in one commit makes both hard to review:

- **Behavior change**: changes what the software does (a feature, a bug fix).
- **Structural change**: rearranges without changing behavior (rename, extract, reorder, add an early return).

This skill only decides which findings are which, so a reviewer can trust a "no behavior change" diff. Splitting the commits, the "no behavior change" message, and the PR text belong to `code-delivery`; making the structural edits belongs to `code-polishing`.

**When to clean up code in your path** (decide, don't reflexively refactor):

- **First**: the cleanup makes the coming change clearly easier and pays off right away. Make the change easy, then make the easy change. Default for local mess you're about to touch.
- **After**: you see the better structure but shipping is urgent; follow up.
- **Later / never**: you won't be back soon, or the cleanup is big. Cleanup is an investment that only pays off on code you'll actually change again; "build it in case" applies to refactoring too.

Prefer many small cleanups, each checked, over one giant refactor PR: smaller risk, and you can stop when the payoff drops.

## Naming and comments as design signals

- **Hard to name means the design is probably off.** The *and* test (SRP above): fix the design, not just the name. Honest exception: a top-level orchestration function; coordinating a sequence of steps *is* one job, as long as it reads top-to-bottom and hands the real work to named helpers.
- **Write the interface comment first.** If the doc comment is hard to write, or explaining the interface requires describing messy internals, the *interface* is wrong; the comment caught it before you wrote the body.
- **Keep names consistent across the API.** One verb per idea (mixing `get` / `fetch` / `load` makes readers wonder whether the difference means something) and matched pairs (`open` / `close`, `to` / `from`). Spotting the inconsistency is this skill's job; the rename is `code-polishing`'s.

## The trade-offs: where judgment actually happens

These rules pull against each other; the usual answers:

- **DRY vs. keeping things separate**: remove a duplicated *fact*; leave alone lookalikes that will change for different reasons **[PP]** (see DRY above).
- **Build only what you need vs. leave room to grow**: build for today cleanly enough that tomorrow is easy to add, but don't build tomorrow today: guessed-at future needs are themselves complexity, and the future rarely arrives in the shape you guessed (Rule of Three above).
- **Hide detail vs. stay explicit**: hide implementation details; keep the contract and the flow of control visible. Cleverness that saves keystrokes now but costs debugging hours later is a bad trade.
- **Ship fast vs. keep it clean**: "it works" isn't the bar. Clean up in small steps as you go (what you touch), not a someday big refactor. Leaving obvious bad design in place tells everyone it's fine here; fix it or write it down, don't let it become normal.

## Quick review checklist

A fast structural scan; each hit is a reason to look closer, not an automatic defect:

- [ ] **One change, many files**: the same fact is probably written in several places, or an abstraction is missing
- [ ] **Thin wrapper**: a part whose interface is as complex as its implementation; many tiny forwarding classes
- [ ] **Split by execution order**: parts named for when they run (reader / processor / writer) instead of what they hide
- [ ] **Same knowledge in two places**: a format / protocol / convention written into two modules
- [ ] **Layer that only passes things through**: adds no real behavior, just plumbing
- [ ] **Does too much**: you can't name it without "and"; a grab-bag `utils`
- [ ] **Long reach**: `a.b.c.d.method()` ties you to the whole chain's structure
- [ ] **Reaches for globals, or hard to test in isolation**: dependencies are tangled; pass them in
- [ ] **Boolean that switches behavior**: a flag parameter picking between two modes is probably two functions
- [ ] **Too many error paths**: special cases that could be defined away
- [ ] **Built for a future that isn't here**: an abstraction / config / hook with exactly one caller
- [ ] **Structure and behavior mixed** in one commit is hard to review; split it
- [ ] **Inconsistent names**: one idea, several verbs; a name you couldn't write cleanly

For each hit, name the symptom (one change touches many files / too much to hold in your head / can't tell what to change) and the root (a dependency, or something not being obvious), then route the fix: style to the language reviewers, cleanup to `code-polishing`, commit and PR shape to `code-delivery`.

## The four sources, one line each

- **[APOSD]** *A Philosophy of Software Design*: keep complexity down by hiding each decision behind a simple interface.
- **[PP]** *The Pragmatic Programmer*: keep parts independent and free of duplicated facts, make things easy to change, and don't leave obvious problems unfixed.
- **[CC]** *Code Complete*: managing complexity is the main job; isolate the parts most likely to change.
- **[TF]** *Tidy First?*: the cost of change is coupling; keep structural changes separate from behavior changes, in small batches.
