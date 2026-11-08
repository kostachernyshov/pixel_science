# 3. The plan is resolved once; only contact depends on the format

Date: 2026-11-08. Status: accepted (#65; recorded after the retro, #68).

## Context

One plan renders in four formats. Before #65 the plan was changed in place for each format and then restored
(`_own`, `_own_keys`, a restore loop in `prepare`), `continue` ran again per format, and Actor state had two
shapes. Architecture reviews suggested a copy of the plan per format as the fix.

## Decision

1. Only contact depends on the format: where `move_to: <actor>` stops comes from the sprites' sizes on the
   stage of that format. This covers the end place of `move_to: <actor>`, the default "edge to edge" of
   `divide`, and the start place of a `continue` actor whose scene ended in contact.
2. Nothing else depends on the format: word times, `continue`, behaviors (`wander`, `hunt`, `divide`), the
   show and hide of verbs.
3. The plan is resolved once, `stage.resolve(plan, times)`, at the end of `prepare`, after word times: these
   become plain beats; `move_to: <actor>` stays a name.
4. Contact is placed per format at draw time, `stage.state_at(plan, sc, t, L)`, for the layout L of the
   current format, lazily, with a memo per (scene, format).
5. No copy of the plan per format, and no change of the plan for one format that is restored later.

## Consequences

- A new beat field or behavior goes into `resolve` when it does not depend on the stage size, and into
  `state_at` when it does (as contact does).
- `pixsci check` sees the plan as it plays in every format: the beats after `resolve`.
- `tools/frame_hashes.py` on the smoke plan in all four formats shows that a change keeps frames equal.
