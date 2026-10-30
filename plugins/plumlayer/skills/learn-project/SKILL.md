---
name: learn-project
description: >
  A cheap orientation pass, run by the plugin's orientation agent, over an uploaded set: reads
  project fields and sheets, takes a few bounded renders (cover, index, key plans), records cited
  facts, writes the project description, and drafts and creates the baseline trade-package split
  off the spec table of contents. Trigger on "learn the project", "orient on this set",
  "orientation pass", "/learn-project". Drives list_projects and the orientation agent, which
  writes with record_batch, update_project and solicitation_create_package. Does not upload
  drawings or run scope-run.
---

# Learn project: the cheap orientation pass (stage 1)

The first stage of a scope run. Before anything is read deep, one cheap pass over what's already
recognized builds the project's context: what it is, its systems, its scope areas, the shape of
the set, and what's missing, and it drafts and creates the baseline trade-package split off the
spec table of contents. Every later pass in the scope run gets this context instead of orienting
from scratch. It does not upload a drawing delivery (`drawing-upload`) or run any later stage of
the scope run (`scope-run`).

## Running one level down

The pass runs in the plugin's `orientation` agent, never in the session that starts this skill.
That agent's renders, spec page reads, package lists and package creates would otherwise stay in
the session the user talks to for the rest of it, and on a set of a few hundred sheets with its
manual they once filled most of that session. A user typing /learn-project, `project-setup`, and
`scope-run`'s orientation stage all start it the same way:

1. Know the project. `project-setup` and `scope-run` hand you its `projectId`. When a user typed
   /learn-project, call `list_projects` and confirm with the user which project record this
   orientation pass is for. If there is no project yet, hand off to `project-setup` first, the same
   way `drawing-upload` step 1 does, and dispatch nothing.
2. Dispatch the orientation agent with the dispatch below. Where the Agent tool takes
   `run_in_background`, as in a headless session, send it `false`, as the dispatch does: the call
   is then the wait, because a headless session stops a background agent after ten idle minutes.
   Where the call comes back with an agent id instead, the agent's report arrives later as its own
   message: end the turn with one line naming what is running, and take the report when it
   arrives. Here its report is the summary. Wait by ending the turn and nothing else: no sleep, no
   shell loop, and no look at the summary file while the agent runs.
3. Read back only its summary. Never relay the agent's own wording to the user and never open the
   packet to retell it: what orientation learned is on the record, and the summary says where.
   Where the summary did not arrive in the message, its summary file is the summary: open that
   file rather than dispatching again.

The project folder is `<runs root>/<projectId>/`, where `<runs root>` is `~/.plumlayer/runs` with
the home directory written out: the folder `scope-run` uses, named for the project id and never for
the project's name, so two projects of one name never write over each other's packet or summary.

```text
subagent_type: plumlayer:orientation
run_in_background: false
Project: <projectId>. Project folder: <runs root>/<projectId>/.
Summary: <project folder>/learn-project-summary.md.
Orient on this project as your definition says, write your summary to that path, then return it.
```

The orientation steps, 1 to 11, with their gates, are the agent's definition,
`agents/orientation.md` in the plugin's own folder, beside its `skills/` folder, and other files
cite them by those numbers: step 8 is the package split, and step 8 sub-step 6 places a section on
a package. You never run a render, a page read, or a package call of those steps yourself. A client
that ships this plugin's skills without its agents has no agent to dispatch: there, read that
definition and run its steps 1 to 11 in this conversation, exactly as it says, and at step 11 tell
the user what the block below says rather than returning a summary.

The summary comes back in the shape the definition's "Your summary" section gives, counts and
named items only (Audience: agent; you word it for the user). Its first line is the counts, where
`questions` is the Questions raised and `packages drafted` the packages created this run:

```text
sheets seen <n>   index findings <n>   spec sections <n>   packages drafted <n>   questions <n>
```

<!-- user-facing -->
Where a user typed /learn-project, tell them, in plain terms, off that summary:
- **What was read**, the project's identity, which of the facts project setup filled were present,
  the disciplines covered, whether the project manual's table of contents was read, and any render
  or page read that failed.
- **What was learned**, by kind: systems, scope areas, set shape, hazards. Name any value already
  on the project that you left as it stands, and any you replaced, with who wrote it.
- **What was filled on Overview** from the cover sheet and title blocks, with the sheet; each firm
  added to the Network or given a type; and anything a sheet states that you left off, and why.
- **What the index check found**, or that it hasn't run yet for this set, never silent on which.
- **What was recorded**, how many facts, and any Question raised for a disagreement between
  documents. What was recorded is the project's working context now, carrying your name and its
  citations; anyone who changes a value later replaces it.
- **The package split**, in these words: "I split the job into N packages; here they are. Change
  any of them on the site or tell me and I will redo it." Then name each package created, off the
  summary's `packages created:` line, then the packages already on the project, by name,
  each package a supplier furnishes with the package that installs its items, each default used
  with the package that follows it and that the user can change any of them in chat, any package
  with no catalog trade and so not created, how many of the manual's sections outside Divisions 00
  and 01 are placed on a package out of how many the manual has (or that the count is incomplete),
  each section placed from its title alone by its number, each section whose item the catalog has
  no trade for with the package it went on, and each section left on no package with what stopped
  its placing. No approval is collected.
- **The structure**, the sheet that grounded the system and the sheet that grounded the floor
  counts when it was filled, or that it was left blank and which half the set does not state.
- **The description**, whether one was written or a person's was already in place and left alone.
- **Where the packet landed**, the full path.
- **What a person should look at**, the facts recorded, visible on plumlayer.com with the page each
  one was read from, and any Question raised for a disagreement between documents.

Close by saying orientation is done and everything it made is on the project record.
<!-- /user-facing -->
