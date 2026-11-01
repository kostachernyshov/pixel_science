# pixel_science

Local tool, agent skill, and sprite library for pixel-art science explainer videos in four formats (16:9, 9:16, 1:1, 4:1). Open to community contributions. First topic: biology.

- Read `README.md` (layout, commands) and, for sprites or scene types, `CONTRIBUTING.md`.
- Making a video: skill `.agents/skills/explain/SKILL.md`; plan format `.agents/skills/explain/PLAN.md`.
- Run commands with `.venv/bin/python` from the repo root. Before a commit: `tools/validate_sprites.py` prints `VALID`, `pixsci.py check examples/*/explainer.yaml` prints `CHECK PASSED`.
- Layout code reads `frame.W` and `frame.H` at draw time; never use fixed 480x270 sizes.
- Rendered videos (`out/`) are not committed.

## Agent skills

### Issue tracker

Issues живут в GitHub Issues (через `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Стандартные пять меток: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

single-context (`GLOSSARY.md` + `docs/adr/` в корне). See `docs/agents/domain.md`.
