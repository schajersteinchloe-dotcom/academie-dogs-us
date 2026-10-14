# Charte de montage — vidéos de leçon Dogs & Us

Toutes les leçons se montent comme la vidéo de référence ci-dessous. Même format, même habillage, mêmes sous-titres.

**Référence** : `videoequipementchiot.mp4` — « Leçon 2 · L'équipement de ton chiot »
(bibliothèque PlugKit, media id `cmv5frp4o1wganz01akw9yo7r`). Planches : `reference/lecon2-ouverture.jpg`
(les 3 premières secondes, une image toutes les 0,4 s) et `reference/lecon2-planche.jpg` (12 images sur toute la vidéo).

## Format

- **16:9 horizontal, 1920×1080.** Ce n'est pas un reel vertical. La référence dure 3 min 30.
- Face caméra, plein cadre, plan fixe, canapé clair en fond. Pas de recadrage ni de zoom.
- Peu de coupes : 5 plans en 3 min 30 (environ 18 s par plan). On enlève les silences, les ratés et les reprises, sans transition ni effet.
- Pas de musique, pas de B-roll vidéo.

## Habillage : la colonne en haut à gauche

Un empilement aligné à gauche, dans le coin haut gauche (marge d'environ 80 px à gauche et 55 px en haut, à mesurer en pleine résolution).

1. **Étiquette de chapitre** : rectangle noir, texte blanc, gras, en MAJUSCULES.
   - Ouverture : `LEÇON 2` (le numéro de la leçon), qui apparaît vers 0,4 s.
   - Puis une étiquette par partie, numérotée avec un point médian : `1 · NOURRITURE`, `3 · BALADE`, `4 · JOUETS`,
     `5 · MASTICATION`, `6 · HYGIÈNE & SOINS`. Elle remplace la précédente au moment où la partie commence.
2. **Cartes de notes** sous l'étiquette : petits rectangles blancs, texte noir, petit et demi-gras.
   - Elles s'ajoutent **une par une, au mot où elle en parle**, et restent affichées. La pile se vide quand le chapitre change.
   - Un style de prise de notes, court : `2 gamelles : inox ou céramique`, `Tapis de fouille / anti-glouton`,
     `Longe de 5 à 10 m`, `Harnais en Y (si assez grand)`, `Sinon : le collier au début`.
   - **Carte d'alerte** : fond rouge, texte blanc, préfixe `×` : `× Éviter le plastique`, `× 500 € de trucs inutiles`.
   - **Carte de précision** : préfixe `→` : `→ seulement pour jouer à deux`.
   - Ouverture : sous `LEÇON 2`, une carte blanche avec le titre de la leçon (`L'équipement de ton chiot`), puis une
     carte rouge qui annonce l'enjeu (`× 500 € de trucs inutiles`).

## Sous-titres

- En bas au centre, sur une ligne, en blanc, police sans-serif grasse, sans fond, sans mot coloré.
- Ils apparaissent **mot à mot**. Un groupe compte 3 à 6 mots, puis le groupe suivant repart d'une ligne vide.
- Orthographe exacte des noms (Kong, etc.).

## Visuels ponctuels

- Quand elle cite ou montre des objets, des **photos d'objets détourées** (sans fond) apparaissent à gauche,
  à côté d'elle. Exemple à 167 s : des bâtons et bois à mâcher pendant « comme ceci, ceci, ceci ».
- Seulement des vrais produits, jamais d'image inventée.

## Effets sonores

Relevés sur la Leçon 2 (voix séparée du reste avec Demucs, puis chaque son cherché dans toute la piste) :

- **Double « tic »** (`kit/sfx/tick.wav`) : deux clics brefs et aigus, le second 111 ms après le premier et 1,5 dB plus
  doux. Un sur **chaque carte** d'une partie numérotée, au moment où elle apparaît. Jamais sur les cartes d'ouverture
  (titre, enjeu), jamais sur les étiquettes.
- **Swish** (`kit/sfx/swish.wav`) : un souffle court (environ 150 ms). Un juste avant la première étiquette, puis à
  chaque changement de partie, quand l'ancienne colonne vient de partir.
- Pas de musique. Volume des effets : celui de la référence, calé sur la voix (`mix-sfx.py` mesure la voix et ajuste).

`build-lesson.py` écrit `assets/sfx-events.json`. Après le rendu, `python3 scripts/mix-sfx.py renders/<leçon>.mp4`
pose les effets sous la voix (copier `kit/sfx/*.wav` dans `assets/sfx/`). La vidéo n'est pas réencodée.

## Mesures exactes (relevées en pleine résolution, 1920×1080)

| Élément | Valeur |
|---|---|
| Police | **Archivo** partout (fichiers dans `kit/fonts/`) |
| Étiquette de chapitre | x 70, y 52, hauteur 75, rayon 12, fond `#0E0C0D`, Archivo 800, 47 px, majuscules, interlettrage +0,02 em |
| Cartes | x 70, première à y 140, une tous les 78 px, hauteur 59, rayon 10, Archivo 700, 37 px, interlettrage −0,02 em |
| Carte blanche | fond `#FFFFFF`, texte `#0E0C0D` |
| Carte d'alerte | fond `#E8462A`, texte blanc, symbole `×` |
| Ombre | `0 6px 18px rgba(0,0,0,.16)` |
| Sous-titres | Archivo 700, 57 px, blanc, ombre douce, une ligne centrée, haut du texte vers y 937 ; 6 mots / 36 caractères au plus |
| Animations | entrée : fondu et montée de 10 px en 0,2 s ; changement de partie : la colonne part vers le haut, floutée, 0,4 s avant la nouvelle étiquette |

Ces valeurs sont codées dans `kit/build-lesson.py` : un rendu de contrôle posé sur une image de la Leçon 2 la recouvre exactement.

## Méthode (reel-kit + WhisperX, dans une session cloud)

1. Réseau de l'environnement : **Full** (ou au minimum `api.plugkit.co`, `huggingface.co`, `*.huggingface.co`, `*.hf.co`,
   `download.pytorch.org`). Installation : `montage/setup-cloud.sh` (reel-kit, HyperFrames, WhisperX, Silero, NLTK).
2. Récupérer le rush dans la bibliothèque PlugKit (`list_media`, puis `curl` sur son `url`). Ne jamais le modifier.
3. Un rush iPhone 4K/60 se convertit d'abord en 1080p/30 (`ffmpeg … -vf scale=1920:1080 -r 30 -c:v libx264 -crf 18`).
   La transcription peut démarrer en parallèle sur un proxy « image noire + son d'origine » : mêmes minutages.
4. `python3 scripts/takes.py <rush>` liste les prises. **Relire chaque prise en entier** : le détecteur laisse passer
   des reprises (phrase redite, « Non… », « Ok super… »). Écrire la découpe dans un `derush_plan.py` (voir
   `lecons/lecon-1-besoins-du-chiot/`) : prises gardées, mots de début et de fin, coupe des pauses sur l'énergie de la voix.
5. Assembler avec `kit/stage_lowmem.py` (même résultat que `stage.py`, sans manquer de mémoire sur un long rush).
6. **Contrôle** : retranscrire `assets/reel-audio.wav` et comparer au texte voulu. Les écarts réels (fin de phrase coupée,
   faux départ resté) viennent d'un mot mal placé par WhisperX : retranscrire le passage seul et corriger ses minutages.
7. Copier `kit/build-lesson.py` dans `scripts/` et `kit/fonts/*` dans `assets/fonts/`, écrire `lesson.json`, puis
   `python3 scripts/build-lesson.py`, contrôler des images (`npx hyperframes@0.8.42 snapshot --at …`) et rendre avec
   `npx hyperframes@0.8.42 render --sdr`. `HYPERFRAMES_BROWSER_PATH` doit pointer sur le Chrome du conteneur, et
   `PRODUCER_STREAMING_ENCODE_MAX_DURATION_SECONDS=1200` fait encoder au fil de la capture : sans lui, une leçon de
   6 minutes demande environ 86 Go d'images temporaires et le rendu s'arrête faute de disque.
8. Effets sonores : `python3 scripts/mix-sfx.py renders/<leçon>.mp4` (voir « Effets sonores »).
9. Déposer le rendu dans la Médiathèque PlugKit (`create_media_upload` puis `curl -T`).

## Le plan d'une leçon

- **Ouverture** : `Leçon N`, la carte titre (« Les besoins de ton chiot »), puis 1 ou 2 cartes qui posent l'enjeu.
- **Une partie par point annoncé**, `N · NOM` en un ou deux mots (`1 · Sommeil`, `4 · Propreté`).
- **Cartes** : 3 à 7 par partie, 30 caractères environ, en style prise de notes, chacune sur le mot où elle en parle.
  Les « à ne pas faire » en rouge (`alert`), les conséquences et conseils en `→` (`arrow`).
- **Récap** quand elle énumère les points à la fin (« Les 5 piliers »), puis rien pendant le mot de la fin.
