# Centre de contrôle

**SUPER + I** ouvre ou ferme le Centre de contrôle. Il s’ouvre depuis le bord actuel de la barre et se ferme avec Escape ou un clic à l’extérieur. Sa fermeture revient à Général. Avec une barre Full à gauche ou à droite, le Centre commence en haut de l’écran, avec des marges intérieures dans la surface reliée à la barre.

Ses pages sont Général, Plugins et Outils. Le bouton en forme d’engrenage en dessous, **Tous les paramètres**, ferme le Centre de contrôle et ouvre les Paramètres, qui regroupent apparence, barre, périphériques, clavier, écrans et système. Les sections repliables commencent généralement fermées ; cliquez sur le titre pour les ouvrir ou fermer, avec mémorisation jusqu’à déconnexion. Si la barre possède un panneau dédié, comme OBS, WiFi ou Bluetooth, le Centre de contrôle l’ouvre.

## Général

<!-- eitr-figure: control-center -->

La page Général. Les boutons de gauche passent entre Général, Plugins et Outils ; l’engrenage en dessous ouvre les Paramètres. Une commande activée se remplit de la couleur d’accent du thème.

- **Connectivité:** interrupteurs WiFi et Bluetooth, et Mode avion.
- **Actions rapides:** Verrouillage automatique, Notifications de plantage, Ne pas déranger, Mode jeu (effets, flou et notifications contextuelles désactivés, profil de performances activé jusqu’à désactivation) et Éclairage nocturne. En dessous, Masquer la barre (SUPER+Shift+Space la réaffiche) et Économiseur d’écran s’exécutent une fois.
- **Son:** volume et gain/sourdine du microphone, et deux interrupteurs facultatifs, désactivés par défaut : **Sons de notification** (un signal, un autre pour les notifications urgentes ; celles de faible priorité restent silencieuses) et, sur les PC avec batterie, **Sons du chargeur** au branchement et au débranchement. Aucun ne sonne en Ne pas déranger ni en Mode jeu.
- **Écran:** luminosité, sur les ordinateurs portables avec écran intégré.
- **Média:** pochette, artiste, lecture et déplacement dans la piste si disponible.
- **Alimentation:** Verrouiller, et **Alimentation…**, qui déplie Déconnexion, Veille, Redémarrer et Éteindre.

Le Mode avion mémorise les radios bloquées et ne restaure que celles-ci. Ne pas déranger masque les notifications contextuelles sans vider l’historique. Verrouillage automatique ne signifie pas empêcher la veille ; veillez à la confidentialité de l’écran.

## Outils

Captures d’écran (sélection, écran entier, fenêtre ou sélection directement dans le presse-papiers), enregistrement (commandes OBS, Enregistrer, Enregistrer + Audio et Arrêter), OCR, QR codes, sélecteur de couleurs, Transcoder, rappels et partage LocalSend. Le panneau se ferme avant le début d’une sélection ou d’un enregistrement.

## Discussion rapide

Choisissez l’assistant par défaut dans Paramètres > Assistant IA.

L’icône de discussion près des onglets ouvre une conversation jetable avec l’assistant par défaut choisi dans Développement > IA. Elle reste masquée sans assistant ou lorsque la politique de l’organisation les désactive. Entrée envoie ; Maj+Entrée insère un saut de ligne. Échap ou Retour ramène aux pages. Nouvelle discussion, quitter la discussion ou fermer le Centre de contrôle efface les messages et annule toute réponse en attente.

Les réponses proposent du Markdown sélectionnable et Copier. La conversation reste en mémoire ; Eitr n’écrit aucun historique ni journal. Sous la saisie figure le fournisseur cloud ou la mention que Ratatoskr tourne sur ce PC. Les fournisseurs reçoivent les messages et les échanges précédents. Le résumé de la machine contient version/canal d’Eitr, noyau, CPU/GPU/RAM et thème comme contexte non fiable.

Aucun nom d’utilisateur ou de machine, fichier, courriel, nom WiFi, titre de fenêtre ou presse-papiers n’est collecté. L’assistant utilise le mode sans interface en lecture seule avec le compte sélectionné ; il ne peut pas modifier le système. Les erreurs apparaissent dans la discussion.

L’assistant reçoit aussi l’introduction du Manuel et des extraits traduits pertinents, une liste fixe d’outils installés et l’indication d’un moniteur HDR connecté. Cela décrit la disponibilité, pas la configuration des services. Il ne peut exécuter aucune commande ni modifier les réglages.

## Plugins

**Centre de contrôle > Plugins** affiche une ligne compacte par plugin installé avec icône, nom et interrupteur d’activation. Sélectionnez une ligne pour voir l’auteur, la version, la description, les actions de mise à jour et de suppression, les widgets, les éléments de barre et l’aperçu. Utilisez Retour ou Échap pour revenir à la liste.

Activer/Désactiver conserve les positions et arrête ou rétablit services, lignes Walker, hooks et composants visuels ; utilisez `eitr plugin enable ID` ou `eitr plugin disable ID`. Ajouter des plugins, Mettre à jour et Supprimer ouvrent les parcours de vérification du terminal ; la suppression demande confirmation. Général conserve uniquement les tuiles. Les erreurs visuelles ont une action indépendante de réactivation.

Pour installer, vérifier et mettre à jour en sécurité, voir [Applications et installation](handbook:apps).

Pour Paramètres (**SUPER + ,**) et les photos de profil, voir [Paramètres](handbook:system).
