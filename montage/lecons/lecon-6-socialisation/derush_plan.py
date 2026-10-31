#!/usr/bin/env python3
"""Leçon 6 (IMG_5254), la socialisation: a talk to camera, cut like the other lessons.

Every stumble and retake goes: the set-up chatter before the lesson, the « Ok » that open a take, the sentences she
abandons (« pour... Non. », « la nouvelle... Non. », « qui frustra... Non, non. pas bien la phrase. », « dans un bain... »),
the asides (« Bref », « Non, alors attends. »), and the pauses longer than MAX_GAP, cut on the voice.
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
    (87.60, 99.90),    # « Si je devais te donner une seule chose… on commence ! » (« Ok, » and « Alors... » go)
    (105.10, 116.60),  # « Donc déjà, qu'est-ce que c'est que la socialisation ?… chaque sortie que tu feras. »
    (131.20, 154.78),  # « En fait… de joie ou neutre, »
    (157.85, 161.95),  # « ça deviendra quelque chose de banal ou… qu'il aime. » (the first « ça deviendra… » goes)
    (172.16, 177.70),  # « Ou si quelque chose le stresse un peu plus… en compte. » (« Et si… pour... Non. » goes)
    (182.30, 182.96),  # « Par exemple, »
    (184.05, 199.70),  # « un chiot qui aura très très mal vécu… un calvaire les trajets. » (« je te donne » goes)
    (207.20, 211.17),  # « Donc il y a une fenêtre d'or entre 6 à 12 semaines, » (« Ok, » and « c'est vraiment cette
                       # période incroyable, » go)
    (213.00, 218.57),  # « C'est vraiment cette période-là… tout ce que tu lui donnes. » (« T'as vraiment 7 de 6 à 12
                       # semaines… », a false start and the same idea again, goes)
    (238.00, 241.86),  # « Après 4 mois, cette facilité, elle commence à disparaître » (« Après ces semaines-là… la
                       # nouvelle... Non. » and « et il commence... » go)
    (248.99, 271.90),  # « Donc ce qu'il n'a pas vécu positivement… sans aucune appréhension. »
    (278.20, 283.90),  # « Donc ce qu'il faut vraiment bien se mettre en tête… un adulte très équilibré » (« et... » goes)
    (287.60, 297.30),  # « Et donc un chiot qui ne l'a pas été… tout se règle. »
    (301.00, 356.40),  # « Donc on va voir ce qu'il faut lui faire découvrir… les surfaces… les bruits… les sonneries, »
    (358.09, 363.46),  # « les sonnettes des vélos… les choses qui font du bruit. » (« les n'importe quoi » and « Il va
                       # vraiment essayer, il va vraiment... » go)
    (368.00, 404.25),  # « Ça va vraiment être important… quelque chose de tout à fait banal plus tard. »
    (406.87, 417.69),  # « Ensuite, évidemment, le plus important, les humains… Pourquoi ? »
    (423.49, 444.40),  # « Sinon plus tard vous aurez un chiot qui va frustrer… des interactions de qualité. » (« Parce que
                       # sinon… qui frustra... Non, non. pas bien la phrase. » goes)
    (451.20, 491.24),  # « Et je précise aussi… les chiens… des chiens calmes et équilibrés, d'accord ? »
    (495.60, 515.40),  # « Des chiens que vous allez connaître… plutôt que quantitatives. » (« Donc des chiens qui vont
                       # pouvoir tout simplement... Bref, » and « Non, alors attends. » go)
    (527.67, 550.20),  # « Donc évidemment, le parc canin… un petit peu trop tôt. » (the lone « ensuite » goes)
    (575.30, 600.00),  # « Une autre chose aussi que les chiens… tous ses différents animaux. »
    (614.53, 636.89),  # « Donc on va vraiment faire en sorte… le temps aussi d'observer, »
    (643.36, 665.20),  # « On ne force pas le chiot… sur 2-3 choses. » (« mais on ne force pas… dans un bain... » goes)
    (670.97, 700.10),  # « Mais c'est tout à fait normal… a réussi à passer au-dessus. »
    (707.40, 740.91),  # « Donc, les règles d'or… Les signaux d'apaisement, c'est très important. »
    (742.11, 779.45),  # « S'il baille… et donc d'arrêter l'interaction. » (the second « C'est très important » goes)
    (787.30, 790.45),  # « Donc pour finir, ce que tu fais ou ne fais pas »
    (792.30, 797.90),  # « durant ces prochaines semaines va vraiment déterminer… plus tard. » (said twice: the first goes)
    (806.82, 840.60),  # « Donc dès aujourd'hui… les bonnes expériences qu'il va avoir. »
    (846.46, 849.12),  # « On se retrouve dans la prochaine leçon. À tout de suite. »
]
SOLID = [(207.20, 211.10),  # played whole: the « s » of « six » is under the voice gate and would be cut
         (614.35, 615.00),  # « Donc on va… »: the « D » starts before the word the transcript places
         (650.85, 651.30)]  # « trouble »: its quiet « -ble » is under the voice gate
CAP = [417.64]              # « Pourquoi ? » ends here: the « P » of the dropped « Parce que » follows at once
FULLW = [(206.50, 213.05)]   # the passage transcript runs « semaines » into « C'est » here: the whole-rush one is right
WORDS = {87.64: "Si", 207.25: "Donc", 172.21: "Ou", 280.34: "chiot", 287.64: "Et", 296.94: "se",
         391.64: "aussi", 391.84: "", 423.50: "Sinon", 495.68: "Des", 501.78: "demander", 504.61: "OK", 504.69: "",
         670.97: "Mais", 727.89: "observer.", 742.12: "S'il", 848.57: "À", 189.0: "eh",
         330.27: "le", 335.81: "c'est"}

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
