# Copia de seguridad y restauración

Traslada tus ajustes del escritorio, carpetas personales elegidas y listas de aplicaciones instaladas a otro equipo o a una instalación nueva de Eitr en un único archivo cifrado `.eitrbackup`.

Las instantáneas de [Recuperación e instantáneas](handbook:recovery) permanecen en el mismo disco para revertir actualizaciones. Copia y restauración crea un archivo portátil comprimido con `zstd` y cifrado con `age` listo para discos externos o la nube.

## Abrir Copia y restauración

- **Configuración**: pulsa **SUPER + ,** y entra en **Sistema > Copia y restauración**.
- **Walker**: pulsa **SUPER + F** y abre **Configuración > Sistema > Copia y restauración**.
- **Terminal**: ejecuta `eitr backup` (o `eitr-backup wizard`).

## Crear una copia de seguridad

1. Elige qué categorías incluir:
   - **Ajustes de Eitr**: preferencias del escritorio, anulaciones en `~/.config/eitr/overrides`, temas, fondos de pantalla y pantallas de bloqueo propios.
   - **Ajustes de apps**: carpetas en `~/.config` ajenas a Eitr (sin perfiles de navegador ni cachés).
   - **Carpetas personales**: carpetas principales de `$HOME`, desmarcadas por defecto, más **Añadir carpeta…** para subcarpetas dentro de `$HOME`. Los tamaños se calculan en segundo plano.
   - **Apps instaladas**: listas de paquetes oficiales, AUR, Flatpak, complementos de Eitr y elementos de Eitr Store instalados además del sistema base.
   - **Configuración de la máquina**: desactivada por defecto; anulaciones locales de pantalla y `hypr/local.lua` para este equipo.
2. Revisa o desmarca carpetas de aplicaciones y apps instaladas (con búsqueda y agrupación por origen).
3. Elige un destino. Los discos externos aparecen antes que `~/Backups`. Guardar en el mismo disco muestra una advertencia; la falta de espacio se rechaza antes de escribir nada.
4. Escribe la frase de contraseña dos veces. Nunca aparece en argumentos, variables de entorno ni archivos guardados.
5. Revisa el resumen en **Revisar** y pulsa **Enter** para escribir el archivo atómicamente, o **Esc** para cancelar sin cambios.

### Qué queda fuera

- Perfiles y cachés de navegadores, bloqueos, sockets y archivos temporales.
- Código y archivos predeterminados del sistema, más salidas generadas (se reconstruyen tras restaurar).
- Credenciales fuera de las preferencias: claves SSH y GPG, llaveros, CLIs en la nube (`~/.aws`, `~/.azure`, `~/.config/gcloud`, `~/.config/gh`) y secretos de Git o Wi-Fi.

## Restaurar desde una copia

1. Selecciona un archivo `.eitrbackup` (de discos conectados, `~/Backups`, el último destino o una ruta personalizada) e introduce la contraseña.
2. Eitr lee primero `manifest.json` y permite desmarcar categorías, carpetas o apps antes de tocar el disco.
3. Confirma en **Revisar**. Los archivos reemplazados se respaldan antes con un registro en `~/.local/state/eitr/restore-backups/<id>/`.
4. Las aplicaciones se reinstalan en orden: paquetes oficiales disponibles en una sola transacción de `pacman` (los ausentes se omiten y listan), paquetes AUR uno a uno con `yay`, Flatpaks, y complementos o elementos de Eitr Store **siempre mediante aprobación normal de revisión**.
5. Los temas y archivos generados se reconstruyen conservando los fondos por pantalla, y Hyprland recarga si la sesión está activa.
6. Después de restaurar, vuelve a iniciar sesión en navegadores, CLIs en la nube (`gh`, `gcloud`, `aws`, `az`) y repón claves SSH/GPG externas.

## Deshacer una restauración

```sh
eitr backup undo <id>
```

Consulta `<id>` en **Configuración > Sistema > Copia y restauración** o con `eitr-backup status`. Undo repone archivos reemplazados, elimina los añadidos y regenera los temas.

## Referencia de CLI

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Las contraseñas se piden en `/dev/tty` sin eco o mediante `--passphrase-fd N`. Las versiones de formato más nuevas se rechazan claramente sin alterar archivos.
