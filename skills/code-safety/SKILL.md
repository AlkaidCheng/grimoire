---
name: code-safety
description: Use whenever code removes, overwrites, moves or renames files or directories, builds a filesystem path from data (configuration, a user-supplied name, a command-line argument, a record read from a file), or runs an external program on such paths. Fires on "add an overwrite option", "clean up old runs", "reset the output directory", "purge", any `rm -rf`, and on review of code that already does these things. Filesystem risks are the classes covered so far. Owns the analysis of what can go wrong and the guard design around irreversible operations; defers structure to software-design, idiom to python-code-review / cpp-code-review, cleanup to code-polishing, commit and PR text to code-delivery.
---

# Code Safety

A bug in code that deletes cannot be fixed by running the code again. This skill names the ways such code goes wrong and the requirements a design meets to keep the destructive call from the wrong target even when its input is wrong. It does not hand over a finished guard: where several mechanisms meet a requirement, the author chooses and states the choice and its limits in the code. This version covers the filesystem risks: removing, overwriting and moving files, paths built from data, external programs acting on paths. A further class of risk is added as a section of the same shape (scenarios, requirements, review questions, tests); the stance holds for every class.

## Stance

- A path from data is untrusted until screened, the project's own configuration included: a typo there does what an attack does.
- The destructive call must be unable to reach anything but the program's own output. Caller discipline does not survive the second maintainer.
- The default refuses. Overwrite, purge and reset are opt-in, and the opt-in widens the target by the smallest step that does the job.
- What the program cannot confirm as its own and unchanged is moved, not deleted. A rename is reversible and costs one system call.
- The docstring states what the guard detects and what it misses. An over-stated guarantee is itself a risk; the next author builds on it.

## How deletion code goes wrong

| Scenario | Mechanism |
|---|---|
| A name from data joins a path | `""`, `.`, `..`, `../x`, an absolute name, a separator, whitespace, a leading `-`. In Python `root / ""` is `root`, and `os.path.join(root, name)` and `root / name` both discard `root` when `name` is absolute (`os.path.join("/data/run", "/etc")` is `/etc`; on Windows a leading backslash or a drive letter does the same). Java's `Path.resolve`, Rust's `PathBuf::push` and .NET's `Path.Combine` discard too; other libraries concatenate. Check the rule per library. |
| A root or near-root target | `/`, the home directory, the checkout, or the current directory when a relative path meets a process started elsewhere. |
| Symbolic links | A link in place of the output directory sends a recursive delete elsewhere; a link inside a tree is followed by some tools and not others; a link can appear between check and use. |
| A shared directory | The user's notes, another job's results or a checkout sit beside the output, and "clear the directory" deletes them. |
| Partial state | A run killed by a scheduler, out of memory or a power cut leaves half-written output that the next cleanup cannot tell from finished output, or from the user's files that went into it. |
| Two runs at once | Two processes in one directory each clear the other's files. |
| Delegated deletion | An external tool deletes with its own defaults: output into an existing directory removes it, a prompt takes the default when input is closed, a shell expands a glob, `rm -rf "$DIR"/` runs with `DIR` unset. |
| Scale | A per-file manifest or existence check passes the tests and is the step removed under time pressure at a million files. |
| Weak evidence | Modification times are set by `touch`, copies and archive extraction; names are chosen by users. |

## Requirements

In dependency order: 1 to 3 keep a path inside its directory, 4 to 6 decide what may be deleted there, 7 to 10 keep the operation safe when things go wrong around it.

1. **Screen names at the boundary.** A name that becomes a path component passes an allow-list (one component; letters, digits, a few punctuation characters; not empty; not starting with `.` or `-`; no separators; no whitespace) or is rejected. Never repair a name: stripping `..` from `....` yields `..`. Check in the constructor of the record that carries the name, so no path is built from an unscreened one.
2. **Normalize once, compare resolved paths.** Expand `~`, resolve `..` and links, make the path absolute, then refuse a filesystem root. A target is inside the root when its resolved path is relative to the resolved root and not equal to it. Build children through one helper that screens each component; delete through one helper that takes the root and checks every path before removing any.
3. **Never follow a link when deleting.** Inspect with `lstat`. A link where a file or directory is expected is refused or moved aside. The tree remover must be one that does not follow links inside the tree (Python's `shutil.rmtree` where `avoids_symlink_attacks` is true), because a link can appear after the check.
4. **Delete only the program's own artifacts, by name.** Enumerate the paths the procedure writes and clear exactly those: never "everything in the directory", never a glob.
5. **Know whose directory it is.** Before clearing, the program needs evidence it wrote itself that the directory is its output directory for this purpose and identity (job, dataset, process); a name alone is not evidence, since a user can create the same name. A marker file, a manifest, a record in a store the program owns and the external tool's own files all serve; each has a trust boundary (a marker file guards against mistakes, not against someone with write access), and the docstring states it. Refuse a directory without the evidence or with another purpose or identity.
6. **Know that nothing changed since the run finished.** Before deleting an artifact, the program needs evidence that nothing was added, removed or replaced in it since the run ended. Judge a candidate by three questions: is it cheap at scale (per-file checks are the ones removed later), can an ordinary tool forge it (`touch` sets modification times; a content digest is honest but reads everything), and what does it miss. A high-water mark over status-change times, a digest, a journal of writes and the tool's completion marker are candidates; the docstring says what the chosen one misses. Prefer evidence written once at the end of the run to a list kept during it: a list does not scale, is written by a step a hard kill skips, and records whatever the user added meanwhile.
7. **Order the work so a failed request changes nothing.** Validate every argument, then check the directory and every artifact, then remove or move aside, then write. A mistyped argument leaves earlier results in place; a refused artifact leaves the others.
8. **Move rather than delete when in doubt.** An artifact the program cannot confirm as its own and unchanged is renamed into a dated holding place in the same directory, or the whole operation is refused; which depends on whether a killed run may block the next one. Either way the function reports what it did and where things went, and the design names who cleans the holding place.
9. **Account for interruption.** Do the end-of-run bookkeeping of requirement 6 in a `finally`, so error, timeout and interrupt still record it. `SIGKILL`, the out-of-memory killer and node loss skip a `finally`; their leftovers are unconfirmed and are moved aside. Turn a scheduler's `SIGTERM` into an exception. Start external programs in their own process group and kill the group on timeout, or their children keep writing after the run is declared over.
10. **Hand paths to external programs with care.** An argument list, never a shell string; an explicit working directory; standard input closed so a prompt reads end-of-file. Read what the tool does with existing output before trusting it. Refuse a path the tool cannot take rather than quoting around it.

## Review questions

- Where does each path component come from, and where is it screened? What does the path join do with an absolute second operand?
- What happens with `""`, `.`, `..`, an absolute name, a separator, a root as the output directory, and an unexpected current directory?
- Which call removes, and what guarantees its argument lies inside the directory the caller named? Is any link followed?
- What else can be in that directory, and how does the code tell its own output from it?
- What does a rerun do after a kill at each step of the previous run?
- Is the default to refuse, and what exactly does opting in widen?
- What does the "unchanged" check miss, and does the docstring say so?
- Which external tool deletes on the program's behalf, with which defaults?
- At a million files, which step is per-file?

## Testing the guards

- Reproduce every scenario in a throwaway directory under the test runner's temporary directory, never a real path; assert a file placed just outside the target is untouched.
- Table-drive the names (`""`, `.`, `..`, `../x`, an absolute path, `a/b`, whitespace, `-x`) and the roots (`/`, `/..`).
- Place links in place of the target, inside the tree, and in place of the program's own marker if it keeps one.
- Try a directory the program never used, one used for another identity, and a user's file beside and inside the output.
- Skip the end-of-run step to simulate a kill, rerun with overwrite, and check the leftovers were not deleted.
- Mutation-test each guard: remove the check, see a test fail, restore it. A guard with no failing mutant is untested.
- Measure the check and the clearing once at scale and record the numbers beside the mechanism.

## Hand-offs

Where the pieces live (names and containment, the program's evidence about a directory, the domain's own sign) is `software-design`'s call; idiom is the language review's; `code-polishing` cleans the result; `code-delivery` writes the PR, which states what the guard detects and misses in the docstring's words.
