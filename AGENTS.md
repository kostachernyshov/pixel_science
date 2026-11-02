# pixel_science

Local tool, agent skill, and sprite library for pixel-art science explainer videos in four formats (16:9, 9:16, 1:1, 4:1). Open to community contributions. First topic: biology.

- Read `README.md` (layout, commands) and, for sprites or scene types, `CONTRIBUTING.md`.
- Making a video: skill `.agents/skills/animate/SKILL.md`; plan format `.agents/skills/animate/PLAN.md`. Sprites live in packs (`packs/<name>/`).
- Run commands with `.venv/bin/python` from the repo root. Before a commit: `tools/validate_sprites.py` prints `VALID`.
- Layout code reads `frame.W` and `frame.H` at draw time; never use fixed 480x270 sizes.
- Rendered videos (`out/`), plans of test videos, and generated code are not committed.

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
