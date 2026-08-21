# Low voltage, telecommunications and security

Trade knowledge for an agent about to read a drawing set and produce scope for the low voltage
family: structured cabling, access control, surveillance, intercom, and their neighbours. Everything
here is learned from real subcontractor proposals and estimator leveling sheets. Where real
proposals have not shown something, this file says so.

Read this before reading the drawings. The first thing to know is that this family is bid as one
market and leveled as nothing at all: no telecommunications and no security tab exists in any
leveling workbook in the corpus, on any project, including one where the family totals over a
million. There is no scope row taxonomy for this trade anywhere, which is exactly why its boundaries
are the least settled of any trade in this cluster.

---

## 1. Trade identity and packaging

The family is anchored in two spec divisions, communications and electronic safety and security, and
its work appears on a technology drawing series and sometimes on a separate electronic security
series. Which series carries the security work is project specific: on one project the security bid
cited the technology sheets, and on another the security bid cited a dedicated security series while
the telecommunications bid cited the technology series. Find both series before scoping.

The family decomposes into six systems, and the only document in the corpus that shows this is a one
page proposal from a project electrician listing all six with a price each:

- Fire alarm, which on that project was roughly three fifths of the whole family.
- Telephone and data, meaning structured cabling.
- Area of rescue assistance, the emergency communication stations at stairs and elevators.
- Emergency responder radio amplification, the public safety radio distribution system.
- Intercom.
- Security and card access, meaning access control and surveillance together.

That decomposition is the single most useful fact in this file, because the market packages those
six in every combination. Understand which combination a given proposal covers before comparing it
to anything.

The bidder kinds:

- The electrical contractor. Bids all six systems as one proposal with one line each, usually the
  same electrician bidding the power package. Its numbers include the fire alarm, which no
  specialist bid does.
- The low voltage systems integrator. Bids structured cabling and security, either as two documents
  with separate quote numbers or as one document with two base bids. This is the reference bidder.
- The electrical contractor with a low voltage division. Bids telecommunications and security as two
  separately numbered proposals that cross-reference each other, so an exclusion in one is resolved
  by the other.
- The cabling contractor. Bids structured cabling only, by drop count.
- The security specialist. Bids access control, surveillance and electrified locks, often as the
  owner's chosen integrator supplying equipment that another contractor installs.
- The equipment supplier, quoting fire alarm or intercom hardware through the electrician rather
  than bidding as a subcontractor.

Collapse attractors:

- Access control and surveillance travel together, effectively always, and usually with the intercom.
- Intercom collapses into security. Wireless intercom platforms have largely replaced the wired
  intercom riser, which removes a cabling scope that older sets still draw.
- Structured cabling and the camera cabling collapse together, except where they do not, which is the
  most damaging exception in the trade. See section 5.
- Certification testing of every copper and fiber run, with a written record and as-built plans.

Specialty carve-outs:

- Fire alarm, which leaves the family whenever a specialist bids it and stays inside it whenever the
  electrician bids the lot.
- Building controls, which are quoted by controls manufacturers under the mechanical division and
  should never be scoped here despite occasionally being filed under a low voltage token.
- Audio visual, excluded by name by most bidders.
- Network switches and active electronics, excluded by every bidder seen without exception. These
  are the owner's or its information technology vendor's.
- Temporary site security, which is not this trade at all. See the boundary note at the end of
  section 5.

---

## 2. How the market bids

There are two proposal shapes and they are not comparable to each other without work.

The first is the device count list. Each outlet or device type gets a line with a quantity and a
description: access point locations, one port and two port data locations, camera outlets,
residential media enclosures, television outlets, equipment racks, fiber runs. Then one price. The
best of these also name cable category, rating and whether each run is labelled, terminated and
tested. This shape is comparable between bidders once the counts are normalized, and it is the shape
to ask for.

The second is the prose scope with assumptions. A paragraph or two describing what is included, a
paragraph of exclusions, and one price, with the quantity basis stated as an assumption in the middle
of a sentence. One such proposal states that the riser does not indicate which cables run to the
unit media panels and that the drawings do not specify the cable type at the access points, and then
assumes one data cable and one coaxial cable per media panel and one data cable per access point.
On a two hundred unit building that single sentence is the entire quantity basis of the bid, and a
competitor assuming two data cables per panel has produced a different number for a reason that
appears nowhere in either total.

One bidder in the corpus publishes a full bill of materials with per-device unit prices, which is
the only place in this cluster where component-level pricing is visible at all.

What a proposal will reliably state:

- The basis drawings by sheet series and the specification divisions, with dates.
- Its pathway exclusions, at length. See section 3.
- Whether the labor is union, and which local, where it is.
- Permit inclusion, which most carry.
- Certification testing and the record it produces.

What a proposal will reliably not state:

- Lead times, on any system, in any proposal seen.
- Labor content or crew size.
- Which of the six systems it is not bidding, unless the omission happens to be listed.
- Whether it is furnishing or only installing the security equipment, except in one qualification
  line buried at the end. See section 5.

Revision habits. This trade's revisions are quantity churn under a stable total, which is the exact
inverse of what a leveler expects.

- One bidder's two rounds on the same project held every line description identical while the
  wireless access point count fell from thirty-three to fourteen and the television outlet count rose
  by about ten percent, and the total rose about two percent. A total diff sees nothing. A device
  diff sees the whole thing.
- Another bidder filed three rounds over five weeks in which not one counted quantity moved, and the
  changes were two patch cord lines disappearing entirely and a media enclosure description quietly
  losing the switch it had previously carried. Diffing totals and diffing counts both find nothing;
  only diffing the inclusion sentences finds it.
- The drawing list a bid cites can grow by more than a dozen sheets between rounds while the cited
  date stays the same, so the cited basis is not always a reliable round key either.

---

## 3. Scope grain rules

There is no scope sheet for this trade in the corpus, so the row set below is built from what the
proposals themselves enumerate and from what their exclusions reveal. Target roughly forty-five to
sixty lines, which is more than any other trade in this cluster and reflects that six systems are
being scoped at once.

### What enumerates

By system, first. Give each of the six systems its own block with its own subtotal asked for
explicitly, because the market packages them differently and a family total cannot be split
afterwards.

Within structured cabling:

- Each outlet type as its own line with a count and a port count: single port data, two port data,
  television outlets, camera outlets, wireless access point locations, and wall versus floor
  locations. Distinguish indoor from outdoor access points; they are different drops.
- Residential media enclosures as their own line with a count, and separately whether the enclosure
  carries a switch inside it. That switch has disappeared from a proposal mid-ladder.
- The cable running to each unit, as its own line, naming category, rating and count per unit. This
  is the assumption that carries the whole residential quantity and it must be stated, not assumed.
- Microduct or pathway to each unit as its own line.
- Backbone fiber as its own line with strand count, mode, rating and the run count from the main
  frame to each intermediate frame.
- Patch panels, adapter plates and horizontal wire management as their own lines.
- Equipment racks as their own lines, split between wall mount and floor standing four post.
- Patch cords as their own line with lengths and counts at both the panel and user ends. They have
  vanished from a base bid between rounds.
- Certification testing and the deliverable record, as its own line.
- Labelling of outlets and patch panels, as its own line.

Within security:

- Card reader door packages as their own lines, split by mount type and by single versus double door,
  with counts. A double door is not two single doors.
- Elevator readers, garage door readers and roof readers as their own lines.
- Door contacts and position switches as their own line with counts.
- Reader controllers, interface modules and enclosure packages as their own lines with counts, since
  these are the head end and they scale in steps rather than continuously.
- Credentials as their own line with a count. One bidder includes a thousand proximity credentials
  per the specification and no other mentions credentials at all.
- Cameras as their own lines by type: interior fixed dome, exterior fixed dome, interior and exterior
  fisheye, multisensor, and elevator cameras. The type mix is the whole cost.
- Viewing workstations as their own line.
- The cabling to the cameras as its own explicit line, with its owner named. See section 5.
- Intercom equipment, its head end and whether it is wired or wireless, as its own line.
- Electrified lock hardware as its own line, with the furnish and install split stated. See section 5.
- Programming, testing and commissioning as their own line, with the party that leads it named.

For the remaining systems:

- Fire alarm devices, panel, programming, battery calculations, acceptance testing visits and
  points-list responsibility as separate lines.
- Area of rescue stations as their own line with a count.
- Emergency responder radio amplification as its own line, including the survey that sizes it.

### What collapses

- Cable, connectors, jacks and faceplates collapse into the drop they serve.
- The head end enclosure's internal components collapse into the enclosure package.
- Individual room enumeration collapses into the outlet type and count.
- Submittals, as-builts and record documentation collapse into one line per system.

### The include or exclude click test

The test fires hardest on the in-unit boundary, on the camera cabling, on the electrified locks, on
the pathway, and on whether equipment is furnished or only installed. It fires hardly at all on the
cable and jack itself.

Silence is a very strong finding in this trade because the proposals are short relative to the scope
they cover. A proposal that does not mention media enclosures on a residential project is not
carrying them.

### The structural gap list

This is the longest structural gap list in the cluster and it is almost entirely pathway. The
following are excluded by essentially every low voltage bidder seen, and each belongs to another
package:

- All conduit, raceway, flexible conduit and cable tray, common area and riser alike.
- Coring, sleeving and firestop sleeves, other than in and out of the telecom rooms in one bidder's
  case.
- Certified firestopping of any penetration outside the telecom rooms.
- Work, junction, floor and poke-through boxes.
- Line voltage power, both temporary and permanent, and every connection.
- Grounding backbone and bus bars, though one bidder includes grounding, so this one genuinely flips.
- Plywood backboards in the telecom rooms.
- Cutting, patching and painting.
- Door preparation and door hardware.
- Fire alarm relay modules, where fire alarm is not in the package.
- Active network switches and electronics.
- Uninterruptible power supplies and power distribution units.
- Utility fiber to the property line, and the service provider's own work.
- Lifts.
- Debris removal to the chutes or dumpsters.
- Payment and performance bonds.

---

## 4. Typical exclusions and qualifications

The pathway list above is boilerplate in the strict sense: it is reproduced almost verbatim by
unrelated competitors and by the same competitor across projects a year apart. It carries no project
information. Read it once to build the trade map and then read the qualifications instead, because in
this trade the qualifications are where the scope actually lives.

The qualifications that are really scope:

- A sentence excluding all work within the living units. This is the largest single scope statement
  in the trade. One electrician's telephone and data line is roughly two fifths of a specialist's on
  the same project entirely because of it, while the specialist carries a media enclosure and two
  television outlets in every apartment. Nothing else in either document says so.
- A sentence stating that a named third party will provide all equipment and this bidder will provide
  cable and consumables only. That converts a furnish and install bid into an install only bid, and
  it sits on the same ranking as furnish and install competitors with nothing but that line to
  distinguish it.
- A sentence stating that camera network cabling is by others including the head end termination.
  That removes the cabling from a surveillance number that still reads as a complete surveillance
  system.
- A sentence stating that the smart locks are furnished for installation by others, alongside a
  separate exclusion of lock hardware generally. Read together these mean the bidder buys the lock
  and touches nothing else.
- A tariff clause. One bidder states twice that the price excludes increases due to tariffs and that
  the quote becomes null and void and must be requoted if the products are affected, and separately
  that the validity window explicitly does not cover tariff increases. That is a commercial condition
  that can void the bid after award.
- A statement that internet addressing is provided by the owner, which is the only acknowledgement in
  the corpus that the owner's information technology vendor is a party to this work.

What is genuine project signal:

- A disclosure that the documents do not specify a cable type or count. Where a bidder writes that
  the riser does not show which cables reach the unit panels, that is a documents gap and belongs
  upstream, not in the leveling.
- A disclosure that a room does not exist on the plans. The strongest instance in the corpus is a
  service provider requirements matrix noting that the main distribution frame is not identified on
  the plans and that the current architectural plans do not show telecom rooms at all, on a three
  hundred unit building. That is a design gap found by a bidder.
- An assumption naming a communication method for the fire alarm, such as a dialer, where the
  documents do not fix one.
- An equipment supplier's statement that its pricing is based on device counts the electrical
  contractor gave it, and that no other documentation was used. That means the fire alarm number is
  only as good as a count nobody in the bid chain independently verified.

One warning about boilerplate assumptions that are simply wrong. A fire alarm supplier's proposal in
the corpus assumes the project requires prevailing wages and assumes the project is tax exempt.
Neither is true of private residential work, and each would move the number materially. Read the
assumptions block of a supplier quote as a default template, not as a statement about the project.

---

## 5. Furnish and install seams, and adjacent-trade overlaps

Four seams decide whether this package works, and none of them are visible on a drawing.

The pathway seam. Everything the cable travels through belongs to the electrician, and everything
the cable is belongs to this trade. That is clean in principle and messy in practice: firestopping
flips between bidders, grounding flips between bidders, and plywood backboards are excluded by
everyone. The rule to apply is that if a low voltage proposal does not name it, the electrician has
to, and if the electrical proposal does not name it either, it is a gap.

The camera cabling seam. A surveillance proposal that excludes all camera cabling including head end
termination is quoting devices and a head end, not a system. Its number will sit on a ranking beside
a competitor who carried the cable, and nothing in either total says which is which. This is the
single most misleading comparison in the trade and it turns on one clarification line.

The equipment supply seam. In access control and surveillance the owner frequently selects an
integrator that supplies all equipment, leaving the bidding contractor to supply cable and
consumables and to assist that integrator with testing and commissioning. So a security package can
be furnish and install, install only, or furnish only depending on a decision made outside the
documents, and a fourth party who never appears on the drawings can be the design and supply
authority. Establish this before comparing any security number.

The electrified lock seam, which is the trade's live boundary with door hardware. Three positions
appear in the corpus. One bidder furnishes a named smart lock platform for installation by others
while separately excluding lock hardware. Another states that the locks at a named access control
door group are provided and installed by others entirely. A third priced an electrified lock line at
more than double the next lowest bidder, and when challenged asked which lock equipment the
competitors had carried, which turned out to be a different architecture: a smart lock platform on
its own versus that platform interfaced with a second manufacturer's keyless locks. So the same
drawing set produced two different lock architectures and a hardware boundary drawn three different
ways. Settle the lock architecture and the furnish and install split before soliciting, and settle it
jointly with the door hardware package.

Other adjacencies:

- Fire alarm. Inside the family when the electrician bids it, outside when a specialist does. The
  specialist relationship is unusual: the fire alarm equipment supplier quotes through the
  electrician off device counts the electrician provides, and holds the electrician responsible for
  clearing shorts, grounds and open circuits, for providing an approved points list before final
  download, and for supplying drawing files at no charge. One acceptance test visit is included and
  additional visits are billable.
- Elevators. Elevator cab cameras and the elevator card reader are this trade's, and they need the
  elevator contractor's traveling cable.
- Trash chutes. The chute door interlock system is low voltage in name but the chute vendor excludes
  all its wiring, so it lands here or on the electrician.
- Mechanical and architectural, for the telecom rooms themselves. This is the least appreciated seam
  in the trade and it belongs in section 6.

A boundary note on temporary site security. Surveillance towers, jobsite cameras and remote video
monitoring are a rental and monitoring market, not a construction package. The vendors are national,
the pricing is monthly or weekly per tower with a separate mobilization charge, the monitoring runs
overnight and weekend hours by subscription, and the builders risk insurer is often the party
requiring it. It belongs in the general requirements and never in the permanent low voltage scope.
Two cautions: the same document has been filed under a surveillance token in one round and a
temporary security token in another on the same project, and the same vendor may sell both jobsite
time lapse cameras and security monitoring under one name, so the token does not tell you which
product is being quoted.

---

## 6. What the drawings will not tell you

What the trade actually prices from:

1. The technology drawing series, for outlet and device locations and for the riser.
2. The electronic security series where one exists, for readers, cameras and door groups.
3. The two specification divisions, whose dates frequently differ from the drawings by weeks or
   months.
4. The unit count, for the residential quantities.

Not deducible from any drawing, and each of them moves the number:

- How many cables run to each unit media panel and of what type. Where the riser is silent, this is
  assumed, and it is the whole residential quantity.
- Whether in-unit work is in the package at all.
- Whether camera cabling is in the surveillance package.
- Who supplies the security equipment.
- The electrified lock architecture and its furnish and install split.
- Whether the owner has an information technology vendor and what it is supplying, including
  addressing, switches and access points. Bidders routinely install customer provided access points,
  so the count of devices installed and the count of devices furnished are different numbers.
- Whether a managed internet service provider is involved, and what that provider requires. This is
  the biggest hidden design input in the trade. A provider's own requirements matrix in the corpus
  specifies a minimum main frame room area and a minimum intermediate frame room area, temperature
  held within a stated range with a minimum air change rate and stated airflow and cooling loads for
  each room type, one intermediate frame per building or per every other floor with a maximum cable
  distance to any unit, two dedicated sleeves where rooms stack vertically, fire caulking to local
  code, a fire rated plywood backboard of stated size, a grounding bus bar, outside distribution
  conduit of stated size and material with long sweeps plus a spare, and entrance conduit of stated
  count and size cast in the slab and stubbed a stated distance. Those are architectural, mechanical
  and electrical requirements arriving through a low voltage bidder, and the matrix carries no price
  at all. On the project where it appeared, the architectural plans showed no telecom rooms.
- Union or open shop labor and the local.
- Whether tariffs will affect the equipment, which one bidder makes an explicit condition on the
  validity of its whole number.
- Lead times, which no proposal in the corpus states for any system.

---

## 7. Quantity and pricing conventions

Units the trade thinks in:

- Drops and outlet locations, with a port count each. The primary unit.
- Doors, for access control, split by mount type and by single or double leaf.
- Cameras, by type.
- Each, for racks, panels, enclosures, controllers, media enclosures, credentials and stations.
- Runs, for backbone fiber, with a strand count and a mode.
- Residential units, for the in-unit quantities and for whatever normalization an estimator improvises.
- Percent of contract value for bond, quoted separately against each base where a bidder carries two.

Cost drivers, roughly in order:

1. Whether fire alarm is inside the package. It dominates everything else when it is.
2. Whether in-unit work is inside the package, worth well over half a structured cabling number on a
   residential building.
3. Whether the package is furnish and install, install only, or furnish only.
4. Whether camera cabling is inside the surveillance number.
5. Device and drop counts, which move freely between rounds.
6. The assumed cables per unit, which is invisible.
7. Union versus open shop, and the local.
8. Camera type mix, since multisensor and fisheye devices cost multiples of a fixed dome.
9. The electrified lock architecture.
10. Tariff exposure on imported equipment.
11. Bond, permit and tax basis.

On spread, and no amounts are given here. Competing telecommunications bids on one project landed
about four times apart, and competing security bids on the same project about one and a
half to two times apart. Neither ratio is a price signal. The four to one gap is a bidder that
excluded fiber, fiber terminations, switches, access point devices, speaker drops and all pathway
against a union bidder that carried a complete cabling and security platform including permits and
certification. They are not offers on the same work. In the other direction, an electrician's whole
family bid and a specialist's structured cabling bid can look comparable in magnitude while covering
entirely different systems. This trade offers no example of a genuinely tight spread, and that is
itself the finding: with no leveling tab, no scope sheet and no scope rows, nobody has ever asked
these bidders the same question, so no two of their numbers have ever been made comparable. A spread
here measures scope definition failure and nothing else.

The practical consequence is that leveling in this trade must start by rebuilding each bid onto a
common system decomposition, then normalizing device counts, then resolving the four seams in
section 5, and only then looking at money. Any comparison that skips those steps is comparing
different buildings.

---

## 8. Coverage and gaps

This file is calibrated on about twenty low voltage proposals from roughly a dozen companies across
three multifamily residential projects in one regional market, all bid by one general contractor,
plus a service provider requirements matrix, a standalone fire alarm supplier quote, and nine
temporary site security quotes captured only to establish that they are a different market. The
proposals span design development, permit, construction documents and conformed rounds. There are no
leveling tabs at all for this trade on any project.

This is the thinnest evidence base in the cluster relative to the scope it covers, and several claims
above rest on single documents. Specifically:

- The six system decomposition in section 1 rests on one proposal from one electrician on one
  project. It is the only document in the corpus that shows the family whole, and the proportions
  between the systems, including fire alarm's dominance, come from that one page. Treat the
  decomposition as sound and the proportions as a single observation.
- The in-unit boundary finding rests on one project where two bidders happened to draw it
  differently and one said so in a single qualification line. The magnitude comes from comparing
  those two numbers, which differ for other reasons too.
- The service provider requirements in section 6, which are the most actionable content in this
  file, come from a single unpriced document on a single project. Whether other providers demand
  the same room sizes, cooling loads and conduit is unverified, though the requirements read as
  standard practice rather than as one company's preference.
- The electrified lock finding assembles three positions from three different projects and one
  negotiation email. No single project shows all three, and the one that shows the pricing
  divergence does so only in correspondence, not in a proposal.
- The camera cabling exclusion appears in exactly one proposal. It is severe enough to include on one
  sighting, but it is one sighting.
- The tariff clause appears in one bidder's two proposals on one project, dated to a specific policy
  moment. Whether it persists is unknown and it may already be stale.
- The quantity churn finding rests on two bidders, one on each of two projects, and both are strong
  clean examples.
- Fire alarm is represented by exactly one specialist supplier quote and by one line in the
  electrician's family bid. The file cannot say how fire alarm is normally packaged, priced or
  leveled, only that it is large and that the supplier prices off counts the electrician supplies.
- Area of rescue and emergency responder radio amplification appear only as line items in that one
  family bid, with no scope, no exclusions and no competing quote. Everything this file says about
  them is that they exist and belong here.
- Building controls are named only to route them away. There is no controls knowledge here.
- No project in the corpus is commercial, institutional, healthcare or laboratory work, where this
  family is far larger, where audio visual and nurse call join it, and where the owner's information
  technology organization is a formal design authority rather than an assumption.
- No signed subcontract or executed buyout appears, so nothing shows how any of the four seams in
  section 5 was actually resolved.
- No proposal in the corpus states a lead time for any system, so this file cannot say what the
  procurement clock looks like even though long lead electronics are a known risk in this family.
- Most importantly, because no leveling sheet exists for this trade anywhere in the corpus, the scope
  row set in section 3 is constructed rather than observed. Every other file in this family of
  documents can point at an estimator's own taxonomy. This one cannot, and the row set should be
  treated as a first proposal to be corrected against the first real leveling sheet that appears.
