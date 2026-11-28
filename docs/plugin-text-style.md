# Plugin text style

The authoring contract for every piece of text shipped with the Plumlayer plugin. It exists because
the shipped text drifted for months with nothing checking it: stale skill lists, a flagship feature
described as broken, internal ticket numbers, and real client project names all reached the
distributed tree. The mechanical parts of this contract are enforced by `harness/static_checks.py`,
so a violation fails the release rather than waiting for someone to notice.

## 1. Two audiences, one rule each

Plugin text serves two readers, and confusing them is the most expensive mistake available here.

**Agent-facing text** is the instructional body of a skill, and the whole body of an agent
definition under `agents/`, which a dispatched agent reads as its system prompt. The agent reads it
to do the work.
Machinery vocabulary belongs here and is load-bearing: `entry`, `predicate`, `supersede`, real
verb names, real field names. Do not "de-jargon" this text. Precision here is
what makes the product reliable.

**User-facing text** is anything a human reads: the README, the manifest descriptions, the skill
frontmatter descriptions, and, inside a skill body, every narration template, example sentence, and
closing report format. Machinery vocabulary is banned here. A shipped script under `scripts/` is
agent-facing in its comments and user-facing in what it prints, and since a run repeats a script's
stdout and error lines back to the person watching, the whole file is held to the user-facing bar.

The boundary that keeps getting missed: **a report template is user-facing text.** A skill whose
instructions say pass and open items, and whose closing report then says "deposits" and "residue",
is running two vocabularies where section 3 requires one. Check every report and narration block
against section 3.

### Declaring the audience

Audience is declared, never inferred. The register rule above is unenforceable while the boundary
it governs is unmarked, so every skill marks it explicitly:

- **User-facing spans are wrapped in paired markers**, each on its own line:
  `<!-- user-facing -->` before the span and `<!-- /user-facing -->` after it. This covers every
  report template, narration block, check-in format, closing report, and any question or
  statement the skill mandates the agent put to the user. Unmarked skill body text is agent-facing
  by default. Frontmatter descriptions, the README, and manifest descriptions are user-facing by
  category and carry no per-instance marker.
- **Every run artifact a skill mandates writing carries an audience clause** beginning with the
  exact token `Audience:`, naming one of user, agent, or machine. An agent-audience artifact says
  so precisely so a later reader never has to guess whether machinery vocabulary is acceptable in
  it (it is). An agent-audience artifact that feeds user-facing output, a ledger feeding a cost
  line in a closing report or a packet whose path is handed to the user, says that too: whatever
  crosses from it into user-facing text becomes user-facing at the crossing and is translated
  there.
- **The markers are mechanical on purpose.** The static check finds user-facing spans by these
  exact tokens; a span the markers miss is ungoverned. When in doubt, over-mark: the expensive
  failure is marking too little.

### Question text on the record

A Question an agent raises with `ask_question` is not shipped plugin text, but the user reads it on
the site exactly like any other user-facing string, so it answers to the same rules as everything
else in this contract. Question text is plain estimator words: no em dashes, no internal names (a
predicate, an internal step, a field, or another Question's own internal name), no bold for
emphasis, one vocabulary the same as section 3 requires. Its first sentence is the ask, written as
the answer to confirm where the set points to one ("Please confirm X and not Y") or as the value to
provide where it does not, and it asks one thing; finds share a Question only where one answer
settles them all. It gives only the values that conflict, each in plain words and never as the set's words copied out in quotation marks, one short line per source where three or
more disagree, and leaves to its citations what they show, with no recital of a section's contents;
it names each item once, in the words the cited sheet uses, with no clause re-describing what that
sheet shows or where the item is; a sentence names at most three tags, only the ones with the
problem; a parenthesis holds a short qualifier, never a sentence; every sheet it names is one of its
citations, boxed on the entry it names there, and cited as the whole sheet only where the point is
that the sheet lacks it or no line of the page's read carries the entry; a sheet the set lacks is
cited at the spot that names it; and it carries no colon without the list it announces, no sentence
repeating the title, and no sentence on why we need the answer. What
makes a Question worth raising, and its title, its citations and how it reads to the design team, is
the standard the `ask_question` verb's own description states, where every agent reads it at the
verb; this section keeps only the plain-words rule, and `learn-project` keeps one worked example.
Every skill or agent file that tells an agent to raise a Question carries the plain-words phrase and
points at the verb's standard instead of restating either.

### Record text never carries another entry's name

Any field a person or a bidder reads on the record, a scope item's name, category, description,
notesExternal, or notesInternal, a bid response or additional item's note or description, answers
to the same rule as Question text: plain estimator words, no internal id, no hand-written
supersede or date tag standing in for the trail. Where one entry replaces another, that is
`supersedesId` on the write, or `retire_scope_item` plus a fresh create for a scope item, never a
tag typed into the text itself. Where one entry needs to point at another for the reader, name it
the way an estimator would, "the wall tile line above," never by its subject id. Every skill or
agent file that writes one of these fields points at this rule instead of restating it. The record
refuses text that carries a record id or such a tag, so a write that does this fails rather than
lands. A scope item's note to bidders is the estimator's own, in his own words, and no agent of
the scope run writes it. An agent of the scope run writes the internal note only by the reader's
NOTES rule: it rests on this job's documents, tells the estimator what the row does not, and is
one he would act on. A person's own agent writes either note only when the person asks.

## 2. The frontmatter description contract

The description does two jobs at once. A human reads it in a listing; the model reads it to decide
whether to invoke the skill. It must serve both.

- **Style:** folded YAML (`description: >`) for every skill, no exceptions, so the ten look alike.
- **Length:** target 450 characters, hard ceiling 600. The harness fails above 600.
- **Shape**, in this order:
  1. What the skill does, in one plain sentence.
  2. When to trigger it: quoted natural phrases, then the slash command.
  3. Which real tools it drives, named directly in a technical clause.
  4. What it does *not* do, pointing at sibling skills by their real current names.
- **Never** in a description: doctrine prose (in particular "the agent reads and judges;
  deterministic tooling grounds; nothing enters untraced"), trust-model vocabulary, the phrase
  "verb surface", deprecated tool aliases, or migration history.

## 3. One vocabulary, both sides of the boundary

The project record's concepts have settled names, and those names are used identically in what the
user reads and in the instructions to the agent. One concept, one name. There is no translation
step, because there is nothing left to translate: a skill that names a round a round and an open
item an open item produces the right register in its output without being told to.

The one carve-out: a raw verb, parameter, or field name is an identifier, not a concept. It stays
what it is, and it appears in a code span, never standing in for a sentence the user reads.

## 4. Banned from all shipped text

Each of these is a harness check.

- **Real client or project names, addresses, or quoted client document text.** Examples are
  invented, always. This is confidentiality, not style: the plugin is distributed.
- **Internal ticket IDs** (`PLU-123`). A stranger cannot resolve them and they read as unfinished
  engineering notes.
- **Internal vault filenames** (`scope-package-architecture.md`, `agent-driven-ingestion.md`,
  `drawing-set-intake-design.md`). These live in a repo the user does not have. Either state the
  rule inline or drop the citation.
- **`MOSOT`**, retired as user-facing vocabulary.
- **Em dashes and middle dots** (`—`, `·`) in prose, per house style. This applies to skill
  instruction bodies too, not only to text a user reads: a model mirrors the register of its
  instructions, so em-dash-saturated instructions push the agent toward the exact writing tic the
  house style bans (Luke's ruling, 2026-08-15).

  **Exemption: inside fenced code blocks and inline code spans, these characters are data, not
  prose, and they stay.** The `evidence.source` format is literally `A-746 — millwork elevation`,
  and the entry atom is written `subject — predicate — value`. A blanket find-and-replace across
  those would silently change a documented data format the agent has to emit correctly. A sweep
  that touches a backtick or a code fence has overreached. Everything else in this section stays
  whole-file: a client name or a ticket ID is banned inside a code block just as much as outside it.
- **Bold for emphasis** on ordinary words, and **Title-Case labels**. Bold is for genuine labels
  only.

## 5. Formatting

- A skill's branch that most runs never take may live in a file beside its `SKILL.md`, which the
  skill names at the branch point and the agent reads by path only when the branch applies, so
  the skill's own load stays small. Such a file is shipped text like `SKILL.md`, and every check
  below that reads skill text reads it too.

- Headings are sentence case: `## 3. Read the open pages`, not `## 3 · Read The Open Pages` and
  not `## Step 3 — Read the open pages`.
- Numbered stages start at 1 and use `N.` as the separator.
- Use `###` for genuine sub-stages; do not substitute a bolded lead-in paragraph.
- Fenced code blocks carry a language tag.
- State a rule once per file. If it needs restating, the first statement was in the wrong place.

## 6. What the harness enforces

`python harness/run.py static` checks, and fails on:

1. The CLI validator passes: `claude plugin validate --strict` exits 0 over the plugin, with
   warnings counted as errors, and where `claude` is not on the path the check reports a skip
   rather than a pass. This cannot judge what the validator does not read: it validates the
   manifest, and it passed while a shipped agent's frontmatter was invalid YAML, which is why
   checks 3 and 4 read the frontmatter themselves.
2. The version quadruple in lockstep: both `marketplace.json` version fields, the Claude
   `plugin.json`, and the Codex `.codex-plugin/plugin.json`.
3. The shipped skill set matches the expected set exactly, in both directions, and every skill's
   frontmatter parses as YAML and carries a non-empty `name` and `description`, with no name
   used twice.
4. The shipped agent set under `agents/` matches the expected set exactly, in both directions.
   Every agent definition's frontmatter parses as YAML and carries a `name` and a `description`,
   and none declares `hooks`, `mcpServers`, or `permissionMode`, the three fields the runtime
   ignores for plugin-shipped agents. Declaring one is not a load error, so it would read as
   configured behavior and silently not be. This cannot judge whether a description dispatches
   its agent at the right moment, only that the fields are there and the runtime reads them.
5. Every frontmatter description is non-empty, folded style, and at most 600 characters.
6. No banned string in any shipped text: client-name denylist, `PLU-\d+`, internal vault filenames,
   `MOSOT`, em dash, middle dot.
7. Retired vocabulary does not creep back in. This is a regression guard, not a live enforcement
   layer: it checks a fixed, curated list of names that a past sweep already retired (most recently
   the D6 rewrite, commit `8096333`), not "is this word acceptable" in general. Three scopes:
   - A **whole-file** list (e.g. `residue`, `roster`, `checkpoint`, `mint`, `enrich`, `operator` as
     the name for the person, `deposit`, `proposed`, `trade-packages`, the authorship stamps
     `agent-stated` and `machine-read`, `trust class`, `working truth`) must not appear anywhere in a
     shipped skill, an agent definition, the README, or a manifest. A literal, current identifier that happens to share
     the retired word — the `operator.json` filename, the JSON key
     `"operator"` — is exempt; it is a real name, not the retired concept.
   - A list matched over each whole file with whitespace collapsed, since its phrases wrap across
     lines: the shape an exclusion had before it was a row of its own, a `"counterparty"` key in a
     role's value, the script's old `exclusion on:` line, an instruction to write an exclusion
     record or role onto the carrying row or a row of another trade, an instruction that has an
     agent of the run write `notesInternal` outside the readers' NOTES rule or `notesExternal` at
     all, an exclusion row's
     description saying who carries the work (`description: By`), and an exclusion row's
     `repeatsScopeItem` naming the row that carries the work, which has another name. A sentence telling the agent
     to write no `counterparty` passes, since it names the field in a code span and gives it no
     value, and so does a sentence that forbids the old write or puts the role on the exclusion
     row itself, and one that forbids a row note ("You never write `notesExternal`"). A row note
     sentence passes only where the forbidding word governs the write ("never write", "writes
     no", "is not written", "no agent writes"), never for a "no" elsewhere in the sentence, and an
     instruction is matched in any case, so "Write the other trade in `notesInternal`" is refused.
     A write of `notesInternal` also passes where the words "only by the NOTES rule" follow the
     field at once ("You write `notesInternal` only by the NOTES rule below"); the rule named
     elsewhere in the sentence excuses nothing, and it never excuses a write of `notesExternal`.
     The check runs each of the three newest phrases over an old sentence it refuses and a new one
     it passes.
   - A **scoped** list (e.g. `supersede`/`supersession`, `fan-out`, `idempotency`, `census`,
     `grain`) is legitimate agent-facing machinery vocabulary everywhere else in a
     skill, and is banned only inside a `<!-- user-facing -->` span or an `Audience: user` artifact
     clause — the places the file itself has already declared the text user-facing.
   Every shipped file takes the same scan. There is no lenient population and no exemption list:
   a shipped file is the plugin's own prose, in the plugin's own voice, and a hit in one is drift.
8. Bold used for emphasis: a mid-sentence bold span made only of words on a short denylist of
   ordinary words (`not`, `never`, `only`, `must`, `no`, `exactly`, `each`, `both`, `before`,
   `once`, and similar), one word (`**not**`) or several (`**must never**`). Position decides, not
   a colon: a span that is the first thing on its line, after optional indentation, an optional
   blockquote `>` and an optional list marker (`-`, `*`, `N.`), or that sits in a table row written
   with a leading pipe, is a label and passes whatever its words (`- **No**: the bidder excluded it.`), while
   `It does **not**:` fails. A span with any word off the list passes anywhere, which keeps the
   check narrower than "any bold not followed by a colon": that broader rule flags the bulk of this
   codebase's own legitimate bolded-lead-in and first-use-term conventions, not just emphasis.
   Words are split on whitespace, compared case-insensitively, and stripped of `.,;:!?` at both
   ends. Bounds: it reads one line at a time, so a span that wraps a line is not seen; it skips
   fenced code; and emphasis on a word off the list (`**new**`, `**local**`), or a span that opens
   a line partway through a wrapped sentence, is left to review. A table written without a leading
   pipe reads as prose, so write tables with leading pipes.
9. Title-Case pseudo-heading lines — a standalone line of 2+ consecutive Title-Case words that isn't
   a real `#`/`##` heading, a table row, a list item, a blockquote, or code — are reported as a WARN.
   This check is advisory only (it never fails the release): an inline version was tested against
   the real shipped text and flagged only proper nouns and quoted example values, never a genuine
   violation, so the narrower standalone-line version ships instead, unproven against a true
   positive.
10. The connector address is exact: `.mcp.json` names the `plumlayer` server at the one
    production url the check pins, character for character. This cannot judge whether that
    server is up or answers, only that the plugin points at it.
11. No absolute local paths in any manifest.
12. A Question is never a failure report. No shipped skill or agent file tells the agent to raise
    a Question near failure language (a failed or timed-out job, an image-only or unresolved
    page, a retry) with no prohibition cue in range, and every file that names `ask_question` or
    tells the agent to raise a Question carries the sentence ending "never about a Plumlayer
    failure". This is a regression guard over a cue list: failure wording it does not name still
    passes, and whether a Question an agent raises is about the project stays in review.
13. The Question bar. `agents/scope-reader.md` and `agents/scope-vocabulary-reader.md` each
    carry the bar in its fixed wording, "a draft RFI". No shipped skill or agent file carries a
    retired raise-for-everything phrase ("rather than smoothing it", "rather than guessing") on the same line as the word Question, and none carries
    the wording of a Question rule the draft-RFI standard retired: "always raises a Question",
    "raise a Question if inferred" or "when inferred", "Question naming the grain", "a correction
    of an earlier write, that is a Question", `mepDeliveryShape`, or a `"scope-item"` source type, matched over the whole file with whitespace collapsed because those
    phrases wrap across lines. The bar is where the documents disagree about a
    work requirement or leave open a requirement or a pricing basis a bidder needs, with no price
    test and no cap: both readers carry it whole, each case under NOTHING with it and the set still
    being drawn as a stated exception, the reviewer and the skill their restatements, and the
    review, the manual part and the skill's copy of the review's shape the no-Question values
    (`left open` with `the sheets select none of it` or `closed Question <id>`, and `agree`),
    the review asking about a document the set lacks by the readers' test, asking nothing about
    work a section requires only where shown or selected when none is, and naming a silence on a
    set still being drawn on its anomaly line alone, with no low-cost wording anywhere and ten
    breaks refused. This cannot judge whether a
    Question an agent raises clears the bar, only that the bar is stated and the retired rules
    have not come back; that judgment stays in review.
14. Question-text plain-words pointer. Every shipped skill or agent file that names `ask_question`
    or tells the agent to raise a Question carries the fixed phrase "Question text is plain
    estimator words", either stating the rule in full (this file's own Question text on the record
    section) or pointing at it beside the standard the `ask_question` verb states. This cannot judge
    whether a given Question actually reads in plain words, only that the instruction carries the
    rule or a pointer to it; that judgment stays in review.
15. The run ledger's fixed line shapes. The scope run's ledger is a line-shaped log, not prose, and
    the harness never sees a run's ledger, so the checkable target is the text that tells the agent
    what to write. Three arms: the runner definition's grammar block declares exactly the three line
    kinds and the closed `note` kind set, both compared in both directions; every skill or agent file
    that instructs appending to the ledger carries the sentence "Nothing else goes in the ledger";
    and no prose-permitting cue (`narrate`, `summarize`, `paragraph`, `in your own words`) sits near
    a ledger mention with no prohibition cue in range. That last arm is a regression guard against a
    drift that shipped, not a proof: wording it does not name still passes. Its bound is stated in
    the harness README entry rather than left to read as a proof.
16. The runner's mode set. The `##` headings of `agents/scope-round-runner.md` match a pinned set
    exactly, in both directions, so the one-runner-per-pass shape cannot be partly undone (a
    `## Round mode` or a `## Leftover mode` coming back, a `## Pass mode` renamed away) without
    failing the release. The set is pass, review and boundary, plus the four headings
    that are not modes.
17. The plan inventory script does its arithmetic. The shipped `plan_inventory.py` is run
    in-process over an invented grid and four packages fixtures, and its counts, its
    three windows' unit lines and page references, its pinned reading order, its balanced pass
    split and its window 3 unit ids and passes are compared against a tally the check computes
    itself off the same fixtures. Window 3 plans every package's review exactly once across its
    passes of reviews, the general requirements package's review alone in the first, at most eight
    to a pass, in package order with every package of one trade kept whole in one pass; a trade over
    eight is kept whole, one over ten is refused by name, every pass of reviews starts after every
    pass of manual parts and standard lines, the pass ids read `W3-M<n>` and `W3-<n>` and are never
    a unit id, and a second run writes the same plan. Window 2 has to come out an exact partition of the inventory minus the window 1
    file the script itself wrote, and every window 3 unit id has to be a legal `verify_unit`
    subject prefix stem with none a prefix of another, which is the join the plan and the reviewer
    would otherwise first meet on mid-run. Broken inputs must each be
    refused with exit 1 and one line on stderr, and every window's bounds line must name its
    counts, so a run that reports nothing fails. Those refusals cover the two ways a sheet could
    otherwise go missing or be miscounted with nothing said about it: two grid rows folding to one
    unit key, which window 2 would subtract as one and drop as two, and a window 1 file naming a key
    as both selected and left out. Every window 1 and 2 plan it writes is also held to the fold:
    a pass under three units joins the pass before or after it, no pass goes over twelve or holds
    two parts of three or more, every folded unit keeps the id its own discipline gave it, and the
    bounds line names each fold and each small pass left alone. A unit verified under its part's
    own pass before a replan folds that part keeps its id and is counted once in the folded pass's
    summary. Every pass block reads `summed: yes` only while the pass's summary on file names
    exactly its unit ids and its last `pass:` line carries that summary, so a fold that leaves the
    count the same still reads no; in window 3, a package added between plans keeps every unit id
    and reads no only on the passes whose reviews changed, and a run folder of one review per pass
    reads every review verified and every pass unsummed. A review's id is bound to its package's id
    in `plan/window-3.json`: a verified package deleted leaves its same-trade sibling unverified
    under its own id, a package added ahead of a verified one leaves that one verified, and a
    replaced package takes an id no package has held and reads unverified, its pass unsummed; in a
    run folder planned before that file, the read plan on file binds them instead, a package on
    each block's `package:` line or on each unit line, so the same delete and insert keep its ids. A
    209-sheet grid carrying a real set's discipline and sheet type shape, with invented sheet numbers, plans its window 1 in three
    passes. A four-file fixture holds the repeated lines: window 1 plans one unit per file holding
    five or more of the rows the run reads, rows `--exclude` left out not counted, in a pass `RS1`
    that never folds and is counted apart from the sheets, each unit naming its file's sheets the
    run left out; its ids keep across a replan by file, a `sheets none` dispatch line trips no
    sheet refusal, and a file cut under five retires its id; window 2 marks a unit
    `repeated lines read in set <version>` only where its file's unit verified ok last, carries a
    `set` note, whose last version the mark carries, and no `unread` note, without moving an id;
    and the pass summary script sums an `RS1` pass.
    Its bound is stated in the harness README entry and in the check's own detail line:
    the fixtures are invented, so this proves the script's arithmetic, its ordering, its fold and
    its refusals, not how a real grid or packages read arrives.
18. The pass summary script sums the ledger. The shipped `pass_summary.py` is run in-process over
    three invented ledger fixtures with their read plans, and its counts, its note placement, its
    refusals and the labels it prints are compared against a tally the check computes itself; the
    labels also have to equal the labels of the skill's own published summary block, in order, so
    the script and the shape cannot drift apart. A pass's units come off its read plan block, so a
    unit verified under its part's own pass id before a replan folded the part is counted once in
    the folded pass, and the runner's own summary command has to be one the script accepts. The
    summary goes to the file `--out` names and the short hand-back the runner returns goes to
    stdout, both compared against a tally and against the labels the skill and the runner
    definition publish, and the hand-back's one `report:` form, in both, names in every window
    the path the lead's record script reads; a window 3 pass of three reviews adds up the pages
    each opened and the searches each ran off its own report, a review that ran no search and one
    that opened no page included, stopping at the labels of the skill's own reviewer block, which
    `agents/scope-reviewer.md`'s report shape has to equal, and a review with no verified line
    adds nothing and is named on the hand-back. A unit read again counts its latest verified line
    alone, whether the line before it read ok or mismatch, and its trades off its latest set,
    which `unit_report.py trades` leaves alone in the file in place of the unit's earlier lines,
    run twice to no change; a verified line with no dispatch line since the unit's last one is
    refused, and a ledger not named `ledger.md` beside its read plan is refused. A unit whose
    latest dispatch line has no verified line after it is not verified, adds nothing and is named
    with that read; one whose latest verified line reads mismatch needs no report. A passed review
    is summed off the report of the read its latest verified line checked where that report is
    whole by the report script's check, and off the restored report of that read otherwise,
    counted on `reports restored`; a stub with only a searches and a pages opened line is refused
    until the restored report is there; and a last line still being written, with no newline yet,
    is neither read nor hashed. Its
    bound is stated in the harness README entry and in the check's own detail line: the fixtures
    are ledger text, so this proves the arithmetic and not a real verification.
19. No dispatch names `fork` as a subagent type, in either the `subagent_type:` dispatch-line
    shape or a `tools: Agent(fork)` frontmatter declaration, so a runner cannot build a wait out
    of fork agents in place of the reader dispatch that is the wait. Ordinary uses of the word
    stay clean, since the pattern matches only right after those two anchors. This cannot judge
    a wait invented in some other shape; that stays in review.
20. Each agent names the connector verbs it calls. No `agents/*.md` tools line takes the whole
    connector as a wildcard, every connector verb an agent's text names is on its tools line,
    every declared verb is one the connector registers, and each entry in the prohibition-only
    exception table is still named in that agent's text and still off its tools line. The check
    runs its own helper over three agent fixtures, so the refusals are shown rather than
    assumed. This cannot judge whether a declared verb is one that agent should hold; that stays
    in review.
21. Every agent pins its model and effort. Every `agents/*.md` frontmatter carries a non-empty
    `model` and an `effort` of low, medium, high, xhigh or max, so a dispatched agent does not run
    on whatever model or effort the session happens to be on, and a fixture with no `model` and a
    fixture with no `effort` are each shown to refuse. This cannot judge which model or effort a
    definition should name; that stays a decision.
22. Every dispatch says how its caller waits. A fenced block in a shipped skill or agent file that
    carries a `subagent_type:` line also carries `run_in_background: false`, so where the Agent
    tool takes that parameter, as in a headless session, which stops a background agent after ten
    idle minutes, the call is the wait. Blocks naming no subagent type are out of that rule's
    scope. Where the call comes back with an agent id instead, as in a terminal, the caller ends
    its turn: every shipped skill or agent file that dispatches an agent, by a template, by naming
    `run_in_background`, or by sending a fresh agent, carries the one wait sentence that says so,
    and none carries `rare seat` or `still comes back at once`, the sentence it replaced. A fence
    left open at the end of a file is refused rather than skipped, so the block it swallowed cannot
    pass as a file with nothing to check. This cannot judge whether a running agent passes the
    parameter or ends its turn, only that the text tells it to.
23. The repeated lines are read and cited as the server serves them. Window 1 units go to
    `agents/scope-vocabulary-reader.md` and window 2 sheets to `agents/scope-reader.md`, as the
    runner's `Agent(...)` list and pass mode say; the sheet reader carries no repeated lines
    section and holds neither `record` nor the file batch verbs, and the vocabulary reader holds no
    `record`. The vocabulary reader carries a section that walks `repeated: "only"` to its end with `setVersion`, cites each
    block's `firstSheet` with a box from the lowest `x0` and `y0` to the highest `x1` and `y1` of
    the note's lines, sent with `frame: "page-points"` and never converted, and names nothing
    `page-points-rendered`. The same section keeps the set version it read, reports a file with no
    block as read with nothing to record, records nothing from a block whose `printedOn` lists only
    sheets the run left out, searching only where `printedOnMore` says the list was cut, cites a
    block whose first sheet carries no number on the first numbered sheet its `printedOn` lists or
    as a page with no box, reads a box on another page around the same spot grown by 4 points,
    since two pages of a block can sit 4 points apart, and copies `notListed` as the one count it
    is, before an answer with no block sends it to report. The sheet reader's window 2 bullet asks for `omit` on
    every call only on `Repeated lines: read in set <version>`, with no probe call, compares the
    set version on every answer of the walk, and restarts the page whole on any answer that names
    no set version or another. The reader report in both readers and in the skill carries
    `cited sheets:`, `page citations:` and `set version:`; the runner verifies an update cited to
    a page with no sheet number by its subject and that page, and a repeated lines unit off the
    first, taking the prefix counts once however many calls the sheets take, as review mode does
    for a review that opened more than 20 pages, and no line of the runner sums the counts across
    those calls; and the runner's own
    dispatch, set and unread note lines, filled in, are read by the shipped plan script as it binds
    and marks. This cannot judge whether the record door takes the evidence shape or the scope
    surface draws the box; that is the api's to prove.
24. A scope pass belongs to one drawing issue. The shipped `plan_inventory.py` plans two sets of
    one project, each from a run folder whose `run.json` names its delivery, the deliveries its
    sheet list comes from and a unit tag, and every unit id of each pass carries its tag, with no
    pass's `scopeItem:<unit id>-` prefix equal to or starting another's, while a folder in the old
    layout plans untagged. It refuses a tag taken by another run folder or on the record, a grid or
    an inventory of another issue or of deliveries `run.json` does not name, a second run folder
    for one issue, a window 2 under another tag than window 1's, any window in a pass folder that
    lost its `run.json`, and two passes in flight. Its `issue` mode resumes the pass in flight before any other, the old layout's
    included, never resumes a closed one, and starts only the latest set with no pass. The skill's
    own `issue` command and `run.json` are fed to the script, the skill lists the `set_grid` calls
    it permits in one place, and the reader's documented citations and Question sources carry
    `fileId`, with an update counted only where a write landed, and the runner checks each sheet
    of a unit on the file its plan line names. The reader searches its pass's own deliveries and
    keeps a hit only on a page its inventory carries, and reads a row's live citations off
    `drawingRefs`. A pass on an addendum plans its own sheets only, reviews only the packages its
    trades files name, the ones it only updated rows on or raised a Question naming among them,
    grouped into passes under its tag (`i3-W3-<n>`), and names the rest, and starts after its
    set's pass, earliest first; the
    reviewer searches its pass's deliveries and names the file of every page it opens, and
    drawing-upload never asks whether a delivery is a set or an addendum. A unit that wrote on a
    trade it did not name makes window 3 review every package, and a trade the package fold
    re-homes a row to is reviewed off the `fold touched` line the folder's re-home appends to
    `trades/fold.txt`; the reviewer asks the manual itself
    before calling it silent; and drawing-upload's re-read of the open Questions, run by the
    question checker the file it reads at step 9b dispatches, reads the uploaded delivery by its
    id and cites its file. This cannot judge whether a reader sends the file on
    every citation; that stays in review and the measured pass.
25. The runner copies each worker's anomalies onto the ledger. The summary script builds the
    summary's `anomalies:` line from the ledger's `anomaly` notes alone, and the closing report names
    the pairs of rows carrying the same work off them, so `agents/scope-round-runner.md` carries,
    in pass mode, the step that appends one `anomaly` note per line of a report's `anomalies:`
    line, copied whole, with review mode copying the reviewer's the same way, and its
    `grain questions:` and `door-owned suggestions:` lines as `grain` and `door` notes, before the
    unit's `verified` line and with no sentence there negating the append; and in its ledger rule,
    the one exception that lets those notes past its ban on re-telling a report and their exemption
    from the 200-character clause. The check runs its own helper over the shipped text with each part
    taken out, the append negated and the order reversed, so the refusals are shown rather than
    assumed. This cannot judge whether a running runner writes the notes; that stays in
    review and the measured pass.
26. A number printed on more than one page is read on every page. The shipped `plan_inventory.py`
    is run in-process over an invented grid whose rows list their pages under `pageOccurrences`,
    and each further page of a row's own delivery has to come out a sheet of its own right after
    its number's row, with its own title, sheet type, file, page and the key it opens as, counted
    apart from the grid's rows that `--expect-count` holds to, and named on the bounds line; a page
    of an earlier issue is named and never planned. Its unit line names its file and that key, a
    replan binds it by the key while a line naming the number binds the number's first page,
    `--exclude` on the number leaves out both pages, a missing or malformed page list is refused,
    a page whose `deliveryId` is absent or neither null nor a delivery id among them, and the
    runner's own worked dispatch line for a further page binds through the script's ledger
    reader. A run resumed on a newer plugin keeps what it already planned: a window 1 file that
    left a number out by its first page keeps its further page out, and a pass dispatched under
    its own unlettered id that a further page takes past twelve keeps that part. This cannot judge whether a reader cites a further page as its text says, or
    how a real `set_grid` answer arrives; that stays in review and the measured pass.
27. Setup reads stay out of the lead. A page image or a page's text read in the session the user
    talks to stays there, and a setup on a set of about 240 sheets once took that session from 58k
    to 774k tokens. No page read verb (`render_page`, `get_page_text`, `search_set_text`,
    `reconcile_index`), and no `set_grid` other than a summary call with `limit: 0`, sits on a line
    a lead runs: project-setup whole, learn-project whole, drawing-upload outside its step 10, and
    drawing-upload's cloud entry file and its step 9b file whole, and no line there reads a PDF's
    pages with the Read tool. drawing-upload carries its `plumlayer:sheet-checker` dispatch, pairing
    each recognition job with its `fileId`, its step 9b file its `plumlayer:question-checker`
    dispatch, learn-project its `plumlayer:orientation` dispatch and
    the first line of its summary, with orientation's numbered steps and summary shape in
    `agents/orientation.md` and none in the skill the lead loads, drawing-upload gives the pages
    file's line shape as the sheet checker writes it and sends a sheet the index lists and the set
    lacks straight to its Question, scope-run neither of its own copies, project-setup and scope-run point at
    learn-project's section, and the retired sentences forbidding any agent in the upload are gone.
    The check runs its scan over fixtures and its shape arms over the shipped text with each part
    broken, so the refusals are shown. This cannot judge whether a session stays small; that is
    measured from its transcript.
28. The lead's pass script keeps its bookkeeping. The scope run's lead takes one `count_entries`
    call per pass and writes the pass's `pass:` line with the shipped `lead_pass.py`, so it never
    holds a summary. The script is run in-process with the plan and summary scripts over one
    invented run folder: its passes listing is a tally of each plan block, units verified and
    units skipped among its values, the prefixes included, with its three closing lines and no
    check-in line, and a window 2 plan with no pass lists none to dispatch; a record takes the
    `count_entries` answer's `counts` array and pairs each count with its unit by prefix, so an
    answer in another order records exactly the line the check builds, `skipped 0` in it, and the
    plan script then reads the pass as `summed: yes`; a count below the runner's, and an answer
    whose short unit a pairing by place would pass, append the `pass:` line reading
    `lead-verified no` and a `short:` line naming the unit with both counts, and the run goes on;
    an answer with a prefix missing, not in the pass or given twice, a summary naming other units,
    or a unit it reads verified no, is refused; window 3's line for a tagged pass of two reviews
    carries both counts and the reviews' pages opened, searches and reports restored, and its
    listing gives each review's prefix. The record speaks the estimator's words: a pass is named by
    the sheets it read, or in window 3 the packages it reviewed, with its new items summed off its
    trades, items updated, Questions raised and replies, and a unit skipped is said as read twice
    and not confirmed. A pass whose unit was skipped records `skipped 1` and is finished; three of
    four units skipped print the breaker with each unit named, two of four do not. An older
    ledger's `checkin:` lines are read past by the summary, plan and lead scripts, the `checkin`
    mode is gone, and the skill carries the new ledger shapes and the turn rule. Both agents'
    shapes and the reader's mandate on the ending name a Question by the full id `ask_question`
    returned and a reply by the id `reply_question` returned, never shortened, and the skill's own
    command lines are fed to the script's arguments. A record whose summary reads a unit verified,
    where a later `verified` line of that unit past the summary's lines reads mismatch, is refused,
    a line past them still being written, with no newline yet, is not read, and the lead reads a
    unit finished off its latest `verified` line, as the plan script does. This cannot judge a count
    the record returns: the counts are the check's own.
29. The package fold runs one level down. The scope run's lead dispatches the package folder at
    stage 6 step 5 and reads its report with the shipped `fold_report.py`, so no package list, row
    or manual page of the fold reaches its context. The step names no fold verb and carries the
    dispatch, the print read and the recheck; the fold's rules stand in the folder's definition and
    nowhere in the skill; the definition appends `phase: packages folded` in fold mode's last step
    alone and nothing to the ledger in recheck mode; fold mode's first step makes the report before
    any act, keeps the package list as the fold found it in `plan/packages-at-fold.json`, which the
    skill's run folder section names, and, on a fold sent again, compares the record's packages
    with that list and the report and writes or finishes an act found after a stop, never writing
    a package still on the record as deleted and writing one whose lists changed with no act to
    match as `changed:`; its report labels are the script's.
    An empty report hands back zeros, a `changed:` line is taken and counted as no act, and a run
    folder that folded before the folder kept a report
    prints one line saying so and names no delete. The script
    prints an invented report whole, a long one under Bash's output limit across calls and a line
    over the limit cut and joined, every line once; its hand-back is a tally of the report under
    the skill's published labels; each malformed report or call is refused in one line; and the
    skill's and the definition's command lines run. This cannot judge how a running folder judges
    a package: the report is invented.
30. A project's folder is named for its project id. A second project of one name once found the
    first one's folder and could pick up its unfinished pass. The skill names the project folder
    `<runs root>/<projectId>/` and no folder for the project's name, and its issue command passes
    `--runs-root`. The shipped `plan_inventory.py` issue mode is run over two invented projects of
    one name: each starts in its own folder; a pass begun in a folder named for the project is
    found by the deliveries its own files name, resumed by its project and never by the other,
    and a later set of that project starts beside it with the next tag; an old layout pass is found
    by its grid's deliveries, a grid response or a bare array of rows, and one whose grid names none
    is matched to no project; a broken `run.json` in another project's folder, or one with a field
    of another type, stops nothing; and a folder two projects shared, a pass naming a delivery of
    each project, an old layout pass naming no delivery beside a pass of the project, or one
    project's passes in two folders, is refused in one line naming the folders, and a `run.json`
    of the project's own with a field of another type in one line naming it. The skill's own
    issue command, filled in, finds the pass in the folder named for the project, and on a shared
    or split folder refusal the skill has the lead say what is wrong in plain words and never a
    folder path. `learn-project` and `drawing-upload` name their local folder for the project id
    too. This cannot judge a seat's real run history: the folders are invented.
31. Every page of a package's manual is planned before window 3 and read exactly once, by manual
    parts before the package's review. A review once named the pages its page cap left on a report
    line the plan script then parsed to bind a follow-up review, and an abbreviated line stopped
    the run; later the review that read the first pages and wrote the standard lines grew past
    what one agent holds. The shipped `plan_inventory.py` reads the manual's sections with their
    pages (`list_spec_sections`, copied to `plan/spec-sections.json`) and `manual_parts.py` divides
    each package's sections into manual parts of up to ten pages each, a section that fits a part
    never split and a part starting partway into a section keeping room for its opening pages.
    Each package's chain is its parts in order and its standard lines unit last, in passes of
    manual parts and standard lines before every pass of reviews, and the manual plan is made once,
    frozen from the window's first dispatch. Each unit line names its pages,
    `agents/scope-manual-reader.md` reads a part's, the report check holds each part's `spans
    read:` and `section lines:` to its dispatch, and no report decides what is read next. The check
    divides eleven invented shapes and holds every page to exactly one part and every part to its
    pages; plans an invented project and reads back the chains, the first part after `none`, the
    standard lines unit last, the sections not read with their reasons and the bounds figures;
    replans with nothing changed to the same bytes, and after a dispatch with a section moved and
    added, a package deleted and added and a part skipped, each listed as not read and nothing
    planned again; plans three packages of one trade, every unit verified and a section added to
    each, to the same bytes twice; puts a long trade's chain first in lettered passes, each waiting
    for the one before it; and refuses a truncated section list, a plan with no section list, one
    page planned for two parts, a chain whose standard lines unit is not last and a part off its
    review's numbering, each in one line writing nothing. Text arms pin the review's reading of
    the manual through `manual_notes.py`, its six-page bound on a row the sheets and the manual
    both define, the manual reader's mandates 12 and 13 and its reads of the reviewer's mandates
    by number, the runner's spans check and the skill's dispatches, with nine mutations refused.
    This cannot judge how much a manual part holds in context on a real manual; that is the
    measured re-run's.
32. Passes of one discipline run alongside each other, and the script says which. A lead once
    guessed which passes could start together, off a mark the plan never wrote, and one set started
    ten at once and another four and stopped. The shipped `plan_inventory.py` pins six passes at
    once and each window's classes of sheet, reads a window 1 discipline's vocabulary ahead of what
    `--include` added with every id a ledger binds kept, and writes `starts after:` under `summed:`
    in every pass block, for a discipline of many parts, a mixed part, a folded pass, the repeated
    lines pass, a resumed plan, a slice and window 3, which the summary script's plan reader reads
    past. The shipped `lead_pass.py passes` prints `start now:` and `waiting:` off those lines, the
    ledger and the summaries, with the plan file untouched since a pass reported: at the limit with
    `--running`, with gates open and shut, and past a pass stopped on a mismatch. Nothing holds a
    start for a check-in, whatever `pass:` lines and older `checkin:` lines the ledger carries, and
    a pass whose unit was skipped is finished, so the part that waits on it starts. `passes
    --reported` prints the one pass's prefixes off the plan at call time, a window 3 manual part
    among them and taken by the real record, and the three closing lines, keeps that pass out until
    it is recorded, and refuses a pass the plan does not carry. Windows 1, 2 and 3 are driven to
    their end, never stuck, never past the limit, each hand-back taking its prefixes off that call,
    every pass finished once. The skill says the lead starts what `start now:` names and never picks
    a pass, that whatever wakes it takes the listing and acts, a hand-back's calls in their order and
    what the lead holds of them, and the measured basis of its time estimate; the runner's boundary
    says what a reader sees; and both readers read a row that moved again, judge their write against
    it, and send a batch again only on the two refusals a row moving causes. Each fix broken again,
    in the script and in the text, is refused. This cannot judge how a running reader handles a
    refusal, or a run's real wall time and duplicate groups; those are the measured run's.
33. Question text reads easily. Every shipped skill or agent file, and this file, that carries
    the phrase "Question text is plain estimator words" carries the two writing sentences after
    it, word for word, and the files known to carry the phrase are pinned. This cannot judge
    whether a Question an agent writes follows them; that stays in review.
34. The question checker settles a Question in three ways. `agents/question-checker.md` carries
    its three outcomes, answered, changed and unchanged, and `never reword it` for a Question
    that has gone out. This cannot judge whether a running checker decides rightly; that is the
    measured re-read's.
35. The standard lines go to one package each. The 46 trade files under
    `skills/scope-run/standard-lines/` carry 327 lines, each row five cells, one of the four kinds,
    a line, a place to look wherever there is a condition, and a row name, and each file one or more
    Home numbers, each one its numbers start, and at most one `Else:` line naming another file's
    title. A row name is at most 36 characters with no comma, one per half of a Which Trade line and
    one for any other line, never twice in a file and never shared by two lines. Each Which Trade
    line names only trades the check knows, a trade named before `Install` among them, reads the
    same in every file whose trade its line or its condition names, and shares its condition with
    no other line, so one piece of work has one line. The shipped `standard_lines.py` is run over production
    package patterns whose files are assigned in the check apart from the script: each file goes to
    the one package the case names, and the script prints exactly the distinct lines of that
    package's files, each once with its kind, row name, condition and place to look, a line with no
    condition, and a line whose condition says only that the sub supplies material, with its
    instrument at the plugin version, no other line with one, and nothing where no file goes to it. Each
    Which Trade case prints its halves' writers and the exclusion rows the one review the script
    names writes, each with its package and its whole name, the half's row name, ` - by ` and who
    carries the work, and no internal note; with every file on its own package every half of every
    Which Trade line has one set of writers every other package names, each exclusion row is
    written by one package and never on the package that writes the half's own row, its name
    ending with the writers' package names, the trade titles where no package writes it, or the
    owner's words, within 80 characters, and past 80 an ending of several carriers names the first
    and `and others` while one carrier is printed whole for the review to shorten the work's words;
    and every other printed name is the line's row name alone within 80 characters, whatever the
    package is called. A bad kind, an empty line, a short row, a number
    two files claim, a number not written as pairs of digits, a table with no header, no Home line,
    a Home number outside the file's numbers, an `Else:` line naming no other file, a long row
    name, a row name with a comma, one row name for two halves, an unknown trade, a code spaced
    another way, a package not on the list or given twice, no name and a missing folder are each
    refused in one line. The reviewer, the runner, the skill and both readers keep the rules that
    hold a line to its condition, keep it from ever being a Question, take the package list before
    the script, write what the script prints, let the paper give this package's own half to it or
    to another trade over what the script printed, name each row and each
    kind row of mandate 12 for its package, put the headings in build order and save that order,
    and shape the exclusion rows and the general requirement records: an exclusion row on the
    trade that leaves the work out, its one role record holding the role alone, its name ending
    with who carries the work within 80 characters and no description, its `repeatsScopeItem`
    naming only another package's exclusion row of its own name, the first of a batch or one a
    refusal names; where a refusal says the row's own package already carries the name, two steps
    apart: the create taken out and the page cited on the row that package already has, and a
    `repeatsScopeItem` that named the removed create pointed at that row, with nothing ever
    pointed at a package's own row to get past the rule that a package holds one row of a name;
    one already on the package for the same work, under any heading, found by one search for the work's words and
    cited and never made again, two such rows on one package a pair, no role on another trade's row, an
    exclusion row a fold left beside the row of its work judged by the work and retired, and a
    stale ending after a fold written over by the review. The project-record skill carries the
    same exclusion procedure for a person's own agent: the row and its role record, its name and
    ending, no description, the search before a create and the four pointer cases. The full rule for home rows on
    `01 11 13` is pinned word for word after whitespace collapse in each carrier: the seven
    headings in order, the full mapping and Miscellaneous examples, allowances, unit prices and
    alternates, the tie-breaks, each heading only where a home row goes under it, general costs as
    home rows with no General Items or general-requirement role, Exclusions kept and shared
    categories unchanged on other packages, and no heading, package name or row saying General
    Conditions. Mutations moving allowances to Miscellaneous in one reader, removing its
    examples, allowing empty headings, changing one reader's trade code, putting a counterparty
    back in one reader and looking for an exclusion row under one heading in one reader are
    refused.
    This cannot judge whether a running
    review finds a condition rightly; that is the measured run's.
36. A runner counts a unit's attempts and its spent reads apart. `agents/scope-round-runner.md`
    counts a unit's attempts by its `dispatch` lines with a reader started after each, a line with no
    `.started` file and no report after it no attempt, and spends a read only on a failed check: a
    read cut off before its report and a blocked call each spend nothing, each noted with its number.
    A unit with two spent reads is skipped, its writes left on the record, and the runner goes on to
    its next unit; three reads in a row cut off or blocked, or one block, stop the pass for the lead.
    A `Read again:` line, which the lead sends only after the recheck's stop, grants one read by its
    number with one note, and a resume counts the same lines. It checks a unit against its own prefix
    alone, its first dispatch holding 0: a report with no `created subjects:` line, or one naming a
    row outside the prefix, is a mismatch, each such row named on a note written at the check that
    first finds it, which the closing report names whatever a later read ends in; a later read that
    updates those rows and creates nothing new passes. A unit checked by count, with no subject
    count, verifies only once every created subject it names is found on the record by name, never
    by figures added up. It takes a failed claim off only the list its own check read. The reader,
    the vocabulary reader, the reviewer and the rechecker each write their `.started` file first,
    every report shape carries `created subjects:`, and the skill takes every skipped unit as settled
    and never reads it again in windows 1, 2 and 3. Each phrase taken out, and each retired phrase of
    the old rules put back, is refused. This cannot judge whether a running runner counts and checks
    as written; that is the measured pass's.
37. A scanned plan is read from its picture. Both readers read a plan, a riser or one-line
    diagram, or a schedule or legend whose text came back machine read and thin from a render,
    within three renders a page, citing only boxes the text read gives and writing no quantity off
    a render alone; a count printed on a riser or one-line diagram is held against the count
    another sheet states, and a count the reader makes never is one; each page or part left is
    named in one shape on `pages unread:` and on the anomaly line, and the closing report names
    each sheet and part, as stage 9 and `close_report.py` give its source. Each phrase taken out
    is refused. This cannot judge whether a running reader reads a scan well; that is the measured
    run's.
38. A unit that fails its check or ends without a usable report is read again or restored, and
    nobody writes a reader's report or changes a ledger line. Every ledger line goes on through the
    shipped `ledger.py`, under a lock, checked as a batch, with a shadow copy, replaced whole each
    time, that keeps whole `phase:` lines added by hand that an append would take, takes off a
    `checkin:` line added by hand and refuses a new one,
    rebuilds a shadow short only of its final newline from the whole ledger, never adopts a line
    written by hand that holds a control character and puts back any other change under one
    `repaired:` line, which the closing report says in the estimator's words; an append writes
    each control character inside a line as one space and refuses none; a runner runs `ledger.py
    heal` before its first look at the ledger. The shipped `unit_report.py` holds each kind of report to its
    agent's own shape, a stub refused, `created` and `questions raised` held to their lists,
    `questions replied` held to at least one id above 0, none at 0 and never fewer replies than
    ids, while `updated` is held to none, and bytes that are not UTF-8 refused alike off a file
    and off stdin, hands a read the work earlier reads left off the ledger, a failed claim on a
    named row among it, answered written off the read's own list for that write, the predicate of
    a field update and the Question of a link held to the same write, and every other failed check
    taken answered or not, restores a
    passed window 3 unit's lost report from the record without touching the reader's file, writes
    a unit's trades as one set, its marker naming the read, gathers the `touched` trades of every
    verified read of a unit, ok or mismatch, noting once on the ledger a read whose trades are not
    known, and keeps the lists a check confirmed off a returned message. An `owed:` list is read past its `-` or `*` markers. Every file either script, and
    the summary script, writes under the run folder is replaced whole, the ledger's own append
    aside, and a write stopped partway leaves the file as it was. Both scripts run in-process over
    invented run folders with real files, and the ledger's writes in real processes too: one
    killed partway through the shadow and one between the shadow and the ledger, and six at once
    with the lock and without it. A runner stopped before each step of closing a unit, and a
    second runner deciding from the run folder alone off the report on disk and a record answer
    for that read, sums one total with no line but a dispatch written twice. The runner's tools
    line carries no `Edit`; the runner, the four readers and the skill carry the ledger script and
    its heal step, the one closing append, the report check, the Owed line and file, the `owed:`
    and `not written:` lines, the answer to a failed claim and the five claimed writes it covers,
    the Question's id on a failed link's note, the control character written as a space, the
    trades, touched and confirmed
    commands, the confirmed command's exemption, the retry of a lock or replace failure and the
    restore, each phrase taken out and each retired one put back refused. This cannot judge how a
    running runner keeps to them.
39. A scope run says everything at its end, in one file a script writes. With no check-in, what a
    check-in told the estimator reaches him in `closing-report.md`, written by the shipped
    `close_report.py` off the run folder: the lead never retells the run's notes, and every id the
    report would print is a name off a byte-for-byte copy a copy agent makes, or a count by package.
    Over one invented run folder carrying every kind of note, a skipped unit of each reason, a
    blocked and a cut off read, fold lines, amendments, sections on no package, the copies and the
    index's leftovers, each of forty-two items lands once in its own section, no record id is printed,
    the short version stays under its cap, and a report written with the copy failed, with no fold
    report, with no ledger or on an early stop is written and never refused. The skill carries stage
    9's three facts in order (the file written, its short version said with the link, `phase: closed
    out` appended), the stops and each one's message, the first message's one permission sentence,
    and nothing that writes or reads a settings file or hands Claude Code a rule string; the
    attended run's words are gone. Each phrase taken out and each retired one put back is refused.
    This cannot judge how a live run's lead says the short version; that is the live run's.

40. A run that goes to its end on its own never strands itself, and its report never says more
    was read than was. Between tries and polls the lead runs `lead_pass.py wait` in the
    foreground, which returns by itself within 280 seconds, and never waits on a background
    command's exit; every poll is bounded at thirty minutes of unchanged answers, and the same
    refusal twice with no new ledger line between is a stop. A unit's third read in a row that
    spent nothing stops at once, whatever ended the last, and the estimator's go on is noted for a
    blocked unit as for a cut off one. A window 3 pass whose every unit was skipped is recorded, so
    the breaker reads it. A slice's paused line goes on before its index, and the plan refuses the
    rest of the window until the index follows it. In the recheck a unit whose reads are spent is a
    stop. The closing report prints what the run could not read and the short version's count of
    it from one list, counts manual pages only off a reader's own report that passes its check,
    counts failed checks off mismatch lines, and says every sheet was read only where every planned
    unit verified ok and the list is empty. Each is held over invented run folders the shipped
    scripts build, every resume row of the skill's table among them, and each fails on the text and
    scripts before the repair. This cannot judge a live run's waits; that is the live run's.

41. The closing report never rewords a note into something else and never says a change was made
    that was not. A note is classified only by the whole shape its producer writes, and a note in no
    shape is printed under To look at in its own words. A package amendment is written as
    `amending:` before its calls and `amended:` after they succeed, and the report says one as made
    only off its `amended:` line, and one with no `amended:` line as started and not confirmed.
    Manual pages read are the spans the reader's verified report says it read, held to the plan.
    The Questions are headed as every Question on the project, open and closed, and each trade's
    figure is said to include the ones that apply to every trade. Gaps are told
    apart by what they are about, and names a boundary fetched again are history in the detail.
    The skill's two bounds, thirty minutes of one answer and the same refusal twice with no ledger
    line between, are counted by `lead_pass.py seen`, which keeps its count in the run folder, so
    a new session keeps it too. A note is a block or an interruption only where its tail is the
    runner's whole shape. Each is held over invented run folders the shipped scripts build, and
    each fails on the scripts before this repair. This cannot judge whether a live lead runs the
    seen mode where the skill says; that is the live run's.

A check that cannot be made mechanical belongs in review, not in this list. Adding a rule here
without adding its check is how the last drift started, and a check added without its line here is
invisible.
42. The package review comes after its manual parts and its standard lines and stays under what one
    agent holds. On a measured run the median review held 218k and the largest 392k, the largest
    leaving a stub report, because one review read the manual's first pages, wrote the standard
    lines and settled the headings in one context. The review now reads what the parts found
    through `scripts/manual_notes.py`, which uses a part's report only where its latest read
    verified ok and the report check holds it whole, names a restored report as not known and a
    part read mismatch or skipped as not read, and prints those first; the standard lines are the
    work of `agents/scope-standard-lines.md`, one unit per package last in its chain; a part's
    section lines are held to its dispatched spans by `unit_report.py check --spans`; and the
    closing report names a skipped standard lines unit's lines as not written, a skipped review's
    headings and order as not settled, a bound a review reached, and each package that took an
    item after its own review. The check runs the notes script over a part verified, restored,
    read mismatch and skipped, the report check over section lines exact, one missing, one twice
    and one malformed, and the closing report over an invented folder, and pins the new agent with
    no Question tool and the review's bounds. This cannot judge a live review's size; that is the
    measured re-run's.
43. What the package review could not check reaches the estimator, and nothing says more was read
    than was. The notes script prints a line for every section the package lists, a part's or not,
    a section with no pages and one the section list lacks saying so, and names each planned span
    a verified part's report did not read as not read with the reason the part named, holding the
    report to its planned spans as the runner does; the lead's record names only the pages that
    report says were read; the closing report puts every entry of a verified review's or manual
    part's `sections not checked:` and `families not checked:` lines, by the shapes beside each
    producer's name or in its own words, a review's copy of a skipped or restored part's section once, as
    the part's gap, and every standard line a review found later, in the one
    collection, and names a package that took an item after its own review by the note's own place
    on the ledger, however the writing review ended; and the manual reader's read of the
    reviewer's both-sources bullet ends at a pinned line. Each is held over invented run folders the
    shipped scripts build, with every report written as its agent's definition says, the whole of
    window 3 run once from the plan to the closing report, and a replan after stage A was dispatched
    driven to the window's end. This cannot judge a live run's reviews; that is the live run's.
44. A review, a manual part and a standard lines unit spend context only on what a check needs. Each
    writes its `.started` file and its report with the Write tool, the report once, lists no folder of
    the run, and creates at most three rows a batch, each whole, sending again only the batch refused;
    the review's write bound counts rows created and citations written, and a review that reaches it
    passes the report check and is named by its bound in the closing report. The reviewer holds once
    the reader's text it reads whole, each passage it no longer holds found whole in that reading. The
    standard lines unit reads the reader's mandates 1 to 7 and 9 whole, as the review does, and the
    manual reader reads neither the review's reads of the Questions nor its second silence: each bound
    matches once, each passage left out on purpose is pinned by its words, and every heading of the
    reader's mandates is read or left out on purpose. The closing report names a skipped or restored part's section a review copies once.
    Each break is refused. This cannot judge a live agent's size; that is the measured re-run's.
45. The closing report names every gap a review or a part wrote, and each one once. Two standard
    lines found later at one line and place, two bounds of one read and two reasons for one section
    are each named where their words differ; a review's copy of a section a verified part left
    unread with its anomaly, of a plan omission, or of the owner's work the parts named, is named
    once, and the short version counts the same. A bound reached is said as its limit, then what the
    review left in its report's words, which the reviewer writes in plain words. The manual reader
    holds no tool it never calls, its read of the row's name bullet ends at a pinned line, and it and
    the standard lines unit read the review's rules for its report between lines that each match
    once, the manual reader carrying the `anomalies:` ending in the reviewer's words. Each is held
    over invented run folders the shipped scripts build, with every report written as its agent's
    definition says, and each break is refused. This cannot judge a live run's reviews; that is the
    live run's.
46. A manual section a part left unread is named with its current reason and its pages, once, and
    every rule an agent applies is read where it runs. Where a part's latest read verified ok and its
    own report of that read is on file and whole, the closing report names the section off that
    report; otherwise it names it off the part's latest anomaly for the section, with the pages the
    plan gave the part, so two parts of one section are told apart by their pages and one sentence
    is never printed twice. The standard lines unit reads the reader's mandates 1 to 7 and 9 whole,
    mandate 1 among them, and keeps its sentence that it raises no Question and writes nothing for
    one. The review's bound on citations is at least twice the measured run's 90th percentile and
    above a small honest review of seven rows cited from nine pages each, and its other write bounds
    sit above the measured run. No Grep pattern a shipped agent or skill tells an agent to run uses
    `$`: every pattern the text gives after `Grep` is held to a table of its files both ways, and
    each of its branches matches the same lines of each file it runs on with LF endings and with a
    carriage return before each line's end, as a Windows checkout writes them. Each is held over
    invented run folders the shipped scripts build, with every report written as its agent's
    definition says, or over the definitions' text, and each break is refused. This cannot judge a
    live run's reviews; that is the live run's.
