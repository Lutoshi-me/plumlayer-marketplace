# Plugin text style

The authoring contract for every piece of text shipped with the Plumlayer plugin. It exists because
the shipped text drifted for months with nothing checking it: stale skill lists, a flagship feature
described as broken, internal ticket numbers, and real client project names all reached the
distributed tree. The mechanical parts of this contract are enforced by `harness/static_checks.py`,
so a violation fails the release rather than waiting for someone to notice.

## 1. Two audiences, one rule each

Plugin text serves two readers, and confusing them is the most expensive mistake available here.

**Agent-facing text** is the instructional body of a skill. The agent reads it to do the work.
Machinery vocabulary belongs here and is load-bearing: `claim`, `predicate`, `trust class`,
`supersede`, real verb names, real field names. Do not "de-jargon" this text. Precision here is
what makes the product reliable.

**User-facing text** is anything a human reads: the README, the manifest descriptions, the skill
frontmatter descriptions, and, inside a skill body, every narration template, example sentence, and
closing report format. Machinery vocabulary is banned here.

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

## 2. The frontmatter description contract

The description does two jobs at once. A human reads it in a listing; the model reads it to decide
whether to invoke the skill. It must serve both.

- **Style:** folded YAML (`description: >`) for every skill, no exceptions, so the ten look alike.
- **Length:** target 450 characters, hard ceiling 600. The harness fails above 600.
- **Shape**, in this order:
  1. What the skill does, in estimator words, one sentence.
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
  and the claim atom is written `subject — predicate — value`. A blanket find-and-replace across
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
2. The shipped skill set matches the expected set exactly, in both directions.
3. Every frontmatter description is non-empty, folded style, and at most 600 characters.
4. No banned string in any shipped text: client-name denylist, `PLU-\d+`, internal vault filenames,
   `MOSOT`, em dash, middle dot.
5. No absolute local paths in any manifest.

A check that cannot be made mechanical belongs in review, not in this list. Adding a rule here
without adding its check is how the last drift started.
