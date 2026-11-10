# Centro de control

Pulsa **SUPER + I** para abrir o cerrar el Centro de control. Se abre desde el borde actual de la barra y se cierra con Escape o un clic fuera. Al cerrarse vuelve a General. Con la barra en modo Full a la izquierda o a la derecha, el Centro empieza en la parte superior de la pantalla, con espacio interior para el contenido dentro de la superficie unida a la barra.

Sus páginas son General, Plugins y Herramientas. El botón con engranaje debajo, **Todos los ajustes**, cierra el Centro de control y abre Ajustes, que reúne apariencia, barra, dispositivos, teclado, pantallas y sistema. Las secciones plegables suelen comenzar cerradas; pulsa el título para abrir o cerrar y la elección se conserva hasta cerrar sesión. Si la barra tiene un panel propio, como OBS, WiFi o Bluetooth, el Centro de control lo abre.

## General

<!-- eitr-figure: control-center -->

La página General. Los botones de la izquierda cambian entre General, Plugins y Herramientas; el engranaje de debajo abre Configuración. Un control activado se rellena con el color de acento del tema.

- **Conectividad:** interruptores de WiFi y Bluetooth y Modo avión.
- **Acciones rápidas:** Bloqueo automático, Notificaciones de fallos, No molestar, Modo juego (desactiva efectos, desenfoque y ventanas emergentes y activa el perfil de rendimiento hasta apagarlo) y Luz nocturna. Debajo, Ocultar barra (SUPER+Shift+Space la recupera) y Salvapantallas se ejecutan una vez.
- **Sonido:** volumen y ganancia/silencio del micrófono, y dos interruptores opcionales, desactivados por defecto: **Sonidos de notificación** (un aviso, otro distinto para las urgentes; las de baja prioridad no suenan) y, en equipos con batería, **Sonidos del cargador** al conectarlo o desconectarlo. Ninguno suena en No molestar ni en Modo juego. Walker > Configuración > Dispositivos > Sonidos de eventos ofrece los mismos interruptores.
- **Pantalla:** brillo, en portátiles con pantalla integrada.
- **Multimedia:** portada, artista, reproducción y desplazamiento por la pista cuando se admite.
- **Energía:** Bloquear y **Energía…**, que despliega Cerrar sesión, Suspender, Reiniciar y Apagar.

El Modo avión recuerda qué conexiones bloqueó y restaura solo esas. No molestar suprime ventanas emergentes sin borrar el historial. Bloqueo automático no equivale a impedir la suspensión; cuida la privacidad de la pantalla.

## Herramientas

Capturas (selección, pantalla completa, ventana o selección directa al portapapeles), grabación (controles de OBS, Grabar, Grabar + Audio y Detener), OCR, códigos QR, selector de colores, Transcodificar, recordatorios y compartir con LocalSend. El panel se cierra antes de empezar una selección o grabación.

## Chat rápido

Elige el predeterminado en Configuración > Asistente de IA.

El icono de chat junto a las pestañas abre una conversación desechable con el asistente predeterminado elegido en Desarrollo > IA. Se oculta si no hay uno o si la política de la organización desactiva los asistentes. Enter envía; Shift+Enter inserta un salto de línea. Escape o Atrás vuelve a las páginas. Nuevo chat, salir del chat o cerrar el Centro de control borra los mensajes y cancela las respuestas pendientes.

Las respuestas ofrecen Markdown seleccionable y Copiar. La conversación permanece en memoria; Eitr no escribe historial ni registros. Debajo de la entrada se identifica al proveedor en la nube o se indica que Ratatoskr se ejecuta en este PC. Los proveedores reciben los mensajes y los turnos anteriores. El resumen del equipo incluye versión/canal de Eitr, kernel, CPU/GPU/RAM y tema como contexto no confiable.

No se recopilan nombres de usuario o equipo, archivos, correos, nombres WiFi, títulos de ventanas ni portapapeles. El asistente usa la ejecución sin interfaz de solo lectura con la cuenta seleccionada y no puede modificar el sistema. Los fallos aparecen en el chat.

El asistente también recibe la introducción del Manual y fragmentos traducidos pertinentes, una lista fija de herramientas instaladas y si hay un monitor HDR conectado. Esto indica disponibilidad, no si un servicio está configurado. El asistente no puede ejecutar comandos ni cambiar ajustes.

## Plugins

**Centro de control > Plugins** muestra una fila compacta por plugin instalado, con icono, nombre e interruptor de activación. Selecciona una fila para ver autor, versión, descripción, acciones de actualización y eliminación, widgets, elementos de la barra y vista previa. Usa Atrás o Escape para volver a la lista. Activar/Desactivar conserva posiciones y detiene o restaura servicios, filas de Walker, hooks y elementos visuales; usa `eitr plugin enable ID` o `eitr plugin disable ID`.

Añadir plugins, Actualizar y Eliminar abren los flujos revisados del terminal; eliminar pide confirmación. General conserva solo los bloques de plugins. Los fallos visuales tienen una acción independiente para reactivar.

Para instalación, revisión y actualizaciones seguras, consulta [Apps e instalación](handbook:apps).

Para Configuración (**SUPER + ,**) y las fotos de perfil, consulta [Configuración](handbook:system).
