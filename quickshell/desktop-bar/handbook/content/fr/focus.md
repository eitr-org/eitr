# Focus

![Bande d’onglets Focus avec des fenêtres d’exemple et deux volets reliés.](assets/focus-strip.png)

Focus remplace la barre par une bande d’onglets de 28 px en haut de chaque écran.
Ouvrez **Style > Focus** ou **Centre de contrôle > Style > Focus**, ou lancez
`eitr focus on`. `eitr focus status` affiche `on` ou `off` sans contacter Hyprland.
`eitr focus off` restaure la barre, les effets et les raccourcis habituels. Aucun
raccourci dédié ne bascule ce mode.

La préférence est dans `~/.config/eitr/focus.json` (sous `$XDG_CONFIG_HOME` si défini).
Elle résiste aux redémarrages, mises à jour et changements de thème. Les réglages
de la barre normale restent séparés et ne sont jamais remplacés.

## Onglets et volets

Les fenêtres ouvertes, flottantes ou sur l’espace spécial compris, sont réunies
en groupes natifs Hyprland. Un groupe remplit l’écran sous la bande. Espacements,
bordures, coins arrondis, flou, ombres et animations sont désactivés. La bande suit
le thème et garde des extrémités carrées comme la disposition Onglets. Elle affiche
uniquement titres, horloge et état réseau/batterie. La batterie apparaît seulement
avec une batterie système. Les titres longs sont abrégés ; une longue liste défile.
L’onglet surligné identifie la fenêtre active. Des lignes d’accent relient les volets
visibles d’une division. Les applications peuvent garder leur style interne.

- **SUPER + 1–9** choisit l’onglet 1–9 de l’écran actif.
- **SUPER + Tab / SUPER + Shift + Tab** choisit l’onglet suivant/précédent.
- **SUPER + backslash** sépare le groupe et son onglet suivant côte à côte.
- **SUPER + minus** place cet onglet dessous.
- **SUPER + H/J/K/L** active le volet gauche/bas/haut/droite.
- **SUPER + Shift + H/J/K/L** réduit la largeur/augmente la hauteur/réduit la hauteur/augmente la largeur, comme sur le bureau normal.
- **SUPER + Shift + backslash** ramène la fenêtre active dans un groupe d’onglets plein écran en réunissant tous les volets dans les onglets.

Il faut un autre onglet dans le groupe actif pour diviser. Quatre volets maximum :
deux sont côte à côte ou empilés ; trois ou quatre utilisent une grille 2×2 (le
troisième remplit la ligne inférieure jusqu’à l’ajout du quatrième). Redimensionner
ajuste les séparateurs partagés. Le raccourci de retour restaure un groupe plein écran en une seule pression. Les numéros suivent l’ordre des fenêtres du compositeur, aussi utilisé par
la bande. Les raccourcis des espaces de travail, du flottement, du déplacement et
de la visibilité de la barre sont inactifs. Lanceurs, fermeture de fenêtre, Centre
de contrôle et Manuel restent accessibles. Apprendre > Raccourcis affiche les
touches Focus quand ce mode est actif.

## Écrans et récupération

Chaque écran a ses fenêtres, sa bande et jusqu’à quatre volets. Les raccourcis
d’onglets agissent sur l’écran actif ; la navigation directionnelle peut passer
sur un autre écran si aucun volet n’existe dans cette direction. Brancher un écran
crée sa bande ; le débrancher déplace ses fenêtres vers un écran disponible où
Focus les réunit. Le choix d’écrans de la barre normale ne limite pas les bandes.

Désactiver Focus dissout les groupes et répartit les fenêtres dans des espaces
numérotés, deux par espace, en gardant leurs écrans actuels. Les anciennes positions,
la géométrie flottante et les états plein écran des applications ne sont pas gardés.
Un bureau vide et des commandes on/off répétées sont pris en charge. Si le processus
de la bande plante, les groupes natifs et le clavier fonctionnent toujours. Lancez
`eitr focus off` dans un terminal pour récupérer le bureau sans la bande. Recharger
Hyprland réapplique la préférence et réunit les nouvelles fenêtres sans dissoudre
les divisions ; les tailles des séparateurs et l’orientation de deux volets sont
réinitialisées. Un échec affiche son erreur ; réessayez `eitr focus off` quand
Hyprland est accessible. Fermer un volet agrandit les volets restants.
