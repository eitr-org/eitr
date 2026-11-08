# Périphériques et saisie

La page Écrans et le panneau d’affichage montrent une carte des moniteurs au-dessus du sélecteur. Les rectangles suivent les positions réelles et les tailles logiques, avec mise à l’échelle et rotation. L’écran principal porte un contour surligné et une étiquette Principal ; les écrans désactivés sont estompés lorsqu’ils figurent dans la topologie. Cliquez sur un moniteur pour ouvrir ses réglages. La carte ne se déplace pas par glissement. Un essai actualise immédiatement la carte et affiche un contour pointillé jusqu’à sa confirmation ou son annulation.

Utilisez **Paramètres > Écrans**, **Paramètres > Son** et **Paramètres > Saisie** pour les commandes partagées dans les paramètres. Son contient les cartes Sortie et Entrée (périphérique, volume avec sourdine et niveau du micro), une ligne par application qui lit du son, et les sons d’événements ; Renommer reste dans la liste des périphériques. Entrée permet d’ajouter, supprimer et réordonner les dispositions du clavier avec les boutons fléchés.

Ouvrez Paramètres > Écrans, Son ou Saisie. Les panneaux correspondants de la barre et le Centre de contrôle proposent aussi des commandes rapides.

Walker > Paramètres > Périphériques et saisie > Éclairage contrôle les appareils OpenRGB. Il est désactivé au départ ; Suivre le thème recolore les appareils compatibles lors des changements de thème.

## Régler le son et le microphone

Volume sélectionne la sortie par défaut et règle le volume général ainsi que celui des applications en lecture. Les périphériques apparaissent avec un nom lisible et une icône de type ; cliquez sur le périphérique actuel pour en choisir un autre et utilisez le bouton crayon d’un périphérique pour le renommer sur cet ordinateur.

Microphone sélectionne l’entrée par défaut, le gain et la mise en sourdine. Son indicateur de niveau ne fonctionne que lorsque le panneau est ouvert ; aucun son n’est enregistré sur disque. Ouvrir d’autres réglages ne démarre pas la surveillance du microphone.

Les curseurs vont jusqu’à 100 % ; une valeur supérieure déjà présente reste inchangée tant que vous ne déplacez pas le curseur. Changer le périphérique audio par défaut peut affecter un appel : faites-le délibérément. Les commandes de lecture sont distinctes du choix du périphérique par défaut.

## Configurer les écrans

Le panneau Écran liste les moniteurs actifs. Cliquez sur l’un d’eux pour ouvrir ses réglages dans sa carte, puis à nouveau pour les fermer. L’écran **Principal** accueille la barre, les panneaux et les notifications : activez **Écran principal** dans les réglages d’un autre moniteur pour les y déplacer. S’il est déconnecté, un autre devient **Principal** et reçoit la barre jusqu’à son retour ; votre choix est conservé.

Les réglages comprennent résolution, fréquence de rafraîchissement, échelle, rotation (Normale, À l’envers, Tournée à droite ou Tournée à gauche, pour un écran tourné sur son pied) et, avec plusieurs moniteurs, position par rapport à un autre ou duplication. L’écran principal reste à sa place et les autres sont disposés autour ; sa ligne Position l’indique simplement. Un moniteur peut être placé à côté de tout autre moniteur, sauf un dont la position dépend déjà de lui.

Chaque réglage occupe une ligne indiquant sa valeur actuelle ; cliquez pour voir les choix. Position, alignement, échelle, duplication et écran principal sont appliqués et enregistrés immédiatement. Une nouvelle **résolution, fréquence de rafraîchissement ou rotation** pourrait laisser un écran noir ou difficile à utiliser ; le panneau demande alors **Conserver ces réglages ?** en bas. Sans **Conserver** dans les 15 secondes, les anciens réglages reviennent automatiquement, même si le panneau est fermé. Les réglages de cet ordinateur sont dans `~/.config/hypr/displays.json`.

Vous pouvez disposer autant de moniteurs que nécessaire : placez chacun à gauche, à droite, au-dessus ou au-dessous d’un autre, puis alignez-le en haut, au milieu ou en bas (à gauche, au centre ou à droite lorsqu’ils sont superposés). La disposition est mémorisée : si la résolution ou l’échelle change, les moniteurs voisins suivent. Un choix provoquant un chevauchement est refusé avec un message. Chaque moniteur connecté reçoit une position exacte, pour que modifier l’un n’amène pas Hyprland à déplacer les autres.

**Modifier la disposition à la main** ouvre `~/.config/hypr/local.lua` pour les cas non couverts, comme les écrans à image inversée ou les espaces de travail affectés à un moniteur. Un nouveau fichier contient des exemples commentés pour trois moniteurs, le mode portrait, la superposition, la duplication et un portable sur station d’accueil. Rien ne change avant de décommenter un exemple et d’exécuter `hyprctl reload`. Les moniteurs définis ici sont prioritaires ; retirez ces définitions pour les gérer à nouveau dans le panneau.

Le curseur de luminosité n’apparaît que sur les ordinateurs portables avec écran intégré (rétroéclairage natif) ; les moniteurs de bureau gardent leurs propres boutons. L’atténuation avant le verrouillage peut encore baisser un moniteur externe via DDC si le moniteur et les permissions le permettent. L’Éclairage nocturne propose un interrupteur manuel et une programmation facultative avec des horaires modifiables.

**HDR** apparaît uniquement sur les moniteurs dont l’EDID indique la prise en charge de PQ ou HLG. Il affiche le bureau en HDR ; les jeux peuvent utiliser HDR même lorsque ce réglage est désactivé. Activer ou désactiver HDR demande aussi de conserver le changement sous 15 secondes, sinon il est annulé.

Lorsque HDR est actif, **Luminosité du contenu SDR** règle le contenu SDR de 1,0× à 2,0× et enregistre immédiatement. Les jeux HDR en plein écran peuvent toujours basculer automatiquement le moniteur lorsque le HDR du bureau est désactivé. Dans les deux cas, Eitr utilise les niveaux de crête et de noir indiqués par l’EDID du moniteur.

Les navigateurs utilisent HDR uniquement lorsque le HDR du bureau est activé pour leur moniteur ; ils ne l’activent jamais automatiquement. Les jeux HDR en plein écran continuent de basculer automatiquement lorsque le HDR du bureau est désactivé. La lecture HDR dans le navigateur dépend aussi de sa prise en charge et de ses réglages.

## Changer les dispositions du clavier

Ouvrez Paramètres > Saisie. Utilisez Ajouter une disposition pour chercher langues et variantes, les flèches pour réordonner et le bouton de suppression pour retirer une disposition. Quatre au maximum sont acceptées, sans doublons ; une au moins doit rester. **Alt + Shift** les parcourt. À partir de deux, cliquez sur le code dans la barre pour changer. Disposition et langue du bureau sont distinctes ; voir [Langue](handbook:language).

Le bureau démarre avec le clavier choisi dans l’installateur. Le choix US inclut US et US International ; Alt + Shift suffit pour accéder aux accents.

### Navigation facultative avec Caps Lock

La configuration keyd facultative dans `distro/keyd/navigation.conf.example` envoie Escape lors d’un appui bref sur Caps Lock. Maintenez Caps Lock et appuyez sur H/J/K/L pour gauche/bas/haut/droite. Les autres touches conservent leur comportement normal.

Pour retrouver cette préférence après réinstallation, installez l’exemple dans `/etc/keyd/navigation.conf` et activez `keyd.service`. Il s’applique à tous les claviers, même hors de Hyprland, et n’est pas activé par défaut. Pour annuler, supprimez la configuration et rechargez keyd ; désactivez le service si aucune autre correspondance ne l’utilise. Le choix de langue et de disposition reste distinct.

## Alimentation et batterie des portables

Les commandes de batterie et de profil énergétique n’apparaissent qu’en présence d’une batterie système, pas simplement d’une souris ou d’un casque sans fil. Économie/Équilibré/Performances nécessitent power-profiles-daemon ; les profils non pris en charge restent indisponibles. Les estimations et l’état de santé ne s’affichent que si le matériel les fournit.

La Limite de charge nécessite une interface sysfs de micrologiciel compatible et une confirmation saisie. Désactivée, elle permet une charge à 100 %. Tous les portables ne la prennent pas en charge.

Une notification avertit à 10 %, puis une notification urgente à 5 %, une fois par décharge. Sur portable, l’installateur ajoute aussi le micrologiciel audio requis par les modèles récents (`sof-firmware`) et, sur les modèles Intel, `thermald` pour gérer la chaleur.

Ces fonctions sont **expérimentales** jusqu’à leur confirmation par les premiers utilisateurs sur de vrais portables : touches de rétroéclairage du clavier et fermeture du capot avec moniteur externe connecté. Dans ce cas, l’écran du portable s’éteint et le bureau passe sur le moniteur externe ; rouvrir le capot le ramène. Sans moniteur externe, fermer le capot met en veille normalement. L’hibernation n’est pas configurée automatiquement.
