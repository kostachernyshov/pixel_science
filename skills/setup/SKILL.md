---
name: setup
description: Set up pixel_science on this machine - Python environment, ffmpeg, and, if the person wants a synthetic voice, Qwen3-TTS and Qwen3-ForcedAligner - then render a short check video. Use after installing the pixel-science plugin, on a new machine or clone, or when animate says the tool is not ready.
---

# Setup

The goal: `pixsci.py doctor` prints `READY`, and a short check video renders. The voice is optional and heavy;
install it only when the person wants it.

## Where the tool is

- Installed as a plugin: `ROOT` is `${CLAUDE_PLUGIN_ROOT}` and `VENV` is `${CLAUDE_PLUGIN_DATA}/venv`.
  `VENV` stays when the plugin updates; `ROOT` does not, so never put the environment in `ROOT`.
- If these two are empty or read literally as `${...}`, the skill runs from a clone of the repo:
  `ROOT` is the repo root and `VENV` is `ROOT/.venv`.
- Write the two paths you found once, at the start, so the person sees where things go.

## Steps

1. **Python.** Find a Python 3.10 to 3.13 (`python3 --version`; on a Mac also `python3.12`, `/opt/homebrew/bin/python3.12`).
   If the person wants the voice, it must be 3.10 to 3.12. None fits: with `uv` installed, `uv python install 3.12`;
   otherwise tell the person how to get one (`brew install python@3.12` on a Mac) and stop.
2. **Environment.** If `VENV/bin/python` does not exist: `<python> -m venv "VENV"`. Then
   `"VENV/bin/pip" install -r "ROOT/requirements.txt"`. Run it again after a plugin update: it is quick when nothing changed.
3. **Check.** Run `"VENV/bin/python" "ROOT/pixsci.py" doctor`. Each line names what it found.
   - `ffmpeg MISSING`: on a Mac `brew install ffmpeg`; on Linux ask the person before `sudo apt-get install -y ffmpeg`.
     If neither works (no Homebrew, no sudo, a sandbox such as Cowork): `"VENV/bin/pip" install imageio-ffmpeg`;
     the tool then uses its ffmpeg. Run `doctor` again.
   - Go on when it prints `READY`.
4. **Voice (ask).** Ask once: "Install the synthetic voice (Qwen3-TTS and the word aligner)? About 6 GB, needs
   Python 3.10 to 3.12; on a laptop CPU speech takes 5 to 10 times its length. yes / later". On "yes":
   ```
   "VENV/bin/pip" install -r "ROOT/requirements-voice.txt"
   "VENV/bin/pip" install --no-deps qwen-asr==0.0.6
   ```
   The models download on the first `pixsci.py voice` run (from `huggingface.co` and `*.hf.co`; a sandbox must allow them).
   `doctor` then prints `voice ready` and the device (`cuda`, `mps`, or `cpu`).
5. **Check video.** From the person's working folder:
   ```
   "VENV/bin/python" "ROOT/pixsci.py" check  "ROOT/skills/setup/smoke/explainer.yaml"
   "VENV/bin/python" "ROOT/pixsci.py" render "ROOT/skills/setup/smoke/explainer.yaml" pixsci-check
   ```
   It renders `pixsci-check/setup-check-landscape.mp4` (about 25 s, a few seconds of work). With the voice installed, also
   run `voice` and `render ... --voice` on the same plan once: this downloads the models now instead of in the
   middle of the first real video.
6. **Summary.** Tell the person in a few lines: where `VENV` is, what `doctor` printed, the path of the check video,
   and what to run next: `/pixel-science:storyboard` or `/pixel-science:animate` from a plugin, `/storyboard` or
   `/animate` in a clone ("make a pixel explainer about how vaccines train B cells").

## Rules

- Install nothing outside `VENV` without asking, except what the person already said yes to.
- Do not install the voice unasked: it is large and most first videos do not need it.
- Do not change files in `ROOT` from this skill.

## Done when

- `pixsci.py doctor` prints `READY` (and `voice ready` if the person asked for the voice).
- `setup-check-landscape.mp4` exists and the person has its path.
