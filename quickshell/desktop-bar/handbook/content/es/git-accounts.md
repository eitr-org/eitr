# Cuentas Git

Abre **Desarrollo > Cuentas de Git**. Puedes usar cuentas GitHub y GitLab simultáneamente, incluso varias del mismo proveedor o servidor empresarial. Las instalaciones nuevas incluyen GitHub CLI (`gh`) y GitLab CLI (`glab`); las ISO existentes deben reconstruirse para incorporar cambios.

Cada cuenta muestra dónde la usa Git: **Predeterminado**, sus carpetas o **Todavía sin usar**. Enter abre las acciones; Shift+Backspace vuelve a la lista.

## Primera configuración

1. **Añadir cuenta** abre un formulario con proveedor, nombre de cuenta, nombre y correo del autor de commits, servidor y una clave SSH privada existente (lista las claves de `~/.ssh`), o ninguna por ahora. Después pregunta si será la cuenta predeterminada y qué carpeta usa solo esa cuenta, muestra el resultado y guarda con Enter.
2. **Importar configuración existente** lee identidades configuradas manualmente: `user.name`/`user.email` predeterminados y reglas por carpeta `includeIf "gitdir:…"` de `~/.gitconfig` o `~/.config/git/config`, incluidos el alias SSH y la clave usados por un archivo incluido (`url.<alias>.insteadOf`). Enumera los hallazgos y crea cuentas y reglas correspondientes tras confirmar. Tus archivos quedan intactos; los patrones de carpetas con comodines se indican como omitidos.

## Cuenta predeterminada y carpetas

La cuenta **predeterminada** se usa en carpetas sin cuenta propia. Una cuenta **de carpeta** solo se usa en sus repositorios. Gana la carpeta más específica; los ajustes locales del repositorio y las opciones de línea de comandos o del entorno de Git siguen teniendo prioridad. EITR conserva configuración global y comentarios, añade una inclusión marcada al final de `~/.gitconfig`, y las reglas confirmadas prevalecen sobre identidades de otras inclusiones.

Las acciones de Walker piden confirmación antes de guardar y muestran una notificación: **Establecer como predeterminada** o **Dejar de usar como predeterminada**, **Añadir carpeta** (elige `~/Development`, una carpeta dentro o **Otra carpeta…** para escribir una ruta) y **Eliminar carpeta**. Git usa el directorio `.git` real; los worktrees vinculados y submódulos pueden seguir la cuenta de un repositorio padre.

## Claves SSH

La identidad de los commits no da acceso al repositorio. **Mostrar clave pública** muestra y copia la clave pública e indica dónde añadirla en el proveedor (GitHub: Settings > SSH keys). **Elegir una clave SSH existente** elige una clave de `~/.ssh`; **Crear clave SSH** crea una Ed25519 con contraseña y muestra su clave pública. **Probar conexión** muestra el saludo del proveedor, como "Hi username!", en una notificación. Nunca compartas la clave privada.

Las claves solo se aplican al servidor SSH del proveedor. El lanzador resuelve los alias existentes sin conectarse y usa únicamente la clave seleccionada, ignorando otros ajustes SSH de esa conexión. Se rechazan conexiones por proxy; conserva un `core.sshCommand` local al repositorio para configuraciones avanzadas. Sigue activa la comprobación de servidores conocidos. Las cuentas sin clave configurada usan SSH normal, no la clave de otra cuenta. Las credenciales HTTPS y sus auxiliares no cambian.

## CLI de los proveedores

**Iniciar sesión en la CLI** inicia sesión en un directorio de configuración separado por cuenta, sin cambiar la cuenta global normal de `gh` o `glab`. Se eliminan las variables de tokens heredadas para ese proceso. La confirmación explica que los tokens se guardan en perfiles privados sin cifrar, evitando entradas del llavero compartidas entre cuentas del mismo servidor. Nunca compartas `~/.config/eitr/git-accounts/cli`; no se incluye en las copias de seguridad de EITR.

Desde un repositorio, usa la CLI que selecciona la cuenta correspondiente:

```sh
eitr-git cli auth status
eitr-git cli repo view
```

La cuenta predeterminada o de carpeta elige `gh` o `glab`. Los comandos normales conservan su comportamiento global. Registrar la clave SSH no autentica operaciones de la API de la CLI. No se incluye una CLI de Bitbucket.

## Eliminación y recuperación

**Editar nombre y correo** cambia la identidad; **Eliminar cuenta** elimina la cuenta y sus reglas tras confirmar. Eliminar una regla de carpeta vuelve a una más general o a la predeterminada; quitar la cuenta predeterminada restaura los ajustes anteriores de Git fuera de las reglas restantes. Nunca se borran proyectos, claves ni credenciales de las CLI; eliminar una regla no revoca el acceso al proveedor.

Los ajustes versionados están en `~/.config/eitr/git-accounts.json`. Cada vez que se aplican cambios, se guarda una copia del archivo global de Git, de la inclusión activa y de los ajustes en `~/.local/state/eitr/git-account-backups/<id>`, con permisos privados. `manifest.json` identifica rutas originales, nombres de copias y permisos. Nunca se copian claves ni tokens de las CLI. Para recuperar manualmente, revisa el manifiesto y conserva cualquier cambio posterior a la copia antes de restaurar. Las inclusiones EITR modificadas o inválidas se rechazan en vez de sustituirse silenciosamente.

Referencias: [inclusiones condicionales de Git](https://git-scm.com/docs/git-config), [perfiles de GitHub CLI](https://cli.github.com/manual/gh_help_environment), [perfiles de GitLab CLI](https://docs.gitlab.com/cli/configuration/).
