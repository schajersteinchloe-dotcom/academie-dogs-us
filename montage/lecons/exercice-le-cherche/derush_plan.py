#!/usr/bin/env python3
"""Exercice (IMG_5142), le cherche: cut like Chloé's own edit « assisapprentissage.mp4 ».

Her edit keeps the demonstrations whole (the dog searching, finding, the praise) and cuts everything around them
tight; stumbles and abandoned sentences go. Here:
  KEEP  rush ranges whose words are kept (word starts in [a, b]); inside them, pauses longer than MAX_GAP are cut
        on the voice (WhisperX stretches word ends over the silence)
  SOLID rush ranges played whole, pauses included: the treat falling, Woody searching and finding

Writes assets/derush/raw.segments.json and raw.captions.json for scripts/stage_lowmem.py.
"""
import json, re, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / "assets" / "derush"
MAX_GAP, PRE, POST, VOICE_DB = 0.6, 0.10, 0.15, -45.0

KEEP = [
    (4.40, 17.10),     # « Pour la stimulation mentale… pour vraiment développer »
    (29.00, 30.10),    # « son meilleur atout » (« sa meilleure… sa meilleure quoi… » goes)
    (32.10, 45.20),    # « La première chose… faire tomber une friandise et dire cherche… il faut aller le chercher »
    (45.50, 48.60),    # « Cherche. Cherche. » (the third one, Woody already bored, goes)
    (53.40, 57.60),    # « Ensuite… commencer à le cacher. Par exemple, ici. »
    (62.90, 66.25),    # « Cherche. » he finds it, « Super. » (the first « Cherche », he doesn't move, goes)
    (70.50, 76.00),    # « Ensuite, qu'est-ce que vous pouvez faire ?… à un endroit. »
    (81.50, 83.26),    # « Moi, je prends ce plot-là, je demande »
    (84.44, 91.00),    # « un assis. Je mets la friandise derrière et je dis cherche. » he finds it (« à vous si à vous dit »,
                       # three transcriptions, never the same twice: it goes, the sentence holds without it)
    (103.00, 106.30),  # he finds it again: « Bravo ! Tu es trop fort ! »
    (107.60, 121.58),  # « Vous allez pouvoir commencer à faire ça dans tous les endroits… avec son nez, de chercher »
    (126.05, 131.60),  # « et d'aller du coup se stimuler mentalement par le flair, qui est l'atout le plus important »
    (137.40, 151.50),  # « Et donc c'est un jeu super intéressant… il pourra le retrouver dans la maison. »
]
SOLID = [
    (35.00, 38.70),    # she holds the treat up, lets it fall, Woody searches
    (45.50, 48.60),    # two more
    (62.90, 66.25),    # « Cherche », he finds it next to her, « Super »
    (79.30, 81.70),    # she takes the red pouf and puts it down
    (84.44, 86.50),    # « un assis »: he sits
    (88.10, 91.00),    # « et je dis cherche »: he goes round the pouf and finds it
    (103.00, 106.30),  # he finds it, « Bravo ! Tu es trop fort ! »
]
WORDS = {104.88: "T'es", 105.22: ""}        # « Tu es » is said « T'es »; "" keeps the sound, no caption
CAPITAL = (107.69,)                         # sentence starts the cut creates
LOWER = (126.11,)                           # « …de chercher et d'aller du coup se stimuler »

# words: the passage-by-passage transcripts where they exist (the finer first), the whole-rush one elsewhere
layers = [("regions2.json", "transcript-regions2.json"), ("regions.json", "transcript-regions.json")]
inside = lambda t, rs: any(a <= t <= b for a, b in rs)
words, covered = [], []
for rf, tf in layers:
    inner = [(r["in"] + 0.5, r["out"] - 0.5) for r in json.loads((ROOT / "src" / rf).read_text())]
    words += [w for w in json.loads((ROOT / "src" / tf).read_text())["words"]
              if inside(w["start"], inner) and not inside(w["start"], covered)]
    covered += inner
full = json.loads((ROOT / "src" / "transcript-full.json").read_text())["words"]
twin = lambda w: any(abs(w["start"] - r["start"]) < 0.15 and w["text"].lower().strip(".,?!") == r["text"].lower().strip(".,?!")
                     for r in words)
words = sorted(words + [w for w in full if not inside(w["start"], covered) and not twin(w)], key=lambda w: w["start"])
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
    k = round(w["start"], 2)
    w["text"] = WORDS.get(k, w["text"])
    if k in CAPITAL:
        w["text"] = w["text"][:1].upper() + w["text"][1:]
    if k in LOWER:
        w["text"] = w["text"][:1].lower() + w["text"][1:]
    w["keep"] = inside(w["start"], KEEP)
END = {17.00: 17.60}                          # « développer »: then the start of « sa meilleure », follow it
for w in words:
    w["end"] = END.get(round(w["start"], 2), w["end"])
for w, nxt in zip(words, words[1:]):           # a stretched word never runs into the next one
    w["end"] = min(w["end"], max(w["start"] + 0.05, nxt["start"] - 0.02))
for a, b in SOLID:
    assert all(w["keep"] for w in words if a <= w["start"] < b), f"a dropped word inside solid {a}-{b}"

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
