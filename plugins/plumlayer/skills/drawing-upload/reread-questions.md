# Drawing upload: re-read the open Questions a delivery touches

Read from `drawing-upload` step 9b, only where a prior delivery or manual existed. Every step this
file names is a step of `drawing-upload`'s own `SKILL.md`, and every gate there applies here
unchanged.

1. **Which sheets changed.** For a manual on its own, the sections step 8 read out of the new
   manual. For a drawing delivery, first read its `issue` off `list_drawing_deliveries`. Where it
   is null with `stillReading` false, the delivery holds no sheet number: `set_grid` refuses it and
   no sheet is known to have changed, so skip the rest of this step and go to step 10, whose
   handoff names it. Otherwise the changed sheets are the ones this delivery itself prints, each
   on its own page of it, read by its own id and never off the current set: an addendum uploaded
   after a later one is not the current set's page for any sheet the later one reprints, and it
   still changed that sheet. Take `set_grid(projectId, deliveryId: <this delivery's id>, limit: 0)`
   for the counts, then pages with `discipline` + `limit`/`offset`.
   - For an addendum, every row is a sheet it prints, on its own page.
   - For a new set, the grid joins the set with its addenda and gives each sheet the newest page
     that prints it. A row whose `deliveryId` is this delivery's is a sheet the set prints, on its
     own page. A row from one of its addenda is a sheet the addendum reprinted or added: find
     whether the set prints it too with
     `search_set_text(projectId, query: "<sheet number>", deliveryId: <this delivery's id>, wholeWord: true)`,
     which searches this delivery's pages only and names each hit's sheet number as this delivery
     printed it. A hit whose `sheetNumber` is that number is the set's own page of the sheet, by
     its `fileId` and `page`, and the sheet changed; with none, the addendum added the sheet and
     this set does not print it.
   Each changed sheet's `fileId` and `pageInPdf` are this delivery's page of it, which points 3
   and 4 read.
2. **Which Questions.** The `sheet` and `section` filters on `list_questions` read only the places
   the ask itself cites, and a reader that meets the same callout on a second sheet cites it in a
   reply, so a filtered read misses a Question that names a changed sheet only in a reply. Read the
   open Questions whole instead: `list_questions(projectId, full: true, limit: 10)`, paged with
   `offset: nextOffset` until `nextOffset` is absent. Keep every one whose ask or any reply cites a
   changed sheet (`sheet:<n>`) or a section the new manual carries (`specSection:<packed code>`).
   A place somebody took off the ask still sits in `sources`, one for one with `sourceRemovals`,
   which is null where the place still stands and names who took it off where it is gone. Skip
   every ask source whose `sourceRemovals` entry is not null, here and in point 3: a Question whose
   only citation of a changed sheet was taken off on purpose is not this step's, and never gets a
   new box put back. Reply citations are read as they are. That read also carries each kept
   Question's ask and every place it and its replies cite, which the points below work from.
3. **On a changed sheet, point the Question at this delivery's page too.** A source that names its
   drawing file opens on the page it was cited on, whatever later issue reprints the sheet; a
   source with no file opens on the page the current set shows for the sheet, at its old
   coordinates, which a moved layout leaves on nothing. Keep every existing source, either way,
   since taking one off is the estimator's call. For each `sheet-region` box or `sheet-point` on a
   changed sheet, in the ask (a standing source only) or in a reply, that names no file or another
   file than this delivery's: find the callout on this delivery's page, the `fileId` and
   `pageInPdf` on that sheet's row from point 1, with `search_set_text` its tag with `deliveryId`
   set to this delivery, whose hits carry boxes in the same PDF points, then `get_page_text(fileId,
   pageNum: <that pageInPdf>, region: <around the hit>)`. A whole-page `render_page(fileId,
   pageNum: <that pageInPdf>)` answers with `pageWidthPt` and `pageHeightPt`, for rendering a
   region where the callout is in the linework. Then `add_question_source` a `sheet-region` box
   around the callout there, built from the boxes `get_page_text` gave you for the callout's words,
   with `frame: "page-points"` and this delivery's `fileId`, so the Question opens on the new paper
   as well as the page it was raised on; the reply in point 5 says so. A render shows you where the
   callout is and never gives the box: where no word of the page's read carries the callout, add
   the sheet with no box (`{ "type": "sheet", "sheet": "sheet:<n>" }` with this delivery's
   `fileId`) and tell the user that sheet's text did not carry the callout.
   `add_question_source` is refused once a Question holds ten places. Never take one off to make
   room: cite the new box in the reply instead, and name that Question to the user as one with no
   room for another place on it.
4. **Re-read each one against the new paper.**
   - On a changed sheet: read the callout's text on this delivery's page, and search the ask's own
     tags and words with `search_set_text` and `deliveryId` set to this delivery, after
     `set_text_status` says the new pages have been read. Render further only where the change is
     in the linework, a cloud or a delta the text does not carry.
   - On a section of the new manual: a spec citation has no box and no sheet. Read the section's
     pages off its `locatedAt` (`search(projectId, subject: "specSection:<packed code>", predicate:
     "locatedAt")`), with `get_page_text` on the part the ask is about, and search the ask's words
     with `search_set_text` and `kind: document`.
5. **Three outcomes, and no fourth.**
   - The new paper answers it: work it as project-record's "When an answer arrives" says.
     `reply_question` saying what the revised sheet or section shows, citing it; tell the user
     what changed and that the reply may answer it, so he can have it pinned; and name the scope
     rows that cite the Question (`questions` on each `list_scope_items` row). Update
     those rows' values, citing the Question, only when he asks in this session; otherwise they
     are the scope pass's in step 10, which reads this delivery's sheets.
   - The new paper changed on the point without answering it: `reply_question` saying what
     changed.
   - Unchanged on the point: no reply, and it is counted in the report, unless point 3 added a
     box, when a reply says only where the callout sits on the new paper.
   A reply on a sheet cites a `sheet-region` box around what it read there, with this delivery's
   `fileId`, built as point 3 builds one, or the sheet with no box where point 3 says. A reply on a section cites the section, `{ "type": "spec", "section":
   "specSection:<packed code>" }`.
6. **Never close one, and never raise one here.** Closing is the estimator's: `close_question`
   only when the user settles it in this session, with their reason in `note`. No new Question
   comes out of this step; what the delivery changes in the scope list is still the handoff in
   step 10.

<!-- user-facing -->
Report: how many open Questions cite a changed sheet or section, how many got a reply, the ones
the new paper may answer with the scope rows each one moves, the ones you pointed at the new paper
too, any with no room for another place on it, and how many were unchanged on the point. Name each
Question by its title, or by its RFI number ("RFI 22") once it holds one. Say plainly that none
was closed and that settling one is theirs.
<!-- /user-facing -->
