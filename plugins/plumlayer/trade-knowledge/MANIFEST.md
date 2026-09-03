# Trade knowledge base: manifest

**Knowledge version: `be7c367a`**. This is the version string every convention-line record cites
(`sourceInstrument: "trade-convention:<trade>@be7c367a"`, per the `scope-run` skill's convention-line
mandate). This pin changes only when the shipped files themselves change; plugin releases that
don't touch them don't move it.

- Trades: 45, each with a hints file and a convention table (the trade list below).
- Source: distilled from a real subcontractor-quote corpus (proposals and matching estimator
  leveling workbooks across multiple multifamily projects in one regional market), scrubbed of all
  identifying data: no company, person, or project names, no addresses, no dollar figures (cost
  signal rides as ratios and multiples). Confidentiality-reviewed before first shipping.
- Content-defining source snapshot: commit `be7c367a` of the source corpus repository.
- Copied into this plugin.

What each hints file rests on is stated on its own last line, the coverage line, which says how
many projects it was written from and whether it has been mined again since. The evidence base is
not the same for every trade and the coverage lines are not comparable with each other, so read
the one for the trade in hand rather than a figure for the set.

## What the two files carry

`hints/<trade>.md` is what a scope reader loads before it reads a sheet for that trade: a title
line, then one instruction per line about something it will actually see, then the coverage line.
Which package owns the work at a seam and the named cases where the reader tags two, and the few
places this trade's rows split or collapse differently from the general grain. Nothing else earns
a line. Each file is at most twenty hint lines and 2,400 characters, and the cut script refuses one
over either bound rather than trimming it. A window 1 pass carries up to ten of these.

`conventions/<trade>.md` is a title line and one table with four columns: `name` (what is done, to
what, where, the way a sub says it, under eighty characters), `category` (the section heading an
estimator's checklist would use), `note to bidder` (one sentence, which goes to `notesExternal`),
and `applies when` (`any`, or a short condition, which goes to `notesInternal` as a watch item
where it is not `any`). The pass runner records every row once per pass; a reader never opens the
file. A trade with no convention rows carries the title line and an empty table.

Both are living documents: a human review pass is the trust mechanism, and new corpus rounds amend
them in place at the source, after which this copy refreshes and the knowledge version moves to the
new content-defining snapshot.

## Trade files

abatement, acoustic-ceilings, appliances, casework, concrete, countertops, demo, dfh, drywall,
earthwork, electrical, elevators, final-cleaning, finish-carpentry, fire-protection, fireproofing,
flooring, glazing, gypsum-underlayment, hvac, insulation, landscaping, low-voltage, masonry,
millwork, misc-metals, overhead-coiling-doors, painting, plumbing, prefab-balconies,
roof-anchors-fall-protection, roofing, rough-carpentry, shower-doors, siding, signage,
smoke-curtains, soe, specialties, structural-steel, tiling, trash-chutes, waterproofing,
window-treatments, windows

Not yet mapped (no or near-no corpus): utilities as a standalone package, load-bearing light
gauge framing and prefabricated wall panels, firestopping as its own package, fire alarm as its
own package, jobsite requirements / Division 01, pools and water features, fireplaces, site
furnishings, EV charging as a package, tower crane / hoisting. A reader hitting one of these
trades creates at best judgment where no hints file covers it, and raises the grain question, per
the `scope-run` skill's mandates.
