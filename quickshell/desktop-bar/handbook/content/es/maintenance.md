# Actualizaciones, limpieza y recuperación

Abre **Sistema > Mantenimiento**. Revisa la salida del terminal y conserva copias de seguridad independientes antes de cambiar el sistema. Las instantáneas no son copias de seguridad en otro disco.

## Actualización

**Actualización > Actualización del sistema** es el proceso normal de actualización completa de paquetes. En una instalación nueva configurada de EITR, comprueba la compatibilidad con instantáneas y crea instantáneas anteriores y posteriores con archivos de arranque. Si falla la protección, la actualización no comienza. Un escritorio Arch existente sin la política de la distribución no necesita esta configuración solo para actualizar. La actualización del sistema también actualiza aplicaciones Flatpak, como GeForce NOW; los fallos de Flatpak se notifican sin deshacer la actualización del sistema.

Antes de actualizar, la actualización del sistema (y las actualizaciones de Pacman en Avanzado) consulta las noticias de Arch Linux desde la última actualización. Anuncian cambios que requieren pasos manuales. Si hay noticias, muestra títulos y enlaces y pregunta **¿Continuar la actualización? [y/N]**: Enter cancela antes de modificar nada para que puedas leer la publicación. Sin noticias o sin internet, continúa.

**Actualización > Canal de actualización** muestra ambos canales y marca el actual; elegir el otro pide tu contraseña en un terminal y cambia el origen de las actualizaciones del propio Eitr. Stable, el predeterminado, las recibe después de probarlas. Testing recibe compilaciones nuevas en cuanto se publican para probar cambios antes; lo demás sigue viniendo de Arch. Volver a Stable conserva una versión más reciente de Eitr hasta que ese canal la alcance. En el terminal, `eitr channel` muestra el canal; `eitr channel testing` o `eitr channel stable` lo cambia.

Si una actualización impide arrancar, la **protección del arranque** la revierte: tras dos intentos consecutivos que no lleguen a la pantalla de inicio de sesión, el siguiente restaura el sistema y los archivos de arranque anteriores a la actualización y reinicia. Tu carpeta personal no se modifica y la siguiente sesión te informa de lo ocurrido. Funciona en equipos instalados con el instalador de Eitr; consulta [Recuperación e instantáneas](handbook:recovery).

**Instantáneas de la carpeta personal** conservan versiones anteriores de tus archivos: actívalas en **Sistema > Mantenimiento > Instantáneas > Instantáneas de la carpeta personal**. Se crean cada hora durante un día y diariamente durante una semana; las más antiguas se eliminan si falta espacio. Se excluyen cachés, Downloads, discos de máquinas virtuales y juegos. Para recuperar un archivo, elige **Restaurar un archivo o carpeta**, escribe su ruta y elige una fecha. La versión anterior aparece junto a la actual sin sustituirla.

**Actualización > Avanzado** ofrece **Pacman + Yay**, **Pacman** y **Yay (AUR)**. Estas opciones no crean instantáneas automáticas deliberadamente. Los comandos directos de pacman/yay también omiten el proceso protegido. Las instantáneas raíz no cubren Flatpaks, entornos de desarrollo ni datos personales separados.

Evita las actualizaciones parciales de Arch. Lee las preguntas de los paquetes en vez de aceptar una eliminación inesperada sin revisarla. Las tareas correctas se cierran; los fallos quedan visibles para que puedas investigar sin perder su salida.

Tras una actualización correcta, una notificación pide completarla cuando sea necesario: **Reiniciar ahora** después de actualizar kernel, firmware, microcódigo, systemd, glibc, controlador gráfico o cifrado de disco; o **Cerrar sesión ahora** después de actualizar el escritorio, como EITR, Hyprland, Quickshell, Walker o PipeWire. **Más tarde** permite seguir trabajando; las nuevas versiones se usan al reiniciar o volver a iniciar sesión.

## Limpieza e instantáneas

Limpieza ejecuta el mantenimiento y mantiene abierto el informe. Revisa sus propuestas; un paquete huérfano no es necesariamente inútil. Instantáneas ofrece los procesos existentes de estado y configuración de Snapper. Consulta [Recuperación e instantáneas](handbook:recovery) para los esquemas de disco compatibles y los límites de los cargadores de arranque.

## Restablecimiento de fábrica

Solo se puede restablecer una instalación compatible de la distribución con su punto de restauración del primer inicio de sesión. Esa base privada está separada de las listas y la limpieza normales de Snapper. Root puede eliminarla y un fallo del disco puede destruirla. Se requieren dos advertencias separadas y una confirmación escrita. Lee [Restablecimiento de fábrica](handbook:factory-reset) para saber exactamente qué conservan Borrar todo y Mantener mis archivos.

## Energía

Principal > Energía y Centro de control > General permiten bloquear, cerrar sesión, suspender, reiniciar y apagar. Guarda tu trabajo primero. Estas acciones se ejecutan de verdad; no son demostraciones.
