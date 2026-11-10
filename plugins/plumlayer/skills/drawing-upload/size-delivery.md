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
file of this delivery and each file of a manual step 8 filed beside it, or each file of a manual
on its own. Poll `set_text_status(projectId, fileId)` on
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
  never a reason to size it. Hold that `openCount`: every plan mode dispatch passes it as
  `Open Questions:`, so the plan's count of open Questions leaves the index check's out too. Where
  you no longer hold it, as on a resume after a crash, never count the open Questions again, since
  a count taken now holds the index check's: pass `Open Questions: not given`, and the plan reads
  that the count was not taken.

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
Open Questions: <in plan mode, the openCount you took right before step 9's recording call, or "not given" where you no longer hold it; otherwise "none">.
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
  handful; on a new set, how many of its sheets changed and are new, how many sheets of the old
  set it no longer prints, and how many could not be compared, with why.
- On an addendum, each package on its own, for the packages that hold any: its references to
  recheck and its open Questions on the sheets it reprints. Then how many references are
  unchanged, which you carry forward.
- On a new set, the references in all, off `in all`, how many read the same and carry forward, and
  how many go to the recheck, off `to recheck`. Then the packages on the `most to recheck` lines
  alone, at most five, the most first, each with its references to recheck and its open Questions
  on the sheets it reprints. Name no other package. Say the full list by package is in the plan,
  as a link whose words are `the plan` and whose target is the plan file's full path, and offer
  to read him the full list. The path and its ids never appear in the text he reads.
- On either, never add two packages' counts together: a Question filed under several trades
  counts in each of their packages.
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

For a new set: "The Permit set is a new set; its cover reads Permit Set. 240 of its 290 sheets
changed, 46 are new, and 4 could not be compared because their page size differs from the sheet
they replace; it no longer prints 12 sheets of the Conceptual set. The project holds 2,410
references: 96 read the same and carry forward, and 2,314 go to the recheck. The most to recheck
are Electrical, 402 references and 21 open Questions; HVAC, 355 and 14; Plumbing, 230 and 9;
Drywall, 198 and 7; and Doors, 120 and 5. The full list by package is in
[the plan](<the plan file's full path>), and I can read it to you. Plan: carry the 96 forward,
run a full scope pass over all 290 sheets, then recheck every scope item, retiring the rows the
new set shows removed. Approve it, change it, or stop it."
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
- He asks for the full list by package. Read it to him off the summary's `package |` lines, in
  their order, each package that holds any references to recheck in plain words as an addendum's
  are given: its name, its references to recheck (its `moved`, `gone` and `other` added
  together) and its open Questions on the sheets it reprints. Never the lines as written, a
  trade code, or an id. The plan stays as shown: append no `status:` line, and ask again whether
  he approves it, changes it, or stops it.

The plan is his decision, and every answer goes through this step: nothing is carried before
`status: approved` is on the plan file, and no scope pass reads the delivery before it either.
