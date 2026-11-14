# Wouaf Balades 2.0 — plan validé le 14/11 (attendre le « vas-y » de l'utilisateur)

1. **Superviseur « Éric », sans code** : le 1er téléphone qui prend le prénom Éric (sans tenir compte des accents ni des majuscules)
   le « réclame » auprès du Worker (`POST /claim`, jeton aléatoire gardé dans KV `admin` et sur le téléphone). Ensuite, les routes
   superviseur acceptent ce jeton **ou** `SUPERVISOR_CODE`. Le prénom Éric est refusé sur un autre téléphone. Le menu ☰ montre
   Pause, Jours bonus, Tableau de bord, Corriger, Restaurer, Annuler une balade et Tout remettre à zéro.
   Téléphone d'Éric = testeur : les balades marchent (objets, brouillard, récap), mais pas de tirelire, pas d'amendes, pas de rappels.
   Ses balades comptent quand même pour les dernières sorties et l'humeur de Roxy.
2. **Remise à zéro de tout le monde** : bouton avec double confirmation → `POST /reset` → KV `reset` = date ; le Worker efface
   d:, b:, a:, last, la liste des sorties récentes et le trésor. Chaque téléphone lit `reset` (avec `/pause`) à l'ouverture et, s'il est
   plus récent que `wouaf-reset-vu`, efface jeu, tirelire, carnet, traces, album photo (IndexedDB), envois en attente, digest…
   **On garde** le prénom, les rappels et la photo de Roxy (`wouaf-avatar`). Ensuite : `firstUse` = lendemain (les amendes
   repartent le lendemain), puis écran « 🎉 Wouaf Balades 2.0, tout repart de zéro ! » et le tuto. Si une balade est en cours,
   on attend sa fin.
3. **« version 2.0 »** affiché en bas (APP_NUM 34, avec un libellé « 2.0 »).
4. **Trésor de la semaine** : à 2–3 km de la maison (au lieu de 0,9–1,8 km), **un seul gagnant** : le 1er reçoit 500 clebsous
   **en plus du plafond** (comme les coffres), puis le trésor disparaît pour tout le monde (Worker `POST /treasure` renvoie
   « déjà trouvé ») et les autres voient « 🏴‍☠️ X a trouvé le trésor ! ». Plus de +20 pour les suivants. ⭐ et objets inchangés.
5. **Annuler une balade** depuis le tableau de bord, avec un motif → `POST /void` (KV a:<prénom>, type void, id = fin de la balade).
   Le téléphone retire tous les gains de la balade (durée, bonus, défi, trésor, coffre ; `game.money`/`bonus`/`total`), la marque
   « ❌ annulée » dans le carnet et les sorties, ne la compte plus pour la série et la semaine parfaite. Si c'était la seule balade
   ≥ 20 min ce jour-là : amende −30 **sans joker**. Message du superviseur à l'ouverture. La balade apparaît barrée dans le tableau de bord.

Ensuite : tests (Playwright + Node pour le Worker), mise à jour de CLAUDE.md, commit et mise en ligne. Prévenir Éric de taper son
prénom avant que les ados ouvrent l'app.
