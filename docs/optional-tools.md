# Optional tools

pixel_science works without anything on this page: `requirements.txt` and ffmpeg render every video.
The tools below are free, open source, and run locally. Add them only when a video needs a voice or subtitles.

| Need | Tool | Status here | License | Runs on |
|---|---|---|---|---|
| Voice-over from text (English) | [Kokoro](https://github.com/hexgrad/kokoro) 82M | built in: `pixsci.py voice`, `render --voice` (README, Voice) | Apache-2.0 | CPU, Mac, Linux |
| Text from a recording | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) large-v3-turbo; on a Mac [mlx-whisper](https://pypi.org/project/mlx-whisper/) | not built in | MIT | CPU, Apple GPU |
| Word timing for a known text (forced alignment) | [Qwen3-ForcedAligner-0.6B](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B) via [qwen-asr](https://pypi.org/project/qwen-asr/); on a Mac [mlx-qwen3-asr](https://github.com/moona3k/mlx-qwen3-asr) | not built in | Apache-2.0 | CPU, CUDA, Apple GPU |
| Word timing, Russian only, small | [GigaAM](https://github.com/salute-developers/GigaAM) CTC as ONNX ([sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)) | not built in | MIT | CPU |
| Burned-in subtitles in a non-pixel style | ASS file + ffmpeg with libass; or [pycaps](https://pypi.org/project/pycaps-ai/) | not built in | LGPL / MIT | CPU |

## Subtitles and word timing

Whisper is good at the words and weak at their timing: its word times come from the model's attention,
not from the sound. On a 191 s Russian voice recording it stretched a word over the pause before it at 45%
of the pauses, and once started a word 4.5 s early. Subtitles and voice cues need the time a word is heard.

The pipeline that fixes this:

1. Transcribe with Whisper (or take the voice-over text you already have).
2. Correct the text: names, gene and protein names, punctuation.
3. Align the corrected text to the audio with Qwen3-ForcedAligner, in pieces of at most 5 minutes cut at pauses.
   Before aligning, write digits and Latin letters as they are spoken ("CDK4" as "си ди кей четыре" in Russian),
   and put the written form back afterwards.
4. Split into subtitle lines: at most 2 lines of 42 characters, 1 to 7 s each, breaks at pauses and punctuation;
   2 to 4 words per cue for vertical videos. Write SRT for YouTube and ASS for burning in.
5. Burn in: draw the words with `pixel_kit` in the pixel font, or use ffmpeg with the ASS file.

Measured on that recording (start of the word after a pause, against pauses found from loudness):

| Tool | Median error | Pauses swallowed by a word |
|---|---|---|
| faster-whisper large-v3-turbo, word timestamps | 329 ms | 45% |
| GigaAM v2 CTC, recognition | 102 ms | 0% |
| GigaAM v2 CTC, alignment of the Whisper text | 179 ms | 19% |

Qwen3-ForcedAligner reports 40 ms average error on Russian and 38 ms on English
([Qwen3-ASR report](https://arxiv.org/html/2601.21337v1)); it is not yet measured on our recordings.

Not recommended: stable-ts (archived in May 2026), ctc-forced-aligner with its default MMS model
(weights are CC-BY-NC, so no monetized channel), WhisperX for Russian (older alignment model, digits lose timing).

## Install

Python 3.10 to 3.12 in `.venv`, as for the voice.

```bash
.venv/bin/pip install faster-whisper                 # text from a recording
.venv/bin/pip install qwen-asr                       # Qwen3-ForcedAligner (PyTorch: Linux, CPU or CUDA)
.venv/bin/pip install mlx-qwen3-asr                  # the same on a Mac with Apple Silicon
.venv/bin/pip install sherpa-onnx kaldi-native-fbank # GigaAM CTC
brew install ffmpeg-full                             # Mac: ffmpeg with libass, needed to burn in ASS subtitles
```

Models download on first use: Kokoro about 330 MB, Qwen3-ForcedAligner about 1.8 GB, Whisper large-v3-turbo
about 1.6 GB. GigaAM and Parakeet ONNX models come from the sherpa-onnx releases on GitHub.

## In a cloud session

A Claude Code cloud environment blocks hosts that are not on its allow list. Models load from Hugging Face,
so allow these domains in the environment's Network access (Limited level, package managers allowed):

- `huggingface.co`
- `*.hf.co` (the model files themselves)

GitHub release downloads (sherpa-onnx models) work without extra domains. A new network setting applies
to sessions started after the change. Cloud machines have no GPU: Kokoro and the aligners run on CPU,
slower than on a Mac but fine for a test of a few minutes of audio.
