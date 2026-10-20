# Terminal y editores

**SUPER + Enter** abre Kitty. **SUPER + Ctrl + Enter** abre o conecta la sesión principal de tmux. **SUPER + P** busca archivos por coincidencia aproximada; **SUPER + Ctrl + P** busca en su contenido. Aprender > Comandos Cmux, Comandos Tmux y Comandos LazyVim son referencias consultables: seleccionar un comando lo copia, no lo ejecuta.

Kitty muestra una estela corta en saltos de al menos dos celdas, como Enter, Home/End o movimientos entre palabras. Empieza tras 3 ms en reposo y desaparece en 0,05–0,15 segundos. Ajusta `cursor_trail`, `cursor_trail_decay` o `cursor_trail_start_threshold` en `~/.config/kitty/local.conf`; `cursor_trail 0` la desactiva. Tus opciones prevalecen sobre las del paquete y sobreviven a los cambios de tema.

### Fuego del cursor

**Estilo > Terminal > Fuego del cursor** ofrece **Desactivado** (predeterminado) y **Activado**. Activado usa el efecto `cursor-trail-blaze` integrado de Kitty al mover el cursor, sin detectar velocidad de escritura. Desactivado recupera la estela rápida normal y tu elección personal de shader.

Requiere Kitty 0.49+ y `shader-slang`, incluidos en las dependencias de Eitr. Activarlo valida el shader antes de guardar o recargar Kitty. La preferencia local está en `~/.config/eitr/terminal.json`; el auxiliar escribe `kitty/cursor-fire.conf`, incluido al final por el cargador del usuario. Activado, selecciona el shader de fuego y baja el umbral a una celda. Fuentes, temas y archivos personales quedan intactos.

## El comando eitr

`eitr` reúne las herramientas de Eitr; ejecútalo sin argumentos para ver la lista. Usa los mismos scripts que los menús para mantener el mismo comportamiento.

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Norse" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
```

`eitr config` y `eitr git` pasan sus argumentos a `eitr-config` y `eitr-git`. Cada comando tiene `--help`.

## Tus propios hooks

Un hook es un pequeño script tuyo que Eitr ejecuta en un momento concreto para ampliar su comportamiento sin modificarlo. Coloca un ejecutable con el nombre de ese momento en `~/.config/eitr/hooks/`:

| Archivo | Cuándo se ejecuta | Argumento recibido |
| --- | --- | --- |
| `post-update` | después de Actualización del sistema o una actualización pacman/AUR | `system`, `pacman`, `yay` o `full` |
| `theme-set` | después de cambiar de tema | nombre de la carpeta del tema |
| `battery-low` | una vez cada vez que la batería baja al 15% | porcentaje |
| `post-boot` | en la primera sesión después de cada arranque | ninguno |

Para cambiar los colores de Spotify con Spicetify al cambiar de tema, crea `~/.config/eitr/hooks/theme-set`:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

Hazlo ejecutable con `chmod +x ~/.config/eitr/hooks/theme-set`. Cada hook dispone de 60 segundos; su salida y los fallos van a `~/.local/state/eitr/hooks.log`. Un fallo nunca detiene la actualización ni el cambio de tema. `eitr hook list` enumera los hooks; `eitr hook run theme-set norse` prueba uno. Las actualizaciones nunca modifican esta carpeta.

## cmux TUI

Ejecuta `cmux` en Kitty o `cmux --session work` para nombrar la sesión. cmux TUI es opcional junto a tmux; no sustituye Kitty ni sus atajos. Las instalaciones nuevas incluyen un binario oficial con versión fijada en `/usr/bin/cmux`; instalaciones previas por usuario pueden tener prioridad en PATH. Compruébalo con `command -v cmux`. Se incluye `less` para leer salidas y archivos de texto.

El prefijo predeterminado es **Ctrl-b**: suéltalo y pulsa la siguiente tecla.

| Atajo | Acción |
| --- | --- |
| Ctrl-b ? | Mostrar atajos actuales |
| Ctrl-b W | Crear espacio de trabajo |
| Ctrl-b c | Crear pantalla |
| Ctrl-b % / Ctrl-b " | Dividir a la derecha / abajo |
| Ctrl-b t | Nueva pestaña de terminal |
| Ctrl-b h/j/k/l | Enfocar izquierda/abajo/arriba/derecha |
| Ctrl-b s | Mostrar/ocultar barra lateral |
| Ctrl-b d | Salir localmente o desconectar de un servidor |

Para que una sesión continúe sin interfaz, ejecuta `cmux --headless --session work` y después `cmux attach --session work` para conectarte. Las pestañas de navegador requieren Chrome/Chromium. Cerrar pestañas, paneles o espacios puede afectar a tareas en curso; compruébalo antes. Aprender > Comandos Cmux incluye sesiones, navegación, ratón y atajos de cierre. Los valores predeterminados pueden cambiar o personalizarse: **Ctrl-b ?** es la referencia actual.

## Terminales de tareas

Los terminales abiertos por menús y notificaciones de actualización o informes flotan centrados sobre tus ventanas, con fondo sólido del tema. Las sesiones de asistentes de IA y proyectos LazyVim de Desarrollo se abren como ventanas normales en mosaico, con fondo translúcido, igual que tus terminales. Los terminales normales son interactivos y no llevan marca. Instalación, actualización y configuración muestran el banner rúnico de EITR; las tareas correctas suelen cerrarse y los fallos permanecen visibles hasta cerrarlos. Los informes informativos pueden quedar abiertos. Reiniciar Elephant no debe cerrar aplicaciones lanzadas: su servicio systemd termina solo el proceso, no todo el cgroup.

Pulsa **Esc** para cerrar los terminales de tareas, cuentas, informes y Acerca de que esperan una tecla. Enter sigue sirviendo para respuestas y confirmaciones, como confirmar que has anotado la clave de recuperación y apagar el instalador.

## Historial del shell

`history` lista comandos recientes. En zsh, comprueba la ruta real con:

```sh
printf '%s\n' "$HISTFILE"
```

Para abrirlo en Neovim:

```sh
nvim "$HISTFILE"
```

El historial puede contener tokens o credenciales: no lo copies en un informe de errores. Cierra otros shells antes de editarlo a mano, pues pueden volver a guardar su historial en memoria. El historial extendido de zsh puede incluir fechas y comandos de varias líneas: elimina la entrada completa, no un fragmento cualquiera. Guarda una copia privada si necesitas deshacerlo.

## Apariencia de los editores

Cambiar de tema actualiza las preferencias generadas de VS Code y LazyVim. Las sesiones LazyVim compatibles se actualizan sin reabrirlas. Tus ajustes o plugins pueden elegir colores propios; compruébalos si el editor no sigue al escritorio. La fuente predeterminada se integra solo donde la aplicación lo admite.
