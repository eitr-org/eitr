# Centro de control

Ajustes y los paneles de la barra comparten controles de selección. Las opciones cortas usan segmentos; las listas largas se despliegan dentro del panel y permiten desplazarse sin abrir una ventana flotante. Los interruptores conservan sus acciones. Las etiquetas doradas y las letras grabadas pertenecen a la familia de ventanas de Ajustes: Ajustes, el Manual y Temas y plugins.

**SUPER + ,** abre Configuración con **Sistema**, el perfil y el resumen del sistema. Temas y Plugins tienen su propia ventana de catálogo. **SUPER + I** abre el Centro de control.

## Configuración

Los grupos son Resumen, Dispositivos, Escritorio, Aplicaciones y teclas, Cuentas y seguridad y Sistema. Los títulos con runas y el indicador dorado deslizante facilitan la navegación. Cada página tiene título, descripción y tarjetas de ajustes. La ventana sigue siendo opaca. El Manual y Temas y plugins usan el mismo marco, barra lateral, encabezado de página y tarjetas, y siguen la misma elección de colores.

Conexiones tiene pestañas **Wi-Fi** (con la elección del backend) y **Bluetooth**. Pantallas separa **Pantallas** y **Luz nocturna**. Apariencia separa **Tema y fondo de pantalla**, **Fuentes y cursor** y **Terminal**. Izquierda/Derecha cambia la pestaña enfocada; la búsqueda abre la pestaña correspondiente. `settings show connections/bluetooth` abre Bluetooth; `network` sigue siendo un alias. Las tarjetas muestran diseños de barra, bordes, superficies, visualizadores, espacios, esquinas y pantallas de bloqueo. **Colores de Ajustes** permite elegir **Colores del tema** o **Sitio web de Eitr** para Ajustes, el Manual y Temas y plugins. La preferencia local se guarda en `eitr/settings-app.json`; también se cambia con `settings palette theme` o `settings palette website`, sin cambiar los colores del escritorio.

Sistema muestra un resumen con tu foto de perfil, uso de CPU/GPU/RAM, pantalla principal, tiempo de actividad, versión de Eitr, canal de actualización y paleta del tema. El hardware solo se actualiza mientras esta página está visible. La imagen grande muestra por ahora el fondo de pantalla. El servicio de datos compartido no ofrece velocidades de transferencia de red.

**SUPER + F2**, **Más temas** en Apariencia y el **+** del carrusel abren el catálogo independiente con barra lateral **Temas y plugins** y botón de cierre. Configuración sigue abierta al pulsar fuera; Escape o Cerrar la cierran. **SUPER + I** abre el Centro de control.

Pulsa **SUPER + I** para abrir o cerrar el Centro de control. Se abre desde el borde actual de la barra y se cierra con Escape o un clic fuera. Al cerrarse vuelve a General. Con la barra en modo Full a la izquierda o a la derecha, el Centro empieza en la parte superior de la pantalla, con espacio interior para el contenido dentro de la superficie unida a la barra.

Sus páginas son General, Plugins y Herramientas. El botón con engranaje debajo, **Todos los ajustes**, cierra el Centro de control y abre Ajustes, que reúne apariencia, barra, dispositivos, teclado, pantallas y sistema. Las secciones plegables suelen comenzar cerradas; pulsa el título para abrir o cerrar y la elección se conserva hasta cerrar sesión. Si la barra tiene un panel propio, como OBS, WiFi o Bluetooth, el Centro de control lo abre.

## General

- **Conectividad:** interruptores de WiFi y Bluetooth y Modo avión.
- **Acciones rápidas:** Bloqueo automático, Notificaciones de fallos, No molestar, Modo juego (desactiva efectos, desenfoque y ventanas emergentes y activa el perfil de rendimiento hasta apagarlo) y Luz nocturna. Un control activado se rellena con el color de acento del tema. Debajo, Ocultar barra (SUPER+Shift+Space la recupera) y Salvapantallas se ejecutan una vez.
- **Sonido:** volumen y ganancia/silencio del micrófono, y dos interruptores opcionales, desactivados por defecto: **Sonidos de notificación** (un aviso, otro distinto para las urgentes; las de baja prioridad no suenan) y, en equipos con batería, **Sonidos del cargador** al conectarlo o desconectarlo. Ninguno suena en No molestar ni en Modo juego.
- **Pantalla:** brillo, en portátiles con pantalla integrada.
- **Multimedia:** portada, artista, reproducción y desplazamiento por la pista cuando se admite.
- **Energía:** Bloquear y **Energía…**, que despliega Cerrar sesión, Suspender, Reiniciar y Apagar.

El Modo avión recuerda qué conexiones bloqueó y restaura solo esas. No molestar suprime ventanas emergentes sin borrar el historial. Bloqueo automático no equivale a impedir la suspensión; cuida la privacidad de la pantalla.

## Herramientas

Capturas (selección, pantalla completa, ventana o selección directa al portapapeles), grabación (controles de OBS, Grabar, Grabar + Audio y Detener), OCR, códigos QR, selector de colores, Transcodificar, recordatorios y compartir con LocalSend. El panel se cierra antes de empezar una selección o grabación.

## Chat rápido

El icono de chat junto a las pestañas abre una conversación desechable con el asistente predeterminado elegido en Desarrollo > IA. Se oculta si no hay uno o si la política de la organización desactiva los asistentes. Enter envía; Shift+Enter inserta un salto de línea. Escape o Atrás vuelve a las páginas. Nuevo chat, salir del chat o cerrar el Centro de control borra los mensajes y cancela las respuestas pendientes.

Las respuestas ofrecen Markdown seleccionable y Copiar. La conversación permanece en memoria; Eitr no escribe historial ni registros. Debajo de la entrada se identifica al proveedor en la nube o se indica que Ratatoskr se ejecuta en este PC. Los proveedores reciben los mensajes y los turnos anteriores. Cada mensaje incluye únicamente versión/canal de Eitr, kernel, CPU/GPU/RAM y tema como contexto no confiable. No se recopilan nombres de usuario o equipo, archivos, correos, nombres WiFi, títulos de ventanas ni portapapeles. El asistente usa la ejecución sin interfaz de solo lectura con la cuenta seleccionada y no puede modificar el sistema. Los fallos aparecen en el chat.

## Plugins

**Configuración > Estilo > Temas y plugins** en Walker, **Más temas** en la página Apariencia de Ajustes o **SUPER + F2** abre la ventana Temas y plugins. El grupo Plugins muestra los plugins instalados, oficiales y de la comunidad, los instala y actualiza tras una revisión en la ventana, busca actualizaciones y elimina plugins instalados tras confirmar. Los flujos de terminal siguientes siguen disponibles.

**Centro de control > Plugins** muestra una fila compacta por plugin instalado, con icono, nombre e interruptor de activación. Selecciona una fila para ver autor, versión, descripción, acciones de actualización y eliminación, widgets, elementos de la barra y vista previa. Usa Atrás o Escape para volver a la lista. Activar/Desactivar conserva posiciones y detiene o restaura servicios, filas de Walker, hooks y elementos visuales; usa `eitr plugin enable ID` o `eitr plugin disable ID`. Añadir plugins, Actualizar y Eliminar abren los flujos revisados del terminal; eliminar pide confirmación. General conserva solo los bloques de plugins. Los fallos visuales tienen una acción independiente para reactivar.

Añadir plugins también acepta repositorios con varios plugins. El índice raíz `eitr-plugins.json` enumera sus IDs y carpetas, cada una con su propio `eitr-plugin.json`. Selecciona uno o más por nombre, descripción e icono y revisa cada plugin por separado. Rechazar uno no aprueba los demás. Los seleccionados comparten una copia del repositorio y quedan fijados individualmente al commit exacto; actualizar uno mantiene los demás en sus commits aprobados. Los detalles muestran la URL del repositorio y la carpeta del plugin. Un único `eitr-plugin.json` en la raíz sigue funcionando como antes.

Actualización del sistema solo comprueba nuevos commits de plugins, incluso cuando los paquetes están al día, e indica la cantidad y dónde actualizar. No revisa ni actualiza plugins; los errores de red se ignoran en silencio. Usa **Actualizar plugins** en **Centro de control > Plugins**, junto a Añadir plugins, o **Plugins > Actualizar plugins**, o ejecuta `eitr plugin update`. La marca ↑ en la fila y «Actualización disponible» en los detalles reflejan la última comprobación del commit aprobado. La acción separada conserva los diffs, avisos de riesgo y confirmaciones por plugin.

La lista de Plugins muestra «Este plugin tiene errores» y el primer mensaje. Seleccione el plugin y elija Ver detalles de errores para saber más; use el interruptor para desactivarlo con un clic. Solo se detectan los errores que indican un archivo de la carpeta del plugin. Los plugins tienen los permisos del escritorio, así que instale solo aquellos en los que confíe.

## Fotos de perfil

Pulsa el avatar redondo en la parte superior de la navegación del Centro de control, o abre Ajustes > Seguridad > Usuarios > Foto de perfil. Elegir imagen… muestra tu carpeta Imágenes dentro del panel: pulsa una carpeta para abrirla, ‹ o Retroceso para subir de nivel, y pulsa una imagen para elegirla. Después, arrastra la vista circular para mover la imagen; usa la rueda, el deslizador o +/− para ampliar de 1× a 4×, y las flechas para moverla. Guardar o Intro aplica el recorte; Cancelar o Escape cierra sin aplicar cambios. Eliminar borra la foto.

La foto siempre aparece como un círculo en el Centro de control, el bloqueo y el inicio de sesión. Sin foto, el Centro de control muestra la inicial del nombre sobre el color de acento, y el bloqueo y el inicio de sesión no muestran ninguna imagen. Se aceptan PNG, JPEG, WebP, GIF (primer fotograma) y BMP hasta 40 MB y 12000 píxeles por lado. Eitr aplica la orientación, elimina metadatos, guarda un PNG de 512×512 en `~/.face` y actualiza AccountsService para SDDM. Si falla la actualización, la foto guardada sigue funcionando en el bloqueo; la interfaz o CLI muestra el error del inicio de sesión.

## Más páginas de Configuración

Atajos muestra la referencia completa de Aprender con búsqueda. Aplicaciones predeterminadas permite elegir programas instalados para navegador, archivos, texto, imágenes, vídeo, música, correo y PDF; Terminal usa la preferencia de Apariencia > Terminal. Usuario muestra el nombre y el editor compartido de la foto de perfil. Git y nube muestra identidades, reglas de carpetas y contextos; sus botones abren los flujos existentes de Walker. Seguridad conserva las confirmaciones de cambios privilegiados. Actualizaciones muestra el canal y los paquetes pendientes; Actualizar sistema abre el flujo existente. Comprobar este PC ejecuta diagnósticos de solo lectura únicamente al pulsar el botón. Acerca de muestra versión, núcleo, hardware, licencia y enlaces. Todas las páginas permiten desplazarse hasta la última fila y enlazan al Manual.
