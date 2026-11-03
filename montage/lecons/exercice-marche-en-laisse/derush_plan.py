#!/usr/bin/env python3
"""Exercice · La marche en laisse (marchenelaisse1): one rush, cut into the exercise without the misses.

The exercises come in order but are broken up by asides (« C'est bon ? Ok, super. », « Il faut que tu me dises...
Arrête le truc là ! », « J'ai les cheveux dans les yeux, c'est un enfer. », « J'espère qu'on n'entend pas trop le vent. »,
« J'ai un peu peur de me prendre une branche… », « Cut ! On arrête ! »), restarted sentences (« Donc ça, c'est vraiment
les... », « On va vraiment travailler ce... », « si c'est... ») and one miss (Woody eating something: « Lâche. »), all
left out. One block per part:
  0 the intro: the 5 m line, « je tire = je gagne », coming back at the end of the line
  1 long line: let him live his life, reward when he comes back or walks by her side, the line tip (PVC, biotane)
  2 short leash: he has to follow, he yields to the pressure
  3 changing direction: he pulls to the side, she stays firm
  4 to remember: start somewhere calm, or he learns to pull
Raw timeline = the rush, zoomed on the far demos (kit/zoomcut.py). In each block:
  KEEP  ranges whose words are kept; pauses longer than MAX_GAP are cut on the voice
  SOLID ranges played whole: the demos

Writes assets/derush/raw.segments.json (in block order) and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -38.0   # outdoors: the floor sits around -45 dB
OFF = json.loads((ROOT / "src" / "raw-offsets.json").read_text())   # {"1": 0}

# (rush, a, b, kind): kind "k" = words kept, pauses cut; "s" = played whole
BLOCKS = [
    [(1, 5.00, 41.16, "k")],                                  # « Donc maintenant, on va parler de la marche en laisse… »
    [(1, 41.15, 41.60, "k"),                                  # « C'est parti ! »
     (1, 42.25, 52.95, "s"),                                  # « Mon loup ! Viens ! Viens, viens, viens ! Ah, t'es baveux ! Hop là ! »
     (1, 62.28, 86.30, "k"),                                  # « Pour l'instant on va le laisser faire sa vie… des regards, évidemment. »
     (1, 87.50, 91.00, "s"),                                  # « Oui, c'est bien ! »
     (1, 114.79, 127.47, "k"),                                # « Si vous n'arrivez pas à manier la longe… ça sera plus simple. »
     (1, 127.40, 136.50, "s")],                               # « Woody ! » … « Oui, super. Oui, très bien. »
    [(1, 156.08, 168.30, "k"),                                # « Ce qu'on va faire maintenant… il va devoir suivre. »
     (1, 168.20, 187.00, "s"),                                # « Ouais, c'est bien mon loupiot ! Super ! Très bien !… Très bien ça ! »
     (1, 187.65, 196.90, "k")],                               # « Donc là, vous voyez, il cède à la pression… fait à la maison. »
    [(1, 198.60, 216.20, "s")],                               # « Allez, on se balade. On change de direction… ce qu'il veut. »
    [(1, 233.80, 235.70, "k"),                                # « Donc ça, c'est vraiment les débuts de la marche en laisse. »
     (1, 238.28, 244.35, "k"),                                # « On va vraiment travailler cet aspect-là… sans trop de stimulation. »
     (1, 249.22, 250.57, "k"),                                # « parce qu'après, au fur et à mesure, »
     (1, 252.80, 267.60, "k"),                                # « si c'est dans la ville… un chien qui fera son poids adulte et qui va tirer ! »
     (1, 308.13, 320.80, "k")],                               # « Donc si vous faites ça bientôt… qui aura pris l'habitude. »
]
# (rush, start): words heard wrong; "" keeps the sound, no caption
WORDS = {(1, 5.03): "Donc", (1, 42.29): "", (1, 42.49): "",   # « Moumoumou ! », a call, not a word
         (1, 48.85): "baveux", (1, 62.30): "Pour", (1, 156.09): "Ce",
         (1, 172.62): "loupiot", (1, 252.82): "si", (1, 311.86): "poids", (1, 313.04): "tirera"}

words = []
for n in map(int, OFF):
    for w in json.loads((ROOT / "src" / f"rush{n}.json").read_text())["words"]:
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

CUTS = []                                 # raw seconds removed whatever the voice gate says
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
