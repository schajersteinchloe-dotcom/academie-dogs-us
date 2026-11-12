#!/usr/bin/env python3
"""make_storyboard.py — storyboard.json + sfx-events.json of one version of the story « Nala et l'os ».

Usage: python3 make_storyboard.py v1|v2|v3 PROJECT_DIR
Reads the cut written by derush_plan.py + stage_lowmem.py (assets/derush/raw.segments.json with each piece's sentence,
assets/edit-decisions.json, assets/transcript.json). One scene per sentence (a few sentences are split on a word), all in
layout F (full-frame face, pop captions on the chest). Each scene alternates the face's zoom level (jump-cut feel) and
carries its labels: black (K), white (W) and red (R) boxes like the lessons' tags, popped on the word they illustrate.
The punch-ins on Nala are already in the rush (zoomcut_v.py, zooms.txt): each one gets a whoosh. A pop per label, a tick
per counted item, a boom on the big beats, a riser before « tout d'un coup », a swish on the sentence changes that have
nothing else. The last frame is held 1.6 s under the closing question.
"""
import json, re, sys
from pathlib import Path

VERSION, PROJ = sys.argv[1], Path(sys.argv[2])
segs = json.loads((PROJ / "assets/derush/raw.segments.json").read_text())
ed = json.loads((PROJ / "assets/edit-decisions.json").read_text())
words = json.loads((PROJ / "assets/transcript.json").read_text())["words"]
DUR = float(ed["duration"])
assert len(ed["keeps"]) == len(segs), "edit-decisions and segments differ: re-run stage_lowmem.py"

K = {"bg": "#0E0C0D", "fg": "#fff"}
W = {"bg": "#fff", "fg": "#0E0C0D"}
R = {"bg": "#E8462A", "fg": "#fff"}


def box(text, at, row=0, size=62, style=K, sfx="pop", **kw):
    pos = {"top": kw.pop("top")} if "top" in kw else {"row": row}
    return dict(text=text, at=at, **pos, size=size, weight=kw.pop("weight", 800), box=style, sfx=sfx, **kw)


def kicker(text, at):
    return box(text, at, top=70, size=34, style=K, weight=700, tracking=".12em", sfx=None, pop="rise")


# sentence → sub-scenes: (split word / ("range", i) / None, items, zoom punches, extra sfx)
DESIGN = {
    "H1": [(None, [kicker("STORY TIME", 0.1),
                   box("45 MINUTES", "w:45", 0, 92, R, weight=900, sfx="boom"),
                   box("UN OS", "w:os", 1, 60, W, pop="rise", out_at="w:trésor"),
                   box("UN TRÉSOR !", "w:trésor", 1, 60, W, pop="rise")],
            [], []),
           ("Oui", [box("LA COUPABLE", "w:oui", top=150, size=84, style=R, weight=900)], [], [])],
    "H2": [(None, [box("STORY TIME", "w:story", 0, 82, K, weight=900),
                   box("UN OS GROS COMME UNE HANCHE", "w:hanche", 1, 48, W, pop="rise", out_at="w:galérer"),
                   box("45 MINUTES DE GALÈRE", "w:galérer", 1, 62, R, pop="rise")],
            [], [])],
    "H3": [(None, [kicker("STORY TIME", 0.1),
                   box("45 MINUTES", "w:45", 0, 92, R, weight=900, sfx="boom"),
                   box("POUR UN OS GÉANT", "w:os", 1, 56, W, pop="rise")],
            [], []),
           ("Dis-nous", [box("ALORS NALA ?", "w:dis-nous", top=150, size=84, style=R, weight=900)], [], [])],
    "B1": [(None, [box("SON TAPIS DE FOUILLE", "w:tapis", 0, 56, W, pop="rise")], [], [])],
    "B2": [(None, [box("EN BALADE", "w:balades", 0, 72, K, weight=900),
                   box("AVEC UNE AMIE", "w:amie", 1, 54, W, pop="rise")], [], [])],
    "B3": [(None, [box("LES HAUTES HERBES", "w:hautes", 0, 62, W, pop="rise")], [], []),
           (("range", 1), [box("ET LÀ…", "w:passe", top=150, size=110, style=R, weight=900)], [], [("riser", "w:coup", -2)])],
    "B4": [(None, [box("UN OS…", "w:os", 0, 66, W, out_at="w:hanche"),
                   box("GROS COMME UNE HANCHE DE MAMIE", "w:hanche", 0, 50, R, sfx="boom"),
                   box("TOUTE FIÈRE", "w:fière", 1, 66, K, pop="rise")],
            [{"at": "w:hanche", "to": 1.12, "dur": 0.25}], [])],
    "B5": [(None, [box("« C'EST TOP »", "w:top", 0, 62, W, out_at="w:trésor"),
                   box("SON TRÉSOR", "w:trésor", 0, 70, K, weight=900),
                   box("= LE SIEN", "w:sien", 1, 70, R, weight=900, pop="rise")],
            [], [])],
    "B6": [(None, [box("TRÈS BON RAPPEL", "w:rappel", 0, 60, W, check=True),
                   box("SAUF POUR SES TROUVAILLES", "w:trouvailles", 1, 52, R, pop="rise")],
            [{"at": "w:tolérante", "to": 1.1, "dur": 0.3}], [])],
    "B7": [(None, [box("FRIANDISES APPÉTENTES", "w:friandises", 0, 54, W, strike_at="w:contrefiche"),
                   box("ELLE S'EN CONTREFICHE", "w:contrefiche", 1, 60, R, pop="rise")],
            [], []),
           ("C'est-à-dire", [box("10 M", "w:10", top=150, size=120, style=W, weight=900, sfx="tick", out_at="w:20"),
                             box("20 M", "w:20", top=150, size=120, style=K, weight=900, sfx="tick", out_at="w:30"),
                             box("30 M", "w:30", top=150, size=120, style=R, weight=900, sfx="tick")],
            [{"at": "w:30", "to": 1.12, "dur": 0.2}], [])],
    "B7b": [(None, [box("ELLE SE POSAIT…", "w:posait", 0, 58, W, pop="rise"),
                    box("…ET REPARTAIT À 10 M", "w:repartait", 1, 58, R, pop="rise")], [], [])],
    "B8": [(None, [box("IMPOSSIBLE DE LA RÉCUPÉRER", "w:récupérer", 0, 48, W, out_at="w:sauf"),
                   box("CONCENTRÉE SUR MOI", "w:concentrée", 0, 58, K),
                   box("PAS SUR MON AMIE", "w:amie", 1, 58, R, pop="rise")], [], [])],
    "B9": [(None, [box("LE PLAN", "w:dit", 0, 76, K, weight=900),
                   box("LE PLUS LOIN POSSIBLE", "w:loin", 1, 52, W, pop="rise", out_at="w:gaga"),
                   box("VOIX GAGA", "w:gaga", 1, 64, R, pop="rise", out_at="w:nounou"),
                   box("« ALLEZ NOUNOU ! »", "w:nounou", 1, 58, W, pop="rise")],
            [{"at": "w:gaga", "to": 1.1, "dur": 0.25}], [])],
    "B10": [(None, [box("ELLE A OUBLIÉ MON AMIE", "w:oublié", 0, 52, W),
                    box("QUI SE RAPPROCHE…", "w:rapprocher", 1, 58, R, pop="rise")], [], [])],
    "B11": [(None, [box("« ALLEZ NOUNOU, À LA MAISON ! »", "w:allez", 0, 44, W, out_at="w:oreilles"),
                    box("LES OREILLES EN AVANT", "w:oreilles", 0, 56, K)], [], [])],
    "B12": [(None, [box("ET HOP !", "w:sauter", top=150, size=110, style=R, weight=900, sfx="boom", out_at="w:harnais"),
                    box("CHOPÉE AU HARNAIS", "w:harnais", top=150, size=62, style=K, pop="rise")],
             [{"at": "w:sauter", "to": 1.15, "dur": 0.18}], [])],
    "B13": [(None, [box("L'OS RÉCUPÉRÉ", "w:reprendre", 0, 62, W, check=True),
                    box("EN MAIN", "w:main", 1, 58, W, strike_at="w:bouche", out_at="w:pardon"),
                    box("EN BOUCHE, PARDON", "w:pardon", 1, 58, R, pop="rise")], [], [])],
    "B14": [(None, [box("45 MINUTES", "w:45", 0, 100, R, weight=900, sfx="boom", pulse_at="w:dîner", pulse=3),
                    box("+ UN DÎNER QUI M'ATTENDAIT", "w:dîner", 1, 46, W, pop="rise")], [], [])],
    "B15": [(None, [kicker("2 JOURS PLUS TARD…", "w:après"),
                    box("CACA BLANC", "w:caca", 0, 100, R, weight=900, out_at="w:mais"),
                    box("RIEN DE GRAVE", "w:rien", 0, 72, W, weight=900, check=True)],
             [{"at": "w:caca", "to": 1.15, "dur": 0.2}], [])],
    "B16": [(None, [kicker("STORY TIME", 0.05),
                    box("ET TOI, TON CHIEN T'A DÉJÀ FAIT ÇA ?", 0.4, 0, 44, W, pop="rise"),
                    dict(chevrons=True, at=0.9, top=1640, sfx=None)], [], [])],
}
MERGE = {}
FACE_SCALES = [1.0, 1.1, 1.03, 1.14]
KEYWORDS = ["Nala", "45", "trésor", "hanche", "mamie", "fière", "contrefiche", "gaga", "Nounou", "oreilles", "harnais",
            "énorme", "caca", "dîner", "grand-mère", "galérer", "sien", "Dis-nous", "story"]
TAIL = 1.6   # the last frame held under the closing question

norm = lambda t: re.sub(r"[^\w%']", "", t.lower())


def resolve(at, lo, hi):
    if isinstance(at, str) and at.startswith("w:"):
        tgt = norm(at[2:])
        for w in words:
            if lo - 0.05 <= w["start"] <= hi and norm(w["text"]) == tgt:
                return w["start"]
        raise SystemExit(f"{VERSION}: anchor not found {at} in [{lo:.2f}, {hi:.2f}]")
    return lo + float(at)


# sentence blocks in cut time
blocks = []
for s, k in zip(segs, ed["keeps"]):
    s["sentence"] = MERGE.get(VERSION, {}).get(s["sentence"], s["sentence"])
    if blocks and blocks[-1]["name"] == s["sentence"]:
        blocks[-1]["end"] = k["end"]; blocks[-1]["pieces"].append(k)
    else:
        blocks.append({"name": s["sentence"], "start": k["start"], "end": k["end"], "pieces": [k]})
scenes, sfx = [], []
for bi, b in enumerate(blocks):
    subs = DESIGN[b["name"]]
    cuts = [b["start"]]
    for split, *_ in subs[1:]:
        if isinstance(split, tuple):            # ("range", i): the block's i-th kept range starts a new scene
            piece = b["pieces"][split[1]] if split[1] < len(b["pieces"]) else b["pieces"][-1]
            cuts.append(piece["start"])
        else:
            w = next(w for w in words if b["start"] - 0.05 <= w["start"] < b["end"] and w["start"] > cuts[-1] + 0.3 and norm(w["text"]) == norm(split))
            prev = max((x["end"] for x in words if x["end"] <= w["start"] + 0.01), default=w["start"])
            cuts.append(round((min(prev, w["start"]) + w["start"]) / 2, 3))
    cuts.append(b["end"])
    for si, (split, items, zooms, extra) in enumerate(subs):
        t0, t1 = cuts[si], cuts[si + 1]
        n = len(scenes)
        sc = {"layout": "F", "start": round(t0, 3), "end": round(t1, 3), "cap_top": 1360,
              "face_scale": FACE_SCALES[n % len(FACE_SCALES)], "holdReason": f"{b['name']}: her face, the labels follow her words"}
        if zooms:
            sc["zoom"] = zooms
        # labels on rows: each row as tall as its biggest label, 16 px apart, from y 140 down
        rows = {}
        for it in items:
            if "row" in it:
                rows[it["row"]] = max(rows.get(it["row"], 0), it["size"] * 1.42)
        tops, y = {}, 140
        for r in sorted(rows):
            tops[r] = round(y); y += rows[r] + 16
        ov = []
        for it in items:
            if "row" in it:
                it = dict(it, top=tops[it["row"]]); it.pop("row")
            it = dict(it)
            snd = it.pop("sfx", "pop")
            ta = resolve(it["at"], t0, t1)
            for key in ("out_at", "dim_at", "pulse_at", "strike_at", "underline_at"):
                if it.get(key) is not None:
                    resolve(it[key], t0, t1)      # fail here, not in build-reel.py
            if snd:
                sfx.append({"t": round(ta + 0.03, 3), "sound": snd, "db": {"swish": -2, "boom": -3}.get(snd, 0)})
            if it.get("anim") == "notif":
                sfx.append({"t": round(ta + 0.55, 3), "sound": "pop", "db": -3})            # the badge
                sfx.append({"t": round(resolve(it["out_at"], t0, t1) + 0.15, 3), "sound": "whoosh", "db": -3})
            if snd == "boom":
                sfx.append({"t": round(ta - 0.05, 3), "sound": "whoosh", "db": -3})
            ov.append(it)
        for snd, at, db in extra:
            sfx.append({"t": round(resolve(at, t0, t1), 3), "sound": snd, "db": db})
        if ov:
            sc["overlay"] = {"out": round(t1 - 0.22, 3), "items": ov}
        scenes.append(sc)
        if n > 0 and not any(abs(e["t"] - t0) < 0.5 for e in sfx):
            sfx.append({"t": round(t0 + 0.02, 3), "sound": "swish", "db": -3})
# a whoosh on every punch-in on Nala that the cut keeps
for line in (Path(__file__).resolve().parent / "zooms.txt").read_text().split():
    a = float(line.split(",")[0])
    k = next((k for k in ed["keeps"] if k["sourceStart"] <= a + 0.05 <= k["sourceEnd"]), None)
    if k:
        t = max(k["start"], k["start"] + a - k["sourceStart"])
        if not any(abs(e["t"] - t) < 0.25 for e in sfx):
            sfx.append({"t": round(t + 0.04, 3), "sound": "whoosh", "db": -4})
scenes[-1]["end"] = DUR + TAIL
sb = {
    "id": f"story-nala-os-{VERSION}", "title": f"Story time · Nala et l'os ({VERSION})", "duration": DUR + TAIL, "fps": 30,
    "freeze_tail": TAIL,
    "speaker": "assets/speaker.mp4", "audio": "assets/reel-audio.wav",
    "caption_style": "pop", "caption_font": "\"Archivo\", \"Helvetica Neue\", Arial, sans-serif", "caption_size": 66,
    "caption_max_words": 3, "caption_accent": "#E8462A", "keywords": KEYWORDS, "locale": "fr-FR",
    "face_origin": "50% 30%", "face_drift": 0.025,
    "brand": {"bg": "#F3F1EE", "ink": "#0E0C0D", "accent": "#E8462A", "font": "\"Archivo\", \"Helvetica Neue\", Arial, sans-serif"},
    "scenes": scenes,
}
(PROJ / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1))
sfx.sort(key=lambda e: e["t"])
(PROJ / "assets/sfx-events.json").write_text(json.dumps(sfx, indent=1))
print(f"{VERSION}: {len(scenes)} scenes · {sum(len((s.get('overlay') or {}).get('items', [])) for s in scenes)} labels · {len(sfx)} sound effects · {DUR:.1f} s")
for s in scenes:
    print(f"  {s['start']:6.2f}-{s['end']:6.2f} x{s['face_scale']} " + " | ".join(i.get("text", "[image]" if "image" in i else "[chevrons]") for i in (s.get("overlay") or {}).get("items", [])))
