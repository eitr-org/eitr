# Se repérer dans Système

Ouvrez **SUPER + F > Système**. Les actions sont regroupées par ordre alphabétique ; la recherche globale les trouve directement sans parcourir chaque groupe.

## Connectivité

**Bluetooth**, **Moteur de réseau**, **WiFi**. Les entrées de périphériques ouvrent les mêmes panneaux que la barre. Le choix du service réseau prépare le prochain démarrage sans relancer la connexion actuelle.

## Périphériques et saisie

**Audio**, **Limite de charge de la batterie**, **Écran**, **Clavier**, **Éclairage**, **Microphone**. La limite de charge exige un firmware de portable compatible. Écran regroupe luminosité, éclairage nocturne, choix du moniteur et profils d’énergie des portables compatibles.

**Éclairage** décide si les changements de thème recolorent ventilateurs, claviers et autres appareils OpenRGB. Cette option est désactivée par défaut pour laisser votre éclairage intact. **Suivre le thème** applique la couleur actuelle maintenant et à chaque changement de thème.

## Informations

**À propos**, **Utilisation de l’IA**, **Matériel**, **Signaler un problème**, **Météo**. À propos ouvre le résumé système EITR ; Signaler un problème recueille un rapport privé à lire avant envoi. Les autres entrées utilisent les panneaux natifs. Calendrier et vue des espaces restent accessibles depuis la barre et la recherche globale sans encombrer ce menu. Cherchez **Ragnarök** pour que Fenrir morde l’écran ; clic ou Escape termine l’effet plus tôt.

## Maintenance

**Nettoyage**, **Réinitialisation d’usine**, **Instantanés**, **Mise à jour**. La mise à jour complète et les mises à jour avancées de paquets sont séparées. La réinitialisation d’usine est destructive et impose deux avertissements. Lisez d’abord [Réinitialisation d’usine](handbook:factory-reset).

## Sécurité

**Clé de sécurité FIDO2**, **Empreinte digitale**, **Déverrouillage du disque TPM**, **Pare-feu**, **Revenir à l’authentification par mot de passe**, **Mettre à jour le mot de passe**. La documentation de Secure Boot se trouve dans **Apprendre > Manuel EITR > Secure Boot**, pas dans une action séparée de menu ou de sécurité.

## Dotfiles

Ouvre votre dossier de configuration dans VS Code, ou LazyVim si VS Code est absent. Gardez les réglages de moniteurs et de matériel propres à ce PC dans `~/.config/hypr/local.lua`, pas dans les valeurs communes. Ne collez ni tokens, ni clés de récupération, ni mots de passe dans les sauvegardes de configuration.

Les chapitres suivants détaillent les procédures et limites de sécurité.

## Langue

**Walker > Système > Langue** liste les langues, la langue actuelle étant cochée ; voir le [Guide de langue](handbook:language). Les noms anglais et traduits restent recherchables. Les sous-menus précèdent les actions, chacun trié par titre traduit. Le menu principal et Applications conservent leur ordre.
