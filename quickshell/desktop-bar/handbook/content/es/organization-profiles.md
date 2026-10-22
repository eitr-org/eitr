# Perfiles de organización

Use la ISO oficial sin modificarla. En una memoria FAT32 llamada `EITRANSWERS`, coloque `eitr-profile.json` junto a `eitr-answers.json` o en su lugar. Solo el perfil conserva el asistente normal y muestra sus cambios en la revisión. Con ambos archivos, se muestran la operación del disco y todos los cambios antes de la cuenta de 15 segundos. Ctrl+C cancela antes de modificar discos. Mantenga la memoria conectada hasta el apagado.

Ejemplo completo: sustituya los hashes de ejemplo por los valores reales de `sha256sum` y copie los archivos indicados.

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Solo `version` y `name` son obligatorios. Se rechazan claves desconocidas y duplicadas. Quite secciones opcionales innecesarias. Las rutas son relativas a la memoria; se prohíben enlaces simbólicos, rutas absolutas y `..`. Todos los archivos deben existir y coincidir con su SHA-256 en minúsculas antes de cambiar discos. El fondo debe ser PNG, JPEG o WebP válido. La clave debe contener exactamente una clave pública OpenPGP y el servidor debe usar HTTPS sin credenciales. La clave se importa y firma localmente en pacman: use solo claves de confianza. Los paquetes y scripts son código administrativo de confianza, sin aislamiento.

`remove` solo acepta `distro/removable-apps.json`, revisado paquete por paquete en `distro/PROFILE-PACKAGE-REVIEW.md`. Un paquete protegido o desconocido rechaza todo el perfil. pacman comprueba dependencias, sin eliminación recursiva ni omitirlas. Las políticas de grupo excluyen los paquetes permitidos de `gaming`, `media`, `development`, `sharing` y `remote_access`. `false` desactiva y `true` permite. `update_channel` solo admite `"stable"`. Las políticas omitidas no restringen.

Las recetas usan `group/name` de `distro/software.json`. Solo se aceptan recetas pacman y Flatpak precompiladas. AUR, instaladores interactivos y aplicaciones web se rechazan; suministre paquetes precompilados en la memoria. Repositorios, recetas y Flathub requieren internet. Los archivos de paquetes funcionan sin conexión si sus dependencias están en la ISO o la memoria. Los nombres deben existir en las bases actuales de pacman; actualice por el proceso normal antes de comprobar adiciones online. No se compila AUR. Las adiciones pacman online realizan una actualización completa. El repositorio adicional sirve para actualizaciones futuras; suministre sus paquetes exclusivos como archivos.

Durante la instalación, las aplicaciones de Flathub y las recetas Flatpak quedan en cola para el usuario del escritorio y se instalan en el primer arranque con conexión a internet. Las instalaciones fallidas se reintentan en el siguiente arranque. Al aplicar un perfil en una máquina ya instalada, se instalan directamente.

Navegadores: Firefox y Chromium; añada Chromium explícitamente. Tema y fondo se guardan para el próximo inicio del usuario elegido, sin reiniciar el escritorio. Canal y repositorio son globales. `setup` se ejecuta como root al final, desde la copia privada de la memoria, tras registrar el perfil. Un marcador SHA-256 registra el intento antes de empezar: fallos e interrupciones no lo repiten silenciosamente. Cambie el script y su hash para autorizar otro intento. Los errores quedan visibles; las transacciones terminadas no se revierten.

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check` lee archivos y metadatos, con directorios temporales, sin cambiar la configuración. `apply` usa `eitr-system profile-apply` como root, copia y vuelve a validar, muestra el resumen y exige escribir `APPLY PROFILE`. Cancelar no cambia nada. Elimina mediante pacman, instala adiciones, guarda valores y escribe `/etc/eitr/policies.json` (0644, root:root) y `/etc/eitr/profile.json`. Otro perfil sustituye las decisiones registradas, sin reinstalar automáticamente eliminaciones anteriores ni restablecer preferencias omitidas. Los marcadores de setup permanecen.

Las exclusiones filtran los manifiestos del instalador. `IgnorePkg` en pacman impide que System Update reinstale por dependencia: un conflicto debe detener la actualización. Crear preferencias de usuario no instala aplicaciones. Las políticas ocultan menús y búsqueda de Elephant, controles de acceso remoto en la barra, colaboración de asistentes y cambio de canal. Las herramientas también rechazan llamadas directas. Puede ser necesario actualizar menús o paneles.

**Esto no bloquea a un usuario con root.** Root puede editar políticas o usar otras herramientas. El bloqueo real exige no conceder root. No es gestión de flotas. Las instalaciones con y sin red, un perfil rechazado y su aplicación a un equipo instalado pasaron en una VM; las comprobaciones restantes están en `distro/PROFILE-VM-TESTING.md`.
