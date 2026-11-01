---
name: script
description: Write the voice-over and scene notes for a long pixel explainer (over 60 s, several mechanisms) as chapters with a hook, open loops and bridges, ready for the `explain` plan. Use after `story`, when a topic is complex, or when the person asks for a script or a storyboard of a long video.
---

# Script

A helper between `story` and `explain` step 4. It decides how the story *sounds* and what the picture *shows*. The input is a story card (`videos/<slug>/story.md`); without one, run `story` first if the core, the hero or the turn is unclear.

Keep the order and meaning of the beats. If a beat does not work (no turn, the end does not follow), say so in one line and offer to go back to `story`.

## Steps

1. **Budget.** 2.5 words a second: 1 min = 150 words. Split the video into **chapters** of 20 to 45 s, one mechanism each. Each chapter is one `explain` part with its own `explainer.yaml`; the parts play in a row. One plan with a longer `max_s` is also fine for 1 to 2 min.
2. **Hook** (first 5 to 10 s). Open on the `(hook)` beat: a paradox, a number, a question, or the middle of the action. No greeting, no "in this video". Offer 2 hooks, one line each, and pick one.
3. **Chapters.** For each chapter write `## S01`, `## S02`, ... as in `voiceover.md`. Each chapter: a hook line, the mechanism, a small answer, then a **bridge**: one line with what we found and the next question. Keep 1 or 2 **open loops** at a time and close each one later. Put the turn near the middle.
4. **Scene notes.** Under each `## Sxx` in `script.md`, add one line for the picture and, when it matters, the sound:
   - `[PICTURE: ...]` what we see and what it means to the viewer. Picture and voice add to each other; the picture shows, the voice explains.
   - `[CAPTION: ...]` 1 to 3 words.
   - `[SOUND: ...]` a pause, a click, silence after the key line.
   - The scene type it fits (`title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`), and the cast from the sheet.
   Change the picture every 3 to 7 s; change the format (cast, action, fact, flow) at least every 30 s.
5. **End.** Close the question, say the point, and return to the image of the hook. The last scene is a `summary`.
6. **Read aloud** with a timer. Over budget by 10 % or more: cut now. Rewrite each line that trips the tongue.
7. **Hand over.** Write `videos/<slug>/voiceover.md` (voice only) and `videos/<slug>/script.md` (voice and notes). Show them with the sources: "Accept the script? yes / changes". After "yes", go to `explain` step 4 with each chapter.

## Writing rules

- One thought in each sentence; a sentence fits one breath. Present tense for the picture.
- A concrete thing beats a general one: a name, a number, an object.
- A number on screen is in a source. Mark a hypothesis as a hypothesis.
- Medicine: no promises of a cure, no personal advice.

## Done when

- The question is asked before 0:30 and answered at the end; every open loop is closed.
- Each chapter has a hook line and a bridge; the reading time is within the budget.
- The person accepted `voiceover.md` and `script.md`.
