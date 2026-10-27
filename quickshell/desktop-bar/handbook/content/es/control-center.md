# Centro de control

Pulsa **SUPER + ,** para abrir o cerrar el Centro de control. Se abre desde el borde actual de la barra y se cierra con Escape o un clic fuera. Al cerrarse vuelve a General.

Sus cinco páginas reúnen todo lo que queda fuera de Desarrollo, Aplicaciones, Instalar, Aprender y Juegos; la mayoría de los ajustes no necesitan Walker. Las secciones plegables comienzan cerradas; pulsa el título para abrir o cerrar y la elección se conserva hasta cerrar sesión. Si la barra tiene un panel propio (OBS, WiFi, Bluetooth, Audio, Pantalla, Hardware, Uso de IA o Tiempo), el Centro de control abre ese panel.

## General

- **Conectividad:** interruptores de WiFi y Bluetooth y Modo avión.
- **Controles rápidos:** Bloqueo automático, Notificaciones de fallos, No molestar, Modo juego (desactiva efectos, desenfoque y ventanas emergentes y activa el perfil de rendimiento hasta apagarlo) y Luz nocturna. Un control activado se rellena con el color de acento del tema. Debajo, Ocultar barra (SUPER+Shift+Space la recupera) y Salvapantallas se ejecutan una vez.
- **Sonido:** volumen y ganancia/silencio del micrófono.
- **Pantalla:** brillo.
- **Multimedia:** portada, artista, reproducción y desplazamiento por la pista cuando se admite.
- **Energía:** Bloquear y **Energía…**, que despliega Cerrar sesión, Suspender, Reiniciar y Apagar.

El Modo avión recuerda qué conexiones bloqueó y restaura solo esas. No molestar suprime ventanas emergentes sin borrar el historial. Bloqueo automático no equivale a impedir la suspensión; cuida la privacidad de la pantalla.

## Estilo

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

**Centro de control > Plugins** muestra cada plugin instalado con icono, autor, versión, descripción y estado. Expande Vista previa para ver su imagen. Activar/Desactivar conserva posiciones y detiene o restaura servicios, filas de Walker, hooks y elementos visuales; usa `eitr plugin enable ID` o `eitr plugin disable ID`. Añadir plugin…, Actualizar y Eliminar abren los flujos revisados del terminal; eliminar pide confirmación. General conserva solo los bloques de plugins. Los fallos visuales tienen una acción independiente para reactivar.
