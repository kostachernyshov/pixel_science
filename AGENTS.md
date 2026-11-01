# pixel_science

Local tool, agent skills, and packs of sprites for 20 to 60 s pixel-art science explainer videos in four formats (16:9, 9:16, 1:1, 4:1) and three styles. Open to community contributions. Design decisions: `docs/design-v0.1.md`.

- Read `README.md` (layout, commands) and, for sprites, packs, or scene types, `CONTRIBUTING.md`.
- Making a video: skill `.agents/skills/animate/SKILL.md`; plan format `.agents/skills/animate/PLAN.md`.
- Complex topic or a video over 60 s: helper skills `story` (beats) and `script` (chapters, voice-over, scene notes) before `animate`.
- A missing character: skill `.agents/skills/add-sprite/SKILL.md`.
- Run commands with `.venv/bin/python` from the repo root; `pixsci.py <command> --json` gives JSON. Before a commit: `tools/validate_sprites.py` prints `VALID`, `pixsci.py catalog --check` passes, `pixsci.py check examples/*/explainer.yaml` prints `CHECK PASSED`.
- The core (`pixel_kit/`) names no pack: sprites, backgrounds, and styles live in `packs/`.
- Layout code reads `frame.W` and `frame.H` at draw time; never use fixed 480x270 sizes. Colors for text and plates are roles (`INK`, `ACCENT`, `PLATE`), so every style can set them.
- Repo text is English. Rendered videos (`out/`) are not committed.

## Agent skills

### Issue tracker

Issues живут в GitHub Issues (через `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Стандартные пять меток: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

single-context (`GLOSSARY.md` + `docs/adr/` в корне). See `docs/agents/domain.md`.
