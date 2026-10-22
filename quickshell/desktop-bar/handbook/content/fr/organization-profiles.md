# Profils d’organisation

Utilisez l’ISO officielle sans la modifier. Sur une clé FAT32 nommée `EITRANSWERS`, placez `eitr-profile.json` à côté de `eitr-answers.json` ou à sa place. Avec le profil seul, l’assistant normal affiche tous ses changements dans la révision. Avec les deux fichiers, l’opération sur le disque et tous les changements précèdent le compte à rebours de 15 secondes. Ctrl+C annule avant toute modification du disque. Gardez la clé branchée jusqu’à l’arrêt.

Exemple complet : remplacez les empreintes d’exemple par les valeurs réelles en minuscules de `sha256sum` et copiez les fichiers indiqués.

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Seuls `version` et `name` sont obligatoires. Les clés JSON inconnues ou dupliquées sont refusées. Supprimez les sections facultatives inutiles. Les chemins sont relatifs à la clé ; chemins absolus, liens symboliques et `..` sont interdits. Tous les fichiers doivent exister et correspondre au SHA-256 avant de modifier un disque. Le fond doit être un PNG, JPEG ou WebP valide. La clé doit contenir exactement une clé publique OpenPGP ; le serveur doit utiliser HTTPS sans identifiants. La clé est importée et signée localement dans pacman : n’utilisez que des clés de confiance. Paquets et scripts sont du code administrateur de confiance, sans bac à sable.

`remove` accepte seulement la liste révisée `distro/removable-apps.json` ; l’examen de chaque paquet figure dans `distro/PROFILE-PACKAGE-REVIEW.md`. Un paquet protégé ou inconnu refuse tout le profil. pacman vérifie les dépendances, sans suppression récursive ni contournement. Les politiques de groupe excluent les paquets autorisés de `gaming`, `media`, `development`, `sharing` et `remote_access`. `false` désactive, `true` autorise. `update_channel` accepte uniquement `"stable"`. Une politique omise ne restreint pas.

Les recettes utilisent `group/name` de `distro/software.json`. Seules les recettes pacman et Flatpak précompilées sont acceptées. AUR, installateurs interactifs et applications web sont refusés ; fournissez des paquets précompilés sur la clé. Dépôts, recettes et Flathub nécessitent Internet. Les fichiers de paquets fonctionnent hors ligne si leurs dépendances sont sur l’ISO ou la clé. Les noms doivent exister dans les bases actuelles de pacman ; actualisez par le processus normal avant les vérifications en ligne. Aucune compilation AUR. Les ajouts pacman en ligne effectuent une mise à niveau complète. Le dépôt supplémentaire sert aux mises à jour futures ; fournissez ses paquets exclusifs comme fichiers.

Pendant l’installation, les applications Flathub et les recettes Flatpak sont mises en attente pour l’utilisateur du bureau et installées au premier démarrage avec une connexion Internet. Les installations échouées sont réessayées au démarrage suivant. L’application d’un profil sur une machine déjà installée les installe directement.

Navigateurs : Firefox et Chromium ; ajoutez Chromium explicitement. Thème et fond sont enregistrés pour la prochaine connexion de l’utilisateur choisi, sans redémarrer le bureau. Canal et dépôt sont globaux. `setup` s’exécute comme root à la fin, depuis la copie privée de la clé, après enregistrement du profil. Un marqueur SHA-256 enregistre la tentative avant le lancement : un échec ou une interruption ne provoque pas de répétition silencieuse. Modifiez le script et son empreinte pour autoriser une nouvelle tentative. Les erreurs restent visibles ; les transactions terminées ne sont pas annulées.

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check` lit fichiers et métadonnées avec des répertoires temporaires, sans modifier la configuration. `apply` utilise l’action root explicite `eitr-system profile-apply`, copie et revalide, affiche le résumé et exige de saisir `APPLY PROFILE`. Annuler ne change rien. Il supprime avec pacman, installe les ajouts, enregistre les valeurs, puis `/etc/eitr/policies.json` (0644, root:root) et `/etc/eitr/profile.json`. Un autre profil remplace les choix enregistrés, sans réinstaller automatiquement les anciennes suppressions ni réinitialiser les préférences omises. Les marqueurs de setup sont conservés.

Les exclusions filtrent les listes d’installation ; `IgnorePkg` empêche System Update de réintroduire une dépendance exclue. Un conflit doit arrêter la mise à niveau. Initialiser les préférences utilisateur n’installe aucune application. Les politiques masquent menus et recherche Elephant, accès distant dans la barre, collaboration des assistants et choix du canal. Les outils refusent aussi les appels directs. Les menus et panneaux peuvent nécessiter une actualisation.

**Ce n’est pas un verrouillage contre un utilisateur ayant root.** Root peut modifier les politiques ou utiliser d’autres outils. Un véritable verrouillage exige aussi de ne pas accorder root. Ce n’est pas de la gestion de parc. Les installations avec et sans réseau, un profil refusé et l’application à une machine installée ont réussi en VM ; les vérifications restantes sont dans `distro/PROFILE-VM-TESTING.md`.
