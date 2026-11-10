# Barre et espaces de travail

Ces commandes sont également disponibles directement dans les paramètres.

<!-- eitr-figure: bar-anatomy -->

La barre complète. Le logo Eitr ouvre le Centre de contrôle ; viennent ensuite Vue d’ensemble, les marqueurs d’espaces de travail, Utilisation IA, Matériel et Verrouillage automatique. La date et l’heure restent centrées, le multimédia avant elles et la météo après. **Afficher les icônes** affiche ou masque les icônes d’état à droite ; les notifications viennent en dernier.

Îlots présente des surfaces séparées pour le logo, la vue d’ensemble et les espaces de travail, Utilisation IA/Matériel/Verrouillage d’inactivité, l’horloge, la météo et les icônes d’état. Les indicateurs multimédias et de capture apparaissent uniquement lorsqu’ils sont actifs. L’horloge reste exactement centrée à l’écran ; la météo possède sa propre surface à côté.

Les surfaces sont toujours entièrement arrondies, quel que soit le réglage des coins, et suivent la couleur/transparence et le flou. Elles se placent à la moitié de l’espacement extérieur actuel de Hyprland du bord, avec l’espacement complet entre surfaces voisines, sur les quatre côtés. La zone réservée aux fenêtres inclut l’épaisseur et cette moitié ; le masquage automatique ne réserve rien.

Les intervalles laissent passer les clics. Les zones vides acceptent les gestes habituels de double clic et de glissement. Ouvrir un panneau fait grandir une carte depuis son îlot (vers le côté libre : la météo à droite, le multimédia et la capture à gauche, l’état vers le centre, l’horloge des deux côtés) et écarte les îlots voisins ; l’îlot reste caché sous la carte jusqu’à ce qu’elle ait rétréci.

Les icônes d’état gardent leur bouton manuel d’affichage/masquage.

Dans Paramètres > Fenêtres, la disposition et les moniteurs se choisissent avec deux boutons. Le nombre d’espaces et Toujours afficher utilisent des listes déroulantes ; Toujours afficher propose de 2 au nombre actuel d’espaces. Les descriptions expliquent chaque réglage, y compris la disposition choisie et les options de défilement.

## Mises à jour

L’icône des mises à jour, avant Notifications, vérifie peu après la connexion et toutes les six heures. Cliquez pour mettre à jour le système ; un clic droit relance la vérification. Une mise à jour réussie indique un système à jour jusqu’à la prochaine vérification, sans en lancer une aussitôt. Hors ligne ou en cas d’échec, l’état est indisponible, jamais faussement « à jour ». La vérification utilise une base privée et ne met aucun paquet à jour.

## Changer la disposition de la barre

- Double-cliquez à gauche sur un **espace vide de la barre** pour passer de Couleur du thème à Flou puis à Site web ; les nouvelles installations démarrent avec Couleur du thème. Site web utilise les couleurs du site d’Eitr, claires ou sombres selon le thème.
- Double-cliquez à droite sur un espace vide pour faire défiler Complète → Centrée → Onglets → Îlots → Dynamique → Complète.
- Faites glisser un espace vide vers le haut, le bas, la gauche ou la droite pour déplacer la barre. À gauche et à droite, la barre est aussi fine qu’en haut et en bas : l’horloge affiche l’heure au-dessus des minutes avec une icône de calendrier, et la météo seulement son icône ; survolez-les pour la date et la température.
- **Horloge** dans Paramètres > Barre de bureau affiche l’heure sur 12 heures avec AM/PM (par défaut) ou sur 24 heures, sur chaque bord.
- Les mêmes réglages figurent dans **Paramètres > Barre de bureau**, dans ses onglets Disposition, Aspect et Comportement.
- **Écrans** (Afficher sur) place la barre uniquement sur l’écran principal, par défaut, ou sur tous. Avec plusieurs barres, chacune indique l’espace de travail de son écran ; les raccourcis comme SUPER + I s’ouvrent sur l’écran utilisé et les notifications apparaissent uniquement sur le principal. Choisissez celui-ci dans le panneau Écran.

<!-- eitr-figure: bar-layouts -->

Les cinq dispositions dans l’ordre où le double clic droit les fait défiler. Au repos, Centrée n’affiche que l’horloge et Dynamique trois petits îlots ; les deux se déplient au survol.

Choisissez une disposition dans Paramètres > Barre de bureau. Les cinq fonctionnent sur chaque bord.

| Disposition | Comportement |
| :--- | :--- |
| Complète | Complète garde toute la barre au bord. Les panneaux s’y rattachent. |
| Centrée | Centrée montre seulement l’horloge avant le survol. L’épingle la garde ouverte ; les panneaux flottent à côté. |
| Onglets | Onglets relie trois onglets par une fine bande. Les icônes d’état restent visibles ; survolez le centre pour la météo. |
| Îlots | Îlots donne une capsule à chaque groupe et affiche toujours toutes les icônes d’état. Ouvrir un panneau agrandit son îlot et écarte les groupes voisins. |
| Dynamique | Dynamique commence par trois îlots : logo, horloge et réseau/batterie. Survolez-en un pour le déplier ; le panneau grandit depuis ce même îlot. |

## Espaces de travail

Dans Paramètres > Fenêtres > Espaces de travail (aussi Walker > Paramètres > Bureau > Fenêtres > Espaces de travail), choisissez **Moniteurs**, **Nombre d’espaces de travail** (5–10, 10 par défaut) et **Toujours afficher** (2 jusqu’au total, 5 par défaut). **Numéros partagés** donne à chaque moniteur ses propres espaces 1…N : SUPER+k change tous les moniteurs ensemble ; SUPER+Maj+k déplace la fenêtre sur son moniteur actuel, et tous les moniteurs passent avec elle à ce numéro. **Répartir entre les moniteurs** partage N également, écran principal en premier, auquel va d’abord le reste ; les autres suivent de gauche à droite puis par nom. SUPER+k active le moniteur concerné. Les touches au-delà de N sont inactives. Le minimum visible est relatif à la plage de chaque moniteur ; les marqueurs supérieurs apparaissent jusqu’à l’espace actuel ou occupé le plus élevé, puis disparaissent. Brancher, retirer ou changer l’écran principal recalcule la répartition sans perdre de fenêtres : elles rejoignent le numéro valide le plus proche sur leur moniteur. Avec un moniteur, les deux modes sont identiques.

Un clic droit sur un marqueur propose Points, Glyphe, Nombres ou Runes, avec exemples en direct. Runes est le choix par défaut et représente 1 à 10 par les dix premières runes du Futhark ancien (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ).

Le marqueur actif affiche le symbole dans la couleur d’accent, sans fond rempli. Les quatre choix tiennent dans le menu sur chaque bord de la barre, sans défilement.

**SUPER + 1–9/0** change d’espace ; **SUPER + Shift + 1–9/0** déplace une fenêtre. **SUPER + Tab** ouvre la Vue d’ensemble. Cliquez sur un aperçu ou utilisez flèches et Enter ; 1–9/0 change directement. Seuls les espaces numérotés occupés apparaissent et leurs aperçus restent en mémoire. Escape ou un clic à l’extérieur ferme la Vue d’ensemble.

**SUPER + S** bascule l’espace spécial, distinct de la Vue d’ensemble. **SUPER + Shift + Space** active ou désactive le masquage automatique de la barre ; si la barre a été masquée depuis le Centre de contrôle, il la réaffiche d’abord. Les notifications continuent de fonctionner.

Les gestes de souris pour fond d’écran et thème sur le bureau vide figurent dans **Apprendre > Gestes de la souris**. En cas de doute, utilisez les raccourcis des carrousels.

Le contrôle Audio/Micro ouvre un panneau avec des sections distinctes pour la sortie audio et le microphone. Tailscale et Streaming se trouvent juste avant OBS. Un interrupteur dans leur en-tête connecte Tailscale ou lance le partage, les détails et les appareils suivent, et les actions de configuration ou de diagnostic sont dans le menu « … ».

Le fond des boutons d’icône apparaît au survol ; les panneaux s’actualisent d’eux-mêmes à l’ouverture, une icône d’actualisation tourne seulement pendant le chargement et les infobulles apparaissent près du pointeur. Les interrupteurs et les boutons d’action intégrés utilisent des dimensions compactes communes.

**Visualiseur de musique** ouvre cava avec les couleurs du thème. Un clic droit sur l’égaliseur multimédia ouvre ce visualiseur ; le clic gauche ouvre toujours les détails multimédias. Appuyez sur **q** ou **Échap** pour le fermer. Si cava manque, il est installé au préalable.

**Masquage automatique**, dans Paramètres > Barre de bureau, rétracte la barre après un bref délai lorsque vous éloignez le pointeur. Placez-le au bord de l’écran pour la faire apparaître. Cela fonctionne sur les quatre bords avec les dispositions Complète, Centrée, Onglets et Îlots et Dynamique. Les panneaux et menus ouverts, ainsi que le déplacement de la barre, la gardent visible ; elle se masque à nouveau ensuite.

Tant que l’option est active, la barre ne réserve aucun espace aux fenêtres : elle glisse par-dessus au lieu de les déplacer. Ce réglage est enregistré indépendamment de l’épingle de la disposition centrée et reste désactivé à l’installation. Les notifications s’affichent sans la faire apparaître.

**Réduire les animations**, dans Paramètres > Barre de bureau, rend instantanés l’ouverture et la fermeture des panneaux, les entrées de la Vue d’ensemble, les transitions des notifications et les animations décoratives de la barre. Cette option est désactivée par défaut et enregistrée dans `bar-settings.json`. Les délais d’actualisation des données, d’expiration des notifications et de masquage automatique restent inchangés.

Le style multimédia est enregistré dans `bar-settings.json` : choisissez Barres (par défaut, dix barres) ou Ligne (une onde audio simple et lisse) dans Paramètres > Barre de bureau. L’indicateur précède les commandes, conserve une taille fixe dans chaque disposition et pivote sur les bords gauche et droit. Le survol affiche le titre ; le clic gauche ouvre les détails et le clic droit ouvre le visualiseur de musique. En pause, la ligne devient plate. Réduire les animations conserve les niveaux audio sans transition et arrête le mouvement décoratif de secours.

Le mode Centré rejoint le bord de l’écran avec des extrémités droites et les mêmes pentes à 45° légèrement arrondies que les onglets des deux côtés. Les pentes tournent avec la barre sur les quatre bords et ignorent le choix des coins ; les panneaux détachés respectent toujours ce choix.

## Dock d’applications

Touchez le bord opposé à la barre pour révéler le dock. Il se déplie depuis ce bord, ses côtés droits rejoignant le bord, au-dessus des fenêtres sans les redimensionner et se masque 350 ms après le départ du pointeur, avec une animation de 320 ms (instantanée avec Réduire les animations). Il apparaît sur l’écran principal, ou sur tous si la barre utilise tous les écrans. Il ne se révèle jamais au-dessus d’une fenêtre en plein écran.

Les applications ouvertes sont regroupées par classe, dans l’ordre des fenêtres de Hyprland. Les icônes occupent 36 px avec un espacement de 6 px et utilisent l’icône du bureau ou un symbole de secours ; les terminaux de tâches et de menus d’Eitr partagent une seule icône au logo d’Eitr.

Les points dessous comptent ses fenêtres, jusqu’à trois, et s’estompent quand aucune n’est sur l’espace actuel de cet écran. Survolez pour lire le nom et le nombre de fenêtres ; les icônes proches du pointeur grandissent, la plus proche davantage, et le dock s’allonge pour les garder à l’intérieur, sauf si **Réduire les animations** est activé.

Cliquez pour activer la fenêtre utilisée le plus récemment, en changeant d’espace si nécessaire ; un nouveau clic passe à sa fenêtre suivante. Le clic central ferme la fenêtre la plus récente. Les longues listes défilent dans l’axe du dock. La surface respecte Flou/Couleur du thème et le choix des coins.

**Dock** dans **Paramètres > Barre de bureau** l’active ou le désactive. Le réglage `dock` dans `bar-settings.json` vaut `"yes"` par défaut. Il n’y a pas de raccourci pour le dock.

Les applications épinglées restent entièrement opaques et sans points lorsqu’elles sont fermées ; cliquez pour les lancer dans leur propre scope d’application. Un clic droit propose Garder dans le Dock / Retirer du Dock, Nouvelle fenêtre (si une entrée de bureau existe) et Fermer ou Fermer toutes les fenêtres. Échap ou un clic à l’extérieur ferme le menu. Les applications sans entrée de bureau ne peuvent pas être épinglées.

Faites glisser les icônes le long du dock pour réordonner les applications épinglées. Glissez une application ouverte dans la section épinglée pour l’y garder, ou sortez une application de cette section pour la détacher. Les autres icônes libèrent la place avec une courte animation (instantanée avec Réduire les animations) ; les applications non épinglées conservent l’ordre des fenêtres de Hyprland. Un fin séparateur apparaît seulement si les deux sections contiennent des applications. Les menus et les déplacements maintiennent le dock visible.

Les IDs des entrées de bureau sont enregistrés dans l’ordre, par écriture atomique, dans le fichier local `quickshell/desktop-bar/dock-pins.json` sous `$XDG_CONFIG_HOME` (normalement `~/.config`). Les nouvelles installations n’ont aucune application épinglée. Les fenêtres sont associées par les IDs de bureau, StartupWMClass et les classes des applications.

L’intensité du flou est partagée avec les terminaux. Choisissez Doux, Moyenne (par défaut) ou Forte dans Barre du bureau de Walker ou dans les Paramètres (SUPER + ,). Consultez [Terminal et éditeurs](handbook:terminal) pour la limite globale et les réglages personnels.

Paramètres > Barre du bureau inclut les repères des espaces (points, glyphe, nombres et runes). Fenêtres conserve les effets et les espacements.
