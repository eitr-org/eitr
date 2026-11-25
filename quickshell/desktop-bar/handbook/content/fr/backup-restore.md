# Sauvegarde et restauration

Déplacez vos réglages du bureau, les dossiers personnels choisis et la liste des applications installées vers un autre PC ou une installation fraîche d’Eitr dans un seul fichier chiffré `.eitrbackup`.

Les instantanés décrits dans [Récupération et instantanés](handbook:recovery) restent sur le même disque pour annuler une mise à jour. Sauvegarde et restauration produit une archive portable compressée avec `zstd` et chiffrée par phrase secrète `age`.

## Ouvrir Sauvegarde et restauration

- **Paramètres** : appuyez sur **SUPER + ,** puis ouvrez **Système > Sauvegarde et restauration**.
- **Walker** : appuyez sur **SUPER + F**, puis **Paramètres > Système > Sauvegarde et restauration**.
- **Terminal** : lancez `eitr backup` (ou `eitr-backup wizard`).

## Créer une sauvegarde

1. Choisissez les catégories à inclure :
   - **Réglages Eitr** : préférences du bureau, surcharges sous `~/.config/eitr/overrides`, thèmes, fonds d’écran et écrans de verrouillage personnels.
   - **Réglages d’applications** : dossiers de `~/.config` hors Eitr (sans profils de navigateur ni caches).
   - **Dossiers personnels** : dossiers principaux de `$HOME`, décochés par défaut, plus **Ajouter un dossier…** pour tout sous-dossier dans `$HOME`. Les tailles sont calculées en arrière-plan.
   - **Applications installées** : paquets officiels, AUR, Flatpak, extensions Eitr et éléments de la boutique ajoutés au système de base.
   - **Configuration matérielle** : désactivée par défaut ; réglages locaux d’écrans et `hypr/local.lua` propres à ce PC.
   - **Comptes Git** (secret optionnel, désactivé par défaut) : `eitr/git-accounts.json`, ses inclusions gérées sous `eitr/git-accounts`, `~/.gitconfig`, les clés SSH désignées par chaque compte (clé privée et `.pub`, conservées en `0600`), `~/.ssh/config`, `~/.ssh/known_hosts`, ainsi que les clés secrètes GPG exportées via `gpg --export-secret-keys --armor` (GPG demande lui-même sa phrase secrète).
   - **Comptes cloud** (secret optionnel, désactivé par défaut) : `~/.aws`, `~/.config/gcloud`, `~/.azure`, `~/.kube` et les libellés cloud d’Eitr (`eitr/cloud-contexts.json`, `eitr/cloud-navigation.json`).
   - **Réseaux WiFi** (secret optionnel, désactivé par défaut) : profils enregistrés iwd (`/var/lib/iwd/*.psk`, `*.8021x`, `*.open`) et NetworkManager (`/etc/NetworkManager/system-connections/*.nmconnection`) exportés via `/usr/lib/eitr/eitr-network` avec `pkexec`.
2. Ajustez la sélection d’applications et de dossiers de configuration (recherche et regroupement par source).
3. Choisissez la destination. Les disques externes passent avant `~/Backups`. Enregistrer sur le même disque affiche un avertissement ; un espace insuffisant refuse l’écriture d’emblée.
4. Saisissez deux fois la phrase secrète. Elle n’apparaît jamais dans la ligne de commande, l’environnement ni les journaux.
5. Vérifiez le résumé sur l’écran **Vérifier** (qui affiche un avertissement lorsque des catégories et entrées secrètes sont incluses) et appuyez sur **Entrée** pour écrire l’archive de façon atomique, ou **Échap** pour annuler sans rien écrire.

### Éléments exclus

- Profils et caches de navigateurs, verrous, sockets et fichiers temporaires.
- Code système fourni, valeurs par défaut et fichiers générés (reconstruits après restauration).
- Trousseaux de session, jetons CLI Git (`~/.config/gh`, `eitr/git-accounts/cli`) et caches de session cloud éphémères : caches SSO et CLI AWS (`~/.aws/sso/cache`, `~/.aws/cli/cache`), bases de jetons et d’identifiants gcloud (`~/.config/gcloud/access_tokens.db*`, `~/.config/gcloud/credentials.db*`, `legacy_credentials`, `logs`), caches de jetons Azure (`~/.azure/msal_token_cache*`, `accessTokens.json`, `msal_http_cache*`, `logs`, `telemetry`, `commands`) et caches de découverte Kubernetes (`~/.kube/cache`, `~/.kube/http-cache`).

## Restaurer depuis une sauvegarde

1. Sélectionnez une archive (disques externes, `~/Backups`, dernière destination ou chemin personnalisé) et saisissez sa phrase secrète.
2. Eitr inspecte d’abord `manifest.json` et permet de décocher catégories, dossiers ou applications avant toute écriture.
3. Confirmez la **Vérifier**. Les fichiers remplacés sont d’abord sauvegardés avec un journal dans `~/.local/state/eitr/restore-backups/<id>/`.
4. Les logiciels sont réinstallés dans l’ordre : paquets officiels disponibles en une transaction `pacman` (absents ignorés et listés), paquets AUR un par un via `yay`, Flatpak, puis extensions Eitr et éléments Store **uniquement après validation normale de revue**.
5. Les fichiers ordinaires sont restaurés d’abord et les catégories secrètes en dernier : les dossiers SSH et GPG gardent les permissions `0700` tandis que les clés SSH (privée et `.pub`), les fichiers GPG et les configurations cloud gardent `0600`, les clés GPG sont importées via `gpg --import` et les profils WiFi sont écrits en `root:root` `0600` via `/usr/lib/eitr/eitr-network` avec `pkexec`.
6. Les thèmes et fichiers générés sont reconstruits sans perdre les fonds d’écran par moniteur, et Hyprland se recharge si la session est active. Reconnectez ensuite vos navigateurs et sessions éphémères de CLI cloud/Git (`gh`, `gcloud`, `aws`, `az`).

## Annuler une restauration

```sh
eitr backup undo <id>
```

Retrouvez `<id>` dans **Paramètres > Système > Sauvegarde et restauration** ou via `eitr-backup status`. Undo rétablit les fichiers précédents (y compris les fichiers secrets, le trousseau GPG et les profils WiFi), supprime ceux ajoutés et régénère les thèmes.
Avant de remplacer les fichiers, la restauration vérifie les conflits à leur emplacement, comme un dossier à la place d’un fichier ou un dossier parent qui est un lien symbolique. Si l’opération est interrompue, le point d’annulation figure dans la même liste.

## Référence CLI

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Les phrases secrètes sont lues sur `/dev/tty` sans écho ou via `--passphrase-fd N`. Un format d’archive plus récent est refusé proprement sans rien modifier.
