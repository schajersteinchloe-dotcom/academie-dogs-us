#!/usr/bin/env python3
"""mix-sfx.py — lays the lesson's sound effects under the voice of a rendered lesson.

Usage: python3 scripts/mix-sfx.py renders/lesson.mp4 [--events assets/sfx-events.json] [--sounds assets/sfx] [--out …-sfx.mp4]

The sounds come from the reference lesson (« L'équipement de ton chiot »): tick.wav is its double tick (the mean of
13 aligned occurrences, so her voice cancels out), swish.wav its opening swish (above 1 kHz, where the voice is absent).
Their level is kept relative to the voice: in the reference the voice sits at REF_VOICE_DB (median RMS over 400 ms),
so the effects get the difference between this lesson's voice and that one. The video stream is copied untouched.
"""
import argparse, json, subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--events", default=str(ROOT / "assets" / "sfx-events.json"))
ap.add_argument("--sounds", default=str(ROOT / "assets" / "sfx"))
ap.add_argument("--out", default=None)
ap.add_argument("--gain", type=float, default=0.0, help="extra dB on every effect (negative = softer)")
args = ap.parse_args()

SR = 48000
REF_VOICE_DB = -20.8                       # the reference's voice, median 400 ms RMS of voiced windows
OFFSET = {"tick": 0.010, "swish": 0.050}   # file start → the sound's peak, which is what events give


def decode(path, channels=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", str(channels), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).copy()


video = Path(args.video)
out = Path(args.out) if args.out else video.with_name(video.stem + "-sfx" + video.suffix)
mix = decode(video)
mono = mix.mean(axis=1)
win, hop = int(0.4 * SR), int(0.1 * SR)
rms = np.array([np.sqrt(np.mean(mono[i:i + win] ** 2)) for i in range(0, len(mono) - win, hop)])
voice_db = 20 * np.log10(np.median(rms[rms > 10 ** (-40 / 20)]))
gain = 10 ** ((voice_db - REF_VOICE_DB + args.gain) / 20)

sounds = {name: decode(Path(args.sounds) / f"{name}.wav") for name in OFFSET}
events = json.loads(Path(args.events).read_text())
for e in events:
    s = sounds[e["sound"]] * gain
    a = int(round((e["t"] - OFFSET[e["sound"]]) * SR))
    if a < 0:
        s, a = s[-a:], 0
    b = min(len(mix), a + len(s))
    mix[a:b] += s[:b - a]
peak = np.abs(mix).max()
# never clip, without lowering the voice: only the few samples of a tick above 0.85 are rounded off (max 0.9, headroom for the AAC encode)
over = np.abs(mix) > 0.85
mix[over] = np.sign(mix[over]) * (0.85 + 0.05 * np.tanh((np.abs(mix[over]) - 0.85) / 0.05))

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
               input=mix.astype(np.float32).tobytes(), check=True)
print(f"{len(events)} effects · voice {voice_db:.1f} dBFS → effects {20 * np.log10(gain):+.1f} dB · peak {20 * np.log10(peak):.1f} dBFS, {int(over.sum())} samples rounded → {out}")
