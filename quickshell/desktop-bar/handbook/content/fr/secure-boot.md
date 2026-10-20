# Secure Boot avec sbctl

Eitr documente Secure Boot, mais **n’inscrit jamais de clés et ne signe aucun fichier à votre place**. Une erreur peut empêcher le démarrage ou priver le PC d’affichage. Suivez donc ces étapes manuellement sur un ordinateur dont vous pouvez ouvrir les réglages du firmware, avec la phrase secrète du disque et les [instructions de récupération](RECOVERY.md) à portée de main. Cette procédure n’a pas encore été vérifiée sur le matériel de test d’Eitr.

## Avant de commencer

- Démarrage UEFI uniquement. Repérez comment ouvrir les réglages du firmware (souvent F2, Del ou F12) et définissez un mot de passe administrateur du firmware. Sinon, n’importe qui pourra désactiver Secure Boot.
- Si le déverrouillage du disque par TPM est configuré, gardez la phrase secrète à portée de main : l’inscription des clés modifie le PCR 7 du TPM. Le prochain démarrage demandera donc cette phrase une fois. Réinscrivez ensuite le déverrouillage par TPM (Sécurité → déverrouillage du disque par TPM : supprimer, puis réinscrire).
- Dans le firmware, placez Secure Boot en **Setup Mode** (souvent "Clear keys" ou "Reset to Setup Mode"). Ne supprimez aucune clé que vous ne pouvez pas restaurer ; la plupart des firmwares proposent "Restore factory keys".

## Procédure avec sbctl

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s` enregistre le fichier dans la base de données de sbctl. Le hook pacman de sbctl signe à nouveau les fichiers enregistrés après les mises à jour du noyau et du chargeur de démarrage. Exécutez `sudo sbctl verify` après chaque modification, puis activez Secure Boot dans le firmware et redémarrez. Sauvegardez `/var/lib/sbctl` hors ligne et de manière confidentielle : ce dossier contient les clés de signature. Ne les copiez jamais dans ce dépôt.

## Risques

- **Option ROMs et clés du fabricant.** Les cartes graphiques, disques NVMe et cartes réseau exécutent souvent un firmware (Option ROMs) signé par l’autorité de certification UEFI de Microsoft. Inscrire uniquement vos propres clés sans `-m` peut amener le firmware à refuser ces composants : plus d’affichage, plus de disque de démarrage et, sur certains portables, plus d’accès aux réglages du firmware. Conservez `-m`, sauf si vous savez que votre matériel n’utilise pas ce type de firmware. Autre possibilité : `sbctl enroll-keys --tpm-eventlog` peut ajouter les empreintes des Option ROMs utilisées lors du démarrage actuel, mais celles-ci changent avec les mises à jour matérielles ou du firmware.
- **Fichiers non signés.** Chaque binaire EFI du chemin de démarrage doit être signé avec vos clés. Un fichier oublié bloque le démarrage ; désactivez Secure Boot dans le firmware pour retrouver l’accès.
- **Double démarrage.** Windows ne continue à démarrer qu’avec `-m`.

## Chargeurs de démarrage et entrées d’instantanés

- **GRUB:** réinstallez-le avec `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock`, puis signez le nouveau `grubx64.efi` et les noyaux dans `/boot`. Dans cette configuration, GRUB ne vérifie pas les signatures des noyaux : les entrées d’instantanés grub-btrfs continuent de démarrer, mais la protection couvre le binaire GRUB plutôt que chaque noyau. Relancez `grub-install` et `sbctl sign` après les mises à jour de GRUB qui modifient son image.
- **Limine:** signez le binaire EFI de Limine (`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` ou son emplacement réel). Limine protège sa configuration et les noyaux par des empreintes plutôt que des signatures. Si vous inscrivez l’empreinte de la configuration dans le binaire (`limine enroll-config`), toute modification de `limine.conf`, y compris chaque nouvelle entrée d’instantané créée par limine-snapper-sync, exige de le réinscrire et de le signer à nouveau. Avant d’activer Secure Boot, vérifiez que les réglages de `limine-mkinitcpio-hook` le font (il utilise sbctl quand celui-ci est installé). Sinon, la prochaine synchronisation des instantanés fera rejeter le menu par le chargeur.
- **systemd-boot:** signez `systemd-bootx64.efi` et les noyaux ou images de noyau unifiées qu’il charge. Il ne prend pas en charge les entrées de démarrage d’instantanés.
- Les entrées d’instantanés d’anciens noyaux doivent aussi réussir les vérifications du chargeur. Après avoir activé Secure Boot, démarrez une fois depuis une entrée d’instantané pour vérifier son fonctionnement avant d’en avoir besoin.

## Annuler

1. Ouvrez les réglages du firmware et désactivez Secure Boot, ou choisissez "Restore factory keys" pour restaurer les clés du fabricant. Le système installé continue à démarrer lorsque Secure Boot est désactivé.
2. Vous pouvez supprimer les fichiers enregistrés de la base de données de sbctl avec `sudo sbctl remove-file <file>` ; les signatures dans les fichiers eux-mêmes sont sans danger.
3. Si le déverrouillage par TPM a été inscrit avec Secure Boot activé, le PCR 7 change à nouveau : saisissez une fois la phrase secrète, puis réinscrivez le déverrouillage.

Références : [sbctl](https://github.com/Foxboron/sbctl), [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
