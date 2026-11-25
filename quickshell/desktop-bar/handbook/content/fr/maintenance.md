# Mises à jour, nettoyage et récupération

Le terminal indique chaque étape de vérification et de création des instantanés pendant son exécution. Si tout est à jour, le message reste visible pendant trois secondes avant la fermeture du terminal.

Les étapes d’attente de la mise à jour système affichent une rune tournante et un arc-en-ciel Bifröst fluide dans les terminaux truecolor, sinon l’accent du thème, suivi de phrases nordiques traduites et du temps écoulé. Une étape réussie laisse une coche et son texte sans couleur.

Ouvrez Paramètres > Mises à jour pour mettre à jour le système et choisir le canal. Walker > Paramètres > Système > Entretien contient nettoyage, miroirs et instantanés. Gardez des sauvegardes indépendantes ; les instantanés ne sont pas une sauvegarde sur un autre disque.

La mise à jour du système vérifie d’abord les paquets officiels avec checkupdates dans une base temporaire distincte, les paquets AUR (y compris ceux de développement) et les Flatpaks utilisateur. Si toutes les vérifications confirment l’absence de mises à jour, elle se termine sans instantanés, mise à niveau ni proposition de redémarrage. Si une vérification échoue ou qu’un outil manque, le processus normal continue.

## Mettre le système à jour

**Paramètres > Mises à jour > Mise à jour du système** est la procédure normale de mise à jour complète des paquets. Sur une nouvelle installation EITR configurée, elle vérifie la prise en charge des instantanés et crée les instantanés avant/après avec les archives de démarrage. Si la protection échoue, aucune mise à jour ne commence.

Un bureau Arch existant sans la politique de la distribution n’a pas besoin de cette configuration pour être mis à jour. La mise à jour du système actualise aussi les applications Flatpak, comme GeForce NOW ; un échec de Flatpak est signalé sans annuler la mise à jour du système.

Avant la mise à jour, la mise à jour du système et les mises à jour des paquets officiels depuis le terminal consultent les nouvelles d’Arch Linux depuis la dernière mise à jour. Arch y annonce les changements nécessitant une intervention manuelle. S’il y a des nouvelles, les titres et liens apparaissent avec **Continuer la mise à jour ?**. Esc annule avant tout changement pour vous laisser lire l’annonce ; Enter continue. Sans nouvelles ou sans internet, la procédure continue.

**Paramètres > Mises à jour > Canal de mise à jour** affiche les deux canaux et marque le vôtre. Choisir l’autre demande votre mot de passe dans un terminal et change l’origine des mises à jour d’Eitr lui-même. Stable, par défaut, les reçoit après essai. Testing reçoit les nouveaux builds dès leur publication pour essayer les changements plus tôt ; le reste provient toujours d’Arch.

Revenir à Stable conserve une version plus récente d’Eitr jusqu’à ce que Stable la rattrape. Dans un terminal, `eitr channel` affiche le canal ; `eitr channel testing` ou `eitr channel stable` le change.

Une seule mise à jour protégée peut s’exécuter à la fois sur la machine. Pacman active la protection du démarrage au début des modifications de paquets et s’arrête si l’activation échoue. La protection reste active si la mise à jour échoue ou est interrompue après ce point.

Si deux démarrages de suite n’atteignent pas un écran graphique de connexion stable ou une session de bureau, la **protection du démarrage** restaure le système et les fichiers de démarrage au troisième essai. Un écran de connexion fonctionnel suffit sans connexion d’un utilisateur. Attendre pendant le même démarrage ne compte pas comme un autre échec. Le dossier personnel est conservé et un avis s’affiche à la prochaine connexion. Voir [Récupération et instantanés](handbook:recovery).

**Instantanés du dossier personnel** conservent les anciennes versions de vos fichiers. Activez-les dans **Walker > Paramètres > Système > Entretien > Instantanés > Instantanés du dossier personnel**. Ils sont créés toutes les heures pendant un jour et chaque jour pendant une semaine ; les plus anciens sont supprimés si le disque manque de place. Caches, Downloads, disques de VM et jeux sont exclus. Pour récupérer un fichier, choisissez **Restaurer un fichier ou un dossier**, saisissez son chemin et choisissez une date. L’ancienne version apparaît à côté de l’actuelle sans la remplacer.

La mise à jour du système couvre les paquets officiels, AUR et Flatpak avec des instantanés sur les installations compatibles de la distribution. Dans les rares cas où seuls les paquets officiels doivent être mis à jour, par exemple après un échec de compilation AUR, ou pour éviter l’instantané, utilisez un terminal : `eitr update pacman`, `eitr update aur` ou `eitr update full` (sans instantanés automatiques), ou directement `sudo pacman -Syu` / `yay -Sua`. Les instantanés racine ne couvrent ni Flatpaks, ni environnements de développement, ni données personnelles séparées.

Évitez les mises à jour partielles d’Arch. Lisez les questions des paquets plutôt que d’accepter une suppression inattendue sans vérifier. Les tâches réussies se ferment ; les échecs restent visibles pour permettre l’examen de leur sortie.

Après une mise à jour du paquet de bureau EITR, la barre se recharge une fois la mise à jour terminée, ses fenêtres et panneaux fermés et toute capture ou diffusion terminée. La Mise à jour du système attend aussi la fin des hooks exécutés après la mise à jour. La session de bureau se poursuit.

Après une mise à jour réussie, une notification demande de la terminer si nécessaire : **Redémarrer maintenant** après une mise à jour du noyau, du firmware, du microcode, de systemd, glibc, du pilote graphique ou du chiffrement du disque. **Se déconnecter maintenant** concerne les mises à jour du bureau, comme Hyprland, Quickshell, Walker ou PipeWire. **Plus tard** permet de continuer à travailler ; les nouvelles versions prennent effet au prochain redémarrage ou à la prochaine connexion.

## Nettoyage et instantanés

Le nettoyage exécute la maintenance et garde le rapport ouvert. Vérifiez les propositions : un paquet orphelin n’est pas forcément inutilisé. Instantanés propose les procédures existantes de consultation et configuration de Snapper. Les dispositions prises en charge et limites des chargeurs sont décrites dans [Récupération et instantanés](handbook:recovery).

## Réinitialisation d’usine

Seule une installation compatible de la distribution disposant de son point de restauration de première connexion peut être réinitialisée. Cette copie initiale privée est séparée des listes et du nettoyage ordinaires de Snapper. Root peut toujours la supprimer et une panne du disque peut la détruire. Deux avertissements distincts et une confirmation saisie sont obligatoires. Consultez [Réinitialisation d’usine](handbook:factory-reset) pour savoir exactement ce que préservent Effacer tout et Garder mes fichiers.

## Alimentation

Menu principal > Alimentation et Centre de contrôle > Général (derrière **Alimentation…**) proposent verrouillage, déconnexion, veille, redémarrage et arrêt. Enregistrez votre travail avant. Ces actions sont réellement exécutées ; ce ne sont pas des démonstrations.

## Miroirs des paquets

Dans Walker > Paramètres > Système > Entretien, choisissez Choisir les miroirs les plus rapides. Le terminal explique le changement ; Enter confirme et Esc annule. Reflector sélectionne jusqu’à dix miroirs HTTPS synchronisés depuis moins de 12 heures, classés par vitesse de téléchargement. Il privilégie le pays identifié par le fuseau horaire, si connu, puis essaie les miroirs mondiaux si trop peu conviennent.

Les trois serveurs mondiaux fournis restent toujours en fin de liste ; si le classement échoue, la liste reste inchangée, miroirs personnalisés compris. Chaque exécution de reflector est limitée à deux minutes.

La liste précédente est sauvegardée à côté de `/etc/pacman.d/mirrorlist` sous `mirrorlist.eitr-<timestamp>.bak`. Si une sauvegarde existe, la même procédure propose de la restaurer : saisissez `restore` et appuyez sur Enter. La restauration sauvegarde aussi la liste actuelle. Le résultat reste visible jusqu’à Esc.

Une nouvelle installation programme une tentative en arrière-plan deux minutes après chaque démarrage, jusqu’à trois tentatives avec connexion. Les démarrages hors ligne sont ignorés en silence et ne comptent pas ; un classement réussi arrête les tentatives. La connexion n’attend jamais le classement. Utilisez le menu si toutes les tentatives échouent. Seuls les miroirs Arch changent ; les dépôts Eitr et Flatpak restent identiques.

État en lecture seule : `/usr/lib/eitr/eitr-system mirrors-status` affiche du JSON avec `last_ranking_time` (UTC, ou null avant réussite), `mirror_count`, `shipped_fallback` et `backup_available`. Il lit les fichiers locaux sans réseau ni sudo.

La mise à jour du système vérifie les nouveaux commits des plugins à la fin sans changer les versions approuvées. Révisez-les et installez-les séparément dans **Centre de contrôle > Plugins > Mettre à jour les plugins**, **Installer > Plugins > Mettre à jour les plugins** ou avec `eitr plugin update`. Les erreurs réseau sont ignorées silencieusement.

Paramètres > Mises à jour affiche les paquets en attente et permet de renouveler la liste. Pour les vérifications en lecture seule, voir [Dépannage](handbook:troubleshooting).
## Nettoyer mon Eitr

**Nettoyer mon Eitr** verrouille le clavier, la souris et le pavé tactile derrière une superposition plein écran sur chaque moniteur afin de les essuyer en toute sécurité. Lancez-le depuis **Paramètres > Vérifier ce PC**, **Centre de contrôle > Outils**, **Walker > Paramètres > Système > Nettoyer mon Eitr**, ou avec `eitr clean start`.

Tant qu’il est actif, les raccourcis du compositeur et les notifications contextuelles sont suspendus, le verrouillage automatique d’inactivité est inhibé et les touches d’alimentation, de mise en veille, d’hibernation et de capot sont bloquées. Maintenez **Esc** pendant trois secondes pour quitter, attendez la limite de sécurité de cinq minutes ou exécutez `eitr clean stop` depuis un autre terminal (`eitr clean status` affiche `on` ou `off`).

Ctrl+Alt+F1 à F12 basculent toujours vers une console texte, comme sur tout bureau Linux ; appuyez sur **Ctrl+Alt+F1** (ou F2) pour revenir, le mode nettoyage reste actif.
