# Applications et installation

Avant l’installation des paquets officiels, le terminal indique qu’il recherche les mises à jour du système en attente. Cette vérification peut prendre un moment avant de vous demander le mot de passe administrateur. Les installations avec Flatpak indiquent également leur étape de préparation.

**SUPER + Space** et Principal > Applications ouvrent la même liste. Enter lance une application. Delete permet de la désinstaller dans Applications après confirmation. La recherche globale par **SUPER + F** lance les applications sans proposer leur désinstallation. Il n’existe pas de menu distinct fondé sur des applications épinglées.

Saisir dans le menu principal recherche les applications installées et les actions de tous les sous-menus. Dans un sous-menu comme Système ou Installer, la recherche couvre celui-ci et ses descendants. Les lignes de sous-menu se terminent par **>** ; **Shift + Backspace** revient au parent.

## Installer

Appuyez sur Delete sur une entrée installée dans les listes d’applications et d’outils d’Installer pour la désinstaller après confirmation. Applications web conserve son action de suppression. Paquets (Pacman et Yay) reste réservé à l’installation, sans action Delete. Les dépendances nécessaires au système ne sont jamais supprimées récursivement ; pacman refuse une suppression qui casserait un autre paquet.

Les ensembles de langages gérés affichent leur avertissement complet dans un terminal avant de demander confirmation avec [y/N] ; Enter annule. La suppression de Node inclut toutes les versions gérées par NVM et leurs outils npm globaux. Celle de Python concerne les versions gérées par uv et uv lui-même, pas Python du système. Pour Java, les versions actuelles de Java et Maven dans SDKMAN sont supprimées ; pour Rust, seule la chaîne d’outils stable est supprimée. Rails et Laravel suppriment leurs outils de framework en conservant Ruby, PHP et Composer. Vos projets, paramètres et identifiants sont conservés, mais certains outils et environnements dépendants pourraient ne plus fonctionner. La suppression des assistants natifs conserve les versions en cache et les paramètres.


Les applications présentes affichent **Installé** sous leur nom ; les choisir l’indique au lieu de réinstaller. Cela reconnaît aussi les outils installés par leur gestionnaire, comme Java avec SDKMAN ou Node.js avec NVM. Un paquet nécessitant un environnement d’exécution, tel Java pour DBeaver, n’en ajoute un petit que si aucun paquet ne le fournit déjà.

- **CLI d’IA:** clients IA facultatifs en ligne de commande.
- **Navigateurs:** choix de navigateurs compatibles.
- **Bases de données:** outils facultatifs comme DBeaver, clients de bases et Valkey, le serveur compatible Redis distribué par Arch à la place de Redis.
- **Langages de développement:** outils facultatifs ; Java/Flutter ne sont pas des dépendances obligatoires du bureau.
- **Outils JavaScript:** environnements d’exécution et outils JavaScript facultatifs.
- **Paquets > Pacman** et **Paquets > Yay (AUR):** recherche de paquets officiels Arch ou communautaires AUR, avec origine et état d’installation. La recherche est en haut, les paquets dessous et les détails de la sélection en bas. **Ctrl+B** alterne avec les instructions de compilation (PKGBUILD), **Ctrl+O** ouvre la page web, **Tab** sélectionne plusieurs paquets et **Enter** les installe. Les paquets AUR sont compilés ici à partir de ces instructions : lisez-les d’abord. Ce ne sont pas des paquets officiels Arch.

Les terminaux d’installation, mise à jour et configuration affichent le bandeau EITR aux couleurs du thème. Les tâches réussies se ferment normalement ; les échecs restent visibles. Les rapports comme Nettoyage restent ouverts pour lecture. Les terminaux ordinaires et À propos n’affichent pas ce bandeau.

Appuyez sur **Échap** pour fermer les terminaux de tâches, de comptes, de rapports et À propos qui attendent une touche. Entrée reste utilisée pour les réponses et confirmations, notamment après avoir noté la clé de récupération et pour éteindre le programme d’installation.

## Outils

**Calculatrice** dans Applications, ou la touche calculatrice, ouvre celle d’Eitr aux couleurs du thème. Saisissez ou cliquez : `+ − × ÷`, `^` pour les puissances, `%` pour les pourcentages (`200×15%`), `√` et parenthèses. Un nombre avant une parenthèse multiplie (`2(3+4)`). Enter affiche le résultat, Backspace supprime un caractère, Escape efface (deux fois ferme), Ctrl+C ou **Copier** copie le résultat. L’expression est calculée sans être exécutée comme du code.

**Dictée hors ligne** transforme la parole en texte sans l’envoyer hors de l’ordinateur. Maintenez **SUPER + D**, parlez et relâchez : les mots sont saisis au curseur dans la langue parlée. Pendant l’écoute, le point rouge à gauche de l’horloge devient une petite onde suivant votre voix, pour confirmer sa réception ; après relâchement, elle pulse jusqu’à la saisie du texte. Le premier usage télécharge une fois le modèle vocal (148 Mo, vérifié avec sa somme de contrôle publiée) dans `~/.local/share/eitr/whisper/` ; ensuite, tout fonctionne hors ligne. La transcription prend un moment après relâchement, davantage sur les anciens processeurs. L’enregistrement s’arrête au relâchement de D, même si SUPER a été relâché avant, ou après 120 secondes ; les mots sont ensuite transcrits comme d’habitude.

**Principal > Outils > Rappels > Nouveau rappel** demande quand (durée comme `10m` ou `1h30m`, heure comme `18:30`) et quoi, puis affiche à cet instant une notification restant jusqu’à fermeture. **Rappels à venir** liste ceux en attente ; choisissez-en un pour l’annuler. Ils survivent au redémarrage ; ceux échus pendant l’arrêt apparaissent à la prochaine connexion. Dans un terminal : `eitr remind 25m Take the tea out` ; `eitr remind` seul les liste.

## Jeux

Principal > Jeux liste **GeForce NOW**, **RetroArch** et **Steam**. Choisir l’un l’ouvre s’il est installé, sinon l’installe. RetroArch provient des paquets officiels Arch avec des cœurs pour NES, SNES, Game Boy et Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP et Dreamcast. Ajoutez vos jeux et les fichiers BIOS nécessaires aux consoles ; Eitr ne fournit ni les uns ni les autres. GeForce NOW s’installe par Flatpak.

**Basculer > Mode jeu** limite les interventions du bureau : animations, flou et ombres désactivés, notifications contextuelles différées (Ne pas déranger), profil de performances activé si disponible. Le désactiver restaure exactement ses changements. Steam inclut **GameMode** et **MangoHud** : ajoutez `gamemoderun mangohud %command%` aux options de lancement du jeu dans Steam pour optimiser le processeur et afficher les FPS.

Le paquet LocalSend inclut ses besoins d’exécution : le Flutter SDK n’est pas nécessaire pour l’utiliser. Les outils de développement restent facultatifs.

Pour mettre à jour, consultez [Mises à jour et nettoyage](handbook:maintenance) ; installer un seul paquet n’équivaut pas à la Mise à jour du système protégée par instantanés.

**Visualiseur de musique** dans **Principal > Outils** ouvre cava avec les couleurs du thème. Un clic droit sur l’égaliseur multimédia ouvre ce visualiseur ; le clic gauche ouvre toujours les détails multimédias. Appuyez sur **q** ou **Échap** pour le fermer. Si cava manque, il est installé au préalable.

## Rappels vocaux

Maintenez **SUPER + Shift + D**, parlez puis relâchez, ou saisissez du texte dans Principal > Outils > Rappels > Parler à l’assistant…. Eitr transcrit localement avec le modèle hors ligne de la dictée, puis consulte l’assistant choisi dans Développement > Assistant par défaut. Seuls la transcription et le contexte des rappels vont à son fournisseur ; l’audio reste local et est supprimé après transcription. L’assistant fonctionne sans fenêtre par la voie en lecture seule d’Eitr. Eitr valide son JSON et exécute les actions ; l’assistant ne reçoit aucun outil permettant des modifications.

Dites « Rappelle-moi d’appeler demain à 15 h » ou « Dentiste le 30 octobre à 15 h, prévenir 30 minutes avant ». Les rendez-vous déclenchent un avis une heure avant par défaut (ou selon le délai demandé), puis à l’heure prévue ; les rappels simples seulement à leur heure. En cas d’ambiguïté ou de détails manquants, un terminal affiche les choix numérotés en entier. Saisissez le numéro ou dictez-le avec SUPER + D ; Esc annule. Une notification indique le résultat. Vous pouvez aussi demander de lister ou d’annuler les rappels.

Nouveau rappel accepte `tomorrow 15:00`, les jours anglais (09:00 sans heure), `2026-10-30 09:00` et `Oct 30 15:00`. Mettez les dates contenant des espaces entre guillemets dans la CLI. Chaque avis possède son minuteur ; l’annulation les supprime tous. Les avis manqués apparaissent à la prochaine connexion. Le calendrier marque les jours concernés ; cliquez pour voir les heures et titres immédiatement actualisés. Les répétitions et la synchronisation externe ne sont pas encore prises en charge.

## Plugins

Un plugin est un dépôt Git contenant des scripts, des entrées Walker et éventuellement un service utilisateur. Les plugins disposent de toutes les permissions de votre compte. Eitr n’a pas vérifié leur code : faites confiance à l’auteur et au dépôt avant d’approuver une installation ou une mise à jour.

Principal > Installer > Plugins > Ajouter un plugin… demande une URL Git HTTPS ou, pour un dépôt privé, une URL SSH comme `git@github.com:you/plugin.git` (elle utilise vos clés SSH via l’agent). La vérification commence par l’avertissement de confiance, puis présente l’auteur du manifeste, le dépôt, le commit exact, l’auteur Git et sa date, les entrées et le service en arrière-plan. Appuyez sur `y` pour installer ; Enter ou Esc annule. Aucun code du plugin ne s’exécute avant approbation. Principal > Outils > Plugins présente ses actions ; la recherche dans Outils les trouve aussi. Le menu vide affiche Aucun plugin installé.

Mise à jour du système vérifie les plugins même sans mise à jour des paquets. Chaque mise à jour montre les anciens et nouveaux commits, leurs sujets et les fichiers modifiés, puis demande avec `[y/N]` ; Enter refuse. Les mises à jour non interactives ignorent les plugins. Installer > Plugins > le plugin propose Mise à jour et Supprimer ; la suppression demande confirmation et retire fichiers, entrées et service. Les mêmes parcours existent avec `eitr plugin list`, `eitr plugin add URL`, `eitr plugin update [ID]` et `eitr plugin remove ID`.

Les plugins résident uniquement dans `$XDG_DATA_HOME/eitr/plugins/<id>/` (par défaut `~/.local/share/eitr/plugins/`) ; les approbations dans `$XDG_STATE_HOME/eitr/plugins.json`. Les services utilisent `$XDG_CONFIG_HOME/systemd/user/eitr-plugin-<id>.service`. N’utilisez jamais sudo. Les mises à jour valident un candidat séparé et gardent le commit approuvé en cas de refus ou d’échec. Un plugin peut modifier vos fichiers ; sa suppression n’annule pas ces modifications.

### Référence du manifeste

La racine contient `eitr-plugin.json`. Seules ces clés sont admises : `id` (minuscules et chiffres séparés par des tirets simples), `name`, `description` (72 caractères maximum), `author`, `version`, `rows` (1–20) et `service` facultatif. Chaque entrée exige `title`, `description` (72 caractères maximum chacun) et `run` ; `icon` et `arguments` (liste de chaînes fixes) sont facultatifs. Un service accepte seulement `run` et éventuellement `arguments`. Les commandes utilisent argv, jamais des chaînes de shell. `run` doit désigner un exécutable interne au dépôt : chemins absolus, `..` et liens symboliques sortants sont refusés. Les clés JSON inconnues ou dupliquées sont refusées. Les sous-modules ne sont pas initialisés.

L’exemple dans `distro/plugins/example/` contient un manifeste et `notify.sh`, une action de notification sans service. Copiez-le dans votre dépôt Git, créez un commit et publiez une URL Git HTTPS pour essayer le parcours complet. Il est fourni comme documentation, sans installation automatique.
