# Drawing upload: size a new delivery before anything reads it

Read from `drawing-upload` step 9a, wherever a prior delivery or manual existed. Every step this
file names is a step of `drawing-upload`'s own `SKILL.md`, and every gate there applies here
unchanged.

On a project that already holds scope items or open Questions, a new delivery's scope pass is
sized before it starts, the way a new project gets its setup step: the estimator sees how much the
delivery changed and approves the pass. The measuring runs one level down, in the plugin's
`delivery-sizer` agent, so no page, comparison row or count of it lands in this conversation. The
agent's definition holds how the delivery is measured and what the plan names; none of it is
restated here. You hold only the summary it returns. Nothing is carried and nothing is read before
he approves the plan.

## 1. The text read

This runs on every path that reads this file, before anything else in it. The comparison and the
re-read of the open Questions both read the new paper's text, and neither finds a word on a page
nobody has read yet, so wait here for the read of each file the new paper came in: each drawing
file of this delivery, or each file of the manual. Poll `set_text_status(projectId, fileId)` on
each one every few seconds, in this conversation, the way `SKILL.md` step 5 polls recognition. The
loop ends on the server's answer only: `state` `succeeded` with `pagesNotRead` 0 is a file whose
text is read; `failed`, `stale`, or `succeeded` with `pagesNotRead` above 0 is a file that never
finished reading. A file whose `state` is `notStarted` has no read yet: call
`read_set_text(projectId, fileId)` once to start it and keep polling; where it still reads
`notStarted` after that, it never finished reading. Never wait on `pagesAwaitingImageRead` or
`imageReadState`: the read of the page images waits behind every other read, and the agents read a
page's image themselves when they judge that page. Note the `fileId` of each file that never
finished reading: step 9b names it on every unit's `Not read:` line. Tell the user:

<!-- user-facing -->
The text of <filename> was not fully read as of <time of the last poll>: <pagesNotRead> of
<pageCount> pages unread. I left alone each Question that needs a search of it, and I name
each one below.
<!-- /user-facing -->

## 2. Whether to size it

Size the delivery only where every one of these holds; otherwise go on to step 9b, and step 10's
handoff is the one it gives when this step does not size:

- it is a drawing delivery, and a prior delivery existed: a manual on its own is never sized;
- `list_drawing_deliveries` gives it `issue` `"set"` or `"addendum"`, and `sheetCount` above 0;
- the two counts you took right before step 9's `reconcile_set(projectId, record: true)` show a
  scope item (the `count` of `search(projectId, subjectPrefix: "scopeItem:", limit: 1)` above 0)
  or an open Question (`openCount` of `list_questions(projectId, limit: 0)` above 0). Those counts
  come from before the index check recorded its own Questions, which are this delivery's and
  never a reason to size it.

## 3. The plan

The plan file is `<upload folder>/plan.md`. It is local, never committed, never uploaded, and never
recorded: the scope pass that follows reads it, and you only append to it. Note the time with
`date -u +%Y-%m-%dT%H:%M:%SZ`, then dispatch the sizer in plan mode:

```text
subagent_type: plumlayer:delivery-sizer
run_in_background: false
Project: <projectId>. Mode: <plan or carry>.
Delivery: <deliveryId>, label <issue label>.
Plan file: <upload folder>/plan.md.
Change: <in plan mode, the estimator's words exactly as he wrote them; otherwise "none">.
Size the delivery as your definition says, write the plan file, then return your summary.
```

Where the Agent tool takes `run_in_background`, send it `false`, as the template does: the call is
then the wait. Where the call comes back with an agent id instead, the agent's report arrives later
as its own message: end the turn with one line naming what is running, and take the report when it
arrives. Wait by ending the turn and nothing else: no sleep, no shell loop, and no look at the plan
file while the agent runs. Where the summary did not arrive in the message, the plan file is the
summary: open it rather than dispatching again. Where the file is absent too, dispatch once more;
a second miss stops the sizing, as a `stopped:` line does below.

A client that ships this plugin's skills without its agents has no agent to dispatch. There, read
`agents/delivery-sizer.md` from the plugin's own folder and run its mode yourself in this
conversation, exactly as the definition says, writing the same plan file. Say once that you
measured the delivery in this conversation.

Read only the summary: its lines are the plan file's. Where its `stopped:` line reads anything but
`no`, there is no plan: tell the user why in one sentence of plain words, carry nothing, and go on
to step 9b; step 10 says no scope pass is planned until he asks for one.

## 4. Put the plan to him

Append the shown line to the plan file with a local command, such as
`printf 'status: shown %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> <plan file>`, then put the plan
to the user off the summary.

<!-- user-facing -->
Tell him, in a few plain sentences, never a table:

- The kind and why: what it is an addendum to, or that it is a new set, and who said so, from what.
  He picked it on upload ("you picked Addendum when you uploaded it"), he told you, or you read it
  off a sheet ("its cover reads Bulletin 3"). Never the sheet count.
- How much changed: on an addendum, the sheets it changes and adds, by number when there are a
  handful; on a new set, how many of its sheets changed and how many sheets of the old set it no longer prints.
- Each package on its own, for the packages that hold any: its references to recheck and its open
  Questions on the sheets it reprints. Never add two packages' counts together: a Question filed
  under several trades counts in each of their packages. Then how many references are unchanged,
  which you carry forward.
- The plan: carry those references forward first, then the pass, a re-read of the sheets named
  or a full scope pass, then the recheck. Say what the recheck does: each row is cited again on
  the new page, updated, or retired as removed by this delivery where its sheets show the work gone,
  and any row it cannot place is listed for him.
- The ask: approve it, change it, or stop it.

For a bulletin: "Bulletin 3 is an addendum to the Permit set; you picked Addendum when you uploaded
it. It changes 6 sheets and adds A-512. Doors has 29 references to recheck and 2 open Questions on those
sheets; Storefront has 12 references to recheck and 2 open Questions on them. 512 references are
unchanged. Plan: carry the 512 forward, re-read the 7 sheets, then recheck each reference that
did not read the same, retiring the rows these sheets show removed. Approve it, change it, or stop it."

For a new set: "The Permit set is a new set; its cover reads Permit Set. 280 of its 290 sheets
changed, and it no longer prints 12 sheets of the Conceptual set. 96 references are unchanged.
Plan: carry the 96 forward, run a full scope pass, then recheck every scope item, retiring the rows the new set shows removed. Approve it,
change it, or stop it."
<!-- /user-facing -->

## 5. His answer

Take his answer in his words, and note the time of it with `date -u +%Y-%m-%dT%H:%M:%SZ`.

- Approve. Append `status: approved <time> "<his words>"` to the plan file, then dispatch the
  sizer in carry mode with `Change: none`. Read its summary, the `carried:` line, and say the
  result in one line: "I carried 512 references forward onto Bulletin 3's sheets, each written as
  yours." Where it reads `stopped:`, say why in one sentence, and that nothing further was carried.
  Then step 9b. The carry runs before step 9b's re-read, so a place it adds on a Question is the
  one the re-read finds there.
- A change of kind ("it's a new set"). Record it as step 5b point 4 does:
  `update_drawing_delivery(projectId, deliveryId, issue, issueSource: { asked: "<his words>" },
  replaces: "<the kind held>")`, his words exactly as he wrote them. Then dispatch plan mode again
  with `Change: none`, and go back to step 4.
- Any other change ("re-read A-001 too", "leave the carry out"). Dispatch plan mode again with
  `Change: "<his words exactly>"`. The sizer applies it or names it as not applied, with why; go
  back to step 4, and name each change not applied, with its reason.
- Stop. Append `status: stopped <time> "<his words>"` to the plan file. Carry nothing, and plan no
  pass. Step 9b still runs: say in one line that you carried nothing and planned no pass, and that
  you are re-reading the open Questions against the new sheets. Step 10 says no scope pass is
  planned until he asks for one.

The plan is his decision, and every answer goes through this step: nothing is carried before
`status: approved` is on the plan file, and no scope pass reads the delivery before it either.
