# Se repérer dans les paramètres

Ouvrez **SUPER + F > Paramètres**. Les dossiers précèdent les actions, par ordre alphabétique. La recherche globale retrouve aussi les anciens noms, dont System et Toggle.

**Connectivité**, **Périphériques et saisie**, **Langue**, **Sécurité**, **Style**, **Système** sont des dossiers. **Centre de contrôle** ouvre les mêmes commandes que SUPER + virgule. **Fichiers de configuration** ouvre votre dossier de configuration dans VS Code ou LazyVim.

Connectivité ouvre les panneaux natifs Bluetooth et WiFi, le moteur réseau et l’accès à distance. Le choix du moteur prépare le prochain démarrage sans relancer la connexion active.

Périphériques et saisie contient Audio, Limite de charge de la batterie, Affichage, Clavier, Éclairage et Microphone. La limite apparaît uniquement avec une batterie système et nécessite un micrologiciel compatible. Les batteries de périphériques n’activent pas les commandes de portable. Affichage inclut luminosité, éclairage nocturne et profils d’énergie compatibles.

L’éclairage est désactivé par défaut. Suivre le thème permet de recolorer les appareils gérés par OpenRGB lors des changements de thème.

Style conserve les choix de thème, fond d’écran, verrouillage, polices et apparence du bureau. Toggle se nomme désormais Actions rapides dans Principal ; Démarrer l’écran de veille le lance immédiatement.

**Paramètres > Système** contient **Informations**, **Entretien**, **Canal de mise à jour**, **À propos**, **Mise à jour du système**. À propos ouvre le résumé du système EITR. Informations contient Utilisation de l’IA, Matériel, Signaler un problème et Météo. Calendrier, vue des espaces de travail et Ragnarök restent accessibles par recherche globale.

Entretien contient Réinitialisation d’usine, Instantanés, Vérifier ce PC, Choisir les miroirs les plus rapides et Nettoyage. La réinitialisation exige deux avertissements et une confirmation saisie ; lisez d’abord [Réinitialisation d’usine](handbook:factory-reset).

Sécurité conserve les commandes d’authentification, de pare-feu et d’utilisateurs. La documentation reste dans [Secure Boot](handbook:secure-boot). Placez les réglages matériels dans `~/.config/hypr/local.lua` et excluez les secrets des sauvegardes de configuration.

**Walker > Paramètres > Langue** liste les langues avec le choix actuel coché ; voir [Langue](handbook:language). Les noms anglais et traduits restent recherchables. Principal et Applications conservent leur ordre.

Sécurité: Accès des assistants, Clé de sécurité FIDO2, Empreinte digitale, Déverrouillage du disque TPM, Utilisateurs, Pare-feu, Revenir à l’authentification par mot de passe, Mettre à jour le mot de passe.
