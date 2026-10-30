# Centre de contrôle

**SUPER + ,** ouvre ou ferme le Centre de contrôle. Il s’ouvre depuis le bord actuel de la barre et se ferme avec Escape ou un clic à l’extérieur. Sa fermeture revient à Général.

Ses cinq pages regroupent tout ce qui est hors Développement, Applications, Installer, Apprendre et Jeux ; la plupart des réglages ne nécessitent donc pas Walker. Les sections repliables commencent généralement fermées ; cliquez sur le titre pour les ouvrir ou fermer, avec mémorisation jusqu’à déconnexion. Si la barre possède un panneau dédié (OBS, WiFi, Bluetooth, Audio, Écran, Matériel, Utilisation IA, Météo), le Centre de contrôle l’ouvre.

## Général

- **Connectivité:** interrupteurs WiFi et Bluetooth, et Mode avion.
- **Commandes rapides:** Verrouillage automatique, Notifications de plantage, Ne pas déranger, Mode jeu (effets, flou et notifications contextuelles désactivés, profil de performances activé jusqu’à désactivation) et Éclairage nocturne. Une commande activée se remplit de la couleur d’accent du thème. En dessous, Masquer la barre (SUPER+Shift+Space la réaffiche) et Économiseur d’écran s’exécutent une fois.
- **Son:** volume et gain/sourdine du microphone.
- **Écran:** luminosité, sur les ordinateurs portables avec écran intégré.
- **Média:** pochette, artiste, lecture et déplacement dans la piste si disponible.
- **Alimentation:** Verrouiller, et **Alimentation…**, qui déplie Déconnexion, Veille, Redémarrer et Éteindre.

Le Mode avion mémorise les radios bloquées et ne restaure que celles-ci. Ne pas déranger masque les notifications contextuelles sans vider l’historique. Verrouillage automatique ne signifie pas empêcher la veille ; veillez à la confidentialité de l’écran.

## Style

Style regroupe les réglages dans Thème et fond d’écran (ouvert au départ), Coins, Barre, Espaces de travail, Écran de verrouillage, Curseur et Terminal. Cliquez sur le titre d’un groupe pour le replier ; sa surface délimite toutes ses options. Barre regroupe Disposition, Position, Apparence, Afficher sur, Horloge, Style multimédia et Comportement. Comportement contient Masquage automatique, Dock et Réduire les animations.

Thème et Fond d’écran ouvrent leurs carrousels ; Police par défaut ouvre la liste des polices. Thème de verrouillage, curseur (famille, taille, couleur), apparence, disposition, bord et écrans de la barre, marqueurs d’espaces, coins et Cursor Fire de Kitty se règlent directement dans le panneau et partagent leurs préférences avec Walker.

Terminal propose Kitty (par défaut) et Ghostty facultatif ; les terminaux utilitaires d’Eitr restent sous Kitty. Consultez [Terminal et éditeurs](terminal.md) pour l’installation et la configuration.

## Outils

Captures d’écran (sélection, écran entier, fenêtre ou sélection directement dans le presse-papiers), enregistrement (commandes OBS, Enregistrer, Enregistrer + Audio et Arrêter), OCR, QR codes, sélecteur de couleurs, Transcoder, rappels et partage LocalSend. Le panneau se ferme avant le début d’une sélection ou d’un enregistrement.

## Système

- **Périphériques:** panneaux Audio, Microphone, Écran (résolution, fréquence, échelle), Bluetooth et WiFi, Éclairage et limite de charge sur portable.
- **Clavier:** sélectionner, ajouter ou supprimer des dispositions en conservant au moins une.
- **Éclairage nocturne et écran principal:** mode et programmation de l’éclairage nocturne, distincts de l’interrupteur manuel, et écran principal accueillant la barre.
- **Informations:** À propos, Matériel, Utilisation IA, Météo et Signaler un problème.
- **Mises à jour:** canal, Mise à jour du système, changements de chaque mise à jour et mises à jour Pacman seules ou AUR seules.
- **Instantanés et nettoyage:** restaurer un fichier, instantanés personnels et de récupération avec leur guide, Nettoyage et Dotfiles.

Sécurité, réinitialisation d’usine et service réseau restent dans Walker > Système avec leurs propres confirmations.

## Langue

**Système > Langue** affiche la langue actuelle selon les paramètres régionaux. Ouvrez le sélecteur, choisissez une langue ou Valeur système, puis déconnectez-vous et reconnectez-vous pour l’appliquer. Seule la langue des messages de votre session change, jamais les fichiers régionaux système. Voir le [Guide de langue](handbook:language).

## Discussion rapide

L’icône de discussion près des onglets ouvre une conversation jetable avec l’assistant par défaut choisi dans Développement > IA. Elle reste masquée sans assistant ou lorsque la politique de l’organisation les désactive. Entrée envoie ; Maj+Entrée insère un saut de ligne. Échap ou Retour ramène aux pages. Nouvelle discussion, quitter la discussion ou fermer le Centre de contrôle efface les messages et annule toute réponse en attente.

Les réponses proposent du Markdown sélectionnable et Copier. La conversation reste en mémoire ; Eitr n’écrit aucun historique ni journal. Sous la saisie figure le fournisseur cloud ou la mention que Ratatoskr tourne sur ce PC. Les fournisseurs reçoivent les messages et les échanges précédents. Chaque message contient uniquement version/canal d’Eitr, noyau, CPU/GPU/RAM et thème comme contexte non fiable. Aucun nom d’utilisateur ou de machine, fichier, courriel, nom WiFi, titre de fenêtre ou presse-papiers n’est collecté. L’assistant utilise le mode sans interface en lecture seule avec le compte sélectionné ; il ne peut pas modifier le système. Les erreurs apparaissent dans la discussion.

## Plugins

**Centre de contrôle > Plugins** affiche une ligne compacte par plugin installé avec icône, nom et interrupteur d’activation. Sélectionnez une ligne pour voir l’auteur, la version, la description, les actions de mise à jour et de suppression, les widgets, les éléments de barre et l’aperçu. Utilisez Retour ou Échap pour revenir à la liste. Activer/Désactiver conserve les positions et arrête ou rétablit services, lignes Walker, hooks et composants visuels ; utilisez `eitr plugin enable ID` ou `eitr plugin disable ID`. Ajouter un plugin…, Mettre à jour et Supprimer ouvrent les parcours de vérification du terminal ; la suppression demande confirmation. Général conserve uniquement les tuiles. Les erreurs visuelles ont une action indépendante de réactivation.

Ajouter un plugin… accepte aussi les dépôts contenant plusieurs plugins. L’index `eitr-plugins.json` à la racine indique leurs identifiants et dossiers, chacun avec son propre `eitr-plugin.json`. Sélectionnez un ou plusieurs plugins par nom, description et icône, puis examinez-les séparément. Refuser l’un n’approuve pas les autres. Les plugins sélectionnés partagent une copie téléchargée du dépôt et sont chacun épinglés au commit exact ; mettre à jour l’un conserve les commits approuvés des autres. Les détails affichent l’URL du dépôt et le dossier du plugin. Un seul `eitr-plugin.json` à la racine continue de fonctionner comme avant.

La mise à jour du système vérifie seulement les nouveaux commits des plugins, même si les paquets sont à jour, et indique leur nombre et où les mettre à jour. Elle ne révise ni ne met à jour les plugins ; les erreurs réseau sont ignorées silencieusement. Utilisez **Mettre à jour les plugins** dans **Centre de contrôle > Plugins**, à côté d’Ajouter un plugin…, ou **Installer > Plugins > Mettre à jour les plugins**, ou lancez `eitr plugin update`. La marque ↑ dans la ligne et « Mise à jour disponible » dans les détails reflètent la dernière vérification du commit approuvé. L’action séparée conserve les diffs, avertissements et confirmations pour chaque plugin.

La liste des plugins affiche « Ce plugin a des erreurs » et le premier message. Sélectionnez le plugin puis Voir les détails des erreurs pour en savoir plus ; le commutateur permet de le désactiver en un clic. Seules les erreurs qui indiquent un fichier du dossier du plugin sont détectées. Les plugins disposent des permissions du bureau : installez uniquement ceux auxquels vous faites confiance.
