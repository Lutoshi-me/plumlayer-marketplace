---
name: setup
description: >
  One-time Plumlayer operator setup — capture your company/operator profile and defaults once, so the
  other skills (project-create, guarded scope handoff, the doc generators) are personalized without
  hardcoding any confidential config into the plugin. Trigger on first install, "set up Plumlayer",
  "configure my company", "onboard me", "/setup", or whenever project-create finds no operator profile.
  Writes a local ~/.plumlayer/operator.json that is NEVER committed — the interview itself is the
  confidentiality scrub: your specifics live in your environment, the shared plugin stays generic.
---

# Plumlayer Setup — your operator profile (run once)

## Talk to your user like an estimator

Verbs, claims, and trust classes are machinery for you, never words the user reads. Speak estimator
words to them: project record, entry, sheet, set, scale, scope item, bid response, flagged item,
trail. Never say to the user: claim, deposit, predicate, subject, proposed, governing, trust class,
supersede, promote, reconcile, QA, sheet type as "sheetType", grounding, residue, or any raw verb or
field name. Translate instead: a value you replaced is "I updated my earlier read"; a machine
mis-read you caught is "the automatic scan grabbed the wrong text, so I read the sheet and flagged
it for you to set on the site"; cross-checking the index is "checking the drawing list against the
actual sheets". Plain prose, no em dashes, no bolded emphasis words. Full guidance is in the
project-record skill's Words section.

This skill captures **who you are and how you usually work** so every other Plumlayer skill can be
personalized to you without ever baking your company's details into shared, version-controlled plugin
code. **The interview is the scrub:** the plugin ships generic; your specifics live only in a local
config file in your environment. Re-run it any time to review or update.

> **Doctrine:** confidential operator/company details go in your **local** `~/.plumlayer/operator.json`
> and **never** into a tracked or committed file, and never into the plugin itself. This skill writes
> exactly one local file and nothing else.

## When to run

- **First install**, or any time you want to change your defaults.
- **Automatically suggested** by `project-create` when it finds no operator profile — running `setup`
  first means you won't be re-asked your company/role/defaults on every new project.

## Step 1 — Check for an existing profile

```bash
CONFIG="$HOME/.plumlayer/operator.json"
[ -f "$CONFIG" ] && echo "FOUND — reviewing/updating" || echo "NONE — creating fresh"
ls -la "$CONFIG" 2>/dev/null
```

- **If it exists:** read it, show the user the current values, and ask what to change. **Update in
  place — never silently overwrite.** Preserve fields the user doesn't touch.
- **If not:** run the interview fresh.

## Step 2 — The interview (operator-level only)

Ask conversationally, in small groups; accept "skip" for anything optional. Nothing here is
project-specific — that's `project-create`'s job. Keep it short.

**Identity**
- Company / operator name.
- Your role: `GC` / `CM` / `subcontractor` / `owner-rep` / `architect` / `other`.
- Trade focus — the disciplines or trade packages you typically bid or self-perform (drives the
  default scope lenses). Skip if you cover everything.
- Region (e.g. "Massachusetts / New England") and unit system (`imperial` / `metric`).

**Defaults** (sensible starting points project-create can override per job)
- Default delivery method (`DBB` / `design-build` / `CM-at-risk` / …).
- Default project type (e.g. `interior fit-out`, `ground-up`, `renovation`).
- Scope preferences for the future PLU-274 engine — the trades/packages you usually care about.
  Do not revive the removed route-first lens data as a production fan-out path.
- Default scope grain preference, if useful later: `bid` (hard-bid / precon, coarser) or `ca`
  (awarded / construction-admin, finer). The guarded `/scope-run` path may ignore this until PLU-274.

**Branding** (optional, forward-looking — for the document-generator skills when they ship)
- Logo path / letterhead reference. Optional; leave null if you're not using doc generators yet.

## Step 3 — Confirm and write

Show the assembled JSON, confirm with the user, then write it. **Do not write until they confirm.**

```bash
mkdir -p "$HOME/.plumlayer"
# write the confirmed JSON to "$CONFIG"
```

Schema (`~/.plumlayer/operator.json`):

```json
{
  "operator": {
    "company": "<company / operator name>",
    "role": "GC | CM | subcontractor | owner-rep | architect | other",
    "tradeFocus": ["<discipline or package>", "..."],
    "region": "<region>",
    "units": "imperial | metric"
  },
  "defaults": {
    "deliveryMethod": "<DBB | design-build | CM-at-risk | ...>",
    "projectType": "<interior fit-out | ground-up | renovation | ...>",
    "scopeLenses": ["<lens-key>", "..."],
    "grainLevel": "bid | ca"
  },
  "branding": {
    "logoPath": null,
    "letterhead": null
  },
  "_meta": {
    "version": 1,
    "note": "Local Plumlayer operator profile. NEVER commit. Written by the `setup` skill; read by project-create and future scope workflows for personalized defaults. The legacy route-first /scope-run path is guarded by PLU-323."
  }
}
```

## Step 4 — Report

Tell the user: the profile is saved at `~/.plumlayer/operator.json`, that it's local-only and never
committed, and that `project-create` will now reuse these defaults so each new project only asks for
project-specific facts. Point them at `/project-create` to start their first project.

## Discipline (non-negotiable)

- The profile lives **only** at `~/.plumlayer/operator.json`. Never write operator/company specifics
  into the plugin directory, the project repo, or any tracked/committed file.
- This skill writes exactly one local file. It makes **no** cloud or MCP calls — it touches no MOSOT.
- Re-runnable: always review-and-update an existing profile rather than clobbering it.
