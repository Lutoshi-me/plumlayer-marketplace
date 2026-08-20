---
name: bid-intake
description: >
  Read a trade's sub proposals into cited bid records on the bid package: bidder profiles, per-row
  responses, coverage, and totals, each cited to its page. Use when the user hands over subcontractor
  proposals to level. Trigger on "bid intake", "read the bids", "level the proposals", "/bid-intake".
  Drives proposal upload, the two-pass blind-then-peer read, supersession for revisions, and a
  count-verified deposit. Does not create the project (project-create), define the bid package (the
  plumlayer.com flow), read drawings (drawing-upload), or sign for the operator.
---

# Bid intake: read sub proposals into cited bid claims, cloud-first

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

Take a trade's subcontractor proposals (the PDFs a sub actually sent back against a bid package) and
turn each one into the bundle of **cited bid claims** the leveling surface reads: who bid, what
they included or excluded per scope row, the dollars they attached, their coverage, and their totals.
Each claim cites the page of the proposal it was read from. A person levels the package and signs the
bid on plumlayer.com.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Every claim this skill writes records as your reading of one bidder's document, cited to
the page it came from. You are the reader; the MCP tools
(`render_page`, `get_page_text` for reading; `get_bid_package` for the rows and peer context;
`propose_batch` and `deposit_additional_item` for the deposit) are the anti-hallucination anchor and
the grounding gate, not the inference engine. There is no server-side proposal reader: you drive
every read, judge every row, and author every claim.

The claim shapes below mirror the `@plumlayer/contract` bid builders exactly; that contract, not this
prose, is the source of truth for a shape. Examples here are generic; never put a real client,
project, or bidder name in this file.

## Confidentiality (non-negotiable)

Proposal PDFs are confidential sub pricing. They are supplied to this skill by **local path** and are
**never committed, never copied to a tracked path, and never quoted verbatim into any file the plugin
or repo tracks.** The bytes upload to the project's private cloud bucket (project isolation + RLS) and
the claims live in the cloud project record; that is fine. What must never happen is a bidder's number or name
landing in a plugin file, a commit, or a note. Reading a proposal you were handed is the job; writing
its contents into tracked source is the leak.

## Narration to the user

<!-- user-facing -->
Keep the words honest and plain: no jargon, no invented certainty. Use plain prose in everything you
say to the user (no em dashes, no bolded emphasis words). Say:

- "uploading proposals" (upload stage)
- "reading <bidder>'s proposal" (per-proposal read)
- "N rows answered, M rows silent" (after a proposal read; never imply a silent row is a zero)
- "N things they priced that aren't on the checklist" (after a proposal read, when the proposal
  carries off-checklist content: plain words for what stage 7b records; never "scope-gap findings")
- "K proposals read, J entries to record" (before recording)
- "declared this a revised proposal, which replaces their prior bid" or "declared a clarification"
  (before recording, when a repeat proposal applies, see stage 6)

Never narrate "claims", "deposit", "proposed", "grounding", "the ledger", "residue", or "the pivot"
to the user: those are machinery. What you record is the package's working data as soon as it
lands, carrying your name and the page it came from; never call it "pending review".
<!-- /user-facing -->

## What this is, and the boundary

`bid-intake` does one thing: read the proposals for **one bid package** (one trade, one project) and
deposit each bidder's bid claims against that package's existing scope rows. It does **not**:

- create the project (`project-create`) or read drawings (`drawing-upload`);
- define the bid package, or invite / manage bidders: that is the plumlayer.com solicitation flow;
  this skill reads an **existing** package's rows and adds bidder responses to them;
- mint a new scope row for proposal content that matches no known row: that content lands as an
  **Additional item** on the package, that bidder's own off-checklist word cited to the page it came
  from, never a minted `scopeItem:` subject (see the hard read rules and stage 7b);
- level or rank the bids (`get_bid_package` computes the leveling projection; this skill only reads it
  for context and deposits the raw response claims the leveling reads from);
- sign or submit anything: leveling the package and committing the bid stay with the operator, on
  plumlayer.com.

The pipeline: **preflight → upload/register → fetch rows + context → two-pass read (blind, then peer) →
assemble + confidence audit → declare supersession mode → deposit the responses → deposit the
additional items → report.** Each stage has gates; they are non-negotiable and collected at the end.

## 1. Preflight

1. **Confirm the account and project.** Call `whoami`, then `list_projects` and confirm with the user
   which project (one project = one project record) these proposals belong to. Capture its `projectId`.
2. **Confirm the bid package exists.** Call `solicitation_list_packages(projectId)` and confirm the
   trade package these proposals are for is present. Capture its **CSI trade code** (e.g. `09 29 00`),
   verbatim, spaces included, no slugging. That trade code keys the package subject and every read
   below. If no package exists for this trade, stop: this skill reads into an existing package; the
   package is defined through the plumlayer.com solicitation flow first.
3. **Take the proposal paths.** The user supplies the proposal PDFs by **local path** (one or more,
   one per bidder, or several from one bidder if a base plus revisions). Confirm which bidder each
   path is for when the filename does not make it obvious; do not guess a bidder from a filename.
4. **Sanity-check each PDF before upload.** The corpus contains at least one 0-byte file. For each
   path, confirm it exists, is non-empty, and is a readable PDF before you upload it:
   ```bash
   for f in "$@"; do
     [ -s "$f" ] && head -c 5 "$f" | grep -q '%PDF' && echo "OK   $f" || echo "SKIP $f (empty or not a PDF)"
   done
   ```
   Report any file you skip and why. An unreadable proposal is named, never silently dropped and never
   guessed at.
5. **Check for byte-identical duplicates.** The corpus has produced the same proposal saved under two
   filenames (a re-send, a renamed copy). Hash each surviving path and intake one copy per distinct
   hash: never upload and read the same content twice under different filenames:
   ```bash
   for f in "$@"; do sha256sum "$f"; done | sort | uniq -c -w64
   ```
   Report which filenames collapsed to the same file and which one you kept.

## 2. Upload and register each proposal (cloud-first)

Proposals read from the cloud, like every other Plumlayer document. Per proposal PDF that passed the
sanity check:

1. `request_file_upload(projectId, filename)` → `{fileId, signedUrl, ...}`. The server mints `fileId`
   and the storage path; you never supply either.
2. PUT the raw bytes to `signedUrl` (the bytes never pass through a tool call):
   ```bash
   curl -X PUT "$SIGNED_URL" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_PDF_PATH"
   ```
3. `register_file(projectId, fileId, filename, contentType: "application/pdf", kind: "proposal")`.
   A proposal is **not** a drawing delivery: pass `kind: "proposal"` and **no `deliveryId`** (the
   `deliveryId` argument is for drawing deliveries only). Idempotent: a retried call for the same
   `fileId` returns the existing row. If it rejects `not_found` / `empty` / `oversize`, stop and report
   rather than retrying blindly.

`render_page` and `get_page_text` gate on file ownership only, so a registered proposal is immediately
readable. Keep the `fileId` for each proposal: **every claim you deposit from it cites that `fileId`
and the page** in its evidence.

You do **not** need `register_pages` for proposals. A file registered as `kind: "proposal"` is
deliberately neither sheet-recognized nor page-registered, so the call probes only the project's
drawing files and does nothing for what you just uploaded. `render_page` and `get_page_text` gate on
file ownership, not on page rows, so your proposals are readable the moment they are registered.

## 3. Fetch the rows and the peer context

`get_bid_package(projectId, trade)` is your one source for the package's checklist. If the live call
fails, **stop and report it; do not reconstruct the rows or the package from raw `search`.** That
fallback is expressly rejected: raw-claim reconstruction re-implements supersession and the scope-item
pivot client-side and drifts from the surface.

**A second failure mode looks like success and is not: an empty checklist.** `get_bid_package` can
return normally with a defined package and `lines: []`: the package exists but no scope items are
enrolled in it yet. This is not an error the tool raises; you have to check for it. If `lines` comes
back empty, **stop and report**: "package scope not yet populated, enroll scope items via
plumlayer.com first." Never proceed to read and deposit proposals against an empty checklist: a
profile/summary-only deposit with no response claims to anchor it is a degenerate run, not a partial
one, and it hides the real blocker (no rows to answer) behind what looks like a normal intake.

- **`get_bid_package(projectId, trade)`** → the leveled projection of the package: the server-computed,
  authoritative, pre-filtered set of scope rows for this trade (`lines[]`, each with its `lineSubject`:
  a `scopeItem:` subject and the row identity you answer against, never minted by you), every current
  bidder (`bidders[].partySubject`, name, laborType, coverage), the head response per cell
  (`lines[].responses[]`, each with `partySubject`, the resolved response, and `receipt.id`: the
  current head claim id for that bidder × row), and the divergence view. **These `lines[]` are the
  checklist**: a bidder responds to these, and only these; do not derive package membership by hand
  from any other read. This is also your **pass-two peer context** and your **supersession head source**
  for existing bidders. It errors "bid package not found" if no package definition claim exists yet for
  the trade; if it does, stop and report (the package definition is a plumlayer.com step), do not fall
  back to `search`.
  It also returns **`additionalItems[]`**: the package's existing off-checklist items, per bidder,
  each with its `subject`, `label`, `citation`, and `receipt.id`. **Read this now and keep it**, before
  you read a single proposal. It is what stage 7b checks against so a re-run never records the same
  off-checklist item twice, and it tells you what a prior run already captured for a bidder you are
  about to re-read. This full read is a stage-3 instrument only. For the post-deposit check, stage 7
  uses `view: "summary"`, a bounded projection of the same read (per-bidder counts and totals, no
  per-line grid, no receipts). Never re-call the full read to verify.
- **`list_scope_items(projectId)`** (optional enrichment only) → the project-wide canonical scope-item
  view. `get_bid_package`'s `lines[]` already carries what this skill needs for the checklist; reach for
  `list_scope_items` only if a specific row needs a field `lines[]` doesn't carry, never to re-derive or
  double-check package membership: that restatement of the server's own filter is exactly the kind of
  client-side drift the read verbs exist to prevent.

**Resolve the contracting party from the whole document: never from the first letterhead.** A
proposal's opening page is often not the bidder's: manufacturer quote sheets and vendor-system
printouts arrive branded with the manufacturer or the quoting software, while the actual contracting
party appears only in a forwarded cover email, a signature block, or a remit-to line deeper in the
bundle. Read the whole submission (cover email included) before deciding who is bidding. Two shapes
this takes in the real corpus:

- **Letterhead mismatch**: the front page carries a vendor or manufacturer name; the cover email or
  signature names the sub who actually carries the contract. The contracting party is the bidder; the
  vendor branding is just where their pricing came from.
- **One submission, several embedded quotes**: a single bidder's package can bundle two or more
  embedded vendor-system quotes covering complementary halves of the scope. That is **one bidder and
  one claim bundle**, with each value cited to the page of the embedded quote it was read from;
  never two bidders.

If the document leaves the contracting party genuinely ambiguous, stop and ask the user; never
guess a bidder into existence.

Then place each proposal's resolved bidder, in this order:

1. **Already a bidder on this package** → reuse that bidder's `partySubject`. This is an existing
   bidder, so supersession may apply (stage 6).
2. **Otherwise, look for the company you invited.** Call `solicitation_list_invitations` for this
   package and read the invited companies. If the proposal's contracting party is plainly one of
   them, use that company's directory id as the party: **`party:<companyId>`**. This is the identity
   the rest of the system already knows the company by, and it is what lets a filed proposal move
   that company to Bid received on the coverage board by itself. **Only the exact company id does
   that**: a name-shaped party never will.
3. **No invited company matches** → mint a stable `party:<slug>` from the bidder's company name (a
   short, stable slug, e.g. `party:acme-drywall`). A bidder who was never invited is still a real
   bidder and files normally; their proposal simply moves no funnel it was never part of.

The matching in step 2 is **your judgment, and you say so**: names differ from legal entities, a
proposal may come from a division or a DBA, and two invited companies can look alike. Match only
when you are actually confident, name the company you matched and why in your report, and fall to
step 3 rather than forcing a doubtful match. A wrong match files a real proposal against the wrong
company's record, worse than an unlinked one, which is merely incomplete. If two invited companies
are plausible, stop and ask the user; never break the tie yourself.

> Party identity was a known seam and this closes it on the intake side (the Sub-CRM owns company
> identity; the bid contract consumes it). Surface the party subject you chose per bidder in the
> report, and whether it came from an invitation or a minted slug.

## 4. The two-pass read (the anti-anchoring discipline)

Read each proposal in **two passes in the same session**. The order is the discipline: pass one reads
each proposal **blind** so a bidder's numbers are never anchored to a peer's; pass two adds peer context
only to flag divergence, never to revise a value.

### Pass one: blind, per proposal

For each proposal, read it against **only the scope rows (stage 3) and that one proposal**: no peer
proposal, no other bidder's numbers in view. Use `render_page` (returns the page image inline; pass a
normalized `region` to zoom a table or a signature block) and `get_page_text` (exact text spans;
`hasTextLayer:false` is the honest image-only signal). Produce, for this bidder:

- **The bidder profile**: name, labor type (one of `Open Shop` / `Union` / `Prevailing Wage` /
  `Supplier`), contact, **proposal date read from the document itself**, and a revision marker if the
  document carries one (R1 / R2 / "Revised"). Never use upload time for the date.
- **Per-row responses**: for each scope row the proposal **addresses**, the response along the three
  axes plus amount and note, per the response value shape (stage 7):
  - **inclusion**: `base` (in the base bid), `adder` (a priced add), or `excluded` (not carried).
  - **routing**: `self` / `by-others` / `NIC`, when the proposal says who carries it. Distinguishes a
    true exclusion from a scope-gap the bidder routes elsewhere. Omit when it is plain base scope.
  - **amount**: the dollar figure when one is given (an adder's add, or a broken-out base cost). Omit
    when none is stated. **Never** derive a number the proposal does not state.
  - **ambiguity**: `OSV` / `TV` / `unclear` when the proposal prices a row ambiguously ("other scope
    value", "to verify", a bare "?"). An ambiguous token **never** resolves to a hard `amount`.
  - **note**: the free-note residue ("included above", "option 1", a typed comment).
- **Coverage**: did this proposal bid the whole package (`full`) or a subset (`partial`)? A `partial`
  coverage carries a human label ("Framing only") and, when the proposal names the covered rows, the
  explicit `coveredItems` subset (the `scopeItem:` subjects from stage 3).
- **Summary totals**: the entered lump figures the proposal states: `base_bid`, and optionally
  `adjustments`, `allowances_alternates` (a parallel bucket, never folded into the total), and
  `total_adj_bid`. These are read as entered, never summed by you from the rows.

  **A submission with several quotes and no combined figure gets NO summary claim at all.** One
  bidder's package can bundle two or more quotes, each with its own stated total and nothing printed
  that adds them up. It is one bidder (stage 3), but there is one summary subject per bidder per
  package and no document figure to put in it. Do not add the quotes together: a summary is only ever
  what the document states, and a total you computed is your arithmetic wearing the bidder's name.
  Deposit the profile, the coverage, and every row response as normal, and simply **omit the
  `bidSummary`**. The leveling projection already handles a bidder with no summary by totalling their
  own row responses and additional items: that is the designed path, not a degraded one, and it
  reaches the same number without anyone inventing it. Say in the report that the bidder carries no
  stated total and name the separate quote figures and their pages, so a person can see what you saw.

**Watch where your project knowledge came from.** A bidder frequently bundles the project's own
schedules and drawings into their submission as attachments. Reading those is grounding against the
project documents, not peer anchoring, and it is legitimate. But if you read them out of the first
bidder's file, every later bidder's mark-mapping leans on a document you obtained from inside a
competitor's package. Prefer the project's own registered drawings for that grounding when they are
available, and if you did lean on a bundled copy, say so in the report so the blind pass is honest
about what it actually had in view.

**Do not let a bidder's phrasing decide where the estimator sees a gap.** The same underlying
exclusion arrives two ways: one bidder writes a blanket "no fire rated glass" that maps to no single
row, another qualifies two specific marks as non-rated. The blanket one becomes an Additional item and
the per-mark one belongs on those rows, both correct, and the result is that the same question
surfaces in two different places depending on wording. So when a blanket exclusion you are recording
as an item also qualifies particular rows, note it on those rows too, and name the connection in the
item's note. The estimator's question is "are we getting rated windows", and it should not be
answerable only for the bidder who happened to phrase it per-mark.

Each of these carries a **receipt** (the `fileId` and page, plus a short `evidence.rationale` paraphrase
of what you read there, the only prose slot the evidence shape carries) and a **confidence** in `[0,1]`
(your read confidence, carried in `evidence.confidence`). Note per flag / value which pass produced it:
pass one for everything here.

### Pass two: peer-aware, flags only

Now, with `get_bid_package`'s peer responses in view, make a second pass over the same proposals. Pass
two may **only**:

- add or adjust **ambiguity flags**: a row you now see every peer priced but this bidder left blank is
  a sharper scope-gap signal; a token you read as plain may now read as `OSV` against the peer pattern;
- run the **miss-direction checks**: is this bidder an outlier low because they excluded a row the
  peers all carried? Flag it for review.

Pass two **must never** revise a pass-one `amount` or `inclusion` to move a bidder toward the peers.
The whole point of reading blind first is that a bidder's price stands on their own document. In the
report, state which pass produced which flag.

### Hard read rules (gates, not advice)

These are gates. Write them into every read:

- **Silence is not a claim.** A scope row the proposal does not address gets **no response claim** at
  all. Count it as silent for that bidder in the report. Never deposit a `base`/`excluded`/zero to
  represent silence: silence is unknown, and a bare grid that treats it as answered is the exact
  conflation coverage exists to prevent.
- **Proposal content matching no known row becomes an Additional item, never a minted row.** If a
  proposal says something about the work that maps to none of the stage-3 scope rows, it lands as an
  **Additional item** on the package (stage 7b): that bidder's own off-checklist word, cited to the
  `fileId` and page it sits on, and **never** as a new `scopeItem:` subject this skill mints. Minting
  scope from a bid would let a bidder's document silently define the scope checklist; recording it as
  that bidder's item says exactly who said it, and leaves the checklist decision with the estimator.

  **What qualifies, in two tests that must both hold.**

  **Test one: is it a statement about work?** The content has to change what this bidder is carrying:
  something they priced into their base, priced as an add, named as an exclusion, or routed to someone
  else. Standing commercial terms fail this outright and never reach test two: payment, retainage and
  credit terms, price-validity windows and escalation clauses, liquidated damages, schedule and access
  caveats, lead-time tables, insurance, bonding and warranty language, capability statements ("we can
  produce shop drawings in a week" states no inclusion and no price), and takeoff-basis caveats. Those
  belong in the bidder's note, the coverage label, or the run report.

  **Test two: is the work anchored to this project?** The named work must ALSO be either

  - **anchored in the documents**: it appears in this project's drawings, schedules, or the package's
    scope rows; or
  - **anchored by a peer**: another bidder on this package priced it or named it.

  Anchoring is what keeps the section honest, and it is not optional. A facade vendor's standard
  exclusion list runs to forty-odd entries naming revolving doors, curtain wall, card readers and
  window-washing equipment on a project that has none of them. Every one of those is a genuine
  statement about work and passes test one; not one is about *this* building. Without the anchor the
  section fills with another project's boilerplate.

  Two consequences to hold honestly. The peer anchor is **not available during a blind pass one**: it
  is a pass-two admission, and admitting an item on peer evidence is not the same as revising a value
  toward a peer, so it does not breach the pass-two rule. And the **first or only bidder on a package
  gets the weaker filter**, with only the document anchor available; say so in the report when that is
  the situation, rather than implying the same bar was applied.

  The reason the gate is this tight: the Additional items section is read by its **mere presence**.
  Anything sitting in it is awaiting the estimator's judgment. Five bidders' worth of boilerplate would
  drown the three real ones and destroy exactly the property that makes the section useful. When a
  piece of content genuinely sits on the line after both tests, record it and say in the report that
  you were unsure; a borderline item a person dismisses in one move beats a real gap you swallowed.
- **Aggregation is narrow, stated once, and flagged per claim.** A proposal often prices one scope
  row across several of its own lines: a variant pair (a tempered option beside the standard unit),
  a split line-item pair, a companion component priced on its own line. Folding those lines into one
  row response is allowed **only** when all three hold: same bidder, same scope row (same mark), and
  the lines are complementary components of that one row's scope; never alternatives to choose
  between. Apply one consistent aggregation rule for the whole run, state it in the report, and flag
  every aggregated response (its note names the lines folded in; the receipt cites where they sit).
  Lines that belong to different rows stay split, and a line that maps to no row becomes an Additional
  item; aggregation never absorbs it into a nearby row. When you cannot tell whether lines are
  complementary or alternative, do not fold: keep the clearest single line as the response, put the
  rest in the note, and flag the row `unclear`.

  **The reverse case: one proposal line covering several rows.** A bidder often prices a single
  combined type against what the schedule splits into two or more marks. Do not silently attach it to
  the likeliest one. Deposit a response on **each** row the line genuinely covers, flag every one of
  them `unclear`, and say in each note that they share one undivided proposal figure and which line it
  was, so a person can see the split is yours and not the bidder's. Never divide the money between
  rows by your own arithmetic.

  **Do not fold across a checklist row and a door assembly.** A line named for a window mark can be
  the glazed half of a door assembly rather than extra units of that mark. When a line's quantity does
  not reconcile against the schedule's own quantity for that mark, treat that as the signal it is a
  different thing, and check before folding: a wrong fold inflates the largest row on the package.

  **Additional items aggregate under the same rule.** Two proposal lines may fold into one item only
  when they are complementary components of the same off-checklist thing; say in the item's note which
  lines were folded and where they sit.
- **An ambiguous token never becomes a hard number.** `OSV` / `TV` / `?` set the `ambiguity` axis; they
  never populate `amount`.
- **No receipt, no deposit.** A value you cannot cite to a `fileId` and page is not deposited. If you
  believe a fact but cannot point at where you read it, it does not become a claim.
- **Nothing you write is a person's word.** Every claim records as your reading of the document; this
  door cannot record one as human-authored, and a human correction outranks yours on the same row.

## 5. Assemble and audit confidence

Assemble the full claim bundle per bidder (profile, coverage, summary, one response per answered
row, and the additional items this proposal earned under the stage-4 gate). Before depositing, run a
**confidence audit**: collect every read whose `evidence.confidence` is **below 0.7** and list it in
the report for human attention. A low-confidence read still deposits, carrying its confidence and its
receipt, but it is called out, not buried in a count. State the per-bidder counts by predicate, the
silent-row count per bidder, and the additional-item count per bidder, so the deposit manifest is
honest.

## 6. Declare the supersession mode (before deposit)

If a bidder is **new** to this package (no prior claims in `get_bid_package`), there is no
supersession: deposit fresh claims, and skip to stage 7.

If a bidder **already has claims** on this package, classify the new document from **its own framing**,
not from a guess:

- **A "revised proposal" / "revised bid" / a higher revision marker → wholesale.** The revised document
  restates the bidder's whole position. Deposit a fresh response claim for every row you read from it,
  each with `supersedesId` set to that row's **current head response claim id** (from
  `get_bid_package`'s `lines[].responses[]`: the cell for this `partySubject` on that row, its
  `receipt.id`). Rows the revised proposal is now **silent** on get **no re-assertion**: their prior
  claim simply lapses (silence lapses; you do not carry a stale prior forward). Also supersede the
  bidder's profile, coverage, and summary claims (see the head-id note below).
- **A "clarification" / "delta" / an addendum letter naming specific items → surgical.** The document
  changes only the rows it names. Deposit new claims **only** for those named rows, each with
  `supersedesId` set to that row's current head claim id; everything else the bidder previously said is
  left untouched.
- **Ambiguous framing** (you cannot tell whether it restates or amends) → **stop and ask the user.**
  Never guess the mode. Guessing wholesale drops rows that should stand; guessing surgical strands a
  stale prior position.

State the declared mode in the report and confirm it with the user **before** you deposit.

> **Head-id note (a real detail the proving run should confirm).** `get_bid_package` exposes the head
> claim id only for **response cells** (`lines[].responses[].receipt.id`). It does **not** expose the
> head ids for a bidder's `bidderProfile`, `bidSummary`, or `bidCoverage` claims. To supersede those
> three on a wholesale revision, resolve each head with a targeted `search` on its deterministic subject
> (e.g. `search(projectId, subject: "bidCoverage:<party>:<pkg>", predicate: "bidCoverage")`) and take
> the current head (the claim no other supersedes). This is a targeted single-subject lookup, not the
> rejected raw-`search` reconstruction of the package. If two revisions land without an explicit
> supersession edge on these subjects, both survive and the head resolves by id tie-break, not
> chronology, so the edge is load-bearing. Surface this in the proving run.

## 7. Deposit: author the claim JSON, batch, verify

Author the claim JSON directly, matching the `@plumlayer/contract` bid builder outputs **exactly**. The
subjects are deterministic recipes; the predicates and value shapes are fixed. Get them wrong and the
claim lands on the wrong subject or fails validation.

**Subject recipes** (build from already-stable constituents: the `partySubject` from stage 3, the
package subject, and the `scopeItem:` subjects (`lineSubject`) from `get_bid_package`'s `lines[]`):

```
package subject   bidPackage:<projectId>:<trade>                        (trade = CSI code verbatim, spaces kept)
response subject   bidResponse:<partySubject>:<bidPackageSubject>:<scopeItemSubject>
summary subject    bidSummary:<partySubject>:<bidPackageSubject>
coverage subject   bidCoverage:<partySubject>:<bidPackageSubject>
profile subject    <partySubject>                                       (the party subject itself)
```

**Predicate + value per claim** (the value must satisfy the contract's zod schema; extra keys are
rejected by `.strict()`, enums are exact):

```json
// bidder profile  (predicate: "bidderProfile", subject: the party subject)
{"subject": "party:acme-drywall", "predicate": "bidderProfile",
 "value": {"name": "Acme Drywall", "laborType": "Open Shop",
           "contact": "j@acme.example", "proposalDate": "2026-03-14", "revision": "R2"},
 "sourceInstrument": "bid-intake-skill",
 "evidence": {"instrument": "bid-intake-skill", "method": "agent-vision-read", "confidence": 0.9,
   "rationale": "cover letter header, dated + signed", "fileId": "<fileId>", "page": 1}}

// per-row response  (predicate: "bidResponse")
{"subject": "bidResponse:party:acme-drywall:bidPackage:<projectId>:09 29 00:scopeItem:<id>",
 "predicate": "bidResponse",
 "value": {"inclusion": "adder", "routing": "self", "amount": 4200,
           "note": "add for level 5 finish"},
 "sourceInstrument": "bid-intake-skill",
 "evidence": {"instrument": "bid-intake-skill", "method": "agent-read", "confidence": 0.8,
   "rationale": "line item 3, priced add", "fileId": "<fileId>", "page": 2}}

// coverage  (predicate: "bidCoverage")  — proposalFileId is the registered file id
{"subject": "bidCoverage:party:acme-drywall:bidPackage:<projectId>:09 29 00",
 "predicate": "bidCoverage",
 "value": {"basis": "partial", "label": "Framing only",
           "coveredItems": ["scopeItem:<id-a>", "scopeItem:<id-b>"], "proposalFileId": "<fileId>"},
 "sourceInstrument": "bid-intake-skill",
 "evidence": {"instrument": "bid-intake-skill", "method": "agent-read", "confidence": 0.85,
   "rationale": "scope statement, page 1", "fileId": "<fileId>", "page": 1}}

// summary totals  (predicate: "bidSummary")  — parallel buckets, never summed by you
{"subject": "bidSummary:party:acme-drywall:bidPackage:<projectId>:09 29 00",
 "predicate": "bidSummary",
 "value": {"base_bid": 128000,
           "allowances_alternates": 6000, "total_adj_bid": 134000},
 "sourceInstrument": "bid-intake-skill",
 "evidence": {"instrument": "bid-intake-skill", "method": "agent-vision-read", "confidence": 0.9,
   "rationale": "proposal total block", "fileId": "<fileId>", "page": 3}}
```

Value rules that the schema enforces, honor them at authoring time:

- `inclusion` ∈ `base | adder | excluded`; `routing` ∈ `self | by-others | NIC`; `ambiguity` ∈
  `OSV | TV | unclear`; `laborType` ∈ `Open Shop | Union | Prevailing Wage | Supplier`; coverage
  `basis` ∈ `full | partial`. No other values, ever.
- Optional fields are **omitted** when absent, never set to `null`. Every optional field in the bid
  schemas is `.optional()`, not `.nullable()`: an explicit `null` is rejected, not treated as "none."
  Omission is the only correct encoding of "not stated."
- `sourceInstrument` equals `evidence.instrument` (the builder sets it from there).
- `evidence.page` requires `evidence.fileId`: a page pointer with no file is rejected.
- For a **surgical or wholesale supersession**, add `"supersedesId": "<current head claim id>"` to the
  claim, resolved per stage 6.
- Bid claims carry **no `versionScope`** (the bid builders do not set one); omit it.

**Batch and verify.** Pool the authored claims and call `propose_batch(projectId, claims)` in batches
of **≤50** claims (the door accepts up to 500, but ≤50 keeps each read faithful and count-verifiable).
It is atomic: one bad entry rejects the whole batch and names the index. Transport every entry
**verbatim**; never re-type a value from memory. **Verify:** the returned `count` must equal the number
of entries you sent in that batch. If it does not, **stop and report** the discrepancy; never retry
with a reconstructed or guessed correction.

**Recount before you confirm.** Any count you are about to restate as checked (rows answered, rows
silent, claims per predicate, entries in a batch, additional items recorded) gets an explicit fresh
recount against its source at the moment you restate it. Echoing a number you computed earlier (or
that the user read back to you) and calling it "confirmed" is not verification; the word "confirmed"
is earned by the recount that precedes it, every time.

## 7b. Deposit the additional items (a different door, after the batch)

The off-checklist content you gathered under the stage-4 gate lands here. **This does not ride
`propose_batch`.** The generic deposit door refuses the `additionalItem` predicate outright: the only
way in is `deposit_additional_item`, **one call per item**.

**Order is a gate, not a preference. Run this stage only after stage 7's batch has landed.** The door
refuses a `partySubject` that is not already a bidder on this package, and what makes a party a bidder
is having a response, a coverage, or a summary claim on it. Deposit an item first and it is refused;
deposit it after the batch and the bidder exists. A bidder whose proposal answered no rows at all is
still fine; their coverage claim alone establishes them.

**Check what already stands before each call.** This door has **no idempotency key**: two identical
calls mint two separate items, silently. Against the `additionalItems[]` you captured in stage 3, for
this bidder:

- **Nothing like it there** → deposit fresh (no `supersedesId`).
- **You are correcting an item a prior run of this skill recorded** → pass `supersedesId` set to that
  item's **`receipt.id`** from `additionalItems[]`. It must be the item's current head; a stale id is
  refused rather than landed, which is the door protecting you.
- **The item has a non-null `migratedFrom`** → **leave it alone entirely.** That is not your record.
  It is a response of this bidder's whose scope row stopped projecting, presented here by the
  projection itself, and it recomputes on every read. Never supersede one, and never re-record its
  content as a fresh item: that would double-count the bidder's money.
- **The item has a non-null `resolution`** → a person already reconciled it. Leave it alone and say so
  in the report; re-recording it would reopen a decision someone already made.

**Per item, call:**

```
deposit_additional_item(
  projectId,
  trade,                 // the CSI code verbatim, same as everywhere else in this run
  partySubject,          // the bidder, exactly as stage 3 resolved them
  label,                 // a short checklist-row-style name, <=200 chars, in the estimator's words
  description,           // optional: when the label alone is not enough
  inclusion,             // optional: base | adder | excluded — what the proposal actually says
  routing,               // optional: self | by-others | NIC — when they say who carries it
  amount,                // optional: the stated dollar figure. NEVER a number you derived
  note,                  // optional: the free-note residue, the qualifier as written
  evidenceFileId,        // REQUIRED — the proposal you read it from
  evidencePage,          // the 1-based page. Always send it; a citation with no page is a weak one
  evidenceMethod,        // e.g. "agent-read" / "agent-vision-read"
  evidenceConfidence,    // your read confidence, 0-1
  evidenceRationale,     // the short why that binds the proposal's text to this item
  sourceInstrument: "bid-intake-skill",
  supersedesId,          // only per the correction case above
)
```

Shape notes that will bite otherwise: `label` is required and capped at 200 characters; the enums are
exact and there is **no `ambiguity` axis on this door** (unlike a response, carry an ambiguous
qualifier in the `note` instead); optional fields are **omitted** when absent, never `null`;
`trade` is the CSI code **exactly** as the package was created with, spaces kept and never slugged,
the same string `get_bid_package` reads with (a different spelling mints the item on a package subject
nothing reads, so it lands and then renders nowhere); and `evidenceFileId` is refused if missing,
because an off-checklist item nobody can trace back to its source is not worth having.

**An alternate has its own field. Never encode one as an inclusion or a signed amount.** When a
bidder offers an alternate, meaning any price contingent on someone choosing it, whether it raises or
lowers the base bid, record it with the `alternate` field: `direction` is `"add"` or `"deduct"`, and
`amount` is the plain positive magnitude the proposal states. Never make the amount negative and never
use a negative adder; the door refuses a negative magnitude outright. Leave `inclusion` and `amount`
alone for the alternate's money: those describe the base bid, and an alternate says nothing about the
base bid. On an additional item the door refuses `amount` and `alternate` together, since the item's
own `amount` counts into the bidder's total and the pair would move a total nobody accepted; if a
proposal both prices an item and states an alternate on it, land the base price on the scope-line
response and put the alternate there, where the two may coexist. File each alternate as its own
additional item so it carries its own citation, or set the field on a response when the alternate
modifies a checklist row the bidder answered. The `note` carries only what the paper says the figures
do not: tax treatment, whether alternates combine, which building or scope the figure covers. Never
write an explanation of how the record is stored. A summary-level alternate still belongs in
`bidSummary.allowances_alternates`, the parallel bucket that is never folded into a total; the
`alternate` field is the same idea at item and response level, and it likewise never moves any total
until someone accepts it.

**Verify by reading back, not by counting your own calls, and read back BOUNDED.**

Do **not** re-call the full `get_bid_package` for this check. On a real package the full response is
enormous: three bidders against a nineteen-row checklist measured roughly 165,000 characters and
overran the tool output limit outright, and that is a small job. The full read is the stage-3 context
call, made once; it is not a verification instrument.

Verify with **`get_bid_package(projectId, trade, view: "summary")`** instead. That returns the bounded
verification projection: per bidder, `responseCount` (that bidder's response cells with a non-null
receipt), `additionalItemCount` (all of the package's additional items for that bidder, reconciled or
not), and the carried totals and ranks. No per-line grid, no receipts: a couple of thousand
characters on a real package.

Check, for each bidder you deposited for:

- **`responseCount`** equals that bidder's stage-3 baseline (their `lines[].responses[]` cells with a
  non-null `receipt` in the read you kept) plus the **fresh** rows you answered. A new bidder's
  baseline is zero. A correction supersedes in place and raises no count.
- **`additionalItemCount`** equals that bidder's stage-3 `additionalItems[]` count plus the **fresh**
  items you deposited (same in-place rule for corrections). Baseline and check come from the same
  projection, so derived (`migratedFrom`) items appear in both and cancel out of the comparison.

Each `deposit_additional_item` call also returns the item's `subject`: keep them for the report. If
any number disagrees, **stop and report**: do not deposit again to "fix" it, and do not reconcile the
difference by reasoning. A duplicate you can see is recoverable in one move by a person; a duplicate
you papered over is not.

## 8. Report and hand off

<!-- user-facing -->
The run report **is** the manifest. State, plainly:

- **Per bidder:** the bidder identity you used, entry counts by type (profile / responses / coverage /
  summary), whether this was a fresh bid, a full revision, or a partial update, and what it replaced,
  and the silent-row count (rows the proposal did not address).
- **Additional items:** how many off-checklist items you recorded per bidder, and where they now live
  (the package's Additional items section on plumlayer.com), a pointer to what landed, not a
  re-listing of it. The items carry their own descriptions and citations; restating them here would
  make the report a second, staler copy of the record. Do name any you judged **borderline** under the
  stage-4 gate, and anything you deliberately left out of the section as a commercial term, so the
  judgment call is visible rather than silent.
- **Low-confidence reads:** every value below 0.7 confidence, called out for review.
- **Pass attribution:** which flags pass one produced versus pass two.
- **Record verification:** each batch's sent-and-recorded count, confirmed equal, and the
  additional-items check (the count before, the count after, and the rise), confirmed to match what
  you recorded.

Then point the user at the **package view on plumlayer.com** to review and level. The numbers are
readable there now, each with the proposal page behind it; the bid itself is theirs to sign.
<!-- /user-facing -->

## Gates (non-negotiable)

- Every claim's evidence cites a `fileId` and page of a proposal you actually read; no receipt → no
  deposit.
- Silence is never a claim; an unaddressed row is counted silent, never deposited as a value. Silence
  produces no Additional item either: the empty cell already says it, and an item nobody asserted
  would be a record of nothing.
- Proposal content matching no scope row becomes an Additional item, never a minted `scopeItem:`. It
  qualifies only if it passes BOTH tests: it states something about work (not a commercial term), and
  that work is anchored either in this project's documents or by another bidder on this package. An
  unanchored boilerplate exclusion naming work this project does not contain never becomes an item.
- A summary is only ever a figure the document states. A submission carrying several quotes and no
  printed combined total gets NO `bidSummary`; the projection totals that bidder from their own rows.
- An alternate is never a negative-amount adder and never an inclusion: it goes in the `alternate`
  field (`direction` plus a positive magnitude), so the bidder's total still equals what they
  submitted and the offer stays visible, priced, and attributable.
- Additional items go through `deposit_additional_item` one at a time, never `propose_batch` (which
  refuses the predicate), and only after the response batch has landed (the door refuses a party who
  is not yet a bidder).
- No item is deposited without first checking the package's existing `additionalItems[]` for it; this
  door has no idempotency key, so an unchecked re-run duplicates silently. A derived item (non-null
  `migratedFrom`) and a reconciled one (non-null `resolution`) are never touched.
- Deposits are verified by reading the package back in **summary view** (`get_bid_package` with
  `view: "summary"`) and matching the rise in per-bidder counts against the stage-3 baseline; a
  mismatch stops the run and is reported, never deposited over. The full read is never re-called for
  verification.
- The contracting party is resolved from the whole document (cover emails, signature blocks,
  letterhead mismatches), never from the first letterhead; a bundle of embedded vendor quotes under
  one party is one bidder; genuinely ambiguous identity stops and asks.
- Line aggregation only ever folds same-bidder, same-row, complementary-component lines, under one
  stated rule, flagged per aggregated response; never across rows, and never to absorb off-checklist
  content that should stand as its own Additional item.
- Any count restated as "confirmed" gets an explicit fresh recount against its source first; an
  echoed number is never verification.
- An ambiguous token (`OSV` / `TV` / `?`) never resolves to a hard `amount`.
- Pass two never revises a pass-one amount or inclusion toward the peers; it only flags.
- Supersession mode is read from the document's own framing; ambiguous framing stops and asks. The
  declared mode is confirmed with the user before deposit.
- Rows a wholesale revision is silent on lapse (no re-assertion); a surgical delta touches only named
  rows.
- Claim JSON matches the `@plumlayer/contract` bid shapes exactly (recipes, predicates, enums,
  `.strict()` values).
- Deposit is verbatim, count-verified transport in ≤50-claim batches; a count mismatch stops the run.
- Nothing this skill writes carries a person's authority or a signature; leveling the package and
  submitting the bid stay with the operator.
- `get_bid_package` is the row + context source; a failure stops the run and is reported; never a
  raw-`search` reconstruction of the package, and never a hand-derived membership filter over
  `list_scope_items` as a substitute.
- A `get_bid_package` success with `lines: []` is not a green light: the checklist is empty, so stop
  and report rather than depositing a degenerate profile/summary-only run with no response claims.
- Proposal specifics live in the cloud project record and in local files; they never enter a tracked/committed
  plugin or repo file, and never appear verbatim in this skill's own text.

## Bundled vs. config

This skill generalizes once. The per-job delta (which project, which trade package, which proposal
folder) is **data** the user supplies at run time, never an edit to the skill. A new intake job never
edits `SKILL.md`; it runs the same pipeline against new paths.

## Deferred / for the proving run to decide (named, not skipped silently)

- **The Additional-items gate: PROVEN on a real run 2026-08-09, and tightened by it.** Three real
  window proposals against a sixteen-row package produced twenty-six items and caught a gap nothing
  else in the record held: every bidder excluded installation, so nobody was installing. The
  statement-about-work test alone proved **too loose**: roughly fifteen of one facade vendor's
  forty-odd boilerplate exclusions passed it, naming work the project does not contain. That is why
  the anchoring test above exists; it cut those fifteen to eleven defensible items. Still open for the
  next run: how the weaker single-bidder filter behaves when there is no peer to anchor against, and
  whether the anchoring test is now too tight on a genuinely novel exclusion no peer thought to name.
- **Where a whole-bid qualification lives.** A bid can substitute a different material against the
  specified one across every row, the single most important leveling fact about that bidder, and it
  is neither per-row nor off-checklist. `bidCoverage` carries `basis`, `label` and `coveredItems` but
  no note, and `bidSummary` has no note either, so it currently gets crammed into the coverage label.
  Raised on the board; until it is settled, put it in the coverage label and lead with it in the
  report so it is not lost.
- **Party identity resolution: settled, see stage 3.** The bridge is the
  directory company id: an invited company's proposal files under `party:<companyId>`, which is what
  moves that company to Bid received on the coverage board. An uninvited bidder still mints
  `party:<slug>`. What remains for a proving run is only how often real proposals match cleanly by
  name against the invited list, and how the ambiguous cases actually read in practice.
- **Head ids for profile / summary / coverage supersession.** `get_bid_package` exposes only response
  head ids; the other three are resolved by targeted `search` on their deterministic subjects (stage 6
  note). Confirm this resolution path on a real revised proposal.
- **Solicitation package vs. bid-package-definition claim.** `solicitation_list_packages` confirms the
  solicitation package; `get_bid_package` needs a `bidPackageDefinition` claim for the trade. If the
  former exists but the latter does not, this skill stops and reports rather than fabricating the
  definition: confirm where the definition is expected to come from.
- **Image-only / scanned proposals.** `hasTextLayer:false` means no vector text; read what you can from
  the render and flag the rest honestly (no OCR dependency here; that is a separate, deferred concern).
