# Accès à distance

Ouvrez System > Connectivity > Accès à distance. Le partage reste désactivé jusqu’à
son activation. Cette étape contrôle le bureau Eitr connecté et éveillé.
Le fonctionnement sans écran, avant connexion et wake on LAN viendront plus tard.
Le comportement verrouillé reste à vérifier ; arrêtez le partage avant de
verrouiller si la confidentialité est importante.

## Sunshine sur Eitr

Dans Partager ce PC, choisissez Configurer le partage. Le responsable de version compile
le paquet natif signé d’Eitr depuis les sources officielles, sans compilation AUR
au premier clic. Flatpak et AppImage ne proposent pas la capture KMS. Les réglages
et appareils associés sont conservés. Ne lancez pas une deuxième instance.

Lisez l’avertissement de contrôle total et saisissez `yes` uniquement pour accepter
la capture KMS et les entrées virtuelles du clavier, de la souris et de la manette.
L’état initial est conservé dans `/var/lib/eitr/remote-access`. La configuration
ajoute une règle udev pour uinput, charge uinput au démarrage, accorde l’accès à
votre utilisateur et applique `cap_sys_admin+p` à Sunshine. Rétablir la configuration du partage
rétablit les fichiers, la capacité et l’ACL d’origine. Si la configuration a chargé uinput, l’annulation le décharge aussi. Si une autre
application l’utilise encore, l’échec est signalé et le journal est conservé pour
fermer l’application puis réessayer.

Démarrer le partage demande confirmation et ouvre `https://localhost:47990`. Acceptez le
certificat local autosigné uniquement à cette adresse. Définissez un identifiant
et un mot de passe fort avant l’association. Ouvrir les réglages rouvre les réglages ;
Associer un appareil ouvre la page du PIN. Saisissez uniquement le PIN de votre appareil
Moonlight. Eitr impose `upnp=off`. Ne configurez pas de redirection de ports sur le routeur.

TCP 47984, 47989 et 48010 et UDP 47998-48000 sont autorisés uniquement depuis les
sous-réseaux LAN privés directement connectés et `tailscale0`. TCP 47990 reste
accessible seulement depuis ce PC, même si une autre règle autorise l’accès.
Les réseaux sont déterminés à chaque démarrage du partage ; relancez-le après un
changement de réseau. Utilisez uniquement un réseau domestique de confiance.
Arrêter le partage désactive aussi le démarrage automatique et ferme les ports, y compris
les flux existants. Une défaillance du service les ferme aussi ; les ouvertures ne
survivent pas au redémarrage. Démarrer à la connexion est facultatif et confirmé séparément ;
Désactiver le démarrage à la connexion conserve le démarrage manuel. État du partage affiche les erreurs.

Au premier démarrage, la diffusion reste bloquée pendant la définition du mot de passe. Revenez au terminal, confirmez sa définition puis saisissez `yes` à la confirmation root pour autoriser le contrôle à distance.

Une mise à jour du paquet Sunshine retire la capacité de capture de l’exécutable.
Si le partage refuse ensuite de démarrer, utilisez à nouveau Configurer le partage
et confirmez l’autorisation. Le journal d’annulation initial est conservé.

## Moonlight sur un Mac

Installez [Moonlight](https://moonlight-stream.org/). Pour le premier essai, utilisez
le même réseau domestique. Ajoutez manuellement l’adresse LAN d’Eitr au besoin.
Sélectionnez le PC, lisez le PIN et utilisez Associer un appareil sur Eitr. Choisissez
Desktop pour contrôler applications et jeux. Sélectionnez l’écran dans Sunshine
et vérifiez chaque moniteur. Gaming > Moonlight et Se connecter à un autre PC installent
ou ouvrent le client Eitr dans le sens inverse. Les nouvelles installations incluent ces applications ; le partage reste désactivé tant que vous ne l’activez pas explicitement.

## Tailscale sur les deux ordinateurs

Dans Accès hors du domicile, choisissez Configurer l’accès extérieur. Après installation,
l’assistant root confirmé active et démarre `tailscaled.service`, puis définit
votre utilisateur comme opérateur. La connexion au compte, la connexion au réseau et la déconnexion demandent une autorisation administrateur, même sans opérateur configuré.
Se connecter ouvre l’URL de `tailscale login` dans le navigateur. Connect connecte ;
Disconnect déconnecte sans effacer les identifiants. État de la connexion indique
l’adresse de ce PC, l’absence de connexion au compte et les connexions directes,
relayées ou inactives. Tester un appareil distant utilise `tailscale ping` pour un appareil précis.
Le relais peut augmenter la latence et réduire la qualité.

Installez [Tailscale sur le Mac](https://tailscale.com/download/mac), connectez-vous
au même tailnet et connectez les deux ordinateurs. Ajoutez l’adresse Tailscale
d’Eitr dans Moonlight et associez comme précédemment. La politique du tailnet doit
autoriser les ports de diffusion. Les réglages web de Sunshine restent locaux.

Rétablir la configuration d’accès extérieur rétablit l’opérateur et les états de démarrage et
d’exécution initiaux ; compte et paquets sont conservés. Un service déjà actif le
reste. Utilisez Disconnect avant si vous voulez couper la connexion. Les erreurs
restent visibles dans le terminal ; corrigez-les puis réessayez. Aucun paquet
n’est supprimé implicitement.

## Vérifications restantes

Les tests automatiques utilisent des simulations. Avec le propriétaire, vérifiez
capture Hyprland/NVIDIA, clavier, souris, audio, manette, deux moniteurs,
verrouillage et démarrage à la connexion ; puis association du MacBook et chemins
Tailscale directs/relayés. Des tests réussis ne valident pas ces fonctions matérielles.
