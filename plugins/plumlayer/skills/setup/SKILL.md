---
name: setup
description: >
  One-time Plumlayer user setup: capture your company and user profile and defaults once, so
  every other skill is personalized without hardcoding any confidential config into the plugin.
  Trigger on first install, "set up Plumlayer", "configure my company", "onboard me", "/setup", or
  whenever project-create finds no user profile. Writes a single local file,
  ~/.plumlayer/operator.json, and makes no cloud or MCP calls. Does not create a project (that is
  project-create) or touch the project record.
---

# Plumlayer setup: your user profile (run once)

This skill captures who you are and how you usually work so every other Plumlayer skill can be
personalized to you without ever baking your company's details into shared, version-controlled plugin
code. The interview is the scrub: the plugin ships generic; your specifics live only in a local
config file in your environment. Re-run it any time to review or update.

> **Doctrine:** confidential user/company details go in your **local** `~/.plumlayer/operator.json`
> and **never** into a tracked or committed file, and never into the plugin itself. This skill writes
> exactly one local file and nothing else.

## When to run

- **First install**, or any time you want to change your defaults.
- **Automatically suggested** by `project-create` when it finds no user profile, since running
  `setup` first means you won't be re-asked your company/role/defaults on every new project.

## 1. Check for an existing profile

```bash
CONFIG="$HOME/.plumlayer/operator.json"
[ -f "$CONFIG" ] && echo "FOUND, reviewing/updating" || echo "NONE, creating fresh"
ls -la "$CONFIG" 2>/dev/null
```

- **If it exists:** read it, show the user the current values, and ask what to change. **Update in
  place, never silently overwrite.** Preserve fields the user doesn't touch. If the existing file
  carries keys the current schema no longer defines, ignore them and drop them on rewrite; never
  error on them.
- **If not:** run the interview fresh.

## 2. The interview (user-level only)

Ask conversationally, in small groups; accept "skip" for anything optional. Nothing here is
project-specific, that's `project-create`'s job. Keep it short.

**Identity**
- Company / user name.
- Your role: `GC` / `CM` / `subcontractor` / `owner-rep` / `architect` / `other`.
- Region (e.g. "Massachusetts / New England") and unit system (`imperial` / `metric`).

**Defaults** (sensible starting points project-create can override per job)
- Default delivery method (`DBB` / `design-build` / `CM-at-risk` / …).
- Default project type (e.g. `interior fit-out`, `ground-up`, `renovation`).

## 3. Confirm and write

<!-- user-facing -->
Summarize the profile back to the user in plain language, not raw JSON, for example: "Here's what
I've got: Acme Construction, GC, focused on interior fit-out work in Massachusetts, defaulting to
CM-at-risk projects. Sound right?"
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
    "company": "<company / user name>",
    "role": "GC | CM | subcontractor | owner-rep | architect | other",
    "region": "<region>",
    "units": "imperial | metric"
  },
  "defaults": {
    "deliveryMethod": "<DBB | design-build | CM-at-risk | ...>",
    "projectType": "<interior fit-out | ground-up | renovation | ...>"
  },
  "_meta": {
    "version": 1,
    "note": "Local Plumlayer user profile. NEVER commit. Written by the `setup` skill; read by project-create and the scope workflows for personalized defaults."
  }
}
```

## 4. Report

<!-- user-facing -->
Tell the user: the profile is saved at `~/.plumlayer/operator.json`; give a one-line summary of what's
in it (company, role, delivery default, project type default) so they know exactly what they configured;
confirm it's local-only and never committed; and that `project-create` will now reuse these defaults
so each new project only asks for project-specific facts. Point them at `/project-create` to start
their first project.
<!-- /user-facing -->

## Discipline (non-negotiable)

- The profile lives **only** at `~/.plumlayer/operator.json`. Never write user/company specifics
  into the plugin directory, the project repo, or any tracked/committed file.
- This skill writes exactly one local file. It makes **no** cloud or MCP calls; it touches no project record.
- Re-runnable: always review-and-update an existing profile rather than clobbering it.
