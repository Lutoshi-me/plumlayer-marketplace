# Scope run: recheck the scope items on a new delivery

Read from `SKILL.md` stage 6 step 6, on a pass whose delivery precondition 7 found sized, with its
plan approved. Every stage this file names is a stage of `SKILL.md`, and every rule there applies
here unchanged: the non-negotiables, the dispatch and wait rules, the ledger's fixed shapes, the
check-in, and the words the user reads.

The carry put each reference that read the same onto the new page, and this pass cited the new
pages it read. What is left is each scope item's reference on a page the delivery replaced that
nothing cited again on the new page, which the comparison names open. The recheck reads those, one
sheet at a time, and for each row cites the item on the new page, updates the row naming what it
replaces, reads it as removed with the sheet that shows it, or names it as not found. Then it
retires the items each of whose open rows reads removed, and lists for the estimator every row it
could not find. After it, no scope item rests only on a replaced page unless it is listed for the user.

The plan the user approved said the recheck does this, so their approval is its go-ahead and the
ask the retires rest on: no further question is put to them before it starts. It runs on a new set and on
an addendum alike, after `phase: packages folded` and the go-ahead at the check-in that follows
it, and before stage 7. The ledger lines of the recheck carry window `r`.

## 1. The comparison is complete

`compare_delivery_status(projectId, deliveryId, kind: "scopeItem", limit: 1)`, reading `complete`.
Where it is false, a box was added on a replaced page since the sizing: call
`compare_delivery(projectId, deliveryId)` and poll `compare_delivery_status(projectId, deliveryId,
limit: 1)` until its `job.status` is `succeeded` or `failed`, waiting between polls rather than
polling back to back, then read `complete` again. A refusal, a failed job, or `complete` still
false stops the recheck: check in, say in one sentence that the comparison could not be finished
and why, and start nothing until it is settled.

## 2. Copy the rows

Send one fresh agent, whose whole job is this and which then ends, with the copy below, `Rows to:
rows-before`. Read its one line and nothing else. Where the Agent tool takes `run_in_background`,
send it `false`, as the template does: the call is then the wait. Where the call comes back with an
agent id instead, the agent's report arrives later as its own message: end the turn with one line
naming what is running, and take the report when it arrives.

```text
run_in_background: false
Copy the recheck's rows for project <projectId> to disk. This is your whole job. Do nothing else,
and end when it is done.
Rows to: <rows-before or rows-after>.

1. Call compare_delivery_status(projectId: "<projectId>", deliveryId: "<deliveryId>", kind: "scopeItem", limit: 200, offset: 0),
   then again at offset 200, 400, and so on, until the rows you have seen cover the response's own
   `referenceRows.total`. Put each response in `<run folder>/recheck/<the folder Rows to: names>/`,
   named `page-000.json`, `page-001.json`, and so on in call order.
2. Only where Rows to: reads rows-before: call list_files(projectId: "<projectId>") and put the
   response at `<run folder>/recheck/files.json`, then solicitation_list_packages(projectId:
   "<projectId>") and put it at `<run folder>/recheck/packages.json`.
3. Where a call's result came back as a path to a file on disk, copy that file into place with the
   Bash tool. Copy it. Never retype it: a model retyping a grounded read is an unrecorded rewrite
   of it. Where a call's result came back inline instead, write the whole response object to the
   same place yourself, as JSON, and say so in your returned line.
4. Return exactly one line: pages fetched, rows on disk, bytes, and copied or transcribed for each
   file. No account of what the rows are, no subjects, no sheet numbers.
```

## 3. Plan the recheck

```sh
python3 '<plugin root>/scripts/recheck.py' plan --run '<run folder>' \
  --delivery-plan '<plan file>' --deliveries '<project folder>/deliveries.json'
```

`<plan file>` is the delivery's plan file precondition 7 read. Read back only its bounds line: the
rows read and open, the units, one per sheet, the passes, and the ids kept. A refusal names one
thing wrong: a page of another delivery or rule version, a comparison not complete, a page missing,
or a file of no delivery on the list. Copy the rows again, as step 2 says, or take the delivery
list again as precondition 3 does, and plan again; never plan by hand. Where it reads `units 0`, no
row is open: go straight to step 6.

## 4. Run the sheet passes

As stage 4 runs a window's passes, with window `r` in every call: `lead_pass.py passes`, one runner
per pass that `start now:` names, your one `count_entries` call over the prefixes when it hands
back, which reads 0 under each since the recheck creates nothing, `lead_pass.py record '<run
folder>/ledger.md' r <pass id>`, and a check-in where `check-in due:` reads yes. Gather that
check-in from the passes the listing's `since the last check-in:` line names:

```sh
python3 '<plugin root>/scripts/lead_pass.py' checkin '<run folder>' r --passes <pass id>,<pass id>
```

Where that line reads `none`, no pass is recorded since the last check-in and none is due: make no
`checkin` call, since it refuses an empty list. Append `checkin: r <the last pass id that
line names> <go|pause>` when the user answers. The runner dispatch:

```text
subagent_type: plumlayer:scope-round-runner
run_in_background: false
Project: <projectId>. Window: r.
Pass: <"recheck-<pass id>" or "retire-<pass id>">.
Delivery: <deliveryId>, label <the delivery's label>. Plan file: <plan file>.
Run folder: <path>. Scripts: <path to the plugin's scripts directory>.
Run your pass as your definition says.
```

`recheck-<pass id>` runs a pass whose `reads for:` reads `the recheck`; `retire-<pass id>` one that
reads `retiring`. A mismatch or a sheet that stopped answering twice stops the recheck as stage 4
step 3 says.

<!-- user-facing -->
Between check-ins, tell the user at most one line per pass as it is recorded, naming the sheets in
plain words with the line under its `pass:` line: "I've rechecked the first architectural sheets:
14 rows cited again on the new sheets, 2 read as removed, 1 I could not find."
<!-- /user-facing -->

## 5. Retire what the delivery removed

When every sheet pass is finished, send the copy of step 2 again with `Rows to: rows-after`, then:

```sh
python3 '<plugin root>/scripts/recheck.py' retire --run '<run folder>' --delivery-plan '<plan file>'
```

Read back only its bounds line: the items to retire, the items theirs to settle, and the items kept on
a current page. It retires an item only where each of its open rows reads removed and none of its
rows now cites a current page; an item with a row not found is never retired, and goes on the
list for them. Each retire carries their approval's words as its basis, the reason naming the sheet
it was on and the delivery that dropped it, and the sheet that shows the removal as its source.
List the passes again and run the retire passes as step 4 runs the sheet passes, with
`retire-<pass id>`.

## 6. Close the recheck

When every pass is finished:

```sh
python3 '<plugin root>/scripts/recheck.py' report --run '<run folder>' --delivery-plan '<plan file>'
```

Its first line is `phase: recheck complete` with the recheck's figures: append it to the ledger as
printed, once, before you check in. Nothing else goes in the ledger. Where its last line names what
it did not print, run the command that line gives for the rest. What it prints is for you to read:
say it in the estimator's words, and never paste a line as it printed. Then check in. Take the
passes listing as stage 4 step 1 does, and gather the passes its `since the last check-in:` line
names, as the check-in section says:

```sh
python3 '<plugin root>/scripts/lead_pass.py' checkin '<run folder>' r --passes <pass id>,<pass id>
```

Where that line reads `none`, or step 3 read `units 0` and the recheck ran no pass, make no
`checkin` call, which refuses an empty list: the check-in is the one line below. Append `checkin: r
window <go|pause>` when the user answers.

<!-- user-facing -->
Where the recheck ran no pass, say in one line that no scope item on the sheets the delivery
replaced needed a recheck, then proceed, adjust, or pause.

Otherwise, at this check-in, say you rechecked every scope item on the sheets the delivery replaced, then, for
each package on its own, in a few plain sentences and never a table: the references carried
forward, the ones this pass cited again on the new sheets, the ones the recheck cited again, the
rows it changed, the rows it removed, and the rows left for them. Name each row removed by its item
and its sheet, and say they can have any of them put back. Name each row left for them with what you
searched, and say it is theirs to settle: keep it, move it, or have it removed. Say an item on two
packages counts in each. Where the carry's own count and the references carried forward differ,
say both. Then name the Questions the recheck put on the record by the trades they name, and what
comes next in one sentence: each package
reviewed on its own against what landed. Proceed, adjust, or pause.
<!-- /user-facing -->

## 7. Resume

On a start, the ledger's lines say where the recheck stands:

- `phase: packages folded` and a `checkin: 2 window go` after it, and no line of window `r`: the
  recheck starts at step 1.
- A `dispatch r` or `pass: r` line and no `phase: recheck complete`: run step 3's plan again with
  the same arguments, which keeps every id and marks the units verified; where
  `<run folder>/recheck/rows-after/` holds pages, run step 5's retire again after it. Then list the
  passes and start what the listing names. A pass already summed is not run again.
- `phase: recheck complete` and no `checkin: r window` line after it: the check-in was never
  answered. Run step 6's report again and show it.
- `checkin: r window go`: stage 7 step 1.
