# Thèmes, fonds d’écran et style

## Catalogue de thèmes et plugins

La barre latérale regroupe Thèmes et Plugins sous Installés et En obtenir plus,
avec leurs nombres. À droite, le
titre, la description et les filtres précèdent une liste à défilement indépendant.
Haut/Bas parcourt la barre ; Droite ou Tab entre dans le contenu. Gauche depuis
la première colonne revient à la barre. Sous 760 px, elle affiche des icônes avec
infobulles, sans titres de groupe ni texte.

Ouvrez **Paramètres > Style > Thèmes et plugins** ou **SUPER + F2**. Le catalogue est une fenêtre qui mémorise sa taille. Maintiens SUPER et fais glisser avec le bouton gauche pour la déplacer ou le bouton droit pour la redimensionner. Les raccourcis habituels permettent de la disposer en mosaïque ou de l’envoyer sur un autre espace de travail. La rouvrir active la fenêtre existante, même sur un autre espace. SUPER + F2 la ferme si elle est active. Son bouton de fermeture, Échap (après avoir fermé toute confirmation) ou le raccourci habituel de fermeture la ferment aussi. Installés affiche chaque thème comme Intégré, Officiel, Tiers ou Les vôtres.
La galerie affiche leurs aperçus. Cliquez sur un thème installé pour l’appliquer
avec le fonctionnement habituel ; une coche indique le thème actuel. Tous, Sombres
et Clairs filtrent la galerie. Installés se rafraîchit à l’ouverture et après chaque action. L’ouverture vérifie les métadonnées en arrière-plan et affiche ensuite les indicateurs de mise à jour. Aucune vérification réseau périodique ; Mettre à jour remplace un thème du catalogue.
Réappliquez un thème actif mis à jour pour actualiser le bureau. Supprimer demande
confirmation dans la fenêtre et refuse le thème actif : appliquez-en un autre d’abord.
Les thèmes intégrés et personnels sont conservés.

En obtenir plus affiche le dépôt officiel `eitr-org/eitr-themes`. Sélectionnez plusieurs
thèmes en cliquant sur leurs aperçus. La barre d’installation en bas ouvre la
vérification avec aperçus, source et taille totale ; Effacer vide la sélection.
Les flèches parcourent les cartes et Espace sélectionne les téléchargements. Entrée
applique un thème installé ou ouvre la vérification si des téléchargements sont
sélectionnés. Entrée ou Installer confirme ; Échap ferme d’abord la vérification,
puis la fenêtre. Téléchargements, progression et erreurs restent dans la
fenêtre. Les aperçus sont téléchargés uniquement pour les cartes visibles et utilisent
le cache utilisateur. Si le dépôt est inaccessible, Réessayer le recharge ; Installés
reste disponible hors ligne.

La page Plugins affiche les plugins installés et le dépôt officiel
`eitr-org/eitr-plugins` sous forme de cartes avec capture, icône centrée ou symbole
générique. Les badges indiquent les plugins installés et désactivés. La suppression
est confirmée dans la fenêtre. Pour installer, utilisez **Walker > Plugins**.
Installation et mises à jour utilisent encore les procédures de vérification
existantes ; le catalogue n’installe pas encore de plugins et n’accepte pas
d’adresses de dépôts tiers.

## Thèmes et fonds d’écran

Ouvrez **Paramètres > Style > Thème** ou **SUPER + Ctrl + Shift + N** pour les menus Sombre/Clair de Walker. Le carrousel de thèmes du bureau (double clic droit sur le bureau, Centre de contrôle > Style > Thème ou IPC appearance) affiche tous les thèmes. Le Soleil au-dessus de la carte sélectionnée n’affiche que les thèmes clairs et la Lune que les thèmes sombres ; un second clic sur celui qui est sélectionné les affiche tous à nouveau. Ctrl+Tab passe de tous aux sombres puis aux clairs. Saisissez du texte pour chercher parmi les thèmes affichés ; flèches/Tab déplacent la sélection, Enter l’applique. Backspace modifie la recherche ou ferme si elle est vide ; Escape efface la recherche avant de fermer. Le carrousel de fonds n’a pas de recherche de thèmes.

**SUPER + Ctrl + N** ouvre les fonds et **SUPER + Shift + N** passe au suivant. Une coche indique le choix actif dans Walker. Les changements n’affichent aucune notification de réussite. Les écrans ultrawide, au moins deux fois plus larges que hauts, utilisent la version 21:9 pour réduire le recadrage ; les autres utilisent la version 4K 16:9.

Eitr propose quatre fonds : Primordial Drop (par défaut), Runestone, Élivágar et Venom Rootlight. Utilisez les mêmes commandes de sélection ; la palette reste identique. Le deuxième fond, Runestone, est animé : les aurores se déplacent lentement derrière l’anneau de runes, se mettent à jour moins souvent derrière les fenêtres ordinaires, s’arrêtent derrière les applications plein écran et restent fixes sur le verrouillage. Le rendu logiciel (par exemple, une VM sans accélération 3D) utilise le fond fixe sélectionné ; il en va de même si le moteur de rendu ne peut pas être détecté. Graphite a été retiré ; les sélections Graphite enregistrées passent à Eitr et à son fond par défaut.

Les 25 thèmes fournis comprennent dix palettes sombres des royaumes : Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim et Vanaheim. Chaque thème des royaumes comprend de deux à cinq fonds originaux, dans des styles variés : encre, gouache, cel-shading et peinture, dans les deux formats. Le premier fond sert d’aperçu du thème.

Eitr Light est la variante claire de Primordial Venom, avec des surfaces vert pâle, du texte vert foncé, des accents jaune-vert de venin et des touches de jade/émeraude. Ses trois fonds fixes sont Primordial Drop, Élivágar et Venom Rootlight, chacun avec une composition panoramique distincte. Choisissez-le dans la catégorie Claire ; Eitr reste le thème par défaut. Fond du thème utilise l’image fixe sélectionnée sur l’écran de verrouillage.

Si Hyprpaper ne peut pas afficher le fond choisi, la barre dessine la même image fixe sur chaque écran concerné, y compris les variantes ultralarges. Les choix de fond et de thème restent appliqués en mode Focus ; cet affichage de secours change sans animation de dévoilement.

## Vos propres fonds d’écran, thèmes et écrans de verrouillage

Vos images, thèmes et écrans de verrouillage restent sur cet ordinateur, dans `~/.local/share/eitr/` (`wallpapers`, `themes` et `lockscreens`). Eitr ne les envoie ni ne les partage jamais, et les mises à jour ne les modifient jamais. Ils apparaissent à côté de ceux distribués, marqués **Le vôtre**, et eux seuls peuvent être supprimés : sélectionnez-en un, appuyez sur **Suppr**, puis Entrée pour confirmer ou Échap pour le garder.

- **Paramètres > Style > Fond d’écran > Ajouter mon fond d’écran** accepte un fichier image ou une adresse https. Les téléchargements s’arrêtent à 50 Mo, et Eitr n’en garde une copie qu’après avoir vérifié qu’il s’agit d’une image JPEG, PNG ou WebP. L’adresse d’une page web fonctionne si la page propose une image principale ; sinon, copiez l’adresse de l’image elle-même. L’image s’applique aussitôt et apparaît dans la liste des fonds d’écran, le carrousel et avec SUPER + Maj + N. Supprimer le fond d’écran utilisé passe d’abord au premier fond d’écran du thème. Choisissez si votre fond apparaît avec tous les thèmes ou seulement le thème actuel.
- **Paramètres > Style > Thème > Créer un thème** demande une image (le fond d’écran actuel, l’un des vôtres, l’un du thème, ou un autre fichier ou une adresse https), clair ou sombre (Automatique suit la luminosité de l’image) et un nom. Après le récapitulatif, Eitr crée une palette complète à partir de l’image, en gardant le texte bien lisible sur l’arrière-plan, et applique le thème à la barre, au terminal, au lanceur, aux applications et aux icônes. Une liste de couleurs suit : choisissez Accent, Arrière-plan, Texte ou l’une des six couleurs du terminal, saisissez six chiffres hexadécimaux, et la modification s’applique aussitôt ; Échap termine. **Ctrl + E** sur l’un de vos thèmes rouvre la liste. Supprimer le thème utilisé revient d’abord au thème utilisé avant sa création.
- **Paramètres > Style > Écran de verrouillage > Créer un écran de verrouillage** utilise le modèle Theme Wallpaper ou Material avec votre image, une couleur d’accent facultative et un message facultatif sous l’horloge, puis affiche un aperçu. Il se choisit comme n’importe quel modèle. L’écran de connexion ne peut pas lire votre dossier personnel : il affiche le même modèle, avec votre image pour Theme Wallpaper et l’image du modèle pour Material. Supprimer l’écran de verrouillage utilisé choisit d’abord son modèle.

## Barre et coins

**Paramètres > Style > Barre de bureau** choisit flou ou couleur du thème, disposition complète ou centrée et bord d’écran. Walker suit cette apparence. **Paramètres > Style > Coins** choisit des coins carrés, arrondis ou très arrondis pour les surfaces EITR et les décorations du compositeur. Les applications tierces peuvent garder leurs propres contrôles ; les points d’état circulaires restent ronds.

## Polices

**Paramètres > Style > Polices** liste les familles installées utilisables, pas chaque variante grasse ou italique. Les familles de documents et de remplacement restent masquées. JetBrainsMono Nerd Font est la police par défaut. La sélection actualise les applications compatibles ; les ligatures sont activées si possible. Supprimer une famille retire ses variantes installées compatibles ; le dernier choix utilisable ne peut pas être supprimé. Il peut être nécessaire de vérifier le paquet propriétaire.

## Curseur

**Paramètres > Style > Curseur** propose Bibata Modern, Breeze et Vanilla DMZ. Couleur propose automatique, sombre et clair ; Taille règle la taille du pointeur. Automatique suit la catégorie claire ou sombre du thème sans changer la famille choisie. Les couleurs fixées explicitement sont conservées. La ligne sélectionnée porte une coche à gauche ; les autres familles montrent des aperçus. Des ressources manquantes provoquent une erreur plutôt qu’un choix enregistré invalide.

Le menu de démarrage Limine utilise les couleurs du thème actuel, un titre EITR et une police plus grande. Les nouvelles installations le configurent ; après un changement de thème, il suit au prochain arrêt. Si votre thème est illisible, les couleurs par défaut sont utilisées. Les entrées de démarrage restent intactes et `limine.conf` est sauvegardé avant chaque modification. Le style n’est pas appliqué avec Secure Boot actif : modifier une configuration Limine dont l’empreinte est inscrite empêcherait le démarrage.

**Paramètres > Style > Écran de verrouillage** définit le verrouillage et l’écran de connexion. Les changements de thème conservent vos préférences.

Les modèles disponibles sont Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing et Theme Wallpaper. Vos propres écrans de verrouillage suivent ; les aperçus ne verrouillent pas la session. Un modèle retiré est remplacé par Clockwork Tape. Les nouvelles installations commencent avec Eitr.

Eitr affiche le mot-symbole EITR dans la couleur d’accent de votre thème, au centre de l’anneau de runes doré de l’écran de démarrage, qui avance chaque seconde, sur un ciel étoilé avec la Voie lactée, parfois une étoile filante, et l’aurore du bureau sur un noir pur (sur un écran OLED, ces pixels restent éteints). L’horloge affiche les heures et les minutes avec les chiffres nordiques propres à Eitr et suit le format 12 ou 24 heures. Chaque caractère saisi grave une rune dans le champ du mot de passe (toujours les mêmes runes, dans l’ordre, donc seule la longueur se voit) ; les flèches, Début et Fin déplacent le curseur bloc, et Retour arrière ou Suppr font s’effriter la rune voisine. Une authentification réussie déverrouille immédiatement la session. L’envoi du mot de passe, un échec de connexion et le changement de compte effacent les runes instantanément, sans les effriter. Réduire les animations fige tout et supprime les effets de gravure et d’effritement. Dans un aperçu, Entrée et Échap le ferment immédiatement sans rien déverrouiller.

Les images visent 4K (3840×2160, 16:9). Coffee et Pillow gardent leur style anime paisible avec des vêtements nordiques ; Material et Clockwork utilisent des ornements runiques discrets. Nothing garde son modèle. QML et SVG restent redimensionnables.

Comparez les neuf modèles avec `bash quickshell/lockscreen/scripts/gallery.sh`. Cela ne change pas le choix actuel ; l’authentification et les actions d’alimentation sont désactivées dans la galerie. Clockwork utilise du QML procédural ; Coffee, Pillow, Material et Nothing gardent leurs dispositions sous licence avec de nouvelles images et JetBrainsMono Nerd Font installée. Aucune vidéo ni police fournie séparément n’est nécessaire.

**Fond d’écran du thème** utilise le fond actuel, avec l’horloge en haut à gauche et la saisie du mot de passe en bas à droite. L’aperçu Walker montre l’image actuelle. Les changements suivants apparaissent au prochain verrouillage ou aperçu ; Ctrl+P montre l’ensemble sans verrouiller. L’écran de connexion ne peut pas lire votre dossier personnel. Il montre une copie qu’Eitr enregistre au choix de ce modèle puis à chaque changement de fond. Si elle manque, un autre fond du thème actuel ou le fond Eitr par défaut est utilisé.

Sur les PC avec plusieurs comptes, l’écran de connexion affiche l’utilisateur sélectionné. Cliquez sur la moitié gauche ou droite du sélecteur, ou utilisez Ctrl+Left / Ctrl+Right, pour choisir un autre compte ; Entrée envoie toujours le mot de passe et Échap conserve son comportement. Avec un seul compte, la présentation ne change pas. L’écran verrouillé affiche le nom réel de la session si disponible et accepte uniquement le mot de passe de ce compte. Changer d’utilisateur (Ctrl+Alt+U) ouvre la connexion SDDM en gardant la session initiale verrouillée. De retour dans la session verrouillée, cliquez une fois dans le champ du mot de passe avant de taper. Cette action apparaît seulement avec plusieurs comptes admissibles et si SDDM autorise le changement. Les aperçus et la galerie utilisent trois comptes fictifs sans authentification.

La barre latérale du catalogue permet de choisir Thèmes ou Plugins. L’onglet Officiel réunit les éléments intégrés et les dépôts Eitr ; Communauté affiche l’index communautaire. Installés affiche les éléments locaux et leur origine. Les cartes montrent les couleurs de la palette disponibles. Sélectionnez des thèmes, vérifiez leurs sources et la taille totale, puis installez-les ensemble. Les plugins communautaires sont répertoriés ; leur installation et l’ajout d’une adresse Git arriveront plus tard.

Supprimer un thème intégré le masque dans les sélecteurs de cette machine. Dans Installés, activez Afficher les thèmes masqués puis choisissez Restaurer. Eitr et le thème actuel ne peuvent pas être masqués. Supprimer un thème téléchargé efface le paquet installé.
