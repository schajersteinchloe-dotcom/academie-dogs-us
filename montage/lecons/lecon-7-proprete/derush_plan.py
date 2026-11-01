#!/usr/bin/env python3
"""Leçon 7 (IMG_5255), la propreté: a talk to camera, cut like the other lessons.

Every stumble and retake goes: the two false starts of the opening (« Ok, bon, la propreté… Non, je suis pas au milieu
là. »), the passage she asks to cut (« C'est pour... Non, c'est nul ça, enlève ça. »), the sentences she abandons and
says again (« si tu fais tout. », « Alors première erreur qu'il ne faut pas... », « Et si votre chiot... », « Donc, pour
nettoyer… Non, attends. Non, ça c'est après. On enlève… Non, c'était ça. Ok. », « un chiffon qui... »), the asides
(« Et oui... », « Ah, mais c'est pas possible ! ») and the pauses longer than MAX_GAP, cut on the voice.
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
    (32.08, 45.75),    # « La propreté, c'est souvent ce qui stresse le plus… trois semaines maximum » (the two first takes,
                       # « Ok, bon, » and the first « si tu fais tout. » go)
    (48.80, 51.40),    # « si tu fais tout ce que je vais te lister en dessous. »
    (60.24, 69.60),    # « La première chose à savoir… se retenir, d'accord ? » (« Ok, » goes)
    (83.34, 97.90),    # « Donc, son sphincter n'est pas mature… très compliqué pour lui. » (« Ses sphinctères… C'est
                       # pour... Non, c'est nul ça, enlève ça. Donc, ses sphinctères ne sont pas bien, hein ? » goes)
    (102.20, 116.40),  # « Donc ça arrive que par exemple tu le sortes… quelques minutes avant. »
    (130.70, 154.55),  # « Alors, première erreur à éviter… le principe contraire d'une alèse. » (the first try and
                       # « Et oui... » go)
    (163.78, 192.72),  # « J'ai utilisé des alèses… ramasser des cacas en intérieur. »
    (199.95, 220.86),  # « Maintenant, on va parler du timing des sorties… après chaque sieste, »
    (223.42, 225.46),  # « après chaque session de jeu. » (« après session de jeu, » goes)
    (228.00, 231.20),  # « Et en gros, toutes les 2-3 heures dans la journée. »
    (234.94, 256.90),  # « Et alors, vous allez me demander, et la nuit… c'est vraiment pour le mieux. »
    (260.60, 313.00),  # « Quand il fait dehors… le timing doit être très précis. »
    (327.80, 343.40),  # « Et n'hésitez pas à rester dehors… de plus en plus, de plus en plus. » (« Et si votre chiot... »
                       # goes)
    (346.08, 366.95),  # « Et dans le cas où vous êtes avec un chiot qui prend très longtemps… quand on sort. »
    (376.25, 451.70),  # « Alors, tu as peut-être aussi déjà vécu ça… quelque chose qui n'est même pas volontaire. »
    (471.78, 512.35),  # « Alors maintenant, si vous le prenez sur le fait… c'est interdit à la maison. » (« Donc, pour
                       # nettoyer… Non, attends… Non, c'était ça. Ok. » goes)
    (516.96, 518.10),  # « Donc c'est doucement, »
    (519.80, 531.99),  # « on fait hop hop hop… ça n'existe pas ça, d'accord ? » (« c'est on voit le chauffeur, », the
                       # same three times in three transcriptions and no sense in a caption, goes)
    (538.95, 561.40),  # « Et évidemment, le mieux c'est d'anticiper… pour pouvoir anticiper au mieux. »
    (569.09, 597.60),  # « Et maintenant sur le principe que tu arrives trop tard… ce que tu vas vouloir dire. » (« Ok, »
                       # and « Donc... » go)
    (598.76, 618.20),  # « On prend le chiot… pour du jeu. »
    (622.83, 626.40),  # « Un chiffon, en fait, qui essuie le sol… un peu drôle. » (« En fait, tout simplement, un chiffon
                       # qui... » goes)
    (627.20, 629.90),  # « Ça peut faire des associations… après. » (« Et donc... » goes)
    (635.58, 643.45),  # « Et donc ensuite, ce que tu feras… ce petit accident. »
    (656.70, 681.40),  # « Donc vraiment, la propreté… des stades qui ne sont pas très drôles. » (« Ah, mais c'est pas
                       # possible ! » goes)
    (685.84, 710.15),  # « Donc le petit exercice… vous vous adaptez évidemment. »
    (716.14, 722.90),  # « Eh bien maintenant c'est super… on se retrouve dans la prochaine leçon. » (« Ok, » goes)
]
SOLID = []
CAP = []
CUTS = [(518.12, 519.80)]   # removed whatever the voice gate says: « c'est on voit le chauffeur, » runs into its neighbours
FULLW = [(130.50, 132.30),   # the passage transcript loses « Alors, » and places « Première » 0.3 s late
         (622.50, 623.45)]   # and loses « Un » of « Un chiffon »
WORDS = {32.10: "La", 60.27: "La", 327.89: "Et", 376.37: "Alors,", 569.10: "Et", 716.16: "Eh", 83.43: "Donc,",
         290.10: "plus", 478.62: "dites", 627.26: "Ça"}
TEXT = [("alaise", "alèse"), ("réveillir", "réveiller")]   # spelling, wherever it occurs

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
