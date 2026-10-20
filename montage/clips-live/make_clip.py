#!/usr/bin/env python3
"""make_clip.py — cuts one short (9:16) out of the live, with burned-in captions between the webcam and the chart.

Usage: python3 tools/make_clip.py clips.json <id> [--preview]

clips.json: [{ "id": "01-...", "keep": [[a, b], ...], "drop": [[a, b], ...], "fix": {"old": "new"}, "words": {...} }]
  keep  source ranges in seconds (word starts inside a range are kept)
  drop  source ranges removed from inside the keeps (asides, chat reading, retakes)
  fix   token replacements for the captions (transcription errors)

Layout (source 720x1280): webcam rows 0-384, the live's own « Rejoins mon lien en bio » sticker and the divider
(384-436) are replaced by a black band, chart rows 436-1280 below. Scaled to 1080x1920; captions centered on the band.
Silences longer than MAX_GAP inside a clip are cut (jump cuts), each piece keeps PRE/POST of air around its words.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("clips")
ap.add_argument("id")
ap.add_argument("--src", default=str(ROOT / "src" / "live.mp4"))
ap.add_argument("--transcript", default=str(ROOT / "transcript-full.json"))
ap.add_argument("--out", default=str(ROOT / "out"))
ap.add_argument("--preview", action="store_true", help="fast encode")
ap.add_argument("--top", type=int, default=384, help="source rows kept above the band (the webcam)")
ap.add_argument("--band", type=int, default=52, help="source rows replaced by the caption band (sticker, toolbar, divider)")
args = ap.parse_args()

MAX_GAP, PRE, POST = 0.50, 0.10, 0.16
VOICE_DB = -42
TOP, BAND = args.top, args.band        # source rows: webcam 0..TOP, band TOP..TOP+BAND, chart below
BAND_Y = (TOP + BAND / 2) * 1.5        # caption center in the 1080x1920 frame
CAP_MAX_WORDS, CAP_MAX_CHARS = 4, 20
NOTE_Y = 740                           # notes sit at the top of the chart
GOLD = "&H3CC9FF&"                     # ASS colours are BGR: #FFC93C
WHITE = "&HFFFFFF&"

clip = next(c for c in json.load(open(args.clips)) if c["id"] == args.id)
words = json.load(open(args.transcript))["words"]


def inside(t, ranges):
    return any(a - 0.02 <= t < b - 0.02 for a, b in ranges)


# keeps play in the order they are listed (a later moment can open the clip); punctuation tokens join their word
_pw = []
for i, w in enumerate(words):
    if _pw and not re.search(r"\w", w["text"]):
        _pw[-1] = dict(_pw[-1], text=_pw[-1]["text"] + w["text"])
    else:
        _pw.append(dict(w, idx=len(_pw)))
words = _pw
ws = [dict(w) for a, b in clip["keep"] for w in words if a - 0.02 <= w["start"] < b - 0.02 and not inside(w["start"], clip.get("drop", []))]
for k, v in clip.get("words", {}).items():          # "start": "new text" (or "" to remove that word)
    for w in ws:
        if abs(w["start"] - float(k)) < 0.02:
            w.update(v if isinstance(v, dict) else {"text": v})
# WhisperX stretches a word's end over the silence that follows: end it where the voice stops (10 ms frames)
import wave
import numpy as np
_wv = wave.open(str(ROOT / "src" / "audio16k.wav"))
_a = np.frombuffer(_wv.readframes(_wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768
_f = _a[: len(_a) // 160 * 160].reshape(-1, 160)
VOICED = 20 * np.log10(np.sqrt((_f ** 2).mean(1)) + 1e-9) > VOICE_DB
for w in words + ws:
    if w["end"] - w["start"] > 0.7:
        i, stop = int((w["start"] + 0.1) * 100), int(w["end"] * 100)
        while i < stop and VOICED[i:i + 25].any():
            i += 1
        w["end"] = min(w["end"], i / 100 + 0.03)
fix = clip.get("fix", {})
for w in ws:
    w["text"] = fix.get(w["text"], w["text"])
if not ws:
    sys.exit("no words in this clip")

# pieces of speech: consecutive words of the live closer than MAX_GAP stay together (a skipped word always cuts)
pieces = []
for w in ws:
    if pieces and w["idx"] == pieces[-1][-1]["idx"] + 1 and w["start"] - pieces[-1][-1]["end"] <= MAX_GAP:
        pieces[-1].append(w)
    else:
        pieces.append([w])
segs = []
pieces = [[w for w in p if w["text"]] for p in pieces]
pieces = [p for p in pieces if p]
for p in pieces:
    a, b = p[0]["start"] - PRE, p[-1]["end"] + POST
    # the air around a piece never reaches into the neighbouring words of the live that are not in it
    i0, i1 = p[0]["idx"], p[-1]["idx"]
    if i0 > 0:
        a = max(a, min(words[i0 - 1]["end"] + 0.03, p[0]["start"] - 0.02))
    if i1 + 1 < len(words):
        b = min(b, max(words[i1 + 1]["start"] - 0.03, p[-1]["end"] + 0.02))
    if segs and segs[-1][0] < a < segs[-1][1]:
        mid = (segs[-1][1] + a) / 2
        segs[-1][1], a = mid, mid
    segs.append([max(0.0, a), b])
# transcript times are those of the extracted wav; in the live's mp4 the audio starts OFFSET s after the video,
# so a media time is wav time + OFFSET. Pieces are cut in media time, snapped to the 30 fps frame grid
# (video and audio then last exactly the same, so captions never drift)
OFFSET = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=start_time",
                               "-of", "csv=p=0", args.src], capture_output=True, text=True).stdout.strip() or 0)
segs = [[int((a + OFFSET) * 30) / 30, -int(-(b + OFFSET) * 30) / 30] for a, b in segs]

# output timeline: word times shifted into their segment
out_t, t0 = [], 0.0
for (a, b), p in zip(segs, pieces):
    for w in p:
        out_t.append({"text": w["text"], "start": t0 + w["start"] + OFFSET - a, "end": t0 + w["end"] + OFFSET - a})
    t0 += b - a
DUR = t0


def norm_caps(s):
    return s.upper().replace("’", "'")


# caption groups: a sentence (or a stretch between pauses) is split into the fewest balanced groups that fit
# CAP_MAX_WORDS / CAP_MAX_CHARS, so a group never runs across two sentences or leaves a lone word behind
def fits(g):
    return len(g) <= CAP_MAX_WORDS and len(" ".join(x["text"] for x in g)) <= CAP_MAX_CHARS + 2


sentences, cur = [], []
for w in out_t:
    if cur and w["start"] - cur[-1]["end"] > 0.35:
        sentences.append(cur)
        cur = []
    cur.append(w)
    if re.search(r"[.?!…]$", w["text"]) or (re.search(r"[,:;]$", w["text"]) and len(cur) >= 3):
        sentences.append(cur)
        cur = []
if cur:
    sentences.append(cur)
groups = []
for sent in sentences:
    n = 1
    while True:
        size = len(sent) / n
        parts = [sent[round(i * size):round((i + 1) * size)] for i in range(n)]
        if all(fits(g) for g in parts) or n >= len(sent):
            break
        n += 1
    groups += [g for g in parts if g]


def ts(t):
    t = max(0.0, t)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def clean(s):
    return re.sub(r"\s*[.,;:]+$", "", s).strip()


ev = []
for gi, g in enumerate(groups):
    g_end = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else DUR
    g_end = min(g_end, g[-1]["end"] + 0.6)
    for wi, w in enumerate(g):
        a = w["start"] if wi else g[0]["start"]
        b = g[wi + 1]["start"] if wi + 1 < len(g) else g_end
        parts = []
        for xi, x in enumerate(g):
            t = norm_caps(clean(x["text"]))
            parts.append(f"{{\\c{GOLD}}}{t}{{\\c{WHITE}}}" if xi == wi else t)
        pop = "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(540,{BAND_Y:.0f})}}{pop}{' '.join(parts)}")

for note in clip.get("notes", []):
    first = min(((w["start"], o) for w, o in zip([w for p in pieces for w in p], out_t) if w["start"] >= note["src"] - 0.02),
                key=lambda x: x[0])[1]                    # the kept word closest after the note's source time
    a = max(0.0, first["start"] - 0.15)
    ev.append(f"Dialogue: 1,{ts(a)},{ts(a + note.get('dur', 1.6))},Note,,0,0,0,,{{\\pos(540,{NOTE_Y})\\fad(120,180)}}{note['text']}")

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
ass = out / f"{clip['id']}.ass"
ass.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1
Style: Note,Montserrat Black,46,&H003CC9FF,&H003CC9FF,&H28000000,&H00000000,0,0,0,0,100,100,1,0,3,16,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")

# one seeked input per piece (fast, no buffering), concat, rebuild the layout, burn the captions, loudness to -14 LUFS
fc, n, inputs = [], len(segs), []
for i, (a, b) in enumerate(segs):
    nf = round((b - a) * 30)                               # exact frame and sample counts: no drift over many cuts
    inputs += ["-ss", f"{a:.4f}", "-t", f"{b - a + 0.3:.3f}", "-i", args.src]
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS,fps=30,trim=end_frame={nf},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,atrim=end_sample={nf * 1600},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.012,afade=t=out:st={nf / 30 - 0.012:.4f}:d=0.012[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append(f"[cv]split[t][c];[t]crop=720:{TOP}:0:0[top];[c]crop=720:{1280 - TOP - BAND}:0:{TOP + BAND}[bot];"
          f"color=black:s=720x{BAND}:r=30[band];[top][band][bot]vstack=3:shortest=1,scale=1080:1920:flags=lanczos,"
          f"ass={ass}:fontsdir={ROOT / 'fonts'},format=yuv420p[vout]")
fc.append("[ca]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
mp4 = out / f"{clip['id']}.mp4"
enc = ["-preset", "veryfast", "-crf", "26"] if args.preview else ["-preset", "medium", "-crf", "18"]
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", *enc, "-profile:v", "high", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", str(mp4)], check=True)
(out / f"{clip['id']}.words.json").write_text(json.dumps(out_t, ensure_ascii=False))
print(f"{clip['id']}: {len(segs)} pieces, {len(out_t)} words, {len(groups)} captions, {DUR:.1f} s → {mp4}")
print("   " + " ".join(w["text"] for w in out_t))
