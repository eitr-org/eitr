# Sécurité et verrouillage

**SUPER + M** verrouille immédiatement l’écran. Cliquez sur l’icône Verrouillage automatique à gauche de la barre (après Utilisation IA) pour activer ou désactiver le verrouillage après inactivité ; son infobulle indique l’état. Activé, l’écran se verrouille après 15 minutes d’inactivité, s’éteint après 30 et l’ordinateur se met en veille après 60. Le Centre de contrôle propose le même réglage et un bouton Verrouiller.

## Mot de passe et authentification alternative

**Système > Sécurité > Mettre à jour le mot de passe** change le mot de passe de votre compte. L’empreinte digitale et FIDO2 ont leurs propres procédures d’inscription et d’activation. Une clé de sécurité FIDO2 est un dispositif physique, pas le lecteur d’empreintes d’un portable. Inscrivez d’abord le dispositif, puis activez l’authentification. L’utilitaire sauvegarde les paramètres PAM ; gardez un mot de passe valide et un moyen d’accéder à un TTY.

Revenir à l’authentification par mot de passe rétablit l’accès uniquement par mot de passe. Ces changements concernent les services PAM de verrouillage, de connexion et de sudo pris en charge. Ils nécessitent du matériel compatible et les utilitaires installés. L’authentification par empreinte peut retarder brièvement la demande de mot de passe. Lire cette page ne modifie pas PAM.

## Pare-feu

Les nouvelles installations démarrent avec le pare-feu activé. Il refuse les connexions entrantes, sauf les réponses aux connexions lancées par votre ordinateur, la découverte des noms locaux et les connexions des applications de partage installées par Eitr : KDE Connect (ports 1714-1764) et LocalSend (53317). Les machines virtuelles et les conteneurs de votre ordinateur peuvent toujours y accéder ; le trafic sortant n’est jamais filtré. Si SSH est activé, il reste également accessible.

**Système > Sécurité > Pare-feu** indique son état et permet de le modifier après confirmation. Sur les ordinateurs configurés avant son introduction, le pare-feu est initialement désactivé. Pour autoriser une autre application à recevoir des connexions, ajoutez un fichier dans `/etc/eitr/firewall.d/`, par exemple `game.nft` contenant :

```
add rule inet eitr_firewall input udp dport 27015 accept
```

Désactivez puis réactivez le pare-feu.

## Chiffrement des disques et TPM

Le chiffrement du disque est un choix proposé à l’installation. Déverrouillage du disque TPM peut ajouter un emplacement de clé TPM2 à une racine LUKS2 existante compatible ; l’installateur ne l’inscrit pas automatiquement. Gardez la phrase secrète et une clé de récupération hors ligne, jamais dans des captures d’écran ou des fichiers du dépôt. Des changements de firmware ou de Secure Boot peuvent imposer la phrase secrète au prochain démarrage.

Lisez [Récupération et instantanés](handbook:recovery) avant de modifier l’authentification ou la configuration du TPM. [Secure Boot](handbook:secure-boot) est une procédure manuelle avancée : EITR n’inscrit pas de clés dans le firmware et ne signe pas les fichiers de démarrage pour vous. Une erreur peut empêcher le démarrage et même l’accès aux réglages du firmware sur certains appareils.
