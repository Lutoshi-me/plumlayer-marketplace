---
name: lead-reads-fixture-clean
description: >
  A lead skill fixture for the setup-reads check. Its lead sections name no page read verb and call
  the sheet grid only for its summary; its exempt step names a page read and passes.
---

# Lead reads fixture, clean

## 1. Count the set

Call `set_grid(projectId, limit: 0)` and read `count` off it. Send every page read to the agent.

## 9b. Re-read the open Questions

Here `get_page_text` and `render_page` stay where the step runs, since this heading is exempt.
