#!/usr/bin/env python3
"""Rough cut of a talking-head reel: every pause longer than MAX_GAP goes, cut on the voice (WhisperX stretches word ends
over the silence). Config in <reel>/derush.json:
  words    the WhisperX transcript of the rush (src/rush.json)
  fix      {"start": "text"}: a word heard wrong; "" keeps the sound, no caption
  insert   [{text, start, end}]: a word the whole-rush transcript missed (found by transcribing the passage alone)
  drop     [[a, b]]: words to cut (start in [a, b])
  solid    [[a, b]]: played whole, pauses included (she turns the camera to the dog)
  cut      [[a, b]]: removed even when the voice gate hears sound there (wind on the mic)
Writes assets/derush/raw.segments.json and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, sys, wave
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1]).resolve()
D = ROOT / "assets" / "derush"
cfg = json.loads((ROOT / "derush.json").read_text())
MAX_GAP, PRE, POST, VOICE_DB = cfg.get("max_gap", 0.35), 0.08, 0.12, cfg.get("voice_db", -40.0)
inside = lambda t, rs: any(a <= t <= b for a, b in rs)

words = json.loads((ROOT / cfg["words"]).read_text())["words"] + cfg.get("insert", [])
words = sorted(words, key=lambda w: w["start"])
merged = []
for w in words:
    if merged and not re.search(r"\w", w["text"]):     # punctuation tokens join their word
        merged[-1]["text"] += w["text"]
    else:
        merged.append(dict(w))
words = merged
for w in words:
    w["text"] = cfg.get("fix", {}).get(f'{w["start"]:.2f}', w["text"])
    w["keep"] = not inside(w["start"], cfg.get("drop", []))
for w, nxt in zip(words, words[1:]):           # a stretched word never runs into the next one
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))

# voice envelope, 10 ms
wv = wave.open(str(ROOT / "src" / "audio16k.wav"))
pcm = np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768
n = len(pcm) // 160
voiced = 20 * np.log10(np.sqrt((pcm[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9) > VOICE_DB


def runs(s, e):
    """Voiced stretches inside [s, e], holes under 150 ms closed."""
    i0, i1 = max(0, int((s - 0.03) * 100)), min(n, int((e + 0.03) * 100) + 1)
    out, cur = [], None
    for i in range(i0, i1):
        if voiced[i]:
            if cur and i - cur[1] <= 15:
                cur[1] = i + 1
            else:
                if cur:
                    out.append(cur)
                cur = [i, i + 1]
    if cur:
        out.append(cur)
    out = [(x / 100, y / 100) for x, y in out if y - x >= 5]
    return out or [(s, min(e, s + 0.4))]


segs = []
for i, w in enumerate(words):
    if not w["keep"]:
        continue
    rs = runs(w["start"], w["end"])
    w["end"] = min(w["end"], rs[-1][1] + 0.03)      # captions end where the voice does
    prev_dropped = i > 0 and not words[i - 1]["keep"]
    for a, b in rs:
        if segs and not prev_dropped and a - segs[-1][1] <= MAX_GAP:
            segs[-1][1] = max(segs[-1][1], b)
        else:
            segs.append([a, b])
        prev_dropped = False
dropped = [w for w in words if not w["keep"]]
for s in segs:                                  # margins, never over a dropped word
    lo = max([w["end"] for w in dropped if w["end"] <= s[0]], default=0.0)
    hi = min([w["start"] for w in dropped if w["start"] >= s[1]], default=1e9)
    s[0], s[1] = max(s[0] - PRE, min(lo + 0.02, s[0] - 0.02), 0.0), min(s[1] + POST, max(hi - 0.02, s[1] + 0.02))
segs = sorted(segs + [list(r) for r in cfg.get("solid", [])])
union = []
for a, b in segs:
    if union and a <= union[-1][1] + 0.02:
        union[-1][1] = max(union[-1][1], b)
    else:
        union.append([a, b])

for ca, cb in cfg.get("cut", []):
    union = [p for a, b in union for p in ([[a, ca], [cb, b]] if a < ca and cb < b else [[a, b]])]
out = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3)} for k, (a, b) in enumerate(union)]
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(out, indent=1))
kept = [w for w in words if w["keep"] and w["text"] and any(s["in"] - 0.03 <= w["start"] < s["out"] for s in out)]
for w in kept:                                  # a caption never runs past the piece its word is in
    w["end"] = min(w["end"], next(s["out"] for s in out if s["in"] - 0.03 <= w["start"] < s["out"]))
bare = lambda t: re.sub(r"[.,;:!…]+$", "", t.replace("...", ""))
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{len(out)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in out):.1f} s")
print(" ".join(w["text"] for w in kept))
