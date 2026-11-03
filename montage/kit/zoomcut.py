#!/usr/bin/env python3
"""4K/60 rush → 1080p/30 with punch-ins on the far demos, cut straight from the 4K pixels (a 2x zoom stays sharp).

usage: zoomcut.py <in.MOV> <out.mp4> "a,b,zoom,cx,cy" ...
Each window [a, b] (seconds) is cropped to 1/zoom of the frame around (cx, cy) (fractions of width and height) and
scaled to 1920x1080; the rest is the whole frame. The pieces are trimmed and joined in one filter graph, so the
output keeps the rush's exact timeline (the cuts are planned on it).
"""
import subprocess, sys

src, out, *wins = sys.argv[1:]
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]))
W, H = 3840, 2160
pieces, t = [], 0.0
for w in sorted((tuple(map(float, x.split(','))) for x in wins)):
    a, b, z, cx, cy = w
    if a > t:
        pieces.append((t, a, None))
    pieces.append((a, b, (z, cx, cy)))
    t = b
if t < dur:
    pieces.append((t, dur, None))
fc, labels = [f"[0:v]fps=30,split={len(pieces)}" + ''.join(f"[s{i}]" for i in range(len(pieces)))], []
for i, (a, b, zm) in enumerate(pieces):
    chain = f"[s{i}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS"
    if zm:
        z, cx, cy = zm
        cw, ch = round(W / z / 2) * 2, round(H / z / 2) * 2
        x = min(max(0, round(cx * W - cw / 2)), W - cw)
        y = min(max(0, round(cy * H - ch / 2)), H - ch)
        chain += f",crop={cw}:{ch}:{x}:{y}"
    chain += f",scale=1920:1080:flags=lanczos,setsar=1[p{i}]"
    fc.append(chain)
    labels.append(f"[p{i}]")
fc.append(''.join(labels) + f"concat=n={len(pieces)}:v=1:a=0,format=yuv420p[v]")
cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-y', '-i', src, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '0:a:0',
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-g', '30', '-r', '30',
       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
print(' '.join(f"[{a:.1f}-{b:.1f}{' x%.1f' % zm[0] if zm else ''}]" for a, b, zm in pieces))
subprocess.run(cmd, check=True)
