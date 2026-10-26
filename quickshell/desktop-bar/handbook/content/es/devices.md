# Dispositivos y entrada

Estos controles están en **Sistema > Dispositivos y entrada** o en los iconos correspondientes de la barra. El Centro de control también ofrece sus interruptores y deslizadores habituales.

## Audio y micrófono

Volumen selecciona la salida predeterminada y controla el volumen general y el de las aplicaciones en reproducción. Los dispositivos aparecen con un nombre legible y un icono de tipo; haz clic en el dispositivo actual para elegir otro y usa el botón de lápiz de un dispositivo para renombrarlo en este equipo. Micrófono selecciona la entrada predeterminada, la ganancia y el silencio. Su medidor de nivel solo funciona mientras el panel está abierto; no guarda audio en disco. Abrir otros ajustes no inicia la monitorización del micrófono.

Los deslizadores llegan al 100 %; un valor superior ya existente no cambia hasta moverlos. Cambiar el dispositivo de audio predeterminado puede afectar a una llamada: hazlo conscientemente. Los controles de reproducción son independientes de la selección del dispositivo.

## Pantalla y brillo

El panel Pantalla muestra los monitores activos. Pulsa uno para abrir los ajustes dentro de su tarjeta y vuelve a pulsarlo para cerrarlos. El monitor **Principal** contiene la barra, los paneles y las notificaciones: activa **Pantalla principal** en los ajustes de otro monitor para trasladarlos. Si se desconecta, otro aparece como **Principal** y recibe la barra hasta su regreso; se conserva tu elección.

Los ajustes incluyen resolución, frecuencia de actualización, escala y, con varios monitores, posición respecto a otro o duplicación. El principal permanece en su sitio y los demás se colocan a su alrededor; su fila Posición solo indica esto. Un monitor puede colocarse junto a cualquiera salvo uno que ya esté posicionado respecto a él.

Cada ajuste ocupa una fila con su valor actual; pulsa para ver las opciones. Posición, alineación, escala, duplicación y pantalla principal se aplican y guardan inmediatamente. Una nueva **resolución o frecuencia de actualización** puede dejar la pantalla negra; en esos casos, el panel pregunta **¿Conservar estos ajustes?** en su borde inferior. Sin pulsar **Mantener** en 15 segundos, revierte automáticamente, incluso con el panel cerrado. Se guarda la configuración de este equipo en `~/.config/hypr/displays.json`.

Puedes organizar cualquier número de monitores: coloca cada uno a izquierda, derecha, arriba o abajo de otro y alinéalo por arriba, centro o abajo (izquierda, centro o derecha si están apilados). La disposición se recuerda: al cambiar la resolución o escala de uno, sus vecinos se desplazan con él. Una opción que solaparía monitores se rechaza con un mensaje. Cada monitor conectado recibe una posición exacta, por lo que cambiar uno no hace que Hyprland mueva los demás.

**Editar la disposición a mano** abre `~/.config/hypr/local.lua` para lo que el panel no cubre, como pantallas giradas o espacios de trabajo fijados a un monitor. Un archivo nuevo contiene ejemplos comentados de tres monitores, orientación vertical, apilado, duplicación y portátil conectado a una base. Nada cambia hasta descomentar un ejemplo y ejecutar `hyprctl reload`. Los monitores definidos allí tienen prioridad; elimina esas definiciones para volver a gestionarlos aquí.

El brillo prefiere un control nativo de retroiluminación utilizable; en su defecto, intenta controlar un monitor externo mediante DDC. Su disponibilidad depende del monitor y los permisos. La Luz nocturna tiene un interruptor manual y un horario opcional editable.

**HDR** solo aparece en monitores cuyo EDID indica compatibilidad con PQ o HLG. Muestra el escritorio en HDR; los juegos pueden usar HDR aunque esté desactivado. Al activar o desactivar HDR también debes conservar el cambio en 15 segundos; de lo contrario, se revierte. Con HDR activo, **Brillo del contenido SDR** ajusta el contenido SDR de 1,0× a 2,0× y guarda inmediatamente. Los juegos HDR a pantalla completa pueden cambiar el monitor automáticamente aunque el HDR del escritorio esté desactivado.

## Teclado

Añade y quita distribuciones en Walker: Sistema > Dispositivos y entrada > Teclado. Añadir distribución lista todos los idiomas y variantes (escribe para buscar); selecciona una distribución y pulsa Supr para quitarla. Se admiten hasta cuatro, sin duplicados, y debe quedar al menos una. **Alt + Shift** las recorre. Con dos o más, la barra muestra el código de la activa (como US o BR); haz clic en él, o usa el Centro de control, para cambiarla. La distribución del teclado es independiente del idioma y la configuración regional del sistema.

El escritorio comienza con el teclado elegido en el instalador. Elegir US incluye US y US International: basta Alt + Shift para acceder a los acentos.

### Navegación opcional con Caps Lock

La configuración opcional de keyd en `distro/keyd/navigation.conf.example` hace que una pulsación breve de Caps Lock envíe Escape. Mantén Caps Lock y pulsa H/J/K/L para izquierda/abajo/arriba/derecha. Las otras teclas conservan su comportamiento.

Para restaurar esta preferencia tras reinstalar, instala el ejemplo como `/etc/keyd/navigation.conf` y activa `keyd.service`. Se aplica a todos los teclados, incluso fuera de Hyprland, y no está activado por defecto. Para deshacerlo, elimina la configuración y recarga keyd; desactiva el servicio si ningún otro mapeo lo usa. La elección de idioma y distribución sigue siendo independiente.

## Energía y batería del portátil

Los controles de batería y perfil de energía solo aparecen cuando existe una batería del sistema, no solo un ratón o auricular inalámbrico. Ahorro/Equilibrado/Rendimiento necesitan power-profiles-daemon; los perfiles sin soporte quedan deshabilitados. Las estimaciones y la salud de batería solo aparecen si el hardware las proporciona.

El Límite de carga requiere una interfaz sysfs de firmware compatible y confirmación escrita. Desactivado permite cargar al 100 %. No todos los portátiles lo admiten.

Una notificación avisa al 10 % y otra, urgente, al 5 %, una vez por descarga. En portátiles, el instalador añade también el firmware de audio necesario en los modelos recientes (`sof-firmware`) y, en modelos Intel, `thermald` para controlar el calor.

Estos recursos son **experimentales** hasta que los primeros usuarios los confirmen en portátiles reales: teclas de retroiluminación del teclado y cierre de tapa con monitor externo conectado. En ese caso, se apaga la pantalla del portátil y el escritorio pasa al monitor externo; abrir la tapa lo devuelve. Sin monitor externo, cerrar la tapa suspende normalmente. La hibernación no se configura automáticamente.
