#!/usr/bin/env python3
"""mix_sfx_reel.py — lays sound effects under the voice of a rendered reel (the lessons' mix-sfx.py, any sound set).

Usage: python3 mix_sfx_reel.py video.mp4 --events sfx-events.json --sounds DIR [--out …-sfx.mp4] [--gain dB]
events: [{"t": seconds, "sound": "pop", "db": -3 (optional, per event)}]. `t` is where the sound's peak lands
(tick 10 ms, swish 50 ms into their files; the others: their loudest 10 ms window; a riser ends on `t`).
Effects are set relative to the voice exactly like the lessons (REF_VOICE_DB), the video stream is copied.
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--events", required=True); ap.add_argument("--sounds", required=True)
ap.add_argument("--out"); ap.add_argument("--gain", type=float, default=0.0)
args = ap.parse_args()
SR, REF_VOICE_DB = 48000, -20.8
FIXED = {"tick": 0.010, "swish": 0.050}


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
base = voice_db - REF_VOICE_DB + args.gain
events = json.loads(Path(args.events).read_text())
sounds, offs = {}, {}
for name in {e["sound"] for e in events}:
    s = decode(Path(args.sounds) / f"{name}.wav")
    sounds[name] = s
    if name in FIXED:
        offs[name] = FIXED[name]
    elif name == "riser":
        offs[name] = len(s) / SR
    else:
        e = np.convolve(np.abs(s).mean(axis=1), np.ones(480) / 480, "same")
        offs[name] = int(np.argmax(e)) / SR
for e in events:
    s = sounds[e["sound"]] * 10 ** ((base + e.get("db", 0)) / 20)
    a = int(round((e["t"] - offs[e["sound"]]) * SR))
    if a < 0:
        s, a = s[-a:], 0
    b = min(len(mix), a + len(s))
    mix[a:b] += s[:b - a]
peak = np.abs(mix).max()
over = np.abs(mix) > 0.85
mix[over] = np.sign(mix[over]) * (0.85 + 0.05 * np.tanh((np.abs(mix[over]) - 0.85) / 0.05))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
               input=mix.astype(np.float32).tobytes(), check=True)
print(f"{len(events)} effects · voice {voice_db:.1f} dBFS → effects {base:+.1f} dB · peak {20 * np.log10(peak):.1f} dBFS, {int(over.sum())} samples rounded → {out}")
