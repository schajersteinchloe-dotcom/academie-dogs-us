#!/usr/bin/env python3
"""build-lesson.py — lesson.json → index.html: a 16:9 lesson in the Dogs & Us look.

Usage: python3 scripts/build-lesson.py [lesson.json] [--until SECONDS]

Reads : lesson.json, assets/transcript.json and assets/edit-decisions.json (stage.py), the speaker and the audio
Writes: index.html (generated: edit lesson.json, never this file)

The look is measured on the reference, « Leçon 2 · L'équipement de ton chiot » (1920×1080):
  - top-left column at x 70: the chapter tag (black, h 75, radius 12, uppercase) at y 52, then the cards
    (h 59, one every 78 px from y 140, radius 10): white with dark text, `alert` red with "× ", `arrow` with "→ ";
  - a tag or a card fades in rising 10 px in 0.2 s on its word; at a new part the whole column leaves upwards,
    blurred, then the next tag comes in; nothing on screen after `end_at` (the outro);
  - captions: one centred white line, words revealed as they are spoken, the line keeps its final layout;
  - optional cut-out product photos (`images`) on the left while she names them;
  - sound (assets/sfx-events.json, mixed by mix-sfx.py): a double tick on each card of a numbered part, a swish
    before the first tag and when a column leaves, never on the opening cards (`"ticks": true` on a part forces them).

lesson.json:
  { "id": "lecon-3", "title": "…", "caption_max_words": 7, "lexicon": {"cong": "Kong"}, "end_at": "w:à bientôt",
    "chapters": [ { "tag": "Leçon 3", "at": 0.4, "cards": [ {"text": "Le titre", "at": 0.6},
                                                           {"text": "Le piège", "kind": "alert", "at": "w:piège"} ] },
                  { "tag": "1 · La laisse", "at": "w:laisse", "cards": [ … ] } ],
    "images": [ {"src": "assets/img/os.png", "x": 40, "y": 360, "w": 320, "rotate": -12, "at": "w:ceci", "out": 171.2} ] }
  Every time is seconds or "w:words" = the start of the first occurrence of these words after the chapter (or card) start.
"""
import argparse, html, json, re
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("lesson", nargs="?", default="lesson.json")
ap.add_argument("--until", type=float, default=None, help="stop the composition there (a quick draft of the opening)")
args = ap.parse_args()

ROOT = Path(__file__).resolve().parent.parent
lesson = json.loads((ROOT / args.lesson).read_text())
transcript = json.loads((ROOT / "assets" / "transcript.json").read_text())
decisions = json.loads((ROOT / "assets" / "edit-decisions.json").read_text())

W, H = 1920, 1080
FPS = int(lesson.get("fps", 30))
ID = lesson.get("id", "lecon")
SPEAKER = lesson.get("speaker", "assets/speaker.mp4")
AUDIO = lesson.get("audio", "assets/reel-audio.wav")
DURATION = round(float(decisions["duration"]), 3)
if args.until:
    DURATION = min(DURATION, args.until)
CAP_MAX_WORDS = int(lesson.get("caption_max_words", 6))
CAP_MAX_CHARS = int(lesson.get("caption_max_chars", 36))

COL_X, TAG_Y, CARD_Y, CARD_PITCH = 70, 52, 140, 78
ENTER, EXIT, EXIT_LEAD = 0.2, 0.2, 0.4      # a part's column starts leaving EXIT_LEAD before the next tag
MAX_CARDS = 8
# Archivo has no arrow: the reference's long thin one, drawn
ARROW_SVG = ('<svg width="36" height="18" viewBox="0 0 36 18"><path d="M2 9H33M26 2.5l7 6.5-7 6.5" fill="none" stroke="currentColor" '
             'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def r3(x):
    return round(float(x), 3)


def esc(s):
    return html.escape(str(s), quote=True)


def norm(s):
    return re.sub(r"[^\w%']", "", s.replace("’", "'").lower())


def apply_lexicon(words):
    lex = {norm(k): v for k, v in lesson.get("lexicon", {}).items()}
    return [dict(w, text=lex.get(norm(w["text"]), w["text"])) for w in words]


WORDS = apply_lexicon(transcript.get("words", []))
NW = [norm(w["text"]) for w in WORDS]


def at_time(at, lo=0.0):
    """Seconds, or "w:words" = start of the first occurrence of these words at or after `lo`."""
    if isinstance(at, (int, float)):
        return float(at)
    if isinstance(at, str) and at.startswith("w:"):
        target = [norm(x) for x in at[2:].split()]
        for i in range(len(WORDS)):
            if WORDS[i]["start"] >= lo - 0.05 and NW[i:i + len(target)] == target:
                return float(WORDS[i]["start"])
        raise SystemExit(f"anchor not found after {lo:.2f} s: {at}")
    return float(at)


# ----------------------------------------------------------------------------- the column: chapter tags and cards

chapters = []
lo = 0.0
for ch in lesson["chapters"]:
    t = at_time(ch["at"], lo)
    chapters.append({"tag": ch["tag"], "at": t, "cards": ch.get("cards", [])})
    lo = t
end_at = at_time(lesson["end_at"], chapters[-1]["at"]) if lesson.get("end_at") is not None else DURATION

col_html, col_tl, plan = [], [], []
# sound effects, as in the reference: a double tick on every card of a numbered part (not the opening ones),
# a swish just before the first tag and each time a column has left; times are the sound's peak
sfx = []
for n, ch in enumerate(chapters):
    if ch["at"] >= DURATION:  # a draft cut short with --until
        break
    nxt = chapters[n + 1]["at"] if n + 1 < len(chapters) else None
    leave = (nxt - EXIT_LEAD) if nxt is not None else end_at
    if leave - ch["at"] < 1.0:
        raise SystemExit(f"part « {ch['tag']} » lasts less than a second ({ch['at']:.2f} → {leave:.2f} s)")
    cid = f"col{n + 1}"
    stop = min(leave + EXIT, DURATION)
    items = [f'<div class="tag" id="{cid}-tag">{esc(ch["tag"])}</div>']
    col_tl.append(f'tl.from("#{cid}-tag", {{ opacity: 0, y: 10, duration: {ENTER}, ease: "power2.out" }}, {r3(ch["at"])});')
    sfx.append({"t": r3(max(0.05, ch["at"] - (0.10 if n == 0 else EXIT_LEAD - EXIT / 2))), "sound": "swish"})
    plan.append(f"{ch['at']:7.2f}s  [{ch['tag']}]")
    if len(ch["cards"]) > MAX_CARDS:
        raise SystemExit(f"part « {ch['tag']} »: {len(ch['cards'])} cards, {MAX_CARDS} at most fit above the captions")
    clo = ch["at"]
    for k, card in enumerate(ch["cards"]):
        t = at_time(card["at"], clo)
        if not (ch["at"] <= t < leave - 0.3):
            raise SystemExit(f"card « {card['text']} » at {t:.2f} s falls outside its part ({ch['at']:.2f} → {leave:.2f} s)")
        kind = card.get("kind", "note")
        text = card["text"]
        if kind == "alert" and not text.startswith("×"):
            text = "× " + text
        if kind == "arrow" and not text.startswith("→"):
            text = "→ " + text
        if len(text) > 36:
            print(f"warning: card « {text} » is long ({len(text)} characters), it may reach the face")
        kid = f"{cid}-c{k + 1}"
        body = esc(text)
        if text[:1] in "×→":  # the reference sets its symbol a little apart from the words
            sym = ARROW_SVG if text[0] == "→" else esc(text[0])
            body = f'<span class="sym{" arrow" if text[0] == "→" else ""}">{sym}</span>{esc(text[1:].lstrip())}'
        items.append(f'<div class="card{" alert" if kind == "alert" else ""}" id="{kid}" style="top:{CARD_Y - TAG_Y + CARD_PITCH * k}px">{body}</div>')
        col_tl.append(f'tl.from("#{kid}", {{ opacity: 0, y: 10, duration: {ENTER}, ease: "power2.out" }}, {r3(t)});')
        plan.append(f"{t:7.2f}s     {text}")
        if lesson["chapters"][n].get("ticks", n > 0):
            sfx.append({"t": r3(t), "sound": "tick"})
        clo = t
    col_tl.append(f'tl.to("#{cid}", {{ opacity: 0, y: -12, filter: "blur(8px)", duration: {EXIT}, ease: "power2.in" }}, {r3(leave)});')
    if nxt is None:
        sfx.append({"t": r3(leave + EXIT / 2), "sound": "swish"})
    col_html.append(f'<div id="{cid}" class="col clip" data-start="{r3(ch["at"])}" data-duration="{r3(stop - ch["at"])}" data-track-index="{2 + n % 2}">'
                    + "".join(items) + "</div>")

# ----------------------------------------------------------------------------- product photos

img_html, img_tl = [], []
for n, im in enumerate(lesson.get("images", []), 1):
    t0 = at_time(im["at"])
    t1 = at_time(im["out"], t0) if im.get("out") is not None else t0 + 3.0
    if t0 >= DURATION:
        continue
    t1 = min(t1, DURATION)
    iid = f"img{n}"
    img_html.append(f'<img id="{iid}" class="photo clip" src="{esc(im["src"])}" data-start="{r3(t0)}" data-duration="{r3(t1 - t0)}" data-track-index="{4 + n % 2}" '
                    f'style="left:{im.get("x", 40)}px;top:{im.get("y", 340)}px;width:{im.get("w", 320)}px;transform:rotate({im.get("rotate", 0)}deg)">')
    img_tl.append(f'tl.from("#{iid}", {{ opacity: 0, scale: 0.85, duration: 0.25, ease: "back.out(1.8)" }}, {r3(t0)});')
    img_tl.append(f'tl.to("#{iid}", {{ opacity: 0, duration: 0.2 }}, {r3(t1 - 0.2)});')
    plan.append(f"{t0:7.2f}s  (photo {im['src']})")

# ----------------------------------------------------------------------------- captions


def caption_chunks():
    sentences, cur = [], []
    for w in WORDS:
        starts_sentence = bool(cur) and w["text"][:1].isupper() and not re.match(r"^[A-Z0-9]{2,}$", w["text"])
        if cur and (w["start"] - cur[-1]["end"] > 0.5 or starts_sentence):
            sentences.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.!?…]$", w["text"]):
            sentences.append(cur); cur = []
    if cur:
        sentences.append(cur)
    chunks = []
    for sen in sentences:
        # balanced groups: at most CAP_MAX_WORDS words and CAP_MAX_CHARS characters per line
        k = 1
        while True:
            size = -(-len(sen) // k)
            groups = [sen[a:a + size] for a in range(0, len(sen), size)]
            if size <= CAP_MAX_WORDS and all(len(" ".join(w["text"] for w in g)) <= CAP_MAX_CHARS for g in groups) or size == 1:
                break
            k += 1
        chunks.extend(groups)
    return chunks


cap_html, cap_tl = [], []
chunks = [c for c in caption_chunks() if c[0]["start"] < DURATION]
for i, ch in enumerate(chunks, 1):
    start = ch[0]["start"]
    end = max(ch[-1]["end"], start + 0.5) + 0.25
    if i < len(chunks):
        end = min(end, chunks[i][0]["start"])
    end = min(end, DURATION)
    parts = []
    for j, w in enumerate(ch):
        wid = f"cap{i}w{j}"
        parts.append(f'<b id="{wid}">{esc(w["text"])}</b>')
        if j:  # the first word comes with the line
            cap_tl.append(f'tl.from("#{wid}", {{ opacity: 0, duration: 0.1 }}, {r3(max(start, w["start"] - 0.02))});')
    cap_html.append(f'<div id="cap{i}" class="cap clip" data-start="{r3(start)}" data-duration="{r3(end - start)}" data-track-index="{20 + i % 4}"><span>{" ".join(parts)}</span></div>')

# ----------------------------------------------------------------------------- page

FONT_FACES = "\n".join(
    f'@font-face {{ font-family: "Archivo"; font-weight: {wt}; src: url(assets/fonts/archivo-{sub}-{wt}-normal.woff2) format("woff2"); unicode-range: {rng}; }}'
    for wt in (600, 700, 800)
    for sub, rng in (("latin", "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"),
                     ("latin-ext", "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF")))

index = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{esc(lesson.get("title", ID))}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      /* generated by scripts/build-lesson.py: edit lesson.json, not this file */
      {FONT_FACES}
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; font-family: "Archivo", "DejaVu Sans", sans-serif; }}
      #speaker {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0; }}
      .col {{ position: absolute; left: {COL_X}px; top: {TAG_Y}px; width: 1100px; height: 900px; z-index: 2; }}
      .tag, .card {{ position: absolute; left: 0; display: flex; align-items: center; white-space: nowrap;
                    box-shadow: 0 6px 18px rgba(0, 0, 0, .16); }}
      .tag {{ top: 0; height: 75px; padding: 0 24px 0 23px; border-radius: 12px; background: #0E0C0D; color: #fff;
              font-weight: 800; font-size: 47px; letter-spacing: .02em; text-transform: uppercase; }}
      .card {{ height: 59px; padding: 0 17px 1px 18px; border-radius: 10px; background: #fff; color: #0E0C0D;
               font-weight: 700; font-size: 37px; letter-spacing: -.02em; }}
      .card.alert {{ background: #E8462A; color: #fff; }}
      .card .sym {{ margin-right: .22em; font-size: 1.25em; line-height: 1; }}
      .card .sym.arrow {{ display: inline-flex; margin-right: .14em; position: relative; top: -1px; }}
      .photo {{ position: absolute; z-index: 3; filter: drop-shadow(0 14px 22px rgba(0, 0, 0, .28)); }}
      .cap {{ position: absolute; left: 160px; right: 160px; top: 922px; z-index: 5; text-align: center; color: #fff;
              font-weight: 700; font-size: 57px; line-height: 1.1; letter-spacing: -.015em;
              text-shadow: 0 2px 5px rgba(0, 0, 0, .45), 0 6px 18px rgba(0, 0, 0, .3); }}
      .cap span {{ display: inline-block; white-space: nowrap; }}
      .cap b {{ font-weight: inherit; display: inline-block; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="{esc(ID)}" data-start="0" data-duration="{r3(DURATION)}" data-width="{W}" data-height="{H}">
      <video id="speaker" class="clip" src="{esc(SPEAKER)}" data-start="0" data-duration="{r3(DURATION - 1 / FPS)}" data-media-start="0" data-track-index="0" muted playsinline></video>
      <audio id="voice" class="clip" src="{esc(AUDIO)}" data-start="0" data-duration="{r3(DURATION)}" data-track-index="10" data-volume="1"></audio>
      {chr(10).join("      " + x for x in col_html)}
      {chr(10).join("      " + x for x in img_html)}
      {chr(10).join("      " + x for x in cap_html)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + x for x in col_tl + img_tl + cap_tl)}
      tl.to({{}}, {{ duration: {r3(DURATION)} }}, 0);
      window.__timelines["{esc(ID)}"] = tl;
    </script>
  </body>
</html>
"""
(ROOT / "index.html").write_text(index)
(ROOT / "assets" / "sfx-events.json").write_text(json.dumps([e for e in sfx if e["t"] < DURATION - 0.3], indent=1))
print("\n".join(plan))
print(f"{len(chapters)} parts, {sum(len(c['cards']) for c in chapters)} cards, {len(chunks)} captions, {DURATION:.1f} s → index.html")
