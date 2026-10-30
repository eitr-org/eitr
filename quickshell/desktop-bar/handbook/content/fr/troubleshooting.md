# Dépannage

## Vérifier ce PC

Ouvrez **Paramètres > Système > Entretien > Vérifier ce PC** ou `eitr check`. Les vérifications lisent seulement, sans réparation ni redémarrage. Les listes de paquets ne sont pas actualisées. DNS utilise le réseau. `eitr check --json` affiche les détails techniques sans invite.

**Vérifications approfondies (mot de passe requis)**: Pour les vérifications approfondies, appuyez sur Entrée ; Échap les ignore. `sudo /usr/lib/eitr/eitr-system selfcheck-deeper` demande votre mot de passe dans le même terminal. Les résultats remplacent les vérifications ignorées correspondantes. Cela lit Snapper, les paires pré/post, la dernière mise à jour réussie, les qgroups Btrfs existants, le JSON de protection du démarrage, un manifeste d’usine déjà monté et les clés Arch Linux/Eitr avec `pacman-key --list-keys`. Aucun quota n’est activé et aucun point d’usine n’est monté. Les données absentes sont ignorées avec une raison ; le manifeste ne vérifie pas l’intégrité des archives. `fsck.vfat -n` vérifie uniquement une ESP FAT identifiée sans ambiguïté et non montée en écriture ; sinon la vérification demande son démontage et est ignorée.

Les unités en échec affichent trois noms au maximum et une commande d’état. Les descriptions des instantanés ne prouvent pas les étapes ultérieures ; les hooks n’ont pas d’horodatage. La barre n’a pas de requête structurée des erreurs. Ensuite **Entrée** copie le rapport expurgé et **Échap** ferme. Relisez avant de partager ; la copie nécessite `wl-copy`.


## Une action indique qu’un outil manque

Les nouvelles installations incluent les dépendances du bureau ; un Arch existant peut ne pas toutes les avoir. Lisez l’erreur et installez le paquet depuis Installer > Paquets > Pacman ou par une mise à jour complète normale. Ne supprimez pas BlueZ/iwd/PipeWire/WirePlumber au seul motif que leurs réglages sont dans des panneaux natifs : ces panneaux utilisent toujours ces services.

Ce manuel n’a pas besoin de `less` : il s’agit de Markdown fourni dans une superposition native. Si le catalogue manque ou est périmé, actualisez les fichiers du bureau EITR.

## Un utilitaire appartenant à root manque

Changement de service réseau, sécurité, limites de charge et récupération nécessitent des utilitaires vérifiés appartenant à root. Un bureau installé seulement par dotfiles peut ne pas encore avoir leurs paquets. Consultez le chapitre concerné. Ne contournez jamais la vérification en exécutant comme root un utilitaire téléchargé modifiable par l’utilisateur. Ouvrir le sélecteur ne doit pas déconnecter le réseau.

## Problèmes de configuration ou de services

Quickshell affiche une erreur de rechargement lisible et garde si possible la dernière configuration fonctionnelle. Corrigez le fichier indiqué ; ne redémarrez pas le gestionnaire de connexion à répétition. **Ne redémarrez jamais SDDM pendant votre session de bureau.**

Redémarrer Elephant recharge les menus. Son service doit conserver `KillMode=process` pour les auxiliaires et les lancements sans uwsm. Dans une session uwsm, les applications et terminaux lancés utilisent des scopes d’application distincts. Les thèmes régénèrent les styles : si un changement disparaît, corrigez le générateur et le résultat produit.

## Les données WiFi ne s’actualisent plus

La barre partage un seul processus de lecture WiFi entre les écrans. S’il se
termine, les dernières données valides restent marquées comme périmées pendant
les tentatives de redémarrage, de plus en plus espacées. Après six tentatives
infructueuses, il attend une relance explicite. Les commandes natives restent
disponibles. Les actions WiFi partagent une file ordonnée et un état occupé entre les écrans. Si une action dépasse son délai ou si le processus s’arrête, son résultat est inconnu : actualisez l’état avant de réessayer explicitement. Les écritures ne sont jamais répétées automatiquement. La génération de QR conserve son auxiliaire séparé.

Pour consulter l’état technique, utilisez
`eitr-shell desktop-bar ipc call -- data status`. La sortie indique l’âge des
données, les codes d’erreur, les lectures en cours, les observateurs et les
redémarrages, sans noms ni adresses réseau. Réessayez avec
`eitr-shell desktop-bar ipc call -- data retry`.

La capture OBS utilise le même processus partagé entre les écrans. Une seule
vérification est effectuée toutes les 2 secondes uniquement tant qu’une fenêtre
ou un processus OBS est connu. Les détails d’enregistrement sont actualisés
toutes les 2 secondes uniquement lorsqu’un panneau d’enregistrement est ouvert
et fournissent aussi l’état partagé. Un état inconnu conserve le dernier état
de capture connu et désactive les commandes jusqu’à une actualisation réussie.
Les actions de capture et les modifications d’options partagent une file
ordonnée. Si le délai expire ou si le processus s’arrête, le résultat reste
inconnu et l’action n’est jamais répétée automatiquement. La commande OBS
autonome reste disponible pour Walker et les raccourcis de capture d’écran.

La batterie, les profils d’énergie et le mode avion partagent aussi ce processus. La batterie est lue toutes les 30 secondes ; les profils et les radios uniquement lorsque les panneaux correspondants sont ouverts. Les batteries de périphériques n’activent pas les commandes pour portable. Les hooks et alertes de batterie faible conservent leurs seuils. Les actions de profil et de mode avion sont ordonnées, signalent les erreurs au panneau demandeur et ne sont jamais répétées après un résultat inconnu. Les commandes autonomes restent disponibles.

## Vérifications d’installation et de récupération

EITR reste en bêta. Les tests en VM ne prouvent pas le fonctionnement de chaque adaptateur WiFi, agent Bluetooth, TPM, GPU, lecteur d’empreintes ou configuration Secure Boot. Le code actuel des services WiFi et de l’authentification d’entreprise est testé par simulation. Vérifiez l’authentification réelle avant d’en dépendre. Modifier les manifestes ne change pas les ISO existantes : reconstruisez le payload et l’ISO pour intégrer les changements aux nouvelles installations.

Sauvegardez les autres disques avant d’installer sur un SSD séparé et vérifiez soigneusement la cible. L’installateur efface le disque que vous confirmez. Gardez phrases secrètes et clés de récupération hors ligne. Les instantanés du même SSD ne sont pas des sauvegardes indépendantes. Commencez par [Récupération et instantanés](handbook:recovery).

## Signaler un problème

**Paramètres > Système > Informations > Signaler un problème** recueille versions d’EITR et des paquets, matériel graphique, erreurs Hyprland, services défaillants, avertissements récents, plantages de la dernière semaine, erreurs du démarrage précédent, journal d’installation et changements de paquets dans `~/Documents/eitr-problem-report-<time>.txt`, lisible uniquement par vous. Il retire nom d’utilisateur, nom du PC, chemin personnel, e-mail, IP et MAC. Les journaux peuvent encore citer applications ou fichiers : lisez le rapport avant envoi.

Rien n’est envoyé automatiquement. Le terminal indique seulement où le rapport est enregistré et propose de l’envoyer ou de le lire d’abord :

1. **Par e-mail** à `reports@eitr.info` : la messagerie ouvre un résumé ; joignez le fichier enregistré.
2. **Ouvrir une issue GitHub** nécessite un compte et ouvre une nouvelle issue du projet. Les issues sont publiques.
3. **Copier le rapport** permet de le coller ailleurs.
4. **Lire le rapport** l’ouvre dans votre éditeur.

Le rapport sert uniquement à identifier et corriger ce problème, puis il est supprimé. Un e-mail partage votre adresse ; répondez à tout moment pour demander la suppression du rapport.

### Quand un composant plante

Les Notifications de plantage sont activées par défaut. Un service utilisateur surveille les nouveaux enregistrements lisibles de systemd-coredump concernant vos propres programmes. Chaque plantage propose Signaler un problème, Ignorer et Mettre ce programme en sourdine ; Demander à l’IA apparaît lorsqu’un assistant par défaut est installé et sélectionné. Les plantages répétés d’un programme sont limités à une notification toutes les cinq minutes. Un plantage qui met fin à la session est proposé à la connexion suivante, mais pas ceux des programmes qui plantent dans la minute suivant une déconnexion, un redémarrage ou un arrêt : ils perdent seulement le bureau autour d’eux. Activez ou désactivez-les dans Principal > Actions rapides ou Centre de contrôle > Réglages rapides. Les préférences et les chemins des programmes masqués restent dans `~/.config/eitr/crash-help.json` ; retirez un chemin de `ignored` pour recevoir à nouveau ses notifications.

Demander à l’IA ouvre votre assistant par défaut avec uniquement le programme, le signal et la trace de pile de `coredumpctl info`, en demandant une explication et une solution proposée sans modifier le système sans votre accord. Aucun fichier de vidage mémoire n’est transmis. Lorsque vous choisissez cette action, l’assistant peut envoyer le résumé à son fournisseur. Signaler un problème joint le même résumé au parcours existant : vérifiez-le avant de le partager ; rien n’est envoyé automatiquement.

## Personnalisations et mises à jour

Le code EITR se trouve sous `/usr/share/eitr` et est actualisé avec `eitr-desktop` ; vos réglages restent dans `~/.config`. Placez les changements durables hors de portée des mises à jour :

- Moniteurs, appareils, raccourcis et règles supplémentaires : `~/.config/hypr/local.lua`.
- Ajouts au shell : `~/.config/eitr/shell.local.zsh`.
- Options du terminal : `~/.config/kitty/local.conf`.
- Couleurs du lanceur : `~/.config/walker/style.override.css`.
- Remplacement complet d’un fichier fourni : même chemin relatif sous `~/.config/eitr/overrides`. Il ne reçoit plus les corrections des mises à jour.

Les fichiers comme `kitty/theme.conf` et le style Walker sont régénérés aux changements de thème et une fois après chaque mise à jour du paquet. Les anciennes copies restent sous `~/.local/state/eitr/generated-backups`. Si le format d’un réglage change, il est converti une fois à la connexion. Un échec est signalé et retenté à la prochaine connexion (`~/.local/state/eitr/migrations.log`). `eitr-config status` liste les réglages et remplacements actifs.

Les tâches échouées proposent **A : demander à l’IA** si un assistant par défaut est choisi ; **Échap** ferme. Seules les 200 dernières lignes restent en mémoire, sans séquences ANSI et avec les lignes contenant des secrets évidents masquées avant partage : un assistant cloud envoie cette sortie à son fournisseur, tandis que Ratatoskr la garde sur ce PC.


La topologie des écrans, la luminosité et la lumière nocturne partagent aussi le broker. Les événements des moniteurs et les changements d’écran principal actualisent la géométrie de tous les écrans. La luminosité et la lumière nocturne ne sont actualisées que lorsqu’elles sont observées ; la luminosité DDC ne fait pas l’objet de lectures périodiques. Les essais d’affichage conservent leur retour automatique indépendant même si la barre ou le broker s’arrête. Les commandes autonomes d’affichage et de réduction et restauration de luminosité restent disponibles.

Le matériel utilise un seul échantillonneur du broker pour tous les écrans et pour l’action Matériel du centre de contrôle. Ouvrir un panneau actualise immédiatement les données, puis toutes les deux secondes tant qu’un panneau matériel reste ouvert. Fermer le dernier panneau arrête les mesures. L’identité du processeur, du disque racine et du GPU reste en mémoire pendant la session du broker, y compris les sondes GPU indisponibles ou trop lentes. Si une lecture échoue, les dernières sections valides restent visibles. La CLI autonome `system-details.py` reste disponible ; `eitr-shell desktop-bar ipc call -- data status` inclut le diagnostic `hardware.details`.

L’accès distant utilise le broker partagé : l’état de Tailscale et Sunshine est actualisé à l’ouverture puis toutes les 10 secondes tant qu’un panneau distant l’observe. Fermer le dernier panneau arrête les lectures. La disponibilité de la politique est lue uniquement au démarrage et lors de ses changements. Les actions utilisent toujours les outils Walker ; le broker ne modifie aucun réglage distant. La CLI `remote-status.py` reste disponible. `eitr-shell desktop-bar ipc call -- data status` inclut les diagnostics `remote.status` et `remote.availability`.

La météo partage une prévision par défaut entre les écrans et les panneaux, avec un cache et une actualisation de 15 minutes. Les recherches et les villes alternatives appartiennent uniquement au panneau demandeur et ne remplacent pas la prévision par défaut. L’utilisation de l’IA partage son cache et s’actualise à l’ouverture, puis toutes les cinq minutes uniquement tant qu’un panneau d’utilisation est ouvert. Fermer le dernier panneau empêche le démarrage des tâches de comptes en attente ; les appels actifs se terminent dans leurs délais existants, puis l’adaptateur IA est libéré. Les délais imposés par les fournisseurs sont respectés. Les commandes autonomes de météo et d’IA et le fichier de sélection de session restent disponibles. `eitr-shell desktop-bar ipc call -- data status` inclut les compteurs `weather.default` et `ai.usage`, sans noms de comptes ni réponses des fournisseurs.
