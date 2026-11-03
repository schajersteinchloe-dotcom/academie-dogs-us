#!/usr/bin/env python3
"""Exercice · Le rappel: three rushes (rappel1, rappel2, rappel3) made into one structured lesson.

The exercises are spread over the three rushes and broken up by asides (« Laisse-le comme ça », « fais un stop le temps
qu'il passe », another dog, « Excuse-moi… », « Cut. »). The lesson takes them back in teaching order, one block per part:
  0 the hook: Woody running to her (rappel3, « juste un rush pour la vidéo d'avant »)
  1 the intro and the long line (rappel1)
  2 the recall on a walk: what to do (rappel1), the two demos (rappel2)
  3 with a distraction: treats on the ground, the demo, why, the second try (rappel2)
  4 from further away, 5 two more recalls on the line (rappel3). The failed off-line test (« Woody, au pied ! Non, tu
    vois, pas encore… il faudrait le faire avec une longe ») is left out: the lesson shows the exercise, not the misses
Raw timeline = the three rushes joined (src/raw-offsets.json). In each block:
  KEEP  ranges whose words are kept; pauses longer than MAX_GAP are cut on the voice
  SOLID ranges played whole: the demos (Woody comes back, the treats, the praise)

Writes assets/derush/raw.segments.json (in block order) and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -38.0   # outdoors: the floor sits around -45 dB
OFF = json.loads((ROOT / "src" / "raw-offsets.json").read_text())   # {"1": 0, "2": …, "3": …}

# (rush, a, b, kind): kind "k" = words kept, pauses cut; "s" = played whole
BLOCKS = [
    [(3, 0.20, 6.80, "s")],                                   # « Woody ? Ok ! Ouais ! Super ! » he runs to her
    [(1, 8.15, 15.90, "k"),                                   # « On se retrouve… avec une longe au début et un chiot. »
     (1, 16.20, 21.30, "k"),                                  # « Donc on va faire appel à Woody… comment on travaille le rappel. »
     (1, 28.50, 29.60, "k")],                                 # « Donc on se munit de la longe. »
    [(1, 49.80, 56.30, "k"),                                  # « Donc ce qu'on va faire maintenant… de le rappeler, »
     (2, 0.38, 4.00, "s"),                                    # « On fait la balade, c'est parti. Allez. »
     (2, 13.00, 23.00, "s"),                                  # far: « Woody, au pied. » he comes back, « Ouais, super. C'est bien. »
     (2, 30.20, 35.20, "s"),                                  # « Woody, au pied. Oui, très bien. »
     (2, 39.10, 41.00, "k")],                                 # « Ça, c'est la manière la plus simple de faire. »
    [(2, 44.80, 54.20, "k"),                                  # « Maintenant, si vous êtes seul… l'autre va pouvoir le rappeler. »
     (2, 54.55, 55.00, "k"),                                  # « Je vais vous montrer. »
     (2, 59.30, 83.10, "s"),                                  # the treats shown and put down, she backs off, calls, he comes, eats
     (2, 83.12, 100.00, "k"),                                 # « L'objectif ici… qu'il puisse revenir. »
     (2, 100.60, 101.30, "k"),                                # « On recommence. »
     (2, 127.80, 136.60, "s")],                               # far: « Woody, au pied. Oui, super, c'est bien. Vas-y, vas-y, vas-y. »
    [(3, 35.80, 41.50, "s")],                                 # from far away: « Woody, au pied ! Oui, super ! »
    [(3, 120.60, 124.60, "s"),                                # on the line: « Woody ? Ok. Oui, super. »
     (3, 133.20, 145.20, "s")],                               # « Woody ? Au pied. Oui. Très bien. »
]
# (rush, start): the transcript hears the name wrong; "" keeps the sound, no caption
WORDS = {(1, 8.17): "On", (1, 16.23): "Donc", (1, 49.84): "Donc", (2, 0.40): "On", (2, 17.43): "Woody,", (2, 17.55): "",
         (2, 31.38): "Woody,", (2, 54.61): "Je", (3, 120.80): "Woody", (3, 133.65): "Woody", (3, 140.92): "Au"}

words = []
for n in (1, 2, 3):
    for w in json.loads((ROOT / "src" / f"rappel{n}.json").read_text())["words"]:
        words.append(dict(w, rush=n, local=w["start"], start=w["start"] + OFF[str(n)], end=w["end"] + OFF[str(n)]))
words.sort(key=lambda w: w["start"])
merged = []
for w in words:
    text = w["text"].replace("«", "").replace("»", "").strip()
    if not text:
        continue
    if merged and not re.search(r"\w", text) and merged[-1]["rush"] == w["rush"]:   # punctuation tokens join their word
        merged[-1]["text"] += text
    else:
        merged.append(dict(w, text=text))
words = merged
ranges = [(bi, OFF[str(n)] + a, OFF[str(n)] + b, kind) for bi, blk in enumerate(BLOCKS) for n, a, b, kind in blk]
inside = lambda t, rs: any(a <= t <= b for a, b in rs)
for w in words:
    w["text"] = WORDS.get((w["rush"], round(w["local"], 2)), w["text"])
    w["block"] = next((bi for bi, a, b, _ in ranges if a <= w["start"] <= b), None)
    w["keep"] = w["block"] is not None
for w, nxt in zip(words, words[1:]):           # a stretched word never runs into the next one
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))

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


dropped = [w for w in words if not w["keep"]]
out = []
for bi in range(len(BLOCKS)):
    keepr = [(a, b) for b_, a, b, k in ranges if b_ == bi and k == "k"]
    solid = [[a, b] for b_, a, b, k in ranges if b_ == bi and k == "s"]
    segs = []
    bw = [w for w in words if w["block"] == bi and inside(w["start"], keepr)]
    for w in bw:
        ri = next(i for i, (a, b) in enumerate(keepr) if a <= w["start"] <= b)
        w["end"] = min(w["end"], keepr[ri][1] + 0.2)   # a word stretched over the next pause stays in its range
        rs = runs(w["start"], w["end"])
        w["end"] = min(w["end"], rs[-1][1] + 0.03)
        for a, b in rs:
            if segs and segs[-1][2] == ri and a - segs[-1][1] <= MAX_GAP:   # never across two kept ranges
                segs[-1][1] = max(segs[-1][1], b)
            else:
                segs.append([a, b, ri])
    segs = [[a, b] for a, b, _ in segs]
    for s in segs:                              # margins, never over a dropped word, never out of the kept range
        lo = max([w["end"] for w in dropped if w["end"] <= s[0]], default=0.0)
        hi = min([w["start"] for w in dropped if w["start"] >= s[1]], default=1e9)
        ka, kb = min(keepr, key=lambda r: 0 if r[0] - 0.05 <= s[0] <= r[1] else min(abs(s[0] - r[0]), abs(s[0] - r[1])))
        s[0] = max(s[0] - PRE, min(lo + 0.02, s[0] - 0.02), ka - 0.05)
        s[1] = min(s[1] + POST, max(hi - 0.02, s[1] + 0.02), kb + 0.25)
    segs = [s for s in segs if s[1] - s[0] >= 0.08]
    union = []
    for a, b in sorted(segs + solid):
        if union and a <= union[-1][1] + 0.02:
            union[-1][1] = max(union[-1][1], b)
        else:
            union.append([a, b])
    out += union

CUTS = [(49.55, 49.84), (56.30, 56.70)]   # raw seconds removed whatever the voice gate says: the « Ok » before « Donc ce
                                          # qu'on va faire », the « donc » after « de le rappeler »
for ca, cb in CUTS:
    out = [p for a, b in out for p in ([[a, ca], [cb, b]] if a < ca and cb < b else
                                       [[a, min(b, ca)]] if a < ca < b else [[max(a, cb), b]] if a < cb < b else [[a, b]])]
segments = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3)} for k, (a, b) in enumerate(out)]
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(segments, indent=1))
kept = [w for w in words if w["keep"] and w["text"] and any(s["in"] - 0.03 <= w["start"] < s["out"] for s in segments)]
for w in kept:                                  # a caption never runs past the piece its word is in
    w["end"] = min(w["end"], next(s["out"] for s in segments if s["in"] - 0.03 <= w["start"] < s["out"]))
bare = lambda t: re.sub(r"[.,;:!?…]+$", "", t)
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{len(segments)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in segments):.1f} s")
print(" ".join(w["text"] for w in kept))
