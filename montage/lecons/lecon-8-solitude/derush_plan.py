#!/usr/bin/env python3
"""Leçon 8 (IMG_5256), la solitude: a talk to camera, cut like the other lessons.

Every stumble and retake goes: the chatter and the false start before the lesson (« Allez, on enchaîne… Dans cette
leçon, Non, pas du tout, je ne vais pas commencer comme ça. »), the sentences she abandons and says again (« Donc... »,
« Donc ça, c'est ce que j'ai dit. Ok, », « tu passes la porte de... Non, non. », « Donc des jouets d'occupation
surtout. », « Alors je ne dis pas ça… non. », « Et donc du coup c'est souvent... Non, pardon. », « que t'es », the first
« pour conclure… de cette énergie-là, non. », the first exercise « …Attends, je le refais. »), the outro joke
(« Wouh ! Module 1 !… ») and the pauses longer than MAX_GAP, cut on the voice.
  KEEP  rush ranges whose words are kept (word starts in [a, b])

Writes assets/derush/raw.segments.json and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -45.0

KEEP = [
    (32.39, 62.10),    # « On se retrouve dans cette nouvelle leçon pour parler de la solitude… ça va poser problème. »
    (73.60, 86.30),    # « Donc évidemment, il y a des choses étape par étape… vous ne voulez absolument pas ça. »
    (94.20, 109.25),   # « La capacité à rester seul… quelque chose qu'on veut éviter. »
    (117.24, 119.45),  # « Donc on va préparer le terrain. »
    (124.13, 144.55),  # « Avant de le laisser seul… tu as comblé tous ses besoins. »
    (149.60, 186.30),  # « Ensuite, on le laisse évidemment dans un endroit calme… incompréhensible pour lui. »
    (195.37, 201.20),  # « Alors maintenant, on va faire le protocole en deux semaines… la solitude ? »
    (204.25, 221.50),  # « Donc les premiers jours, jour 1 à 3… et que tout se passe bien. »
    (226.72, 286.42),  # « Donc en gros, t'as envie d'aller aux toilettes… jour 4 à 7… à chaque fois que tu vas faire ça. »
    (291.80, 300.70),  # « Donc on parle surtout de jouets d'occupation… pour s'occuper. »
    (306.70, 386.55),  # « Et ensuite, évidemment, du jour par exemple 8 à 14… qu'est-ce qui se passe à la maison. »
    (394.09, 399.18),  # « Donc il y a un point crucial aussi, c'est les départs et les retours neutres. »
    (402.50, 442.75),  # « Je ne dis pas que quand tu ne vois pas ton chien pendant 8 heures… pas dès le retour, par exemple. »
    (451.89, 473.45),  # « Donc vraiment en rendant les départs et les retours neutres… ça va générer une émotion. »
    (476.80, 491.15),  # « Et donc du coup ça peut arriver… ils vont faire des bêtises. »
    (501.20, 528.20),  # « Ensuite, on va avoir le cas où le chiot pleure… Si vous avez un chiot »
    (529.20, 541.45),  # « qui hurle à la mort… les minutes où on le laisse seul. » (« qui... et » goes)
    (548.25, 555.30),  # « Donc voilà, si les pleurs sont intenses… ce n'est pas grave. »
    (559.95, 605.55),  # « Ensuite, les mois vont avancer… malgré le fait »
    (606.65, 629.80),  # « que tu as travaillé sur toute cette solitude… dans votre quotidien. »
    (641.40, 681.20),  # « Mais donc pour conclure, deux semaines, ça suffit… manger, pipi, etc. »
    (700.14, 708.30),  # « Petit exercice. Donc, tu passes dans une autre pièce… de manière tout à fait banale. »
    (716.75, 724.58),  # « Dans les prochaines leçons… je vous laisse passer à la suite. »
]
SOLID = []
CAP = []
CUTS = []
FULLW = []
WORDS = {195.42: "Alors", 402.58: "Je", 501.25: "Ensuite,", 700.15: "Petit", 95.97: "seul,", 454.09: "retours neutres,",
         582.02: "chiot", 128.29: "comblés.", 336.58: "l'aura", 336.76: ""}
TEXT = []

# words: the passage-by-passage transcript, the whole-rush one outside it and inside FULLW
inside = lambda t, rs: any(a <= t <= b for a, b in rs)
inner = [(r["in"] + 0.5, r["out"] - 0.5) for r in json.loads((ROOT / "src" / "regions.json").read_text())]
words = [w for w in json.loads((ROOT / "src" / "transcript-regions.json").read_text())["words"]
         if inside(w["start"], inner) and not inside(w["start"], FULLW)]
full = json.loads((ROOT / "src" / "transcript-full.json").read_text())["words"]
words = sorted(words + [w for w in full if not inside(w["start"], inner) or inside(w["start"], FULLW)],
               key=lambda w: w["start"])
merged = []
for w in words:
    text = w["text"].replace("«", "").replace("»", "").strip()
    if not text:
        continue
    if merged and not re.search(r"\w", text):    # punctuation tokens join their word
        merged[-1]["text"] += text
    else:
        merged.append(dict(w, text=text))
words = merged
for w in words:
    w["text"] = WORDS.get(round(w["start"], 2), w["text"])
    for x, y in TEXT:
        w["text"] = w["text"].replace(x, y)
    w["keep"] = inside(w["start"], KEEP)
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
for c in CAP:
    segs = [[a, min(b, c) if a < c < b else b] for a, b in segs]
for ca, cb in CUTS:
    segs = [p for a, b in segs for p in ([[a, ca], [cb, b]] if a < ca and cb < b else
                                          [[a, min(b, ca)]] if a < ca < b else [[max(a, cb), b]] if a < cb < b else [[a, b]])]
union = []
for a, b in segs:
    if union and a <= union[-1][1] + 0.02:
        union[-1][1] = max(union[-1][1], b)
    else:
        union.append([a, b])

out = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3)} for k, (a, b) in enumerate(union)]
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(out, indent=1))
kept = [w for w in words if w["keep"] and w["text"] and any(s["in"] - 0.03 <= w["start"] < s["out"] for s in out)]
bare = lambda t: re.sub(r"[.,;:!?…]+$", "", t)  # captions without punctuation, like the other lessons
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{len(out)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in out):.1f} s")
print(" ".join(w["text"] for w in kept))
