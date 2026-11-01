---
name: story
description: Shape a complex science topic into one story before the voice-over is written - hero, stakes, turn, beats - and hand a story card to the `script` skill. Use when a topic has more than one mechanism, a long history, or a video longer than 60 s; or when the person asks to work on the story.
---

# Story

A helper before `explain` (or before `script`, for a long video). It decides *what* we tell and in what order. It writes no voice-over and no scenes.

Skip it for a short explainer with one mechanism: `explain` step 1 covers that.

## Steps

1. **Take the material.** Topic, notes, papers, a draft. If the length and the viewer are unclear, ask in the same message as step 3. Default: adult viewer, 1 to 3 min.
2. **Find the six parts.** Write one line each:
   - **Core**: the story in one sentence, and why a viewer without training cares.
   - **Question**: what the viewer wants answered until the end.
   - **Hero**: whose eyes we see through. A cell, a scientist, a patient. One hero.
   - **Stakes**: what can be lost or won.
   - **Turn**: what the viewer learns that they did not expect.
   - **Point**: the one rule or idea the viewer leaves with.
3. **Ask** at most 3 short questions, only for what the person must decide (facts, what really happened, what matters to them). Decide craft yourself. If the person is away, make the guess and mark it `(guess)`.
4. **Lay out the beats.** 5 to 9 beats, one line each, linked by *but* or *so*, never *and then*. Mark one beat `(hook)`: the strongest moment, which opens the video. Put the turn near the middle.
5. **Check** each beat against these, and fix:
   - One idea in each beat; one term, named once, with an image.
   - One line at a time; one example for each idea.
   - Expectation first, the turn second; the title does not give the turn away.
   - Each strong claim follows from a source. Mark a hypothesis as a hypothesis.
6. **Hand over** the story card in `videos/<slug>/story.md` and show it to the person: "Accept the story? yes / changes". Then suggest `script` (long video) or `explain` (short).

## Story card

```
# Story: <working title>
Core:
Question:
Hero and stakes:
Turn:
Point:
Length: ~N min
Beats:
1. ... (hook)
2. ...
Keep as is: <the person's decisions>
Sources: <1 to 5, the paper or review behind each strong claim>
```

## Done when

- Each of the six parts has one line, and each beat links to the next by *but* or *so*.
- The person accepted `story.md`, or the open guesses are marked `(guess)`.
