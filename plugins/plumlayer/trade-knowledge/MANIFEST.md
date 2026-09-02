# Trade knowledge base: manifest

**Knowledge version: `6cc73340`**. This is the version string every convention-line record cites
(`sourceInstrument: "trade-convention:<trade>@6cc73340"`, per the `scope-run` skill's convention-line
mandate). This pin changes only when the trade files themselves change; plugin releases that don't
touch the trade files don't move it.

- Trade files: 45 (one per trade; the file list below).
- Source: distilled from a real subcontractor-quote corpus (proposals and matching estimator
  leveling workbooks across multiple multifamily projects in one regional market), scrubbed of all
  identifying data: no company, person, or project names, no addresses, no dollar figures (cost
  signal rides as ratios and multiples). Confidentiality-reviewed before first shipping.
- Content-defining source snapshot: commit `6cc73340` of the source corpus repository.
- Copied into this plugin.

Forty-three of these files were mined from one corpus of four projects. `structural-steel` was the
first mined from a much larger one, about twenty projects and thirty-four pricing rounds, by several
readers over separate cohorts rather than one reader over a trade, and `drywall` is the first amended
in place the same way, from twenty-five projects and forty-one pricing rounds. Each of those two
coverage sections says what that buys and what it does not, and their coverage statements are not
comparable with the other forty-three.

## What a trade file carries

Each trade file is the self-contained, agent-facing knowledge a scope reader loads before reading
drawings for that trade: how the trade bids and splits itself in the market, scope grain rules
(what earns its own line vs. rides in a description, and the structural gap list the emit mandate
fires on), exclusions and their usual counterparties, furnish/install seams, convention work the
drawings will not say, pricing conventions as ratios, and an honest coverage statement naming what
the corpus did and did not support.

Trade files are living documents: a human review pass is the trust mechanism, and new corpus rounds
amend them in place at the source, after which this copy refreshes and the knowledge version
moves to the new content-defining snapshot.

## Trade files

abatement, acoustic-ceilings, appliances, casework, concrete, countertops, demo, dfh, drywall,
earthwork, electrical, elevators, final-cleaning, finish-carpentry, fire-protection, fireproofing,
flooring, glazing, gypsum-underlayment, hvac, insulation, landscaping, low-voltage, masonry,
millwork, misc-metals, overhead-coiling-doors, painting, plumbing, prefab-balconies,
roof-anchors-fall-protection, roofing, rough-carpentry, shower-doors, siding, signage,
smoke-curtains, soe, specialties, structural-steel, tiling, trash-chutes, waterproofing,
window-treatments, windows

Not yet mapped (no or near-no corpus): utilities as a standalone package, jobsite requirements /
Division 01, pools and water features, fireplaces, site furnishings, EV charging as a package,
tower crane / hoisting. A reader hitting one of these trades creates at best judgment where no trade
file covers it, and raises the grain question, per the `scope-run` skill's mandates.
