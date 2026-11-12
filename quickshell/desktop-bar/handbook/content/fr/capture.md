# Capture et partage

Les captures d’écran et enregistrements se trouvent dans Principal > Outils > Capture ; Couleur, Reconnaissance de texte, Code QR et Transcoder sont directement dans Principal > Outils. Centre de contrôle > Outils propose les mêmes actions.

## Captures d’écran et extraction

- **Print:** capture complète dans l’éditeur flottant.
- **SUPER + Print:** sélection figée dans l’éditeur flottant.
- **SUPER + Shift + Print:** capture de la fenêtre active dans l’éditeur.
- **SUPER + Ctrl + Print:** extraction du texte d’une sélection par OCR.
- **SUPER + Alt + Print:** décodage d’un QR code dans une sélection.
- **SUPER + =:** choix et copie d’une couleur.

Après une capture, un bref éclair frappe la zone capturée. L’effet commence après l’acquisition de l’image et n’apparaît donc jamais sur la capture.

Vérifiez le contenu avant d’enregistrer ou de partager. L’OCR peut se tromper ; les QR codes peuvent contenir des identifiants privés ou des URL non fiables. Un éditeur d’images ne garantit pas la suppression du texte sensible en arrière-plan.

Les captures enregistrées proposent des actions de notification pour ouvrir l’image, la modifier dans l’éditeur de captures (elle est enregistrée par-dessus), l’embellir, l’épingler à l’écran ou ouvrir son dossier de captures.

**Embellir** pose la capture sur un fond (le dégradé du thème, quelques préréglages, la couleur d’accent ou aucun) avec marge, coins arrondis et ombre réglables ; **Copier l’image** met l’image en taille réelle dans le presse-papiers et **Enregistrer l’image** l’écrit à côté de l’original sous `NAME-beautified.png`.

**Épingler à l’écran** fait flotter la capture au-dessus de toutes les fenêtres et sur tous les espaces de travail, comme référence. Faites-la glisser pour la déplacer et faites défiler dessus pour la redimensionner ; fermez-la avec son bouton ×, Échap ou un clic du milieu.

## Enregistrement et diffusion

Enregistrement d’écran ouvre les commandes OBS. Elles utilisent votre scène configurée et l’autorisation de capture Wayland enregistrée ; la scène doit inclure une source d’écran visible. Démarrer la capture prépare OBS et ferme le panneau avant l’acquisition. Les commandes utilisent WebSocket d’OBS, désactivé par défaut : Eitr l’active avec un mot de passe la première fois qu’OBS est fermé. Si OBS est alors ouvert, fermez-le une fois et réessayez.

Les enregistrements vont dans **Videos/Records** de votre dossier personnel. OBS utilise par défaut le dossier personnel lui-même ; Eitr ne change que cette valeur et conserve un dossier choisi dans OBS > Paramètres > Sortie.

Pendant un enregistrement ou une diffusion OBS, un point rouge apparaît à gauche de l’horloge. Cliquez pour voir durée, taille du fichier, pause/reprise, arrêt, marqueur de chapitre (nécessite le format Hybrid MP4 d’OBS), microphone et caméra OBS, et scène. Une diffusion affiche un compteur LIVE avec son propre arrêt. À la fin d’un enregistrement, une notification propose Lire l’enregistrement, Ouvrir le dossier et Copier le chemin.

Vérifiez les choix audio/micro et le moniteur avant de commencer. La webcam nécessite une source caméra dans OBS. Les interrupteurs audio de capture agissent sur les entrées OBS, pas sur le volume système.

Le manuel ne démarre jamais d’enregistrement ni de diffusion. Partage d’écran et capture restent des actions explicites. Transcoder ouvre la conversion d’images et vidéos existante ; vérifiez les chemins de sortie avant de remplacer un fichier.

Quand OBS est fermé, Enregistrer capture l’écran qui a le focus : Eitr répond lui-même à la demande d’écran d’OBS, sans sélecteur, et règle le canevas d’OBS sur la taille de cet écran (une sortie réduite garde son rapport). Une fenêtre OBS que vous avez ouverte vous-même continue d’enregistrer ce qu’elle capture déjà ; à la fin de l’enregistrement, Eitr ferme l’OBS qu’il a lancé, et le suivant suit de nouveau votre focus. Les autres apps qui partagent votre écran, comme un appel vidéo, affichent toujours le sélecteur de Hyprland. Un `~/.config/hypr/xdph.conf` que vous avez modifié est conservé ; le sélecteur peut alors demander à chaque fois.

Pour une nouvelle configuration OBS, Eitr crée la collection Untitled avec une Scene : capture d’écran, caméra masquée et sources audio par défaut du bureau et du microphone. La caméra reste éteinte jusqu’à ce que vous l’activiez. Les collections existantes ne sont jamais modifiées.

## Partager

Principal > Outils > Partager propose LocalSend et les outils de transfert existants. L’envoi exige de choisir la destination ou l’appareil. Vérifiez les destinataires et évitez de partager clés privées, codes de récupération, jetons ou un dossier personnel/de configuration complet non vérifié.
