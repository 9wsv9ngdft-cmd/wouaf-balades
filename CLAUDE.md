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

## Méthode de travail
- On discute d'abord avec l'utilisateur, puis une seule série de modifications une fois validé. Toujours au plus simple.
