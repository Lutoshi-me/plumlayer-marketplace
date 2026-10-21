---
name: lead-reads-fixture-render
description: >
  A lead skill fixture for the setup-reads check. One lead section renders a page itself, which the
  check refuses in one line.
---

# Lead reads fixture, a render in the lead

## 1. Count the set

Call `set_grid(projectId, limit: 0)` and read `count` off it.

## 6. Read the pages the pass could not name

Read each page's title block yourself with `render_page`.
