# Restablecimiento de fábrica

Los equipos instalados con la ISO de Eitr pueden volver al estado del primer inicio de sesión desde Walker → Sistema → Mantenimiento → Restablecimiento de fábrica. El restablecimiento es local: restaura una copia de solo lectura guardada en el mismo disco. No es una copia de seguridad ni un borrado seguro; si el disco falla, se pierden tanto el sistema como su punto de restauración.

## El punto de restauración

El último paso del instalador guiado ejecuta `eitr-factory-reset capture`, que guarda la instalación terminada en el subvolumen Btrfs de nivel superior `@eitr-factory`:

| Ruta | Contenido |
|---|---|
| `root` | instantánea de solo lectura de `@` (sistema, cuentas y ajustes) |
| `home` | instantánea de solo lectura de `@home` (carpetas personales preparadas durante la instalación) |
| `boot.tar` | archivos de la partición EFI: Limine, su menú, kernel e initramfs |
| `manifest.json` | fecha de creación, UUID del sistema de archivos y de la partición EFI, cuentas y SHA-256 de `boot.tar` |

El propio `@eitr-factory` pasa a ser de solo lectura. Está junto a `@`, no dentro de `@/.snapshots`: Snapper nunca lo enumera ni lo elimina durante la limpieza, y Walker no ofrece una opción para borrarlo. Root sí puede eliminarlo, y formatear el disco o un fallo de este lo destruye. Sus instantáneas comparten datos con el sistema en ejecución: al principio ocupan poco espacio y crecen cuando las actualizaciones sustituyen los archivos originales.

`capture` se niega a sustituir un punto de restauración existente. Las instalaciones hechas sin la ISO no tienen ninguno, y Restablecimiento de fábrica lo indica.

## Los dos modos de restablecimiento

**Borrar todo** devuelve el equipo al primer inicio de sesión: desaparecen las aplicaciones instaladas después, los ajustes modificados, las cuentas añadidas posteriormente y todos los archivos de las carpetas personales.

**Mantener mis archivos** restaura el sistema, las aplicaciones y los ajustes, conservando las carpetas personales. Para cada cuenta presente en el punto de restauración, las entradas ocultas actuales (`~/.config`, `~/.local`, `~/.ssh`, perfiles del navegador y otras) se mueven a una carpeta visible llamada `Settings before reset <date time>` dentro de su carpeta personal. Después se copian las entradas ocultas del punto de restauración. No se borra nada de la carpeta personal. Las cuentas añadidas tras la instalación se eliminan del sistema, pero sus carpetas permanecen en `/home`.

Ambos modos conservan la contraseña de cifrado del disco (nunca se modifica la cabecera LUKS) y la contraseña actual de cada cuenta también presente en el punto de restauración. La ranura de desbloqueo mediante TPM permanece en la cabecera LUKS, pero el initramfs restaurado pide la contraseña hasta que se configure de nuevo ese desbloqueo. Se conservan los registros (`@log`) y la caché de paquetes (`@pkg`).

## Confirmación

La acción de Walker muestra dos advertencias separadas en un terminal:

1. Qué elimina y conserva el modo elegido. Solo `y` o `yes` permite continuar; Enter cancela.
2. Qué equipo se restablecerá, que se reiniciará inmediatamente y que se perderá el trabajo sin guardar. Debes escribir exactamente `RESET MY COMPUTER`.

El auxiliar propiedad de root (`/usr/lib/eitr/eitr-factory-reset`) vuelve a comprobar la frase y valida lo siguiente antes de cambiar nada:

- `/` es el subvolumen `@` y `/home` es `@home` en el mismo sistema de archivos Btrfs; `/boot` es la partición EFI en FAT.
- El punto de restauración y sus instantáneas siguen siendo de solo lectura; el manifiesto identifica ese sistema de archivos y esa partición EFI, y `boot.tar` coincide con su SHA-256.
- Secure Boot está desactivado: los archivos de arranque restaurados no están firmados con las claves registradas.
- No hay ningún restablecimiento anterior pendiente.

`sudo /usr/lib/eitr/eitr-factory-reset status` (Walker → Estado del restablecimiento) realiza las mismas comprobaciones sin cambiar nada.

## Cómo se realiza el restablecimiento

Nunca se escribe sobre la raíz ni las carpetas personales en uso. En un nuevo subvolumen de nivel superior, `@eitr-reset-previous`, el auxiliar:

1. Crea una instantánea escribible de la raíz del punto de restauración, recrea el subvolumen `.snapshots` de Snapper, copia las contraseñas actuales y habilita allí `eitr-factory-reset-finish.service`.
2. Crea las nuevas carpetas personales: una instantánea escribible de las del punto de restauración (Borrar todo), o una instantánea del `@home` actual con los ajustes apartados como se describe arriba (Mantener mis archivos).
3. Archiva los archivos actuales de la partición EFI en `boot.tar` y extrae el archivo del punto de restauración para preparar su copia.

Un fallo hasta este punto elimina `@eitr-reset-previous` y deja el equipo intacto. A continuación, el auxiliar copia los archivos de arranque restaurados a la partición EFI (si falla, restaura el archivo que acaba de crear), renombra `@` y `@home` a `old@` y `old@home` dentro de `@eitr-reset-previous`, renombra los subvolúmenes preparados a `@` y `@home` y reinicia. Si falla un cambio de nombre, restaura los nombres anteriores y los archivos de arranque.

En el siguiente arranque, `eitr-factory-reset-finish.service` confirma que la raíz en uso es la restaurada, elimina `@eitr-reset-previous` (incluidas las instantáneas de Snapper del sistema antiguo) y se deshabilita.

## Recuperar un restablecimiento interrumpido

Un corte de corriente durante los cambios de nombre puede dejar `@` o `@home` ausente. Arranca desde la ISO de Eitr, pulsa Escape para salir del asistente, desbloquea el disco si está cifrado (`cryptsetup open /dev/<partition> root`) e inspecciona:

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # or the Btrfs partition itself
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- Existen `@` y `@home` y ya no existe `@eitr-reset-previous/new-root`: el intercambio terminó. Reinicia; el servicio de finalización limpiará los restos.
- Falta `@` o `@home`: devuelve su nombre al `@eitr-reset-previous/old@` u `old@home` correspondiente (`mv /mnt/@eitr-reset-previous/old@ /mnt/@`), extrae `@eitr-reset-previous/boot.tar` en la partición EFI para que coincida con el sistema antiguo y reinicia.

Elimina `@eitr-reset-previous` con `btrfs subvolume delete --recursive` solo cuando el sistema arranque correctamente; hasta entonces contiene el sistema anterior.

## Verificación

Probado en máquinas virtuales UEFI sin red (véase [LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)): ambos modos en una instalación sin cifrar que borra el disco y en una instalación LUKS2 junto a un disco con estructura similar a la de Windows. Tras cada prueba se verificaron el arranque, el inicio de sesión y la limpieza del servicio de finalización. Aún no probado: hardware real, cortes de corriente durante el intercambio y conservación del punto de restauración durante actualizaciones en línea (las máquinas virtuales no tenían red).
