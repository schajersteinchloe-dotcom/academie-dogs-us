#!/usr/bin/env python3
"""Story time · Nala et l'os (IMG_5376) — three versions of one story, each opening on a different hook.

One rush: the story told while filling Nala's snuffle mat, then two more hooks recorded at the end. Each version is a
hook + the same body. In each block KEEP ranges keep their words and cut the pauses on the voice; the slips (« Non,
putain », « Elle me dit… n'importe quoi, je te raconte n'importe quoi », « On va tester d'autres hooks », the repeated
« l'écart entre nous », « pour pouvoir lui sauter dessus » said twice) are never inside a range. The aside « pendant qu'elle
essayait de m'échapper… elle le chiquait » told after the story is moved to where it belongs, before the ending.

Usage: python3 derush_plan.py v1|v2|v3 PROJECT_DIR [SRC_DIR]  → PROJECT_DIR/assets/derush/raw.segments.json + raw.captions.json
"""
import json, re, sys, wave
from pathlib import Path

import numpy as np

VERSION, PROJ = sys.argv[1], Path(sys.argv[2])
SRC = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/root/videos/nala-src")
D = PROJ / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.45, 0.10, 0.15, -45.0

# sentences: (a, b) in the rush's seconds
S = {
    "H1": [(13.00, 22.62),     # « Il faut que je vous raconte la fois où Nala m'a fait attendre 45 minutes… un os, un trésor, que dis-je, »
           (25.36, 27.84)],    # « Oui, c'est de toi qu'on parle. » (to Nala)
    "H2": [(248.95, 255.60)],  # « Story time du jour où Nala a mangé un os… galérer pendant 45 minutes. »
    "H3": [(271.70, 279.12),   # « Est-ce que tu leur racontes le jour où tu m'as fait galérer… hanche de grand-mère ? » (to Nala)
           (281.40, 281.80)],  # « Dis-nous. »
    "B1": [(30.56, 35.20)],    # « Bon, je commence l'histoire… dans son tapis de fouille. »
    "B2": [(35.55, 50.78)],    # « En gros, qu'est-ce qui s'était passé ? … à prendre un chemin. »
    "B3": [(50.78, 56.78),     # « Et Nala, je la vois aller dans des hautes herbes… dans ces hautes herbes. »
           (63.27, 64.62)],    # « Et qu'est-ce qui se passe tout d'un coup ? » (second take)
    "B4": [(65.05, 78.24)],    # « Je la vois revenir avec un os de cette taille-là… en train de mâchouiller son os. »
    "B5": [(78.24, 86.50),     # « Et là, je me dis, c'est top… quand Nala, elle a trouvé un trésor, »
           (88.50, 91.19)],    # « bon, c'est le sien, on ne peut plus rien faire. »
    "B6": [(91.19, 102.35)],   # « Surtout que Nala a déjà un très bon rappel… moins tolérante sur le sujet. »
    "B7": [(102.35, 113.65),   # « Donc, on commence à faire des tours… plus elle met de l'écart entre nous. »
           (115.78, 119.21)],  # « C'est-à-dire qu'elle met 10 mètres, 20 mètres, 30 mètres. »
    "B7b": [(207.02, 214.40)], # « Parce que pendant qu'elle essayait de m'échapper… elle repartait à 10 mètres. »
    "B8": [(123.30, 133.81)],  # « Mais du coup je me dis… qu'elle n'était pas concentrée sur mon amie. »
    "B9": [(133.81, 145.92)],  # « Donc ce qu'on s'est dit… Du coup elle était hyper concentrée sur moi. »
    "B10": [(145.92, 156.00)], # « Ce qui faisait qu'elle avait totalement oublié mon amie… la choper rapidement. »
    "B11": [(158.25, 167.90)], # « Et donc je continue de lui parler… les oreilles en avant vers moi en m'écoutant. »
    "B12": [(167.90, 173.15),  # « Jusqu'à ce que mon amie du coup arrive à s'approcher assez suffisamment »
            (176.95, 179.30)], # « lui sauter dessus. La choper au harnais. »
    "B13": [(179.30, 182.55),  # « Reprendre l'os qu'elle avait en main qui était énorme. »
            (183.40, 184.86),  # « enfin qu'elle avait en bouche pardon »
            (185.82, 189.60)], # « et qu'on puisse enfin tout simplement continuer notre balade. »
    "B14": [(190.30, 200.40)], # « Donc voilà, et tout ça, ça avait duré 45 minutes… pas de timing à respecter. »
    "B15": [(224.03, 228.05),  # « Après, pendant deux jours, elle a fait caca blanc. »
            (228.85, 230.95),  # « Son caca était un os. »
            (232.31, 233.88)], # « Mais il lui est rien arrivé du tout. »
    "B16": [(242.78, 244.60)], # « Voilà pour la petite story time. »
}
BODY = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B7b", "B8", "B9", "B10", "B11", "B12", "B13", "B14", "B15", "B16"]
VERSIONS = {"v1": ["H1"] + BODY, "v2": ["H2"] + BODY, "v3": ["H3"] + BODY}
# start (rounded) → corrected text; "" keeps the sound, no caption
WORDS = {92.04: "a", 92.17: "déjà", 107.56: "appétentes.", 76.98: "mâchouiller", 168.55: "amie", 211.66: "chiquait,",
         141.35: "Nounou", 281.47: "Dis-nous.", 281.61: "", 22.68: "dis-je,", 183.17: "", 183.43: "Enfin,", 185.84: "Et",
         176.40: "", 224.14: "Après,", 63.29: "Et", 102.37: "Donc,", 65.39: "Je", 95.49: "bon,", 189.20: "balade.",
         190.38: "Donc", 199.86: "respecter.", 21.48: "dis-je !", 172.63: "suffisamment,", 177.02: "lui", 177.54: "dessus,",
         177.96: "la", 184.51: "pardon."}
# start → (start, end): the transcript's timing is off (stretched over a pause, or heard late)
TIMES = {111.24: (111.26, 111.56), 112.44: (111.62, 111.90), 114.42: (112.18, 112.38), 114.98: (112.42, 112.64),
         115.08: (112.68, 113.18), 115.40: (113.20, 113.42), 115.62: (113.46, 113.60)}   # « plus elle met de l'écart entre
# nous » said at 111.3-113.6 and repeated at 114-115.8 (the region pass hears both, the full pass only the second)
# (a, b) removed whatever the voice gate says
CUTS = []

words = []
for w in json.loads((SRC / "IMG_5376.json").read_text())["words"]:
    text = w["text"].strip()
    if not text:
        continue
    if words and not re.search(r"\w", text):
        words[-1]["text"] += text; words[-1]["end"] = max(words[-1]["end"], w["end"])
    else:
        words.append(dict(w, text=text, local=w["start"]))
ranges = []
for name in VERSIONS[VERSION]:
    for a, b in S[name]:
        ranges.append((len(ranges), name, a, b))
for w in words:
    key = round(w["local"], 2)
    w["text"] = WORDS.get(key, w["text"])
    if key in TIMES:
        w["start"], w["end"] = TIMES[key]
    w["range"] = next((i for i, _, a, b in ranges if a <= w["start"] <= b), None)
for w, nxt in zip(words, words[1:]):
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))

wv = wave.open(str(SRC / "IMG_5376.wav"))
pcm = np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768
n = len(pcm) // 160
voiced = 20 * np.log10(np.sqrt((pcm[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9) > VOICE_DB


def runs(s, e):
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
    for s in segs:
        lo = max([w["end"] for w in others if w["end"] <= s[0] + 0.01], default=0.0)
        hi = min([w["start"] for w in others if w["start"] >= s[1] - 0.01], default=1e9)
        s[0] = max(s[0] - PRE, min(lo + 0.02, s[0] - 0.02), ka - 0.05)
        s[1] = min(s[1] + POST, max(hi - 0.02, s[1] + 0.02), kb + 0.25)
    if segs:   # range starts are set on the voice onsets: trust them
        segs[0][0] = min(segs[0][0], ka)
    mine = [w for w in words if w["range"] == ri]
    for a, b in segs:
        if b - a >= 0.08 and (b - a >= 0.25 or any(a - 0.03 <= w["start"] < b for w in mine)):
            out.append([a, b, ri, name])
for ca, cb in CUTS:
    out = [p for a, b, ri, nm in out for p in ([[a, ca, ri, nm], [cb, b, ri, nm]] if a < ca and cb < b else
                                               [[a, min(b, ca), ri, nm]] if a < ca < b else [[max(a, cb), b, ri, nm]] if a < cb < b else [[a, b, ri, nm]])]

segments = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3), "sentence": nm} for k, (a, b, _, nm) in enumerate(out)]
db = lambda t: 20 * np.log10(np.sqrt((pcm[int(t * 16000):int(t * 16000) + 320] ** 2).mean()) + 1e-9)
for sg in segments:
    for edge, t in (("in", sg["in"]), ("out", sg["out"] - 0.02)):
        if db(t) > -35:
            print(f"  ! {sg['name']} {sg['sentence']} {edge} at {t:.2f}: voice {db(t):.0f} dB")
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(segments, indent=1))
kept = []
for s in segments:
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
