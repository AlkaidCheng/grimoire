---
name: session-handoff
description: Write a handoff document that lets a future session continue a coding project from a cold start: no shared memory, no access to this session's files. Use when the context window is running low or a session is about to end and its state must carry into a fresh one, and when the user asks to summarize a session, write a handoff or "context for next time", capture where things stand, or set up a clean pickup point; also covers a cumulative reference summary spanning a multi-session effort. The defining discipline is detailed in the body: reference only durable state (merged code, real branch and commit names), never the ephemeral session filesystem.
---

# Session handoff

A handoff is written for a reader you will never meet: a future session with a clean filesystem, no memory of this conversation, and nothing to work from but the repository and this document. Write it when the context window is running low or the session is wrapping up. The single mistake that makes a handoff worse than useless is pointing at things that will not exist: a working copy under `/tmp`, a generated patch in an output folder, "the zip attached earlier". Those evaporate, and the reference implies the work is retrievable when it is not.

## Reference only what survives the session

- **Durable (cite freely):** code merged into the repository, branch and commit identifiers that exist there, established facts about the system, the handoff prose itself.
- **Ephemeral (never lean on it):** everything the session created in its own container: output folders, patch files, zips, scratch checkouts, the upload path an input arrived on.
- In-flight work: the patch will be gone, so describe each change precisely enough to **re-create it from the repository** (what changed, in which files, why, how it was verified) and treat that description as the spec.
- Record each change's status as "merged" or "needs reproducing from the description below," never as a path. Tell the reader to establish what landed by diffing the current repo against the descriptions, not by opening an artifact.
- An index of session-local files is not a convenience to add; it is a thing to cut.

## Build on the prior handoff instead of repeating it

If a previous handoff exists, read it first and treat it as the established record. Point back to it for everything that did not change (architecture, data model, testing approach, conventions) and spend the new document only on what moved this session. "The prior handoff still describes X; read it for that" is a complete and honest section; restating unchanged material buries the delta and creates a second copy that drifts out of date.

## What earns a place in the document

A workable skeleton, to adapt rather than follow rigidly:

```
# <project>: handoff (<what this session was about>)
## What this is:            a few sentences: the system, its purpose, its main features, stack, where it runs (or a one-line identity plus a pointer to the prior handoff)
## State at the close:      the baseline in repo terms; what is verified; what is in flight
## What this session changed: each change as a reproducible spec: problem, change, why, files, result, scope (what it does not touch), verification
## Findings to carry forward: the reasoning, premises that evidence overturned, failure modes caught, the methodology
## Roadmap:                  what is next and why, in priority order; flag items that need evidence before acting
## Rejected alternatives:    ideas tried and dropped, each with the evidence or reason that rejected it: "do not re-propose without new evidence"
## Deliberately left alone:  pre-existing non-issues and out-of-scope items, so they are not re-flagged
## Conventions:              gating rules, quality gates, delivery discipline (or a pointer to the prior handoff)
## Status:                   per change: merged, or reproduce-from-spec; how to confirm
```

Lead with orientation: a cold-start reader cannot make sense of any delta until they know what the system is. Open with a few accurate sentences: what the project is and is for, its main features or public surface, the language and stack, and where it runs or deploys. A short paragraph, favoring durable identity over implementation detail that will date. For a continuation handoff, a one-line identity plus a pointer to the prior handoff is enough; never re-derive the whole architecture, but never leave the reader with no idea what they are working on.

The sections that repay the most effort, the ones a fresh session cannot reconstruct:

- **Reasoning behind decisions**, not just the decisions: why an approach was chosen, the tradeoff, which failure mode a guard exists to prevent. Without that, a session relitigates settled questions or undoes a fix whose purpose is invisible.
- **The premise each change rested on, especially when evidence overturned the obvious one**: "the bug was assumed to be in input validation; tracing showed it was a race in the signup handler" stops the next session from chasing the wrong cause.
- **Scope**: bound each change by naming what it leaves untouched (which inputs, paths, or platforms still run the old way), so the reader knows the blast radius.

Three standing lists:

- **Rejected alternatives, each paired with the evidence or reason that rejected it**, under a heading that says plainly "do not re-propose without new evidence." A bare "we didn't do X" invites the next session to try X; "X was tried and dropped because it broke the streaming API's ordering guarantee" closes the question until the requirements change.
- **Deliberately left alone**: pre-existing warnings out of scope for the work, motivation that reads as iteration but is legitimate, so it is not re-flagged as an oversight.
- **Roadmap in priority order**: mark items that need investigation before action ("get the evidence first; do not change this on intuition") and, for each deferred item, the condition that would reopen it.

## Be concrete, and write it for a teammate

- Name the actual files, symbols, functions, and flags; quote the real numbers and the real error; state thresholds and counts. "Improved the flow" gives a future session nothing to act on.
- Tie every claim to the **condition it holds under** (the inputs, environment, or scale it was checked at) and say where the change does *not* apply or was confirmed to carry no regression: not "fixed the login bug" but "fixed the login failure that hit SSO users on token refresh; password login was never affected."
- Performance claims carry their regime: "3x on many-small-record inputs, ~1x on few-large," never a bare "3x faster."
- Write for a human engineer who will read only the repo and this file. Keep out anything that resolves only inside the session: references to the assistant, this conversation, or internal tooling or process names (the full no-process-leak / no-personal-info rule is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md)). The one exception: "this session," "the prior session," and "the next session" are the natural timeline vocabulary and read correctly to anyone.
- Plain, professional prose; a table only where a status grid or a comparison genuinely helps.

## What it looks like in practice

Orientation a stranger could absorb in one read (identity, purpose, surface, stack, runtime) and no more:

```
## What this is
`webcache` is a thread-safe HTTP response cache for Python services: a
read-through cache (`get_or_fetch`), TTL/LRU eviction, and a pluggable backend
(in-memory or Redis). Pure Python over `urllib3`; runs in-process inside the
host service. (A continuation handoff: one line plus "see `handoff-2026-05.md` section 1".)
```

The contrast that matters most is how in-flight work gets recorded. Never the version that points at the session's own filesystem:

```
### PR 3: retry backoff
Delivered as a patch under outputs/pr3/ and zipped; apply the zip from the repo
root. Baseline is the uploaded project.zip.
```

Instead, a spec actionable from the repository alone, carrying its premise, verification, scope, and an observable status:

```
### Exponential backoff on the HTTP retry path (queued)
Branch `fix/retry-backoff`; 1 commit. `client/retry.py`: the retry loop slept a
fixed 200 ms between attempts; replaced with capped exponential backoff
(base 200 ms, factor 2, cap 5 s, full jitter). Premise check first: the outage
storms were assumed to be pool exhaustion; tracing showed synchronized retries
from the fixed delay. Verified: full suite (142 tests) plus a new
`test_backoff_is_jittered` that fails on the old code. Scope: touches only the
delay between attempts; retry count, error classification, and the connection
pool are unchanged. Status: not confirmed merged; if `retry.py` still shows the
fixed `sleep(0.2)`, reproduce from this description.
```

Roll the per-change statuses into one grid keyed on what the reader can observe in the repo:

```
| Change | Files | Status to confirm |
|---|---|---|
| Exponential backoff on retries | `client/retry.py` | Merged if no fixed `sleep(0.2)` remains; else reproduce from section 2. |
| Rename `--cache-ttl-secs` -> `--cache-ttl` | `cli.py`, `docs/usage.md` | `--help` shows `--cache-ttl`; else reproduce from section 2. |
```

Keep the dead ends closed: each rejected or skipped item pairs the thing with the evidence and its reopen condition:

```
## Rejected alternatives (do not re-propose without new evidence)
- A dedicated cache-invalidation API so callers could purge keys directly:
  dropped because it exposes the internal key layout and every caller would
  couple to it; the TTL plus read-through refresh already cover the cases we
  have. Revisit only if a caller needs sub-TTL invalidation.

## Deliberately left alone
- The dependency deprecation warnings in `client/pool.py` predate this work and
  are out of scope for a retry fix; a dependency-bump PR should handle them.
```
