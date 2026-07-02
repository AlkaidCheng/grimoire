---
name: session-handoff
description: Write a handoff document that lets a future session continue a coding project from a cold start — no shared memory, no access to this session's files. Use when the context window is running low or a session is about to end and its state must carry into a fresh one, and when the user asks to summarize a session, write a handoff or "context for next time", capture where things stand, or set up a clean pickup point; also covers a cumulative reference summary spanning a multi-session effort. The defining discipline — reference only durable state (merged code, real branch and commit names), never the ephemeral session filesystem — is detailed in the body.
---
 
# Session handoff
 
A handoff is written for a reader you will never meet: a future session that opens with a clean filesystem, no memory of this conversation, and nothing to work from but the repository and the document you leave behind. You write it when the context window is running low or a session is wrapping up — the point where the live state is about to evaporate — so that reader can resume without you in the room. The single mistake that makes a handoff worse than useless is pointing at things that will not exist — a working copy under `/tmp`, a generated patch in an output folder, "the zip attached earlier." Those evaporate when the session ends, so a reference to them sends the next session hunting for a file it can never open, and quietly implies the work is retrievable when it is not.
 
## Reference only what survives the session
 
At handoff time two kinds of state exist and only one persists. Durable: code actually merged into the repository, the branch and commit identifiers that exist there, established facts about the system, and the handoff prose itself. Ephemeral: everything the session created in its own container — output folders, patch files, zips, scratch checkouts, the upload path an input arrived on. Cite the durable kind freely; never lean on the ephemeral kind.
 
This shapes how you record in-flight work. The patch that implemented a change will be gone, so describe the change precisely enough to **re-create it from the repository** — what changed, in which files, why, and how it was verified — and treat that description as the spec. Record each change's status as "merged" or "needs reproducing from the description below," never as a path. Tell the reader to establish what actually landed by diffing the current repo against the descriptions, not by opening an artifact. An index of session-local files is not a convenience to add; it is a thing to cut.
 
## Build on the prior handoff instead of repeating it
 
If a previous handoff exists, read it first and treat it as the established record. Point back to it for everything that did not change — the architecture, the data model, the testing approach, the conventions — and spend the new document only on what moved this session. Restating unchanged material buries the delta the reader actually needs and creates a second copy that drifts out of date. "The prior handoff still describes X; read it for that" is a complete and honest section, and a far better one than a paraphrase.
 
## What earns a place in the document
 
A workable skeleton, to adapt rather than follow rigidly:
 
```
# <project> — handoff (<what this session was about>)
## What this is            — a few sentences: the system, its purpose, its main features, stack, where it runs (or a one-line identity plus a pointer to the prior handoff)
## State at the close      — the baseline in repo terms; what is verified; what is in flight
## What this session changed — each change as a reproducible spec: problem, change, why, files, result, scope (what it does not touch), verification
## Findings to carry forward — the reasoning, premises that evidence overturned, failure modes caught, the methodology
## Roadmap                  — what is next and why, in priority order; flag items that need evidence before acting
## Rejected alternatives    — ideas tried and dropped, each with the evidence or reason that rejected it: "do not re-propose without new evidence"
## Deliberately left alone  — pre-existing non-issues and out-of-scope items, so they are not re-flagged
## Conventions              — gating rules, quality gates, delivery discipline (or a pointer to the prior handoff)
## Status                   — per change: merged, or reproduce-from-spec; how to confirm
```
 
Lead with orientation. A cold-start reader cannot make sense of any delta until they know what the system is, so open with a few accurate sentences: what the project is, what it is for, its main features or public surface, the language and stack, and where it runs or deploys. Keep it to a short paragraph — this is a map, not the territory, and it must stay true as the project moves, so favor durable identity over implementation detail that will date. For a continuation handoff a one-line identity plus a pointer to the fuller description in the prior handoff is enough; never re-derive the whole architecture, but never leave the reader with no idea what they are working on either.
 
The sections that repay the most effort are the ones a fresh session cannot reconstruct on its own:

- **Reasoning behind decisions**, not just the decisions — why an approach was chosen, what the tradeoff was, which failure mode a guard exists to prevent. Without that context a session will relitigate settled questions or undo a fix whose purpose is invisible.
- **The premise each change rested on, especially when evidence overturned the obvious one**: "the bug was assumed to be in input validation; tracing showed it was a race in the signup handler" is worth more than the change itself, because it stops the next session from chasing the wrong cause.
- **Scope** — bound each change by naming what it leaves untouched (which inputs, paths, or platforms still run the old way), so the reader knows the blast radius and what is still on the table.
 
Three standing lists are worth keeping:

- **Rejected alternatives, each paired with the evidence or reason that rejected it**, under a heading that says plainly "do not re-propose without new evidence." A bare "we didn't do X" invites the next session to try X and rediscover why it loses; "X was tried and dropped because it broke the streaming API's ordering guarantee" closes the question until the requirements change.
- **Deliberately left alone** — pre-existing warnings out of scope for the work, motivation that reads as iteration but is legitimate — so it is not re-flagged as an oversight.
- **Roadmap in priority order** — mark items that need investigation before action ("get the evidence first; do not change this on intuition") and, for each deferred item, the condition that would reopen it.
 
## Be concrete, and write it for a teammate
 
Vague summaries do not survive a cold start. Name the actual files, symbols, functions, and flags; quote the real numbers and the real error; state thresholds and counts. A future session acts on specifics, and "improved the flow" tells it nothing it can use. Tie every claim to the **condition it holds under** — the inputs, environment, or scale it was checked at — and say explicitly where the change does *not* apply or where it was confirmed to carry no regression. A bare "fixed the login bug" is not actionable; "fixed the login failure that hit SSO users on token refresh — password login was never affected" tells the reader exactly where the fix lands and where it does not. Performance claims follow the same rule: "3× faster" alone is not actionable; attach the regime — "3× on many-small-record inputs, ~1× on few-large."
 
Write the document for a human engineer who will read only the repo and this file. Keep out anything that resolves only inside the session that produced it — references to the assistant, to this conversation, to internal tooling or process names (the full no-process-leak / no-personal-info rule is in [`../_shared/human-facing-artifacts.md`](../_shared/human-facing-artifacts.md)). The one exception is framing the timeline: "this session," "the prior session," and "the next session" are the natural vocabulary of a handoff and read correctly to anyone. Plain, professional prose, with a table where a status grid or a comparison genuinely helps and prose everywhere else.
 
## What it looks like in practice
 
Open with orientation a stranger to the project could absorb in one read — identity, purpose, surface, stack, runtime — and no more:
 
```
## What this is
`webcache` is a thread-safe HTTP response cache for Python services: a
read-through cache (`get_or_fetch`), TTL and LRU eviction, and a pluggable
backend (in-memory or Redis). Pure Python over `urllib3`; runs in-process
inside the host service. Priorities: correctness under concurrency first, then
hit-rate, then footprint. (A continuation handoff would shrink this to one line
plus "see `handoff-2026-05.md` §1".)
```
 
The contrast that matters most is how in-flight work gets recorded. Avoid the version that points at the session's own filesystem — the next session has none of these files:
 
```
### PR 3: retry backoff
Delivered as a patch under outputs/pr3/ and zipped; apply the zip from the repo
root. Baseline is the uploaded project.zip.
```
 
Write it instead as a spec the next session can act on from the repository alone — what changed, why, how it was checked, and how to tell whether it landed:
 
```
### Exponential backoff on the HTTP retry path (queued)
Branch `fix/retry-backoff`; 1 commit. `client/retry.py` — the retry loop slept a
fixed 200 ms between attempts; replaced with capped exponential backoff
(base 200 ms, factor 2, cap 5 s, full jitter). Why: under a downstream outage the
fixed delay produced synchronized retry storms. Verified: full suite (142 tests)
plus a new `test_backoff_is_jittered`. Status: not confirmed merged — if
`retry.py` still shows the fixed `sleep(0.2)`, reproduce from this description.
```
 
A change carries its premise and its limits alongside the diff, so the next session inherits the reasoning rather than the hunch behind it:
 
```
### Stale entries served after a backend switch (merged)
Branch `fix/backend-switch-staleness`; 2 commits. Premise check first: the stale
reads were assumed to be a TTL bug, but tracing showed the in-memory and Redis
backends derived the cache key differently, so switching backends orphaned the
old keys instead of expiring them. Change: move key derivation into one shared
`cache_key()` that both backends call (`cache/store.py`, `cache/redis_backend.py`).
Verified: full suite plus a new `test_key_is_backend_independent` that fails on
the old code. Scope: touches only key derivation — eviction, TTL, and the
read-through path are unchanged.
```
 
Roll the per-change statuses into one grid keyed on what the reader can observe in the repo, so confirming what landed never requires chasing an artifact:
 
```
| Change | Files | Status to confirm |
|---|---|---|
| Exponential backoff on retries | `client/retry.py` | Merged if no fixed `sleep(0.2)` remains; else reproduce from §2. |
| Rename `--cache-ttl-secs` → `--cache-ttl` | `cli.py`, `docs/usage.md` | `--help` shows `--cache-ttl`; else reproduce from §2. |
| Remove dead `_legacy_key()` | `cache/keys.py` | Symbol absent repo-wide; else reproduce from §2. |
```
 
Keep the dead ends closed. A rejected-alternatives list pairs each idea with the evidence that killed it, so the next session does not spend a day rediscovering why it loses:
 
```
## Rejected alternatives (do not re-propose without new evidence)
- A dedicated cache-invalidation API so callers could purge keys directly —
  dropped because it exposes the internal key layout and every caller would
  couple to it; the TTL plus read-through refresh already cover the cases we
  have. Revisit only if a caller needs sub-TTL invalidation.
- Swapping `urllib3` for `httpx` to get async — rejected: it pulls an async
  stack into a synchronous host service for no current benefit, and the retry
  path would need a full rewrite. Revisit only if the host itself goes async.
```
 
A "deliberately left alone" entry earns its place by naming both the thing and the reason it was skipped, so it reads as a decision the reader can trust rather than an oversight they should fix:
 
```
- The dependency deprecation warnings in `client/pool.py` predate this work and
  are out of scope for a retry fix; a dependency-bump PR should handle them.
- A connection-pool rewrite was considered for the retry storms and rejected —
  backoff plus jitter solved the symptom at far lower risk. Revisit only if pool
  exhaustion recurs under backoff.
```
 
And when a prior handoff already covers the parts that did not move, the honest version of that section is a pointer, not a paraphrase:
 
```
## Architecture, data model, conventions
Unchanged this session — see the prior handoff (`handoff-2026-05.md`, §2–§4).
This document covers only the fixes and cleanups above.
```
