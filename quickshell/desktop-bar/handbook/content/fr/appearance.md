# Thèmes, fonds d’écran et style

Ces commandes sont également disponibles directement dans les paramètres.

Les paramètres (**SUPER + ,**) incluent les réglages d’apparence ; **Plus de thèmes** ouvre le catalogue séparé des Modules complémentaires (**SUPER + F2**).

## Disposition des fenêtres

Choisis **Mosaïque** (par défaut, dwindle de Hyprland) ou **Défilement** dans **Paramètres > Fenêtres > Disposition des fenêtres** ou **Walker > Paramètres > Bureau > Fenêtres > Disposition des fenêtres**. Défilement place les fenêtres en colonnes sur un ruban mobile. Le choix est enregistré localement et persiste après les changements de thème, rechargements et redémarrages ; il recharge la configuration du compositeur sans redémarrer la session.

Défilement affiche Direction (Droite, Gauche, Bas, Haut), Largeur de colonne par défaut (Un tiers, Moitié, Deux tiers, Pleine) et Ajustement du focus. Centrer centre la colonne active ; Ajuster la rend visible avec un déplacement minimal. Suivre le focus autorise le ruban à suivre les changements de focus, y compris les clics. Plein écran avec une seule colonne permet à une colonne unique de remplir l’écran sans activer le plein écran de l’application. Valeurs par défaut : Droite, Moitié, Ajuster et les deux interrupteurs activés. Les options restent enregistrées en revenant à Mosaïque. Le menu Disposition des fenêtres de Walker propose chacune en sous-menu.

Uniquement en Défilement : **SUPER + ALT + flèches** change le focus ; **SUPER + ALT + SHIFT + Gauche/Droite** échange les colonnes ; **SUPER + ALT + Equal/Minus** alterne entre un tiers, la moitié, deux tiers et la pleine largeur. Le cycle redimensionne la colonne active ; la largeur par défaut s’applique aux nouvelles colonnes. Voir la [référence clavier](handbook:shortcuts).


## Catalogue de Modules complémentaires

Le catalogue partage le cadre, la barre latérale, l’en-tête de page et les cartes
de la fenêtre des Paramètres. Il suit les couleurs du thème, ou la palette du site
web Eitr lorsque les Paramètres la choisissent, avec la police Cinzel incluse.

La barre latérale liste Installé, Officiel et Communauté sous Thèmes et sous
Plugins. À droite figurent le titre, la description, le filtre Toutes, Clair et
Sombre pour les thèmes et une galerie à défilement indépendant. Haut/Bas parcourt
la barre ; Droite ou Tab entre dans le contenu. Gauche depuis la première colonne
revient à la barre latérale.

Ouvrez **Plus de thèmes** dans Paramètres > Apparence > Thème et fond d’écran ou appuyez sur **SUPER + F2**. Modules complémentaires est une fenêtre séparée. Voir [Paramètres](handbook:system) pour la navigation.

Le catalogue est une fenêtre qui mémorise sa taille. Maintiens SUPER et fais glisser avec le bouton gauche pour la déplacer ou le bouton droit pour la redimensionner. Les raccourcis habituels permettent de la disposer en mosaïque ou de l’envoyer sur un autre espace de travail. La rouvrir active la fenêtre existante, même sur un autre espace.

SUPER + F2 la ferme si elle est active. Son bouton de fermeture, Échap (après avoir fermé toute confirmation) ou le raccourci habituel de fermeture la ferment aussi. Installés affiche chaque thème comme Intégré, Officiel, Tiers ou Les vôtres. La galerie affiche leurs aperçus. Cliquez sur un thème installé pour l’appliquer
avec le fonctionnement habituel ; une coche indique le thème actuel.

Tous, Sombres
et Clairs filtrent la galerie. Installés se rafraîchit à l’ouverture et après chaque action. L’ouverture vérifie les métadonnées en arrière-plan et affiche ensuite les indicateurs de mise à jour. Aucune vérification réseau périodique ; Mettre à jour remplace un thème du catalogue ; Tout mettre à jour, à côté d’Ajouter, met à jour tour à tour chaque thème signalé et, pour les extensions, ouvre la revue de chaque mise à jour l’une après l’autre. Réappliquez un thème actif mis à jour pour actualiser le bureau.

Supprimer demande
confirmation dans la fenêtre et refuse le thème actif : appliquez-en un autre d’abord. Les thèmes intégrés et personnels sont conservés.

Officiel réunit les thèmes intégrés et le dépôt `eitr-org/eitr-themes` ;
Communauté affiche les thèmes communautaires. Cliquez sur une carte de ces onglets
pour ouvrir ses détails : aperçu, description, palette (survolez pour les valeurs
hexadécimales), source, taille, responsable et licence. Les fonds apparaissent en
miniatures ; ceux de la communauté utilisent des cartes avec nom et taille.

Cliquez pour agrandir, utilisez Précédent/Suivant pour parcourir et Retour pour
revenir. Échap, le bouton de fermeture ou un clic à l’extérieur ferme les détails
et rend le focus à la carte. Les fonds distants complets sont téléchargés seulement
à l’ouverture ; les images installées sont lues localement.

Installer sur la carte bascule la sélection et affiche Sélectionné avec une coche. Les cartes installées affichent Installé et Actuel si nécessaire. Sélectionnez
plusieurs thèmes, puis utilisez Vérifier et installer dans la fenêtre contextuelle sous les cartes pour vérifier
aperçus, sources et taille totale ; Effacer vide la sélection. Les flèches naviguent,
Espace bascule la sélection et Entrée ouvre les détails dans Officiel ou Communauté.

Avec Tab, atteignez Vérifier et installer dans cette fenêtre contextuelle, puis Entrée ouvre la
vérification. Entrée applique toujours un thème dans Installés et confirme une
vérification ouverte. Installer dans les détails vérifie uniquement ce thème ;
après installation, Appliquer ou Actuel apparaît. Échap annule d’abord la
vérification, puis ferme les détails ou la fenêtre.

Téléchargements, progression
et erreurs restent dans la fenêtre. Aperçus visibles et galeries ouvertes utilisent
le cache. Si le dépôt est inaccessible, Réessayer le recharge ; Installés reste
disponible hors ligne.

Les tailles des fonds communautaires absents du cache affichent Taille indisponible
jusqu’à l’ouverture : Git téléchargerait tout le fichier pour les connaître. Les tailles en cache sont affichées.

La page Plugins affiche les plugins installés et le dépôt officiel
`eitr-org/eitr-plugins` sous forme de cartes avec capture, icône centrée ou symbole
générique. Les badges indiquent les plugins installés et désactivés. La suppression
est confirmée dans la fenêtre.

Le catalogue installe et met à jour les plugins dans la fenêtre. Les cartes Officiel et Communauté ouvrent les détails avec images, vidéos et composants. Les vidéos démarrent sans son et s’arrêtent à la fermeture. Installer et Mettre à jour présentent source, commit complet, auteur, fichiers, commandes, avertissements et changements ; la vérification facultative par IA apparaît sous forme de texte.

Les plugins disposent de toutes les permissions du compte. Entrée confirme et Échap annule. Le commit installé est exactement celui vérifié ; Communauté utilise le commit fixé dans l’index. La vérification expire après 15 minutes et est supprimée à la fermeture du catalogue. Installés > Ajouter depuis une adresse Git accepte HTTPS ou SSH pour les plugins et les thèmes de données, sans terminal.

Les thèmes intégrés font partie d’Eitr et ne peuvent pas être supprimés. La corbeille d’un thème téléchargé efface son paquet installé ; le thème actuel ne peut pas être supprimé.

Tapez n’importe où dans le catalogue, ou appuyez sur Ctrl+F ou /, pour chercher dans la page actuelle par nom ou description. Les mots peuvent être dans n’importe quel ordre ; Échap efface d’abord la recherche.


### Écrans de verrouillage dans Modules complémentaires

Ouvrez **Modules complémentaires > Écrans de verrouillage > Officiel** pour installer des modèles depuis le dépôt de paquets signés d’Eitr. L’installation et la suppression demandent le mot de passe administrateur dans la fenêtre Eitr. **Installé** affiche les modèles installés ; choisissez le modèle à utiliser dans **Paramètres > Écran de verrouillage** ou Walker. **Eitr** est intégré et ne peut pas être supprimé. Le modèle utilisé par la session ou la connexion porte le badge **Actuel** et n’a pas de corbeille. Vos écrans basés sur un modèle désinstallé sont masqués, jamais supprimés, et reviennent après sa réinstallation. System Update installe les huit paquets optionnels une seule fois ; les nouvelles installations les incluent aussi. Les suppressions ultérieures sont conservées.


## Choisir thème et fond d’écran

Choisissez thème et fond dans Paramètres > Apparence > Thème et fond d’écran. Pour les menus Sombre/Clair de Walker, utilisez **Walker > Paramètres > Bureau > Apparence > Thème** ou **SUPER + Ctrl + Shift + N**. Un double clic droit sur le bureau vide ouvre le carrousel. Le Soleil filtre les thèmes clairs, la Lune les sombres ; recliquez le filtre actif pour tout afficher.

Le + ouvre le catalogue séparé avec le même filtre. Ctrl+Tab parcourt les filtres, taper cherche, flèches/Tab déplacent et Entrée applique. Backspace corrige la recherche, jusqu’à la vider ; Échap l’efface avant de fermer.

**SUPER + Ctrl + N** ouvre les fonds et **SUPER + Shift + N** passe au suivant. Une coche indique le choix actif dans Walker. Les changements n’affichent aucune notification de réussite. Les écrans ultrawide, au moins deux fois plus larges que hauts, utilisent la version 21:9 pour réduire le recadrage ; les autres utilisent la version 4K 16:9.

Eitr propose quatre fonds : Fjord des aurores (par défaut), Fjord au crépuscule, Rune Seal et Runestone. Utilisez les mêmes commandes de sélection ; la palette reste identique. Le quatrième fond, Runestone, est animé : les aurores se déplacent lentement derrière l’anneau de runes, se mettent à jour moins souvent derrière les fenêtres ordinaires, s’arrêtent derrière les applications plein écran et restent fixes sur le verrouillage.

Le rendu logiciel (par exemple, une VM sans accélération 3D) utilise le fond fixe sélectionné ; il en va de même si le moteur de rendu ne peut pas être détecté. Graphite a été retiré ; les sélections Graphite enregistrées passent à Eitr et à son fond par défaut.

Les 13 thèmes intégrés restent disponibles hors ligne. Installez les 14 thèmes supplémentaires, dont les thèmes clairs Freyja et Skaði, depuis le catalogue officiel `eitr-org/eitr-themes`. Les comptes existants ont reçu les 12 premiers en arrière-plan, avec de nouvelles tentatives après un échec réseau, sans changer le thème actuel ni le fond enregistré. Les nouveaux comptes reçoivent seulement les thèmes intégrés.

Les 13 thèmes fournis comprennent dix palettes sombres des royaumes : Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim et Vanaheim. Chaque thème des royaumes comprend de deux à cinq fonds originaux, dans des styles variés : encre, gouache, cel-shading et peinture, dans les deux formats. Le premier fond correspond généralement à l’aperçu du thème ; Svartalfheim conserve son aperçu indépendant.

Eitr Light est la variante claire de Primordial Venom, avec des surfaces vert pâle, du texte vert foncé, des accents jaune-vert de venin et des touches de jade/émeraude. Ses quatre fonds fixes sont Fjord au crépuscule (par défaut), The Gates of Yggdrasil, Rune Seal et Primordial Drop, chacun avec une composition panoramique distincte. Choisissez-le dans la catégorie Claire ; Eitr reste le thème par défaut. Fond du thème utilise l’image fixe sélectionnée sur l’écran de verrouillage.

Si Hyprpaper ne peut pas afficher le fond choisi, la barre dessine la même image fixe sur chaque écran concerné, y compris les variantes ultralarges. Les choix de fond et de thème restent appliqués en mode Focus ; cet affichage de secours change sans animation de dévoilement.

## Vos propres fonds d’écran, thèmes et écrans de verrouillage

Vos images, thèmes et écrans de verrouillage restent sur cet ordinateur, dans `~/.local/share/eitr/` (`wallpapers`, `themes` et `lockscreens`). Eitr ne les envoie ni ne les partage jamais, et les mises à jour ne les modifient jamais. Ils apparaissent à côté de ceux distribués, marqués **Le vôtre**, et eux seuls peuvent être supprimés : sélectionnez-en un, appuyez sur **Suppr**, puis Entrée pour confirmer ou Échap pour le garder.

- **Walker > Paramètres > Bureau > Apparence > Fond d’écran > Ajouter mon fond d’écran** accepte un fichier image ou une adresse https. Les téléchargements s’arrêtent à 50 Mo, et Eitr n’en garde une copie qu’après avoir vérifié qu’il s’agit d’une image JPEG, PNG ou WebP. L’adresse d’une page web fonctionne si la page propose une image principale ; sinon, copiez l’adresse de l’image elle-même. L’image s’applique aussitôt et apparaît dans la liste des fonds d’écran, le carrousel et avec SUPER + Maj + N. Supprimer le fond d’écran utilisé passe d’abord au premier fond d’écran du thème. Choisissez si votre fond apparaît avec tous les thèmes ou seulement le thème actuel.
- **Walker > Paramètres > Bureau > Apparence > Thème > Créer un thème** demande une image (le fond d’écran actuel, l’un des vôtres, l’un du thème, ou un autre fichier ou une adresse https), clair ou sombre (Automatique suit la luminosité de l’image) et un nom. Après le récapitulatif, Eitr crée une palette complète à partir de l’image, en gardant le texte bien lisible sur l’arrière-plan, et applique le thème à la barre, au terminal, au lanceur, aux applications et aux icônes. Une liste de couleurs suit : choisissez Accent, Arrière-plan, Texte ou l’une des six couleurs du terminal, saisissez six chiffres hexadécimaux, et la modification s’applique aussitôt ; Échap termine. **Ctrl + E** sur l’un de vos thèmes rouvre la liste. Supprimer le thème utilisé revient d’abord au thème utilisé avant sa création.
- **Walker > Paramètres > Bureau > Écran de verrouillage > Créer un écran de verrouillage** utilise le modèle Theme Wallpaper ou Material avec votre image, une couleur d’accent facultative et un message facultatif sous l’horloge, puis affiche un aperçu. Il se choisit comme n’importe quel modèle. L’écran de connexion ne peut pas lire votre dossier personnel : il affiche le même modèle, avec votre image pour Theme Wallpaper et l’image du modèle pour Material. Supprimer l’écran de verrouillage utilisé choisit d’abord son modèle.

## Changer la disposition de la barre

**Paramètres > Barre de bureau** choisit disposition, position et apparence ; voir [Barre de bureau](handbook:desktop-bar). **Paramètres > Fenêtres > Coins** choisit Carrés, Arrondis ou Très arrondis. Espacement des fenêtres et Réduire les animations figurent sur la même page Fenêtres. Les applications tierces peuvent garder leur style interne.

<!-- eitr-figure: window-style -->

Espacement des fenêtres et Coins tels que **Paramètres > Fenêtres** les montre, avec vos choix actuels cochés. Par défaut, 6 px séparent les fenêtres et 12 px les bords de l’écran.

Dans **Paramètres > Fenêtres > Espacement des fenêtres** ou **Walker > Paramètres > Bureau > Fenêtres > Espacement des fenêtres**, choisissez Aucun, Petit, Moyen (par défaut) ou Grand. Le choix local résiste aux changements de thème et aux rechargements.

## Changer les polices

Choisissez une police installée dans Paramètres > Apparence > Polices et curseur. JetBrainsMono Nerd Font est la valeur par défaut. Le choix actualise les applications compatibles ; certaines conservent leurs propres réglages. Pour supprimer une famille, utilisez Walker > Paramètres > Bureau > Apparence > Polices et vérifiez ses paquets. La dernière famille utilisable ne peut pas être supprimée.

## Changer le pointeur

Ouvrez Paramètres > Apparence > Polices et curseur. Famille du pointeur choisit Bibata Modern, Breeze ou Vanilla DMZ. Couleur du pointeur propose Automatique, Sombre ou Clair ; Automatique suit le thème sans changer la famille. Taille du pointeur ajuste sa taille. Les choix explicites de couleur et de taille résistent aux changements de thème. La page montre le pointeur sélectionné si ses fichiers sont disponibles.

## Choisir un écran de verrouillage

**Paramètres > Écran de verrouillage** définit le verrouillage et l’écran de connexion. Les changements de thème conservent vos préférences.

Les modèles disponibles sont Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing et Theme Wallpaper. Vos propres écrans de verrouillage suivent ; les aperçus ne verrouillent pas la session. Un modèle retiré est remplacé par Clockwork Tape. Les nouvelles installations commencent avec Eitr.

Eitr affiche le mot-symbole EITR dans la couleur d’accent de votre thème, au centre de l’anneau de runes doré de l’écran de démarrage, qui avance chaque seconde, sur un ciel étoilé avec la Voie lactée, parfois une étoile filante, et l’aurore du bureau sur un noir pur (sur un écran OLED, ces pixels restent éteints).

L’horloge affiche les heures et les minutes avec les chiffres nordiques propres à Eitr et suit le format 12 ou 24 heures. Chaque caractère saisi grave une rune dans le champ du mot de passe (toujours les mêmes runes, dans l’ordre, donc seule la longueur se voit) ; les flèches, Début et Fin déplacent le curseur bloc, et Retour arrière ou Suppr font s’effriter la rune voisine.

Une authentification réussie déverrouille immédiatement la session. L’envoi du mot de passe, un échec de connexion et le changement de compte effacent les runes instantanément, sans les effriter. Réduire les animations fige tout et supprime les effets de gravure et d’effritement. Dans un aperçu, Entrée et Échap le ferment immédiatement sans rien déverrouiller.

Les images visent 4K (3840×2160, 16:9). Coffee et Pillow gardent leur style anime paisible avec des vêtements nordiques ; Material et Clockwork utilisent des ornements runiques discrets. Nothing garde son modèle. QML et SVG restent redimensionnables.

Comparez les neuf modèles avec `bash quickshell/lockscreen/scripts/gallery.sh`. Cela ne change pas le choix actuel ; l’authentification et les actions d’alimentation sont désactivées dans la galerie. Clockwork utilise du QML procédural ; Coffee, Pillow, Material et Nothing gardent leurs dispositions sous licence avec de nouvelles images et JetBrainsMono Nerd Font installée. Aucune vidéo ni police fournie séparément n’est nécessaire.

**Fond d’écran du thème** utilise le fond actuel, avec l’horloge en haut à gauche et la saisie du mot de passe en bas à droite. L’aperçu Walker montre l’image actuelle. Les changements suivants apparaissent au prochain verrouillage ou aperçu ; Ctrl+P montre l’ensemble sans verrouiller. L’écran de connexion ne peut pas lire votre dossier personnel. Il montre une copie qu’Eitr enregistre au choix de ce modèle puis à chaque changement de fond. Si elle manque, un autre fond du thème actuel ou le fond Eitr par défaut est utilisé.

Sur les PC avec plusieurs comptes, l’écran de connexion affiche l’utilisateur sélectionné. Cliquez sur la moitié gauche ou droite du sélecteur, ou utilisez Ctrl+Left / Ctrl+Right, pour choisir un autre compte ; Entrée envoie toujours le mot de passe et Échap conserve son comportement. Avec un seul compte, la présentation ne change pas.

Avec plusieurs écrans, l’écran de connexion n’apparaît que sur le plus grand ; les autres restent noirs.

L’écran verrouillé affiche le nom réel de la session si disponible et accepte uniquement le mot de passe de ce compte. Changer d’utilisateur (Ctrl+Alt+U) ouvre la connexion SDDM en gardant la session initiale verrouillée. De retour dans la session verrouillée, cliquez une fois dans le champ du mot de passe avant de taper.

Cette action apparaît seulement avec plusieurs comptes admissibles et si SDDM autorise le changement. Les aperçus et la galerie utilisent trois comptes fictifs sans authentification.

## Notes techniques

Le menu de démarrage Limine utilise les couleurs du thème actuel, un titre EITR et une police plus grande. Les nouvelles installations le configurent ; après un changement de thème, il suit au prochain arrêt. Si votre thème est illisible, les couleurs par défaut sont utilisées. Les entrées de démarrage restent intactes et `limine.conf` est sauvegardé avant chaque modification. Le style n’est pas appliqué avec Secure Boot actif : modifier une configuration Limine dont l’empreinte est inscrite empêcherait le démarrage.

## Aperçus et affectations des fonds

Dans Paramètres > Apparence > Thème et fond, cliquez sur une image pour afficher son image fixe sur le bureau. Appliquer l’enregistre ; Annuler l’aperçu, changer de page ou fermer rétablit le choix enregistré. La palette reste inchangée. Walker > Paramètres > Bureau > Apparence > Fond ouvre le carrousel sur l’image choisie. Les flèches prévisualisent, Entrée applique, Échap ou un clic à l’extérieur annule.

Au-dessus des fonds du carrousel, **Ce thème** et **Tous les thèmes** basculent entre les fonds du thème actuel et ceux de tous les thèmes installés (Ctrl+Tab aussi). Le nom de chaque fond s’affiche dessous (avec tous les thèmes, aussi son thème d’origine), et la saisie cherche dans les noms et les thèmes ; vos propres images viennent en dernier. En choisir un change seulement le fond ; les couleurs du thème restent.

Fond par écran dans Paramètres > Apparence > Thème et fond (ou Walker > Paramètres > Bureau > Apparence > Fond par écran) est désactivé par défaut : choisir ou prévisualiser un fond change tous les écrans. Activez-le pour ne changer que l’écran utilisé au moment du choix. Un écran sans choix propre utilise le fond global.

Les affectations et l’interrupteur restent locaux. Le désactiver rétablit immédiatement le fond global partout tout en conservant les choix par écran ; le réactiver les restaure. La connexion et la reconnexion restaurent chaque sortie séparément. Changer de thème efface tous les choix par écran, conserve l’interrupteur et utilise le fond du nouveau thème. Choisir seulement un fond conserve les choix par écran. Les fichiers indisponibles sont retirés des affectations. L’animation Runestone reprend après l’aperçu ; le rendu logiciel utilise la même image fixe.
