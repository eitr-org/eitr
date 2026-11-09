# Sécurité et verrouillage

**SUPER + M** verrouille immédiatement l’écran. Cliquez sur l’icône Verrouillage automatique à gauche de la barre (après Utilisation IA) pour activer ou désactiver le verrouillage après inactivité ; son infobulle indique l’état. Activé, l’écran se verrouille après 15 minutes d’inactivité, s’éteint après 30 et l’ordinateur se met en veille après 60. Le Centre de contrôle propose le même réglage et un bouton Verrouiller.

Vingt secondes avant le verrouillage, les écrans compatibles réduisent leur luminosité à environ 30 % du niveau précédent (jamais à zéro). Toute activité rétablit exactement le niveau précédent, même après le verrouillage ; désactiver le verrouillage automatique le rétablit aussi. Les moniteurs externes sans contrôle de luminosité DDC sont ignorés.

## Mot de passe et authentification alternative

**Paramètres > Utilisateurs > Changer le mot de passe** change le mot de passe de votre compte et garde le trousseau de connexion ouvert avec lui. L’empreinte digitale et Clé de sécurité FIDO2 ont leurs propres procédures d’inscription et d’activation. Une clé de sécurité FIDO2 est un dispositif physique, pas le lecteur d’empreintes d’un portable. Inscrivez d’abord le dispositif, puis activez l’authentification. L’utilitaire sauvegarde les paramètres PAM ; gardez un mot de passe valide et un moyen d’accéder à un TTY.

Revenir à l’authentification par mot de passe rétablit l’accès uniquement par mot de passe. Ces changements concernent les services PAM de verrouillage, de connexion et de sudo pris en charge. Ils nécessitent du matériel compatible et les utilitaires installés. L’authentification par empreinte peut retarder brièvement la demande de mot de passe. Lire cette page ne modifie pas PAM.

## Pare-feu

Les nouvelles installations démarrent avec le pare-feu activé. Il refuse les connexions entrantes, sauf les réponses aux connexions lancées par votre ordinateur, la découverte des noms locaux et les connexions des applications de partage installées par Eitr : KDE Connect (ports 1714-1764) et LocalSend (53317). Les machines virtuelles et les conteneurs de votre ordinateur peuvent toujours y accéder ; le trafic sortant n’est jamais filtré. Si SSH est activé, il reste également accessible.

**Paramètres > Sécurité > Protection > Pare-feu** indique son état et permet de le modifier après confirmation. Sur les ordinateurs configurés avant son introduction, le pare-feu est initialement désactivé. Pour autoriser une autre application à recevoir des connexions, ajoutez un fichier dans `/etc/eitr/firewall.d/`, par exemple `game.nft` contenant :

```
add rule inet eitr_firewall input udp dport 27015 accept
```

Désactivez puis réactivez le pare-feu.

## Chiffrement des disques et TPM

Le chiffrement du disque est un choix proposé à l’installation. Déverrouillage du disque TPM peut ajouter un emplacement de clé TPM2 à une racine LUKS2 existante compatible ; l’installateur ne l’inscrit pas automatiquement. Gardez la phrase secrète et une clé de récupération hors ligne, jamais dans des captures d’écran ou des fichiers du dépôt. Des changements de firmware ou de Secure Boot peuvent imposer la phrase secrète au prochain démarrage.

Lisez [Récupération et instantanés](handbook:recovery) avant de modifier l’authentification ou la configuration du TPM. [Secure Boot](handbook:secure-boot) est une procédure manuelle avancée : EITR n’inscrit pas de clés dans le firmware et ne signe pas les fichiers de démarrage pour vous. Une erreur peut empêcher le démarrage et même l’accès aux réglages du firmware sur certains appareils.

## Comptes utilisateur

**Paramètres > Utilisateurs > Créer un utilisateur…** crée une connexion distincte. Saisissez le nom d’utilisateur, le nom complet facultatif, le type de compte et le mot de passe, puis vérifiez et appuyez sur Entrée pour créer le compte. Échap annule avant toute application. Les comptes standard ne peuvent pas utiliser sudo ; les administrateurs rejoignent wheel et reçoivent une règle sudo protégée par mot de passe.

Le nouveau dossier personnel ne contient aucun fichier de votre compte. À la première connexion Hyprland via UWSM, Eitr exécute la configuration du bureau par utilisateur de l’installateur et adopte la structure du paquet sous l’identité du nouvel utilisateur. La configuration du shell peut nécessiter internet. Un échec conserve le marqueur pour la connexion suivante ; après réussite, elle ne se répète pas. Un échec de création laisse le compte incomplet verrouillé et expiré pour examen manuel.

Les administrateurs voient les onglets **Utilisateurs** et **Gérer** dans Paramètres > Utilisateurs ; les comptes standard ne voient que la liste des utilisateurs. Un Administrateur appartient à wheel et possède une règle sudo Eitr ; un compte Standard ne possède ni l’un ni l’autre. Gérer permet de créer des comptes, de changer leur type, de définir le mot de passe d’un autre compte et de supprimer des comptes. Chaque action ouvre une fenêtre de confirmation, puis un terminal de tâche : Entrée continue et Échap annule. La réinitialisation demande deux fois le nouveau mot de passe dans le terminal ; le trousseau de connexion de l’autre compte ne peut pas être mis à jour et conserve son ancien mot de passe. Pour votre propre compte, utilisez Changer le mot de passe dans Utilisateurs. La suppression conserve le dossier personnel par défaut ; choisissez Supprimer le dossier personnel pour effacer ses fichiers. Vous ne pouvez pas supprimer votre propre compte, un compte avec une session active ou le dernier administrateur ; ce dernier ne peut pas non plus devenir standard. Seuls les comptes humains (UID 1000–65533) peuvent être gérés. La liste est actualisée au retour du terminal.

Les comptes dont le groupe principal est wheel ne peuvent pas devenir standard ici ; modifiez d’abord leur groupe principal par administration manuelle.

## Photos de profil

Paramètres > Utilisateurs liste chaque compte de ce PC. Cliquez-y sur votre photo pour la changer, ou utilisez l’icône de corbeille dessous pour la retirer. Voir [Paramètres](handbook:system) pour choisir une image et ajuster son cadrage. Le Centre de contrôle affiche seulement la photo.
