# Trade knowledge base: manifest

**Knowledge version: `83be34d`**. This is the version string every convention-line record cites
(`sourceInstrument: "trade-convention:<trade>@83be34d"`, per the `scope-run` skill's convention-line
mandate). This pin changes only when the entries themselves change; plugin releases that don't touch
the entries don't move it.

- Entries: 44 (one per trade; the file list below).
- Source: distilled from a real subcontractor-quote corpus (proposals and matching estimator
  leveling workbooks across multiple multifamily projects in one regional market), scrubbed of all
  identifying data: no company, person, or project names, no addresses, no dollar figures (cost
  signal rides as ratios and multiples). Confidentiality-reviewed before first shipping
  (2026-08-13).
- Content-defining source snapshot: commit `83be34d` (2026-08-01) of the source corpus repository.
- Copied into this plugin: 2026-08-13.

## What an entry carries

Each entry is the self-contained, agent-facing knowledge a scope reader loads before reading
drawings for that trade: how the trade bids and splits itself in the market, scope grain rules
(what earns its own line vs. rides in a description), exclusions and their usual counterparties,
furnish/install seams, convention work the drawings will not say (the lines the emit mandate
fires on), pricing conventions as ratios, and an honest coverage statement naming what the corpus
did and did not support.

Entries are living documents: a human review pass is the trust mechanism, and new corpus rounds
amend them in place at the source, after which this copy refreshes and the knowledge version
moves to the new content-defining snapshot.

## Entries

abatement, acoustic-ceilings, appliances, casework, concrete, countertops, demo, dfh, drywall,
earthwork, electrical, elevators, final-cleaning, finish-carpentry, fire-protection, fireproofing,
flooring, glazing, gypsum-underlayment, hvac, insulation, landscaping, low-voltage, masonry,
millwork, misc-metals, overhead-coiling-doors, painting, plumbing, prefab-balconies,
roof-anchors-fall-protection, roofing, rough-carpentry, shower-doors, siding, signage,
smoke-curtains, soe, specialties, tiling, trash-chutes, waterproofing, window-treatments, windows

Not yet mapped (no or near-no corpus): utilities as a standalone package, jobsite requirements /
Division 01, pools and water features, fireplaces, site furnishings, EV charging as a package,
tower crane / hoisting, structural steel as its own package (misc-metals holds the boundary).
A reader hitting one of these trades runs entry-silent: mint at best judgment and flag the grain
as unspecced, per the `scope-run` skill's mandates.
