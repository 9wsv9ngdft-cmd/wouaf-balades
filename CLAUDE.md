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

## Motivation (version 17)
- 🎯 Défi du jour (`DEFIS`, `defiOf` : même défi pour tous, change chaque jour) : +15 pts une fois par jour (`game.defiDone`), balade ≥ 15 min.
- `motivLines()` : série en danger (série ≥ 2 et dernière balade hier), 🔥 coffre chaud (`chestFrom()` passé), défi ; dans la bannière
  de départ et en haut de l'onglet Progrès.
- 🌤️ Créneau météo au 1er point GPS (`weatherTip`, Open-Meteo minutely_15).
- 📸 Album photo : base IndexedDB `wouaf-photos` (photos réduites ~800 px, 60 max), galerie dans Progrès.
- 🏅 Récap de la semaine (lundi–dimanche) à la 1re ouverture d'une nouvelle semaine (`game.weekSeen`, record `game.bestWeek`).

## Rappels (notifications)
- Programme Cloudflare : `worker/wouaf-rappels.js` + `worker/wrangler.jsonc`, déployé automatiquement depuis GitHub
  (Workers Builds, dossier racine `worker`, Worker « wouaf-rappels » sur wouaf-rappels.6fgbcr2vtp.workers.dev ; KV `WOUAF`
  créée toute seule, Cron `*/15 * * * *`). Un push dans `worker/` met le programme à jour. Clés VAPID créées par le Worker (KV `vapid`), `GET /key`,
  `POST /register | /state | /test | /unregister` ; abonnés `u:<id>`, envois déjà faits `s:<id>`. Heure de Paris.
- App : `PUSH_API` (URL du Worker ; vide = carte des rappels cachée), `sw.js` (push + clic seulement, pas de cache),
  clé `wouaf-rappels` (id, on, horaires matin/soir par jour, index = getDay()). Il faut l'app sur l'écran d'accueil (iOS 16.4+).
- **Jamais de position envoyée** : seulement prénom, horaires, série, coffre chaud, défis des 8 jours, résumé de la semaine.
- Messages : pas de rappel si déjà sortie aujourd'hui ; soir = série en danger en priorité ; dimanche soir = résumé de la semaine.

## Malus (version 18, décidé le 14/11)
- À partir du lundi 16/11/2026 (et pas avant le 1er jour d'utilisation du téléphone) : jour sans balade ≥ 15 min avec l'app
  = −0,20 € (2 jokers/mois, appliqués dans l'ordre) ; dès la 3e balade < 15 min de la semaine −0,10 € chacune ; semaine
  (lun–dim) avec moins de 4 jours de balade (moins les jours de pause) −0,50 €. Malus même si un autre promeneur est sorti.
- `game.malus` (liste), `game.malusEur["AAAA-MM"]` ; tirelire affichée = `moneyOf(k)` = gains − malus, jamais < 0.
  Calcul à l'ouverture (`processMalus`, rattrape les jours passés), annonce dans une fenêtre ; détail dans l'onglet Tirelire,
  le récap de la semaine, le bilan de quinzaine et le récap (« ⏱️ trop courte −0,10 € »).
- Rappels et bannières : formulation positive (« À gagner : 15 min 0,16 € · 25 min 0,35 € · 45 min 0,85 € · 1 h 1,30 € »),
  jamais de « −0,20 € » ; le négatif seulement dans Tirelire / récaps.
- 🏖️ Pause du superviseur : lien discret « Superviseur » en bas de Progrès (si `PUSH_API`), code = variable secrète `SUPERVISOR_CODE` du
  Worker (pas dans le fichier : le dépôt est public), `GET/POST /pause`, KV `pauses`. Pendant une pause : pas de malus,
  pas de rappels, série conservée (`streakAlive`) ; pause ajoutée après coup = malus remboursés (sauf semaine faible).
