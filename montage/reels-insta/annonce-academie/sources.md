# Annonce · Académie Dogs & Us (3 versions)

Rushs (4K vertical, HEVC, 30 i/s) : `IMG_5295.mov` (les hooks), `IMG_5296.mov` et `IMG_5297.mov` (le corps, plusieurs prises
par phrase), `IMG_5299.jpg` (capture d'un message reçu, posée au-dessus de la tête dans la V1 : non versionnée ici).

| Version | Hook | Durée |
|---|---|---|
| V1 | « Ça fait des mois que je reçois ce genre de message. » + la bulle du message (notification, badge 99+) | 72,7 s |
| V2 | « J'ai une grande annonce à vous faire. » | 72,5 s |
| V3 | « Je vais peut-être perdre des abonnés… personne ne t'explique exactement comment. » | 80,1 s |

Chaîne :
1. Les trois rushs convertis en 1080×1920 puis joints (`raw-offsets.json` : 5295 → 0, 5296 → 42,333, 5297 → 169,367).
2. `derush_plan.py vN PROJET` : phrases choisies (meilleure prise), pauses coupées sur la voix, débuts de phrase calés sur
   l'attaque réelle de la voix → `assets/derush/raw.segments.json` + `raw.captions.json`, puis `kit/stage_lowmem.py`.
3. Vérification : re-transcription WhisperX de la coupe comparée au texte attendu (99,6 % / 99,2 % / 98,7 %).
4. `make_storyboard.py vN PROJET` → `storyboard.json` (layout F, sous-titres pop Archivo, étiquettes noires/blanches/rouges
   posées sur le mot, zooms alternés + punch-ins) et `sfx-events.json`.
5. reel-kit `build-reel.py` patché (`kit/build-reel-annonce.patch` : zoom visage, carte « notification », pulse) →
   HyperFrames 0.8.42 `render --sdr`.
6. `kit/synth_sfx.py` (pop, ding, whoosh, boom, riser synthétisés) + tick/swish des leçons, mixés par `kit/mix_sfx_reel.py`.
7. Encodage web : libx264 slow crf 20, maxrate 8M, faststart.
