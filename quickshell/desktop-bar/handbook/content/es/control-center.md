# Centro de control

Pulsa **SUPER + ,** para abrir o cerrar el Centro de control. Se abre desde el borde actual de la barra y se cierra con Escape o un clic fuera. Al cerrarse vuelve a General.

Sus cinco páginas reúnen todo lo que queda fuera de Desarrollo, Aplicaciones, Instalar, Aprender y Juegos; la mayoría de los ajustes no necesitan Walker. Las secciones plegables suelen comenzar cerradas; pulsa el título para abrir o cerrar y la elección se conserva hasta cerrar sesión. Si la barra tiene un panel propio (OBS, WiFi, Bluetooth, Audio, Pantalla, Hardware, Uso de IA o Tiempo), el Centro de control abre ese panel.

## General

- **Conectividad:** interruptores de WiFi y Bluetooth y Modo avión.
- **Controles rápidos:** Bloqueo automático, Notificaciones de fallos, No molestar, Modo juego (desactiva efectos, desenfoque y ventanas emergentes y activa el perfil de rendimiento hasta apagarlo) y Luz nocturna. Un control activado se rellena con el color de acento del tema. Debajo, Ocultar barra (SUPER+Shift+Space la recupera) y Salvapantallas se ejecutan una vez.
- **Sonido:** volumen y ganancia/silencio del micrófono.
- **Pantalla:** brillo, en portátiles con pantalla integrada.
- **Multimedia:** portada, artista, reproducción y desplazamiento por la pista cuando se admite.
- **Energía:** Bloquear y **Energía…**, que despliega Cerrar sesión, Suspender, Reiniciar y Apagar.

El Modo avión recuerda qué conexiones bloqueó y restaura solo esas. No molestar suprime ventanas emergentes sin borrar el historial. Bloqueo automático no equivale a impedir la suspensión; cuida la privacidad de la pantalla.

## Estilo

Estilo organiza los ajustes en Tema y fondo de pantalla (abierto al principio), Esquinas, Barra, Espacios de trabajo, Pantalla de bloqueo, Cursor y Terminal. Haz clic en el título de un grupo para plegarlo; su superficie delimita todas sus opciones. Barra reúne Distribución, Posición, Apariencia, Mostrar en, Reloj, Estilo multimedia y Comportamiento. Comportamiento contiene Ocultar automáticamente, Dock y Reducir movimiento.

Tema y Fondo abren sus carruseles; Fuente predeterminada abre la lista de fuentes. Diseño de bloqueo, cursor (familia, tamaño y color), apariencia, disposición, borde y pantallas de la barra, marcadores de espacios, esquinas y Fuego del cursor de Kitty cambian directamente en el panel y comparten preferencias con Walker.

## Herramientas

Capturas (selección, pantalla completa, ventana o selección directa al portapapeles), grabación (controles de OBS, Grabar, Grabar + Audio y Detener), OCR, códigos QR, selector de colores, Transcodificar, recordatorios y compartir con LocalSend. El panel se cierra antes de empezar una selección o grabación.

## Sistema

- **Dispositivos:** paneles de Audio, Micrófono, Pantalla (resolución, frecuencia y escala), Bluetooth y WiFi, Iluminación y límite de carga en portátiles.
- **Teclado:** seleccionar, añadir y eliminar distribuciones, conservando al menos una.
- **Luz nocturna y pantalla principal:** modo y horario de Luz nocturna, independientes del interruptor manual, y pantalla principal que contiene la barra.
- **Información:** Acerca de, Hardware, Uso de IA, Tiempo e Informar de un problema.
- **Actualizaciones:** canal, Actualización del sistema, cambios de cada actualización y actualizaciones solo de Pacman o AUR.
- **Instantáneas y limpieza:** restaurar archivo, instantáneas personales y de recuperación, su guía, Limpieza y Dotfiles.

Seguridad, restablecimiento de fábrica y servicio de red siguen en Walker > Sistema, con sus propias confirmaciones.

## Idioma

**Sistema > Idioma** muestra el idioma actual según la configuración regional. Abre el selector, elige un idioma o Predeterminado del sistema y cierra e inicia sesión para aplicarlo. Solo cambia el idioma de mensajes de tu sesión, nunca los archivos regionales del sistema. Consulta la [Guía de idioma](handbook:language).

## Chat rápido

El icono de chat junto a las pestañas abre una conversación desechable con el asistente predeterminado elegido en Desarrollo > IA. Se oculta si no hay uno o si la política de la organización desactiva los asistentes. Enter envía; Shift+Enter inserta un salto de línea. Escape o Atrás vuelve a las páginas. Nuevo chat, salir del chat o cerrar el Centro de control borra los mensajes y cancela las respuestas pendientes.

Las respuestas ofrecen Markdown seleccionable y Copiar. La conversación permanece en memoria; Eitr no escribe historial ni registros. Debajo de la entrada se identifica al proveedor en la nube o se indica que Ratatoskr se ejecuta en este PC. Los proveedores reciben los mensajes y los turnos anteriores. Cada mensaje incluye únicamente versión/canal de Eitr, kernel, CPU/GPU/RAM y tema como contexto no confiable. No se recopilan nombres de usuario o equipo, archivos, correos, nombres WiFi, títulos de ventanas ni portapapeles. El asistente usa la ejecución sin interfaz de solo lectura con la cuenta seleccionada y no puede modificar el sistema. Los fallos aparecen en el chat.

## Plugins

**Centro de control > Plugins** muestra una fila compacta por plugin instalado, con icono, nombre e interruptor de activación. Selecciona una fila para ver autor, versión, descripción, acciones de actualización y eliminación, widgets, elementos de la barra y vista previa. Usa Atrás o Escape para volver a la lista. Activar/Desactivar conserva posiciones y detiene o restaura servicios, filas de Walker, hooks y elementos visuales; usa `eitr plugin enable ID` o `eitr plugin disable ID`. Añadir plugin…, Actualizar y Eliminar abren los flujos revisados del terminal; eliminar pide confirmación. General conserva solo los bloques de plugins. Los fallos visuales tienen una acción independiente para reactivar.

Añadir plugin… también acepta repositorios con varios plugins. El índice raíz `eitr-plugins.json` enumera sus IDs y carpetas, cada una con su propio `eitr-plugin.json`. Selecciona uno o más por nombre, descripción e icono y revisa cada plugin por separado. Rechazar uno no aprueba los demás. Los seleccionados comparten una copia del repositorio y quedan fijados individualmente al commit exacto; actualizar uno mantiene los demás en sus commits aprobados. Los detalles muestran la URL del repositorio y la carpeta del plugin. Un único `eitr-plugin.json` en la raíz sigue funcionando como antes.

Actualización del sistema solo comprueba nuevos commits de plugins, incluso cuando los paquetes están al día, e indica la cantidad y dónde actualizar. No revisa ni actualiza plugins; los errores de red se ignoran en silencio. Usa **Actualizar plugins** en **Centro de control > Plugins**, junto a Añadir plugin…, o **Instalar > Plugins > Actualizar plugins**, o ejecuta `eitr plugin update`. La marca ↑ en la fila y «Actualización disponible» en los detalles reflejan la última comprobación del commit aprobado. La acción separada conserva los diffs, avisos de riesgo y confirmaciones por plugin.

La lista de Plugins muestra «Este plugin tiene errores» y el primer mensaje. Seleccione el plugin y elija Ver detalles de errores para saber más; use el interruptor para desactivarlo con un clic. Solo se detectan los errores que indican un archivo de la carpeta del plugin. Los plugins tienen los permisos del escritorio, así que instale solo aquellos en los que confíe.
