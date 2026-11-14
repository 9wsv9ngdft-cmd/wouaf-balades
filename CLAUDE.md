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
- Fin (≥ 5 min) : (objets + cases) × durée (1 / 1,25 dès 40 min / 1,5 dès 55 / 2 dès 85) + 2 retour au départ + 1 série ≥ 3 jours.
- Équilibre (v11, 14/11) : ~1 balade par jour et par ado ≈ 600–700 pts/mois (45 min ≈ 20–25 pts une fois le quartier exploré).
- Récompenses réelles : tableau `REWARDS` dans index.html (à modifier sur demande de l'utilisateur) : écran 50, glace 60, repas 120,
  5 € (`euros:5`, prix variable), ciné 300.
- Euros (v12) : objectif 1 balade/jour ≈ 10 €/mois, plus si plus de balades, 15 € max par mois calendaire (`EURO_MAX`).
  Prix des 5 € = 15 × points moyens par balade (≥ 5 min) sur les 15 jours précédents, recalculé le 1er et le 16
  (`game.euro`, défaut 330, borné 100–600). Rythme du mois et bilan de quinzaine (proposé au 1er/16, `game.bilanSeen`). Réclamer = points retirés
  + message au superviseur via le menu Partager.
- Propositions : rang bonus pour les lieux en cases neuves, tri final par `newPct` (« 🆕 x % de nouveau »).

## Méthode de travail
- On discute d'abord avec l'utilisateur, puis une seule série de modifications une fois validé. Toujours au plus simple.
