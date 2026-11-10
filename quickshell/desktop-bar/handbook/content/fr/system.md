# Trouver un réglage

Appuyez sur **SUPER + ,** pour ouvrir Paramètres. Système est la vue d’ensemble, pas un dossier contenant tous les réglages.

Recherchez un réglage précis, comme **Taille du pointeur**, ou une page dans la barre latérale des paramètres. La page et l’onglet figurent sous le nom. Utilisez Haut/Bas et Entrée, ou cliquez, pour ouvrir l’onglet, faire défiler jusqu’au contrôle et le mettre brièvement en évidence. Échap efface d’abord la recherche. Avec les animations réduites, la mise en évidence apparaît et disparaît sans fondu.

<!-- eitr-figure: settings-window -->

La fenêtre Paramètres propose une barre latérale avec recherche et des cartes regroupant les commandes liées. Un clic à l’extérieur ne la ferme pas. Utilisez Échap, son bouton de fermeture ou le raccourci habituel de fermeture de fenêtre.

Les liens en bas des panneaux ferment le panneau et ouvrent la page correspondante de Paramètres. Tous les paramètres dans le Centre de contrôle fait de même ; **SUPER + I** ouvre les commandes rapides. Voir [Centre de contrôle](handbook:control-center).

Choisissez Couleurs des paramètres dans Paramètres > Apparence > Thème et fond d’écran : Couleurs du thème suit le bureau, Site web Eitr utilise la palette du site. Cela concerne Paramètres, le Manuel et Thèmes et plugins, pas le thème du bureau. Walker > Paramètres > Bureau > Apparence > Couleurs des paramètres ouvre ce choix.

Le catalogue séparé Thèmes et plugins s’ouvre avec SUPER + F2 ou Plus de thèmes dans Apparence.

## Choisir une page

Utilisez les noms de page ci-dessous. Les chapitres liés expliquent les étapes.

| Page | En savoir plus |
| :--- | :--- |
| Système | [Système](handbook:information) |
| Écrans — Écrans, Éclairage nocturne | [Écrans](handbook:devices) |
| Son | [Son](handbook:devices) |
| Connexions — Wi-Fi, Bluetooth | [Connexions](handbook:connectivity) |
| Streaming | [Streaming](handbook:remote-access) |
| Saisie | [Saisie](handbook:devices) |
| Apparence — Thème et fond d’écran, Polices et curseur, Terminal | [Apparence](handbook:appearance) |
| Barre de bureau | [Barre de bureau](handbook:desktop-bar) |
| Fenêtres | [Fenêtres](handbook:appearance) |
| Écran de verrouillage | [Écran de verrouillage](handbook:appearance) |
| Notifications | [Notifications](handbook:information) |
| Focus | [Focus](handbook:focus) |
| Assistant IA | [Assistant IA](handbook:development) |
| Raccourcis clavier | [Raccourcis clavier](handbook:shortcuts) |
| Applications par défaut | [Applications par défaut](handbook:apps) |
| Utilisateurs | [Utilisateurs](handbook:security) |
| Sécurité | [Sécurité](handbook:security) |
| Mises à jour | [Mises à jour](handbook:maintenance) |
| Vérifier ce PC | [Vérifier ce PC](handbook:troubleshooting) |
| À propos | [À propos](handbook:information) |

## Changer votre photo de profil

Ouvrez Paramètres > Utilisateurs (ou cliquez sur votre photo dans la vue Système des paramètres) et cliquez sur votre photo. Le sélecteur de fichiers du système s’ouvre dans une fenêtre flottante centrée au-dessus des paramètres et n’affiche que des images ; une fois l’image choisie, l’éditeur de recadrage s’ouvre dans une feuille au-dessus des paramètres.

Faites glisser l’aperçu rond pour déplacer l’image ; la molette, le curseur ou +/− zooment de 1× à 4×, et les flèches la déplacent. Enregistrer (ou Entrée) applique le recadrage ; Annuler ou Échap ferme la feuille sans l’appliquer. L’icône de corbeille sous votre photo la retire après confirmation.

La photo reste circulaire dans le Centre de contrôle, le verrouillage et l’écran de connexion. Le Centre de contrôle se contente d’afficher la photo en haut de sa navigation ; sans photo, il n’y affiche rien, tout comme le verrouillage et l’écran de connexion. Les paramètres affichent à la place l’initiale de votre nom sur un cercle de la couleur d’accent.

PNG, JPEG, WebP, GIF (première image) et BMP sont acceptés jusqu’à 40 Mo et 12000 pixels par côté. Eitr corrige l’orientation, retire les métadonnées, enregistre un PNG de 512×512 dans `~/.face`, puis actualise AccountsService pour SDDM. En cas d’échec, la photo enregistrée fonctionne toujours au verrouillage ; l’interface ou la CLI signale l’erreur de connexion.

## Changer votre mot de passe

Ouvrez Paramètres > Utilisateurs et choisissez Changer le mot de passe à côté de votre nom. Saisissez votre mot de passe actuel, puis deux fois le nouveau : Entrée passe au champ suivant et confirme sur le dernier ; Échap annule. Les règles de mot de passe du système décident de ce qui est accepté, et un mot de passe refusé affiche la raison. Eitr passe aussi le trousseau de connexion au nouveau mot de passe, pour que les mots de passe enregistrés continuent de se déverrouiller à la connexion. La phrase secrète de chiffrement du disque est distincte et reste la même. Walker > Paramètres > Sécurité > Mettre à jour le mot de passe fait la même chose dans un terminal.

## Gérer les comptes

Les administrateurs disposent des onglets **Utilisateurs** et **Gérer** dans Paramètres > Utilisateurs. Les comptes standard ne voient que la liste des utilisateurs. Gérer propose Créer un utilisateur…, Changer le type, Définir le mot de passe d’autres comptes et Supprimer avec un choix pour le dossier personnel. Confirmez dans la fenêtre, puis appuyez sur Entrée dans le terminal de tâche pour continuer ou Échap pour annuler ; saisissez les mots de passe uniquement dans ce terminal. Les dossiers personnels sont conservés par défaut. Consultez [Comptes utilisateur](handbook:security) pour les autorisations, les limites du trousseau et les protections de suppression.

## Utiliser Walker comme alternative

**SUPER + F** ouvre Walker. Son menu Paramètres suit les groupes de l’application Paramètres : Périphériques, Bureau, Applications et touches, Comptes et sécurité et Système, avec Centre de contrôle et Dotfiles en bas. Applications et touches ouvre les pages Applications par défaut et Raccourcis clavier de l’application Paramètres.

<!-- eitr-figure: launcher -->

Le menu Paramètres de Walker est une alternative avec ses propres dossiers. > ouvre un sous-menu ; la description sous une action explique son effet.

Walker affiche les dossiers avant les actions. Tapez pour chercher, appuyez sur Entrée pour ouvrir et Shift + Backspace pour revenir. La langue se choisit dans Walker > Paramètres > Périphériques > Langue ; voir [Langue](handbook:language).
