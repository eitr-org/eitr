# Instantanés de récupération d’Eitr

Les instantanés sont des points de récupération, **pas des sauvegardes sur un autre appareil**. Une panne du disque peut détruire ensemble le système et ses instantanés. Conservez des sauvegardes indépendantes.

Eitr prend en charge Snapper sur une racine Btrfs où `/usr`, `/etc` et `/var/lib/pacman` se trouvent dans le même sous-volume racine. `/home` peut être séparé : un instantané de la racine ne le couvre pas. Les dispositions non prises en charge bloquent les mises à jour avant toute modification. `install.sh` ne formate aucun disque et ne réorganise pas les sous-volumes existants. Seul `eitr-guided-install`, sur l’ISO, efface le disque que vous confirmez et crée cette disposition (voir l’installation guidée dans le README).

## Avant les mises à jour

L’installateur active `/etc/eitr/system-update-policy.conf`. Avant de mettre à jour les paquets officiels et AUR, Système → Maintenance → Mettre à jour → Mise à jour du système :

1. Vérifie la disposition prise en charge et la configuration Snapper de la racine.
2. Archive `/boot` et `/efi` uniquement s’ils sont des montages séparés. Un dossier `/boot` dans la racine Btrfs est déjà inclus dans son instantané. Les archives sont conservées sous `/var/lib/eitr/boot-backups/<snapshot-number>/`, accessibles uniquement à root.
3. Crée un instantané de la racine avant la mise à jour.
4. Annule la mise à jour si la sauvegarde des fichiers de démarrage ou la création de l’instantané échoue.

À la fin, en cas d’échec ou de refus de la mise à jour, le processus crée l’instantané après correspondant. Sa description indique le résultat ("after package upgrade", "after failed package upgrade"). Si le processus a été interrompu avant, la prochaine mise à jour du système clôt d’abord l’instantané avant resté ouvert par un instantané après nommé "after interrupted package upgrade". Une mise à jour échouée conserve dans tous les cas son instantané avant et ses archives de démarrage. Ces instantanés ne protègent pas les mises à jour de Flatpaks, les environnements SDKMAN/NVM ni les fichiers des sous-volumes personnels séparés. Les commandes de terminal `eitr update pacman|aur|full` et les commandes directes pacman/yay ne créent volontairement aucun instantané automatique. Pour adopter cette politique, supprimez les anciens hooks d’instantanés Eitr si vous les aviez installés manuellement.

Les nouvelles configurations Snapper conservent jusqu’à 10 instantanés numérotés ordinaires et 5 importants grâce au minuteur de nettoyage. Les politiques existantes sont conservées. Chaque mise à jour du système ne garde que les 10 archives de démarrage les plus récentes, conformément à la limite d’instantanés par défaut. Une archive peut survivre à son instantané si Snapper supprime celui-ci d’abord : vérifiez donc que l’instantané existe avant toute restauration. Un disque plein bloque les mises à jour au lieu de contourner la protection.

## Protection du démarrage

Après une mise à jour système réussie avec la disposition de l’installation guidée d’Eitr, la protection du démarrage garde prêt l’instantané avant cette mise à jour (`/var/lib/eitr/boot-guard.json`). `eitr-boot-guard.service` compte chaque tentative au début du démarrage. `eitr-boot-guard-healthy.service` la considère réussie lorsque l’écran de connexion est resté affiché 45 secondes, ce qui désarme la protection.

Si deux démarrages consécutifs après la mise à jour n’atteignent pas ce stade, le troisième restaure automatiquement le système avec les étapes testées de la réinitialisation d’usine :

1. Les fichiers de démarrage de l’instantané (`/var/lib/eitr/boot-backups/<number>/boot.tar`) sont copiés sur la partition EFI après avoir conservé les fichiers actuels pour pouvoir les remettre.
2. Le sous-volume racine défaillant est renommé `@eitr-guard-failed`. Une copie accessible en écriture de l’instantané devient `@`, et le stockage `.snapshots` de Snapper y est déplacé.
3. L’ordinateur redémarre sur le système restauré. Si une étape échoue, les sous-volumes et fichiers de démarrage sont remis dans leur état initial et aucun redémarrage n’a lieu.

Le système restauré supprime `@eitr-guard-failed` lorsqu’il atteint l’écran de connexion ; la prochaine connexion affiche une notification. Les dossiers personnels restent intacts. Cette protection ne peut pas aider si le noyau lui-même ne démarre pas. Démarrez alors l’instantané de la mise à jour depuis le menu de démarrage (ci-dessous). Cette protection n’est jamais activée pour les autres dispositions de disque.

## Changements d’authentification

Sécurité → activer empreinte/FIDO2 sauvegarde `/etc/pam.d/hyprlock`, `sddm` et `sudo` sous `/var/lib/eitr/pam-backups/<timestamp>/` avant de les modifier, et restaure les trois si une écriture échoue. L’empreinte est ajoutée aux trois : "mot de passe uniquement" s’applique donc aussi à l’écran de verrouillage. pam_fprintd peut retarder la demande de mot de passe de 10 secondes au maximum. Pour revenir à une politique précédente depuis un shell root fonctionnel ou un TTY :

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## Déverrouillage du disque TPM

Sécurité → Déverrouillage du disque TPM peut ajouter un emplacement de clé TPM2 à une racine LUKS2 pour déverrouiller le disque au démarrage sans saisir la phrase secrète. Rien de cela n’est exécuté depuis l’installateur. L’utilitaire root (`luks-tpm-check`, `luks-recovery-key`, `luks-tpm-enroll`, `luks-tpm-remove`) refuse l’opération sauf si le périphérique est LUKS2, qu’un TPM2 apparaît dans `systemd-cryptenroll --tpm2-device=list` et qu’un emplacement de phrase secrète ou de récupération existe déjà. Il **ajoute seulement** un emplacement ; la phrase secrète reste utilisable.

- **D’abord la clé de récupération.** Walker propose `systemd-cryptenroll --recovery-key`. La clé s’affiche une seule fois dans le terminal et n’est jamais stockée. Notez-la hors ligne. Elle fonctionne à la demande habituelle de phrase secrète.
- **Choix du PCR.** Eitr lie le déverrouillage au PCR 7 (état et clés de Secure Boot). Les mises à jour du firmware le modifient rarement, mais un changement de clés Secure Boot le modifie. Le PCR 7 n’offre une protection significative qu’avec Secure Boot activé et vos propres clés (voir [SECURE-BOOT.md](SECURE-BOOT.md)). Sinon, n’importe qui peut démarrer cet ordinateur avec une ligne de commande du noyau modifiée et obtenir un disque déverrouillé. Pour davantage de protection, inscrivez-le manuellement avec un PIN : `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`.
- **Initramfs.** Le hook busybox `encrypt` ne peut pas utiliser de jetons TPM2 ; l’inscription est donc refusée tant qu’il est configuré. Passer à `systemd` et `sd-encrypt` dans `HOOKS` (avec `rd.luks.name=<LUKS-UUID>=root` remplaçant `cryptdevice=` dans la ligne de commande du noyau, ou avec `/etc/crypttab.initramfs`) est une modification critique du démarrage qu’Eitr vous laisse effectuer. Faites-la, exécutez `sudo mkinitcpio -P`, mettez l’entrée de démarrage à jour et vérifiez qu’un démarrage avec phrase secrète fonctionne **avant** d’inscrire le TPM.

Si le TPM cesse de déverrouiller (changement du firmware ou de Secure Boot, réinitialisation du TPM), la demande de phrase secrète réapparaît comme avant. Saisissez-la, supprimez l’inscription et recommencez-la. Pour tout annuler, utilisez l’action de suppression du déverrouillage TPM ou, depuis un shell fonctionnel :

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## Réinitialisation d’usine

Les ordinateurs installés avec l’ISO d’Eitr gardent aussi un point de restauration en lecture seule de la première connexion, hors de Snapper. Walker → Système → Maintenance → Réinitialisation d’usine y revient, en conservant ou non les fichiers personnels. Voir [FACTORY-RESET.md](FACTORY-RESET.md).

## Examiner les points de récupération

Utilisez Walker → Système → Maintenance → Instantanés ou ces vérifications en lecture seule :

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

Si le bureau échoue mais que le système démarre encore, passez à une console texte ou utilisez une connexion SSH que vous avez configurée vous-même. S’il ne démarre plus, utilisez l’ISO officielle d’installation d’Arch et montez le système de fichiers Btrfs. Identifiez le bon disque, le mappage de chiffrement, le sous-volume racine, le numéro d’instantané et le montage EFI avant toute modification. Ne recopiez pas aveuglément les commandes d’une autre machine.

## Instantanés du dossier personnel

Désactivés par défaut. **Système > Entretien > Instantanés > Instantanés du dossier personnel** les active après confirmation ; les désactiver les supprime. La configuration `home` de Snapper conserve alors un instantané de `/home` par heure pendant un jour et un par jour pendant une semaine. Les plus anciens sont supprimés lorsque l’espace libre passe sous 20 %.

Les caches, `~/Downloads`, les dossiers de disques de VM (`~/.local/share/libvirt/images`, GNOME Boxes, `~/VirtualBox VMs`) et la bibliothèque Steam sont exclus. Au prochain démarrage, avant toute connexion, `eitr-home-exclusions.service` les transforme en sous-volumes Btrfs imbriqués que les instantanés personnels n’incluent pas. Leurs fichiers sont conservés par reflinks, sans espace supplémentaire pour le déplacement. Le mode Garder mes fichiers de la réinitialisation d’usine les transfère dans le dossier personnel restauré : les sous-volumes cachés vont dans "Settings before reset" et les caches sont abandonnés. Si l’un d’eux ne peut pas être déplacé, l’ancien dossier personnel est conservé pour examen au lieu d’être supprimé.

**Instantanés > Restaurer un fichier ou un dossier** (ou `eitr restore PATH`) liste les instantanés contenant le chemin et copie la version choisie à côté de l’actuelle sous le nom `NAME (restored DATE)`, ou à son emplacement d’origine si elle a été supprimée. Rien n’est jamais écrasé.

## Ce que chaque mise à jour a changé

Avant une restauration, vérifiez ce que vous annuleriez. **Système > Entretien > Instantanés > Ce que chaque mise à jour a changé** (ou `eitr snapshots changes`) liste chaque paire avant/après d’une mise à jour avec le nombre de paquets mis à jour, rétrogradés, installés et supprimés. `eitr snapshots changes <before number>` liste chaque paquet d’une mise à jour avec ses versions ancienne et nouvelle. La comparaison utilise les bases de données de paquets des deux instantanés. Si l’instantané après n’existe pas encore, elle utilise le système en cours d’exécution.

## Démarrer un ancien instantané

Avec GRUB ou Limine, le menu de démarrage peut lister les instantanés Snapper en lecture seule pour examiner et annuler une mise à jour défaillante sans support externe. L’installateur ne le propose qu’après saisie de `yes`. Sur une installation existante, exécutez `bash distro/bootloader/setup.sh` ; `--check` affiche seulement l’état. Vérifiez le résultat dans Walker → Système → Maintenance → Instantanés → état des instantanés amorçables, ou avec `sudo /usr/lib/eitr/eitr-system snapshots-boot-status`.

| Chargeur de démarrage | Intégration | Paquets (`distro/bootloader/`) |
|---|---|---|
| GRUB | `grub-btrfsd.service` reconstruit le sous-menu "Arch Linux snapshots" quand Snapper ajoute ou supprime un instantané | `grub-btrfs`, `inotify-tools` (officiels) |
| Limine | `limine-snapper-sync.service` ajoute des entrées d’instantanés à `limine.conf` | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **Non pris en charge.** Charge seulement les noyaux de la partition EFI/XBOOTLDR et ne peut pas ouvrir les instantanés Btrfs | Utilisez la procédure avec support externe ci-dessous |

La détection lit les fichiers GRUB, Limine et systemd-boot sous `/boot`, `/efi` et `/boot/efi`. Si plusieurs chargeurs sont configurés, par exemple des restes de systemd-boot à côté de GRUB, l’installation refuse plutôt que de deviner. Supprimez les fichiers obsolètes ou configurez les entrées manuellement. Elle copie d’abord `grub.cfg`/`limine.conf` sous `/var/lib/eitr/boot-config-backups/<timestamp>/` et active le service pour le prochain démarrage :

- **GRUB:** la configuration exécute une fois `grub-mkconfig -o /boot/grub/grub.cfg`. Si `/boot` est une partition séparée, les entrées d’instantanés démarrent le noyau *actuel*. Après une mise à jour du noyau, restaurez aussi l’archive de démarrage correspondante (ci-dessous).
- **Limine:** `limine-snapper-sync` gère les entrées créées par `limine-entry-tool` (de `limine-mkinitcpio-hook`) et garde des copies du noyau de chaque instantané sur la partition EFI. Celle-ci doit donc avoir de la place ; le projet recommande 4 GiB. Vérifiez `/etc/default/limine` (`SNAPPER_CONFIG_NAME="root"` et `ESP_PATH` si non détecté), exécutez `sudo limine-update`, vérifiez le menu, puis exécutez `sudo systemctl start limine-snapper-sync.service`. Eitr n’exécute pas `limine-update` à votre place car il réécrit le menu de démarrage.

Pour annuler, désactivez le service et recopiez la sauvegarde, par exemple avec `sudo systemctl disable grub-btrfsd.service` et `sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`.

### Instantanés en lecture seule

Les instantanés Snapper sont en lecture seule. Un instantané démarré directement ne peut pas écrire dans `/var` : SDDM et d’autres services peuvent échouer. Connectez-vous sur une console texte (Ctrl+Alt+F3) si la connexion graphique ne démarre pas. Une surcouche dans l’initramfs rend l’instantané accessible en écriture en RAM ; les modifications disparaissent au redémarrage. Eitr ne modifie pas `HOOKS`. Ajoutez-la puis régénérez vous-même ; seuls les instantanés créés ensuite contiendront le hook :

- GRUB : ajoutez `grub-btrfs-overlayfs` à `HOOKS=(...)` dans `/etc/mkinitcpio.conf`, puis exécutez `sudo mkinitcpio -P`.
- Limine : ajoutez `btrfs-overlayfs` après `filesystems` (ou `sd-btrfs-overlayfs` avec les hooks systemd), puis exécutez `sudo limine-update`.

### Revenir durablement à un instantané

1. Choisissez l’instantané "before package upgrade" le plus récent dans la liste du menu de démarrage et vérifiez que le système y fonctionne.
2. **Limine:** exécutez `sudo limine-snapper-restore` et choisissez l’instantané. La restauration utilise la méthode `RESTORE_METHOD` configurée et ajoute une entrée de secours du système remplacé pour pouvoir annuler la restauration elle-même depuis le menu de démarrage.
3. **GRUB:** `snapper rollback` fonctionne uniquement si la racine est montée via le sous-volume Btrfs par défaut. Arch utilise généralement `rootflags=subvol=@` (vérifiez `findmnt -no OPTIONS /` et `/etc/fstab`), donc le rollback serait sans effet. Remplacez le sous-volume racine depuis un support externe après avoir examiné les sous-volumes du premier niveau du système de fichiers. L’exemple suivant concerne **uniquement** l’installation guidée d’Eitr, où Snapper a créé le sous-volume imbriqué `@/.snapshots`. Les autres dispositions nécessitent leurs chemins réels :

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   Si une commande échoue, arrêtez-vous et examinez la situation ; ne supprimez pas la racine conservée. Vérifiez la présence du stockage d’instantanés sous la racine restaurée et examinez son fstab avant de continuer. Si `/boot` est séparé, restaurez l’archive correspondante sous `/var/lib/eitr/boot-backups/<number>/`. Redémarrez sur l’entrée normale, exécutez `sudo grub-mkconfig -o /boot/grub/grub.cfg` et ne supprimez `@.broken` avec `sudo btrfs subvolume delete` qu’après vérification du système restauré.

## Restaurer prudemment depuis un support externe

1. Sauvegardez les fichiers récents dont vous avez besoin. Montez le premier niveau du système de fichiers Btrfs et examinez les sous-volumes. Trouvez le sous-volume `snapshot` de l’instantané choisi ; les chemins dépendent de l’emplacement de montage de `.snapshots`.
2. Conservez le sous-volume racine défaillant en le renommant. Créez un **instantané Btrfs accessible en écriture** du point de récupération choisi à l’emplacement d’origine du sous-volume racine, conformément aux rootflags et au fstab du chargeur installé.
3. Montez cette racine restaurée et ses vraies partitions de démarrage/EFI. Restaurez les archives de démarrage correspondantes si les fichiers du noyau, de l’initramfs ou du chargeur ont changé. Elles doivent correspondre à l’instantané racine choisi : ne mélangez jamais un noyau plus récent et des modules anciens.
4. Vérifiez le fstab et la configuration du chargeur, puis régénérez l’initramfs ou réparez les entrées avec `arch-chroot` selon les besoins de cette machine. Ne redémarrez que lorsque racine et fichiers de démarrage concordent.

C’est une procédure manuelle adaptée à la disposition du disque, **pas une implémentation vérifiée de restauration en un clic**. La commande `rollback` de Snapper seule ne suffit pas pour toutes les dispositions de sous-volumes et de chargeurs d’Arch. Les entrées d’instantanés GRUB et Limine doivent encore être validées sur du matériel réel avant de promettre une récupération automatique.

Références : [grub-btrfs](https://github.com/Antynea/grub-btrfs), [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync), [concepts de récupération Snapper](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html), [guide d’installation Arch](https://wiki.archlinux.org/title/Installation_guide).
