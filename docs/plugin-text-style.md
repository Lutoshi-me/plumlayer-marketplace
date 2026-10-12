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
Machinery vocabulary belongs here and is load-bearing: `entry`, `predicate`, `trust class`,
`supersede`, real verb names, real field names. Do not "de-jargon" this text. Precision here is
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
emphasis, one vocabulary the same as section 3 requires. What makes a Question worth raising, and
its title, its citations and how it reads to the design team, is the standard the `ask_question`
verb's own description states, where every agent reads it at the verb; this section keeps only
the plain-words rule, and `learn-project` keeps one worked example. Every skill or agent file that
tells an agent to raise a Question carries the plain-words phrase and points at the verb's
standard instead of restating either.

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
lands.

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
   the D6 rewrite, commit `8096333`), not "is this word acceptable" in general. Two scopes:
   - A **whole-file** list (e.g. `residue`, `roster`, `checkpoint`, `mint`, `enrich`, `operator` as
     the name for the person, `deposit`, `proposed`, `trade-packages`) must not appear anywhere in a
     shipped skill, an agent definition, the README, or a manifest. A literal, current identifier that happens to share
     the retired word — the `operator.json` filename, the JSON key
     `"operator"` — is exempt; it is a real name, not the retired concept.
   - A **scoped** list (e.g. `supersede`/`supersession`, `fan-out`, `idempotency`, `census`,
     `grain`, `trust class`) is legitimate agent-facing machinery vocabulary everywhere else in a
     skill, and is banned only inside a `<!-- user-facing -->` span or an `Audience: user` artifact
     clause — the places the file itself has already declared the text user-facing.
   Every shipped file takes the same scan. There is no lenient population and no exemption list:
   a shipped file is the plugin's own prose, in the plugin's own voice, and a hit in one is drift.
8. Bold used for emphasis on a short, high-precision denylist of ordinary words (`not`, `never`,
   `only`, `must`, `no`, `exactly`, and similar) when the bold span is not immediately followed by a
   colon (the `**Label**:` convention that marks a genuine label). This is deliberately narrower than
   "any bold not followed by a colon": that broader rule flags the bulk of this codebase's own
   legitimate bolded-lead-in and first-use-term conventions, not just emphasis.
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
13. The Question bar. `agents/scope-reader.md` carries the bar in its fixed wording, "a draft
    RFI". No shipped skill or agent file carries a retired raise-for-everything phrase ("rather than
    smoothing it", "rather than guessing") on the same line as the word Question, and none carries
    the wording of a Question rule the draft-RFI standard retired: "always raises a Question",
    "raise a Question if inferred" or "when inferred", "Question naming the grain", "a correction
    of an earlier write, that is a Question", `mepDeliveryShape`, or a `"scope-item"` source type, matched over the whole file with whitespace collapsed because those
    phrases wrap across lines. This cannot judge whether a Question an agent raises clears the bar,
    only that the bar is stated and the retired rules have not come back; that judgment stays in
    review.
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
    in-process over an invented grid and two packages fixtures, and its counts, its
    three windows' unit lines and page references, its pinned reading order, its balanced pass
    split and its window 3 unit ids are compared against a tally the check computes itself off the
    same fixtures. Window 2 has to come out an exact partition of the inventory minus the window 1
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
    count the same still reads no. A 209-sheet grid carrying a real
    set's discipline and sheet type shape, with invented sheet numbers, plans its window 1 in three
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
    the folded pass, and the runner's own summary command has to be one the script accepts. Its
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
21. Every agent pins its model. Every `agents/*.md` frontmatter carries a non-empty `model`, so a
    dispatched agent does not run on whatever model the session happens to be on, and a fixture
    with no `model` is shown to refuse. This cannot judge which model a definition should name;
    that stays a decision.
22. Every dispatch template runs in the foreground. A fenced block in a shipped skill or agent
    file that carries a `subagent_type:` line also carries `run_in_background: false`, so the
    Agent call that dispatches an agent is the wait rather than a turn that can end with work in
    flight. Blocks naming no subagent type are out of scope. A fence left open at the end of a file
    is refused rather than skipped, so the block it swallowed cannot pass as a file with nothing to
    check. This cannot judge whether a running agent passes the parameter, only that the text tells
    it to.
23. The repeated lines are read and cited as the server serves them. `agents/scope-reader.md`
    carries a section that walks `repeated: "only"` to its end with `setVersion`, cites each
    block's `firstSheet` with a box from the lowest `x0` and `y0` to the highest `x1` and `y1` of
    the note's lines, sent with `frame: "page-points"` and never converted, and names nothing
    `page-points-rendered`. The same section keeps the set version it read, reports a file with no
    block as read with nothing to record, records nothing from a block whose `printedOn` lists only
    sheets the run left out, searching only where `printedOnMore` says the list was cut, cites a
    block whose first sheet carries no number on the first numbered sheet its `printedOn` lists or
    as a page with no box, reads a box on another page around the same spot grown by 4 points,
    since two pages of a block can sit 4 points apart, and copies `notListed` as the one count it
    is, before an answer with no block sends it to report. Its window 2 bullet asks for `omit` on
    every call only on `Repeated lines: read in set <version>`, with no probe call, compares the
    set version on every answer of the walk, and restarts the page whole on any answer that names
    no set version or another. The reader report in the agent and in the skill carries
    `cited sheets:`, `page citations:` and `set version:`; the runner verifies an update cited to
    a page with no sheet number by its subject and that page, and a repeated lines unit off the
    first, taking the prefix counts once however many calls the sheets take, as review mode does
    for a review that opened more than 20 pages, and no line of the runner sums the counts across
    those calls; and the runner's own
    dispatch, set and unread note lines, filled in, are read by the shipped plan script as it binds
    and marks. This cannot judge whether the record door takes the evidence shape or the scope
    surface draws the box; that is the api's to prove.

A check that cannot be made mechanical belongs in review, not in this list. Adding a rule here
without adding its check is how the last drift started, and a check added without its line here is
invisible.
