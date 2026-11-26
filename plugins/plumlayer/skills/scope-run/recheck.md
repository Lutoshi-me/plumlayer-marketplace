# Scope run: recheck the scope items on a new delivery

Read from `SKILL.md` stage 6 step 6, on a pass whose delivery precondition 7 found sized, with its
plan approved. Every stage this file names is a stage of `SKILL.md`, and every rule there applies
here unchanged: the non-negotiables, the dispatch and wait rules, the ledger's fixed shapes, the
stops, and the words the user reads.

The carry put each reference that read the same onto the new page, and this pass cited the new
pages it read. What is left is each scope item's reference on a page the delivery replaced that
nothing cited again on the new page, which the comparison names open. The recheck reads those, one
sheet at a time, and for each row cites the item on the new page, updates the row naming what it
replaces, reads it as removed with the sheet that shows it, or names it as not found. Then it
retires the items each of whose open rows reads removed, and lists for the estimator every row it
could not find. Where the delivery came with its project manual, the comparison also lists each
scope item citing a section of an earlier manual, and the recheck reads those one section at a time
against the new manual the same way. After it, no scope item rests only on a replaced page or an
earlier manual unless it is listed for the user.

The plan the user approved said the recheck does this, so their approval is its go-ahead and the
ask the retires rest on: no further question is put to them before it starts. It runs on a new set and on
an addendum alike, right after `phase: packages folded`, and before stage 7. What it did goes to
the closing report. The ledger lines of the recheck carry window `r`.

## 1. The comparison is complete

`compare_delivery_status(projectId, deliveryId, kind: "scopeItem", limit: 1)`, reading `complete`.
Where it is false, a box was added on a replaced page since the sizing: call
`compare_delivery(projectId, deliveryId)` and poll `compare_delivery_status(projectId, deliveryId,
limit: 1)` until its `job.status` is `succeeded` or `failed`, with the wait mode between polls,
bounded as the skill's stops section says, then read `complete` again. A refusal, a failed job, or `complete` still
false stops the run, as the skill's stops section says for a window that cannot be planned: say
in one sentence that the comparison could not be finished and why.

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
   then again at offset 200, 400, and so on, until the rows you have seen cover both the response's
   own `referenceRows.total` and its `manualRows.total`. Put each response in `<run folder>/recheck/<the folder Rows to: names>/`,
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
5. Where a call cannot be made, because Claude Code refused it, your sign-in failed, or Plumlayer
   did not answer after one try more, stop and return exactly one line instead:
   `blocked: <tool> <sign-in, refused by the client or server>`.
```

## 3. Plan the recheck

```sh
python3 '<plugin root>/scripts/recheck.py' plan --run '<run folder>' \
  --delivery-plan '<plan file>' --deliveries '<project folder>/deliveries.json'
```

`<plan file>` is the delivery's plan file precondition 7 read. Read back only its bounds line: the
rows read and open, the units, one per sheet, the passes, and the ids kept. A refusal names one
thing wrong: a page of another delivery or rule version, a comparison not complete, a page missing,
a manual row naming no section, or a drawing file of no delivery on the list. Copy the rows again, as step 2 says, or take the delivery
list again as precondition 3 does, and plan again; never plan by hand. A refusal that comes back
after the rows are copied again is a stop, as step 1's is. Where it reads `units 0`, no
row is open: go straight to step 6.

## 4. Run the sheet passes

As stage 4 runs a window's passes, with window `r` in every call: `lead_pass.py passes`, one runner
per pass that `start now:` names, your one `count_entries` call over the prefixes when it hands
back, which reads 0 under each since the recheck creates nothing, and `lead_pass.py record '<run
folder>/ledger.md' r <pass id>`. The runner dispatch:

```text
subagent_type: plumlayer:scope-round-runner
run_in_background: false
Project: <projectId>. Window: r.
Pass: <"recheck-<pass id>" or "retire-<pass id>">.
Delivery: <deliveryId>, label <the delivery's label>. Plan file: <plan file>.
Run folder: <path>. Scripts: <path to the plugin's scripts directory>.
Read again: <"<unit id> read <n>", only after the stop below, the unit the user said to read again and one more than the reads its unread note names, or none>.
Run your pass as your definition says.
```

`recheck-<pass id>` runs a pass whose `reads for:` reads `the recheck`; `retire-<pass id>` one that
reads `retiring`.

Here, unlike the windows, a unit whose two reads both failed their check is never skipped: the
retires rest on every sheet's outcome, so its pass stays unfinished, its hand-back names it on
`unverified:`, and the record script refuses the pass. That stops the run. Write the closing report
so far as the skill's stops section says, and say:

<!-- user-facing -->
"Rechecking <sheet> failed its check <n> times, so the recheck cannot tell which items the new
drawings removed, and I stopped after <what finished>. Look at its items on <sheet>, then tell me
to read it once more."
<!-- /user-facing -->

`<n>` is the reads its unread note names, three or more where a read granted after this stop
failed too, which stops the run the same way.

On that go-ahead, dispatch the pass again with `Read again: <unit id> read <n>`, `<n>` one more than
the reads its unread note names; its runner reads the unit once more and then the ones after it.

<!-- user-facing -->
As each pass is recorded, tell the user one line naming the sheets in plain words with the line
under its `pass:` line: "I've rechecked the first architectural sheets: 14 rows cited again on the
new sheets, 2 read as removed, 1 I could not find."
<!-- /user-facing -->

## 5. Retire what the delivery removed

When every sheet pass is finished, send the copy of step 2 again with `Rows to: rows-after`, then:

```sh
python3 '<plugin root>/scripts/recheck.py' retire --run '<run folder>' --delivery-plan '<plan file>'
```

Read back only its bounds line: the items to retire, the items theirs to settle, and the items kept on
a current page. It retires an item only where each of its open rows reads removed and none of its
rows now cites a current page: none reads `open: false`, and none reads `itemOnCurrentPage: true`,
which says the item holds a source other than one index_citations wrote on some page of the
current set, such as a sheet its work moved to. Those items count with the items kept on a current
page. Where rows-after holds rows the comparison wrote before it gave `itemOnCurrentPage`, the
bounds line counts them, and for those rows only `open: false` keeps an item off the retire. An
item with a row not found is never retired, and goes on the list for them. Each retire carries their approval's words as its basis, the reason naming the sheet
it was on and the delivery that dropped it, and the sheet that shows the removal as its source.
List the passes again and run the retire passes as step 4 runs the sheet passes, with
`retire-<pass id>`.

## 6. Close the recheck

When every pass is finished:

```sh
python3 '<plugin root>/scripts/recheck.py' report --run '<run folder>' --delivery-plan '<plan file>'
```

Its first line is `phase: recheck complete` with the recheck's figures: append it to the ledger as
printed, once, through the ledger script as every line goes on. Nothing else goes in the ledger,
and you read nothing more of what it prints: the closing report takes the recheck's figures by
package off the same script. Then dispatch the package folder in mode `recheck` where the fold
deleted a package, as the skill's stage 6 step 5 says, and go to stage 7.

<!-- user-facing -->
Where the recheck ran no pass, say in one line that no scope item on the sheets the delivery
replaced needed a recheck.
<!-- /user-facing -->

## 7. Resume

On a start, the ledger's lines say where the recheck stands:

- `phase: packages folded` and no line of window `r`: the recheck starts at step 1.
- A `dispatch r` or `pass: r` line and no `phase: recheck complete`: run step 3's plan again with
  the same arguments, which keeps every id and marks the units verified; where
  `<run folder>/recheck/rows-after/` holds pages, run step 5's retire again after it. Then list the
  passes and start what the listing names. A pass already summed is not run again, and a pass
  holding a unit whose two reads both failed brings back step 4's stop.
- `phase: recheck complete`: stage 7 step 1, after the folder's recheck mode where step 6 says.
