# Langue

Eitr suit la langue des messages du système. **Centre de contrôle > Système > Langue** indique la langue utilisée pour les paramètres régionaux actuels et ouvre un sélecteur de langue ; **Walker > Système > Langue** liste les mêmes choix, le choix actuel étant coché. Choisissez une langue ou **Valeur par défaut du système**, puis déconnectez-vous et reconnectez-vous. Eitr ne vous déconnecte jamais automatiquement.

Eitr vérifie d’abord **LC_ALL**, puis **LC_MESSAGES**, et enfin **LANG**. Les variables vides sont ignorées. `LC_MESSAGES` change les messages sans modifier les formats de date, de nombres ou de monnaie. `LC_ALL` remplace toutes les catégories régionales et reste généralement non définie. Avec `C`, `POSIX` ou une langue non prise en charge, Eitr utilise l’anglais. Un message sans traduction s’affiche en anglais ; pour un chapitre absent, le chapitre anglais entier est utilisé.

## Changer la langue du système

Si vous devez aussi modifier les réglages de tout le système, utilisez ses paramètres régionaux. Sous Arch Linux, activez la locale souhaitée dans `/etc/locale.gen` et générez les locales installées avec `sudo locale-gen`. Définissez ensuite la langue dans `/etc/locale.conf`, par exemple :

```text
LANG=pt_BR.UTF-8
```

Les premières langues proposées sont `pt_BR.UTF-8` (portugais brésilien), `es_ES.UTF-8` (espagnol), `de_DE.UTF-8` (allemand) et `fr_FR.UTF-8` (français). Une variante régionale peut utiliser la traduction de la langue de base. Exécutez `locale` dans un terminal pour vérifier les variables prioritaires et `locale -a` pour afficher les locales installées. Déconnectez-vous puis reconnectez-vous pour appliquer la langue au bureau, aux menus et aux nouveaux terminaux. Le sélecteur écrit uniquement `~/.config/environment.d/90-eitr-language.conf` : il définit `LC_MESSAGES` et vide `LC_ALL` pour la prochaine session, en conservant les formats de date et de nombres. **Valeur par défaut du système** supprime cette préférence. Il ne modifie pas `/etc/locale.conf` et ne génère aucune locale. Les applications déjà ouvertes conservent leur langue.

## Contribuer à une traduction

Le texte anglais est la source. Les catalogues se trouvent dans `i18n/catalogs/<locale>/` ; modifiez les valeurs traduites en conservant les clés anglaises. Les messages Python et shell utilisent le domaine gettext commun `eitr`. Conservez les paramètres `%1` et `{name}`, les glyphes, les noms de paquets, les commandes et les chemins. Les mots à saisir pour confirmer une action destructive doivent correspondre exactement aux mots acceptés par la vérification.

Les chapitres du manuel se trouvent dans `quickshell/desktop-bar/handbook/content/<locale>/<chapter-id>.md`. Conservez les liens `handbook:`, les blocs de code et les commandes. Les tableaux du clavier et de la souris sont générés à partir des sources de référence des raccourcis ; traduisez leurs messages dans le catalogue du manuel plutôt que de maintenir une seconde liste de touches.

Exécutez `python3 tools/i18n-build.py --check`, générez le manuel avec `python3 quickshell/desktop-bar/scripts/handbook-build.py`, puis exécutez son option `--check` et `bash tools/check.sh`. Les vérifications énumèrent les messages manquants et les paramètres modifiés. Vérifiez les traductions longues dans des aperçus rendus hors écran avant de proposer votre contribution.

Après avoir traduit intégralement un chapitre modifié, mettez à jour son entrée dans `source-hashes.json` avec le SHA-256 de la source anglaise. La vérification signale les sources modifiées ou non enregistrées ; régénérer les catalogues ne valide jamais un changement de source.

La ligne Par défaut du système affiche le nom natif résolu depuis `/etc/locale.conf` : `LC_ALL`, puis `LC_MESSAGES` et `LANG`, en ignorant les valeurs vides. Elle ignore les substitutions de la session. English impose l’anglais ; Par défaut du système suit le système. Si la configuration régionale ne peut pas être lue, la ligne conserve son libellé simple.
