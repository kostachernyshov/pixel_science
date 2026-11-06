# pixel_science

Local tool, agent skill, and sprite library for pixel-art science explainer videos in four formats (16:9, 9:16, 1:1, 4:1). Open to community contributions. First topic: biology.

- Read `docs/tool.md` (commands, voice, how it works, layout) and, for sprites or scene types, `CONTRIBUTING.md`.
- Making a video: skill `skills/animate/SKILL.md`; plan format `skills/animate/PLAN.md`. Sprites live in packs (`packs/<name>/`).
- Finding what to show (form, emotion, key frames, voice-over): skill `skills/storyboard/SKILL.md`, before `animate`.
- Setting up a machine: skill `skills/setup/SKILL.md` (`pixsci.py doctor` says what is missing). The repo is also a Claude plugin (`.claude-plugin/`): skills find the tool through `${CLAUDE_PLUGIN_ROOT}`, or the repo root in a clone; keep both working.
- Run commands with `.venv/bin/python` from the repo root. Before a commit: `tools/validate_sprites.py` prints `VALID`.
- Layout code reads `frame.W` and `frame.H` at draw time; never use fixed 480x270 sizes.
- Rendered videos (`out/`), plans of test videos, and generated code are not committed.
- Voice, word times, and subtitles (`--voice`, `subtitles: true`): docs/tool.md, Voice and subtitles. Their packages stay in `requirements-voice.txt`, never in `requirements.txt`.
- Effects: a beat names a verb (`pixsci.py verbs`). A verb is YAML in a pack; a primitive is Python in the core. Terms: `GLOSSARY.md`.
- A verb is missing: add it to the pack with `skills/add-verb/SKILL.md` and go on. A new primitive in the core needs the maintainer's "yes" first.
- Do not add entities without need. A new field, file, option, or test only when nothing that exists can do the job. First look for what already does it: the setup check plan (`skills/setup/smoke/explainer.yaml`) is also the test of the tool, so a fix adds its case to that plan, not a new test file.

## Ideas, bugs, and pull requests

- A new idea or a bug found while working goes into a new GitHub issue (see Issue tracker below), not into the current change. Label it `needs-triage`.
- An issue becomes work only after it is discussed with the maintainer. Then one pull request per issue, small and on one topic, linked to the issue (`Closes #N`).
- Before a pull request, agree with the maintainer on what it adds. Nothing generated (test videos, their plans, catalogs) goes into it.

## Agent skills

### Issue tracker

Issues живут в GitHub Issues (через `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Стандартные пять меток: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

single-context (`GLOSSARY.md` + `docs/adr/` в корне). See `docs/agents/domain.md`.
