---
name: storyboard
description: Find the form of a pixel science video (how to tell it, how to show the result, which emotion) and write a key-frame storyboard with voice-over for `animate`. Use when the person does not know what to show, the topic is an experiment or a history of 3 or more steps, has two lines to compare, runs over 30 s, or is a series; also from `explain`.
---

# Storyboard

The job is the **form**. Each time, think again: how do we tell this story, and how do we show the result so that the viewer understands it, finds it interesting, and feels something? A good example is not a template.

The output is `videos/<slug>/storyboard.md`: 6 to 12 key frames with the voice-over. `animate` builds its plan from this file. Write all files in English.

## Two modes

- **Direct** (the person runs `/storyboard`): offer forms in step 4 and wait for a choice. Ask for acceptance in step 8.
- **From `explain`**: ask nothing. Choose the form yourself, write each guess as one line `Guess: ...` at the top of the file, and show the finished storyboard.

## Steps

1. **Input.** A topic, or the person's own meaning chunks (notes in their words, in their order). With chunks, keep their order and wording. Change their text only with a one-line reason under the frame. Default viewer: adult without training.
2. **Sources.** 1 to 5 reliable sources (review, textbook, original paper). Each claim of the voice-over follows from them. Mark a hypothesis as a hypothesis.
3. **Core.** Write the result as one sentence: "AND ..., BUT ..., THEREFORE ...". If it does not come, the topic is not clear yet: read more, do not draw. Then write the final frame in one line: what the viewer sees at the end.
4. **Form.** Read [FORMS.md](FORMS.md) and [EMOTIONS.md](EMOTIONS.md). Write 2 to 3 forms, one line each: how we tell it, how we show the result, the main emotion. At least one form is not in the catalogue. Recommend one.
5. **Running device.** Choose one device that stays to the end and shows the viewer where they are: levels, a HUD value, two panels, a counter, a map. Choose one main emotion (and at most one support emotion).
6. **Key frames.** Write 6 to 12 frames, one for each meaning chunk, plus the frame of the turn. Budget: 2.5 words a second, 20 to 60 s in total.
   - The hook is in the first 3 s: a question or a strange fact, no greeting.
   - The turn is at 60 to 70 % of the time. Expectation first, then the turn.
   - Link the chunks by *but* or *therefore*, never *and then*.
   - One term once, with an image. One line of the story at a time.
   - The result reads with the sound off: one caption word or one HUD value.
   - The end is the answer and the final frame from step 3.
7. **Check each frame.** Under a frame with a metaphor or a simplification, write what it claims and what it does not claim. The frame stays true to the science even where the voice simplifies. This line is for the storyboard only; it is not shown in the video.
8. **Show.** Write `storyboard.md` (format below). If the harness can publish artifacts, publish one page made from it: each frame is a card with a rough sketch on the left (inline SVG: boxes, circles, arrows, labels; who stands where and what happens) and the voice-over and caption on the right. Else show the file as text. Direct mode: ask "Accept the storyboard? yes / changes".
9. **Hand over.** After "yes" (or at once from `explain`), go to `animate`. It takes the topic, sources, voice-over, and scenes from `storyboard.md`.

## Long topic: a series

If the topic needs more than 60 s or more than one mechanism, first write a series plan in `videos/<series>/series.md`: one line and one question for each video, and one running device for the whole series. Show it (direct mode: ask for acceptance). Then make the storyboard of one video at a time.

## storyboard.md

```markdown
# <title>
Guess: <only from explain; one line each>
Core: AND ..., BUT ..., THEREFORE ...
Form: <name>: <one line>
Device: <running device>
Emotion: <main> (+ <support>)
Length: ~N s, N words
Sources:
- <author, title, journal, year, doi>

| Time, frame | Voice-over, caption |
|---|---|
| **F01 0–3 s** hook. <picture in one line> | "<voice-over>" <br> CAPTION: <1–3 words> |
| **F02 3–8 s** <picture> <br><sub>claims: ...; not: ...</sub> | "<voice-over>" <br> CAPTION: ... |
```

## Rules

- Each frame earns its place: the viewer learns or feels something new.
- No invented numbers. A number on screen is in a source.
- Honest emotion: the rules in [EMOTIONS.md](EMOTIONS.md).
- No real person's face, logo, or brand. Name scientists in text only.

## Done when

- The core sentence, the final frame, the form, the device, and the emotion each have one line.
- Each frame has time, picture, voice-over, and caption; each metaphor has its claims line.
- The total time is in the budget, and the last frame shows the answer.
- Direct mode: the person accepted the storyboard. From `explain`: the guesses are listed.
