# Comptes Git

Ouvrez **Développement > Comptes Git**. Vous pouvez utiliser simultanément des comptes GitHub et GitLab, y compris plusieurs comptes du même fournisseur ou serveur d’entreprise. Les nouvelles installations incluent GitHub CLI (`gh`) et GitLab CLI (`glab`). Les ISO existantes doivent être reconstruites pour incorporer les changements.

Chaque ligne indique où Git utilise le compte : **Par défaut**, ses dossiers ou **Pas encore utilisé**. Enter ouvre les actions ; Shift+Backspace revient à la liste.

## Première configuration

1. **Ajouter un compte** ouvre un formulaire : fournisseur, nom du compte, nom et e-mail de l’auteur des commits, serveur et clé SSH privée existante (choisie dans `~/.ssh`), ou aucune pour l’instant. Il demande ensuite si ce compte est celui par défaut et quel dossier l’utilise seul, présente le résultat et enregistre avec Enter.
2. **Importer la configuration existante** lit les identités configurées manuellement : valeurs par défaut `user.name`/`user.email` et règles par dossier `includeIf "gitdir:…"` dans `~/.gitconfig` ou `~/.config/git/config`, dont l’alias SSH et la clé employés par un fichier inclus (`url.<alias>.insteadOf`). Il montre ses résultats et crée les comptes et règles correspondants après confirmation. Vos fichiers restent intacts ; les motifs de dossiers avec jokers sont indiqués comme ignorés.

## Compte par défaut et dossiers

Le compte **par défaut** s’applique aux dossiers sans compte propre. Un compte **de dossier** ne s’applique qu’aux dépôts de ce dossier. Le dossier le plus précis l’emporte ; les réglages locaux du dépôt et les options de ligne de commande ou d’environnement Git restent prioritaires. EITR conserve configuration globale et commentaires, ajoute une inclusion marquée en fin de `~/.gitconfig`, et les règles confirmées prévalent sur les identités d’inclusions externes.

Chaque action Walker est confirmée avant enregistrement et signalée par notification : **Définir par défaut** ou **Ne plus utiliser par défaut**, **Ajouter un dossier** (choisissez `~/Development`, un sous-dossier ou **Autre dossier…** pour saisir un chemin) et **Supprimer le dossier**. Git considère le vrai répertoire `.git` ; les worktrees liés et sous-modules peuvent suivre le compte d’un dépôt parent.

## Clés SSH

L’identité des commits ne donne pas accès au dépôt. **Afficher la clé publique** affiche et copie la clé publique, puis indique la page du fournisseur où l’ajouter (GitHub : Settings > SSH keys). **Choisir une clé SSH existante** choisit une clé dans `~/.ssh` ; **Créer une clé SSH** crée une Ed25519 avec phrase secrète et affiche sa clé publique. **Tester la connexion** montre la réponse du fournisseur, comme "Hi username!", dans une notification. Ne partagez jamais une clé privée.

Les clés s’appliquent uniquement au serveur SSH du fournisseur. Le lanceur résout les alias existants sans connexion, puis utilise seulement la clé choisie en ignorant les autres réglages SSH pour cette connexion. Les connexions proxy sont refusées ; conservez un `core.sshCommand` local au dépôt pour les configurations avancées. La vérification des serveurs connus reste active. Sans clé configurée, le compte utilise SSH normalement, pas la clé d’un autre compte. Les identifiants HTTPS et leurs auxiliaires restent inchangés.

## CLI des fournisseurs

**Se connecter à la CLI** se connecte dans un répertoire de configuration séparé par compte, sans changer le compte global habituel de `gh` ou `glab`. Les variables de tokens héritées sont retirées pour ce processus. La confirmation explique que les tokens restent dans des profils CLI privés non chiffrés, pour éviter les entrées de trousseau partagées entre comptes du même serveur. Ne partagez jamais `~/.config/eitr/git-accounts/cli` ; ce dossier est exclu des sauvegardes EITR.

Depuis un dépôt, utilisez la CLI qui sélectionne le compte adapté :

```sh
eitr-git cli auth status
eitr-git cli repo view
```

Le compte par défaut ou de dossier sélectionne `gh` ou `glab`. Les commandes CLI ordinaires gardent leur comportement global. Enregistrer une clé SSH n’authentifie pas les opérations d’API de la CLI. Aucune CLI Bitbucket n’est fournie.

## Suppression et récupération

**Modifier le nom et l’e-mail** modifie l’identité ; **Supprimer le compte** supprime le compte et ses règles après confirmation. Retirer une règle de dossier fait revenir à une règle plus générale ou au compte par défaut. Retirer ce dernier rétablit les réglages Git précédents hors des règles restantes. Les projets, clés et identifiants CLI ne sont jamais supprimés ; supprimer une règle ne révoque pas l’accès au fournisseur.

Les réglages versionnés se trouvent dans `~/.config/eitr/git-accounts.json`. Chaque application des réglages sauvegarde le fichier global Git, l’inclusion active et les réglages sous `~/.local/state/eitr/git-account-backups/<id>`, avec des permissions privées. `manifest.json` indique chemins d’origine, noms de sauvegardes et permissions. Clés et tokens CLI ne sont jamais copiés. Pour restaurer manuellement, examinez le manifeste et conservez les changements faits depuis la sauvegarde avant de restaurer. Les inclusions EITR modifiées ou invalides sont refusées plutôt que remplacées silencieusement.

Références : [inclusions conditionnelles Git](https://git-scm.com/docs/git-config), [profils GitHub CLI](https://cli.github.com/manual/gh_help_environment), [profils GitLab CLI](https://docs.gitlab.com/cli/configuration/).
