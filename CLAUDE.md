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

## Version 27 (décidé le 14/11)
- 🌙 Mode poche (`pocketOn/Off`, `#pocket`) : écran noir, GPS et balade continuent ; double toucher pour revenir ; se ferme au coffre,
  au trésor, au retour maison et à la fin.
- 📊 Tableau de bord superviseur : après chaque balade, l'app envoie **seulement des chiffres** (`queueWalk` → `POST /walk`, file
  `wouaf-envois` réessayée à l'ouverture) ; le Worker garde `d:<prénom>` (60 dernières balades + résumé) et `last` (dernière sortie
  de Roxy). Superviseur › code › « 📊 Tableau de bord » (`POST /dash`). Pas de notification « Roxy est sortie » (refusé : WhatsApp suffit).
- 🎉 Jours bonus ×2 (`POST /boost`, KV `boosts`, dans la même fenêtre Superviseur que les pauses) : bonus du jeu ×2 (`res.boostMult`),
  mission et rappel du matin.
- 🥺 Humeur de Roxy (`mood()`) selon les heures depuis sa dernière vraie balade, tous promeneurs (`last` reçu avec `/pause`).
- 🏴‍☠️ Trésor de la semaine (`weekHunt`, `game.hunt`) : même endroit pour toute la maison (tiré avec la semaine), à 0,9–1,8 km de la
  maison, recalé sur le lieu le plus proche (Photon) ; zone de 200 m sur la carte ; +50 au premier (`POST /treasure`), +20 ensuite.
- 📡 Radar (`radar()`) : objet ou trésor à < 150 m (tiède / chaud / brûlant, `haptic(2)`) ; balade libre : prochain objet dans ~X m.
- 📱 « Mon mois avec Roxy » (`monthCard`) : image 1080×1350 (photo, balades, km, temps, clebsous, niveau) à partager, depuis la
  tuile Tirelire et le jour de paie.
- 📳 `haptic(n)` : `navigator.vibrate` sur Android ; sur iPhone (iOS 18+) astuce de l'interrupteur caché (`<input type=checkbox switch>`
  basculé via son label) = petit tic haptique, pas garanti hors geste de l'utilisateur. Appelé par `ding()` (objets, coffre…),
  radar « brûlant » et retour maison.

## Version 28 (décidé le 14/11)
- 💾 Sauvegarde (`backupNow`) : jeu + tirelire + carnet sans tracés → `POST /backup` (KV `b:<prénom>`), après chaque balade et
  toutes les 6 h. Restauration : Superviseur › code › « ♻️ Restaurer un promeneur » (`POST /restore`, remplace le téléphone).
- ✏️ Corrections : Superviseur › « ✏️ Corriger une tirelire » (prénom, ± clebsous, motif) → `POST /adjust` (KV `a:<prénom>`) ;
  le téléphone l'applique à l'ouverture (`applyAdjust`, `game.adj[mois]`, `game.adjDone`) avec une fenêtre « Message du superviseur ».
- 🎄 🎃 🐣 Événements (`seasonEvent`, `EVENT`) : décembre = Noël (🎁 ⛄ 🍪 🌟), 20/10–2/11 = Halloween (🍬 🦇 👻 🎃),
  Pâques ±7 j (🥚 🐣 🍫 🐰) ; mêmes valeurs et même album, déco dans le titre et mission.
- 👯 Balade à deux : bouton 👯 ; les deux touchent pendant la même balade (`POST /duo`, départs à < 45 min) → +15 chacun
  (`DUO_PTS`), vérifié aussi juste après la fin.
- 🎂 Anniversaire de Roxy : `ROXY_BDAY` (« MM-JJ », vide tant que l'utilisateur ne l'a pas donné) → bonus ×3, chapeau 🎉, mission.

## Version 29 : simplification et esthétique (décidé le 14/11)
- 2 onglets : 🏠 Accueil et 🏆 Progrès ; la tirelire détaillée et le carnet s'ouvrent depuis Progrès (`.subnav`, bouton
  « ← Retour aux progrès » `backBtn`). Les vues `shop` / `log` existent toujours.
- Barre de balade : 📷, Terminer, Pipi/Caca ; 🆘 👯 🌙 rangés dans « ⋯ » (`#moreBtn` ; les vrais boutons sont cachés `.hid`).
- Plus de bilan de quinzaine (remplacé par le tableau de bord et le jour de paie ; `sendBilan` reste dans le code, non appelé).
- En-tête sans sous-titre ; crédits repliés dans « À propos » (pied de page `<details>`).
- ✨ « Quoi de neuf » (`startupDigest`) : une seule fenêtre à cartes qui défilent (nouveautés, malus, message du superviseur,
  jour de paie, semaine) ; remplace `showNews` / `showMalus` / `applyAdjust` / `offerPayday` / `offerWeek` à l'ouverture.
- 🐕 Avatar : photo officielle `roxy.jpg` (envoyée par l'utilisateur le 14/11), remplaçable sur un téléphone depuis l'album (« En faire la photo de Roxy », `wouaf-avatar`) ;
  `roxyHTML` l'utilise partout (accueil, carte, fiches), accessoires par-dessus.
- 🎉 `confetti()` : coffre, trésor, paie, record, fin du tuto, niveau / album / trophée au récap.
- 🧾 Récap façon ticket (grosse somme de clebsous, photo de Roxy), « Le détail » en dessous.
- 🌙 Mode sombre automatique (`prefers-color-scheme: dark`, bloc CSS en fin de `<style>`).
- Icône = vraie tête de Roxy (photo du 14/11) dans un cercle + pièce de clebsous : icon-180/192/512.png (iOS garde l'ancienne icône tant que l'app n'est pas ré-ajoutée).
- 🐾 Dernières sorties (décidé le 14/11, option A : sans trajet) : toucher la ligne d'humeur sous « Salut X » ouvre `sheetOuts`
  (qui, quand, durée, km, 💧💩, tous promeneurs) via `GET /recent` du Worker (fusionné avec le carnet local). Jamais de trajet
  ni de position envoyés ; les trajets restent dans les liens de récap WhatsApp.
- Départ (v30, décidé le 14/11) : « ▶️ C'est parti » ouvre un choix « 🚶 Balade libre » (démarre aussitôt) / « 🗺️ Choisir un
  parcours » (`locate()` → propositions sur la carte, bouton « ▶️ On y va ») ; plus de bouton « Proposer des parcours » visible ;
  bandeau de départ = « 🐾 C'est parti ! » + missions, boutons « 👍 OK » / « ✕ Annuler ».
- 🌫️ Brouillard en direct pendant la balade (`drawWalkFog`, 3 km autour de la maison) : grisé = rues neuves (pas faites depuis
  15 jours = bonus), éclairci au passage ; le brouillard de Progrès reste « à vie ».

## Version 31 : règles d'argent finales (décidé le 14/11)
- **Sortie obligatoire : 1 balade ≥ 20 min par jour** (`MONEY_MIN = 20`). La durée ne paie qu'au-delà : `walkEuros(min) =
  0,35 × ((min/25)^1,5 − (20/25)^1,5)` → 20 min 0 · 30 min 21 · 45 min 60 · 1 h 105 · 1 h 30 214 clebsous. Les **bonus** du jeu
  (objets, rues neuves, défi, trésor, photo, duo…) comptent dès 20 min. Durées proposées : 20/30/45/60/90.
- Plafond doux secret : au-delà de 15 € (gains du mois), chaque gain ÷ 4 ; plafond final 20 € (`MONEY_SOFT`, `MONEY_MAX`, `addMoney`).
  Coffres hors plafond, **seulement si ≥ 4 jours de balade sur les 7 derniers** (`regular()`).
- Malus : jour sans balade ≥ 20 min −30 (1 joker/mois) ; semaine < 6 jours −50 ; 3e balade < 20 min de la semaine −10.
  🏆 Semaine parfaite (7/7, pauses déduites) : +30 (`PERFECT_WEEK`, `game.perfect`), annoncée dans le récap de la semaine.
- Estimation par ado et par mois : rechigne ≈ 0 € · minimum chaque jour ≈ 0–4 € (bonus seulement) · 30 min la plupart des jours
  ≈ 12–16 € · 45 min et plus chaque jour ≈ 20–30 € (coffres compris).
- 🌫️ Brouillard opaque (`fogPolygon`, calque `fog` sous les tracés, ≈ 50 km, opacité .93) pendant la balade (rues faites < 15 j
  visibles) et dans Progrès (toutes les rues déjà vues).
- Balade (v31, retours du 14/11) : carte plein écran au-dessus de la barre du bas (`--wbh` via ResizeObserver), en-tête et accueil
  cachés ; 1er point GPS → centré zoom 17 (`firstFix`) ; bouton 📍 « recentrer » quand on a déplacé la carte ; bandeau de départ
  court (« 🐾 C'est parti pour 45 min ! », disparaît après 8 s) ; météo dans la ligne sous le chrono (plus de pop-up).
- 🐕 Fiche Tamagotchi (v32, `sheetRoxy`, ouverte en touchant Roxy en haut ou la tuile Roxy) : écran avec Roxy animée selon son
  humeur (saute si contente, triste et grise si elle attend), barres ❤️ Bonheur (`mood()`), ⚡ Forme (minutes de la semaine / 3 h 30),
  niveau, 🗺️ Exploration ; cagnotte, série, clebsous pour le prochain niveau ; bouton « ▶️ Sortir Roxy ».

## Version 33 (décidé le 14/11) : accueil allégé, menu ☰, brouillard « lampe », tuto complet
- Fiches (`openSheet`) : contenu dans `.sbody` qui défile seul, derniers `.btns` déplacés dans un pied collé `.sfoot`
  (sauf dans un formulaire), croix ✕ `#sheetX` ; la page derrière est bloquée (`lockBody` / `unlockBody`, classe `body.locked`).
- Accueil : en-tête avec bouton ☰ (`#menuBtn`, `openMenu`), Roxy Tamagotchi + humeur + 🪙 cagnotte du mois (`#purse` → `sheetMoney`),
  durée + « C'est parti », puis **une seule ligne** (`#oneLine`, priorité 🏖️ 🎂 🔥 💰 🎉 🏴‍☠️ 🎯 → `sheetToday`). Plus de tuiles ni d'onglets.
- Menu ☰ : Progrès, Tirelire (vue `shop`), Carte d'exploration, Dernières sorties, Carnet, Album (Progrès › photos), Mes rappels,
  Bonus et règles, Tuto, Changer de prénom, Superviseur (discret). Pages = `body.page` + bouton fixe `#backHome` « ← Accueil ».
- 🌫️ Brouillard « lampe » 100 % opaque : toile `FogCanvas` (L.Canvas modifié : repeint tout en `FOG_COLOR`, puis efface en
  `destination-out`) dans le calque `fog` ; chemins éclairés sur `LAMP_M` = 40 m (épaisseur recalculée au zoom), anciennes cases
  sans chemin = ronds de 55 m ; repeint pendant les glissements. Chemins gardés **seulement sur le téléphone** (`wouaf-traces`,
  `saveTrace` à la fin d'une balade, ~600 Ko max, jamais envoyés). En balade : chemins < 15 jours + chemin en cours en direct.
- 🗺️ Carte d'exploration plein écran (`openExplore`, `body.explore`, barre `#exploreBar`) centrée sur ma position avec Roxy ;
  plus de cercle des 2 km (le % reste calculé sur 2 km).
- Balade : zoom toujours au centre quand la carte suit (`setFollow`), recentrage après zoom ; Roxy placée au 1er point GPS.
  Ligne du chrono et mode poche : « 🪙 +12 · 447 au total » (`liveMoney`).
- 📖 Tuto 8 écrans illustrés (`tutoPages`, `showTuto(step, replay)`), à revoir depuis le menu ou « Les bonus ».

## Version 2.0 (APP_NUM 34, libellé « 2.0 », décidé le 14/11 : PLAN-v2.md)
- 🔑 **Superviseur « Éric », sans code** : le 1er téléphone qui prend le prénom Éric (accents et majuscules ignorés) le réclame
  (`POST /claim`, jeton aléatoire dans KV `admin` et dans `wouaf-sup` sur le téléphone ; refusé sur un autre téléphone). Les routes superviseur
  (`/check /pause /boost /dash /restore /adjust /reset /void`) acceptent le jeton (`supOk`) **ou** `SUPERVISOR_CODE` (toujours valable, 20 essais ratés/jour).
  Le menu ☰ d'Éric montre Pause · Jours bonus, Tableau de bord, Corriger, Restaurer, Annuler une balade, Tout remettre à zéro (`supAuth()`).
- 🧪 **Éric = testeur** (`isTester()` = jeton + prénom Éric) : balades, objets, brouillard et récap marchent, mais pas de tirelire (ni coffre ni trésor),
  pas d'amendes (`processMalus`/`shortMalus`), pas de rappels (menu caché, Worker `isTester` ignore `/register` et le cron). Ses balades sont envoyées
  (cs 0, `sum.test`) donc comptent pour les dernières sorties et l'humeur de Roxy.
- 🧹 **Remise à zéro** (`POST /reset`, double confirmation dans `openReset`) : le Worker efface `d: b: a: t: duo:` et `last`, écrit KV `reset` = date (ms),
  ignore ensuite les `/walk` plus vieux. `GET /pause` renvoie `reset`, `treasure`, `last`. Chaque téléphone (`applyReset`, appelé à l'ouverture, au retour dans
  l'app et à la fermeture d'une fiche) compare à `wouaf-reset-vu` ; attend la fin d'une balade et la fermeture du récap ; efface jeu, carnet, traces, album photo
  (IndexedDB), envois, sorties, tuto… **garde** prénom, rappels, `wouaf-avatar`, jeton superviseur ; `firstUse` = demain (amendes dès demain) ; écran
  « 🎉 Wouaf Balades 2.0, tout repart de zéro ! » (`showWelcome2`, clé `wouaf-welcome2`) puis tuto. Téléphone neuf : pas d'écran, juste le tuto.
- 🏴‍☠️ **Trésor** : à 2–3 km de la maison, **un seul gagnant** : `POST /treasure` (KV `t:<semaine>`) → `first` ou `found`+`by`. Le gagnant reçoit 500 clebsous
  **hors plafond** (`game.bonus`, comme un coffre, `res.hunt`, `gx.h`) ; les autres voient « 🏴‍☠️ X a trouvé le trésor ! » (`hunt.gone`, `syncHunt` via `/pause`).
  Sans réseau, pas de gain décidé tout seul (nouvel essai 30 s). ⭐ et objets inchangés.
- ❌ **Annuler une balade** : tableau de bord › ❌ Annuler › motif → `POST /void` (KV `a:<prénom>`, `type:"void"`, id = fin de balade `e` en secondes ; la balade est
  barrée dans le tableau de bord et `/recent`, `last` est recalculé sans elle). Le téléphone (`applyVoid`, via `fetchAdjust`) retire durée, bonus, défi, trésor,
  coffre, stats, album, série, semaine parfaite grâce à `gx` gardé dans l'entrée du carnet (`saveToLog`), marque `e.void` (« ❌ annulée » dans carnet et sorties,
  exclue de `walkedOn`/`walksBetween`/`lastWalk`). Seule balade ≥ 20 min du jour : amende −30 **sans joker** (`malus k:"void"` ou `game.noJoker[jour]`).
  Fiche « Balade annulée » avec motif à l'ouverture.
- Tests : `tests/worker.test.mjs` (Node : `node --test tests/worker.test.mjs`, KV simulée) et `tests/e2e.py` (Playwright, vraie page, **vrai code du Worker**
  via `tests/serve-worker.mjs` sur le port 8787, `python3 -m http.server 8000` ; Leaflet remplacé par `tests/leaflet-stub.js`, donc la carte n'est pas testée).
- À savoir : prévenir Éric de taper son prénom **avant** que les ados ouvrent l'app (sinon l'un d'eux pourrait prendre « Éric »).
- 🚨 Alerte trésor (décidé le 14/11) : si un promeneur annule sa balade (`cancelWalk`) après avoir trouvé le trésor, personne n'est payé : le téléphone envoie
  `POST /alert` (KV `alerts`) ; le tableau de bord d'Éric l'affiche avec « Redonner 500 » (`POST /alert-resolve`, ajoute une correction `/adjust` de 500) ou « Ignorer ».
- Correctifs du 14/11 au soir : `autoClaim()` à l'ouverture (prénom Éric choisi avant la 2.0 = pas de jeton → demandait le code) ; Éric pris ailleurs
  (autre téléphone, Safari au lieu de l'icône) → Superviseur › « 🔑 C'est mon téléphone » avec le code une fois (`POST /claim` + `code` : nouveau jeton,
  l'ancien ne marche plus, 20 essais/jour) ; « Payé ✓ » sans code sur le téléphone d'Éric ; tableau de bord lisible en mode sombre (`.dash .wk`).
- ✨ Nouvelle version (décidé le 14/11) : **un seul écran** « Nouveau dans la version X » (`showNewsScreen`, `NEWS[APP_NUM]`, 2–3 lignes) avant le reste
  du « Quoi de neuf ». Tuto **court de 3 écrans** (`tutoShort`) au 1er lancement et après la remise à zéro ; le tuto complet (8) reste dans ☰ › Tuto et « Les bonus ».
  Tests : `tests/e2e_claim.py`, `tests/e2e_accueil.py`.
- Libérer le prénom Éric volé ou perdu : fait avec « C'est mon téléphone » (code). Trésor : on garde l'anneau 2–3 km, même endroit pour tous.

## Version 2.1 (APP_NUM 35, décidé le 14/11 : PLAN-v35)
- ⚔️ **Duels** (menu ☰ › Duels, `sheetDuels`, `sheetDuelNew`, `ficheHTML`) : qui, 3 ou 7 jours, 🐾 Balades (plus de balades ≥ 20 min, puis minutes) ou
  🗺️ Guerre des rues, mise 0/25/50/100 (≤ tirelire de chacun : `have` envoyé + `sum.cs` du serveur). Fiche récap identique pour les deux ; 24 h pour répondre ;
  commence le lendemain (journée de l'app, 4 h). Un seul duel ouvert par personne. Annuler = les deux d'accord ; abandon = défaite ; égalité = rien ne bouge.
  Worker : KV `duels` (liste), routes `/duels /duel-new /duel-answer /duel-cancel /duel-quit /duel-map`, `/duel-admin` (superviseur), fin calculée à la lecture
  et par le cron (`getDuels`). Mises = corrections `a:<prénom>` avec `duel:1` (hors plafond, pas de carte « Message du superviseur » à part). Notifications push
  (`pushTo`) : défi reçu, accepté, refusé, rues volées, fin. Éric exclu (403), voit et annule les duels dans le tableau de bord.
- 🗺️ **Guerre des rues** : seulement pendant un duel « streets », l'app ajoute `cells` (cases `cellOf` ≈ 100 m, sans tracé ni horaires) à l'envoi `/walk` d'une balade
  ≥ 20 min ; passer sur une case de l'autre la vole (`lost`). Carte `sheetDuelMap` (rectangles orange / violet, sans brouillard). Cases effacées à la fin du duel.
- 🏅 **Record du mois** : KV `rec:AAAA-MM` (plus longue balade valide, Éric exclu), renvoyé par `/walk` (`record`) et `GET /pause` ; +50 hors plafond (`RECORD_CS`,
  `game.recWins` pour le retirer si la balade est annulée ; `/void` recalcule le record). Affiché dans Progrès, sur l'accueil, et carte « X a battu le record ».
- 💎 Accueil : la ligne importante montre d'abord le duel (`duelLine`), puis les gros lots (`lotsHTML`) : trésor doré tant qu'il n'est pas gagné, coffre (chaud ou pas),
  record, « Lance un duel ». L'accueil remplit l'écran (`main.wrap` en colonne). Retour dans l'app = `startupDigest` (résultats de duel sur les deux téléphones).
- Tests : `tests/duels.test.mjs` (Node) et `tests/e2e_duels.py`. Relancer `tests/serve-worker.mjs` après une modification du Worker (il garde l'ancien code).
- Retours du 14/11 (19 h) : défi sans réponse = expiré au bout de **6 h** (`DUEL_TTL`) ; l'adversaire peut **proposer une autre mise** (`/duel-counter` : l'ancien défi
  devient `countered`, nouveau défi dans l'autre sens avec `counterOf` et `was`) ; celui qui a lancé peut « Retirer » ou « Changer le défi ».
  👀 **Dans son ombre** (`shadowCheck` dans `onFix`, `shadowClear` à la fin) : pendant une balade d'un duel « Guerre des rues » commencé, les rues de l'autre sont en
  violet sur la carte (`/duel-map`, rafraîchi toutes les 10 min) et un toast + petit tic préviennent quand on entre dans l'une d'elles (une fois par rue).
- Retours du 14/11 (19 h 30) : champ prénom lisible en mode sombre (`.sheet input` dans le bloc sombre) ; prénom Éric refusé → champ code dans la fiche du
  prénom (`#whoSup`, « C'est moi ») ; « Quoi de neuf » = **une carte à la fois** (plus de glissement horizontal, qui coinçait sur iPhone) ; messages de la fenêtre
  Superviseur et de la remise à zéro aussi en bandeau (`toast`).
- Retours du 14/11 (20 h) : confettis calés sur le temps (même vitesse à 30/60/120 images/s) et jusqu'en bas de l'écran (7 s max) ; Éric voit ☰ › ⚔️ Duels
  en **aperçu** (`duelPreview`, `duelPrev` : formulaire et fiche avec les vrais prénoms de `/recent`, envoi désactivé) ; tableau de bord : % d'exploration
  (`sum.fog`, un chiffre, aucun trajet) et duel en cours de chaque promeneur.
- 📈 Statistiques d'utilisation (décidé le 14/11, chiffres seulement) : `wouaf-usage` (par jour, 14 j : `o` ouvertures, `s` secondes dans l'app, `p` pages vues =
  titre `<h2>` de chaque fiche + onglets + carte + balade), envoyé par `sendUsage` (`POST /usage`, KV `use:<prénom>`, Éric ignoré) à l'ouverture et quand l'app
  passe en arrière-plan ; tableau de bord : « 📱 7 derniers jours : N ouvertures · X min dans l'app » + 5 pages les plus vues. Effacé par la remise à zéro.
- Retours du 14/11 (20 h 10), les 6 points UX : **une seule fenêtre** à l'ouverture (nouveautés + « Quoi de neuf » empilés, `.dstack`, un bouton ;
  `showNewsScreen` n'est plus appelé à l'ouverture) ; mode sombre relu (album, trophées, accessoires, puces du tuto, sélecteurs) ; tout message `role=status`
  d'une fiche hors de l'écran → bandeau (MutationObserver sur `#sheet`) ; boutons « ❌ Annuler » du tableau de bord plus grands ; tuto court : « rue neuve »
  expliquée ; menu d'Éric : une seule entrée « 🔑 Superviseur » (`sheetSupMenu`).
- 🔒 Statistiques **seulement avec l'accord du promeneur** (`wouaf-stats-ok`, décidé le 14/11) : carte de choix en tête de la fenêtre d'ouverture tant qu'il n'a
  pas répondu (`statsCardHTML`, « ✅ D'accord » / « Non merci »), avec le rappel de ce qui reste privé (`PRIVACY_TXT`) ; changer d'avis : ☰ › 🔒 Vie privée
  (`sheetPrivacy`). Non = rien compté, chiffres effacés sur le serveur.
- Retours du 14/11 (21 h) : gros lots visibles aussi pour Éric (testeur) ; trésor annoncé sur l'accueil même sans maison (avant la 1re balade / après la
  remise à zéro), caché seulement une fois trouvé cette semaine (`wouaf-tresor`).
- 📲 Bouton « Sortir Roxy » (décidé le 14/11 ; un vrai widget iPhone est impossible pour une web app) : lien `#go` (`goFromShortcut`, aussi sur `hashchange`)
  = balade libre tout de suite (durée choisie en dernier) ; ☰ › 📲 Bouton « Sortir Roxy » (`sheetShortcut`) : copier le lien + étapes Raccourcis › « Ouvrir les URL »
  › icône `sortir-roxy.png` (Roxy + ▶️) via « Sur l'écran d'accueil ». **Lien testé par Éric : `webapp://<hôte><chemin>#go`** (ouvre l'app, pas Safari ; la forme avec https ne marche pas). `SHORTCUT_URL` = lien iCloud du raccourci d'Éric (14/11) → bouton « ⬇️ Télécharger le raccourci ». Test : `tests/e2e_go.py`.
  À vérifier sur iPhone : le raccourci doit ouvrir l'app de l'écran d'accueil, pas Safari (stockages séparés).
- 📲 Fenêtre d'ouverture : carte « Sors Roxy en un seul geste » **une fois par téléphone** (`wouaf-sc-tip`, pas pour Éric), bouton « Je l'installe » → `sheetShortcut` ;
  dernière page du tuto court : astuce ☰ › 📲.
- Correctif 14/11 (22 h 30) : intro vue deux fois après la remise à zéro (une mise à jour en attente rechargeait la page en fermant l'écran « tout repart »,
  en plein tuto) → `introRunning` (écran d'accueil + tuto non rejoué) bloque `applyUpdate` et les rechargements de `closeSheet` jusqu'à la fin du tuto.
- ⚔️ **Arène** sur l'accueil (décidé le 14/11, 22 h 30 : « plus ludique, les enjeux, la compétition ») : `arenaHTML` (carte violette, classes `.arena`, `.atag`, `.bet`)
  → défi reçu (VS, pulse), duel en cours (face-à-face « Toi a – b X » avec barres, phrase « Tu mènes ! » / « X mène… » / « Égalité… »), défi envoyé, ou
  « ⚔️ Défier X » (3 adversaires max). À droite, le pari : « 🎲 ± mise 🪙 » (ou « pour la gloire »). En tête des gros lots pendant un duel ou un défi reçu.
  Éric : arène en aperçu. La ligne importante ne montre plus le duel.
- 🎲 **Que des paris** (décidé le 14/11, 22 h 40) : mises 25 / 50 / 100 seulement (`DUEL_STAKES` dans l'app et le Worker, 0 refusé) ; il faut ≥ 25 dans les deux
  tirelires (sinon « Voir la fiche » grisé avec un message) ; contre-proposition parmi les autres mises.

## Version 2.2 (APP_NUM 36, décidé le 14/11 : maquettes « accueil A » et « menu C »)
- 🏠 **Accueil sur un seul écran** (testé à 393 × 760, iPhone sans barres) : en-tête plus fin, humeur sur une ligne (`.moodBtn .mt`), « Combien de temps ? »
  caché, bouton « C'est parti » compact (« jusqu'à N 🪙 clebsous », le détail durée + bonus reste dans « 🎁 Bonus ? »), astuce courte « 💡 1 h : jusqu'à N (×1,5) ».
  Gros lots = **3 tuiles** côte à côte (`.ltiles .lt`, même `data-lot` qu'avant), titre « 💎 Les gros lots », arène raccourcie ; plus de `min-height` sur `main.wrap`.
- ☰ **Menu en tuiles** (`openMenu`) : 4 grosses tuiles (`.mgrid` : Progrès, Tirelire, Duels, Exploration), liste courte (`.mlist` : sorties, carnet, album, bonus,
  🔑 Superviseur pour Éric), réglages en icônes (`.micons` : rappels, raccourci, prénom, vie privée, tuto), pied « Superviseur » discret + « À propos · version »
  (`#muAbout`, fiche avec les crédits du `<footer>`, désormais caché). Mêmes id `mu…` qu'avant.
- Tests : `tests/e2e_accueil.py` vérifie l'accueil et le menu sans défilement.

## Version 2.3 (APP_NUM 37, décidé le 15/11 : « Roxy plus vivante », lot 1 points 2, 3, 4 ; le reste attend)
- 🐶 **Roxy parle** : bulle sous l'en-tête (`#heroSay`, `#sayBtn`, classe `.say`). À l'ouverture et au retour dans l'app, phrase d'accueil (`sayHello` :
  1re balade, « Merci pour tout à l'heure » / « X m'a sortie tout à l'heure » < 3 h, « Je m'ennuie » ≥ 14 h, « Tu me manques » ≥ 24 h), sinon une phrase au hasard
  (`sayPool` : heure du jour, week-end, trésor, coffre chaud, série, duel, record, phrases générales ; `sayNext` évite les 6 dernières). Toucher la bulle = autre phrase.
  L'humeur reste en barre sous « Salut X » (toucher = dernières sorties). Aucune donnée nouvelle envoyée.
- ❤️ **Caresser Roxy** (`bindPet`, accueil et fiche Roxy) : glisser le doigt sur la photo → cœurs (`.heart`), queue qui remue vite (`.petted`), petit tic, phrase contente ;
  un glissement n'ouvre pas la fiche (`petAt`).
- Place gagnée : titre « Les gros lots » retiré (tuiles seules), tuiles un peu plus basses, arène « Qui sortira le plus Roxy ? Mise des clebsous ! ».
- En attente (décidé le 15/11) : rappels « à la voix de Roxy », lot 2 (rythme de la journée, souvenirs, journal), lot 3 (photos par humeur, tenues, anniversaire), lot 4 (balle, réactions en balade).
- 🧭 **Classement des explorateurs** (décidé le 15/11 : « de l'enjeu », **seulement la couronne**, à la semaine) : le Worker calcule, pour la semaine lundi–dimanche
  (journée de l'app, 4 h ; `weekOfDay`, `explorers`), 3 × rues neuves + objets ramassés des balades ≥ 20 min non annulées (Éric exclu), et `GET /pause` renvoie
  `explo = { wk, rank:[{w, r}], prev:{ wk, rank } }` : **seulement les places** (ex aequo = même place), jamais les points. L'app envoie `nc` (rues neuves, `res.cells`)
  et `ob` (objets, `res.got`) avec `/walk`. Accueil : carte `#exploCard` (`exploHTML`, podium 3 premiers, « Toi », astuce « tu passes devant X ») à la place de la ligne
  des missions ; fiche `sheetExplo` (podium, règles) ; lundi : carte dans « Quoi de neuf » (clé `wouaf-explo-vu`). 👑 **Couronne** sur Roxy (`wearCrown` dans `roxyHTML`)
  chez le 1er de la semaine passée, toute la semaine. Pas de clebsous. Test : `tests/explo.test.mjs`, `tests/e2e_explo.py`.
- Les missions du jour passent dans la bulle de Roxy (`sayMission` : pause, anniversaire, jour bonus, défi du jour) et dans le menu (📋 `#muToday` → `sheetToday`).
  Arène sans duel = une ligne (`.arena.slim`, un seul bouton) ; sur l'accueil, pas de phrase sous le face-à-face (`#home .arena .atag`).

## Version 2.4 « Croquette » (APP_NUM 38, décidé le 15/11 entre 0 h 50 et 2 h 20 ; ⚠️ règle : ne coder que sur demande explicite)
- 🏠 **Gros bouton** (`#goCard`) : mini-carte du quartier en canvas (`drawMiniMap` : cases vues, chemins `wouaf-traces`, Roxy à la maison, % exploré, flèche du trésor ;
  toucher = carte d'exploration) qui **prend toute la place restante** (`fitHome`, mesure le bas de `#homeFoot`, jamais de défilement) ; « ▶️ C'est parti ! » / « Encore une ? »
  + gain (`updateGo`) ; objectifs (`#goObj` : défi, trésor, coffre chaud ou place d'explorateur → `sheetToday`) ; durées dans le bouton (étiquette « ×N » sur la durée conseillée,
  `.sug`) ; « où j'en suis » (`#goStat` : ma sortie du jour + dernière sortie de Roxy + 🔥 série → `sheetOuts`). Plus de « Combien de temps ? » ni de ligne « Bonus ? ».
- 🌤️ Météo (`loadWx`, Open-Meteo, coordonnées arrondies de la maison, cache 30 min `wouaf-meteo`) : pastille sous « Salut X » (`wxText`) ; Roxy en parle (`sayWeather`)
  seulement si elle n'est pas sortie depuis ≥ 3 h. L'humeur courte s'affiche s'il n'y a pas de météo.
- Classement des explorateurs sur une ligne (`.explo.one`, l'astuce est dans l'aria-label et la bulle) ; gros lots or / **argent** (coffre) / **bronze** (record) + **4e tuile
  violette « ⚔️ Défier »** quand il n'y a pas de duel en cours (sinon la carte de l'arène complète).
- 🔢 Ligne du bas `#homeFoot` : « v2.4 « Croquette » » (`CODENAMES`) + compteur de la famille (KV `fam` du Worker, `GET /pause` → `wouaf-fam`).
- 🤫 **Secret** : 17 touchers à la suite (< 1,5 s entre deux) sur `#homeFoot` (`EGG_N` = lettres de « Wouaf Wouaf Balades ») → `eggOpen` : Roxy 😎, stats cachées,
  **+500 clebsous hors plafond une seule fois par ado** (`game.egg`, `game.bonus`) ; Éric : pas de gain. Indices dans la bulle (`eggHint`, un par semaine à partir du 16/11).
- 🗺️ **Écran de balade B** : missions en haut (`#wChips` : objets, rues neuves, photo ; cibles selon la durée `walkTargets`), trésor = flèche au bord (`#wTreasure`),
  pas 🐾 tous les ~28 m (`addPaw`, ligne du trajet discrète `TRACK_STYLE`), toucher Roxy → `#roxyMenu` (pipi, caca, photo, ⋯ = duo / alerte) ; en bas gros chiffres
  (`walkNums`), une ligne (`renderWLine` : radar > classement > astuce) et deux boutons : 🌙 Poche et ⏹ **Fini en appui long 1 s** ; la barre se réduit après 10 s
  (`wakeBar`, classe `.mini`) ; objets qui s'envolent vers le compteur (`flyPlus`) ; fête « Sortie validée » à 20 min. Les anciens boutons existent toujours (cachés).
- 👃 **Flair** : toutes les 15 min (au quart d'heure, dès 5 min de balade) une piste fraîche à ~100 m pendant 3 min, +5 (`spawnTrail`, `flairTick`, `trailCheck`),
  bandeau violet `#wFlair`, message en mode poche. Le téléphone envoie `POST /walk-live` (on:1 + heure de départ / on:0), **jamais de position** ; le cron du Worker (`flairs`, KV `live`)
  envoie la notification « 👃 Roxy a flairé quelque chose ! » (tag `wouaf-flair`) ; `/walk` et la remise à zéro effacent l'entrée.
- 💡 Bulles d'aide (`coach`, clé `wouaf-tips`, une fois par sujet : toucher Roxy, flair, barre réduite ; « Garde le doigt » à chaque appui trop court).
- ❓ Menu : « Aide » (`sheetHelp` : tuto complet, bonus et règles, questions fréquentes, revoir les bulles) remplace « Bonus et règles » et l'icône Tuto. Tuto refait (8 + 3 écrans).
- 🐛 Plus de « Bravo ! 0 min » collé sous l'accueil : `setStatus` passe en bandeau en haut hors carte ; balade < 2 min = « Balade trop courte : pas notée ».
- Tests : `tests/e2e_balade.py` (écran de balade, flair, Fini), `tests/e2e_accueil.py` (gros bouton, secret, météo, aide), `tests/explo.test.mjs` (walk-live, flair, fam).
- En attente (idées, pas de feu vert) : échange de balades payé entre ados (règles à trancher), bouton « Signaler un bug » vers un groupe WhatsApp dédié.

## Version 2.5 « Caviar » (APP_NUM 39, décidé le 15/11 entre 2 h 38 et 3 h 09, codé à 3 h 52 sur demande)
- 🌙 **Accueil « nuit » épuré** : classe `body.nuit` (posée par `setNuit`, MutationObserver sur les classes du body) quand on n'est ni en balade, ni sur une page,
  un récap, la carte ou l'exploration ; fond #0b0e13, cartes #141922, ivoire #f3efe6, titres Didot ; `theme-color` suit. Les fiches, la balade et les pages gardent leurs couleurs.
- **Doré seulement pour le gros lot** (choix « B ») : tracés de la mini-carte, contour de Roxy, tirelire et flèche du trésor en ivoire/gris. Le bouton « C'est parti »
  (verre, liseré émeraude) devient doré (`.hot`, ligne `#goLot`) quand le trésor est libre (`huntOpen`) ou que le coffre est chaud.
- 👑 **Couronne** : vraie couronne sur Roxy (`wearCrown`, 1er la semaine passée), sinon **couronne fantôme** grise (`#crownBtn.ghost`) ; toucher = `sheetExplo`.
  Plus de barre de classement sur l'accueil. Petite 👑 qui pulse dans le bouton (`#goCrown`) quand cette balade peut te mettre 1er (2e, ou personne classé). Pas de médaille.
- 🎯 **Une seule icône d'objectifs** en haut à droite de la mini-carte (`#goObj`, pastille = défi + trésor + coffre chaud restants, ✓ quand tout est fait) → `sheetToday`.
- **Petite ligne sous le prénom** (`heroLine`, `#hLine` → `sheetOuts`) : « ☀️ 14° · ✓ sortie ce matin · 🔥 5 » / « attend depuis 6 h » (pas de 🔥 à 0). `#goStat` caché.
- 🐶 **Roxy ne parle que quand on touche sa photo** (`showSay`, bulle 6 s par-dessus la carte ; toucher la bulle = `sheetRoxy`) ; plus de bulle permanente.
- Durées en **pattes 🐾 qui grossissent** (`updateGo` ajoute `<em>`, `.done` / `.on`, étiquette verte « ×N ») + barre émeraude `#durFill`.
- Tuiles du bas pleines, chiffres seuls (or sourd, argent, bronze, violet). Ligne du bas « v2.5 · CAVIAR » + petite ligne famille.
- Tests : `tests/e2e_accueil.py` (nuit, ligne, couronne fantôme, bouton doré, bulle au toucher), `tests/e2e_explo.py` (vraie couronne, 👑 qui pulse).

## Version 2.6 « Croquette » (APP_NUM 40, décidé le 15/11 entre 9 h 09 et 9 h 50 : PLAN-v40-croquette dans le projet)
- 🏷️ Nom de code **toujours « Croquette »** (`CODENAMES`), seul le numéro change.
- 🔍 **Lisibilité** : `--muted` foncé (#4d5549 clair, #bcc6bd sombre, #b6becb sur l'accueil nuit), plus de texte < 12,5 px (12 px → 13 px), moins de textes
  estompés (`opacity`). **Bug corrigé** : les fiches ouvertes depuis l'accueil « nuit » héritaient du texte ivoire (`body.nuit .sheet{color:var(--ink)}`).
  Carte verte de Progrès plus foncée. Audit de contraste automatique (Playwright) sur 13 écrans, clair et sombre.
- 🔍 **La page ne se zoome plus** (bug du 15/11 : pincer zoomait aussi la barre du bas) : viewport `maximum-scale=1, user-scalable=no`, `gesturestart`/
  `touchmove` à 2 doigts bloqués **hors** `.leaflet-container`, `touch-action:manipulation`. Pas de blocage du double-toucher (mode poche, secret).
- 🗺️ Cartes un cran plus loin : balade zoom 16 (au lieu de 17), exploration 15 ; l'exploration ne se recentre plus toute seule quand la position GPS
  arrive si on a déjà touché la carte (`exploreTouched`).
- ☁️ **Trésor = grand nuage doré flou** (`huntCloud`, `HUNT_CLOUD` = 600 m, centre décalé de 150–450 m du trésor, le même pour tous) à la place du cercle
  orange de 200 m. Flèche au bord (`#wTreasure`) = direction et distance du **nuage** (« fouille ! » dedans) ; la toucher = la carte va sur le nuage
  (`cloudBounds`, 📍 pour revenir). Mini-carte : halo doré + « ☁️🏴‍☠️ x km » ; toucher la flèche ou la tuile Trésor = exploration centrée sur le nuage
  (`openExplore(true)`). Le radar (< 150 m) prend le relais.
- ☁️ **Nuage argenté du coffre chaud** (`chestCloud`, `CHEST_CLOUD` = 350 m, `CHEST_CLOUD_X` = ×2) : quand `chestChance() > 0`, un coin peu exploré
  (cases `game.seen` absentes) à 0,7–1,8 km de la maison, tiré chaque jour (`game.chestCloud`) ; chance de coffre doublée dedans. Carte de balade (💰 pâle),
  exploration, mini-carte ; tuile Coffre chaud = exploration centrée dessus (`openExplore("chest")`). Calculé sur le téléphone, rien n'est envoyé.
- 🥣 Rappels de soin sur le récap (`careBox`, sans clebsous, à cocher) : eau (« Il fait X° » si ≥ 25°, `HOT_C`), 🦴 friandise si ≥ 45 min (`TREAT_MIN`).
  Pas de goutte d'eau (ça fait penser au pipi).
- 🐕 **Copains chiens** (`wouaf-copains` sur le téléphone : id, n, c, last, note) : bouton 🐕 dans le menu de Roxy en balade (`sheetCopWalk`, position gardée),
  « Tu as croisé un copain ? » sur le récap (`copRecapBox`), ☰ › Copains (`sheetCopains`, fiche : renommer, note, supprimer).
- 📍 Repères de balade (`addPin` → `gw.pins` : p pipi, c caca, d copain, t trésor) gardés **avec le chemin** (`wouaf-traces` : `w` prénom, `t`, `p`), jamais envoyés.
  Récap : « 💧 Roxy a marqué N territoires ».
- 🔥 **Carte de chaleur** (☰ › Carte de chaleur, `sheetHeat`, carte Leaflet dans la fiche) : seulement les chemins du promeneur (`myTraces` : `w` = prénom,
  ou sans prénom = anciens chemins de ce téléphone), calques 🐾 💧 💩 🐕 🏴‍☠️, période 7 j / 30 j / tout, territoire en km² (cases × 0,0095).
- 🔊 **Sons** (WebAudio) : « cling » (`ding`), aboiement en fin de balade (`bark`), fanfare trésor/coffre (`fanfare`). Bouton pour couper : ☰ › 🔊 Sons et
  ⋯ pendant la balade (`wouaf-son`, 0 = coupé). Le mode silencieux de l'iPhone coupe déjà les sons de la page.
- 💶 **Paie à la semaine** (remplace la paie du mois ; `offerPayday` neutralisé) : `weekPayRoll` à la 1re ouverture d'une nouvelle semaine (journée de l'app) :
  paie = `moneyAll()` (somme des `moneyOf` de tous les mois) − `game.wkBase.cum` ; `game.weeks[AAAA-MM-JJ du lundi]` (clés complétées par `padK`).
  1re fois : base = total − balades de la semaine en cours du carnet. Carte « Jour de paie » dans le « Quoi de neuf » ; **révélation 100 clebsous = 1 €**
  à la 1re paie (`game.reveal`). Envoi `POST /week-pay` → KV `pays` (12 semaines par promeneur) ; tableau de bord : « 💶 Paies de la semaine » avec
  « Versé ✓ » (`POST /pay-mark`, superviseur) ; `/pause` renvoie `paid` → `wouaf-paid` ; Tirelire : « Paies des semaines ». Plafond toujours mensuel.
  Notification du dimanche soir : « Demain, c'est jour de paie ». La remise à zéro efface `pays`.
- 🎒 **Heures de cours** (☰ › Mes rappels : début/fin du lundi au samedi + « 🏖️ Vacances scolaires ») : `rap.cours`, `rap.vac` envoyés avec `/register`
  (`cleanCours`). Worker : aucune notification pendant un cours (`classEnd` dans `run` et `pushTo`, donc flair et duels aussi) ; un rappel prévu pendant
  un cours part à la fin du cours.
- 📊 **Roxy en chiffres** (`roxyNumbers`, en haut de Progrès) : km et « pas de chien » depuis le début (carnet du téléphone), cap atteint (`KM_PLACES`),
  et pour le promeneur : heure préférée, jour le plus actif, mois record.
- ☰ Menu : liste sur deux colonnes (tient sur un écran avec Carte de chaleur et Copains), icône 🔊 Sons.
- Pas dans cette version (décidé le 15/11) : planning et « je ne peux pas » (chaque ado doit sortir Roxy chaque jour : le relais n'a pas de sens).
- Tests : `tests/e2e_v26.py` (navigateur), `tests/worker.test.mjs` (cours, paies). Les tests ouvrent l'app avec `wouaf-vu` = 40.

## Version 2.7 « Croquette » (APP_NUM 41, décidé le 15/11 entre 10 h 17 et 10 h 24 : PLAN-v41-nuages dans le projet)
- 🐛 **Carte d'exploration vide** (écran blanc + barre verte : on croyait que la balade démarrait) : la règle `body:not(.hasmap)… #map{display:none}` la cachait ;
  corrigé par `body.explore #map{display:block !important}`. Touchers mini-carte, Roxy de la mini-carte, tuiles trésor/coffre → exploration visible.
- ☁️ **Nuages** sur les deux cartes (balade et exploration) : `FOG_COLOR` = blanc doux #f3f4f1 ; zones peintes dans la même toile (`FogCanvas._draw`, `fogZones`) :
  **doré** = trésor (`huntCloud`, 600 m), **argenté** = coffre chaud (`chestCloud`, 350 m), dégradé radial ; tout s'efface le long des chemins.
  Plus de cercles à part (halos de la 2.6 retirés). **En balade, tout ce qui a déjà été fait reste visible** (`fogData(false, …)`), comme en exploration.
  Pattes 🐾 avec ombre foncée, trajet en pointillés bruns (lisibles sur le blanc).
- 🐛 **Appui long sur « Fini »** : plus de texte sélectionné sur le récap (`#walkbar` sans sélection, `body.nosel` pendant que le doigt est posé, sélection effacée).
- Tests : `tests/e2e_realmap.py` avec la **vraie** carte Leaflet 1.9.4 (construite par `tests/build-leaflet.sh` : clone GitHub + `bun build`) : mini-carte,
  exploration visible, pixels du nuage (blanc, doré, chemin découvert), tuile trésor, Fini en appui long. Les autres tests gardent le faux Leaflet.

## Version 2.8 « Croquette » (APP_NUM 42, décidé le 15/11 entre 10 h 33 et 10 h 39 : PLAN-v42 dans le projet)
- 👆 **Toucher la mini-carte = « Encore une ? »** (`#miniMap` → `#freeWalk`) : fiche « On part comment ? » avec 3 choix : 🚶 Balade libre · 🗺️ Choisir un parcours ·
  ☁️ **Carte d'exploration** (`#chExplo`, nouveau). La carte d'exploration reste aussi dans le menu ☰.
- 🐾 **Motif du nuage** (choix n° 1 d'Éric) : petites pattes très pâles (`fogPattern`, tuile 64 px, 2 pattes, gris 15 %) peintes par `FogCanvas._draw`
  par-dessus le blanc, le doré et l'argenté ; effacées avec le nuage le long des chemins.
- « Exploré à 0 % » et mini-carte vide : normal après « Tout remettre à zéro » (plus aucune case vue) ; se remplit dès la 1re balade.

## Version 2.9 « Croquette » (APP_NUM 43, décidé le 17/11 en Wouaf 6 : lot 1 = trésor accessible + carte du superviseur)
- 🏴‍☠️ **Trésor plus près** : 0,8–1,5 km de la maison (`HUNT_MIN`, `HUNT_MAX` ; avant 2–3 km, trop loin pour les balades du quotidien).
  Nuage plus petit : `HUNT_CLOUD` = 400 m, centre décalé de 100–300 m. Les anciens trésors de la semaine (sans `v:2`) sont recalculés, sauf s'ils sont déjà trouvés.
- 🛣️ **Toujours sur une voie ouverte** (retour du 16/11 : trésor dans une résidence privée) : `snapHunt` interroge **Overpass** (`OVERPASS`, `HUNT_WAYS`) à 250 puis 600 m
  et pose le trésor sur le point le plus proche (`nearestOnWays`) d'une rue / chemin piéton ; exclus : voies de service (allées, parkings), `access` privé / interdit,
  `foot=no|private`. Photon n'est plus utilisé pour le trésor. Pas de réponse = nouvel essai à la prochaine synchro (`loadPauses`).
- 📌 **Superviseur › 🏴‍☠️ Carte du trésor** (`openHuntAdmin`, carte Leaflet dans la fiche) : maison, trésor, nuage vu par les promeneurs ; toucher la carte ou faire glisser 🏴‍☠️
  puis « Mettre le trésor ici » → `POST /hunt-move` (superviseur, KV `hpos` = { wk, lat, lon, at }) ; « Placement automatique » = `clear`. `GET /pause` renvoie `hpos`
  (→ `wouaf-hpos`) ; `weekHunt` le prend tel quel pour la semaine `wk` (même endroit pour tout le monde, pas recalé, `hunt.moved = at`). Déplacement impossible une fois trouvé.
  La remise à zéro efface `hpos`.
- Tests : `tests/e2e_v43.py` (vraie carte, Overpass simulé), `tests/worker.test.mjs` (/hunt-move).

## Version 3.0 « Croquette » (APP_NUM 44, décidé le 17/11 en Wouaf 6 : lot 2 superviseur)
- 🏠 **Maison de la famille** placée par Éric (Superviseur › 🗺️ Carte du superviseur : toucher la carte + « Maison ici », ou « 📍 Je suis à la maison »,
  confirmation si elle existe déjà) → `POST /home-set` (KV `home`, **arrondie à 0,002° × 0,003° ≈ 200 m** : le dépôt est public, jamais l'adresse exacte).
  `GET /pause` renvoie `home` (→ `wouaf-fhome`) ; `applyFamilyHome` remplace `game.home` de chaque téléphone (et oublie son nuage argenté du jour).
  Changer la maison efface un trésor automatique (`hpos.auto`), jamais un trésor placé à la main. La remise à zéro garde la maison.
- 🏴‍☠️ **Un seul trésor pour tous** : le téléphone d'Éric publie son trésor automatique une fois recalé (`publishHunt` → `/hunt-move` avec `auto:1`) ;
  le Worker ne remplace jamais une position de la même semaine par une automatique. `weekHunt` recalcule si la maison change (`hunt.hk`). Sans publication,
  chaque téléphone calcule le même trésor à partir de la maison commune.
- ☁️ **Nuages argentés** : chaque ado envoie le nuage du jour de son coffre chaud (`sendCloud` → `POST /cloud`, centre d'une zone de 350 m, jamais sa position ;
  `off` quand il n'y en a plus ; clé `wouaf-cl-sent`) → KV `cl:<prénom>` (48 h) ; lus **seulement par Éric** (`POST /clouds`, superviseur). Éric n'envoie rien.
- 🗺️ **Carte du superviseur** (`openHuntAdmin`, remplace « Carte du trésor ») : sans balade ni nuages : maison, trésor (glisser ou toucher + « Trésor ici »),
  nuage doré, nuages argentés avec prénom, résumé en haut. Exploration ouverte au superviseur même sans maison (`openExplore`).
- 🏴‍☠️ 💰 **Fiches des gros lots** (tuiles de l'accueil ; avant, les deux ouvraient `sheetBonus`) : `sheetTreasure` (carte dorée, 500, un seul gagnant, distance
  et direction depuis la maison, temps restant jusqu'à lundi 4 h, « ▶️ J'y vais ! » = `goNow`, « ☁️ Voir le nuage doré ») ; `sheetChest` (carte argentée, chaud /
  dort / se réveille dans N jours, % de chances, règles, « Voir le nuage argenté », « 🎁 Ce que vaut chaque bonus » → `sheetBonus`). Classes `.trez`, `.tz-l`.
- 🐛 Dates sans zéro (`dayKey` / `weekKey` : « 2026-12-7 ») acceptées par `/hunt-move` et `/cloud` (bug de la 2.9 en décembre).
- Tests : `tests/e2e_v44.py`, `tests/worker.test.mjs` (home-set, auto, clouds) ; `e2e.py`, `e2e_realmap.py`, `e2e_duels.py` adaptés.

## Version 3.1 « Croquette » (APP_NUM 45, décidé le 17/11 en Wouaf 6 : lot 3, retours des promeneurs)
- 📷 **Bouton Photo visible** : 3 gros boutons en bas de la balade, `#camBtn` « 📷 Photo » (clique `#photoBtn`) · 🌙 Poche · ⏹ Fini (retour : une personne âgée ne trouvait pas la photo,
  cachée dans le menu de Roxy, qui reste aussi).
- 🌙 **Mode poche : glisser la patte** (`#pkSlide`, `#pkKnob`, pointer events) jusqu'à 85 % du rail pour revenir ; le double toucher est supprimé (il se déclenchait dans la poche).
- 📲 **Groupe WhatsApp « Roxy »** (`WA_GROUP`, `waHint()`) : consigne verte juste au-dessus du bouton « 📩 Envoyer au groupe « Roxy » » du récap et des paies (retour : récap envoyé au
  mauvais contact). Le partage reste le menu Partager de l'iPhone (choix d'Éric).
- Tests : `tests/e2e_v45.py` ; `e2e.py` : la balade de référence de Zoé suit l'horloge du test (`NOW`), plus l'heure réelle (le test échouait après 15 h).

## Version 3.2 « Croquette » (APP_NUM 46, décidé le 17/11 en Wouaf 6 : anti-oubli ; contient aussi la 3.1)
- 😴 **Anti-oubli** (retour du 16/11 : la fin automatique près de la maison a arrêté une balade, la promeneuse a relancé puis oublié → 1 h 30 comptée) :
  `checkForgot` (à chaque tic de `updateWalk`, aussi juste après une reprise) ; `stillSince` = début du groupe de derniers points du trajet à moins de `STILL_R` (60 m,
  ou la précision jusqu'à 120 m) ; immobile depuis `STILL_MIN` (12 min) → bandeau « 😴 Tu ne bouges plus depuis N min. La balade est finie ? » (`askForgot`, mode poche fermé,
  petit tic) « ⏹ Oui, terminer » / « Je continue » (pas de nouvelle question avant 12 min) ; sans réponse en `STILL_WAIT` (3 min) → arrêt automatique.
  Dans les deux cas **`stopWalk(cutAt)` coupe la balade au moment où on s'est arrêté (+1 min)** : trajet tronqué, durée, argent et carnet recalculés ; toast « le temps
  immobile ne compte pas ». Balade de plus de `LONG_MIN` (2 h 30) → même question une fois, sans coupe. La fin automatique près de la maison est inchangée.
- Tests : `tests/e2e_v46.py`.

## Version 3.3 « Croquette » (APP_NUM 47, décidé le 17/11 en Wouaf 6 : historique)
- 📖 **Journal de bord** (`sheetJournal`) : **toucher Roxy sur l'accueil** (`#heroDog`, après le saut ; avant : bulle) ; Roxy parle en haut (`.jhead`, `.jsay`, `sayNow`/`sayNext`) ;
  « Depuis le début, en famille » (balades, km, temps dehors, rues neuves : `fam` du Worker, `fam.min` ajouté) ; pipis / cacas ; « Qui sort Roxy ? » par promeneur
  (cette semaine, 30 jours, dernière, record, km) ; « Mes balades » (carnet du téléphone, cliquables) ; boutons Dernières sorties / Fiche de Roxy.
  Worker **`GET /journal`** (public, chiffres seulement : par promeneur sur ses 60 dernières balades non annulées + `fam`). La bulle (`showSay`) reste pour les autres cas.
- 🗺️ **Revoir une balade** (`sheetWalk(id, back)`) : carte Leaflet du trajet du carnet (`e.line`), 🟢 départ, 🏁 arrivée, repères 💧💩🐕🏴‍☠️ de `wouaf-traces` (trace dont `t` est à
  moins de 20 s de `e.id`), durée, distance, vitesse, clebsous (`recap.eu`), « Refaire ce trajet », « Renvoyer au groupe Roxy », « ← Retour ». Ouvert depuis le journal,
  le carnet (toucher une balade ; avant : tracé sur la carte cachée), les dernières sorties (seulement **mes** balades, classe `.entry.tap`) et Tirelire › Paies des semaines
  (`sheetWeekWalks(wk)` : balades de la semaine). Les trajets ne quittent jamais le téléphone ; Éric voit ceux des autres via les liens des récaps WhatsApp.
- Tests : `tests/e2e_v47.py` (vraie carte), `tests/worker.test.mjs` (/journal) ; `e2e_accueil.py` adapté (toucher Roxy = journal).

## Version 3.4 « Croquette » (APP_NUM 48, décidé le 17/11 en Wouaf 6 : gains du quotidien, express, paie du dimanche)
- 💶 **Budget du mois réparti** : `paceAllowed()` = `MONEY_SOFT` (15 €) × jour / jours du mois + `PACE_SLACK` (2 €) ; si les gains du mois (`game.money`) dépassent ce rythme,
  `addMoney` divise le gain par 2 (`PACE_CUT`), jamais zéro ; puis plafond doux / final comme avant.
- 💰 **Coffres plus fréquents, moins chers** : `CHEST_EUR` = 2 (200 clebsous, avant 5), `CHEST_GAP_DAYS` = 3 (avant 10), chance 8 % + 3 %/jour (max 30 %) ;
  budget coffres `CHEST_MONTH` = 6 €/mois (`game.chestM[mois]`) : au-delà, petits coffres `CHEST_SMALL` = 0,50 € (`chestValue()`), jamais plus de coffre « vide ».
  Toujours hors plafond (`game.bonus`) ; `applyVoid` retire aussi de `game.chestM`.
- 🛣️ **Trajets du quotidien** : `FRESH_DAYS` = 7 (avant 15 : une rue redevient « neuve » au bout d'une semaine) ; objets tous les 260–350 m (avant 350–450).
- ⚡ **Balade express 10 min** (`EXPRESS()`, `p.express`, `isExpress()`) : « On part comment ? » › ⚡ ; pas de jeu (`gameFix`, `huntCheck`, `flairTick` ignorés, pas d'objets),
  pas de clebsous (moins de 20 min), **pas d'amende « balade courte »** (et les express ne comptent pas parmi les courtes), notée dans le carnet (`express:1`) et envoyée
  au serveur ; `body.express` cache missions, trésor, flair, radar. Ne remplace pas la sortie de 20 min du jour.
- 💶 **Paie le dimanche** (`weekPayRoll`) : dès le dimanche `PAY_HOUR` (18 h), la semaine en cours est payée (`wkBase.done`) ; ce qui est gagné ensuite compte pour la semaine
  suivante ; app pas ouverte le dimanche soir = paie à la 1re ouverture suivante. Notification du dimanche soir : « C'est jour de paie : ouvre l'app ! ».
- Tests : `tests/e2e_v48.py` ; `e2e.py` (coffre à 2 €).

## Version 3.5 « Croquette » (APP_NUM 49, décidé le 17/11 en Wouaf 6 : signaler un bug)
- 🐞 **Signaler un bug** (☰ › « Signaler un bug », `sheetBug`, icône coccinelle dessinée `bugIcon`) : une ligne de texte (500 caractères) + **capture d'écran facultative** (`#bugFile`,
  réduite à ~800 px par `shrink`, JPEG < 390 Ko) → `POST /bug` (prénom, texte, version ; **ni position ni notification**). Worker : KV `bugs` (100 derniers, 10 par jour et par promeneur),
  image à part `bugimg:<id>` (JPEG seulement, **gardée 60 jours**, lue seulement par le superviseur).
- 🔑 **Superviseur › 🐞 Bugs signalés** (`sheetBugs`) : liste récente d'abord, « Réglé ✓ » / « Rouvrir » / « Supprimer » (efface aussi l'image), « 📎 Voir la capture » (`POST /bugs`, `/bug-done`, `/bug-img`, jeton ou code).
- Tests : `tests/e2e_v49.py` (navigateur, avec image), `tests/worker.test.mjs` (bugs, captures).
- Prochaines étapes décidées : signalements de la communauté (route barrée, chien agressif…), puis design plus doux et joyeux.

## Version 3.6 « Croquette » (APP_NUM 50, décidé le 18/11 : bug de localisation, balade à 0 m)
- 📍 **GPS surveillé** (`startGps`, `gpsErr`, `gpsCheck`, `gpsProblem`, `gpsHelp`) : retour d'un promeneur (17/11) : sur iPhone, la web app de l'écran d'accueil redemande la
  localisation à chaque ouverture ; sans réponse ou « Refuser », aucun point n'arrivait et la balade finissait à 0 m (gain limité par la distance) sans rien dire.
  Maintenant : position refusée (`code 1`) → **bandeau rouge** tout de suite (`showBanner("gps")`, classe `.wbanner.gps`) avec « 🔄 Réessayer » (relance `watchPosition`)
  et « ❓ Comment faire » (Autoriser, fermer / rouvrir l'app, Réglages › Service de localisation › Sites web Safari « Lorsque l'app est active ») ; pas de 1re position
  après 40 s (`GPS_WAIT`) ou plus rien depuis 90 s (`GPS_LOST`) → même bandeau (contrôle toutes les 15 s avec le chrono ; aussi quand l'appel iOS reste bloqué sans erreur).
  Une position revient → bandeau retiré + « 📍 C'est bon, Roxy te voit ! ». Le retour dans l'app (`visibilitychange`) passe aussi par `startGps`.
- ⏹ **« Fini » à 0 m** (`finishWalk`, appui long et clavier) : balade ≥ 5 min et < 50 m (hors express) → fiche « Roxy ne t'a pas vu bouger » : réessayer le GPS et continuer,
  comment faire, ou terminer quand même. Fin automatique et anti-oubli inchangés.
- Tests : `tests/e2e_v50.py` (faux GPS : refusé, muet, revenu ; Fini à 0 m) ; `e2e_accueil.py` / `e2e_v49.py` passent à 3.6.

## Version 3.9 « Croquette » (APP_NUM 51, décidé le 17–18/11 en Wouaf 6 : cadeaux et gains + trophées ; contient aussi la 3.8)
- 🥈 **Cadeau argenté 250** (`SILVER_CS`, `SILVER_CLOUD` = 350 m) : même principe que le trésor doré (un seul pour tous, **un seul gagnant**, nuage flou), mais **posé à la main par Éric**
  (Superviseur › Carte du superviseur › « 🥈 Cadeau argenté ici » ; « 🗑️ Retirer ») et qui **reste jusqu'à ce qu'on le trouve**. Worker : KV `spos` = `{ id, lat, lon, at }`
  (`POST /silver-set`, superviseur), `POST /silver-found` (public : `sv:<id>` = prénom du gagnant ; Éric testeur ne le prend jamais ; id inconnu = `gone`), renvoyé par `GET /pause`
  (`silver` avec `by`, comme `hpos`). App : `silverSrv` (`wouaf-silver`), `silverLive`, `silverCenter` (nuage décalé de 80–200 m, tiré avec l'id), `silverCheck` (dans `gameFix`, à < 40 m),
  `game.silver` = `{ id, found | gone }`, `gw.silver` / `res.silver` / `gx.sv` (hors plafond dans `game.bonus`, retiré par `applyVoid`), tuile 🥈 sur l'accueil (`data-lot="silver"`),
  `sheetSilver`, radar 🥈, flèche au bord = le nuage le plus proche (doré ou argenté), mini-carte et exploration (`openExplore("silver")`). Annuler la balade après l'avoir trouvé :
  `POST /alert` `kind:"silver"` → tableau de bord « Redonner 250 » (`/alert-resolve`). La remise à zéro efface `spos`, `sv:`.
- 🔥 **Coffre chaud = orange-rouge** (l'argent est réservé au cadeau argenté) : `FOG_ZONE.hot`, `hotCloud`, `.lt.fire`, `.trez.fire`, textes « nuage orange ».
- 💰 **Coffres à 100** (`CHEST_EUR` = 1 ; petits coffres 50 inchangés, budget `CHEST_MONTH` 6 €).
- 🦴 **Objets selon la cagnotte** (`objScale`, `objVal`) : si les gains du mois dépassent le rythme (`paceAllowed`), chaque objet vaut moitié moins (au moins 1, arrondi). La part « objets » du bonus
  (`gw.objPts` → `res.keep`) n'est plus coupée une 2e fois par `addMoney(eur, keepEur)`.
- 🌧️ **« Il pleut des billets »** remplace le bonus pluie ×1,5 (`rainMult` supprimé) : sous la pluie (météo du 1er point GPS), un billet 💶 tombe à 45–75 m devant soi tous les ~160–260 m de marche
  (`billsTick`, `BILL_CS` = 4, `BILL_MAX` = 8, vit `BILL_LIFE` = 4 min, ramassé à < 25 m, `gw.bills`, `gw.billGot` → `res.bills`), valeur ajustée à la cagnotte, ajoutée au bonus du jeu
  (donc dans le budget du mois). Pas en balade express. `res.rain` / `rn` partent avec `/walk` (trophée Courageux).
- Plus de « cadeaux du ciel au hasard » : il n'y en avait pas dans le code (rien à retirer) ; les futurs bonus iront sur les lieux (points d'intérêt).
- 🏆 **Trophées de Roxy du mois** (v3.8) : le Worker calcule, avec les chiffres déjà envoyés par balade (`pp cc nc m min rn du s`, 60 dernières balades par promeneur, Éric exclu),
  le gagnant de 9 trophées : 💩 Roi du Caca · 💧 Maître Arroseur · 🗺️ Explorateur · 🏃 Marathonien (km) · ⏱️ Patient (plus longue balade) · 🔥 Fidèle (jours de sortie ≥ 20 min) ·
  🌧️ Courageux (balades sous la pluie) · 🌅 Lève-tôt (départ avant 8 h) · 🤝 Sociable (balades à deux). Ex æquo = tous gagnants ; valeur 0 = pas de trophée. KV `hon:AAAA-MM`
  (`{ mk, t:{ id:{ w:[prénoms], v } }, fam:{ n walkers m min pp cc nc ob } }`), figé une fois le mois fini (`honorsAll`, aussi au cron) ; `GET /honors` (public, chiffres seulement).
  La remise à zéro efface `hon:`.
- 🎉 App : `honorsCard` = carte « Les trophées de Roxy · Novembre » en tête de la fenêtre d'ouverture le 1er du mois (une fois, `wouaf-hon-vu`, confettis), avec le **résumé drôle**
  (`funnyLines` : km comparés à `KM_PLACES`, cacas, pipis, minutes en films, rues neuves). ☰ › 🏆 **Palmarès** (`sheetPalmares`) : tableau d'honneur de l'année (nombre de trophées par promeneur,
  👑 en tête, couronne de l'année une fois l'année finie ; carte de décembre = « Couronne AAAA »), puis mois par mois. Résumé drôle aussi dans le journal de bord.
- Limite connue : les trophées ne s'appuient que sur les 60 dernières balades de chaque promeneur ; les premiers sont ceux de novembre (balades depuis la remise à zéro du 14/11), publiés le 1er décembre.
- Tests : `tests/v39.test.mjs` (Worker : cadeau argenté, alerte, trophées), `tests/e2e_v51.py` (navigateur). `e2e_v26.py` (attend « 3.4 ») et `e2e_duels.py` échouaient déjà avant.

## Version 3.9.1 « Croquette » (APP_NUM 52, décidé le 18/11 à 18 h 22 : rappel du récap oublié)
- 📩 **Récap pas envoyé au groupe « Roxy »** : la liste des récaps déjà partagés reste **sur le téléphone** (`wouaf-wa-sent`, clé `recapKey` = `s-e`, 80 max) ;
  `shareRecap` appelle `markSent` dès que le menu Partager aboutit (pas sur « Annuler »). 1re fois (`waSentList`) : toutes les balades déjà au carnet comptent comme envoyées.
- En fermant le récap sans l'avoir envoyé (`pendingRecap`, posé par `showRecapSheet`, testé dans `closeSheet`) → fiche « 📩 Tu as oublié le récap ! » (`recapNudge`) :
  « Envoyer maintenant » / « Plus tard » ; si une autre fenêtre est ouverte (record, coffre…), elle attend qu'elle se ferme (toutes les 1,5 s, 1 min max).
- À l'ouverture et au retour dans l'app : carte « Récap pas envoyé » dans le « Quoi de neuf » (`unsentCard`, `unsentRecaps` : mes balades ≥ 2 min des 3 derniers jours, pas annulées,
  3 max) avec un bouton « 📩 Envoyer » par balade et « Pas besoin ». Pas pour Éric (testeur). Toujours possible à la main : ☰ › Carnet / journal › la balade › « Renvoyer ».
- Tests : `tests/e2e_v52.py` ; `e2e.py` marque ses récaps comme envoyés (`markSent`) ; `e2e_v49.py` attend « 3.9.1 ».
