#!/usr/bin/env python3
"""synth_sfx.py — synthesises the reel sound effects that the lesson kit lacks (pop, ding, whoosh, boom, riser).

Usage: python3 synth_sfx.py OUT_DIR
Everything is generated from sines and filtered noise (no third-party samples, nothing to license).
Each file is 48 kHz stereo, levelled against the lessons' tick (LEVEL); its peak sits near the start so mix_sfx_reel.py can align it on an event time.
"""
import sys, wave
from pathlib import Path
import numpy as np

SR = 48000
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


# loudest 100 ms (RMS dBFS) of each sound, set against the lessons' tick (-25.8) so that one mix gain serves them all
LEVEL = {"pop": -25.0, "ding": -23.0, "whoosh": -26.0, "boom": -17.0, "riser": -26.0}


def save(name, x, width=0.0):
    win = int(0.1 * SR)
    loud = max(np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, max(1, len(x) - win), win // 4))
    x = x * 10 ** (LEVEL[name] / 20) / loud
    # a little stereo width: the right channel is delayed by `width` ms
    d = int(width * SR / 1000)
    st = np.stack([x, np.concatenate([np.zeros(d), x[:len(x) - d]]) if d else x], axis=1)
    with wave.open(str(out / f"{name}.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype(np.int16).tobytes())


def t(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))


def bandsweep(x, f0, f1):
    """noise through a band-pass whose centre glides f0 → f1 (done in short overlapping blocks)."""
    n, hop = len(x), 1024
    y = np.zeros(n); win = np.hanning(2 * hop)
    for i in range(0, n - 2 * hop, hop):
        fc = f0 * (f1 / f0) ** (i / n)
        seg = x[i:i + 2 * hop] * win
        S = np.fft.rfft(seg); f = np.fft.rfftfreq(len(seg), 1 / SR)
        S *= np.exp(-0.5 * (np.log(np.maximum(f, 1) / fc) / 0.45) ** 2)
        y[i:i + 2 * hop] += np.fft.irfft(S, len(seg))
    return y


# pop: a short pitched bubble, 900 → 300 Hz in 60 ms
tt = t(0.09)
f = 300 + 600 * np.exp(-tt / 0.018)
pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.022) * (1 - np.exp(-tt / 0.0015))
save("pop", pop)

# ding: a phone-like notification, two bell partials then a second higher note
tt = t(0.9)
def bell(fr, d):
    return (np.sin(2 * np.pi * fr * tt) + 0.35 * np.sin(2 * np.pi * fr * 2.76 * tt) * np.exp(-tt / 0.05)) * np.exp(-tt / d) * (1 - np.exp(-tt / 0.002))
ding = bell(1318.5, 0.22) + np.concatenate([np.zeros(int(0.11 * SR)), bell(1975.5, 0.30)[:len(tt) - int(0.11 * SR)]])
save("ding", ding, width=0.4)

# whoosh: noise swept up then down, 0.55 s, peak at ~0.30 s
tt = t(0.6)
env = np.exp(-0.5 * ((tt - 0.30) / 0.11) ** 2)
wh = bandsweep(rng.standard_normal(len(tt)), 500, 3800) * env
save("whoosh", wh, width=0.6)

# boom: a sub drop for the big reveal (80 → 38 Hz) with a soft noise transient
tt = t(1.2)
f = 38 + 42 * np.exp(-tt / 0.12)
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.38) * (1 - np.exp(-tt / 0.004))
boom += 0.25 * lowpass(rng.standard_normal(len(tt)), 900) * np.exp(-tt / 0.03)
save("boom", boom)

# riser: 1.2 s of noise rising in pitch and level, cut dead at its peak (the event time = the end)
tt = t(1.2)
ri = bandsweep(rng.standard_normal(len(tt)), 300, 5000) * (tt / tt[-1]) ** 2.2
ri[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
save("riser", ri, width=0.6)
print("pop ding whoosh boom riser →", out)
