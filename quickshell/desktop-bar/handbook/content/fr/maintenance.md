# Mises à jour, nettoyage et récupération

Le terminal indique chaque étape de vérification et de création des instantanés pendant son exécution. Si tout est à jour, le message reste visible pendant trois secondes avant la fermeture du terminal.

Les étapes d’attente de la mise à jour système affichent une rune tournante et un arc-en-ciel Bifröst fluide dans les terminaux truecolor, sinon l’accent du thème, suivi de phrases nordiques traduites et du temps écoulé. Une étape réussie laisse une coche et son texte sans couleur.

Ouvrez **Système > Entretien**. Lisez les sorties du terminal et gardez des sauvegardes indépendantes avant de modifier le système. Les instantanés ne sont pas des sauvegardes sur un autre disque.

La mise à jour du système vérifie d’abord les paquets officiels avec checkupdates dans une base temporaire distincte, les paquets AUR (y compris ceux de développement) et les Flatpaks utilisateur. Si toutes les vérifications confirment l’absence de mises à jour, elle se termine sans instantanés, mise à niveau ni proposition de redémarrage. Si une vérification échoue ou qu’un outil manque, le processus normal continue.

## Mise à jour

**Mise à jour > Mise à jour du système** est la procédure normale de mise à jour complète des paquets. Sur une nouvelle installation EITR configurée, elle vérifie la prise en charge des instantanés et crée les instantanés avant/après avec les archives de démarrage. Si la protection échoue, aucune mise à jour ne commence. Un bureau Arch existant sans la politique de la distribution n’a pas besoin de cette configuration pour être mis à jour. La mise à jour du système actualise aussi les applications Flatpak, comme GeForce NOW ; un échec de Flatpak est signalé sans annuler la mise à jour du système.

Avant la mise à jour, la mise à jour du système et les mises à jour Pacman sous Avancé consultent les nouvelles d’Arch Linux depuis la dernière mise à jour. Arch y annonce les changements nécessitant une intervention manuelle. S’il y a des nouvelles, les titres et liens apparaissent avec **Continuer la mise à jour ? [y/N]**. Enter annule avant tout changement pour vous laisser lire l’annonce. Sans nouvelles ou sans internet, la procédure continue.

**Mise à jour > Canal de mise à jour** affiche les deux canaux et marque le vôtre. Choisir l’autre demande votre mot de passe dans un terminal et change l’origine des mises à jour d’Eitr lui-même. Stable, par défaut, les reçoit après essai. Testing reçoit les nouveaux builds dès leur publication pour essayer les changements plus tôt ; le reste provient toujours d’Arch. Revenir à Stable conserve une version plus récente d’Eitr jusqu’à ce que Stable la rattrape. Dans un terminal, `eitr channel` affiche le canal ; `eitr channel testing` ou `eitr channel stable` le change.

Si une mise à jour empêche le démarrage, la **protection du démarrage** l’annule. Après deux tentatives consécutives sans atteindre l’écran de connexion, la suivante restaure le système et les fichiers de démarrage d’avant la mise à jour, puis redémarre. Votre dossier personnel reste intact et la prochaine connexion explique ce qui s’est passé. Cela concerne les PC installés par l’installateur d’Eitr ; voir [Récupération et instantanés](handbook:recovery).

**Instantanés du dossier personnel** conservent les anciennes versions de vos fichiers. Activez-les dans **Système > Entretien > Instantanés > Instantanés du dossier personnel**. Ils sont créés toutes les heures pendant un jour et chaque jour pendant une semaine ; les plus anciens sont supprimés si le disque manque de place. Caches, Downloads, disques de VM et jeux sont exclus. Pour récupérer un fichier, choisissez **Restaurer un fichier ou un dossier**, saisissez son chemin et choisissez une date. L’ancienne version apparaît à côté de l’actuelle sans la remplacer.

**Mise à jour > Avancé** propose **Pacman + Yay**, **Pacman** et **Yay (AUR)**. Ces options ne créent volontairement aucun instantané automatique. Les commandes directes pacman/yay contournent également la procédure protégée. Les instantanés racine ne couvrent ni Flatpaks, ni environnements de développement, ni données personnelles séparées.

Évitez les mises à jour partielles d’Arch. Lisez les questions des paquets plutôt que d’accepter une suppression inattendue sans vérifier. Les tâches réussies se ferment ; les échecs restent visibles pour permettre l’examen de leur sortie.

Après une mise à jour réussie, une notification demande de la terminer si nécessaire : **Redémarrer maintenant** après une mise à jour du noyau, du firmware, du microcode, de systemd, glibc, du pilote graphique ou du chiffrement du disque. **Se déconnecter maintenant** concerne les mises à jour du bureau, comme EITR, Hyprland, Quickshell, Walker ou PipeWire. **Plus tard** permet de continuer à travailler ; les nouvelles versions prennent effet au prochain redémarrage ou à la prochaine connexion.

## Nettoyage et instantanés

Le nettoyage exécute la maintenance et garde le rapport ouvert. Vérifiez les propositions : un paquet orphelin n’est pas forcément inutilisé. Instantanés propose les procédures existantes de consultation et configuration de Snapper. Les dispositions prises en charge et limites des chargeurs sont décrites dans [Récupération et instantanés](handbook:recovery).

## Réinitialisation d’usine

Seule une installation compatible de la distribution disposant de son point de restauration de première connexion peut être réinitialisée. Cette copie initiale privée est séparée des listes et du nettoyage ordinaires de Snapper. Root peut toujours la supprimer et une panne du disque peut la détruire. Deux avertissements distincts et une confirmation saisie sont obligatoires. Consultez [Réinitialisation d’usine](handbook:factory-reset) pour savoir exactement ce que préservent Effacer tout et Garder mes fichiers.

## Alimentation

Menu principal > Alimentation et Centre de contrôle > Général (derrière **Alimentation…**) proposent verrouillage, déconnexion, veille, redémarrage et arrêt. Enregistrez votre travail avant. Ces actions sont réellement exécutées ; ce ne sont pas des démonstrations.
