# Terminal et éditeurs

**SUPER + Enter** ouvre le terminal choisi (Kitty par défaut). **SUPER + Ctrl + Enter** ouvre ou rejoint la session tmux principale. **SUPER + P** recherche des fichiers par correspondance approximative ; **SUPER + Ctrl + P** cherche dans leur contenu. Apprendre > Commandes Cmux, Commandes Tmux et Commandes LazyVim sont des références consultables : choisir une commande la copie sans l’exécuter.

Kitty affiche une courte traînée lors des sauts d’au moins deux cellules, comme Enter, Home/End ou les déplacements entre mots. Elle commence après 3 ms de repos et disparaît en 0,05–0,15 seconde. Réglez `cursor_trail`, `cursor_trail_decay` ou `cursor_trail_start_threshold` dans `~/.config/kitty/local.conf` ; `cursor_trail 0` la désactive. Vos options priment sur celles du paquet et survivent aux changements de thème.

### Feu du curseur

**Paramètres > Style > Terminal > Feu du curseur** propose **Désactivé** (par défaut) et **Activé**. Activé, il utilise l’effet intégré `cursor-trail-blaze` de Kitty pendant les déplacements, sans détecter la vitesse de frappe. Désactivé, il rétablit la traînée rapide normale et votre choix personnel de shader.

L’effet nécessite Kitty 0.49+ et `shader-slang`, inclus dans les dépendances d’Eitr. L’activation vérifie le shader avant d’enregistrer ou recharger Kitty. La préférence locale est `~/.config/eitr/terminal.json` ; l’utilitaire écrit `kitty/cursor-fire.conf`, inclus en dernier par le chargeur utilisateur. Activé, il choisit le shader de feu et abaisse le seuil à une cellule. Polices, thèmes et fichiers personnels restent intacts.

## Choisir son terminal

**Paramètres > Style > Terminal** dans Walker et **Centre de contrôle > Style > Terminal** proposent
**Kitty** (par défaut) et **Ghostty**. Le champ local `terminal` de
`~/.config/eitr/terminal.json` contrôle Super+Entrée, tmux, les sessions utilisateur,
les terminaux IA/projets et les actions Walker pour ouvrir dans un terminal.
Si Ghostty manque, le sélectionner ouvre le processus habituel d’installation du
paquet officiel : Entrée installe, Échap annule. Kitty reste sélectionné jusqu’à
la réussite de l’installation. Si Ghostty est ensuite supprimé, Kitty prend le relais.
Ghostty est facultatif et n’est pas inclus dans l’ISO.

Les changements de thème régénèrent `~/.config/ghostty/eitr.conf` avec les 16 couleurs
ANSI et les couleurs de fond, texte, sélection et curseur de texte. Les changements
de police reprennent la famille choisie ; la taille par défaut est de 10 points.
Ghostty utilise le même zsh et son invite, avec une opacité de 75 % et aucune marge
intérieure dans les fenêtres normales. Hyprland fournit le flou, les décorations et
les règles normales. La famille, la taille et le choix Auto/Clair/Sombre du pointeur
dans `eitr/cursor.json` restent appliqués par GTK et le compositeur, indépendamment
du curseur de texte.

Le lanceur Eitr charge le fichier généré. Placez vos réglages comme
`font-size = 12` ou `cursor-style = bar` dans `~/.config/ghostty/local.conf`, chargé
en dernier et conservé lors des changements de thème. Les sessions ouvertes
reçoivent le signal de rechargement pris en charge après un changement de thème
ou de police. Certaines options ne concernent que les nouvelles fenêtres.
La traînée et le Feu du curseur de Kitty restent propres à Kitty ; Ghostty ne
possède pas de réglage Blaze intégré équivalent.

Les terminaux de tâches, menus, état et configuration d’Eitr utilisent toujours
Kitty, y compris `eitr-menu-terminal`, `eitr-plugins` et `fif-terminal` : leurs
options `--class`, `--hold`, `--title` et règles de fenêtres flottantes dépendent
de Kitty. Choisir Ghostty ne les modifie pas.


## La commande eitr

`eitr` rassemble les outils d’Eitr ; lancez-le sans argument pour les lister. Il utilise les mêmes scripts que les menus pour garder le même comportement.

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Eitr" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
eitr about
```

`eitr about` ouvre la fenêtre d’informations d’Eitr ou remet la fenêtre existante au premier plan.

`eitr config` et `eitr git` transmettent leurs arguments à `eitr-config` et `eitr-git`. Chaque commande propose `--help`.

## Vos propres hooks

Un hook est un petit script personnel exécuté par Eitr à un moment donné. Il permet d’ajouter un comportement sans modifier Eitr. Placez un exécutable portant le nom de ce moment dans `~/.config/eitr/hooks/` :

| Fichier | Exécution | Argument reçu |
| --- | --- | --- |
| `post-update` | après la mise à jour du système ou une mise à jour pacman/AUR | `system`, `pacman`, `yay` ou `full` |
| `theme-set` | après changement de thème | nom du dossier du thème |
| `battery-low` | une fois à chaque baisse de batterie à 15% | pourcentage |
| `post-boot` | à la première connexion après chaque démarrage | aucun |

Pour recolorer Spotify avec Spicetify à chaque changement de thème, créez `~/.config/eitr/hooks/theme-set` :

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

Rendez-le exécutable avec `chmod +x ~/.config/eitr/hooks/theme-set`. Chaque hook dispose de 60 secondes. Sortie et erreurs vont dans `~/.local/state/eitr/hooks.log` ; un échec n’arrête jamais une mise à jour ou un changement de thème. `eitr hook list` liste les hooks ; `eitr hook run theme-set eitr` en essaie un. Les mises à jour ne touchent jamais ce dossier.

## cmux TUI

Exécutez `cmux` dans Kitty, ou `cmux --session work` pour une session nommée. cmux TUI est facultatif aux côtés de tmux ; il ne remplace ni Kitty ni ses raccourcis. Les nouvelles installations incluent un binaire officiel à version fixée sous `/usr/bin/cmux`. Les anciennes installations par utilisateur peuvent être prioritaires dans PATH ; vérifiez avec `command -v cmux`. `less` est inclus pour lire les sorties et fichiers texte.

Le préfixe par défaut est **Ctrl-b** : relâchez-le, puis appuyez sur la touche suivante.

| Raccourci | Action |
| --- | --- |
| Ctrl-b ? | Afficher les raccourcis actuels |
| Ctrl-b W | Créer un espace de travail |
| Ctrl-b c | Créer un écran |
| Ctrl-b % / Ctrl-b " | Diviser à droite / en bas |
| Ctrl-b t | Nouvel onglet terminal |
| Ctrl-b h/j/k/l | Focaliser à gauche/en bas/en haut/à droite |
| Ctrl-b s | Afficher/masquer la barre latérale |
| Ctrl-b d | Quitter localement ou se détacher d’un serveur |

Pour continuer sans interface, lancez `cmux --headless --session work`, puis `cmux attach --session work` pour rejoindre la session. Les onglets navigateur nécessitent Chrome/Chromium. Fermer des onglets, panneaux ou espaces peut affecter les tâches en cours ; vérifiez avant. Apprendre > Commandes Cmux comprend sessions, navigation, souris et raccourcis de fermeture. Les valeurs peuvent changer ou être personnalisées ; **Ctrl-b ?** est la référence actuelle.

## Terminaux de tâches

Les terminaux ouverts par les menus et notifications de mise à jour ou de rapport flottent au centre, au-dessus de vos fenêtres, avec le fond opaque du thème. Les sessions d’assistants IA et projets LazyVim de Développement s’ouvrent en fenêtres ordinaires en mosaïque avec fond translucide, comme vos terminaux personnels. Les terminaux ordinaires sont interactifs et sans bannière. Installation, mise à jour et configuration affichent la bannière runique d’EITR. Les tâches réussies se ferment normalement ; les échecs restent jusqu’à fermeture. Les rapports informatifs peuvent rester ouverts. Redémarrer Elephant ne doit pas fermer les applications lancées : les applications et terminaux ouverts depuis les menus, raccourcis et boutons de la barre utilisent des scopes d’application distincts dans une session uwsm. Sans uwsm, ils sont lancés directement. Elephant conserve l’arrêt du seul processus pour les auxiliaires du bureau et les lancements sans uwsm.

Appuyez sur **Échap** pour fermer les terminaux de tâches, de comptes, de rapports et À propos qui attendent une touche. Entrée reste utilisée pour les réponses et confirmations, notamment après avoir noté la clé de récupération et pour éteindre le programme d’installation.

## Historique du shell

`history` liste les commandes récentes. Dans zsh, vérifiez le vrai chemin avec :

```sh
printf '%s\n' "$HISTFILE"
```

Pour l’ouvrir dans Neovim :

```sh
nvim "$HISTFILE"
```

L’historique peut contenir des tokens ou identifiants ; ne le copiez pas dans un rapport de problème. Fermez les autres shells avant de l’éditer manuellement : ils peuvent réécrire leur historique en mémoire. L’historique étendu de zsh peut inclure des horodatages et commandes multilignes. Supprimez l’entrée entière, pas un fragment arbitraire. Gardez une sauvegarde privée pour pouvoir revenir en arrière.

## Apparence des éditeurs

Changer de thème actualise les préférences générées de VS Code et LazyVim. Les sessions LazyVim compatibles s’actualisent sans réouverture. Vos réglages et plugins peuvent imposer leurs couleurs ; vérifiez-les si l’éditeur ne suit pas le bureau. La police par défaut est intégrée uniquement là où l’application le permet.
