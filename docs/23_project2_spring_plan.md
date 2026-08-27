# Project 2 — Spring 2027: the distributable

**2026-08-27.** A separate project from `docs/22`, with its own deliverable, its own risks and
its own administrative gates. Project 1 produces a measured backend; Project 2 turns it into
something a stranger can install.

**Entry condition:** Project 1's paper exists. This phase never starts at the cost of that.

---

## What it is

A **desktop RAG backend for an AI assistant**, distributed as something a person installs on
their own machine and points their client at.

Two access paths over one store on disk:

| Path | Needs running | Audience |
|---|---|---|
| **MCP over stdio** | nothing — the desktop client spawns the process | Claude Desktop and equivalents |
| **Local HTTP + browser extension** | a process while they browse | people who live in claude.ai in a browser |

Same JSONL, `.npy` and SQLite underneath. "Always-on server" is a requirement of the second path
only, not of the product.

---

## The framing, and it is deliberate

**Multiple partitioned workspaces on paired devices, for one person.**

Not multi-user. One account holder, one set of credentials, several isolated contexts — work
separate from personal, a sensitive domain separate from the general store, a project scoped so
it does not bleed into unrelated sessions.

This is not a euphemism. The live archive is already ten partitioned userspaces, two of them
gitignored as local-only precisely because they should not mix. Context isolation for a single
person is the thing that was actually built.

**The framing has to be carried through into the implementation**, or it does not hold:

| Not this | This |
|---|---|
| username | **workspace name** |
| grant access to a spouse | **pair another device** |
| partitioned users | **isolated contexts** |
| an invite flow | a device-pairing flow |

The auth code is for your laptop and your phone, not for another person.

### Why this framing and not the household one

It resolves four problems at once: no question about whose API key serves whom, no minors, no
IRB exposure from family members, and a stated purpose that matches every provider's terms
without argument.

A household deployment remains technically possible and is off-label. Running one on your own
machine for your own family is your call; it is not the product story and it does not appear in
the documentation or the onboarding.

---

## Architecture

**Partition by filesystem.** One folder per workspace, each with its own store, its own
credentials, its own service links. Nothing shared, so there is no policy engine and nothing to
police. This is what closes the multi-tenancy gap from the `docs/15` quality pass for this
deployment.

**One process per workspace, not one process routing by token.** If a single server picks the
folder from a request token, a bug in token validation crosses the partition and the isolation
was only ever code discipline. Separate process, separate port, separate working directory makes
the boundary real.

**Credentials live outside the synced folder**, or encrypted at rest. Each workspace holds its
own key, so secrets now exist in N places on one machine and every backup contains N sets. The
live archive already has form here — an open credential-shape gate and unrevoked tokens in
pushed history.

**Three ownership layers, so updates never merge:**

| Layer | Owner | On update |
|---|---|---|
| Client code | host | **always overwritten** |
| Config — workspace name, persona, preferences, prompts | user | **never touched** |
| User extensions — their own additions | user | **never touched** |

**And rollback rather than merge.** Snapshot, health-check, revert — the mechanism already
exists in the Jessica build. Snapshot *per layer* so a bad code push does not cost the user's
config and a bad user edit does not revert the host's fix. Keep a bounded number of snapshots.

**Know what the guarantee is.** Rollback triggers on "won't load," not on "loads and behaves
wrong." The user-facing promise is *it always starts*, not *it always works*.

**The folder is portable.** Copy it to another machine and the memory comes with it. No export,
no migration, no account. That is a genuine product property and it falls out of the design.

---

## What is already proven

This is not speculative architecture. Jessica's Assistant v3 runs it: server on a desktop,
Tailscale Funnel for reach, a browser extension as a thin client, an install page gating the
download on a pairing code, a PWA for phones, and self-update with device-side snapshot and
rollback.

The failures that build hit were **build-and-publish** problems — a zip writer emitting backslash
separators, a syntax check running in the wrong parse goal, a client-side scanner pretending to
parse JS, three interacting version gates. All fixed, all documented, and **fixing them once
fixes them for every N**. They do not recur per user.

The genuinely N-dependent risks are two, and neither is architectural:

- **Auth.** One pairing code for one trusted person is not N identities on a public URL. Tailscale
  Funnel is publicly reachable; a code checked once at provisioning is not authentication.
- **Support burden.** N people hitting problems you diagnose remotely without access to their
  machine.

---

## Deliverables

**Committed:**
- The MCP folder — store, server, manifest, install docs. Zero infrastructure, since the client
  spawns the process
- Backend choice exposed through the storage port: files by default, Neo4j as an advanced option
- A conformance test suite run against **both** adapters, or the one not developed against rots
- Portability demonstrated: the folder moved to a second machine and working

**Stretch:**
- The browser extension and local HTTP path
- Multi-workspace pairing across devices
- A household deployment as a personal demonstration, clearly off-label

---

## Administrative gates

**IRB, if there is a tester study.** A department email recruiting testers whose usage informs
the work is human-subjects research and needs review *before* recruitment. Weeks, not days. If
testers might set it up for family, **scope the study to adults explicitly** — minors in research
is a much heavier category requiring parental permission and child assent.

**Per-user API keys as the default.** Each tester brings their own. That keeps the host out of
the accountability path and keeps the design robust to a provider changing its terms.

**Chrome Web Store, only if it goes public.** For a controlled test group, sideload from your own
install page — you already have that flow, and it skips a review cycle that would scrutinise host
permissions on claude.ai. If it ever grows past a known group, the store's automatic updating
stops being friction and becomes the fix for the exact thing that broke repeatedly.

---

## Symposium

One board is what ISU provides — 36" × 48", one foamboard, clips and an easel, per the 2025
guidelines. **Verify the 2026 guidelines before designing.**

Three columns, left to right: *what the backend holds* → *whether it works* → *what you can
take*. Problem, evidence, artifact. The browsable wiki lives on a laptop rather than competing
for board space, and the QR codes go to a website (no install), the preprint, and the repo.
