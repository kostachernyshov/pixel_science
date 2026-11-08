# pixel_science

Local tool, agent skills, and sprite library for pixel-art science explainer videos in four formats (16:9, 9:16,
1:1, 4:1), 20 to 60 s each. Open to community contributions. Everything in the repo is in English; talk with the
maintainer (Kosta) in Russian.

## Layout: the only places to write

The repo holds the product only. Each kind of file has one home; put new work there and nowhere else.

| Path | Holds | Changes |
|---|---|---|
| `pixsci.py`, `pixel_kit/` | the core: CLI, layout, render, primitives (`fx.py`) | a new primitive needs the maintainer's "yes" |
| `packs/<pack>/` | `pack.yaml` (license, author), `verbs.yaml`, `bible.md`, `code/library.py` | packs: `biology`, `earth`, `physics`; a new pack needs a "yes" |
| `packs/<pack>/sprites/` | PNG sheets and `sprites.json`, flat | every sprite of a topic goes into its topic's pack |
| `skills/<skill>/` | agent skills (`.claude/skills`, `.agents/skills` link here) | see Skills below |
| `tools/` | `build_sprites.py`, `validate_sprites.py`, `make_sheet.py` | |
| `docs/tool.md` | commands, voice, how it works, layout | |
| `docs/adr/NNNN-*.md` | one accepted decision each | see Decisions below |
| `docs/agents/` | issue tracker, labels, domain docs | |
| `README.md`, `CONTRIBUTING.md`, `GLOSSARY.md`, `AGENTS.md`, `CLAUDE.md` | product docs and these rules | |
| `fonts/`, `.claude-plugin/`, `.github/` | fonts and licenses, plugin manifest, CI | |

Local only, ignored by git, left as they are: `.venv/`, `examples/`, and `packs/stardew_reference/`
(proprietary game art: a visual reference to look at, never used in a render or a commit).

## Three zones of work

```
repo (this folder)        product only; changes reach it through a pull request
video folder              the person's folder for one video: plan, voice-over, voice, rendered videos
temporary system folder   tries, previews, boards, sheets, scripts of the agent; it is deleted
```

A try goes to the temporary folder. Show it in the chat. When the person says "yes", the result goes into the
repo (a sprite into its pack, a fix into the core) in a pull request. Plans and videos live in the video folder
the person names; ask when none is named.

## Permission rules

- A new folder or a new `.md` file anywhere in the repo needs the person's explicit "yes" in this chat for that
  exact path. A "yes" holds for the current task only.
- Reports, reviews, verification, prompts, sources, and PR or issue texts go into the chat or onto GitHub. Never
  into files.
- Never create `out/`, backup copies, or second versions of a file (`-v2`, `old`, `copy`): git keeps history.
- Before an action that deletes the person's files, ask.

## Decisions

An ADR (`docs/adr/`) records a serious decision only: architecture, the pack format, licenses, rules of the
process. Show its text in the chat first; write the file after the "yes". Small results of tries stay in the chat.

## Skills: when to read one

Read the skill before you start the task it names.

| Task | Skill |
|---|---|
| Set up a machine or clone; `pixsci.py doctor` is not `READY` | `skills/setup/SKILL.md` |
| Find what to show: form, emotion, key frames, voice-over; a long topic, a history, a series | `skills/storyboard/SKILL.md`, before `animate` |
| Make a video from a known idea or an accepted storyboard | `skills/animate/SKILL.md`; plan format `skills/animate/PLAN.md` |
| Add, import, generate, or redraw a reusable sprite | `skills/add-sprite/SKILL.md`, then `CONTRIBUTING.md` |
| A beat needs an action that `pixsci.py verbs` does not list | `skills/add-verb/SKILL.md` |
| Work on the core, a scene type, or a background | `docs/tool.md` and `CONTRIBUTING.md` |

The repo is also a Claude plugin (`.claude-plugin/`): skills find the tool through `${CLAUDE_PLUGIN_ROOT}`, or the
repo root in a clone; keep both working.

## Working rules

- Run commands with `.venv/bin/python` from the repo root. Before a commit: `tools/validate_sprites.py` prints `VALID`.
- Previews go to the temporary folder: `pixsci.py sheet /tmp/sheet.png`, `pixsci.py verbs /tmp/verbs.png`.
- Sprites from an image generator are welcome (`docs/adr/0002-generated-sprites.md`). A sprite name is unique across packs.
- Credit: the pack's `license` and `author` in `pack.yaml`. A sprite by an outside author adds `author`, `license`,
  and `url` to its entry in `sprites.json`.
- Layout code reads `frame.W` and `frame.H` at draw time; never use fixed 480x270 sizes.
- Voice, word times, subtitles: `docs/tool.md`, Voice and subtitles. Their packages stay in `requirements-voice.txt`,
  never in `requirements.txt`.
- Effects: a beat names a verb (`pixsci.py verbs`). A verb is YAML in a pack; a primitive is Python in the core.
  Terms: `GLOSSARY.md`.
- Reuse what exists. A new field, file, option, or test only when nothing that exists can do the job. The setup check
  plan (`skills/setup/smoke/explainer.yaml`) is also the test of the tool: a fix adds its case there.

## Ideas, bugs, and pull requests

- A new idea or a bug found while working goes into a new GitHub issue, not into the current change. Label it `needs-triage`.
- An issue becomes work only after it is discussed with the maintainer. Then one pull request per issue, small and
  on one topic, linked to the issue (`Closes #N`).
- Before a pull request, agree with the maintainer on what it adds.

### Issue tracker

GitHub Issues (through `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single context: `GLOSSARY.md` and `docs/adr/` at the root. See `docs/agents/domain.md`.
