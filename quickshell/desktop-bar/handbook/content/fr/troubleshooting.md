# Dépannage

## Une action indique qu’un outil manque

Les nouvelles installations incluent les dépendances du bureau ; un Arch existant peut ne pas toutes les avoir. Lisez l’erreur et installez le paquet depuis Installer > Paquets > Pacman ou par une mise à jour complète normale. Ne supprimez pas BlueZ/iwd/PipeWire/WirePlumber au seul motif que leurs réglages sont dans des panneaux natifs : ces panneaux utilisent toujours ces services.

Ce manuel n’a pas besoin de `less` : il s’agit de Markdown fourni dans une superposition native. Si le catalogue manque ou est périmé, actualisez les fichiers du bureau EITR.

## Un utilitaire appartenant à root manque

Changement de service réseau, sécurité, limites de charge et récupération nécessitent des utilitaires vérifiés appartenant à root. Un bureau installé seulement par dotfiles peut ne pas encore avoir leurs paquets. Consultez le chapitre concerné. Ne contournez jamais la vérification en exécutant comme root un utilitaire téléchargé modifiable par l’utilisateur. Ouvrir le sélecteur ne doit pas déconnecter le réseau.

## Problèmes de configuration ou de services

Quickshell affiche une erreur de rechargement lisible et garde si possible la dernière configuration fonctionnelle. Corrigez le fichier indiqué ; ne redémarrez pas le gestionnaire de connexion à répétition. **Ne redémarrez jamais SDDM pendant votre session de bureau.**

Redémarrer Elephant recharge les menus. Son service doit conserver `KillMode=process` pour préserver les applications lancées. Les thèmes régénèrent les styles : si un changement disparaît, corrigez le générateur et le résultat produit.

## Vérifications d’installation et de récupération

EITR reste en bêta. Les tests en VM ne prouvent pas le fonctionnement de chaque adaptateur WiFi, agent Bluetooth, TPM, GPU, lecteur d’empreintes ou configuration Secure Boot. Le code actuel des services WiFi et de l’authentification d’entreprise est testé par simulation. Vérifiez l’authentification réelle avant d’en dépendre. Modifier les manifestes ne change pas les ISO existantes : reconstruisez le payload et l’ISO pour intégrer les changements aux nouvelles installations.

Sauvegardez les autres disques avant d’installer sur un SSD séparé et vérifiez soigneusement la cible. L’installateur efface le disque que vous confirmez. Gardez phrases secrètes et clés de récupération hors ligne. Les instantanés du même SSD ne sont pas des sauvegardes indépendantes. Commencez par [Récupération et instantanés](handbook:recovery).

## Signaler un problème

**Système > Informations > Signaler un problème** recueille versions d’EITR et des paquets, matériel graphique, erreurs Hyprland, services défaillants, avertissements récents, plantages de la dernière semaine, erreurs du démarrage précédent, journal d’installation et changements de paquets dans `~/Documents/eitr-problem-report-<time>.txt`, lisible uniquement par vous. Il retire nom d’utilisateur, nom du PC, chemin personnel, e-mail, IP et MAC. Les journaux peuvent encore citer applications ou fichiers : lisez le rapport avant envoi.

Rien n’est envoyé automatiquement. Le terminal indique seulement où le rapport est enregistré et propose de l’envoyer ou de le lire d’abord :

1. **Par e-mail** à `reports@eitr.info` : la messagerie ouvre un résumé ; joignez le fichier enregistré.
2. **Ouvrir une issue GitHub** nécessite un compte et ouvre une nouvelle issue du projet. Les issues sont publiques.
3. **Copier le rapport** permet de le coller ailleurs.
4. **Lire le rapport** l’ouvre dans votre éditeur.

Le rapport sert uniquement à identifier et corriger ce problème, puis il est supprimé. Un e-mail partage votre adresse ; répondez à tout moment pour demander la suppression du rapport.

### Quand un composant plante

Les Notifications de plantage sont activées par défaut. Un service utilisateur surveille les nouveaux enregistrements lisibles de systemd-coredump concernant vos propres programmes. Chaque plantage propose Signaler un problème, Ignorer et Ne plus notifier pour ce programme ; Demander à l’IA apparaît lorsqu’un assistant par défaut est installé et sélectionné. Les plantages répétés d’un programme sont limités à une notification toutes les cinq minutes. Activez ou désactivez-les dans Principal > Basculer ou Centre de contrôle > Réglages rapides. Les préférences et les chemins des programmes masqués restent dans `~/.config/eitr/crash-help.json` ; retirez un chemin de `ignored` pour recevoir à nouveau ses notifications.

Demander à l’IA ouvre votre assistant par défaut avec uniquement le programme, le signal et la trace de pile de `coredumpctl info`, en demandant une explication et une solution proposée sans modifier le système sans votre accord. Aucun fichier de vidage mémoire n’est transmis. Lorsque vous choisissez cette action, l’assistant peut envoyer le résumé à son fournisseur. Signaler un problème joint le même résumé au parcours existant : vérifiez-le avant de le partager ; rien n’est envoyé automatiquement.

## Personnalisations et mises à jour

Le code EITR se trouve sous `/usr/share/eitr` et est actualisé avec `eitr-desktop` ; vos réglages restent dans `~/.config`. Placez les changements durables hors de portée des mises à jour :

- Moniteurs, appareils, raccourcis et règles supplémentaires : `~/.config/hypr/local.lua`.
- Ajouts au shell : `~/.config/eitr/shell.local.zsh`.
- Options du terminal : `~/.config/kitty/local.conf`.
- Couleurs du lanceur : `~/.config/walker/style.override.css`.
- Remplacement complet d’un fichier fourni : même chemin relatif sous `~/.config/eitr/overrides`. Il ne reçoit plus les corrections des mises à jour.

Les fichiers comme `kitty/theme.conf` et le style Walker sont régénérés aux changements de thème et une fois après chaque mise à jour du paquet. Les anciennes copies restent sous `~/.local/state/eitr/generated-backups`. Si le format d’un réglage change, il est converti une fois à la connexion. Un échec est signalé et retenté à la prochaine connexion (`~/.local/state/eitr/migrations.log`). `eitr-config status` liste les réglages et remplacements actifs.
