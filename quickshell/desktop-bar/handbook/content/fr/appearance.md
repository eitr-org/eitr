# Thèmes, fonds d’écran et style

## Thèmes et fonds d’écran

Ouvrez **Style > Thème** ou **SUPER + Ctrl + Shift + N**. Choisissez sombre ou clair, puis un thème. Saisissez du texte dans le carrousel de thèmes pour filtrer ; flèches ou Tab déplacent la sélection, Enter l’applique. Backspace modifie d’abord la recherche ; Escape l’efface avant de fermer. Le choix de catégorie et le carrousel de fonds n’ont pas de recherche de thèmes.

**SUPER + Ctrl + N** ouvre les fonds et **SUPER + Shift + N** passe au suivant. Une coche indique le choix actif dans Walker. Les changements n’affichent aucune notification de réussite. Les écrans ultrawide, au moins deux fois plus larges que hauts, utilisent la version 21:9 pour réduire le recadrage ; les autres utilisent la version 4K 16:9.

Norse comprend des dessins de corbeau, Valkyrie, Odin, Fenrir et Jörmungandr sur fond noir. Utilisez les mêmes commandes de sélection ; ces images supplémentaires ne changent pas la palette. Le premier fond, la pierre runique, est animé : des aurores se déplacent lentement derrière l’anneau de runes. Elles s’arrêtent derrière les applications plein écran ; le verrouillage montre l’image fixe.

## Barre et coins

**Style > Barre de bureau** choisit flou ou couleur du thème, disposition complète ou centrée et bord d’écran. Walker suit cette apparence. **Style > Coins** choisit des coins carrés, arrondis ou très arrondis pour les surfaces EITR et les décorations du compositeur. Les applications tierces peuvent garder leurs propres contrôles ; les points d’état circulaires restent ronds.

## Polices

**Style > Polices** liste les familles installées utilisables, pas chaque variante grasse ou italique. Les familles de documents et de remplacement restent masquées. JetBrainsMono Nerd Font est la police par défaut. La sélection actualise les applications compatibles ; les ligatures sont activées si possible. Supprimer une famille retire ses variantes installées compatibles ; le dernier choix utilisable ne peut pas être supprimé. Il peut être nécessaire de vérifier le paquet propriétaire.

## Curseur

**Style > Curseur** propose Bibata Modern, Breeze et Vanilla DMZ. Couleur propose automatique, sombre et clair ; Taille règle la taille du pointeur. Automatique suit la catégorie claire ou sombre du thème sans changer la famille choisie. Les couleurs fixées explicitement sont conservées. La ligne sélectionnée porte une coche à gauche ; les autres familles montrent des aperçus. Des ressources manquantes provoquent une erreur plutôt qu’un choix enregistré invalide.

Le menu de démarrage Limine utilise les couleurs du thème actuel, un titre EITR et une police plus grande. Les nouvelles installations le configurent ; après un changement de thème, il suit au prochain arrêt. Si votre thème est illisible, les couleurs par défaut sont utilisées. Les entrées de démarrage restent intactes et `limine.conf` est sauvegardé avant chaque modification. Le style n’est pas appliqué avec Secure Boot actif : modifier une configuration Limine dont l’empreinte est inscrite empêcherait le démarrage.

**Style > Écran de verrouillage** définit le verrouillage et l’écran de connexion. Les changements de thème conservent vos préférences.

Les modèles disponibles sont Clockwork Neo Orbital, Clockwork Tape, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing et Theme Wallpaper. Seuls ceux distribués apparaissent ; les aperçus ne verrouillent pas la session. Un modèle retiré est remplacé par Clockwork Tape, le choix par défaut des nouvelles installations.

Les images visent 4K (3840×2160, 16:9). Coffee et Pillow gardent leur style anime paisible avec des vêtements nordiques ; Material et Clockwork utilisent des ornements runiques discrets. Nothing garde son modèle. QML et SVG restent redimensionnables.

Comparez les huit modèles avec `bash quickshell/lockscreen/scripts/gallery.sh`. Cela ne change pas le choix actuel ; l’authentification et les actions d’alimentation sont désactivées dans la galerie. Clockwork utilise du QML procédural ; Coffee, Pillow, Material et Nothing gardent leurs dispositions sous licence avec de nouvelles images et JetBrainsMono Nerd Font installée. Aucune vidéo ni police fournie séparément n’est nécessaire.

**Fond d’écran du thème** utilise le fond actuel, avec l’horloge en haut à gauche et la saisie du mot de passe en bas à droite. L’aperçu Walker montre l’image actuelle. Les changements suivants apparaissent au prochain verrouillage ou aperçu ; Ctrl+P montre l’ensemble sans verrouiller. L’écran de connexion ne peut pas lire votre dossier personnel. Il montre une copie qu’Eitr enregistre au choix de ce modèle puis à chaque changement de fond. Si elle manque, un autre fond du thème actuel ou le fond Norse par défaut est utilisé.
