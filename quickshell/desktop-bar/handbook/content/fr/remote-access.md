# Accès à distance

Ouvrez Paramètres > Streaming pour Sunshine et Moonlight, ou Walker > Paramètres > Périphériques > Streaming pour les mêmes actions. Le partage reste désactivé jusqu’à
son activation. Cette étape contrôle le bureau Eitr connecté et éveillé.
Le fonctionnement sans écran et wake on LAN viendront plus tard.
Si cet ordinateur se verrouille pendant le partage, l’écran distant affiche
l’écran de verrouillage : la personne connectée le voit et peut saisir le mot de
passe. Arrêtez le partage avant de vous absenter si la confidentialité compte.

Les dossiers de configuration regroupent les réglages. Streaming > Configuration du partage contient Configurer le partage, Paramètres de partage, Démarrer à la connexion, Désactiver le démarrage à la connexion, État détaillé et Restaurer la configuration du partage. Les actions de partage courantes (Démarrer le partage, Arrêter le partage, Associer un appareil, État du partage et Se connecter à un autre PC) restent directement dans Streaming.

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
sous-réseaux LAN privés directement connectés. TCP 47990 reste
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

## Partager l’écran de connexion

Paramètres > Streaming > Partager l’écran de connexion (aussi Streaming > Configuration du partage > Partager l’écran de connexion) permet à Moonlight d’atteindre ce PC pendant que l’écran de connexion s’affiche, après un redémarrage ou une déconnexion, pour vous connecter à distance. Cela modifie le système pour tout le monde : le mot de passe administrateur et une confirmation saisie sont demandés. Ne plus partager l’écran de connexion l’annule sans rien laisser ; Rétablir la configuration du partage le désactive aussi.

Il faut avoir lancé Configurer le partage, démarré une fois le partage avec le mot de passe de Sunshine défini, et associé au moins un appareil. L’écran de connexion accepte exactement les appareils associés à votre partage, avec le même nom de PC et le même certificat : Moonlight voit le même PC avant et après la connexion. Un appareil dissocié de votre partage est aussi refusé à l’écran de connexion dès le démarrage suivant. Toute personne qui détient un appareil associé voit l’écran de connexion, mais se connecter demande toujours le mot de passe d’un compte.

Un Sunshine distinct, sous le compte système `eitr-loginshare`, ne fonctionne que tant que personne n’est connecté sur ce PC. Dès qu’une personne se connecte, il s’arrête et le flux se termine : reconnectez-vous pour atteindre son propre partage s’il démarre à la connexion, sinon rien. Les appareils associés à une personne ne voient jamais le bureau d’une autre. La déconnexion relance le partage de l’écran de connexion. Il n’y a pas de son à l’écran de connexion.

## Moonlight sur un Mac

Installez [Moonlight](https://moonlight-stream.org/). Pour le premier essai, utilisez
le même réseau domestique. Ajoutez manuellement l’adresse LAN d’Eitr au besoin.
Sélectionnez le PC, lisez le PIN et utilisez Associer un appareil sur Eitr. Choisissez
Desktop pour contrôler applications et jeux. Sélectionnez l’écran dans Sunshine
et vérifiez chaque moniteur. Gaming > Moonlight et Se connecter à un autre PC installent
ou ouvrent le client Eitr dans le sens inverse. Les nouvelles installations incluent ces applications ; le partage reste désactivé tant que vous ne l’activez pas explicitement.

Raccourcis SUPER depuis le Mac : dans les réglages de Moonlight, activez **Capture system keyboard shortcuts** (en plein écran ou toujours). Ce n’est qu’ainsi que Moonlight envoie la touche Commande du Mac comme SUPER ; sinon, les raccourcis avec Commande restent sur le Mac. Ctrl+Alt+Maj+K active ou désactive la capture pendant une session.

## Ce qui a été vérifié

Les tests automatiques utilisent des simulations. Sur un vrai bureau (un puis deux
moniteurs) avec un MacBook sous Moonlight : configuration, démarrage du partage,
association par adresse, image, clavier, souris, audio, l’écran de verrouillage
(déverrouillé depuis le Mac), démarrage à la connexion, Arrêter le partage et
Restaurer la configuration sur le réseau domestique et depuis l’extérieur via un VPN. Les manettes, les autres
cartes graphiques et les autres clients n’ont pas été testés.

Streaming se trouve à côté de Connexions dans Périphériques. Sunshine affiche l’état du partage, la configuration, le démarrage/arrêt, le lancement à la connexion, l’association, les réglages, le diagnostic et la restauration. Moonlight affiche l’état d’installation et un bouton installer/ouvrir.
