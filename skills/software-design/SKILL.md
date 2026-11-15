---
name: software-design
description: Use this skill when making or reviewing software *design* decisions: the structural layer above formatting and idiom. Trigger when decomposing a system into modules/classes/functions, designing an interface or API, judging whether an abstraction is right, grouping related types under one class hierarchy, deciding which class a function belongs to, weighing whether to refactor before adding a feature, or reviewing code for structural quality (coupling, cohesion, complexity) rather than lint-level issues. Fires on "design this module", "is this the right abstraction", "reduce the complexity here", "review the design, not the formatting", "should I refactor first", "this feels over-engineered / tangled", "why does every change ripple everywhere". Distilled from Ousterhout's *A Philosophy of Software Design*, Hunt & Thomas's *The Pragmatic Programmer*, McConnell's *Code Complete*, and Beck's *Tidy First?*. Defer to `python-code-review` / `cpp-code-review` for language style, `code-polishing` for iteration-artifact cleanup, and `code-delivery` for commit/PR mechanics.
---

# Software Design

How to split a system into parts, hide detail, and keep the whole cheap to change: the layer above formatting and naming. Maintainability is the primary goal — implement for the reader and the next change, not just for today's behavior. A capable model already writes reasonable names, short functions, early returns, and correct-before-fast; collected here are the design moves that are easy to skip under time pressure. Source tags: **[APOSD]** Ousterhout, **[PP]** Hunt & Thomas, **[CC]** McConnell, **[TF]** Beck.

The classic named principles, in this skill's sharper form:

- **Abstraction**: what shares a concept, a purpose, a kind of data or a kind of task is one abstract class, specialized by inheritance; see "Model each concept as a class". The other moves assume it.
- **SRP (Single Responsibility)**: if you cannot name a part without *and*, it holds two jobs; split it.
- **DRY**: remove the same *fact* written in two places, not chunks that merely look alike; merging lookalikes couples things that should change apart.
- **YAGNI / Rule of Three**: build for today's case; generalize on the third real occurrence, not the first imagined one.
- **KISS**: not a separate rule here; keeping complexity down is the whole point of the skill.
- **Inheritance for kinds, composition for parts / low coupling**: see "Keep parts independent".

## Scope and hand-offs

This skill decides *what* the design problem is; the fix goes to its owner:

| Need | Owner |
|---|---|
| Language style, type hints, idioms | `python-code-review` / `cpp-code-review` |
| Stripping dead code, stale docs, iteration artifacts, renames | `code-polishing` |
| Commit split, "no behavior change" messages, PR text | `code-delivery` |
| Guards for code that deletes, overwrites or builds paths from data | `code-safety` |

When a request mixes layers, do design first: fixing structure after formatting wastes the formatting.

## Spot complexity by its symptoms

The cost of software is mostly the cost of changing it; what drives that cost is coupling: how much one change forces other changes **[TF]**. Between two designs, prefer the one that leaves the system **easier to change** next **[PP]**. When reviewing, name the symptom; it points at the fix:

- **One change touches many files**: the same fact lives in several places, or a decision wasn't kept in one spot.
- **Too much to keep in your head**: a short function hiding three surprising side effects is worse than a longer, obvious one; fewer lines is not the goal.
- **You can't tell what you'd have to change**: the worst case, unclear what to touch or know to change safely. Fix by making the needed information visible where it's needed.

At function scale the symptoms have names: **cyclomatic complexity** (independent paths), **cognitive complexity** (how hard the code is for a person to follow), and **Halstead difficulty** (expression density), defined with their reduction moves in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). They quantify "too much to keep in your head": treat a high value as a symptom to name, not a number to optimize.

The two roots are always **dependencies** (code you can't understand or change on its own) and **things not being obvious** (needed information isn't in front of you). Every move below reduces one of them.

## Model each concept as a class

The first move, and the one the others build on: find the concepts and give each one class. Whatever shares a concept, serves the same purpose, holds the same kind of data or performs a similar task belongs under one abstract class, specialized by inheritance where a kind adds or changes something. The data and the behaviour that needs it then live together, and a new kind is a new subclass instead of an edit at every call site.

- **One purpose, one class.** Types that serve one purpose and differ only in which fields they fill are one class: a record of an output, of an input and of an event file each identify a file by its path, size and fingerprint, so they are one `FileRecord`, with a subclass only where a field is typed and read (`EventFileRecord` adds the format and the event count). The same count applies to roles: one external tool described by a directory class, a driver function, an adapter and a run record is one concept spread over four places. Count the classes a reader must learn for one concept; each beyond the first needs a reason the others cannot carry.
- **Specialize by inheritance.** A subclass is a kind of its base (an LHE file is a data file): it states its own facts as class attributes (its format name, its file name) and overrides only what differs, while the base holds what every kind shares, written once. A function that branches on which kind it was given (`if stage == "simulate"`) is a method each kind's class should state.
- **Refactor a helper instead of inventing one.** A helper written for the call at hand restates a little of some class's knowledge; enough of them become code no class owns, which nobody can change safely. Place a helper before writing it. If it uses one class's data or serves its purpose, it is a method of that class, or of the base when every kind needs it. If it depends on none of the concepts, generalize it until it is reusable and put it in a shared module named for what it does (`safe_paths`, `filetree`), not a grab-bag `utils`.
- **A function handed an object's own data may be that object's method.** When every call passes values one class already holds, as `record_inputs(run.input_paths, Workspace.input_classes)` does, the call site restates what the class knows and the two can drift. If the work is that class's own responsibility, put the function on the class (`workspace.input_records()`) so it reads its own state. Reading an object's data is not enough: a renderer that turns an invoice into a PDF serves presentation, and on `Invoice` it would give the domain class a presentation job and a dependency pointing the wrong way, so it stays in the layer it serves and takes the invoice as an argument. The same holds for derived facts: the class that parses a format, and so computes its fingerprint and counts, also returns the record of a file in that format; a helper that takes what the class computed and adds the rest by hand splits one responsibility in two.
- **Helpers that share an argument list are one object.** When a module grows private functions that all take the same values (a spec and a directory, a connection and a table name), those values are the state of a thing the module has not named, and each helper is one of its operations. Name the thing, give it the values once, and make the helpers its methods: the main function then reads as its sequence of steps, and nothing threads five arguments through eight calls. This is how a feature built one requirement at a time ends up as a core function ringed by helpers; the fix is the missing object, not fewer helpers. The sign to act on while writing is the third helper that takes the same first two parameters.
- **Keep a reader beside its writer.** A record written from a class's fields (`asdict`, a `to_dict`) is read back on the same class from the same list of fields, each subclass converting only what is not a plain value. A free function that names the keys by hand is a second copy of the field list, and the first field added to the class breaks it without an error.

## Hide a lot behind a small interface

The interface is what a caller has to learn; aim for a lot of capability behind a small, simple one.

- The opposite: an interface almost as complicated as its implementation, such as fifteen tiny forwarding methods, or a "manager" that just passes calls along. Many tiny classes can be worse: the wiring between parts is its own complexity; more, smaller pieces is not automatically better.
- Every exposed option is something every future reader must learn; don't add one "in case someone needs it."
- Public-method test: *what it saves the caller vs. what the caller must learn*; if about equal, it is not earning its place.

## Organize modules around what they hide

Each module hides one decision (a file format, a wire protocol, a units convention), so when that decision changes, only that module changes.

- **Watch for the same knowledge in two places.** A format or convention written into two modules forces them to change together: the main reason one change spreads. Put whatever is most likely to change behind a single interface **[CC]**.
- **Don't split by execution order.** Read, then process, then write, one class each, makes the reader and writer both know the format. Split by what each part hides, not by when the steps run.
- **Absorb the mess in one place**: handle unavoidable mess once inside the module, not at every caller. Sensible defaults (caller passes nothing) beat forcing every caller to fill in every value; keep them in one configuration place, each with the source it comes from, rather than inside the function that uses them.
- **Slightly general beats narrowly specific.** Build around the underlying capability, not today's single caller, but only slightly: no plugin system for one file format.
- **Keep each layer at its level.** A generic layer (a job, a record, a base class) names no particular tool, and a tool's module holds nothing generic: a tool's counts go into that tool's metadata rather than a field of the shared record, and a helper every tool could use moves to a shared module. Shared code that names one tool, or tool code that others import, is in the wrong layer.
- **Split along the domain's own steps.** A pipeline stage is a step a practitioner of the field would name, not a format conversion or a convenience; a check against a reference is its own command, apart from production. Ask what the people using the result care about before reaching for a formal structure.
- **A module holds a decision, not a class.** A new module for one small type is a boundary nobody needed; put the type with the module that holds its concept (what a run returns beside what runs), named the way its sibling modules are.

## Keep parts independent

Concrete moves that cut coupling:

- **Pass dependencies in.** A part reaching for globals or singletons is welded to them: unreadable, unreusable, untestable alone. Take what it needs as constructor or function parameters so the caller decides **[CC]**.
- **Hard to test is a design signal.** Heavy mocking or elaborate setup means tangled dependencies; fix the design, not the test scaffolding. Low coupling and easy testing are the same property.
- **Inheritance for kinds, composition for parts.** Inherit when the subclass is a kind of its base and shares its concept; compose when one thing uses another (a workspace has a directory; it is not one). Inheriting only to reuse code couples unrelated classes to each other's internals.

## Design the error away where you can

Every error path adds a branch at each call site; the best error handling is the case removed by design. Before adding one, ask whether the behavior can be defined so the situation isn't an error:

- Deleting a range past the end of a string: clamp it, don't throw.
- Unset a variable that isn't set: do nothing; the end state is already what was asked for.
- Catch and combine errors at a boundary so the layers above never have to.

The flip side **[PP] [CC]**: when something that should never happen does happen, fail loudly and right away; don't quietly swallow it. Check untrusted input once at the edge of the system, then trust it inside. An error the user can meet names the way out (the option or the step that resolves it) in the user's terms, built the same way wherever it is raised.

## Sketch it twice

For an important interface, rough out two genuinely different designs before committing; even when the first idea wins, the comparison exposes its weak spots. Cheap, pays off, almost nobody does it. Test each sketch against the real scale and against failure (a million files, a run killed halfway), not the example in front of you. And know *why* your code works, not just that it happens to work today **[PP]**.

For a family of data types, sketch the data before the code: one row per type, its fields, and the code that reads each field. Rows that hold the same kind of information for the same purpose are one type, while rows that only share fields stay apart (two identifiers that each hold a string keep their own types, so one cannot be passed for the other); a field without a reader goes, the class that computes a field is the one that fills it, and the names follow from what each row holds. When a reviewer rejects one name or one class of the family, redo the table instead of replacing that one item: its siblings were chosen the same way, and fixing them one review at a time costs a round each.

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
- **Keep one spelling per idea across surfaces.** A concept that appears as a command, a flag, a configuration key, a record key, a directory and an identifier under different names (`--log-level`, `logLevel`, `verbosity`) is a decision nobody made; a reader pays for the mapping at every boundary. Name a step after the action the user invokes, not the tool that performs it: the tool can change, the action is the contract. A name that differs across surfaces is a design finding because fixing it changes what the program writes and accepts.
- **A name built on "without" or "except" is a prompt to look at ownership.** Often it is the right name: `rows_except_total` for a filtered collection that one part computes and uses. It is a design finding when the exclusion exists because two parts each hold a piece of one list, so that one part has to name what the other contributes. Then give each part its own piece (the base class contributes its item, the subclass extends the list) instead of naming around the split.
- **A stored field that only repeats another field is a second copy of a fact.** Check what the field holds first: a `retry_reason` that records something the status of the previous attempt does not say is information and stays. When every value of the field follows from other fields of the same record, as an `is_empty` beside a count does, derive it where it is read, since two copies can disagree. A value of an enumeration must also read correctly on every record that can carry it.
- **Every stored field has a reader.** Name who reads each field a record keeps: the code, a person auditing the record, or a documented tool outside the repository. A value with no reader of any kind, such as a hash of every output that neither code nor provenance needs, costs time on each run and must still be kept correct; leave it unset, or compute it where its reader needs it. A field kept as provenance is taken when the run happens, since it cannot be rebuilt once the inputs change. Record only what can be recorded truly: the thread count a program was asked for is not the count it used.
- **Check an option's name against its behavior in every state.** For a flag or a boolean parameter, write down what a newcomer expects from the name alone in each state the target can be in (never started, in progress, failed, finished, changed since). Where the behavior differs, change the name or the behavior. An option that raises an error in a state where its name says "carry on" is a design finding, not a documentation gap.

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
- [ ] **Helpers sharing an argument list**: private functions that all take the same values are one object's methods; name the object
- [ ] **Helper with no home**: a free function that is neither a method of the class whose responsibility it carries nor a general function in a module named for what it does; one handed an object's own data (`f(x.paths, X.classes)`) for that object's own work, or a reader that names the keys its writer derives from fields, belongs on that class
- [ ] **Parallel types with one purpose**: compare their fields; one class, with a subclass where a field is typed and read
- [ ] **Field nobody reads**, no code, person or external tool, above all one that is costly to compute
- [ ] **Long reach**: `a.b.c.d.method()` ties you to the whole chain's structure
- [ ] **Reaches for globals, or hard to test in isolation**: dependencies are tangled; pass them in
- [ ] **Boolean that switches behavior**: a flag parameter picking between two modes is probably two functions
- [ ] **Branch on the kind of thing**: a method each kind's class states; **a tool's name in a generic layer**: move the code to the layer it serves
- [ ] **Too many error paths**: special cases that could be defined away
- [ ] **Built for a future that isn't here**: an abstraction / config / hook with exactly one caller
- [ ] **Structure and behavior mixed** in one commit is hard to review; split it
- [ ] **Inconsistent names**: one idea, several verbs; a name you couldn't write cleanly; one concept spelled differently on the command line, on disk and in code
- [ ] **Name built on an exclusion** (`x_without_y`), **field that may only repeat another field**, **option whose name and behavior part ways in some state**: look for a structural cause before renaming

For each hit, name the symptom (one change touches many files / too much to hold in your head / can't tell what to change) and the root (a dependency, or something not being obvious), then route the fix: style to the language reviewers, cleanup to `code-polishing`, commit and PR shape to `code-delivery`.

## The four sources, one line each

- **[APOSD]** *A Philosophy of Software Design*: keep complexity down by hiding each decision behind a simple interface.
- **[PP]** *The Pragmatic Programmer*: keep parts independent and free of duplicated facts, make things easy to change, and don't leave obvious problems unfixed.
- **[CC]** *Code Complete*: managing complexity is the main job; isolate the parts most likely to change.
- **[TF]** *Tidy First?*: the cost of change is coupling; keep structural changes separate from behavior changes, in small batches.
