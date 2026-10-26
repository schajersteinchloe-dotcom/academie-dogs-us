#!/usr/bin/env python3
"""Leçon (IMG_5141), le pas bouger: cut like Chloé's own edit « assisapprentissage.mp4 ».

Her edit keeps the demonstrations whole (the dog obeying, 1-2 s of silence after a command) and cuts everything
around them tight; Nala's interruptions and the abandoned takes go. Here:
  KEEP  rush ranges whose words are kept (word starts in [a, b]); inside them, pauses longer than MAX_GAP are cut
        on the voice (WhisperX stretches word ends over the silence)
  SOLID rush ranges played whole, pauses included: Woody sitting, staying, her stepping back

Writes assets/derush/raw.segments.json and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -45.0

KEEP = [
    (60.70, 78.00),    # « Maintenant, je vais vous expliquer… le pas bouger, c'est très très simple » (« Ok, du coup » goes)
    (78.90, 92.00),    # « Vous prenez votre chiot… un pas en arrière. Pas bouger. Très bien. »
    (93.50, 95.20),    # « Ensuite, vous allez faire deux pas en arrière. » (Woody gets up: the « Non. Non. » try goes)
    (145.00, 160.00),  # the try where he stays: « Pas bouger. Très bien, super. Donc ça, le principe… »
    (160.40, 167.60),  # « Le pas bouger peut aussi se bosser en durée… votre chien en pas bouger. » (« Vous allez… » goes)
    (172.00, 186.00),  # « Pas bouger. Vous allez vous écarter… en durée, en distance et en distraction. »
    (211.80, 214.18),  # « Et la distraction, qu'est-ce que ça va pouvoir être ? » (the first try, Nala, goes)
    (215.50, 240.00),  # « pour la distraction… je vais juste tenir Woody au collier… ceci est une distraction. »
    (267.80, 287.00),  # « Je précise que ces exercices… des challenges au quotidien dans la communauté et toutes les semaines. »
]
SOLID = [
    (75.90, 79.00),    # « …de plus en plus. Le pas bouger, c'est très très simple » and she gets up (no jump cut)
    (79.00, 92.00),    # she sits him down, steps back, « Pas bouger. Très bien. »
    (145.30, 152.25),  # two steps back and back to him
    (171.90, 176.20),  # « Pas bouger » and she walks away (no jump cut while she walks)
    (225.50, 226.50),  # « Assis. »…
    (228.70, 239.70),  # …he sits (2 s of him standing still cut), stays, « Très bien, vas-y », the treat thrown
]
FIX = {"simulant": "stimulant"}
CAPITAL = (60.78, 215.60, 149.92, 151.40, 172.01, 173.69)   # sentence starts the cut creates or the commands' transcript lacks

# words: the whole-rush transcript, and inside the demo passages the one transcribed passage by passage
full = json.loads((ROOT / "src" / "transcript-full.json").read_text())["words"]
regs = json.loads((ROOT / "src" / "regions.json").read_text())
reg_words = json.loads((ROOT / "src" / "transcript-regions.json").read_text())["words"]
inner = [(r["in"] + 0.5, r["out"] - 0.5) for r in regs]
inside = lambda t, rs: any(a <= t <= b for a, b in rs)
reg_kept = [w for w in reg_words if inside(w["start"], inner)]
twin = lambda w: any(abs(w["start"] - r["start"]) < 0.15 and w["text"].lower().strip(".,?!") == r["text"].lower().strip(".,?!")
                     for r in reg_kept)
words = sorted([w for w in full if not inside(w["start"], inner) and not twin(w)] + reg_kept, key=lambda w: w["start"])
merged = []
for w in words:                     # punctuation tokens join their word
    if merged and not re.search(r"\w", w["text"]):
        merged[-1]["text"] += w["text"]
    else:
        merged.append(dict(w))
words = merged
for w in words:
    w["text"] = FIX.get(w["text"].rstrip(".,?!"), w["text"].rstrip(".,?!")) + w["text"][len(w["text"].rstrip(".,?!")):]
    if round(w["start"], 2) in CAPITAL:
        w["text"] = w["text"][:1].upper() + w["text"][1:]
    w["keep"] = inside(w["start"], KEEP)
END = {91.63: 92.00, 95.14: 95.60}   # « bien », « arrière »: a breath, then the start of « Non », follow them
for w in words:
    w["end"] = END.get(round(w["start"], 2), w["end"])
for w, nxt in zip(words, words[1:]):           # a stretched word never runs into the next one
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))
for a, b in SOLID:
    assert all(w["keep"] for w in words if a <= w["start"] < b), f"a dropped word inside solid {a}-{b}"

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
    return out or [(s, min(e, s + 0.5))]


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
# margins, never over a dropped word
dropped = [w for w in words if not w["keep"]]
for s in segs:
    lo = max([w["end"] for w in dropped if w["end"] <= s[0]], default=0.0)
    hi = min([w["start"] for w in dropped if w["start"] >= s[1]], default=1e9)
    s[0], s[1] = max(s[0] - PRE, min(lo + 0.02, s[0] - 0.02)), min(s[1] + POST, max(hi - 0.02, s[1] + 0.02))
# solid ranges play whole; overlapping pieces become one
segs = sorted(segs + [[a, b] for a, b in SOLID])
union = []
for a, b in segs:
    if union and a <= union[-1][1] + 0.02:
        union[-1][1] = max(union[-1][1], b)
    else:
        union.append([a, b])

out = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3)} for k, (a, b) in enumerate(union)]
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(out, indent=1))
kept = [w for w in words if w["keep"] and any(s["in"] - 0.03 <= w["start"] < s["out"] for s in out)]
bare = lambda t: re.sub(r"[.,;:!?…]+$", "", t)  # captions without punctuation, like the other lessons
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{len(out)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in out):.1f} s")
print(" ".join(w["text"] for w in kept))
