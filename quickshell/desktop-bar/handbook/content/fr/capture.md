# Capture et partage

Les outils de capture se trouvent dans Principal > Outils > Capture et Centre de contrôle > Outils.

## Captures d’écran et extraction

- **Print:** capture complète dans l’éditeur flottant.
- **SUPER + Print:** sélection figée dans l’éditeur flottant.
- **SUPER + Shift + Print:** capture de la fenêtre active dans l’éditeur.
- **SUPER + Ctrl + Print:** extraction du texte d’une sélection par OCR.
- **SUPER + Alt + Print:** décodage d’un QR code dans une sélection.
- **SUPER + =:** choix et copie d’une couleur.

Après une capture, un bref éclair frappe la zone capturée. L’effet commence après l’acquisition de l’image et n’apparaît donc jamais sur la capture.

Vérifiez le contenu avant d’enregistrer ou de partager. L’OCR peut se tromper ; les QR codes peuvent contenir des identifiants privés ou des URL non fiables. Un éditeur d’images ne garantit pas la suppression du texte sensible en arrière-plan.

## Enregistrement et diffusion

Enregistrement d’écran ouvre les commandes OBS. Elles utilisent votre scène configurée et l’autorisation de capture Wayland enregistrée ; la scène doit inclure une source d’écran visible. Démarrer la capture prépare OBS et ferme le panneau avant l’acquisition. Les commandes utilisent WebSocket d’OBS, désactivé par défaut : Eitr l’active avec un mot de passe la première fois qu’OBS est fermé. Si OBS est alors ouvert, fermez-le une fois et réessayez.

Les enregistrements vont dans **Videos/Records** de votre dossier personnel. OBS utilise par défaut le dossier personnel lui-même ; Eitr ne change que cette valeur et conserve un dossier choisi dans OBS > Paramètres > Sortie.

Pendant un enregistrement ou une diffusion OBS, un point rouge apparaît près de la météo. Cliquez pour voir durée, taille du fichier, pause/reprise, arrêt, marqueur de chapitre (nécessite le format Hybrid MP4 d’OBS), microphone et caméra OBS, et scène. Une diffusion affiche un compteur LIVE avec son propre arrêt. À la fin d’un enregistrement, une notification propose Ouvrir le dossier et Copier le chemin. Vérifiez les choix audio/micro et le moniteur avant de commencer. La webcam nécessite une source caméra dans OBS. Les interrupteurs audio de capture agissent sur les entrées OBS, pas sur le volume système.

Le manuel ne démarre jamais d’enregistrement ni de diffusion. Partage d’écran et capture restent des actions explicites. Transcoder ouvre la conversion d’images et vidéos existante ; vérifiez les chemins de sortie avant de remplacer un fichier.

Pour une nouvelle configuration OBS, Eitr crée la collection Untitled avec une Scene : capture d’écran, caméra masquée et sources audio par défaut du bureau et du microphone. À la première utilisation, le système vous demande quel écran partager ; OBS conserve cette autorisation. La caméra reste éteinte jusqu’à ce que vous l’activiez. Les collections existantes ne sont jamais modifiées.

## Partager

Principal > Outils > Partager propose LocalSend et les outils de transfert existants. L’envoi exige de choisir la destination ou l’appareil. Vérifiez les destinataires et évitez de partager clés privées, codes de récupération, jetons ou un dossier personnel/de configuration complet non vérifié.
