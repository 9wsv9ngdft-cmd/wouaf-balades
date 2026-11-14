# Wouaf Balades

Web app (un seul `index.html`) publiée sur GitHub Pages : https://9wsv9ngdft-cmd.github.io/wouaf-balades/

## Mise à jour automatique des téléphones
- `index.html` contient `const APP_VERSION = "…"`. L'app relit sa page sur le serveur et se recharge si ce numéro a changé
  (à l'ouverture / au retour dans l'app ; sinon bandeau « Mettre à jour » ; jamais pendant une balade).
- **Le numéro doit changer à chaque mise en ligne.** Le hook `.githooks/pre-commit` le fait tout seul :
  dans un nouveau clone, lancer une fois `git config core.hooksPath .githooks`.

## Numéro de version et nouveautés
- `APP_NUM` (entier, affiché en bas de l'app) et `NEWS[APP_NUM]` (2–3 lignes) : à augmenter / remplir à chaque nouveauté
  visible par les promeneurs. La fenêtre « Nouveau dans la version N » s'affiche une fois par téléphone (clé `wouaf-vu`).

## Balade automatique (version 9)
- À l'ouverture : reprise de la balade en cours (`wouaf-encours`, gardée toutes les 15 s et à la mise en arrière-plan, valable 4 h),
  sinon balade libre lancée toute seule, sauf sur un lien de récap ou moins d'1 h après une balade terminée (`wouaf-fin`).
- Fin automatique : à < 40 m du départ (1er point GPS précis), après 5 min, 200 m d'éloignement et 60 % du parcours choisi ;
  compte à rebours de 30 s avec « Je continue ».

## Jeu « Points Roxy » (version 10)
- Clé `wouaf-jeu` : `pts` (disponibles), `total` (gagnés, pour les niveaux), `streak`, `claims`, `seen` (cases ~100 m déjà visitées).
- Objets : 🦴1 🎾2 🍖3 ⭐5 ; parcours choisi → semés tous les 350–450 m sur le tracé, ramassés à < 25 m ; balade libre → trouvés tous les 350–450 m,
  ⭐ à 400 m du départ. Objet dans une case jamais visitée ×2 ; +1 par case neuve. Ignoré au-delà de 15 km/h ou précision > 35 m.
- Points = score de jeu seulement (niveaux, coins). Fin (≥ 15 min, sinon rien) : (objets + cases) × durée (1 / 1,25 dès 40 min /
  1,5 dès 55 / 2 dès 85) + 2 retour au départ + 1 série ≥ 3 jours.
- **Argent (v14, décidé le 14/11)** : pas de boutique (glace, écran, ciné… retirés), seulement une tirelire. Chaque balade de
  ≥ 15 min rapporte `walkEuros(min) = 0,35 € × (min/25)^1,5` (15 min 0,16 · 25 min 0,35 · 30 min 0,46 · 45 min 0,85 · 1 h 1,30),
  donc 2 × 15 min < 1 × 30 min (voulu par l'utilisateur : ne pas additionner les petites balades). Toute balade compte (pas
  besoin de revenir au départ). Durée retenue = min(durée, distance marchée / 30 m/min). Plafond 15 €/mois calendaire
  (`game.money["AAAA-MM"]`), **jamais affiché aux promeneurs** (v16 : sinon ils arrêteraient de sortir le chien une fois atteint). Objectif ≈ 10 €/mois pour 25 min par jour. Récap : « 💶 +0,46 € ».
- Bilan de quinzaine (1er–15, 16–fin) proposé au 1er/16 (`game.bilanSeen`) et bouton dans l'onglet 💶 Tirelire ; le bilan
  de fin de mois ajoute le total de la tirelire.
- Propositions : rang bonus pour les lieux en cases neuves, tri final par `newPct` (« 🆕 x % de nouveau »).

## Progrès (version 15, décidé le 14/11)
- 💰 Coffre : 5 € **en plus** du plafond (`game.bonus["AAAA-MM"]`, `game.chests`), seulement en entrant dans une case jamais
  visitée après 5 min de balade ; aucune chance pendant 10 jours après le dernier (1er coffre possible après 5 jours d'usage),
  puis 5 % par case neuve +1,5 %/jour (max 20 %). Écran plein « COFFRE TROUVÉ ! », récap « 💰 coffre +5 € ».
- Saisons de 2 mois (v16 : jan–fév, mars–avr, mai–juin, juil–août, sept–oct, nov–déc ; clé « AAAA-bN ») : album 🦴80 🎾45
  🍖30 ⭐25 (au prorata si la saison a commencé en cours, au moins un quart),
  complet = 🎁 récompense à choisir avec le superviseur (`game.season`, `game.pastSeasons`).
- Niveaux allongés : 0 / 300 / 1 000 / 2 500 / 5 000 pts ; passage de niveau = 🎁 (`game.levelSeen`).
- Trophées permanents (`TROPHIES`, `game.trophies`, `game.stats` : walks, km, early < 8 h, rain via Open-Meteo au 1er point,
  long ≥ 60 min, bestStreak) ; certains avec 🎁.
- Carte du brouillard : cases vues dans 2 km autour de la maison (`game.home` = 1er départ), paliers 25/50/75 % (trophées).
- Accessoires de Roxy (v16) : le chien 🐕 est toujours affiché, les accessoires s'ajoutent dessus (`game.acc` = liste ; 🎀 oreille,
  🧣 cou, 🕶️ museau, 🎩/👑 tête, un seul couvre-chef) ; débloqués à 200/600/1 200/2 500/5 000 pts.
- « Où en sont les autres » : `r.g` (snapshot) dans le lien du récap ; un autre promeneur qui ouvre le lien le garde
  (`wouaf-autres`). Pas de classement (choix de l'utilisateur).
- Récompenses réelles 🎁 : texte générique « à choisir avec le superviseur » (l'utilisateur précisera plus tard).

## Méthode de travail
- On discute d'abord avec l'utilisateur, puis une seule série de modifications une fois validé. Toujours au plus simple.
