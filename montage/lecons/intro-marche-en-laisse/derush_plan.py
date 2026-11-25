#!/usr/bin/env python3
"""Formation Marche en laisse · Vidéo d'introduction — derush of the face cam (videointro.mov, 8 min 48).

The face cam follows the Notion script « Vidéo d'introduction — Transforme tes balades » with retakes:
« À chaque balade… Non, c'est nul », « Et tu es gênée… Non », « Mais du coup… Non… Chut Thierry », « c'était
facilement… », « tout va… Non », two false starts of « Dans ces vidéos », « Arnaud… Arlo ? ». None is inside a range.
The long pauses she left for the practice clips are cut too: the clips are laid over her voice (lesson.json broll).

Usage: python3 derush_plan.py PROJECT_DIR [SRC_DIR]  → PROJECT_DIR/assets/derush/raw.segments.json + raw.captions.json
(the raw timeline is the face cam itself: raw.mp4 = videointro.mov reframed to 1920×1080, same times)
"""
import json, re, sys, wave
from pathlib import Path

import numpy as np

PROJ = Path(sys.argv[1])
SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/root/videos/intro-src")
D = PROJ / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.45, 0.10, 0.15, -45.0

# (a, b) in the face cam's seconds, in reading order; a third item "s" plays the range whole
RANGES = [
    (28.82, 35.25),    # Bienvenue dans la formation Marche en laisse… Est-ce que tes balades ressemblent à ça ?
    (61.20, 68.43),    # Ton chien tire absolument pour tout… tu as mal à l'épaule
    (83.25, 93.85),    # La gêne que tu ressens aussi en croisant quelqu'un… que l'inverse.
    (98.30, 110.60),   # Et bien évidemment, ce ressenti… des solutions qui ne sont peut-être pas adaptées.
    (114.80, 132.95),  # Et pourtant, tu as déjà tout essayé… à la moindre stimulation, il repart.
    (143.75, 150.65),  # Tu as essayé des solutions pendant un ou deux jours… abandonné.
    (155.20, 170.20),  # Tu as testé potentiellement un harnais antitraction… dérangeant quand même pour ton chien.
    (182.10, 191.30),  # On t'a peut-être même conseillé des méthodes dures… quelle est la solution.
    (199.15, 203.28),  # Si rien n'a marché, c'est ni de ta faute, ni celle de ton chien.
    (229.15, 235.45),  # C'est juste simplement que personne ne t'a donné la bonne méthode et dans le bon ordre.
    (239.65, 246.10),  # Donc, laisse-moi te présenter Arlo… le chien qui m'a permis de faire cette formation.
    (252.40, 266.00),  # Et donc les maîtres d'Arlo m'avaient appelée… une pile électrique.
    (268.15, 282.60),  # Donc Arlo il est ultra dynamique… force de proposition.
    (291.10, 295.75),  # Donc comme c'est un chien qui part au quart de tour, qui a un peu du mal à gérer ses émotions,
    (298.20, 311.15),  # On pouvait facilement le qualifier d'irrécupérable… dans un bon ordre,
    (313.78, 315.55),  # eh bien, tout peut se régler.
    (321.45, 326.20),  # Bon, je vous peins un petit peu le tableau, mais voilà où on était à la première séance.
    (334.70, 339.20),  # Et du coup voilà où on en est avec Arlo aujourd'hui à la fin de ces séances.
    (348.15, 352.20),  # C'est exactement le même chien. Les mêmes rues. La même tentation.
    (358.98, 364.05),  # La seule différence, c'est un protocole précis, qui a été appliqué étape par étape.
    (368.95, 371.70),  # Et c'est exactement ce protocole que je te donne ici.
    (381.18, 397.85),  # Dans cette formation, tu vas avoir 3 modules, étape par étape. Le premier… avant la sortie.
    (400.40, 414.55),  # Ensuite tu vas avoir le module 2… la concentration de ton chien.
    (418.10, 434.10),  # Et bien sûr, dans le module 3… avec tout ce qui a été fait en amont.
    (454.80, 465.05),  # Dans ces vidéos, tu vas évidemment retrouver mes explications… avec Arlo et ses maîtres.
    (488.20, 503.70),  # Donc maintenant, imagine, dans quelques semaines… vous allez apprécier enfin vos balades.
    (513.15, 523.75),  # Et bien tout ça c'est possible, Arlo en est la preuve… débloquer ta situation.
]
CUTS = [(383.44, 383.66), (68.48, 68.75), (232.47, 233.98)]   # « Ok » between « 3 modules » and « étape par étape », the « et » after « l'épaule »,
# « la bonne méthode » said twice (the transcript hears it once)
# (time, heard, written): the transcript's word near `time`; "" keeps the sound, no caption
FIX = [(131.18, "moins", "moindre"), (131.38, "de", ""), (160.68, "alti", "Halti"), (299.46, "de", ""),
       (299.68, "irrécupérable", "d'irrécupérable"),
       (361.56, "Qui", "qui"), (383.34, "Ok", ""), (325.65, "séance", "séance."), (339.16, "séances", "séances."),
       (349.69, "chien", "chien."), (350.65, "rues", "rues."), (351.57, "tentation", "tentation."),
       (360.34, "protocole", "protocole"), (363.54, "étape", "étape."), (371.03, "ici", "ici."), (382.92, "modules", "modules,"),
       (384.26, "étape", "étape."), (323.57, "Mais", "mais"), (338.06, "à", "à"), (337.10, "Aujourd'hui", "aujourd'hui"),
       (513.92, "possible,", "possible,"), (256.50, "appelé", "appelée")]
# (time, start, end): words the transcript put in the wrong place (a sentence's first word stuck to the previous one)
TIMES = [(326.15, 334.74, 334.86), (352.13, 359.02, 359.12), (364.04, 368.97, 369.03), (371.67, 381.22, 381.40),
         (512.78, 513.20, 513.28), (339.16, 348.18, 348.24),
         (127.32, 127.42, 127.70), (163.70, 163.94, 164.08), (278.94, 279.18, 279.30), (297.64, 298.24, 298.33), (406.54, 406.86, 406.96), (263.68, 263.68, 265.95)]

norm = lambda t: re.sub(r"[^\w']", "", t.replace("’", "'").lower())
raw = json.loads((SRC / "videointro.json").read_text())["words"]
for t, a, b in TIMES:   # before the merge: a lone « C » goes back to its « 'est »
    w = min(raw, key=lambda w: abs(w["start"] - t))
    if abs(w["start"] - t) < 0.05:
        w["start"], w["end"] = a, b
raw.sort(key=lambda w: w["start"])
words = []
for w in raw:   # « j » + « 'ai », « Est » + « -ce », « C » + « 'est »: one word
    w = dict(w, text=w["text"].strip())
    if words and (w["text"][:1] in "'’-" or (words[-1]["text"].lower() in ("j", "c", "l", "n", "qu", "t", "d", "m", "s", "aujourd")
                                             and w["text"][:1] in "'’")):
        words[-1]["text"] += w["text"]; words[-1]["end"] = w["end"]
    else:
        words.append(w)
for t, heard, written in FIX:
    cand = [w for w in words if abs(w["start"] - t) < 0.6 and norm(w["text"]) == norm(heard)]
    if not cand:
        raise SystemExit(f"FIX: « {heard} » not found near {t}")
    min(cand, key=lambda w: abs(w["start"] - t))["text"] = written

ranges = [(i, a, b) for i, (a, b, *k) in enumerate(RANGES)]
for w in words:
    w["range"] = next((i for i, a, b in ranges if a <= w["start"] <= b), None)
for w, nxt in zip(words, words[1:]):
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))

wv = wave.open(str(SRC / "videointro.wav"))
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
for ri, ka, kb in ranges:
    if len(RANGES[ri]) > 2:
        out.append([ka, kb, ri]); continue
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
    if segs:   # the range starts are set on the voice onsets: trust them
        segs[0][0] = min(segs[0][0], ka)
    mine = [w for w in words if w["range"] == ri]
    for a, b in segs:
        if b - a >= 0.08 and (b - a >= 0.25 or any(a - 0.03 <= w["start"] < b for w in mine)):
            out.append([a, b, ri])
for ca, cb in CUTS:
    out = [p for a, b, ri in out for p in ([[a, ca, ri], [cb, b, ri]] if a < ca and cb < b else
                                           [[a, min(b, ca), ri]] if a < ca < b else [[max(a, cb), b, ri]] if a < cb < b else [[a, b, ri]])]
for p_, q_ in zip(out, out[1:]):   # two ranges that touch: their margins must not overlap (the audio would repeat)
    if p_[0] - 0.01 < q_[0] < p_[1]:
        p_[1] = q_[0] = (q_[0] + p_[1]) / 2

segments = [{"name": f"s{k + 1:03d}", "in": round(a, 3), "out": round(b, 3), "range": ri} for k, (a, b, ri) in enumerate(out)]
db = lambda t: 20 * np.log10(np.sqrt((pcm[int(t * 16000):int(t * 16000) + 320] ** 2).mean()) + 1e-9)
for sg in segments:
    for edge, t in (("in", sg["in"]), ("out", sg["out"] - 0.02)):
        if db(t) > -35:
            print(f"  ! {sg['name']} range {sg['range']} {edge} at {t:.2f}: voice {db(t):.0f} dB")
D.mkdir(parents=True, exist_ok=True)
(D / "raw.segments.json").write_text(json.dumps(segments, indent=1))
kept = []
for s in segments:
    for w in words:
        if w["range"] is not None and w["text"] and s["in"] - 0.03 <= w["start"] < s["out"] and w not in kept:
            w["end"] = min(w["end"], s["out"])
            kept.append(w)
bare = lambda t: re.sub(r"[.,;:!?…]+$", "", t)   # as in the other lessons: the captions split on capitals and pauses
(D / "raw.captions.json").write_text(json.dumps(
    [{"text": bare(w["text"]), "startMs": round(w["start"] * 1000), "endMs": round(w["end"] * 1000)} for w in kept],
    ensure_ascii=False, indent=1))
print(f"{len(segments)} segments · {len(kept)} words · {sum(s['out'] - s['in'] for s in segments):.1f} s")
print(" ".join(w["text"] for w in kept))
