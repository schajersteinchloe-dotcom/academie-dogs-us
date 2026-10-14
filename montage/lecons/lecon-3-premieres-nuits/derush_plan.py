#!/usr/bin/env python3
"""Leçon 3 (IMG_4993), les premières nuits: the takes kept after reading every line, cut on the voice.

Writes assets/derush/raw.segments.json and raw.captions.json for scripts/stage.py.
Selections are rush times: a take, or the words of a take whose start lies in [a, b].
Inside what is kept, every pause longer than MAX_GAP (measured on the voice, not on the
word timings, which WhisperX stretches over pauses) is removed.
"""
import json, subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
takes = json.loads((D / "takes.json").read_text())

MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -48.0

ALL = None
KEEP = [  # (take, a, b): words of the take starting in [a, b]; ALL = the whole take
    # 1-4: applause, « On se réinstalle… », « Et c'est parti » go
    (5, ALL),
    (7, ALL),             # the full version of the sleeping place; 8-9 say it again, shorter
    (10, ALL),
    (11, 146.90, 155.00), # up to « s'agiter »: « gérer la gestion » is corrected in 12-14
    (14, 168.70, 172.75), # « …gérer la propreté. Ça va être plus simple pour vous. » (« Soit… des alarmes » scrapped in 15)
    (15, 181.05, 187.60), # from « La gestion de la propreté » (« On s'en fiche ça » goes); 16 belongs to the scrapped alarm idea
    (21, ALL),            # her redo of the summary: 18 « c'était nul ça, on refait »
    (23, ALL),            # 13, 17, 22, 24: off-script remarks
]
INSERT = {}
WORDS = {}
FIX = {"pleuré": "pleurer"}
CAPITAL = ()

# voice envelope, 10 ms
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(D / "raw.mp4"), "-vn", "-ac", "1", "-ar", "16000",
                      "-af", "highpass=f=120", "-f", "s16le", "-"], capture_output=True, check=True).stdout
a = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
n = len(a) // 160
env = 20 * np.log10(np.sqrt(np.mean(a[:n * 160].reshape(n, 160) ** 2, axis=1)) + 1e-9)
voiced = env > VOICE_DB


def runs(s, e):
    """Voiced stretches inside [s, e], tiny holes closed."""
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
    return out or [(s, min(e, s + 0.5))]


all_words, kept = [], []
for ti, t in enumerate(takes, 1):
    own = [dict(w) for w in t.get("words", [])]
    if ti in WORDS:
        own = [dict(w) for w in WORDS[ti]]
    ws = sorted(own + INSERT.get(ti, []), key=lambda w: w["start"])
    for w in ws:
        w["text"] = FIX.get(w["text"], w["text"])
        if round(w["start"], 2) in CAPITAL:
            w["text"] = w["text"][:1].upper() + w["text"][1:]
        w["take"] = ti
    all_words.extend(ws)
all_words.sort(key=lambda w: w["start"])
for take, *rng in KEEP:
    for w in all_words:
        if w["take"] == take and (rng[0] is ALL or rng[0] <= w["start"] <= rng[1]):
            w["keep"] = True

segments = []
for i, w in enumerate(all_words):
    if not w.get("keep"):
        continue
    prev_dropped = i > 0 and not all_words[i - 1].get("keep")
    for rs, re_ in runs(w["start"], w["end"]):
        if segments and not prev_dropped and rs - segments[-1]["out"] <= MAX_GAP:
            segments[-1]["out"] = max(segments[-1]["out"], re_)
        else:
            segments.append({"in": rs, "out": re_, "first": i})
        prev_dropped = False
    segments[-1]["last"] = i

# margins, never over a dropped word nor the previous segment
for k, s in enumerate(segments):
    lo = all_words[s["first"] - 1]["end"] if s["first"] > 0 and not all_words[s["first"] - 1].get("keep") else 0.0
    hi = all_words[s["last"] + 1]["start"] if s["last"] + 1 < len(all_words) and not all_words[s["last"] + 1].get("keep") else 1e9
    s["in"] = round(max(s["in"] - PRE, lo, segments[k - 1]["out"] if k else 0.0), 3)
    s["out"] = round(min(s["out"] + POST, hi), 3)
for k in range(len(segments) - 1):
    if segments[k]["out"] > segments[k + 1]["in"]:
        mid = round((segments[k]["out"] + segments[k + 1]["in"]) / 2, 3)
        segments[k]["out"], segments[k + 1]["in"] = mid, mid

out = [{"name": f"s{k + 1:03d}", "in": s["in"], "out": s["out"]} for k, s in enumerate(segments)]
(D / "raw.segments.json").write_text(json.dumps(out, indent=1))
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": w["text"], "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in all_words if w.get("keep")],
    ensure_ascii=False, indent=1))
total = sum(s["out"] - s["in"] for s in out)
print(f"{len(out)} segments · {sum(1 for w in all_words if w.get('keep'))} words kept of {len(all_words)} · {total:.1f} s")
print(" ".join(w["text"] for w in all_words if w.get("keep")))
