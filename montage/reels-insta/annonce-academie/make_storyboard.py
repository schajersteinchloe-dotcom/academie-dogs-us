#!/usr/bin/env python3
"""make_storyboard.py — storyboard.json + sfx-events.json of one version of the Académie announcement.

Usage: python3 make_storyboard.py v1|v2|v3 PROJECT_DIR
Reads the cut written by derush_plan.py + stage_lowmem.py (assets/derush/raw.segments.json with each piece's sentence,
assets/edit-decisions.json, assets/transcript.json). One scene per sentence (a few sentences are split on a word), all in
layout F (full-frame face, pop captions on the chest). Each scene alternates the face's zoom level (jump-cut feel) and
carries its labels: black (K), white (W) and red (R) boxes like the lessons' tags, popped on the word they illustrate.
The sound effects follow the motion: a pop per label, a tick per list item, a ding on the message, a whoosh + boom on
the « Académie Dogs & Us » reveal, a swish on the sentence changes that have nothing else.
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


# sentence → sub-scenes: (split word or None, items, zoom punches, extra sfx)
DESIGN = {
    "H1": [(None, [dict(image="assets/img/message.png", anim="notif", at=0.12, top=48, left=320, w=440, tilt=-4,
                        badge="99+", stack=2, out_at="w:j'ouvre", sfx="ding"),
                   box("MA COMMUNAUTÉ EN LIGNE", "w:communauté", 0, 60, K),
                   box("L'ENTRÉE EST GRATUITE", "w:gratuite", 1, 62, R, check=True, pop="rise")],
            [{"at": "w:j'ouvre", "to": 1.1, "dur": 0.25}], [])],
    "J1": [(None, [box("MA COMMUNAUTÉ EN LIGNE", "w:communauté", 0, 60, K),
                   box("L'ENTRÉE EST GRATUITE", "w:gratuite", 1, 62, R, check=True, pop="rise")],
            [{"at": "w:j'ouvre", "to": 1.1, "dur": 0.25}], [])],
    "J1b": [(None, [box("MA COMMUNAUTÉ EN LIGNE", "w:communauté", 0, 60, K),
                    box("L'ENTRÉE EST GRATUITE", "w:gratuite", 1, 62, R, check=True, pop="rise")],
             [], [])],
    "H2": [(None, [box("GRANDE", "w:grande", 0, 92, K),
                   box("ANNONCE", "w:annonce", top=282, size=120, style=R, weight=900, sfx="boom", pulse_at="w:faire", pulse=3)],
            [{"at": "w:annonce", "to": 1.16, "dur": 0.22}], [("riser", "w:annonce", -1)])],
    "H3": [(None, [box("JE VAIS PERDRE DES ABONNÉS…", "w:perdre", 0, 62, W, pop="rise"),
                   box("CHAQUE MAÎTRE DEVRAIT ÊTRE", "w:chaque", 1, 50, K),
                   box("L'ÉDUCATEUR DE SON CHIEN", "w:éducateur", 2, 60, R)],
            [{"at": "w:éducateur", "to": 1.1, "dur": 0.3}], []),
           ("Tout", [box("« ÉDUQUE TON CHIEN ! »", "w:dit", 0, 58, W, pop="rise"),
                     box("MAIS COMMENT ?", "w:personne", top=255, size=96, style=R, weight=900, pulse_at="w:comment", pulse=3)],
            [{"at": "w:comment", "to": 1.15, "dur": 0.22}], [])],
    "J2": [(None, [box("EN RENDEZ-VOUS", "w:rendez-vous", 0, 62, K),
                   box("AVEC MES CLIENTS", "w:clients", 1, 54, W, pop="rise")],
            [], [])],
    "J3a": [(None, [box("DES CENTAINES DE PERSONNES", "w:centaines", 0, 54, K),
                    box("LES MÊMES ERREURS", "w:erreurs", 1, 66, R, pop="rise")],
             [{"at": "w:erreurs", "to": 1.1, "dur": 0.3}], [])],
    "B2": [(None, [box("DEPUIS 2022", "w:2022", 0, 76, K, weight=900),
                   box("DES CENTAINES DE DUOS", "w:duos", 1, 52, W, pop="rise"),
                   box("LES MÊMES GALÈRES", "w:galères", 2, 62, R, pop="rise")],
            [{"at": "w:galères", "to": 1.1, "dur": 0.3}], [])],
    "B3": [(None, [box("IL TIRE EN LAISSE", "w:tire", 0, 54, W, sfx="tick", out_at="w:solitude"),
                   box("IL NE REVIENT PAS", "w:revient", 1, 54, W, sfx="tick", out_at="w:solitude"),
                   box("IL MORDILLE TOUT", "w:mordille", 2, 54, W, sfx="tick", out_at="w:solitude"),
                   box("LA SOLITUDE", "w:solitude", 0, 54, W, sfx="tick"),
                   box("LA PROPRETÉ", "w:propreté", 1, 54, W, sfx="tick")],
            [], []),
           ("Bref,", [box("TOUT LE TEMPS", "w:revient", top=200, size=100, style=R, weight=900)],
            [{"at": "w:temps", "to": 1.12, "dur": 0.25}], [])],
    "J3b": [(None, [box("UNE SOLUTION", "w:solution", top=170, size=92, style=R, weight=900),
                    box("POUR VOUS AIDER", "w:aider", top=300, size=54, style=W, pop="rise")],
             [], [])],
    "B4": [(None, [box("L'ACADÉMIE", "w:l'académie", top=150, size=92, style=K, weight=900, sfx="whoosh", out_at="w:communauté"),
                   box("DOGS & US", "w:dogs", top=270, size=128, style=R, weight=900, sfx="boom"),
                   box("UNE COMMUNAUTÉ EN LIGNE", "w:communauté", top=150, size=54, style=W, pop="rise")],
            [{"at": "w:l'académie", "to": 1.15, "dur": 0.22}], [])],
    "B4s": [(None, [box("L'ACADÉMIE", "w:l'académie", top=150, size=92, style=K, weight=900, sfx="whoosh"),
                    box("DOGS & US", "w:dogs", top=270, size=128, style=R, weight=900, sfx="boom", pulse_at="w:us", pulse=3)],
             [{"at": "w:l'académie", "to": 1.15, "dur": 0.22}], [])],
    "K1": [(None, [box("DES VIDÉOS", "w:vidéos", 0, 66, W, dim_at="w:important", dim_to=0.5)],
            [], []),
           (("range", 1), [box("LE PLUS IMPORTANT", "w:important", 0, 48, K),
                           box("COMPRENDRE TON CHIEN", "w:comprennes", 1, 62, R),
                           box("QUOI FAIRE ET POURQUOI", "w:saches", 2, 52, W, pop="rise")],
            [{"at": "w:comprennes", "to": 1.1, "dur": 0.3}], [])],
    "B5": [(None, [kicker("DANS L'ACADÉMIE", 0.15),
                   box("GUIDES GRATUITS", "w:guides", 0, 68, R, check=True),
                   box("CHIOT", "w:chiot", 1, 52, W, sfx="tick", out_at="w:marche", pop="rise"),
                   box("MARCHE EN LAISSE", "w:marche", 1, 52, W, sfx="tick", out_at="w:adoption", pop="rise"),
                   box("ADOPTION", "w:adoption", 1, 52, W, sfx="tick", out_at="w:réactif", pop="rise"),
                   box("CHIEN RÉACTIF", "w:réactif", 1, 52, W, sfx="tick", pop="rise")],
            [], [])],
    "B6": [(None, [kicker("DANS L'ACADÉMIE", 0.15),
                   box("FORMATIONS VIDÉO", "w:formations", 0, 68, R, check=True),
                   box("PAS À PAS", "w:pas", 1, 56, W, pop="rise")],
            [{"at": "w:éduquer", "to": 1.08, "dur": 0.4}], [])],
    "B7": [(None, [kicker("DANS L'ACADÉMIE", 0.15),
                   box("DES LIVES AVEC MOI", "w:live", 0, 68, R, check=True),
                   box("JE RÉPONDS À TES QUESTIONS", "w:répondre", 1, 50, W, pop="rise")],
            [], [])],
    "B8": [(None, [box("LE PLUS INTÉRESSANT", "w:intéressant", top=70, size=40, style=K, weight=700, tracking=".06em"),
                   box("UNE COMMUNAUTÉ", "w:communauté", 0, 68, R, check=True),
                   box("DE MAÎTRES COMME TOI", "w:toi", 1, 54, W, pop="rise"),
                   box("ON S'ENTRAIDE", "w:s'entraider", 2, 60, K, pop="rise")],
            [{"at": "w:s'entraider", "to": 1.1, "dur": 0.3}], [])],
    "B9": [(None, [box("L'OBJECTIF", "w:l'objectif", 0, 56, K),
                   box("COMPRENDRE TON CHIEN", "w:comprennes", 1, 62, R),
                   box("SAVOIR QUOI FAIRE", "w:saches", 2, 52, W, pop="rise")],
            [], []),
           ("Et", [box("UNE VIE PLUS DOUCE", "w:douce", top=190, size=82, style=R, weight=900)],
            [{"at": "w:douce", "to": 1.12, "dur": 0.4, "ease": "power2.out"}], [])],
    "CTA": [(None, [box("ENTRÉE GRATUITE", "w:gratuite", top=180, size=84, style=R, weight=900, check=True)],
             [], []),
            ("donc,", [box("COMMENTE", "w:commente", 0, 62, K),
                       box("ACADÉMIE", "w:académie", top=250, size=124, style=R, weight=900, sfx="boom", pulse_at="w:t'envoie", pulse=7),
                       box("ET JE T'ENVOIE LE LIEN", "w:lien", top=420, size=48, style=W, pop="rise"),
                       dict(chevrons=True, at="w:rejoindre", top=1640, sfx=None)],
             [{"at": "w:commente", "to": 1.1, "dur": 0.25}], [])],
}
MERGE = {"v1": {"J1": "H1"}}    # v1: the message stays up while she answers it (« j'ouvre ma communauté »)
FACE_SCALES = [1.0, 1.1, 1.03, 1.14]
KEYWORDS = ["message", "annonce", "gratuite", "galères", "Académie", "Dogs", "Us", "guides", "formations", "live",
            "entraider", "douce", "commente", "abonnés", "comment", "erreurs", "éducateur", "2022", "comprennes", "solution"]

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
                sfx.append({"t": round(ta + 0.03, 3), "sound": snd, "db": {"swish": -2}.get(snd, 0)})
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
scenes[-1]["end"] = DUR
sb = {
    "id": f"annonce-academie-{VERSION}", "title": f"Annonce Académie Dogs & Us ({VERSION})", "duration": DUR, "fps": 30,
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
