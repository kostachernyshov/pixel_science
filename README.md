# Pixel-art science videos that you make by talking to an agent

Tell Claude what idea you want to explain. It finds the sources, writes the voice-over, shows you a storyboard,
and renders a short pixel-art video in four formats: YouTube, Reels, a feed post, and a banner. You accept each
step; the agent does the work. The first topic is biology: immune cells, tumors, molecules, labs, people.

| Format | Size | For |
|---|---|---|
| landscape 16:9 | 1920x1080 | YouTube, slides |
| vertical 9:16 | 1080x1920 | Reels, Shorts, TikTok |
| square 1:1 | 1080x1080 | feed posts |
| banner 4:1 | 1920x480 | site header |

## Install (2 minutes)

### 1. Add the plugin

**Claude Code** (terminal, desktop app, IDE). In your shell:

```bash
claude plugin marketplace add kostachernyshov/pixel_science
claude plugin install pixel-science@pixel-science
```

Or in a session, in one line: `/plugin install pixel-science --marketplace kostachernyshov/pixel_science`.

**Cowork and claude.ai.** Open [Customize > Plugins](https://claude.ai/customize/plugins), choose
**Add > Add marketplace**, enter `kostachernyshov/pixel_science`, and add **pixel-science**. The plugin then also
reaches Claude Code on each computer where you sign in with the same account.

### 2. Set it up once

Open a folder for your videos, start a session there, and type:

```
/pixel-science:setup
```

The agent makes a Python environment, checks ffmpeg, asks whether you want a synthetic voice, and renders a 15 s
check video. The plugin adds the prefix `pixel-science:` to each command. Below, the commands are short:
`/animate` means `/pixel-science:animate`.

### 3. Make a video

```
/animate how vaccines train B cells
```

<details>
<summary><strong>Update</strong></summary>

```bash
claude plugin marketplace update pixel-science
claude plugin update pixel-science@pixel-science
```

Restart the session after the update. In Cowork and claude.ai, open the plugin and choose **Check for updates**.

</details>

<details>
<summary><strong>Cloud sessions and a clone of the repo</strong></summary>

Cloud sessions (claude.ai/code) do not load plugins from a marketplace. Add this repo to the session instead:
the same skills load from `.claude/skills` without the prefix (`/setup`, `/animate`). This also works on your own
computer in a clone, which is the way to change the tool or add sprites.

</details>

## Quick examples

**"Make a 30 s reel about how NK cells find cancer cells."** You know the topic but not the picture.

```
/storyboard     the form of the story, 6 to 12 key frames, the voice-over; you accept it
/animate        the plan, a storyboard in each format, then the videos
```

**"I know what to show."** Type `/animate` with the idea. The agent asks you to accept the voice-over and the
storyboard before it renders.

**"I want a voice and subtitles."** Run `/setup` again and answer "yes" to the voice (about 6 GB, best on a fast
computer). Then ask `/animate` for a video with a voice: each action lands on the word that names it.

**"There is no action for this."** When a scene needs an action the library does not have (a cell releases
something, a drug blocks a receptor), the agent adds it with `add-verb` and goes on.

## Commands

**Person** commands start when you type them. **Agent** skills start by themselves when the task needs them.

**Person**

- **[setup](skills/setup/SKILL.md)**: Gets the computer ready: Python environment, ffmpeg, the voice if you want it, a check video.
- **[storyboard](skills/storyboard/SKILL.md)**: Finds how to tell the story (form, emotion, key frames) and writes the voice-over with sources. Use it first when you are not sure what to show.
- **[animate](skills/animate/SKILL.md)**: From an idea or a storyboard to the videos: sources, voice-over, plan, check, storyboard images, render.

**Agent**

- **[add-verb](skills/add-verb/SKILL.md)**: Adds a missing action (a verb such as `secrete` or `block`) to a sprite pack.

## What is inside

- 108 shared base sprites: 100 in `biology` (cells, molecules, organelles, labs, organs,
  organisms, plants, people) and 8 in `earth` (water, weather, soil). One sprite source
  is reused across light/dark environments and visual styles.
- Actions with light and hit effects, one plan for all four formats, a synthetic voice (Qwen3-TTS) with word-timed
  subtitles.
- The tool `pixsci.py`, which the skills run. To run it by hand or to see how it works: [docs/tool.md](docs/tool.md).

## Contribute

New sprites, packs, scene types, and actions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md); rules for agents
are in [AGENTS.md](AGENTS.md). Ideas and bugs: [Issues](https://github.com/kostachernyshov/pixel_science/issues).

The tool comes from the `animate` skill of [kostachernyshov/skills](https://github.com/kostachernyshov/skills)
and the *Cancer Wars* video series.

License: code MIT; sprites CC0-1.0 (each pack's `pack.yaml`; an outside sprite under CC-BY-4.0 names its author in `sprites.json`); fonts GNU Unifont and Medeo Pixel (SIL OFL 1.1, `fonts/LICENSE_medeo.txt`).
See [LICENSE](LICENSE).
