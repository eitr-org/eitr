# Accès à distance

Ouvrez Paramètres > Streaming pour Sunshine et Moonlight, ou Walker > Paramètres > Périphériques > Streaming pour les mêmes actions. Le partage reste désactivé jusqu’à
son activation. Cette étape contrôle le bureau Eitr connecté et éveillé.
Le fonctionnement sans écran, avant connexion et wake on LAN viendront plus tard.
Si cet ordinateur se verrouille pendant le partage, l’écran distant affiche
l’écran de verrouillage : la personne connectée le voit et peut saisir le mot de
passe. Arrêtez le partage avant de vous absenter si la confidentialité compte.

Les dossiers de configuration regroupent les réglages. Streaming > Configuration du partage contient Configurer le partage, Paramètres de partage, Démarrer à la connexion, Désactiver le démarrage à la connexion, État détaillé et Restaurer la configuration du partage. Les actions de partage courantes (Démarrer le partage, Arrêter le partage, Associer un appareil, État du partage et Se connecter à un autre PC) restent directement dans Streaming. Tailscale est le plugin officiel Tailscale, avec son propre panneau dans la barre.

État détaillé ouvre un terminal de diagnostic qui reste ouvert jusqu’à un appui sur Esc.

## Sunshine sur Eitr

Dans Partager ce PC, choisissez Configurer le partage. Le responsable de version compile
le paquet natif signé d’Eitr depuis les sources officielles, sans compilation AUR
au premier clic. Flatpak et AppImage ne proposent pas la capture KMS. Les réglages
et appareils associés sont conservés. Ne lancez pas une deuxième instance.

Lisez l’avertissement de contrôle total et saisissez `yes` uniquement pour accepter
la capture KMS et les entrées virtuelles du clavier, de la souris et de la manette. L’état initial est conservé dans `/var/lib/eitr/remote-access`. La configuration
ajoute une règle udev pour uinput, charge uinput au démarrage, accorde l’accès à
votre utilisateur et applique `cap_sys_admin+p` à Sunshine.

Rétablir la configuration du partage
rétablit les fichiers et l’ACL d’origine et retire les permissions de capture. Si la configuration a chargé uinput, l’annulation le décharge aussi. Si une autre
application l’utilise encore, l’échec est signalé et le journal est conservé pour
fermer l’application puis réessayer.

Démarrer le partage demande confirmation et ouvre `https://localhost:47990`. Acceptez le
certificat local autosigné uniquement à cette adresse. Définissez un identifiant
et un mot de passe fort avant l’association. Ouvrir les réglages rouvre les réglages ;
Associer un appareil ouvre la page du PIN. Saisissez uniquement le PIN de votre appareil
Moonlight. Eitr impose `upnp=off`. Ne configurez pas de redirection de ports sur le routeur.

TCP 47984, 47989 et 48010 et UDP 47998-48000 sont autorisés uniquement depuis les
sous-réseaux LAN privés directement connectés et `tailscale0`. TCP 47990 reste
accessible seulement depuis ce PC, même si une autre règle autorise l’accès. Les réseaux sont déterminés à chaque démarrage du partage ; relancez-le après un
changement de réseau.

Utilisez uniquement un réseau domestique de confiance. Arrêter le partage désactive aussi le démarrage automatique et ferme les ports, y compris
les flux existants. Une défaillance du service les ferme aussi ; les ouvertures ne
survivent pas au redémarrage. Après le premier démarrage, Démarrer et Arrêter le partage basculent aussitôt, sans question ni mot de passe.

Démarrer à la connexion est facultatif et bascule aussitôt depuis le panneau Streaming ou le menu ;
Désactiver le démarrage à la connexion conserve le démarrage manuel. État du partage affiche les erreurs.

Au premier démarrage, la diffusion reste bloquée pendant la définition du mot de passe. Revenez au terminal et confirmez sa définition ; votre mot de passe administrateur autorise alors le contrôle à distance.

Une mise à jour du paquet Sunshine remplace l’exécutable, ce qui retire sa capacité
de capture ; la mise à jour la rend ensuite au compte qui a configuré le partage. Si le
partage ne démarre toujours pas, l’interrupteur Streaming en donne la raison :
configurez à nouveau le partage, ou déconnectez-vous puis reconnectez-vous après une
première configuration. Le journal d’annulation initial est conservé.

Sunshine utilise la capacité KMS uniquement comme root ou avec le compte de partage : la configuration applique `root:eitr-sharing`, mode `0750`, et ajoute votre compte à ce groupe système. Déconnectez-vous puis reconnectez-vous avant de démarrer pour actualiser les groupes du service utilisateur. La configuration laisse le processus actif ; un redémarrage avant la prochaine connexion peut échouer.

Arrêter conserve les permissions. Rétablir retire le compte du groupe et toutes les capacités du fichier, puis applique `root:root`, mode `0755`, même pour les anciens journaux. Après une mise à jour du paquet, la configuration répare le propriétaire et le mode avant de réattribuer la capacité.

## Moonlight sur un Mac

Installez [Moonlight](https://moonlight-stream.org/). Pour le premier essai, utilisez
le même réseau domestique. Ajoutez manuellement l’adresse LAN d’Eitr au besoin.
Sélectionnez le PC, lisez le PIN et utilisez Associer un appareil sur Eitr. Choisissez
Desktop pour contrôler applications et jeux. Sélectionnez l’écran dans Sunshine
et vérifiez chaque moniteur. Gaming > Moonlight et Se connecter à un autre PC installent
ou ouvrent le client Eitr dans le sens inverse. Les nouvelles installations incluent ces applications ; le partage reste désactivé tant que vous ne l’activez pas explicitement.

Raccourcis SUPER depuis le Mac : dans les réglages de Moonlight, activez **Capture system keyboard shortcuts** (en plein écran ou toujours). Ce n’est qu’ainsi que Moonlight envoie la touche Commande du Mac comme SUPER ; sinon, les raccourcis avec Commande restent sur le Mac. Ctrl+Alt+Maj+K active ou désactive la capture pendant une session.

## Tailscale sur les deux ordinateurs

Installez le plugin officiel **Tailscale** (Thèmes et plugins > Plugins) et placez son
icône depuis Centre de contrôle > Plugins. L’étape **Configurer** de son panneau
installe Tailscale, active et démarre `tailscaled.service` et définit votre utilisateur
comme opérateur. La connexion au compte, la connexion au réseau et la déconnexion ne
demandent donc aucun mot de passe. Se connecter ouvre la page de connexion Tailscale
dans le navigateur. Le panneau affiche l’adresse Tailscale de ce PC, chaque appareil et
si son chemin est direct, relayé ou inactif, envoie un ping à un appareil, envoie des
fichiers avec Taildrop, ouvre un rapport détaillé et annule la configuration d’Eitr
(l’opérateur et l’état du service précédents reviennent ; le compte Tailscale et les
paquets restent).

Les chemins relayés peuvent augmenter la latence et réduire la qualité.

Installez [Tailscale sur le Mac](https://tailscale.com/download/mac), connectez-vous
au même tailnet et connectez les deux ordinateurs. Ajoutez l’adresse Tailscale
d’Eitr dans Moonlight et associez comme auparavant. La politique du tailnet doit
autoriser les ports de streaming. Les réglages web de Sunshine restent locaux.

## Ce qui a été vérifié

Les tests automatiques utilisent des simulations. Sur un vrai bureau (un puis deux
moniteurs) avec un MacBook sous Moonlight : configuration, démarrage du partage,
association par adresse, image, clavier, souris, audio, l’écran de verrouillage
(déverrouillé depuis le Mac), démarrage à la connexion, Arrêter le partage et
Restaurer la configuration sur le réseau domestique, ainsi que la configuration,
la connexion et l’accès Tailscale depuis l’extérieur. Les manettes, les autres
cartes graphiques et les autres clients n’ont pas été testés.

Streaming se trouve à côté de Connexions dans Périphériques. Sunshine affiche l’état du partage, la configuration, le démarrage/arrêt, le lancement à la connexion, l’association, les réglages, le diagnostic et la restauration. Moonlight affiche l’état d’installation et un bouton installer/ouvrir. Tailscale est un plugin avec son propre panneau.
