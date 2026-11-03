# Forced alignment: when each word of a known text is heard in a wav (Qwen3-ForcedAligner-0.6B, Apache 2.0).
#
#   python pixel_kit/align.py JOBS.json      JOBS: [{"wav": ..., "text": ..., "lang": "Russian", "out": ...}]
#   writes to each "out": [{"text": unit, "start": s, "end": e}, ...]
#
# It runs as its own process, so the aligner may live in another venv (qwen-asr pins its own transformers):
# PIXSCI_ALIGN_PYTHON=/path/to/python. pixel_kit/words.py maps the units back to the written words.
# Install: pip install qwen-asr (PyTorch, CPU is enough). The first run downloads ~1.8 GB from Hugging Face.

import json, os, subprocess, sys

MODEL = "Qwen/Qwen3-ForcedAligner-0.6B"
PITFALL = ("The aligner is not installed. Install it into a venv with Python 3.10 to 3.12:\n"
           "  <venv>/bin/pip install qwen-asr\n"
           "and set PIXSCI_ALIGN_PYTHON=<venv>/bin/python (or install it into .venv).\n"
           "Without it, beats on words and subtitles use estimated word times.")


def run(jobs, workdir):
    """Aligns jobs in a child process. Returns True if it ran, False if the aligner is missing."""
    if not jobs:
        return True
    py = os.environ.get("PIXSCI_ALIGN_PYTHON", sys.executable)
    p = os.path.join(workdir, "align-jobs.json")
    json.dump(jobs, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run([py, os.path.abspath(__file__), p])
    if r.returncode == 3:
        print(PITFALL)
        return False
    if r.returncode != 0:
        raise SystemExit(f"alignment failed (exit {r.returncode})")
    return True


def main(path):
    # this file's folder holds modules (model.py, timing.py...) that would shadow the aligner's imports
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]
    try:
        import torch
        from qwen_asr import Qwen3ForcedAligner
    except ImportError as e:
        print(e)
        sys.exit(3)
    jobs = json.load(open(path, encoding="utf-8"))
    m = Qwen3ForcedAligner.from_pretrained(MODEL, dtype=torch.float32, device_map="cpu")
    for j in jobs:
        res = m.align(audio=j["wav"], text=j["text"], language=j.get("lang", "English"))[0]
        items = [{"text": it.text, "start": float(it.start_time), "end": float(it.end_time)} for it in res.items]
        json.dump(items, open(j["out"], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"aligned {os.path.basename(j['wav'])}: {len(items)} units", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
