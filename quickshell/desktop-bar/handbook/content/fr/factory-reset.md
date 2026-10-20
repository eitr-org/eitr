# Réinitialisation d’usine

Les ordinateurs installés avec l’ISO d’Eitr peuvent retrouver l’état de leur première connexion depuis Walker → Système → Maintenance → Réinitialisation d’usine. Cette réinitialisation restaure une copie locale en lecture seule, sur le même disque. Ce n’est ni une sauvegarde ni un effacement sécurisé : une panne du disque fait perdre le système et son point de restauration.

## Le point de restauration

La dernière étape de l’installation guidée exécute `eitr-factory-reset capture`, qui enregistre l’installation terminée dans le sous-volume Btrfs de premier niveau `@eitr-factory` :

| Chemin | Contenu |
|---|---|
| `root` | instantané en lecture seule de `@` (système, comptes, réglages) |
| `home` | instantané en lecture seule de `@home` (dossiers personnels préparés à l’installation) |
| `boot.tar` | fichiers de la partition EFI : Limine, son menu, noyau et initramfs |
| `manifest.json` | date de création, UUID du système de fichiers et de la partition EFI, comptes, SHA-256 de `boot.tar` |

`@eitr-factory` devient lui-même accessible en lecture seule. Il se trouve à côté de `@`, pas dans `@/.snapshots`. Snapper ne l’affiche donc jamais et ne le supprime pas lors du nettoyage ; Walker ne propose aucune commande pour le supprimer. Root peut toujours le supprimer, et un formatage ou une panne du disque le détruit. Ses instantanés partagent les données du système en cours d’exécution : ils occupent peu de place au départ, puis grossissent lorsque les mises à jour remplacent les fichiers d’origine.

`capture` refuse de remplacer un point de restauration existant. Les installations faites sans l’ISO n’en ont pas, ce que signale Réinitialisation d’usine.

## Les deux modes

**Effacer tout** ramène l’ordinateur à sa première connexion : les applications installées depuis, les réglages modifiés, les comptes ajoutés ensuite et tous les fichiers des dossiers personnels sont supprimés.

**Garder mes fichiers** restaure le système, les applications et les réglages tout en conservant les dossiers personnels. Pour chaque compte présent dans le point de restauration, les entrées cachées actuelles (`~/.config`, `~/.local`, `~/.ssh`, profils de navigateur, etc.) sont déplacées dans un dossier visible nommé `Settings before reset <date time>` dans son dossier personnel. Les entrées cachées du point de restauration sont ensuite recopiées. Rien n’est supprimé dans un dossier personnel. Les comptes ajoutés après l’installation sont retirés du système, mais leurs dossiers restent sous `/home`.

Les deux modes conservent la phrase secrète de chiffrement du disque (l’en-tête LUKS n’est jamais modifié) et le mot de passe actuel de chaque compte également présent dans le point de restauration. L’emplacement de déverrouillage TPM reste dans l’en-tête LUKS, mais l’initramfs restauré demande la phrase secrète jusqu’à ce que ce déverrouillage soit reconfiguré. Les journaux (`@log`) et le cache des paquets (`@pkg`) sont conservés.

## Confirmation

L’action de Walker affiche deux avertissements distincts dans un terminal :

1. Ce que le mode choisi supprime et conserve. Seuls `y` ou `yes` permettent de continuer ; Enter annule.
2. Quel ordinateur sera réinitialisé, qu’il redémarrera immédiatement et que le travail non enregistré sera perdu. Il faut saisir exactement `RESET MY COMPUTER`.

L’utilitaire appartenant à root (`/usr/lib/eitr/eitr-factory-reset`) vérifie de nouveau la phrase saisie, puis contrôle ces points avant toute modification :

- `/` est le sous-volume `@`, `/home` est `@home` sur le même système de fichiers Btrfs et `/boot` est la partition EFI au format FAT.
- Le point de restauration et ses instantanés sont toujours en lecture seule ; son manifeste désigne ce système de fichiers et cette partition EFI, et `boot.tar` correspond à son SHA-256.
- Secure Boot est désactivé : les fichiers de démarrage restaurés ne sont pas signés avec les clés inscrites.
- Aucune réinitialisation précédente n’est encore en attente.

`sudo /usr/lib/eitr/eitr-factory-reset status` (Walker → État de la réinitialisation) effectue les mêmes vérifications sans rien modifier.

## Déroulement d’une réinitialisation

La racine et les dossiers personnels en cours d’utilisation ne sont jamais modifiés. Dans un nouveau sous-volume de premier niveau, `@eitr-reset-previous`, l’utilitaire :

1. Crée un instantané accessible en écriture de la racine du point de restauration, y recrée le sous-volume `.snapshots` de Snapper, copie les mots de passe actuels et y active `eitr-factory-reset-finish.service`.
2. Crée les nouveaux dossiers personnels : un instantané accessible en écriture de ceux du point de restauration (Effacer tout), ou un instantané du `@home` actuel dont les réglages sont mis de côté comme décrit plus haut (Garder mes fichiers).
3. Archive les fichiers actuels de la partition EFI dans `boot.tar`, puis extrait l’archive du point de restauration pour préparer sa copie.

Un échec jusque-là supprime `@eitr-reset-previous` et laisse l’ordinateur inchangé. L’utilitaire copie ensuite les fichiers de démarrage restaurés sur la partition EFI (en cas d’échec, il restaure l’archive qu’il vient de créer), renomme `@` et `@home` en `old@` et `old@home` dans `@eitr-reset-previous`, renomme les sous-volumes préparés en `@` et `@home`, puis redémarre. Si un renommage échoue, les anciens noms et fichiers de démarrage sont restaurés.

Au démarrage suivant, `eitr-factory-reset-finish.service` confirme que la racine utilisée est celle restaurée, supprime `@eitr-reset-previous` (y compris les instantanés Snapper de l’ancien système), puis se désactive.

## Récupérer une réinitialisation interrompue

Une coupure de courant pendant les renommages peut laisser `@` ou `@home` manquant. Démarrez l’ISO d’Eitr, appuyez sur Escape pour quitter l’assistant, déverrouillez le disque s’il est chiffré (`cryptsetup open /dev/<partition> root`), puis inspectez :

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # or the Btrfs partition itself
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- `@` et `@home` existent et `@eitr-reset-previous/new-root` a disparu : l’échange est terminé. Redémarrez ; le service de finalisation nettoiera les restes.
- `@` ou `@home` manque : redonnez son nom au `@eitr-reset-previous/old@` ou `old@home` correspondant (`mv /mnt/@eitr-reset-previous/old@ /mnt/@`), puis extrayez `@eitr-reset-previous/boot.tar` sur la partition EFI pour qu’elle corresponde à l’ancien système, et redémarrez.

Ne supprimez `@eitr-reset-previous` avec `btrfs subvolume delete --recursive` qu’une fois le système correctement démarré ; jusque-là, il contient le système précédent.

## Vérification

Testé sur des VM UEFI sans réseau (voir [LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)) : les deux modes sur une installation non chiffrée avec effacement du disque et sur une installation LUKS2 à côté d’un disque de structure semblable à Windows. Chaque test a été suivi d’un démarrage, d’une connexion et d’un nettoyage réussis par le service de finalisation. Pas encore testé : matériel réel, coupure de courant pendant l’échange et conservation du point de restauration au fil des mises à jour système en ligne (les VM n’avaient pas de réseau).
