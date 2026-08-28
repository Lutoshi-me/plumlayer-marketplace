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
emphasis, one vocabulary the same as section 3 requires. The worked rule and an example live in
`learn-project`'s judgment-entry table; every other skill or agent file that tells an agent to raise
a Question points at that rule instead of restating it.

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

1. The version quadruple in lockstep: both `marketplace.json` version fields, the Claude
   `plugin.json`, and the Codex `.codex-plugin/plugin.json`.
2. The shipped skill set matches the expected set exactly, in both directions, and so does the
   shipped agent set under `agents/`. Every agent definition carries a `name` and a `description`,
   and none declares `hooks`, `mcpServers`, or `permissionMode`, the three fields the runtime
   ignores for plugin-shipped agents.
3. Every frontmatter description is non-empty, folded style, and at most 600 characters.
4. No banned string in any shipped text: client-name denylist, `PLU-\d+`, internal vault filenames,
   `MOSOT`, em dash, middle dot.
5. No absolute local paths in any manifest.
6. Retired vocabulary does not creep back in. This is a regression guard, not a live enforcement
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
   The pinned trade-knowledge/ corpus files are out of scope for this check entirely: ordinary
   English collides with several of these names there (a subcontractor's payment "deposit", a
   "proposed" product substitution), and that collision is real trade vocabulary, not drift.
7. Bold used for emphasis on a short, high-precision denylist of ordinary words (`not`, `never`,
   `only`, `must`, `no`, `exactly`, and similar) when the bold span is not immediately followed by a
   colon (the `**Label**:` convention that marks a genuine label). This is deliberately narrower than
   "any bold not followed by a colon": that broader rule flags the bulk of this codebase's own
   legitimate bolded-lead-in and first-use-term conventions, not just emphasis.
8. Title-Case pseudo-heading lines — a standalone line of 2+ consecutive Title-Case words that isn't
   a real `#`/`##` heading, a table row, a list item, a blockquote, or code — are reported as a WARN.
   This check is advisory only (it never fails the release): an inline version was tested against
   the real shipped text and flagged only proper nouns and quoted example values, never a genuine
   violation, so the narrower standalone-line version ships instead, unproven against a true
   positive.
9. The run ledger's fixed line shapes. The scope run's ledger is a line-shaped log, not prose, and
   the harness never sees a run's ledger, so the checkable target is the text that tells the agent
   what to write. Three arms: the runner definition's grammar block declares exactly the three line
   kinds and the closed `note` kind set, both compared in both directions; every skill or agent file
   that instructs appending to the ledger carries the sentence "Nothing else goes in the ledger";
   and no prose-permitting cue (`narrate`, `summarize`, `paragraph`, `in your own words`) sits near
   a ledger mention with no prohibition cue in range. That last arm is a regression guard against a
   drift that shipped, not a proof: wording it does not name still passes. Its bound is stated in
   the harness README entry rather than left to read as a proof.
10. The runner's mode set. The `##` headings of `agents/scope-round-runner.md` match a pinned set
    exactly, in both directions, so the one-runner-per-pass shape cannot be partly undone (a
    `## Round mode` coming back, a `## Pass mode` renamed away) without failing the release.
11. The pass-knowledge excerpt is verbatim. The shipped cut script is run over every trade file the
    knowledge manifest lists, and each trade's whole scope grain rules section, plus each headed
    structural gap list block, must come back as a contiguous byte-identical run in the excerpt.
    Contiguity is the assertion: an every-line-is-present check passes on text that has been
    reordered or reflowed. The knowledge version in the excerpt is compared against the one this
    check reads out of the manifest itself, and the section 7 arm is asserted in both directions.
    Its bound is stated in the harness README entry: four trade files carry no structural gap list
    anywhere in the source, and the check names them rather than passing over them in silence.
12. The plan inventory script does its arithmetic. The shipped `plan_inventory.py` is run
    in-process over invented grid, packages, kinds, and index fixtures, and its counts, its
    three windows' unit lines and page references, and its balanced pass split are compared
    against a tally the check computes itself off the same fixtures. Broken inputs must each be
    refused with exit 1 and one line on stderr, and every window's bounds line must name its
    counts, so a run that reports nothing fails. Its bound is stated in the harness README entry
    and in the check's own detail line: the fixtures are invented, so this proves the script's
    arithmetic and its refusals, not how a real grid or index file's fields arrive.
13. Question-text plain-words pointer. Every shipped skill or agent file that names `ask_question`
    or tells the agent to raise a Question carries the fixed phrase "Question text is plain
    estimator words", either stating the rule in full (`learn-project`'s judgment-entry table, and
    this file's own Question text on the record section) or pointing at it. This cannot judge
    whether a given Question actually reads in plain words, only that the instruction carries the
    rule or a pointer to it; that judgment stays in review.

A check that cannot be made mechanical belongs in review, not in this list. Adding a rule here
without adding its check is how the last drift started, and a check added without its line here is
invisible.
