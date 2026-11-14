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

## Balade automatique (version 9, modifiée en v20)
- À l'ouverture : reprise de la balade en cours (`wouaf-encours`, gardée toutes les 15 s et à la mise en arrière-plan, valable 4 h),
  sinon **écran d'accueil** (v20, choix de l'utilisateur : plus de démarrage automatique) avec le gros bouton
  « ▶️ C'est parti avec Roxy » (balade libre) et « 🗺️ Proposer des parcours ».
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
  (Workers Builds, dossier racine `worker`, Worker « wouaf-notifs » sur wouaf-notifs.6fgbcr2vtp.workers.dev (l’ancien « wouaf-rappels » est un Hello World inutile) ; KV `WOUAF`
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

## Accueil et Clebsous (version 20, décidé le 14/11)
- Accueil (`renderHome`, `#home`) sous les boutons : tirelire, série, niveau, `motivLines()` (à gagner aujourd'hui / déjà
  sortie, série, coffre chaud, défi), ligne « 👀 » des autres. La carte est cachée sauf en balade, en choix de parcours,
  sur un récap ou après « Proposer des parcours » (classe `hasmap`, retirée à la fin d'une balade).
- 🪙 **Clebsous** : monnaie affichée aux promeneurs, 100 clebsous = 1 € (`fmtCs`), partout dans l'app et les rappels (y compris
  malus et coffre = 500 clebsous). Les données restent en euros, mais **l'équivalent en € est secret** (choix de l'utilisateur : les promeneurs le découvriront après le 1er mois) : aucun « € » à l'écran, récaps et bilans compris (le superviseur divise par 100).

## Monnaie unique (version 21, décidé le 14/11, budget « 1 » ≈ 13 €/mois pour 25 min/jour)
- Plus de « points » pour les promeneurs : tout rapporte des clebsous, versés dans la tirelire (`addMoney`, plafond secret 15 €
  sur `game.money`) à la fin d'une balade ≥ 15 min : durée (`walkEuros`, `res.dur`) + bonus du jeu (`res.total` : objets
  🦴1 🎾2 🍖3 ⭐5 ×2 sur rue neuve, +1 par rue neuve, × durée longue, 🏠 +2, 🔥 +1, 🎯 défi +10). Moins de 15 min : rien.
- `game.total` = clebsous gagnés depuis le début (durée + bonus) → niveaux 0/600/2 000/5 000/10 000 et accessoires
  400/1 200/2 400/5 000/10 000. Tirelire affichée (`moneyOf`) = gains − malus (≥ 0) + coffres du mois.
- Accueil : phrase « tout se transforme en clebsous… à la fin du mois, de vrais sous ». Récap : « 🪙 +136 clebsous » avec le détail.

## Rues neuves = pas faites depuis 15 jours (version 22, décidé le 14/11)
- `game.seen[c]` = numéro du jour (`dayNum`) de la dernière visite (anciennes valeurs 1 converties en « aujourd'hui »).
  `isNewCell` = jamais vue ou vue il y a ≥ `FRESH_DAYS` (15) jours : vaut pour +1 par rue, objets ×2, coffres, tri des parcours.
  Au plus `MAX_NEW_CELLS` (10) rues neuves comptées par balade. Le brouillard compte toutes les cases déjà vues (à vie).

## Accueil v23 (décidé le 14/11)
- Ordre : en-tête Roxy (avec accessoires) « Salut X 👋 », durée, gros bouton « ▶️ C'est parti · 45 min · jusqu'à 85 clebsous + les
  bonus » (`updateGo` ; la balade libre garde `p.min` = durée choisie comme objectif affiché), « 🗺️ Proposer des parcours » ;
  les envies (filtres) n'apparaissent qu'avec la carte (`body.hasmap`).
- Trois tuiles (Tirelire / Série / Roxy) qui ouvrent `sheetMoney` / `sheetStreak` (14 derniers jours) / `sheetRoxy` ;
  missions du jour (`missions()`), puis les autres et la phrase sur les clebsous. Toucher Roxy en haut : saut + « Wouaf ! » puis `sheetRoxy`.
- Logo des Clebsous (v24) : pièce dorée SVG avec un C barré de deux traits (`CSI_SVG`) ; tout « 🪙 » affiché dans la page est
  remplacé automatiquement (`coinify` + MutationObserver). Les notifications et les messages envoyés gardent l'emoji 🪙.
  Gros gain sur le bouton « C'est parti » (`#goGain`).
- Bonus visibles (v25) : `bonusEst(min)` = estimation haute des bonus (objets ×2, trésor, rues neuves, durée longue, retour, défi),
  `gainEst` = durée + bonus. Pas de bonus « retour au départ » (retiré le 14/11 : on revient toujours à la maison). Bouton « jusqu'à N clebsous (X pour la durée + ~Y de bonus) », astuce « 💡 En 45 min : jusqu'à … soit
  N fois plus » (passe à cette durée), et « 🎁 Les bonus ? » (`sheetBonus`, tableau de ce que rapporte chaque bonus).

## Version 26 (décidé le 14/11)
- 💧 💩 Boutons « Pipi / Caca » pendant la balade (`gw.needs`, `needsUI`) → `r.pp` / `r.cc` dans le récap (« · 💧 · 💩 ») et
  sur la page du superviseur. Plus de note « fin loin du départ » (le retour ne compte plus).
- 👋 Tutoriel 3 écrans au premier lancement (`showTuto`, clé `wouaf-tuto`), revoir depuis « 🎁 Les bonus ? ».
- 💶 Jour de paie : 1re ouverture d'un nouveau mois (`offerPayday`, `game.payShown`) : total du mois précédent en clebsous et
  **révélation 100 clebsous = 1 €** (choix de l'utilisateur : secret jusqu'à la 1re paie), envoi « 💶 Paie de … = X € ».
  Onglet Tirelire : mois précédents, « Payé ✓ » avec le code superviseur (`POST /check` du Worker, `game.paid`).
- 📸 « Montre-moi Roxy ! » une fois par balade (`maybeAskPhoto`, entre 6 min et la moitié de la durée) : photo dans les 5 min = +5.
- 🌧️ Bonus courage : il pleut au 1er point GPS → bonus du jeu ×1,5 (`res.rainMult`).
