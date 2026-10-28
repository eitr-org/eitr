# Barra y espacios de trabajo

La barra mantiene fecha y hora centradas. A la izquierda está primero el logotipo de Eitr, que abre el Centro de control, seguido de Vista general, marcadores de espacios de trabajo, Uso de IA, Hardware y Bloqueo automático; a la derecha, controles de dispositivos y estado. Pulsa **Mostrar iconos** para mostrar u ocultar ese grupo derecho.

## Actualizaciones

El icono de actualizaciones está en el grupo derecho, antes de Notificaciones, y consulta paquetes y AUR poco después de iniciar sesión y cada seis horas. Si hay actualizaciones, una notificación ofrece ejecutar la Actualización del sistema. Gira mientras consulta y luego muestra una marca si todo está actualizado, o un icono cuya descripción indica la cantidad de actualizaciones y el tamaño de descarga. Pulsa para actualizar el sistema; pulsa con el botón derecho para consultar otra vez. Vuelve a consultar automáticamente al finalizar la actualización. Sin conexión, indica sistema actualizado y vuelve a consultar en el siguiente inicio de sesión. Usa una copia privada de las bases de datos de paquetes para no dejar nunca el sistema parcialmente actualizado.

## Posición y apariencia

- Haz doble clic izquierdo en el **espacio vacío de la barra** para alternar Desenfoque/Color del tema; las instalaciones nuevas comienzan con Color del tema.
- Haz doble clic derecho en el espacio vacío para recorrer Completa → Centrada → Muesca → Completa.
- Arrastra el espacio vacío hacia arriba, abajo, izquierda o derecha para mover la barra.
- Las mismas opciones están en **Estilo > Barra del escritorio** y Centro de control > Estilo.
- **Pantallas** (Mostrar en) coloca la barra solo en la principal, por defecto, o en todas. En todas, cada barra marca el espacio de trabajo de su pantalla; atajos como SUPER + , se abren en la pantalla en uso y las notificaciones aparecen solo en la principal. Elige la principal en el panel Pantalla.

El modo centrado muestra el reloj hasta pasar el puntero. Los iconos se despliegan en su orden habitual. La chincheta entre medios y reloj mantiene la barra abierta; los paneles abiertos también. En modo completo los paneles se unen a la barra; en modo centrado se sitúan junto a ella. Ambos abren y cierran con la misma animación fluida. Cada lado se ajusta a su contenido y el reloj permanece en el centro de la pantalla en los cuatro bordes.

Pestañas muestra una franja continua de 7 px y tres pestañas ajustadas al contenido de los grupos izquierdo, central y derecho. Conservan la profundidad completa (30 px en horizontal), uniones trapezoidales fijas con pendientes rectas de 45° fuera del relleno de las pestañas. El reloj permanece centrado en la pantalla incluso con multimedia. Los paneles flotan junto a la barra en superficies redondeadas separadas, alineadas a la izquierda, al centro o a la derecha como en Completa y separadas del borde de la pantalla por el margen exterior, con la separación entre ventanas actual de Hyprland y la misma animación de 320 ms del modo Centrado. Los huecos dejan pasar los clics; las ventanas respetan toda la profundidad de las pestañas. Doble clic derecho alterna Completa → Centrada → Pestañas → Completa. Los cambios de dirección se suavizan ligeramente y no siguen la preferencia de esquinas; los extremos de la pantalla permanecen cuadrados y rellenos. Pestañas siempre muestra todos los controles derechos sin flecha para ocultarlos. El tiempo permanece oculto hasta pasar el puntero sobre la pestaña central y se desliza tras el reloj fijo en 320 ms. Se retrae tras una breve demora al salir y permanece visible mientras su panel está abierto. Solo crece el lado posterior a lo largo del eje de la barra, con 4 px tras el último elemento visible.

## Espacios de trabajo

La barra empieza en 1–5 y crece hasta el espacio actual o el mayor ocupado, con un máximo de 10. Los marcadores superiores vacíos desaparecen cuando dejan de necesitarse. Pulsa un marcador con el botón derecho para elegir Puntos, Glifo, Números o Runas, con ejemplos en vivo. Runas es el valor predeterminado y representa los espacios 1 a 10 con las diez primeras runas del Futhark antiguo (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ). El marcador activo muestra el símbolo en el color de acento, sin fondo relleno.

**SUPER + 1–9/0** cambia de espacio; **SUPER + Shift + 1–9/0** mueve una ventana. **SUPER + Tab** abre Vista general. Pulsa una vista previa o usa flechas y Enter; 1–9/0 cambia directamente. Solo aparecen espacios numerados ocupados y sus vistas previas quedan en memoria. Escape o un clic fuera cierra Vista general.

**SUPER + S** alterna el espacio especial, independiente de Vista general. **SUPER + Shift + Space** oculta/muestra la barra, sin detener el servicio de notificaciones.

Los gestos de ratón para fondo y tema en el escritorio vacío están en **Aprender > Gestos del ratón**. Si tienes dudas, usa los atajos de teclado de los carruseles.

El control Audio/Mic abre un panel con secciones separadas para la salida de audio y el micrófono. Tailscale y Streaming están justo antes de OBS. Un interruptor en su cabecera conecta Tailscale o inicia el uso compartido, debajo siguen detalles y dispositivos, y las acciones de configuración o diagnóstico están en el menú «…». El fondo de los botones de icono aparece al pasar el puntero; los paneles se actualizan solos al abrirse, un icono de actualización gira solo mientras cargan y las ayudas aparecen cerca del puntero. Los interruptores y los botones de acción internos tienen tamaños compactos comunes.

**Visualizador de música** en **Principal > Herramientas** abre cava con los colores del tema. Haz clic derecho en el ecualizador multimedia para abrirlo; el clic izquierdo sigue abriendo los detalles multimedia. Pulsa **q** o **Esc** para cerrarlo. Si falta cava, se instala primero.

**Ocultar automáticamente**, en Estilo > Barra del escritorio y Centro de control > Estilo, retrae la barra tras un breve retraso cuando sales de ella con el puntero. Lleva el puntero al borde de la pantalla para mostrarla. Funciona en los cuatro bordes con los modos Completa, Centrada y Pestañas. Los paneles y menús abiertos, así como arrastrar la barra, la mantienen visible; después vuelve a ocultarse. Mientras está activado, la barra no reserva espacio para las ventanas: se desliza sobre ellas en vez de moverlas. La preferencia se guarda por separado del anclaje del modo centrado y viene desactivada en instalaciones nuevas.

**Reducir movimiento**, en Estilo > Barra del escritorio y Centro de control > Estilo > Barra, hace instantáneas la apertura y el cierre de paneles, las entradas de Vista general, las transiciones de notificaciones y las animaciones decorativas de la barra. Está desactivado por defecto y se guarda en `bar-settings.json`. Los temporizadores de actualización de datos, caducidad de notificaciones y ocultación automática mantienen su funcionamiento normal.

El estilo multimedia se guarda en `bar-settings.json`: elige Barras (predeterminado, ocho barras) o Línea (una onda de audio suave y sencilla) en Estilo > Barra del escritorio o Centro de control > Estilo > Barra. El indicador precede a los controles, mantiene un tamaño fijo en todos los diseños y gira en los bordes izquierdo y derecho. Al pasar el puntero muestra la canción; el clic izquierdo abre los detalles y el derecho abre el visualizador de música. En pausa, la línea queda plana. Reducir movimiento mantiene los niveles de audio sin transiciones y detiene el movimiento decorativo de respaldo.
