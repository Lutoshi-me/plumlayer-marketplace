# Drawing upload: re-read the open Questions a delivery touches

Read from `drawing-upload` step 9b, only where a prior delivery or manual existed, once step 9a has
run. Every step this file names is a step of `drawing-upload`'s own `SKILL.md`, and every gate
there applies here unchanged.

The re-read runs one level down, in the plugin's `question-checker` agent, one fresh instance per
unit, so no Question's thread and no page lands in this conversation. The agent's definition holds
how a Question is read against the new paper and what it writes; none of it is restated here, and
you never read a Question's thread or a page yourself. It closes each Question the new paper
answers, with one line naming where, rewrites each one nobody has sent that the new paper changed,
replies once on each sent one it changed, and points each one it still applies to at the new pages,
taking the old pages off an unsent one. It raises none.

Where step 8 filed a project manual in the same upload as a drawing delivery, one re-read reads
both: every unit's `Delivery:` line names the delivery and the `fileId` of each file step 8 filed.
The list unit then puts the manual's sections on `sheets.txt` beside the delivery's sheets, so a
Question citing only a section of the new manual is read against it, and each Question is read
once, in the one unit its line falls in.

Each re-read has a folder of its own. When step 9b starts, note the time with
`date -u +%Y%m%dT%H%M%SZ` and make `<upload folder>/reread-<that time>/reports/` with
`mkdir -p`. That re-read folder holds this re-read's `sheets.txt`, `questions.txt` and reports, and
every command below reads it and nothing else, so a re-read of the same delivery run earlier never
adds to these counts. The sheet checker's files stay where "Who reads the pages" puts them.

1. **The count before.** Call `list_questions(projectId, limit: 0)` and note `openCount` and
   `closedCount`.
2. **The text read.** Step 9a waited for the read of each file the new paper came in, as
   `size-delivery.md` step 1 says, and told the user of each file that never finished reading.
   Take that result: name the `fileId` of each such file on every unit's `Not read:` line, or
   `none` where every file finished reading.
3. **The list unit.** Dispatch one unit with `Mode: list`. It writes `sheets.txt` and
   `questions.txt` in the re-read folder (Audience: agent), which you count and never read. Where
   its report says it wrote 0 lines, no open Question can be in scope: say so in the closing
   report, with its `no sheet number:` line where that reads yes, and go to step 10.
4. **The questions units.** Count the lines with
   `awk 'END{print NR}' <re-read folder>/questions.txt`, which counts a last line with no newline
   too. Where that count is not the list report's `lines written`, stop the re-read there and name
   both counts in the closing report. Otherwise dispatch one unit with `Mode: questions` per six
   lines: lines 1-6, then 7-12, and so on, the last unit taking what is left.
5. **The count after.** Once every questions unit has reported, call `list_questions(projectId,
   limit: 0)` again. Its `closedCount` is the count before plus the `closed` figures the questions
   units reported. Where they differ, name both counts in the closing report.
6. **The closing report.** Once every questions unit has reported, read it off the reports with a
   local command, never from memory:
   `grep -h '^closed |' <re-read folder>/reports/questions-*.md` for every close, with its title or
   RFI number and its note; `grep -h '^rewritten |' <re-read folder>/reports/questions-*.md` for
   every rewrite, by its new title; the counts with
   `awk '/^closed [0-9]/ {c+=$2; w+=$4; r+=$6; u+=$8; p+=$11; t+=$14} /^read [0-9]/ {s+=$5} END {print "in scope", s, "closed", c, "rewritten", w, "replied", r, "unchanged", u, "places added", p, "taken off", t}' <re-read folder>/reports/questions-*.md`;
   and `grep -hE '^(taken off|no room|no box|not found|pages not read|new disagreement|not returned) \|' <re-read folder>/reports/questions-*.md`
   for the rest.

A dispatch carries pointers and nothing else. Dispatch the list unit alone and take its report
before any other. Page units go one at a time, and questions units up to four at once: send up to
four Agent calls in one message, in line order, and when they have all reported send the next four.
Two questions units never write on one Question, since the list unit puts each Question on one line
of the file, and they only read the pages. Before each message that dispatches, note the time with
`date -u +%Y-%m-%dT%H:%M:%SZ`. `Asked before:` is the time you noted before step 9's
`reconcile_set(projectId, record: true)`. Where the Agent tool takes `run_in_background`, send it
`false`, as the template does. Where the call comes back with an agent id instead, the agent's
report arrives later as its own message: end the turn with one line naming what is running, and
take the report when it arrives. There, the line names every unit running, and as each report
arrives you dispatch the next unit, keeping up to four running. Where a unit's report did not
arrive, its report file in the re-read folder is the report; where the file is absent too, send
that unit once more with `Since:` set to the time you noted before its first dispatch. A second
miss of any unit stops the re-read there: dispatch no new unit, let the units still running finish
and take their reports, and name in the closing report each unit's lines and which of them missed
twice.

```text
subagent_type: plumlayer:question-checker
run_in_background: false
Project: <projectId>. Mode: <list or questions>.
Delivery: <deliveryId>, label <issue label>, issue <set, addendum, or none>, manual <the fileId of each manual file step 8 filed in this upload, or "none">; or "manual", with the fileId of each manual file.
Asked before: <the time you noted before step 9's recording call>.
Questions file: <for questions, <re-read folder>/questions.txt lines <a>-<b>; otherwise "none">.
Since: <for a unit sent again, the time its first dispatch was sent; otherwise "none">.
Not read: <each fileId whose text never finished reading at step 9a's text read; otherwise "none">.
Re-read folder: <upload folder>/reread-<time>/. Report: <re-read folder>/reports/questions-<list, or <a>-<b>>.md.
Check your unit as your definition says, write your report to that path, then return it.
```

A client that ships this plugin's skills without its agents has no agent to dispatch. There, read
`agents/question-checker.md` from the plugin's own folder and run each unit yourself in this
conversation, one after another, exactly as the definition says, writing the same report file. Say
once in the closing report that you read the Questions in this conversation.

<!-- user-facing -->
Report: how many open Questions I read against the new set, the new addendum or the new manual,
naming the manual that came in with the new set or addendum where one did, and
how many of them cite, in the ask or a reply, a sheet or section the new paper prints or a sheet
the new set ended. Then the Questions I closed because the new set answers them, each by its title,
or by its RFI number ("RFI 22") once it holds one, with the line naming where, and say: these are
the Questions I closed because the new set answers them (the new addendum, or the new manual, as it
is); review them first and reopen any that is wrong. Then the ones I reworded to read as of the new
paper, by their new titles, since nobody had sent them. Then how many I replied to saying what
changed, how many I left as they were because I found their point unchanged, how many places I
added, and which old pages I took off because the new paper printed them again or no longer prints
them, each by its Question and sheet. Then any I added no place to because it holds ten already, any
I pointed at a sheet with no box because I found no words for the callout on its page, any citing a
sheet that is no longer in the new set, and any I left alone because the text of the new pages they
need never finished
reading, naming that file. Then each disagreement I found on another point, by sheet, for you to
decide whether to ask about it.
<!-- /user-facing -->
