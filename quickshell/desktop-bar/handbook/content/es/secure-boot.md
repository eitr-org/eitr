# Secure Boot con sbctl

Eitr documenta Secure Boot, pero **nunca registra claves ni firma archivos por ti**. Un error puede impedir que el equipo arranque o muestre imagen. Sigue estos pasos manualmente, en un equipo donde puedas acceder a la configuración del firmware, con la contraseña del disco y las [instrucciones de recuperación](RECOVERY.md) a mano. Todavía no se ha verificado esta guía en el hardware de prueba de Eitr.

## Antes de empezar

- Solo arranque UEFI. Aprende a abrir la configuración del firmware (a menudo F2, Del o F12) y establece una contraseña de administrador del firmware; de lo contrario, cualquiera podrá volver a desactivar Secure Boot.
- Si has registrado el desbloqueo del disco mediante TPM, ten preparada la contraseña: registrar claves cambia el PCR 7 del TPM, por lo que el próximo arranque la pedirá una vez. Después, vuelve a registrar el desbloqueo mediante TPM (Seguridad → desbloqueo del disco mediante TPM: eliminar y volver a registrar).
- En el firmware, pon Secure Boot en **Setup Mode** (a menudo "Clear keys" o "Reset to Setup Mode"). No elimines claves que no puedas restaurar; la mayoría de los firmwares ofrece "Restore factory keys".

## Procedimiento con sbctl

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s` guarda el archivo en la base de datos de sbctl; su hook de pacman vuelve a firmar los archivos registrados tras actualizar el kernel o el cargador de arranque. Ejecuta `sudo sbctl verify` después de cada cambio; después, activa Secure Boot en el firmware y reinicia. Guarda una copia de seguridad de `/var/lib/sbctl` sin conexión y en privado: contiene las claves de firma. Nunca la copies en este repositorio.

## Riesgos

- **Option ROMs y claves del fabricante.** Las tarjetas gráficas, unidades NVMe y tarjetas de red suelen ejecutar firmware (Option ROMs) firmado por la autoridad certificadora UEFI de Microsoft. Registrar únicamente tus claves sin `-m` puede hacer que el firmware lo rechace: sin imagen, sin disco de arranque y, en algunos portátiles, sin forma de volver a la configuración del firmware. Mantén `-m` salvo que sepas que el hardware no utiliza ese tipo de firmware. Como alternativa, `sbctl enroll-keys --tpm-eventlog` puede añadir los hashes de las Option ROMs usadas en este arranque, pero cambian con las actualizaciones de hardware o firmware.
- **Archivos sin firmar.** Cada binario EFI en la ruta de arranque debe estar firmado con tus claves. Omitir un archivo impide el arranque; desactiva Secure Boot en el firmware para recuperar el acceso.
- **Arranque dual.** Windows solo sigue arrancando con `-m`.

## Cargadores de arranque y entradas de instantáneas

- **GRUB:** reinstálalo con `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock` y firma el nuevo `grubx64.efi` y los kernels en `/boot`. Con esta configuración, GRUB no comprueba las firmas de los kernels: las entradas de instantáneas de grub-btrfs siguen arrancando, pero la protección cubre el binario de GRUB, no cada kernel. Vuelve a ejecutar `grub-install` y `sbctl sign` tras las actualizaciones de GRUB que cambien la imagen.
- **Limine:** firma el binario EFI de Limine (`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` o la ruta donde esté instalado). Limine protege su configuración y los kernels con hashes, no con firmas. Si registras el hash de configuración en el binario (`limine enroll-config`), cada cambio en `limine.conf`, incluida cada nueva entrada de instantánea creada por limine-snapper-sync, exige volver a registrarlo y firmarlo. Antes de activar Secure Boot, confirma que la configuración de `limine-mkinitcpio-hook` hace esto (usa sbctl cuando está instalado); de lo contrario, la siguiente sincronización de instantáneas hará que el cargador rechace su menú.
- **systemd-boot:** firma `systemd-bootx64.efi` y los kernels o imágenes unificadas del kernel que carga. No admite entradas de arranque de instantáneas.
- Las entradas de instantáneas de kernels antiguos también deben superar las comprobaciones del cargador. Tras activar Secure Boot, arranca una vez desde una entrada de instantánea para comprobar que funciona antes de necesitarla.

## Cómo deshacerlo

1. Entra en el firmware y desactiva Secure Boot, o elige "Restore factory keys" para restaurar las claves del fabricante. El sistema instalado sigue arrancando con Secure Boot desactivado.
2. Si quieres, elimina archivos registrados en la base de datos de sbctl con `sudo sbctl remove-file <file>`; las firmas de los propios archivos son inofensivas.
3. Si registraste el desbloqueo mediante TPM con Secure Boot activado, el PCR 7 vuelve a cambiar: introduce la contraseña una vez y registra de nuevo el desbloqueo.

Referencias: [sbctl](https://github.com/Foxboron/sbctl), [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
