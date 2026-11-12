# Story time · Nala et l'os (3 versions)

Rush : `IMG_5376.mov` (4K vertical, HEVC, 30 i/s, 4 min 53) — l'histoire racontée en remplissant le tapis de fouille de
Nala, puis deux hooks enregistrés à la fin.

| Version | Hook | Durée |
|---|---|---|
| V1 | « Il faut que je vous raconte la fois où Nala m'a fait attendre 45 minutes… Oui, c'est de toi qu'on parle. » | 2 min 41 |
| V2 | « Story time du jour où Nala a mangé un os qui avait la taille d'une hanche… 45 minutes. » | 2 min 38 |
| V3 | « Est-ce que tu leur racontes le jour où tu m'as fait galérer pendant 45 minutes… ? Dis-nous. » (à Nala) | 2 min 40 |

Chaîne :
1. `kit/zoomcut_v.py IMG_5376.mov nala-1080z.mp4 $(cat zooms.txt)` : 1080×1920 avec les zooms sur Nala tirés de la 4K
   (« Nala m'a fait attendre », « c'est de toi qu'on parle », les hautes herbes, « toute fière », « elle m'évite »,
   le hook V2 « Nala a mangé un os », le hook V3 où elle parle à Nala).
2. `derush_plan.py vN PROJET` : hook + même corps, ratés et répétitions retirés, l'aparté « elle le chiquait » remis avant
   la fin ; les plages contiguës ne se chevauchent plus (sinon un bout de son serait joué deux fois).
3. `kit/stage_lowmem.py`, puis vérification par re-transcription (≈ 95 % ; les écarts restants sont des variantes du
   transcripteur : voix gaga non transcrite, « l'écart » → « l'escarre », « Dis-nous » → « des noms »).
4. `make_storyboard.py vN PROJET` : même style que l'annonce V3 (sous-titres pop Archivo, mots clés en rouge, étiquettes
   noires/blanches/rouges sur le mot), zooms alternés + punch-ins, whoosh sur chaque zoom sur Nala, question de fin
   « Et toi, ton chien t'a déjà fait ça ? » sur l'image figée 1,6 s.
5. reel-kit `build-reel.py` patché (`kit/build-reel-annonce.patch`) → HyperFrames 0.8.42, SFX `kit/mix_sfx_reel.py`,
   encodage web libx264 crf 20.
