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
