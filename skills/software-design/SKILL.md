---
name: software-design
description: Use this skill when making or reviewing software *design* decisions — the structural layer above formatting and idiom. Trigger when decomposing a system into modules/classes/functions, designing an interface or API, judging whether an abstraction is right, weighing whether to refactor before adding a feature, or reviewing code for structural quality (coupling, cohesion, complexity) rather than lint-level issues. Fires on "design this module", "is this the right abstraction", "reduce the complexity here", "review the design, not the formatting", "should I refactor first", "this feels over-engineered / tangled", "why does every change ripple everywhere". Distilled from Ousterhout's *A Philosophy of Software Design*, Hunt & Thomas's *The Pragmatic Programmer*, McConnell's *Code Complete*, and Beck's *Tidy First?*. Defer to `python-code-review` / `cpp-code-review` for language style, `code-polishing` for iteration-artifact cleanup, and `code-delivery` for commit/PR mechanics.
---

# Software Design

How to split a system into parts, how those parts hide detail and talk to each other, and how to keep the whole thing cheap to change. This is the layer above formatting and naming style.

**What this covers.** A capable model already writes reasonable names, short functions, early returns, and "get it correct before making it fast" without being told — so those aren't repeated here. This skill collects the design moves that are easy to skip under time pressure but pay off later. Each point is tagged to the book it comes from — **[APOSD]** Ousterhout, **[PP]** Hunt & Thomas, **[CC]** McConnell, **[TF]** Beck.

## Scope and hand-offs

This skill decides *what* the design problem is. It hands the fix to the skill that owns it:

| Need | Owner |
|---|---|
| Language style, type hints, idioms | `python-code-review` / `cpp-code-review` |
| Stripping dead code, stale docs, iteration artifacts, renames | `code-polishing` |
| Commit split, "no behavior change" messages, PR text | `code-delivery` |

When a request mixes layers, do design first — fixing structure after formatting wastes the formatting.

## Spot complexity by its symptoms

Complexity builds up gradually — no single change causes it, and then one day the code is hard to change safely. The cost of software is mostly the cost of changing it, and what drives that cost is coupling: how much one change forces other changes **[TF]**. So when choosing between two designs, the better one is usually the one that leaves the system **easier to change** next **[PP]**.

When reviewing, name the symptom — it points at the fix:

- **One change touches many files** — a single change forces edits all over. Usually the same fact is written down in several places, or a decision wasn't kept in one spot.
- **Too much to keep in your head** — how much you must know to change something safely. A short function that hides three surprising side effects is harder to work with than a longer, obvious one; fewer lines is not the goal.
- **You can't tell what you'd have to change** — it isn't even clear what to touch, or what to know, to make a change safely. The worst case. The fix is to make the needed information visible right where it's needed.

The two roots are always **dependencies** (code you can't understand or change on its own) and **things not being obvious** (the information you need isn't in front of you). Every move below reduces one of them.

## Hide a lot behind a small interface

A module's interface is what a caller has to learn; its implementation is what it does for them. Aim for a lot of capability behind a small, simple interface.

- The opposite is a part whose interface is almost as complicated as its implementation, so it hides little — a class of fifteen tiny forwarding methods, a "manager" that just passes calls along. Splitting code into many tiny classes can make things worse: the number of parts and the wiring between them becomes its own kind of complexity. More, smaller pieces is not automatically better.
- Keep the interface as small as it can be. Every option you expose is something every future reader has to learn — don't add one "in case someone needs it."

Quick test for a public method: *how much does it save the caller, versus how much does the caller have to learn to use it?* If those are about equal, it isn't earning its place.

## Organize modules around what they hide

Each module should hide one decision — a file format, a wire protocol, a units convention — that the rest of the system can't see and therefore can't depend on. When that decision changes, only this one module changes.

- **Watch for the same knowledge in two places.** If a format or convention is written into two modules, both have to change together — the main reason one change spreads into many. Put whatever is most likely to change behind a single interface **[CC]**.
- **Don't split by execution order.** Structuring parts as read → process → write, one class each, makes the reader and the writer both need to know the format — so the knowledge leaks between them. Split by what each part hides, not by the order the steps run in.
- **Absorb the mess in one place.** When something is unavoidably messy, deal with it once inside the module rather than making every caller handle it. Sensible defaults (the caller passes nothing) beat forcing every caller to fill in every value.
- **Slightly general beats narrowly specific.** An interface built around the underlying capability is usually cleaner than one built around today's single caller — but only slightly: don't build a plugin system for one file format.

## Design the error away where you can

The best error handling is the error case you removed by design. Every error path adds a branch at each call site. Before adding one, ask whether you can define the behavior so the situation simply isn't an error:

- Deleting a range past the end of a string → clamp it, don't throw.
- Unset a variable that isn't set → do nothing; the end state is already what was asked for.
- Catch and combine errors at a boundary so the layers above never have to.

Fewer special cases means less to keep track of. The flip side **[PP] [CC]**: when something that should never happen does happen, fail loudly and right away — don't quietly swallow it. Check untrusted input once at the edge of the system, then trust it inside.

## Sketch it twice

For an important interface, rough out two genuinely different designs before committing to one. Even when the first idea wins, comparing it against another exposes its weak spots. It's cheap and it pays off, and almost nobody does it because the quick path is to build the first thing that compiles. And make sure you know *why* your code works, not just that it happens to work today **[PP]**.

## Keep structural changes separate from behavior changes **[TF]**

Every edit is one of two kinds, and mixing them in one commit makes both hard to review:

- **Behavior change** — changes what the software does (a feature, a bug fix).
- **Structural change** — rearranges without changing behavior (rename, extract, reorder, add an early return).

This skill only decides which findings are structural and which change behavior, so a reviewer can trust a "no behavior change" diff. Splitting the commits, writing the "no behavior change" message, and the PR text belong to `code-delivery`; making the structural edits belongs to `code-polishing`.

**When to clean up code in your path** — decide, don't reflexively refactor:

- **First** — the cleanup makes the change you're about to make clearly easier, and pays off right away. Make the change easy, then make the easy change. This is the default for local mess you're about to touch.
- **After** — you can see the better structure but shipping is urgent; follow up.
- **Later / never** — it's awkward but you won't be back soon, or the cleanup is big. Cleanup is an investment; it only pays off on code you'll actually change again. "Build it in case we need it later" applies to refactoring too.

Prefer many small cleanups, each checked, over one giant refactor PR — smaller risk, and you can stop when the payoff drops.

## Naming and comments as design signals

Not "use good names / comment the why" (a model does that already). The part worth flagging:

- **If it's hard to name, the design is probably off.** If you can't name something clearly without using "and," it likely does more than one thing. Fix the design, not just the name.
- **Write the interface comment first.** If the doc comment is hard to write, or you have to describe the messy internals just to explain the interface, the *interface* is wrong — the comment caught it before you wrote the body.
- **Keep names consistent across the API.** One verb per idea (mixing `get` / `fetch` / `load` makes readers wonder whether the difference means something) and matched pairs (`open` / `close`, `to` / `from`). Spotting the inconsistency is this skill's job; doing the rename is `code-polishing`'s.

## The trade-offs — where judgment actually happens

These rules pull against each other; the skill is knowing which one wins here. The usual answers:

- **DRY vs. keeping things separate** — "don't repeat yourself" is about the same *fact* living in two places, not about two chunks of code that happen to look alike **[PP]**. Two pieces that look similar today but will change for different reasons are not real duplication; merging them ties together things that should move independently. Remove a fact that's duplicated; leave lookalikes alone.
- **Build only what you need vs. leave room to grow** — build for today cleanly enough that tomorrow is easy to add, but don't build tomorrow today. Building for guessed-at future needs is itself complexity, and the future rarely shows up in the shape you guessed. Wait for the third real case before generalizing, not the first imagined one.
- **Hide detail vs. stay explicit** — hide implementation details; keep the contract and the flow of control visible. Cleverness that saves a few keystrokes now but costs hours of debugging later is a bad trade.
- **Ship fast vs. keep it clean** — "it works" isn't the bar; keeping the design clean is part of the job. Do it in small steps as you go (clean up what you touch), not as a someday big refactor that never comes. Leaving obvious bad design in place tells everyone it's fine here — fix it or write it down, don't let it become normal.

## Quick review checklist

A fast structural scan; each hit is a reason to look closer, not an automatic defect:

- [ ] **One change, many files** — the same fact is probably written in several places, or an abstraction is missing
- [ ] **Thin wrapper** — a part whose interface is as complex as its implementation; many tiny forwarding classes
- [ ] **Split by execution order** — parts named for when they run (reader / processor / writer) instead of what they hide
- [ ] **Same knowledge in two places** — a format / protocol / convention written into two modules
- [ ] **Layer that only passes things through** — adds no real behavior, just plumbing
- [ ] **Does too much** — you can't name it without "and"; a grab-bag `utils`
- [ ] **Long reach** — `a.b.c.d.method()` ties you to the whole chain's structure
- [ ] **Boolean that switches behavior** — a flag parameter picking between two modes → probably two functions
- [ ] **Too many error paths** — special cases that could be defined away
- [ ] **Built for a future that isn't here** — an abstraction / config / hook with exactly one caller
- [ ] **Structure and behavior mixed** in one commit → hard to review; split it
- [ ] **Inconsistent names** — one idea, several verbs; a name you couldn't write cleanly

For each hit, name the symptom (one change touches many files / too much to hold in your head / can't tell what to change) and the root (a dependency, or something not being obvious), then route the fix — style to the language reviewers, cleanup to `code-polishing`, commit and PR shape to `code-delivery`.

## The four sources, one line each

- **[APOSD]** *A Philosophy of Software Design* — keep complexity down by hiding each decision behind a simple interface.
- **[PP]** *The Pragmatic Programmer* — keep parts independent and free of duplicated facts, make things easy to change, and don't leave obvious problems unfixed.
- **[CC]** *Code Complete* — managing complexity is the main job; isolate the parts most likely to change.
- **[TF]** *Tidy First?* — the cost of change is coupling; keep structural changes separate from behavior changes, in small batches.
