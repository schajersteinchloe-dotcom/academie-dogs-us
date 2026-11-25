# Formation Marche en laisse · Vidéo d'introduction

Drive « Formation Academie D&U » (téléchargé par lien de partage : le connecteur Drive plafonne à 10 Mo) :
- `videointro.mov` — face cam, 3374×2158, 8 min 48 → recadré 2900×1632 depuis (8, 0) puis 1920×1080 (elle à droite
  du centre, la colonne de titres libre à gauche)
- inserts, posés sur sa voix (lesson.json `broll`) :
  - début, « Est-ce que tes balades ressemblent à ça ? » → `IMG_5056.MOV` puis `IMG_5055.MOV` (AVANT)
  - milieu, « voilà où on était à la première séance » → `cessionalapress(1).mp4` (1RE SÉANCE) ;
    « voilà où on en est aujourd'hui… même chien, mêmes rues » → `IMG_5330.MOV` (AUJOURD'HUI) ;
    module 1 « à la maison… le harnais, la laisse, les sorties » → `cessionalapress(1).mp4` + `marcheenlaisseintérieur.mp4`
  - fin, « Imagine, dans quelques semaines… Arlo en est la preuve » → `IMG_5331.MOV`, `IMG_5330.MOV` (APRÈS)
- Script : Notion, Formation Marche en Laisse → « Vidéo d'introduction — Transforme tes balades ».

Chaîne :
1. `kit/transcribe_fw.py` (faster-whisper large-v3-turbo, CPU) → `videointro.json`
2. `derush_plan.py` (plages lues sur le script, reprises retirées, attaques calées sur la voix) → `kit/stage_lowmem.py`
3. Vérification : re-transcription de la coupe (98,5 %, écarts = variantes du transcripteur) ; « la bonne méthode »
   dit deux fois coupé ensuite et revérifié à l'écoute.
4. `kit/build-lesson.py lesson.json` (colonne de titres et cartes, sous-titres, inserts en fondu, zoom aux coupes de
   reprise) → HyperFrames 0.8.42 `render --sdr` → `kit/mix_sfx_reel.py` (tick, swish, whoosh) → encodage web.
