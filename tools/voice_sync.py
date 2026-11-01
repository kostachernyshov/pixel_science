# Voice -> timing. A command wrapper around pixel_kit/voice.py.
#
#   python3 tools/voice_sync.py probe  voice.wav                       duration, fps, audio or not
#   python3 tools/voice_sync.py cues   transcript.srt [A B] [out.json] cues of [A, B) with pace and pauses
#   python3 tools/voice_sync.py silences voice.wav [A B]               pauses in speech (local time)
#   python3 tools/voice_sync.py extract voice.wav A B voice/part.wav  cut the voice of [A, B)
#   python3 tools/voice_sync.py mux video.mp4 voice/part.wav preview.mp4

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pixel_kit import voice


def main(a):
    cmd = a[0]
    if cmd == "probe":
        print(voice.probe(a[1]))
    elif cmd == "cues":
        start = float(voice._sec(a[2])) if len(a) > 2 else 0.0
        end = float(voice._sec(a[3])) if len(a) > 3 else None
        cues = voice.load(a[1], start, end)
        voice.table(cues)
        if len(a) > 4:
            voice.dump(cues, a[4])
            print("->", a[4])
    elif cmd == "silences":
        start = float(voice._sec(a[2])) if len(a) > 2 else 0.0
        end = float(voice._sec(a[3])) if len(a) > 3 else None
        for s, e in voice.silences(a[1], start, end):
            print(f"{s:7.2f}-{e:7.2f}  ({e - s:.2f} s)")
    elif cmd == "extract":
        print(voice.extract(a[1], voice._sec(a[2]), voice._sec(a[3]), a[4]))
    elif cmd == "mux":
        print(voice.mux(a[1], a[2], a[3]))
    else:
        print(__doc__ or open(__file__).read().split("\n\n")[0])


if __name__ == "__main__":
    main(sys.argv[1:])
