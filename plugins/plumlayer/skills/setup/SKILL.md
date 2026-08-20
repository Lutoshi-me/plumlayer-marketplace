---
name: setup
description: >
  One-time Plumlayer operator setup: capture your company and operator profile and defaults once, so
  every other skill is personalized without hardcoding any confidential config into the plugin.
  Trigger on first install, "set up Plumlayer", "configure my company", "onboard me", "/setup", or
  whenever project-create finds no operator profile. Writes a single local file,
  ~/.plumlayer/operator.json, and makes no cloud or MCP calls. Does not create a project (that is
  project-create) or touch the project record.
---

# Plumlayer setup: your operator profile (run once)

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

This skill captures who you are and how you usually work so every other Plumlayer skill can be
personalized to you without ever baking your company's details into shared, version-controlled plugin
code. The interview is the scrub: the plugin ships generic; your specifics live only in a local
config file in your environment. Re-run it any time to review or update.

> **Doctrine:** confidential operator/company details go in your **local** `~/.plumlayer/operator.json`
> and **never** into a tracked or committed file, and never into the plugin itself. This skill writes
> exactly one local file and nothing else.

## When to run

- **First install**, or any time you want to change your defaults.
- **Automatically suggested** by `project-create` when it finds no operator profile, since running
  `setup` first means you won't be re-asked your company/role/defaults on every new project.

## 1. Check for an existing profile

```bash
CONFIG="$HOME/.plumlayer/operator.json"
[ -f "$CONFIG" ] && echo "FOUND, reviewing/updating" || echo "NONE, creating fresh"
ls -la "$CONFIG" 2>/dev/null
```

- **If it exists:** read it, show the user the current values, and ask what to change. **Update in
  place, never silently overwrite.** Preserve fields the user doesn't touch.
- **If not:** run the interview fresh.

## 2. The interview (operator-level only)

Ask conversationally, in small groups; accept "skip" for anything optional. Nothing here is
project-specific, that's `project-create`'s job. Keep it short.

**Identity**
- Company / operator name.
- Your role: `GC` / `CM` / `subcontractor` / `owner-rep` / `architect` / `other`.
- Trade focus, the disciplines or trade packages you typically bid or self-perform (drives the
  default scope lenses). Skip if you cover everything.
- Region (e.g. "Massachusetts / New England") and unit system (`imperial` / `metric`).

**Defaults** (sensible starting points project-create can override per job)
- Default delivery method (`DBB` / `design-build` / `CM-at-risk` / …).
- Default project type (e.g. `interior fit-out`, `ground-up`, `renovation`).
- Scope preferences, the trades and packages you usually care about. `scope-run`, the live
  scope-item-first engine, does not read this field today: it derives its package split fresh each
  run from the spec table of contents and the trade knowledge base, so treat this as a note for
  later use, not a current input.
- Default scope grain preference, if useful later: `bid` (hard-bid or precon, coarser) or `ca`
  (awarded or construction-admin, finer). `scope-run` does not read this field today either.

**Branding** (optional, forward-looking, for the document-generator skills when they ship)
- Logo path / letterhead reference. Optional; leave null if you're not using doc generators yet.

## 3. Confirm and write

<!-- user-facing -->
Summarize the profile back to the user in plain language, not raw JSON, for example: "Here's what
I've got: Acme Construction, GC, focused on interior fit-out work in Massachusetts, defaulting to
CM-at-risk projects and a coarser bid-level scope grain. Sound right?"
<!-- /user-facing -->
Confirm each part they want
changed, then write the file. **Do not write until they confirm.**

```bash
mkdir -p "$HOME/.plumlayer"
# write the confirmed JSON to "$CONFIG"
```

Audience: agent. `operator.json` is read by `project-create` and the scope workflows to pre-fill
defaults; its values reach the user only through the plain-language summary in step 3 and the
report in step 4, and whatever crosses into that summary or report becomes user-facing at the
crossing and is translated there.

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
    "note": "Local Plumlayer operator profile. NEVER commit. Written by the `setup` skill; read by project-create and the scope workflows for personalized defaults."
  }
}
```

## 4. Report

<!-- user-facing -->
Tell the user: the profile is saved at `~/.plumlayer/operator.json`; give a one-line summary of what's
in it (company, role, delivery default, grain default) so they know exactly what they configured;
confirm it's local-only and never committed; and that `project-create` will now reuse these defaults
so each new project only asks for project-specific facts. Point them at `/project-create` to start
their first project.
<!-- /user-facing -->

## Discipline (non-negotiable)

- The profile lives **only** at `~/.plumlayer/operator.json`. Never write operator/company specifics
  into the plugin directory, the project repo, or any tracked/committed file.
- This skill writes exactly one local file. It makes **no** cloud or MCP calls; it touches no project record.
- Re-runnable: always review-and-update an existing profile rather than clobbering it.
