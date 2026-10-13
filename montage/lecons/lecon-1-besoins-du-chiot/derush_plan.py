#!/usr/bin/env python3
"""Leçon 1 (IMG_4913): the takes kept after reading every line, cut on the voice.

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
    (1, 15.40, 19.70),    # second « Bienvenue… »: the first one stops on « Non »
    (2, ALL), (3, ALL),
    (5, 77.20, 84.40),    # from « premier point le sommeil »: « Ok super, par rapport au sommeil, ok donc » goes
    (5, 89.25, 91.45),    # the second « Oui c'est énorme »
    (5, 105.15, 110.60),
    (6, ALL), (7, ALL),
    (9, ALL),             # règle numéro 1, her second version (8 dropped)
    (10, ALL), (11, ALL), (12, ALL),
    (13, 185.80, 191.40), # « exactement comme un enfant fatigué » is already in 12
    (15, ALL), (16, ALL), # 14 « plus âgé » is the slip she corrects in 15
    (18, 226.80, 228.20), (19, ALL),
    (20, ALL), (21, ALL), (23, ALL), (24, ALL), (25, ALL), (27, ALL),
    (26, 310.00, 314.20),  # 26: she restarts « Ça veut dire… », the second version is the whole one
    (28, ALL), (29, 340.60, 343.00),
    (30, ALL),
    (33, 374.00, 378.30), (34, ALL),   # 31 is abandoned
    (35, 395.65, 404.10),
    (36, 415.40, 419.75),
    (38, 439.60, 444.75),
    (39, 465.50, 468.90),              # the clean « Et surtout parce qu'il n'a pas besoin… »
    (40, ALL), (41, ALL), (43, ALL),   # 37 and 42 are abandoned
    (45, ALL), (46, ALL), (47, ALL), (48, ALL),   # 45 is the complete version of 44
    (51, 573.40, 573.95),              # « quatrième point »
    (52, 579.75, 587.60),
    (53, ALL), (54, 595.40, 596.95), (55, ALL), (56, ALL),
    (58, ALL), (60, ALL), (61, ALL),   # 58 is the retake of 57
    (62, ALL), (64, 678.30, 681.90),
    (66, ALL), (67, ALL),              # 66 is the complete version of 65
    (68, 718.15, 720.80), (69, ALL),
    (70, ALL), (71, ALL), (72, ALL),
    (73, 763.20, 767.90),  # 73: « potentiellement développe… » restarted
    (75, ALL),
    (74, 778.15, 783.40),  # 74: « Donc voici les cinq piliers hyper importants de… » restarted
    (76, ALL), (77, ALL),
]
INSERT = {  # words the per-take transcription missed, heard again on the passage alone
    3: [{"text": "On", "start": 51.84, "end": 51.98}],
    75: [{"text": "l'hygiène", "start": 785.80, "end": 786.60}],
}
# words re-heard on the passage alone, where the per-take alignment was off (found by re-transcribing the cut)
def _w(spec, last_end):
    ws = [{"text": t, "start": float(a)} for t, a in (x.rsplit("@", 1) for x in spec.split())]
    for a, b in zip(ws, ws[1:]):
        a["end"] = round(b["start"] - 0.02, 2)
    ws[-1]["end"] = last_end
    return ws
WORDS = {  # take → its words (58: only from 637 s on)
    26: _w("Ça@310.15 veut@310.27 dire@310.39 que@310.54 tu@310.66 peux@310.80 anticiper@311.22 quand@312.42 est-ce@312.68 "
           "qu'il@312.88 aura@313.06 envie@313.30 de@313.52 faire@313.60 ses@313.80 besoins@313.96", 314.10),
    58: _w("parce@637.23 qu'ils@637.43 ne@639.18 peuvent@639.30 juste@639.58 pas@640.02 se@640.20 retenir@640.34 "
           "plus@640.92 longtemps@641.08", 641.30),
    74: _w("Donc@778.23 voici@778.39 les@778.71 5@778.93 piliers@779.15 hyper@779.55 importants@779.89 de@780.39 ton@780.53 "
           "chiot@780.74 Le@781.36 sommeil@781.50 les@782.10 repas@782.26 le@782.98 jeu@783.16", 783.50),
    73: _w("peut@763.34 potentiellement@763.54 développer@764.26 des@764.88 peurs@765.04 ou@765.40 de@765.52 la@765.62 "
           "réactivité@765.72 face@766.70 à@767.12 certains@767.26 stimuli@767.56", 767.84),
}
FIX = {"l'accord": "la corde"}  # « en train de tirer à la corde »
CAPITAL = (77.22, 395.68, 573.43)  # sentences whose start was cut: « Premier point », « Maintenant », « Quatrième point »

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
        since = WORDS[ti][0]["start"] - 0.05 if ti == 58 else -1
        own = [w for w in own if w["start"] < since] + [dict(w) for w in WORDS[ti]]
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
