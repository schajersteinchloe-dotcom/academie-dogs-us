# Exercice · Le rappel : les sources

Trois rushs 4K/60 de la Médiathèque PlugKit, raccrochés en une seule ligne de temps (`raw-offsets.json`) :

| Rush | Durée | Préparation |
|---|---|---|
| `rappel1.MOV` | 93,2 s | 1080p/30, plan entier |
| `rappel2.MOV` | 144,3 s | `kit/zoomcut.py` : x2 sur 11–24,5 s et 127–138 s, x1,6 sur 28,5–37 s, x1,5 sur 58,5–100 s et 103–116 s |
| `rappel3.MOV` | 157,2 s | `kit/zoomcut.py` : x1,4 sur 35,5–42 s, x1,3 sur 48–67 s |

Les zooms sont pris dans les pixels 4K : sur les démos filmées de loin, Woody et Chloé restent nets.
Puis `derush_plan.py` (6 blocs, dans l'ordre de la leçon), `stage_lowmem.py`, `build-lesson.py`, `mix-sfx.py`.
