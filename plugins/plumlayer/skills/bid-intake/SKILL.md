---
name: bid-intake
description: >
  Read a trade's sub-proposal PDFs and turn them into cited bid claims on the matching bid
  package in the project's Plumlayer MOSOT — bidder profiles, per-row responses (inclusion / routing /
  amount), coverage, and summary totals, each grounded to a page of the proposal it came from. Use when
  the user hands over one or more subcontractor proposals / quotes for a trade package and wants them
  read into Plumlayer for leveling. Trigger on "bid intake", "read the bids", "read these proposals",
  "level the proposals", "get sub quotes into plumlayer", "intake this quote for <trade>", "we got
  bids back for <package>", "load the drywall proposals", "/bid-intake". Drives proposal upload +
  registration, the two-pass blind-then-peer read, supersession for revised proposals, and a
  count-verified claim deposit over the hosted Plumlayer MCP verb surface. The agent reads and judges;
  deterministic tooling grounds; nothing enters untraced. Every claim cites the proposal page it came
  from and records as the agent's reading. This skill does NOT create the project (project-create),
  define the bid package or invite bidders (the plumlayer.com solicitation flow), read drawings
  (drawing-upload), or sign anything on the operator's behalf.
---

# Bid Intake — read sub proposals into cited bid claims, cloud-first

Take a trade's subcontractor proposals — the PDFs a sub actually sent back against a bid package — and
turn each one into the bundle of **cited bid claims** the leveling surface reads: who bid, what
they included or excluded per scope row, the dollars they attached, their coverage, and their totals.
Each claim cites the page of the proposal it was read from. A person levels the package and signs the
bid on plumlayer.com.

Doctrine binds every stage: **agents read and judge; deterministic tooling grounds; nothing enters
untraced.** Every claim this skill writes records as your reading of one bidder's document, cited to
the page it came from. You are the reader; the MCP tools
(`render_page`, `get_page_text` for reading; `get_bid_package` for the rows and peer context;
`propose_batch` for the deposit) are the anti-hallucination anchor and the grounding
gate, not the inference engine. There is no server-side proposal reader — you drive every read, judge
every row, and author every claim.

Design lineage: `proposal-intake-design.md` (the two-pass discipline, the read gates, the verb surface
this skill drives) and `bid-leveling-surface-design.md` (the claim data model this deposits into — the
subject recipes, predicates, and value schemas). The claim shapes below mirror the `@plumlayer/contract`
bid builders exactly; that contract, not this prose, is the source of truth for a shape. Examples here
are generic — never put a real client, project, or bidder name in this file.

## Confidentiality (non-negotiable)

Proposal PDFs are confidential sub pricing. They are supplied to this skill by **local path** and are
**never committed, never copied to a tracked path, and never quoted verbatim into any file the plugin
or repo tracks.** The bytes upload to the project's private cloud bucket (project isolation + RLS) and
the claims live in the cloud MOSOT — that is fine. What must never happen is a bidder's number or name
landing in a plugin file, a commit, or a note. Reading a proposal you were handed is the job; writing
its contents into tracked source is the leak.

## Narration to the user

Keep the words honest and plain — no jargon, no invented certainty. Use plain prose in everything you
say to the user (no em dashes, no bolded emphasis words). Say:

- "uploading proposals" (upload stage)
- "reading <bidder>'s proposal" (per-proposal read)
- "N rows answered, M rows silent" (after a proposal read — never imply a silent row is a zero)
- "K proposals read, J entries to record" (before deposit)
- "declared this a revised proposal (supersedes the prior bid)" or "declared a clarification"
  (before deposit, when supersession applies — see stage 6)

Never narrate "claims", "deposit", "proposed", "grounding", "the ledger", "residue", or "the pivot"
to the user — those are machinery. What you record is the package's working data as soon as it
lands, carrying your name and the page it came from; never call it "pending review".

## What this is, and the boundary

`bid-intake` does one thing: read the proposals for **one bid package** (one trade, one project) and
deposit each bidder's bid claims against that package's existing scope rows. It does **not**:

- create the project (`project-create`) or read drawings (`drawing-upload`);
- define the bid package, or invite / manage bidders — that is the plumlayer.com solicitation flow;
  this skill reads an **existing** package's rows and adds bidder responses to them;
- mint a new scope row for proposal content that matches no known row — that is a named scope-gap
  finding in the report, never a minted `scopeItem:` subject (see the hard read rules);
- level or rank the bids (`get_bid_package` computes the leveling projection; this skill only reads it
  for context and deposits the raw response claims the leveling reads from);
- sign or submit anything — leveling the package and committing the bid stay with the operator, on
  plumlayer.com.

The pipeline: **preflight → upload/register → fetch rows + context → two-pass read (blind, then peer) →
assemble + confidence audit → declare supersession mode → deposit → report.** Each stage has gates; they
are non-negotiable and collected at the end.

## 1 · Preflight

1. **Confirm the account and project.** Call `whoami`, then `list_projects` and confirm with the user
   which project (one project = one MOSOT) these proposals belong to. Capture its `projectId`.
2. **Confirm the bid package exists.** Call `solicitation_list_packages(projectId)` and confirm the
   trade package these proposals are for is present. Capture its **CSI trade code** (e.g. `09 29 00`) —
   verbatim, spaces included, no slugging. That trade code keys the package subject and every read
   below. If no package exists for this trade, stop: this skill reads into an existing package; the
   package is defined through the plumlayer.com solicitation flow first.
3. **Take the proposal paths.** The user supplies the proposal PDFs by **local path** (one or more,
   one per bidder — or several from one bidder if a base plus revisions). Confirm which bidder each
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
   hash — never upload and read the same content twice under different filenames:
   ```bash
   for f in "$@"; do sha256sum "$f"; done | sort | uniq -c -w64
   ```
   Report which filenames collapsed to the same file and which one you kept.

## 2 · Upload and register each proposal (cloud-first)

Proposals read from the cloud, like every other Plumlayer document. Per proposal PDF that passed the
sanity check:

1. `request_file_upload(projectId, filename)` → `{fileId, signedUrl, ...}`. The server mints `fileId`
   and the storage path; you never supply either.
2. PUT the raw bytes to `signedUrl` (the bytes never pass through a tool call):
   ```bash
   curl -X PUT "$SIGNED_URL" -H "Content-Type: application/pdf" --data-binary @"$LOCAL_PDF_PATH"
   ```
3. `register_file(projectId, fileId, filename, contentType: "application/pdf", kind: "proposal")`.
   A proposal is **not** a drawing delivery — pass `kind: "proposal"` and **no `deliveryId`** (the
   `deliveryId` argument is for drawing deliveries only). Idempotent: a retried call for the same
   `fileId` returns the existing row. If it rejects `not_found` / `empty` / `oversize`, stop and report
   rather than retrying blindly.

`render_page` and `get_page_text` gate on file ownership only, so a registered proposal is immediately
readable. Keep the `fileId` for each proposal — **every claim you deposit from it cites that `fileId`
and the page** in its evidence.

Then call `register_pages(projectId)` **once** so every uploaded PDF has renderable page rows.

## 3 · Fetch the rows and the peer context

`get_bid_package(projectId, trade)` is your one source for the package's checklist. If the live call
fails, **stop and report it — do not reconstruct the rows or the package from raw `search`.** That
fallback is expressly rejected: raw-claim reconstruction re-implements supersession and the scope-item
pivot client-side and drifts from the surface.

**A second failure mode looks like success and is not: an empty checklist.** `get_bid_package` can
return normally with a defined package and `lines: []` — the package exists but no scope items are
enrolled in it yet. This is not an error the tool raises; you have to check for it. If `lines` comes
back empty, **stop and report**: "package scope not yet populated — enroll scope items via
plumlayer.com first." Never proceed to read and deposit proposals against an empty checklist — a
profile/summary-only deposit with no response claims to anchor it is a degenerate run, not a partial
one, and it hides the real blocker (no rows to answer) behind what looks like a normal intake.

- **`get_bid_package(projectId, trade)`** → the leveled projection of the package: the server-computed,
  authoritative, pre-filtered set of scope rows for this trade (`lines[]`, each with its `lineSubject` —
  a `scopeItem:` subject and the row identity you answer against, never minted by you), every current
  bidder (`bidders[].partySubject`, name, laborType, coverage), the head response per cell
  (`lines[].responses[]`, each with `partySubject`, the resolved response, and `receipt.id` — the
  current head claim id for that bidder × row), and the divergence view. **These `lines[]` are the
  checklist** — a bidder responds to these, and only these; do not derive package membership by hand
  from any other read. This is also your **pass-two peer context** and your **supersession head source**
  for existing bidders. It errors "bid package not found" if no package definition claim exists yet for
  the trade — if it does, stop and report (the package definition is a plumlayer.com step), do not fall
  back to `search`.
- **`list_scope_items(projectId)`** (optional enrichment only) → the project-wide canonical scope-item
  view. `get_bid_package`'s `lines[]` already carries what this skill needs for the checklist; reach for
  `list_scope_items` only if a specific row needs a field `lines[]` doesn't carry, never to re-derive or
  double-check package membership — that restatement of the server's own filter is exactly the kind of
  client-side drift the read verbs exist to prevent.

**Resolve the contracting party from the whole document — never from the first letterhead.** A
proposal's opening page is often not the bidder's: manufacturer quote sheets and vendor-system
printouts arrive branded with the manufacturer or the quoting software, while the actual contracting
party appears only in a forwarded cover email, a signature block, or a remit-to line deeper in the
bundle. Read the whole submission (cover email included) before deciding who is bidding. Two shapes
this takes in the real corpus:

- **Letterhead mismatch** — the front page carries a vendor or manufacturer name; the cover email or
  signature names the sub who actually carries the contract. The contracting party is the bidder; the
  vendor branding is just where their pricing came from.
- **One submission, several embedded quotes** — a single bidder's package can bundle two or more
  embedded vendor-system quotes covering complementary halves of the scope. That is **one bidder and
  one claim bundle**, with each value cited to the page of the embedded quote it was read from —
  never two bidders.

If the document leaves the contracting party genuinely ambiguous, stop and ask the user — never
guess a bidder into existence.

Then place each proposal's resolved bidder, in this order:

1. **Already a bidder on this package** → reuse that bidder's `partySubject`. This is an existing
   bidder, so supersession may apply (stage 6).
2. **Otherwise, look for the company you invited.** Call `solicitation_list_invitations` for this
   package and read the invited companies. If the proposal's contracting party is plainly one of
   them, use that company's directory id as the party: **`party:<companyId>`**. This is the identity
   the rest of the system already knows the company by, and it is what lets a filed proposal move
   that company to Bid received on the coverage board by itself. **Only the exact company id does
   that** — a name-shaped party never will.
3. **No invited company matches** → mint a stable `party:<slug>` from the bidder's company name (a
   short, stable slug, e.g. `party:acme-drywall`). A bidder who was never invited is still a real
   bidder and files normally; their proposal simply moves no funnel it was never part of.

The matching in step 2 is **your judgment, and you say so**: names differ from legal entities, a
proposal may come from a division or a DBA, and two invited companies can look alike. Match only
when you are actually confident, name the company you matched and why in your report, and fall to
step 3 rather than forcing a doubtful match. A wrong match files a real proposal against the wrong
company's record — worse than an unlinked one, which is merely incomplete. If two invited companies
are plausible, stop and ask the user; never break the tie yourself.

> Party identity was a known seam and this closes it on the intake side (the Sub-CRM owns company
> identity; the bid contract consumes it). Surface the party subject you chose per bidder in the
> report, and whether it came from an invitation or a minted slug.

## 4 · The two-pass read (the anti-anchoring discipline)

Read each proposal in **two passes in the same session**. The order is the discipline: pass one reads
each proposal **blind** so a bidder's numbers are never anchored to a peer's; pass two adds peer context
only to flag divergence, never to revise a value.

### Pass one — blind, per proposal

For each proposal, read it against **only the scope rows (stage 3) and that one proposal** — no peer
proposal, no other bidder's numbers in view. Use `render_page` (returns the page image inline; pass a
normalized `region` to zoom a table or a signature block) and `get_page_text` (exact text spans;
`hasTextLayer:false` is the honest image-only signal). Produce, for this bidder:

- **The bidder profile** — name, labor type (one of `Open Shop` / `Union` / `Prevailing Wage` /
  `Supplier`), contact, **proposal date read from the document itself**, and a revision marker if the
  document carries one (R1 / R2 / "Revised"). Never use upload time for the date.
- **Per-row responses** — for each scope row the proposal **addresses**, the response along the three
  axes plus amount and note, per the response value shape (stage 7):
  - **inclusion** — `base` (in the base bid), `adder` (a priced add), or `excluded` (not carried).
  - **routing** — `self` / `by-others` / `NIC`, when the proposal says who carries it. Distinguishes a
    true exclusion from a scope-gap the bidder routes elsewhere. Omit when it is plain base scope.
  - **amount** — the dollar figure when one is given (an adder's add, or a broken-out base cost). Omit
    when none is stated. **Never** derive a number the proposal does not state.
  - **ambiguity** — `OSV` / `TV` / `unclear` when the proposal prices a row ambiguously ("other scope
    value", "to verify", a bare "?"). An ambiguous token **never** resolves to a hard `amount`.
  - **note** — the free-note residue ("included above", "option 1", a typed comment).
- **Coverage** — did this proposal bid the whole package (`full`) or a subset (`partial`)? A `partial`
  coverage carries a human label ("Framing only") and, when the proposal names the covered rows, the
  explicit `coveredItems` subset (the `scopeItem:` subjects from stage 3).
- **Summary totals** — the entered lump figures the proposal states: `base_bid`, and optionally
  `adjustments`, `allowances_alternates` (a parallel bucket, never folded into the total), and
  `total_adj_bid`. These are read as entered, never summed by you from the rows.

Each of these carries a **receipt** (the `fileId` and page, plus a short `evidence.rationale` paraphrase
of what you read there — the only prose slot the evidence shape carries) and a **confidence** in `[0,1]`
(your read confidence, carried in `evidence.confidence`). Note per flag / value which pass produced it —
pass one for everything here.

### Pass two — peer-aware, flags only

Now, with `get_bid_package`'s peer responses in view, make a second pass over the same proposals. Pass
two may **only**:

- add or adjust **ambiguity flags** — a row you now see every peer priced but this bidder left blank is
  a sharper scope-gap signal; a token you read as plain may now read as `OSV` against the peer pattern;
- run the **miss-direction checks** — is this bidder an outlier low because they excluded a row the
  peers all carried? Flag it for review.

Pass two **must never** revise a pass-one `amount` or `inclusion` to move a bidder toward the peers.
The whole point of reading blind first is that a bidder's price stands on their own document. In the
report, state which pass produced which flag.

### Hard read rules (gates, not advice)

These are gates. Write them into every read:

- **Silence is not a claim.** A scope row the proposal does not address gets **no response claim** at
  all. Count it as silent for that bidder in the report. Never deposit a `base`/`excluded`/zero to
  represent silence — silence is unknown, and a bare grid that treats it as answered is the exact
  conflation coverage exists to prevent.
- **Proposal content matching no known row is a scope-gap finding, never a minted row.** If a proposal
  prices or excludes something that maps to none of the stage-3 scope rows, that is a **named scope-gap
  finding** in the report (a description plus the `fileId`/page it is on) — never a new `scopeItem:`
  subject this skill mints. Minting scope from a bid would let a bidder's document silently define the
  scope checklist.
- **Aggregation is narrow, stated once, and flagged per claim.** A proposal often prices one scope
  row across several of its own lines — a variant pair (a tempered option beside the standard unit),
  a split line-item pair, a companion component priced on its own line. Folding those lines into one
  row response is allowed **only** when all three hold: same bidder, same scope row (same mark), and
  the lines are complementary components of that one row's scope — never alternatives to choose
  between. Apply one consistent aggregation rule for the whole run, state it in the report, and flag
  every aggregated response (its note names the lines folded in; the receipt cites where they sit).
  Lines that belong to different rows stay split, and a line that maps to no row is a scope-gap
  finding — aggregation never absorbs it into a nearby row. When you cannot tell whether lines are
  complementary or alternative, do not fold — keep the clearest single line as the response, put the
  rest in the note, and flag the row `unclear`.
- **An ambiguous token never becomes a hard number.** `OSV` / `TV` / `?` set the `ambiguity` axis; they
  never populate `amount`.
- **No receipt, no deposit.** A value you cannot cite to a `fileId` and page is not deposited. If you
  believe a fact but cannot point at where you read it, it does not become a claim.
- **Nothing you write is a person's word.** Every claim records as your reading of the document; this
  door cannot record one as human-authored, and a human correction outranks yours on the same row.

## 5 · Assemble and audit confidence

Assemble the full claim bundle per bidder (profile, coverage, summary, and one response per answered
row). Before depositing, run a **confidence audit**: collect every read whose `evidence.confidence` is
**below 0.7** and list it in the report for human attention. A low-confidence read still deposits,
carrying its confidence and its receipt, but it is called out, not buried in a count. State the per-bidder
counts by predicate, and the silent-row count per bidder, so the deposit manifest is honest.

## 6 · Declare the supersession mode (before deposit)

If a bidder is **new** to this package (no prior claims in `get_bid_package`), there is no
supersession: deposit fresh claims, and skip to stage 7.

If a bidder **already has claims** on this package, classify the new document from **its own framing**,
not from a guess:

- **A "revised proposal" / "revised bid" / a higher revision marker → wholesale.** The revised document
  restates the bidder's whole position. Deposit a fresh response claim for every row you read from it,
  each with `supersedesId` set to that row's **current head response claim id** (from
  `get_bid_package`'s `lines[].responses[]` — the cell for this `partySubject` on that row, its
  `receipt.id`). Rows the revised proposal is now **silent** on get **no re-assertion** — their prior
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
> chronology — so the edge is load-bearing. Surface this in the proving run.

## 7 · Deposit — author the claim JSON, batch, verify

Author the claim JSON directly, matching the `@plumlayer/contract` bid builder outputs **exactly**. The
subjects are deterministic recipes; the predicates and value shapes are fixed. Get them wrong and the
claim lands on the wrong subject or fails validation.

**Subject recipes** (build from already-stable constituents — the `partySubject` from stage 3, the
package subject, and the `scopeItem:` subjects (`lineSubject`) from `get_bid_package`'s `lines[]`):

```
package subject   bidPackage:<projectId>:<trade>                        (trade = CSI code verbatim, spaces kept)
response subject   bidResponse:<partySubject>:<bidPackageSubject>:<scopeItemSubject>
summary subject    bidSummary:<partySubject>:<bidPackageSubject>
coverage subject   bidCoverage:<partySubject>:<bidPackageSubject>
profile subject    <partySubject>                                       (the party subject itself)
```

**Predicate + value per claim** (the value must satisfy the contract's zod schema — extra keys are
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

Value rules that the schema enforces — honor them at authoring time:

- `inclusion` ∈ `base | adder | excluded`; `routing` ∈ `self | by-others | NIC`; `ambiguity` ∈
  `OSV | TV | unclear`; `laborType` ∈ `Open Shop | Union | Prevailing Wage | Supplier`; coverage
  `basis` ∈ `full | partial`. No other values, ever.
- Optional fields are **omitted** when absent, never set to `null`. Every optional field in the bid
  schemas is `.optional()`, not `.nullable()` — an explicit `null` is rejected, not treated as "none."
  Omission is the only correct encoding of "not stated."
- `sourceInstrument` equals `evidence.instrument` (the builder sets it from there).
- `evidence.page` requires `evidence.fileId` — a page pointer with no file is rejected.
- For a **surgical or wholesale supersession**, add `"supersedesId": "<current head claim id>"` to the
  claim, resolved per stage 6.
- Bid claims carry **no `versionScope`** (the bid builders do not set one) — omit it.

**Batch and verify.** Pool the authored claims and call `propose_batch(projectId, claims)` in batches
of **≤50** claims (the door accepts up to 500, but ≤50 keeps each read faithful and count-verifiable).
It is atomic — one bad entry rejects the whole batch and names the index. Transport every entry
**verbatim**; never re-type a value from memory. **Verify:** the returned `count` must equal the number
of entries you sent in that batch. If it does not, **stop and report** the discrepancy — never retry
with a reconstructed or guessed correction.

**Recount before you confirm.** Any count you are about to restate as checked — rows answered, rows
silent, claims per predicate, entries in a batch — gets an explicit fresh recount against its source
at the moment you restate it. Echoing a number you computed earlier (or that the user read back to
you) and calling it "confirmed" is not verification; the word "confirmed" is earned by the recount
that precedes it, every time.

## 8 · Report and hand off

The run report **is** the manifest. State, plainly:

- **Per bidder:** the party subject you used, claim counts **by predicate** (profile / responses /
  coverage / summary), the **declared supersession mode** (new / wholesale / surgical) and what it
  superseded, and the **silent-row count** (rows the proposal did not address).
- **Scope-gap findings:** proposal content that matched no known row, each with its description and
  `fileId`/page — the pile a human should reconcile against the scope list, not something this skill
  minted.
- **Low-confidence reads:** every value below 0.7 confidence, called out for review.
- **Pass attribution:** which flags pass one produced versus pass two.
- **Deposit verification:** each batch's sent-vs-returned count, confirmed equal.

Then point the user at the **package view on plumlayer.com** to review and level. The numbers are
readable there now, each with the proposal page behind it; the bid itself is theirs to sign.

## Gates (non-negotiable)

- Every claim's evidence cites a `fileId` and page of a proposal you actually read; no receipt → no
  deposit.
- Silence is never a claim; an unaddressed row is counted silent, never deposited as a value.
- Proposal content matching no scope row is a named scope-gap finding, never a minted `scopeItem:`.
- The contracting party is resolved from the whole document (cover emails, signature blocks,
  letterhead mismatches), never from the first letterhead; a bundle of embedded vendor quotes under
  one party is one bidder; genuinely ambiguous identity stops and asks.
- Line aggregation only ever folds same-bidder, same-row, complementary-component lines, under one
  stated rule, flagged per aggregated response — never across rows, and never to absorb a scope-gap.
- Any count restated as "confirmed" gets an explicit fresh recount against its source first; an
  echoed number is never verification.
- An ambiguous token (`OSV` / `TV` / `?`) never resolves to a hard `amount`.
- Pass two never revises a pass-one amount or inclusion toward the peers — it only flags.
- Supersession mode is read from the document's own framing; ambiguous framing stops and asks. The
  declared mode is confirmed with the user before deposit.
- Rows a wholesale revision is silent on lapse (no re-assertion); a surgical delta touches only named
  rows.
- Claim JSON matches the `@plumlayer/contract` bid shapes exactly (recipes, predicates, enums,
  `.strict()` values).
- Deposit is verbatim, count-verified transport in ≤50-claim batches; a count mismatch stops the run.
- Nothing this skill writes carries a person's authority or a signature; leveling the package and
  submitting the bid stay with the operator.
- `get_bid_package` is the row + context source; a failure stops the run and is reported — never a
  raw-`search` reconstruction of the package, and never a hand-derived membership filter over
  `list_scope_items` as a substitute.
- A `get_bid_package` success with `lines: []` is not a green light — the checklist is empty, so stop
  and report rather than depositing a degenerate profile/summary-only run with no response claims.
- Proposal specifics live in the cloud MOSOT and in local files; they never enter a tracked/committed
  plugin or repo file, and never appear verbatim in this skill's own text.

## Bundled vs. config

This skill generalizes once. The per-job delta — which project, which trade package, which proposal
folder — is **data** the user supplies at run time, never an edit to the skill. A new intake job never
edits `SKILL.md`; it runs the same pipeline against new paths.

## Deferred / for the proving run to decide (named, not skipped silently)

- **Party identity resolution — SETTLED 2026-08-07 (PLU-874), see stage 3.** The bridge is the
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
  definition — confirm where the definition is expected to come from.
- **Image-only / scanned proposals.** `hasTextLayer:false` means no vector text; read what you can from
  the render and flag the rest honestly (no OCR dependency here — that is a separate, deferred concern).
