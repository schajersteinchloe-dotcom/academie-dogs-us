#!/usr/bin/env python3
"""transcribe_fw.py — word-level transcription with faster-whisper (CPU, no torch), in the format the montage scripts read.

Usage: transcribe_fw.py media.wav --out words.json [--lang fr] [--model large-v3-turbo] [--threads 4]
                        [--segments regions.json]   # [{in, out}]: transcribe each region on its own
Writes {"words": [{"text", "start", "end"}], "language", "duration"}; the text keeps its punctuation (« Non, »).
condition_on_previous_text is off so that a retake is written as it was said, not smoothed into the previous take.
Install: python3 -m venv ~/.wx/venv && ~/.wx/venv/bin/pip install faster-whisper
(the full WhisperX pulls several GB of CUDA wheels on a CPU-only machine).
"""
import argparse, json

import subprocess

import numpy as np
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument("media")
ap.add_argument("--out", required=True)
ap.add_argument("--lang", default="fr")
ap.add_argument("--model", default="large-v3-turbo")
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--segments")
args = ap.parse_args()

SR = 16000
# decoded with ffmpeg (faster-whisper's own decoder breaks on recent PyAV releases)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", args.media, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=args.threads)
slices = [(0.0, len(audio) / SR)]
if args.segments:
    slices = [(float(s["in"]), float(s["out"])) for s in json.load(open(args.segments))]

words = []
for a, b in slices:
    part = audio[int(a * SR):int(b * SR)]
    if len(part) < SR // 4:
        continue
    segs, _ = model.transcribe(part, language=args.lang, beam_size=5, word_timestamps=True, vad_filter=not args.segments,
                               condition_on_previous_text=False)
    n = 0
    for seg in segs:
        for w in seg.words or []:
            t = w.word.strip()
            if t:
                words.append({"text": t, "start": round(a + w.start, 3), "end": round(a + w.end, 3), "p": round(w.probability, 2)})
                n += 1
    print(f"[{a:7.1f}-{b:7.1f}] {n} words", flush=True)

json.dump({"words": words, "language": args.lang, "duration": round(len(audio) / SR, 3)},
          open(args.out, "w"), ensure_ascii=False, indent=0)
print(f"{len(words)} words · {len(audio) / SR:.1f} s · {args.lang} · {args.out}")
