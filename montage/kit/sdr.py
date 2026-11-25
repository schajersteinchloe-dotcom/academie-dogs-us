"""sdr.py — the video filter and colour tags that bring any rush to SDR BT.709, limited range (what the players expect).

sdr_vf(path): HLG / PQ (iPhone HDR) → tone-mapped to BT.709; full-range (yuvj) → limited range; else just yuv420p.
SDR_TAGS: the colour tags to write on the encode.
"""
import subprocess


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=pix_fmt,color_transfer,color_range", "-of", "default=nw=1", str(path)],
                       capture_output=True, text=True)
    return dict(l.split("=", 1) for l in r.stdout.split() if "=" in l)


def sdr_vf(path):
    p = _probe(path)
    if p.get("color_transfer") in ("arib-std-b67", "smpte2084"):
        return ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
                "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    if p.get("pix_fmt", "").startswith("yuvj") or p.get("color_range") == "pc":
        return "scale=in_range=full:out_range=tv,format=yuv420p"
    return "format=yuv420p"


SDR_TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
