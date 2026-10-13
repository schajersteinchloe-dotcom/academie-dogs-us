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

## Couleurs

- Noir `#111111` (étiquettes), blanc `#FFFFFF` (cartes et sous-titres), rouge alerte proche de `#E53935`.
- Valeurs exactes, police, tailles et marges : à relever sur une image en pleine résolution de la référence.

## Méthode (reel-kit + WhisperX)

1. Récupérer le rush depuis la bibliothèque PlugKit (`list_media`), le copier, ne jamais le modifier.
2. Transcrire avec WhisperX (`scripts/takes.py`), proposer la liste des prises gardées et coupées, et faire valider.
3. Proposer le **plan de la leçon** : un tableau avec chapitre, cartes et mot déclencheur, et faire valider.
4. Brouillon en 16:9, puis retours, puis rendu final en 1920×1080.

Réglages réseau nécessaires pour la session cloud : `api.plugkit.co` (vidéos PlugKit), `huggingface.co`,
`*.huggingface.co`, `*.hf.co` (modèle Whisper), `download.pytorch.org` (alignement des mots en français).
