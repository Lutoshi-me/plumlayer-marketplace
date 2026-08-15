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

The boundary that keeps getting missed: **a report template is user-facing text.** A skill that
prints a kill list and then writes "report the deposit counts and the residue" has violated its own
rule. Check every report and narration block against section 3.

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

## 3. The estimator-voice block

Every skill carries this block verbatim, byte for byte. It is duplicated deliberately: skills load
independently, so an agent running `takeoff` may never read `project-record`, and a pointer alone
would leave that agent ungoverned. Duplication is the reliability choice; **drift** is the defect the
harness now catches by comparing all ten copies for exact equality.

Only `project-record` carries the extended list with per-term translations. Everything else carries
exactly this and nothing more:

```markdown
## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. This covers
everything the user sees, including your closing report: a report template is user-facing text.

Speak estimator words: project record, entry, sheet, set, scale, scope item, bid response, flagged
item, trail.

Never say to the user: claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, promote, reconcile, reconciliation, ledger, grounding, residue, idempotency, QA,
sheetType, or any raw verb, field, or parameter name.

Translate instead: a value you replaced is "I updated my earlier read"; a machine misread you caught
is "the automatic scan grabbed the wrong text, so I read the sheet and set it right"; cross-checking
the index is "checking the drawing list against the actual sheets"; what you could not settle is
"what is still open". Plain prose, no em dashes, no bolded emphasis words.

The full list, with translations, is in the project-record skill's Words section.
```

## 4. Banned from all shipped text

Each of these is a harness check.

- **Real client or project names, addresses, or quoted client document text.** Examples are
  invented, always. This is confidentiality, not style: the plugin is distributed.
- **Internal ticket IDs** (`PLU-123`). A stranger cannot resolve them and they read as unfinished
  engineering notes.
- **Internal vault filenames** (`scope-package-architecture.md`, `agent-driven-ingestion.md`,
  `drawing-set-intake-design.md`). These live in a repo the user does not have. Either state the
  rule inline or drop the citation.
- **`MOSOT`**, retired as operator-facing vocabulary.
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

- Headings are sentence case: `## 3. Read the residue`, not `## 3 · Read The Residue` and not
  `## Step 3 — Read the residue`.
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
4. The estimator-voice block is byte-identical across every skill that carries it.
5. No banned string in any shipped text: client-name denylist, `PLU-\d+`, internal vault filenames,
   `MOSOT`, em dash, middle dot.
6. No absolute local paths in any manifest.

A check that cannot be made mechanical belongs in review, not in this list. Adding a rule here
without adding its check is how the last drift started.
