#!/usr/bin/env python3
"""Leçon (IMG_4991), les balades: the takes kept after reading every line, cut on the voice.

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
    (3, 57.70, 79.30),    # up to « 3 types différents » (« Est-ce que » abandoned)
    (4, ALL),
    (7, 126.65, 136.60),  # from « pourquoi » (« Ok bon déjà » goes)
    (9, 143.00, 148.00),  # up to « suffisant »; 10 « j'arrête de faire ça » goes, 11 says the end again
    (11, ALL),
    (12, 172.10, 181.25), (13, ALL),
    (14, ALL),
    (15, 239.60, 242.60), (16, ALL), (17, ALL),   # « …les trois types de balades différentes que vous allez devoir repérer… et pour quelles raisons »
    (18, 259.45, 267.40), # from the second « La première balade »
    (19, ALL),
    (20, 285.60, 289.55), # up to « pâté de maison »
    (21, 291.00, 297.85), # « c'est que le chien comprenne… safe et intéressant pour lui »
    (21, 302.10, 303.60), # her corrected « Des petits coins d'herbe, des buissons » (the first try ends on « Non »)
    (22, ALL),
    (27, ALL),            # 23-26 « On le refait, on coupe ça »: 27 is the clean version
    (28, 380.40, 383.00), (29, ALL),
    (30, ALL),
    (31, 431.30, 432.75), (32, ALL), (33, ALL),   # « L'objectif de la balade socialisation, c'est de l'exposer… »
    (34, ALL),
    (35, 467.70, 477.75), (36, ALL),              # « …attention à ça, puisque laisser son chiot… »
    (37, 497.05, 499.00), # « C'est mieux la qualité que la quantité » (not « la quantité… n'importe quoi »)
    (38, 504.90, 531.65), (39, 532.35, 533.60),   # « …que tout va bien et que les humains ne vont pas le manger »
    (40, ALL),
    (41, ALL),
    (42, 569.10, 573.95), (43, ALL),              # « …En général, les chiots peuvent suivre… »
    (44, 590.20, 603.00), # the second « Et ce qu'il faut savoir »
    (45, ALL),            # 46-50: « aïe aïe », the Gilles de la Tourette aside, « On cut ça », « OK »
    (51, ALL),
    (52, 666.50, 676.05), (52, 679.00, 690.85),   # « Si c'est pas tous les jours, c'est ok » once
    (53, 695.40, 700.60),
    (54, ALL), (56, ALL), (57, ALL), (58, ALL), (59, ALL),
    (62, 883.10, 895.30), (63, ALL),              # « …diversifier le plus possible pour que votre chiot… »
    (64, ALL),            # 61 « Je finis », 65 « Mais t'es long » go
]
INSERT = {  # said low, missed by the per-take transcription, heard again on the passage alone
    41: [{"text": "On", "start": 559.60, "end": 559.72}, {"text": "prend", "start": 559.74, "end": 560.00}, {"text": "une", "start": 560.02, "end": 560.16}],
    42: [{"text": "On", "start": 569.17, "end": 569.28}],
    64: [{"text": "On", "start": 900.53, "end": 900.63}, {"text": "se", "start": 900.65, "end": 900.75}],
}
_own = {i: t.get("words", []) for i, t in enumerate(takes, 1)}
WORDS = {  # 38 and 39 overlap in time: 38's abandoned « que les yeux » would interleave with 39, and 39's
           # « manger » is stretched over a laugh and « Je ne sais pas si je laisse ça »
    38: [w for w in _own[38] if w["start"] <= 531.65],
    39: [dict(w, end=533.95) if w["text"] == "manger" else w for w in _own[39] if w["start"] <= 533.6],
    43: [dict(w, end=579.62) if w["text"] == "mois" else w for w in _own[43]],   # « mois » is said at 579.35-579.6
}
FIX = {"jokers": "joggers", "course": "courte"}
CAPITAL = (126.71, 679.04)          # « Pourquoi », « Si c'est pas tous les jours »
LOWER = (296.90, 575.17)            # « safe et intéressant », « En général, les chiots »
LOWER_FIRST_OF = (17,)              # « et pour quelles raisons »

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
        if round(w["start"], 2) in LOWER or (ti in LOWER_FIRST_OF and w is ws[0]):
            w["text"] = w["text"][:1].lower() + w["text"][1:]
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
