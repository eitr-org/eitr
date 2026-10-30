# Solución de problemas

## Comprobar este PC

Abra **Configuración > Sistema > Mantenimiento > Comprobar este PC** o `eitr check`. Las comprobaciones solo leen; no reparan ni reinician nada. No actualizan listas de paquetes. DNS usa la red. `eitr check --json` muestra detalles técnicos sin preguntas.

**Comprobaciones profundas (requiere contraseña)**: Para comprobaciones profundas pulse Enter; Esc las omite. `sudo /usr/lib/eitr/eitr-system selfcheck-deeper` pide su contraseña en el mismo terminal. Los resultados sustituyen las comprobaciones omitidas correspondientes. Lee Snapper, pares pre/post, la última actualización de paquetes correcta, qgroups Btrfs existentes, JSON de protección de arranque, un manifiesto de fábrica ya montado y claves Arch Linux/Eitr con `pacman-key --list-keys`. Nunca activa cuotas ni monta el punto de fábrica. Los datos ausentes se omiten con un motivo; el manifiesto no verifica la integridad del archivo. `fsck.vfat -n` solo comprueba una ESP FAT identificada sin ambigüedad que no esté montada con escritura; de lo contrario pide desmontarla y omite la prueba.

Las unidades fallidas muestran hasta tres nombres y un comando de estado. Las descripciones de snapshots no prueban los pasos posteriores; los hooks no tienen fechas. No hay consulta estructurada de errores de la barra. Después **Enter** copia el informe redactado y **Esc** cierra. Revíselo antes de compartir; copiar requiere `wl-copy`.


## Una acción indica que falta una herramienta

Las instalaciones nuevas incluyen las dependencias del escritorio, pero un Arch existente puede carecer de algunas. Lee el error e instala el paquete correspondiente desde Instalar > Paquetes > Pacman o con una actualización completa normal. No elimines BlueZ/iwd/PipeWire/WirePlumber solo porque los ajustes estén en paneles nativos: estos siguen necesitando esos servicios.

Este manual no necesita `less`: es Markdown incluido en una superposición nativa. Si indica un catálogo ausente o desactualizado, actualiza los archivos del escritorio EITR.

## Falta un auxiliar propiedad de root

Los cambios de servicio de red, la seguridad, los límites de batería y la recuperación requieren auxiliares revisados propiedad de root. Una instalación solo de dotfiles quizá aún no tenga los paquetes necesarios. Consulta el capítulo correspondiente; nunca omitas la comprobación ejecutando como root un auxiliar descargado modificable por el usuario. Abrir el selector no debe desconectar tu red.

## Problemas de configuración o servicios

Quickshell muestra un error de recarga legible y conserva la configuración anterior funcional cuando puede. Corrige el archivo indicado; no reinicies repetidamente el gestor de inicio de sesión. **Nunca reinicies SDDM durante tu sesión de escritorio.**

Reiniciar Elephant recarga los menús. Su servicio debe mantener `KillMode=process` para auxiliares e inicios sin uwsm. En una sesión uwsm, las aplicaciones y terminales lanzados usan ámbitos de aplicación separados. Los temas regeneran estilos: si desaparece un cambio, corrige tanto el generador como la salida.

## Los datos de WiFi dejan de actualizarse

La barra comparte un único proceso de lectura de WiFi entre las pantallas. Si se
cierra, los últimos datos válidos quedan marcados como obsoletos mientras el
proceso intenta reiniciarse con intervalos crecientes. Tras seis intentos fallidos,
espera un reintento explícito. Los controles nativos siguen disponibles; las
acciones de WiFi comparten una cola ordenada y el estado ocupado entre pantallas. Si una acción agota su plazo o el proceso termina, el resultado es desconocido: actualiza el estado antes de reintentar explícitamente. Las escrituras nunca se repiten automáticamente. La generación de QR conserva su auxiliar separado.

Para consultar el estado técnico, usa
`eitr-shell desktop-bar ipc call -- data status`. Informa de la antigüedad de los
datos, códigos de error, lecturas en curso, observadores y reinicios, sin nombres
ni direcciones de red. Reintenta con
`eitr-shell desktop-bar ipc call -- data retry`.

## Comprobaciones de instalación y recuperación

EITR sigue en beta: las pruebas en máquinas virtuales no demuestran que funcionen todos los adaptadores WiFi, agentes Bluetooth, TPM, GPU, lectores de huellas o configuraciones Secure Boot. El código actual de servicios WiFi y autenticación empresarial se prueba con simulaciones; comprueba la autenticación real antes de depender de ella. Cambiar los manifiestos no modifica las ISO existentes: reconstruye el payload y la ISO para incorporar cambios a nuevas instalaciones.

Guarda copias de tus otros discos antes de instalar en un SSD separado y comprueba bien el disco de destino. El instalador borra el disco que confirmes. Conserva contraseñas de cifrado y claves de recuperación sin conexión. Las instantáneas del mismo SSD no son copias independientes. Empieza por [Recuperación e instantáneas](handbook:recovery).

## Informar de un problema

**Configuración > Sistema > Información > Informar de un problema** recoge versiones de EITR y paquetes, hardware gráfico, errores de Hyprland, servicios fallidos, avisos recientes, fallos de la última semana, errores del arranque anterior, registro de instalación y cambios recientes de paquetes en `~/Documents/eitr-problem-report-<time>.txt`, legible solo por ti. Elimina usuario, nombre del equipo, ruta personal, correo, IP y MAC; los registros aún pueden mencionar aplicaciones o archivos. Léelo antes de enviarlo.

Nada se envía automáticamente. El terminal muestra solo dónde se guardó y ofrece enviarlo o leerlo primero:

1. **Enviarlo por correo** a `reports@eitr.info`: abre tu correo con un resumen; adjunta el archivo guardado.
2. **Abrir una incidencia en GitHub** requiere cuenta GitHub y abre una nueva incidencia del proyecto. Las incidencias son públicas.
3. **Copiar el informe** para pegarlo donde quieras.
4. **Leer el informe** lo abre en tu editor.

El informe se usa solo para identificar y corregir el problema y se elimina al resolverlo. Un correo comparte tu dirección; responde cuando quieras para pedir que se elimine tu informe.

### Cuando falla un componente

Las Notificaciones de fallos están activadas de forma predeterminada. Un servicio de usuario observa los nuevos registros legibles de systemd-coredump de tus propios programas. Cada fallo ofrece Informar de un problema, Ignorar y Silenciar este programa; Preguntar a la IA aparece cuando tienes un asistente predeterminado instalado y seleccionado. Los fallos repetidos de un programa generan como máximo una notificación cada cinco minutos. Un fallo que cierra la sesión se ofrece en el siguiente inicio de sesión, pero no los programas que fallan en el minuto posterior a cerrar sesión, reiniciar o apagar: solo están perdiendo el escritorio. Actívalas o desactívalas en Principal > Acciones rápidas o Centro de control > Acciones rápidas. Las preferencias y las rutas silenciadas se guardan en `~/.config/eitr/crash-help.json`; elimina una ruta de `ignored` para volver a recibir avisos.

Preguntar a la IA abre tu asistente predeterminado solo con el programa, la señal y la traza de pila de `coredumpctl info`, pidiendo una explicación y una propuesta de solución sin cambiar el sistema salvo que lo autorices. No se pasa ningún volcado de memoria. Al elegir esta acción, el asistente puede enviar el resumen a su proveedor. Informar de un problema adjunta el mismo resumen al flujo existente: revísalo antes de compartirlo; nada se envía automáticamente.

## Personalizaciones y actualizaciones

El código de EITR está en `/usr/share/eitr` y se actualiza con `eitr-desktop`; tus ajustes quedan en `~/.config`. Coloca los cambios duraderos donde no los modifiquen las actualizaciones:

- Monitores, dispositivos, atajos y reglas adicionales: `~/.config/hypr/local.lua`.
- Complementos del shell: `~/.config/eitr/shell.local.zsh`.
- Opciones del terminal: `~/.config/kitty/local.conf`.
- Colores del lanzador: `~/.config/walker/style.override.css`.
- Sustitución completa de un archivo distribuido: la misma ruta relativa bajo `~/.config/eitr/overrides`. Deja de recibir correcciones de actualizaciones.

Archivos como `kitty/theme.conf` y el estilo de Walker se regeneran al cambiar temas y una vez tras cada actualización del paquete. Las copias anteriores quedan en `~/.local/state/eitr/generated-backups`. Si cambia el formato de un ajuste, se convierte una vez al iniciar sesión; un fallo se informa y se reintenta en la siguiente sesión (`~/.local/state/eitr/migrations.log`). `eitr-config status` muestra los ajustes y sustituciones activos.

Los terminales de tareas fallidas ofrecen **A: preguntar a la IA** si hay un asistente predeterminado; **Esc** cierra. Solo se conservan en memoria las últimas 200 líneas, sin secuencias ANSI y con líneas de secretos evidentes ocultas antes de compartir: un asistente en la nube envía esta salida a su proveedor y Ratatoskr la mantiene en este PC.
