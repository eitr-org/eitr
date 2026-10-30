# Instantáneas de recuperación de Eitr

Las instantáneas son puntos de recuperación, **no copias de seguridad en otro dispositivo**. Si el disco falla, el sistema y sus instantáneas pueden perderse juntos. Mantén copias de seguridad independientes.

Eitr admite Snapper en una raíz Btrfs con `/usr`, `/etc` y `/var/lib/pacman` dentro del mismo subvolumen raíz. `/home` puede estar separado: una instantánea de la raíz no lo incluye. Los esquemas de subvolúmenes no compatibles bloquean las actualizaciones antes de modificar nada. `install.sh` no formatea discos ni reorganiza subvolúmenes existentes; solo `eitr-guided-install` de la ISO borra el disco que confirmes y crea este esquema (consulta la sección de instalación guiada del README).

## Antes de actualizar

El instalador habilita `/etc/eitr/system-update-policy.conf`. Antes de actualizar paquetes oficiales y de AUR, Sistema → Mantenimiento → Actualizar → Actualizar el sistema:

1. Comprueba el esquema compatible y la configuración de raíz de Snapper.
2. Archiva `/boot` y `/efi` solo si son montajes separados (un directorio `/boot` dentro de la raíz Btrfs ya está en la instantánea de la raíz). Los archivos se guardan en `/var/lib/eitr/boot-backups/<snapshot-number>/`, accesibles solo para root.
3. Crea una instantánea de la raíz anterior a la actualización.
4. Cancela la actualización si falla la copia de los archivos de arranque o la creación de la instantánea.

Cuando la actualización termina, falla o se rechaza, el proceso crea la instantánea posterior correspondiente. Su descripción registra el resultado ("after package upgrade", "after failed package upgrade"). Si el proceso se interrumpió antes, la siguiente actualización del sistema cierra primero la instantánea previa pendiente con otra posterior llamada "after interrupted package upgrade". Una actualización fallida conserva siempre su instantánea previa y los archivos de arranque. Estas instantáneas no protegen actualizaciones de Flatpaks, entornos SDKMAN/NVM ni archivos de subvolúmenes personales separados. Los comandos de terminal `eitr update pacman|aur|full` y los comandos directos de pacman/yay no crean instantáneas automáticas deliberadamente. Para adoptar esta política, elimina los antiguos hooks de instantáneas de Eitr si los instalaste manualmente.

Las nuevas configuraciones de Snapper conservan hasta 10 instantáneas numeradas normales y 5 importantes mediante el temporizador de limpieza. Se respetan las políticas existentes. Cada actualización del sistema conserva los 10 archivos de arranque más recientes, según el límite predeterminado de instantáneas. Un archivo puede sobrevivir a su instantánea si Snapper la elimina primero: comprueba que la instantánea existe antes de restaurarlo. Un disco lleno impide actualizar en lugar de omitir la protección.

## Protección del arranque

Tras una actualización correcta del sistema en el esquema de la instalación guiada de Eitr, la protección del arranque deja preparada la instantánea anterior a esa actualización (`/var/lib/eitr/boot-guard.json`). `eitr-boot-guard.service` cuenta cada intento al inicio del arranque. `eitr-boot-guard-healthy.service` considera correcto un arranque cuando la pantalla de inicio de sesión lleva abierta 45 segundos y desactiva la protección.

Si dos arranques consecutivos tras la actualización no alcanzan ese punto, el tercero restaura automáticamente siguiendo los pasos probados del restablecimiento de fábrica:

1. Copia los archivos de arranque de la instantánea (`/var/lib/eitr/boot-backups/<number>/boot.tar`) a la partición EFI, tras guardar los actuales por si es necesario recuperarlos.
2. Renombra el subvolumen raíz fallido a `@eitr-guard-failed`; una copia escribible de la instantánea pasa a ser `@` y el almacén `.snapshots` de Snapper se traslada a ella.
3. El equipo reinicia en el sistema restaurado. Si falla cualquier paso, los subvolúmenes y archivos de arranque vuelven a su estado anterior y no se reinicia.

El sistema restaurado elimina `@eitr-guard-failed` al llegar a la pantalla de inicio de sesión; la siguiente sesión muestra una notificación. Las carpetas personales no se modifican. Esta protección no puede ayudar si el propio kernel no arranca: inicia la instantánea de la actualización desde el menú de arranque (más abajo). Nunca se activa para otros esquemas de disco.

## Cambios de autenticación

Seguridad → activar huella/FIDO2 guarda copias de `/etc/pam.d/hyprlock`, `sddm` y `sudo` bajo `/var/lib/eitr/pam-backups/<timestamp>/` antes de editarlos y restaura los tres si falla alguna escritura. La huella se añade a los tres, por lo que "solo contraseña" también se aplica a la pantalla de bloqueo. pam_fprintd puede retrasar la solicitud de contraseña hasta 10 segundos. Para volver a una política anterior desde un shell root funcional o un TTY:

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## Desbloqueo del disco mediante TPM

Seguridad → Desbloqueo del disco mediante TPM puede añadir una ranura de clave TPM2 a una raíz LUKS2 para desbloquear el disco al arrancar sin escribir la contraseña. Nada de esto se ejecuta desde el instalador. El auxiliar root (`luks-tpm-check`, `luks-recovery-key`, `luks-tpm-enroll`, `luks-tpm-remove`) rechaza la operación salvo que el dispositivo sea LUKS2, aparezca un TPM2 en `systemd-cryptenroll --tpm2-device=list` y ya exista una ranura de contraseña o recuperación. Solo **añade** una ranura; la contraseña permanece.

- **Primero, la clave de recuperación.** Walker ofrece `systemd-cryptenroll --recovery-key`; la clave se muestra una sola vez en el terminal y nunca se almacena. Anótala sin conexión. Funciona en la solicitud de contraseña habitual.
- **Elección del PCR.** Eitr vincula el desbloqueo al PCR 7 (estado y claves de Secure Boot). Las actualizaciones del firmware rara vez lo cambian, pero un cambio de claves de Secure Boot sí. El PCR 7 solo ofrece una protección significativa con Secure Boot activado y tus propias claves (consulta [SECURE-BOOT.md](SECURE-BOOT.md)); de lo contrario, cualquiera puede arrancar el equipo con una línea de comandos del kernel modificada y obtener el disco desbloqueado. Para mayor protección, regístralo manualmente con PIN: `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`.
- **Initramfs.** El hook `encrypt` de busybox no puede usar tokens TPM2; por eso se rechaza el registro mientras esté configurado. Cambiar a `systemd` y `sd-encrypt` en `HOOKS` (con `rd.luks.name=<LUKS-UUID>=root` en lugar de `cryptdevice=` en la línea de comandos del kernel, o usando `/etc/crypttab.initramfs`) es un cambio crítico del arranque que Eitr deja en tus manos. Hazlo, ejecuta `sudo mkinitcpio -P`, actualiza la entrada de arranque y confirma que puedes arrancar con contraseña **antes** de registrar el TPM.

Si el TPM deja de desbloquear (cambio de firmware o Secure Boot, o restablecimiento del TPM), vuelve a aparecer la solicitud de contraseña. Introdúcela, elimina el registro y repítelo. Para deshacerlo completamente, usa la opción para eliminar el desbloqueo mediante TPM o, desde cualquier shell funcional:

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## Restablecimiento de fábrica

Los equipos instalados con la ISO de Eitr también guardan un punto de restauración de solo lectura del primer inicio de sesión, fuera de Snapper. Walker → Sistema → Mantenimiento → Restablecimiento de fábrica vuelve a ese punto, conservando o no los archivos personales; consulta [FACTORY-RESET.md](FACTORY-RESET.md).

## Inspeccionar los puntos de recuperación

Usa Walker → Sistema → Mantenimiento → Instantáneas o ejecuta estas comprobaciones de solo lectura:

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

Si falla el escritorio pero el sistema arranca, cambia a una consola de texto o usa una conexión SSH que hayas configurado tú. Si no arranca, usa la ISO oficial del instalador de Arch y monta el sistema de archivos Btrfs. Identifica el disco, el mapeo de cifrado, el subvolumen raíz, el número de instantánea y el montaje EFI correctos antes de cambiar nada. No copies comandos de otro equipo sin comprobarlos.

## Instantáneas de la carpeta personal

Desactivadas de forma predeterminada. **Sistema > Mantenimiento > Instantáneas > Instantáneas de la carpeta personal** las activa (pide confirmación; desactivarlas las elimina). La configuración `home` de Snapper conserva una instantánea de `/home` cada hora durante un día y una diaria durante una semana, eliminando las más antiguas cuando el espacio libre baja del 20 %.

Se excluyen las cachés, `~/Downloads`, las carpetas de discos de máquinas virtuales (`~/.local/share/libvirt/images`, GNOME Boxes, `~/VirtualBox VMs`) y la biblioteca de Steam. En el siguiente arranque, antes de cualquier inicio de sesión, `eitr-home-exclusions.service` las convierte en subvolúmenes Btrfs anidados que las instantáneas personales no incluyen. Los archivos se conservan mediante reflinks, sin espacio adicional para moverlos. El modo Mantener mis archivos del restablecimiento de fábrica lleva estos subvolúmenes a la carpeta personal restaurada: los ocultos van a "Settings before reset" y las cachés se descartan. Si alguno no puede moverse, se conserva la carpeta personal anterior para revisarla en vez de eliminarla.

La conversión y la creación de carpetas excluidas ausentes se ejecutan como el propietario de la carpeta personal, incluidos sus grupos suplementarios. Se rechazan las carpetas personales accedidas mediante enlaces simbólicos y las rutas en otro sistema de archivos; una carpeta excluida que es un enlace simbólico o está dentro de uno (como Descargas en otro disco) se deja como está y nunca se sigue. Si la conversión falla, la configuración queda pendiente y las carpetas `NAME.eitr-subvolume` o `NAME.eitr-old` se conservan para su inspección; los archivos originales permanecen en `NAME` o `NAME.eitr-old`. Revise estas carpetas antes de eliminar los restos y reintentarlo. No se realiza ninguna limpieza automática privilegiada: eliminar un subvolumen Btrfs no vacío como su propietario normalmente requiere `user_subvol_rm_allowed`.

**Instantáneas > Restaurar un archivo o carpeta** (o `eitr restore PATH`) enumera las instantáneas que contienen la ruta y copia la versión elegida junto a la actual como `NAME (restored DATE)`, o en su lugar original si se había borrado. Nunca se sobrescribe nada.

## Qué cambió cada actualización

Antes de revertir, comprueba qué desharías. **Sistema > Mantenimiento > Instantáneas > Lo que cada actualización cambió** (o `eitr snapshots changes`) muestra cada par anterior/posterior de una actualización y cuántos paquetes se actualizaron, cambiaron a una versión anterior, instalaron o eliminaron. `eitr snapshots changes <before number>` enumera todos los paquetes de una actualización con sus versiones antigua y nueva. Compara las bases de datos de paquetes dentro de las dos instantáneas; si aún no hay instantánea posterior, compara con el sistema en ejecución.

## Arrancar una instantánea anterior

Con GRUB o Limine, el menú de arranque puede mostrar instantáneas de Snapper de solo lectura para inspeccionar y revertir una actualización fallida sin un medio externo. El instalador solo lo ofrece tras escribir `yes`; en una instalación existente ejecuta `bash distro/bootloader/setup.sh` (`--check` solo informa). Comprueba el resultado en Walker → Sistema → Mantenimiento → Instantáneas → estado de instantáneas arrancables o con `sudo /usr/lib/eitr/eitr-system snapshots-boot-status`.

| Cargador de arranque | Integración | Paquetes (`distro/bootloader/`) |
|---|---|---|
| GRUB | `grub-btrfsd.service` reconstruye el submenú "Arch Linux snapshots" cuando Snapper añade o elimina una instantánea | `grub-btrfs`, `inotify-tools` (oficiales) |
| Limine | `limine-snapper-sync.service` añade entradas de instantáneas a `limine.conf` | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **No compatible.** Solo carga kernels desde la partición EFI/XBOOTLDR y no puede abrir instantáneas Btrfs | Usa el procedimiento con un medio externo de abajo |

La detección lee los archivos de GRUB, Limine y systemd-boot en `/boot`, `/efi` y `/boot/efi`. Si hay varios cargadores configurados (por ejemplo, restos de systemd-boot junto a GRUB), la configuración rechaza la operación en vez de adivinar. Elimina los archivos obsoletos o configura las entradas manualmente. Primero copia `grub.cfg`/`limine.conf` a `/var/lib/eitr/boot-config-backups/<timestamp>/` y habilita el servicio para el próximo arranque:

- **GRUB:** la configuración ejecuta `grub-mkconfig -o /boot/grub/grub.cfg` una vez. Si `/boot` es una partición separada, las entradas de instantáneas arrancan el kernel *actual*. Tras actualizarlo, restaura también el archivo de arranque correspondiente (más abajo).
- **Limine:** `limine-snapper-sync` gestiona las entradas creadas por `limine-entry-tool` (de `limine-mkinitcpio-hook`) y conserva copias del kernel de cada instantánea en la partición EFI, que necesita espacio (el proyecto recomienda 4 GiB). Revisa `/etc/default/limine` (`SNAPPER_CONFIG_NAME="root"` y `ESP_PATH` si no se detecta), ejecuta `sudo limine-update`, comprueba el menú y después ejecuta `sudo systemctl start limine-snapper-sync.service`. Eitr no ejecuta `limine-update` por ti porque reescribe el menú de arranque.

Para deshacerlo, deshabilita el servicio y restaura la copia de seguridad, por ejemplo con `sudo systemctl disable grub-btrfsd.service` y `sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`.

### Instantáneas de solo lectura

Las instantáneas de Snapper son de solo lectura. Una instantánea arrancada directamente no puede escribir en `/var`, por lo que SDDM y otros servicios pueden fallar. Inicia sesión en una consola de texto (Ctrl+Alt+F3) si no aparece el inicio gráfico. Una capa de superposición en el initramfs permite escribir en la instantánea en RAM; los cambios desaparecen al reiniciar. Eitr no modifica `HOOKS`: añade la capa y regenera tú mismo. Solo las instantáneas creadas después contendrán el hook:

- GRUB: añade `grub-btrfs-overlayfs` a `HOOKS=(...)` en `/etc/mkinitcpio.conf` y ejecuta `sudo mkinitcpio -P`.
- Limine: añade `btrfs-overlayfs` después de `filesystems` (o `sd-btrfs-overlayfs` con los hooks de systemd) y ejecuta `sudo limine-update`.

### Revertir de forma permanente

1. Elige la instantánea "before package upgrade" más reciente del menú de arranque y confirma que el sistema funciona en ella.
2. **Limine:** ejecuta `sudo limine-snapper-restore` y elige la instantánea. Restaura usando el `RESTORE_METHOD` configurado y añade una entrada de respaldo del sistema sustituido para poder deshacer la propia restauración desde el menú de arranque.
3. **GRUB:** `snapper rollback` solo funciona si la raíz se monta mediante el subvolumen predeterminado de Btrfs. Arch suele arrancar con `rootflags=subvol=@` (comprueba `findmnt -no OPTIONS /` y `/etc/fstab`), por lo que el rollback no tendría efecto. Sustituye el subvolumen raíz desde un medio externo tras inspeccionar los subvolúmenes del nivel superior del sistema de archivos. El siguiente ejemplo es **solo** para la instalación guiada de Eitr, donde Snapper creó el subvolumen anidado `@/.snapshots`; otros esquemas requieren sus rutas reales:

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   Si falla algún comando, detente e inspecciona; no elimines la raíz conservada. Comprueba que el almacén de instantáneas está en la raíz restaurada y revisa su fstab antes de continuar. Si `/boot` está separado, restaura el archivo correspondiente de `/var/lib/eitr/boot-backups/<number>/`, reinicia desde la entrada normal, ejecuta `sudo grub-mkconfig -o /boot/grub/grub.cfg` y elimina `@.broken` con `sudo btrfs subvolume delete` solo después de verificar el sistema restaurado.

## Restaurar con seguridad desde un medio externo

1. Guarda los archivos más recientes que necesites. Monta el nivel superior del sistema de archivos Btrfs e inspecciona sus subvolúmenes. Localiza el subvolumen `snapshot` de la instantánea elegida; las rutas dependen de dónde se monte `.snapshots`.
2. Conserva el subvolumen raíz fallido cambiándole el nombre. Crea una **instantánea Btrfs escribible** del punto de recuperación elegido en la ruta original del subvolumen raíz, respetando los rootflags y el fstab del cargador instalado.
3. Monta esa raíz restaurada y sus particiones reales de arranque/EFI. Restaura los archivos de arranque correspondientes si cambiaron el kernel, initramfs o cargador. Deben coincidir con la instantánea raíz elegida; nunca mezcles un kernel más nuevo con módulos antiguos.
4. Revisa el fstab y la configuración del cargador; regenera el initramfs o repara las entradas desde `arch-chroot` según necesite ese equipo. Reinicia solo cuando la raíz y los archivos de arranque sean coherentes.

Este es un procedimiento manual que depende del esquema de disco, **no una implementación verificada de reversión con un clic**. El comando `rollback` de Snapper por sí solo no basta para cualquier esquema de subvolúmenes y cargadores de Arch. Las entradas de instantáneas de GRUB y Limine aún necesitan validación en hardware real antes de afirmar que ofrecen recuperación automática.

Referencias: [grub-btrfs](https://github.com/Antynea/grub-btrfs), [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync), [conceptos de recuperación de Snapper](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html), [guía de instalación de Arch](https://wiki.archlinux.org/title/Installation_guide).
