#!/usr/bin/env python3
"""Annonce · Académie Dogs & Us — three versions of one announcement, each opening on a different hook.

Rushes: IMG_5295 (the hooks), IMG_5296 and IMG_5297 (the body, several retakes per sentence). Raw timeline = the three
joined (src/raw-offsets.json). Each version is a list of blocks in reading order; in each block KEEP ranges keep their
words and cut the pauses on the voice. The broken takes (« Non, c'est nul », « Gitgap… Ouh ! », « blablabla »,
« Non. », « C'est tout. ») are never inside a range.

Usage: python3 derush_plan.py v1|v2|v3 PROJECT_DIR   → PROJECT_DIR/assets/derush/raw.segments.json + raw.captions.json
"""
import json, re, sys, wave
from pathlib import Path

import numpy as np

VERSION, PROJ = sys.argv[1], Path(sys.argv[2])
SRC = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/root/videos/annonce-src")
D = PROJ / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.45, 0.10, 0.15, -45.0      # indoors, quiet room
OFF = json.loads((SRC / "raw-offsets.json").read_text())

# sentences: (rush, a, b) in the rush's own seconds
S = {
    "H1": [(5295, 0.50, 3.85)],        # « Ça fait des mois que je reçois ce genre de message. »
    "H2": [(5295, 23.27, 25.25)],      # « J'ai une grande annonce à vous faire. » (second take)
    "H3": [(5295, 26.85, 40.95)],      # « Je vais peut-être perdre des abonnés… personne ne t'explique exactement comment. »
    "J1": [(5296, 0.48, 4.90)],        # « Du coup, j'ouvre ma communauté en ligne et l'entrée est gratuite. »
    "J1b": [(5296, 1.02, 4.90)],       # the same without « Du coup, »
    "J2": [(5296, 21.32, 26.54)],      # « Si tu me suis depuis un moment… en physique avec mes clients. »
    "J3a": [(5296, 26.54, 34.40)],     # « Mais le seul problème… les mêmes erreurs se répéter et les mêmes problèmes, »
    "J3b": [(5296, 40.97, 44.25)],     # « Je voulais trouver une solution pour tous pouvoir vous aider. »
    "K1": [(5296, 57.29, 61.00),       # « Dans ma communauté, évidemment, tu vas retrouver des vidéos, mais c'est pas le plus important. »
           (5296, 75.58, 78.55),       # « Le plus important, c'est vraiment que tu comprennes ton chien, »
           (5296, 85.12, 88.00)],      # « que tu saches quoi faire et pourquoi il faut le faire. »
    "B2": [(5297, 16.60, 23.95)],      # « Depuis 2022, j'ai accompagné… et je vois toujours les mêmes galères. »
    "B3": [(5297, 25.64, 35.82)],      # « Le chien qui tire en laisse… Bref, tout ça, ça revient tout le temps. »
    "B4": [(5297, 44.08, 48.75)],      # « Alors du coup, j'ai créé l'Académie Dogs & Us. C'est une communauté en ligne. »
    "B4s": [(5297, 44.08, 46.90)],     # « Alors du coup, j'ai créé l'Académie Dogs & Us. »
    "B5": [(5297, 69.52, 72.31),       # « Dedans, tu vas retrouver mes guides gratuits. » (« D'accord ? » out)
           (5297, 72.67, 76.98)],      # « Que ce soit pour ton chiot, pour la marche en laisse, pour une adoption, pour un chien qui est réactif. »
    "B6": [(5297, 81.07, 85.07),       # « Tu vas aussi retrouver des formations vidéos complètes pas à pas »
           (5297, 90.31, 94.20)],      # « pour vraiment savoir comment et quoi faire pour éduquer ton chien. »
    "B7": [(5297, 100.88, 109.45)],    # « Et évidemment, vous allez pouvoir me retrouver en live et je vais pouvoir répondre à vos questions. »
    "B8": [(5297, 120.94, 127.12),     # « Et on n'oublie pas le plus intéressant, il y a évidemment une communauté de maîtres… que toi »
           (5297, 140.89, 142.50)],    # « et on va tous pouvoir s'entraider. »
    "B9": [(5297, 152.68, 168.80)],    # « L'objectif, c'est vraiment que tu comprennes enfin ton chien… douce comme tu l'attendais. »
    "CTA": [(5297, 186.93, 189.85),    # « Je précise que l'entrée est évidemment gratuite, »
            (5297, 209.31, 214.45)],   # « Donc, commente Académie et je t'envoie directement le lien pour rejoindre la communauté. »
}
VERSIONS = {
    "v1": ["H1", "J1", "B2", "B3", "B4s", "B5", "B6", "B7", "B8", "B9", "CTA"],
    "v2": ["H2", "J1b", "J2", "J3a", "B3", "J3b", "B4", "B5", "B6", "B7", "B8", "CTA"],
    "v3": ["H3", "B2", "B3", "B4", "K1", "B5", "B6", "B7", "B8", "CTA"],
}
# (rush, start) → corrected text; "" keeps the sound, no caption
WORDS = {(5297, 29.42): "mordille", (5296, 103.06): "parte", (5296, 103.38): "sur", (5297, 38.48): "&", (5297, 46.57): "&",
         (5297, 210.56): "Académie", (5297, 17.43): "2022,", (5297, 140.91): "et", (5297, 209.46): "donc,", (5296, 78.30): "chien,"}
WORDS.update({"v2": {(5296, 1.24): "J'ouvre"}}.get(VERSION, {}))
# (rush, start) → (start, end): the transcript's timing is off (« conseils » stretched over the silence, « Depuis »
# heard 0.36 s after its real onset at 16.66; sentence ends stretched up to the next take's first word)
TIMES = {(5297, 9.19): (9.19, 9.76), (5297, 17.02): (16.64, 17.0), (5296, 33.65): (33.65, 34.3), (5297, 48.31): (48.31, 48.6),
         (5297, 105.74): (105.74, 106.2), (5297, 189.13): (189.13, 189.8),
         (5296, 0.80): (0.80, 0.95), (5296, 1.24): (1.06, 1.62)}
# (rush, a, b) removed whatever the voice gate says: « D'accord ? » glued to « gratuits »
CUTS = [(5297, 72.08, 72.64)]

words = []
for n in (5295, 5296, 5297):
    for w in json.loads((SRC / f"IMG_{n}.json").read_text())["words"]:
        words.append(dict(w, rush=n, local=w["start"], start=w["start"] + OFF[str(n)], end=w["end"] + OFF[str(n)]))
words.sort(key=lambda w: w["start"])
merged = []
for w in words:
    text = w["text"].strip()
    if not text:
        continue
    if merged and not re.search(r"[\w&]", text) and merged[-1]["rush"] == w["rush"]:   # « ? », « ! » join their word
        merged[-1]["text"] += text
        merged[-1]["end"] = max(merged[-1]["end"], w["end"])
    else:
        merged.append(dict(w, text=text))
words = merged
ranges = []   # (order, sentence, a, b) raw seconds
for name in VERSIONS[VERSION]:
    for n, a, b in S[name]:
        ranges.append((len(ranges), name, OFF[str(n)] + a, OFF[str(n)] + b))
for w in words:
    w["text"] = WORDS.get((w["rush"], round(w["local"], 2)), w["text"])
    if (w["rush"], round(w["local"], 2)) in TIMES:
        a, b = TIMES[(w["rush"], round(w["local"], 2))]
        w["start"], w["end"] = a + OFF[str(w["rush"])], b + OFF[str(w["rush"])]
    w["range"] = next((i for i, _, a, b in ranges if a <= w["start"] <= b), None)
for w, nxt in zip(words, words[1:]):           # a stretched word never runs into the next one
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))

wv = wave.open(str(SRC / "audio16k.wav"))
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


out = []
for ri, name, ka, kb in ranges:
    others = [w for w in words if w["range"] != ri]
    segs = []
    for w in (w for w in words if w["range"] == ri):
        w["end"] = min(w["end"], kb + 0.2)
        rs = runs(w["start"], w["end"])
        w["end"] = min(w["end"], rs[-1][1] + 0.03)
        for a, b in rs:
            if segs and a - segs[-1][1] <= MAX_GAP:
                segs[-1][1] = max(segs[-1][1], b)
            else:
                segs.append([a, b])
    for s in segs:                              # margins, never over another range's word, never far out of the range
        lo = max([w["end"] for w in others if w["end"] <= s[0] + 0.01], default=0.0)
        hi = min([w["start"] for w in others if w["start"] >= s[1] - 0.01], default=1e9)
        s[0] = max(s[0] - PRE, min(lo + 0.02, s[0] - 0.02), ka - 0.05)
        s[1] = min(s[1] + POST, max(hi - 0.02, s[1] + 0.02), kb + 0.25)
    if segs:   # the range starts were set on the voice onsets (the transcript often starts a word late): trust them
        segs[0][0] = min(segs[0][0], ka)
    mine = [w for w in words if w["range"] == ri]
    for a, b in segs:   # a short run with no word starting in it is a stretched word's tail or the next take's onset
        if b - a >= 0.08 and (b - a >= 0.25 or any(a - 0.03 <= w["start"] < b for w in mine)):
            out.append([a, b, ri, name])

for n_, ca, cb in CUTS:                        # raw seconds removed whatever the voice gate says
    ca, cb = ca + OFF[str(n_)], cb + OFF[str(n_)]
    out = [p for a, b, ri, nm in out for p in ([[a, ca, ri, nm], [cb, b, ri, nm]] if a < ca and cb < b else
                                               [[a, min(b, ca), ri, nm]] if a < ca < b else [[max(a, cb), b, ri, nm]] if a < cb < b else [[a, b, ri, nm]])]

segments = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3), "sentence": nm} for k, (a, b, _, nm) in enumerate(out)]
db = lambda t: 20 * np.log10(np.sqrt((pcm[int(t * 16000):int(t * 16000) + 320] ** 2).mean()) + 1e-9)
for sg in segments:                            # a cut inside a voiced stretch clips a word: say so
    for edge, t in (("in", sg["in"]), ("out", sg["out"] - 0.02)):
        if db(t) > -35:
            rush = max((r for r in OFF if OFF[r] <= t), key=lambda r: OFF[r])
            print(f"  ! {sg['name']} {sg['sentence']} {edge} at {t - OFF[rush]:.2f} in {rush}: voice {db(t):.0f} dB")
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(segments, indent=1))
kept = []
for s in segments:                              # words in segment order (the cut's order, not the raw order)
    for w in words:
        if w["range"] is not None and w["text"] and s["in"] - 0.03 <= w["start"] < s["out"] and w not in kept:
            w["end"] = min(w["end"], s["out"])
            kept.append(w)
bare = lambda t: re.sub(r"[.,;:!?…]+$", "", t)
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{VERSION}: {len(segments)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in segments):.1f} s")
print(" ".join(w["text"] for w in kept))
