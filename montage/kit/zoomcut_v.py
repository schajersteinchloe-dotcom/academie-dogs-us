#!/usr/bin/env python3
"""zoomcut_v.py — a 4K rush (any orientation) → 1080p/30 with punch-ins cut straight from the 4K pixels.

usage: zoomcut_v.py <in.MOV> <out.mp4> [--size 1080x1920] "a,b,zoom,cx,cy" ...
Each window [a, b] (seconds) is cropped to 1/zoom of the frame around (cx, cy) (fractions of width and height) and
scaled to --size; the rest is the whole frame. The pieces are trimmed and joined in one filter graph, so the output
keeps the rush's exact timeline (the cuts are planned on it). Up to 2x the crop stays pixel-sharp from a 4K source.
"""
import subprocess, sys

args = sys.argv[1:]
size = "1080x1920"
if "--size" in args:
    i = args.index("--size"); size = args[i + 1]; del args[i:i + 2]
src, out, *wins = args
OW, OH = map(int, size.split("x"))
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]))
W, H = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                         '-of', 'csv=p=0', src]).decode().strip().split(','))
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
    chain += f",scale={OW}:{OH}:flags=lanczos,setsar=1[p{i}]"
    fc.append(chain)
    labels.append(f"[p{i}]")
fc.append(''.join(labels) + f"concat=n={len(pieces)}:v=1:a=0,format=yuv420p[v]")
cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '0:a:0',
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-g', '30', '-r', '30',
       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
print(' '.join(f"[{a:.1f}-{b:.1f}{' x%.1f' % zm[0] if zm else ''}]" for a, b, zm in pieces))
subprocess.run(cmd, check=True)
