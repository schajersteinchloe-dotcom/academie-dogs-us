#!/usr/bin/env python3
"""qa.py — what is heard in each rendered clip (WhisperX on the clip, padded) against the words the clip should hold."""
import json, difflib, re, glob, sys
def norm(s): return re.sub(r"[^\w'%]", "", s.lower().replace("’", "'"))
for f in sorted(glob.glob("out/*.words.json")):
    name = f.split("/")[-1][:-11]
    exp = json.load(open(f))
    got = json.load(open(f"qa/audio/pad-{name}.json"))["words"]
    a = [norm(w["text"]) for w in exp]; b = [norm(w["text"]) for w in got]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    print(f"== {name}  match {sm.ratio()*100:.0f}%")
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            t = exp[i1]["start"] if i1 < len(exp) else exp[-1]["end"]
            print(f"   {op:7s} @{t:5.1f}s  expected [{' '.join(a[i1:i2])}]  heard [{' '.join(b[j1:j2])}]")
