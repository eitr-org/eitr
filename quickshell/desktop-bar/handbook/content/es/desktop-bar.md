# Barra y espacios de trabajo

<!-- eitr-figure: bar-anatomy -->

La barra completa. El logotipo de Eitr abre el Centro de control; le siguen Vista general, los marcadores de espacios de trabajo, Uso de IA, Hardware y Bloqueo automático. La fecha y la hora quedan centradas, con la multimedia delante y el tiempo detrás. **Mostrar iconos** muestra u oculta los iconos de estado de la derecha; las notificaciones van al final.

Islas presenta grupos en superficies separadas: logotipo, Vista general y espacios de trabajo, Uso de IA/Hardware/Bloqueo por inactividad, reloj, tiempo y controles de estado. Los indicadores multimedia y de captura aparecen solo cuando están activos. El reloj permanece exactamente centrado en la pantalla; el tiempo tiene su propia superficie al lado.

Las superficies son siempre totalmente redondeadas, sea cual sea la preferencia de esquinas, y siguen el color/transparencia y el desenfoque. Las superficies quedan a la mitad del espacio exterior actual de Hyprland del borde, con el espacio completo entre superficies vecinas, en los cuatro lados. La reserva para ventanas incluye el grosor y esa mitad; la ocultación automática no reserva espacio.

Los huecos dejan pasar los clics. El espacio vacío de cada superficie admite los gestos habituales de doble clic y arrastre. Abrir un panel hace crecer una tarjeta desde su isla (hacia el lado libre: el tiempo a la derecha, multimedia y captura a la izquierda, el estado hacia el centro, el reloj hacia ambos lados) y aparta las islas vecinas; la isla queda oculta bajo la tarjeta hasta que vuelve a encogerse.

Los iconos de estado conservan el botón manual para mostrar u ocultar.

En Configuración > Ventanas, la disposición y los monitores usan dos botones. El número de espacios y Siempre mostrar usan listas desplegables; Siempre mostrar ofrece de 2 al número actual de espacios. Las descripciones explican el efecto de cada ajuste, incluida la disposición elegida y las opciones de desplazamiento.

## Actualizaciones

El icono de actualizaciones, antes de Notificaciones, comprueba poco después de iniciar sesión y cada seis horas. Púlsalo para actualizar el sistema; el clic derecho vuelve a comprobar. Una actualización correcta lo marca como actualizado hasta la próxima comprobación, sin iniciar otra inmediatamente. Sin conexión o si falla, indica que el estado no está disponible, nunca un falso «actualizado». La comprobación usa una base de paquetes privada y no actualiza paquetes.

## Cambiar la disposición de la barra

- Haz doble clic izquierdo en el **espacio vacío de la barra** para recorrer Color del tema → Desenfoque → Sitio web; las instalaciones nuevas comienzan con Color del tema. Sitio web usa los colores del sitio de Eitr, claros u oscuros según el tema.
- Haz doble clic derecho en el espacio vacío para recorrer Completa → Centrada → Pestañas → Islas → Dinámico → Completa.
- Arrastra el espacio vacío hacia arriba, abajo, izquierda o derecha para mover la barra. A izquierda y derecha la barra es tan estrecha como arriba y abajo: el reloj muestra la hora sobre los minutos con un icono de calendario y el tiempo solo su icono; pasa el puntero para ver la fecha y la temperatura.
- **Reloj** en Configuración > Barra del escritorio muestra la hora en formato de 12 horas con AM/PM (predeterminado) o de 24 horas, en cualquier borde.
- Las mismas opciones están en **Configuración > Barra del escritorio**, en sus pestañas Distribución, Apariencia y Comportamiento.
- **Pantallas** (Mostrar en) coloca la barra solo en la principal, por defecto, o en todas. En todas, cada barra marca el espacio de trabajo de su pantalla; atajos como SUPER + I se abren en la pantalla en uso y las notificaciones aparecen solo en la principal. Elige la principal en el panel Pantalla.

<!-- eitr-figure: bar-layouts -->

Los cinco diseños en el orden en que los recorre el doble clic derecho. En reposo, Centrada muestra solo el reloj y Dinámico tres pequeñas islas; ambos se despliegan al pasar el puntero.

Elige una disposición en Configuración > Barra del escritorio. Las cinco funcionan en cualquier borde.

| Disposición | Funcionamiento |
| :--- | :--- |
| Completa | Completa mantiene toda la barra en el borde. Los paneles se unen a ella. |
| Centrada | Centrada muestra solo el reloj hasta pasar el puntero. La chincheta la mantiene abierta; los paneles flotan al lado. |
| Pestañas | Pestañas une tres pestañas con una franja fina. Los iconos de estado quedan visibles; pasa el puntero por la central para ver el tiempo. |
| Islas | Islas da a cada grupo su propia cápsula y muestra siempre todos los iconos de estado. Abrir un panel amplía su isla y aparta los grupos vecinos. |
| Dinámico | Dinámico empieza con tres islas: logotipo, reloj y red/batería. Pasa el puntero para ampliar una; un panel crece desde esa misma isla. |

## Espacios de trabajo

En Ajustes > Ventanas > Espacios de trabajo (también Walker > Ajustes > Estilo > Espacios de trabajo), elige **Monitores**, **Número de espacios de trabajo** (5–10, predeterminado 10) y **Mostrar siempre** (2 hasta el total, predeterminado 5). **Números compartidos** da a cada monitor sus propios espacios 1…N: SUPER+k cambia todos los monitores juntos; SUPER+Mayús+k mueve la ventana en su monitor actual. **Repartir entre monitores** divide N por igual, empezando por la pantalla principal y asignándole primero el resto; las demás siguen de izquierda a derecha y por nombre. SUPER+k enfoca la pantalla correspondiente. Las teclas superiores a N no hacen nada. El mínimo visible es relativo al rango de cada monitor; los marcadores superiores aparecen hasta el espacio actual o el mayor ocupado y luego desaparecen. Conectar, desconectar o cambiar la pantalla principal recalcula la distribución sin perder ventanas: se trasladan al número válido más cercano de su monitor. Con un monitor ambos modos se comportan igual.

Pulsa un marcador con el botón derecho para elegir Puntos, Glifo, Números o Runas, con ejemplos en vivo. Runas es el valor predeterminado y representa los espacios 1 a 10 con las diez primeras runas del Futhark antiguo (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ).

El marcador activo muestra el símbolo en el color de acento, sin fondo relleno. Las cuatro opciones caben en el menú en cualquier borde de la barra, sin desplazamiento.

**SUPER + 1–9/0** cambia de espacio; **SUPER + Shift + 1–9/0** mueve una ventana. **SUPER + Tab** abre Vista general. Pulsa una vista previa o usa flechas y Enter; 1–9/0 cambia directamente. Solo aparecen espacios numerados ocupados y sus vistas previas quedan en memoria. Escape o un clic fuera cierra Vista general.

**SUPER + S** alterna el espacio especial, independiente de Vista general. **SUPER + Shift + Space** activa o desactiva el ocultamiento automático de la barra; si la barra se ocultó desde el Centro de control, primero la muestra. Las notificaciones siguen funcionando.

Los gestos de ratón para fondo y tema en el escritorio vacío están en **Aprender > Gestos del ratón**. Si tienes dudas, usa los atajos de teclado de los carruseles.

El control Audio/Mic abre un panel con secciones separadas para la salida de audio y el micrófono. Tailscale y Streaming están justo antes de OBS. Un interruptor en su cabecera conecta Tailscale o inicia el uso compartido, debajo siguen detalles y dispositivos, y las acciones de configuración o diagnóstico están en el menú «…».

El fondo de los botones de icono aparece al pasar el puntero; los paneles se actualizan solos al abrirse, un icono de actualización gira solo mientras cargan y las ayudas aparecen cerca del puntero. Los interruptores y los botones de acción internos tienen tamaños compactos comunes.

**Visualizador de música** abre cava con los colores del tema. Haz clic derecho en el ecualizador multimedia para abrirlo; el clic izquierdo sigue abriendo los detalles multimedia. Pulsa **q** o **Esc** para cerrarlo. Si falta cava, se instala primero.

**Ocultar automáticamente**, en Configuración > Barra del escritorio, retrae la barra tras un breve retraso cuando sales de ella con el puntero. Lleva el puntero al borde de la pantalla para mostrarla. Funciona en los cuatro bordes con los modos Completa, Centrada, Pestañas e Islas y Dinámico. Los paneles y menús abiertos, así como arrastrar la barra, la mantienen visible; después vuelve a ocultarse.

Mientras está activado, la barra no reserva espacio para las ventanas: se desliza sobre ellas en vez de moverlas. La preferencia se guarda por separado del anclaje del modo centrado y viene desactivada en instalaciones nuevas. Las notificaciones aparecen sin mostrarla.

**Reducir movimiento**, en Configuración > Barra del escritorio, hace instantáneas la apertura y el cierre de paneles, las entradas de Vista general, las transiciones de notificaciones y las animaciones decorativas de la barra. Está desactivado por defecto y se guarda en `bar-settings.json`. Los temporizadores de actualización de datos, caducidad de notificaciones y ocultación automática mantienen su funcionamiento normal.

El estilo multimedia se guarda en `bar-settings.json`: elige Barras (predeterminado, diez barras) o Línea (una onda de audio suave y sencilla) en Configuración > Barra del escritorio. El indicador precede a los controles, mantiene un tamaño fijo en todos los diseños y gira en los bordes izquierdo y derecho. Al pasar el puntero muestra la canción; el clic izquierdo abre los detalles y el derecho abre el visualizador de música. En pausa, la línea queda plana. Reducir movimiento mantiene los niveles de audio sin transiciones y detiene el movimiento decorativo de respaldo.

El modo Centrado se une al borde de la pantalla con extremos rectos y las mismas pendientes de 45° suavemente redondeadas que Pestañas a ambos lados. Las pendientes giran con la barra en los cuatro bordes e ignoran la preferencia de esquinas; los paneles separados siguen respetándola.

## Dock de aplicaciones

Toca el borde opuesto a la barra para mostrar el dock. Se despliega desde ese borde, con lados rectos que llegan hasta él, sobre las ventanas sin redimensionarlas y se oculta 350 ms después de que salga el puntero, con una animación de 320 ms (instantánea con Reducir movimiento). Aparece en la pantalla principal o en todas si la barra usa todas las pantallas. Nunca aparece sobre una ventana a pantalla completa.

Las aplicaciones abiertas se agrupan por clase, en el orden de ventanas de Hyprland. Los iconos ocupan 36 px con separaciones de 6 px y usan el icono de escritorio o un símbolo alternativo; las terminales de tareas y menús de Eitr comparten un único icono con el logotipo de Eitr.

Los puntos debajo cuentan sus ventanas, hasta tres, y se atenúan si ninguna está en el espacio actual de esa pantalla. Pasa el puntero para ver el nombre y el número de ventanas; los iconos cercanos al puntero crecen, más el más cercano, y el dock se alarga para mantenerlos dentro, salvo con **Reducir movimiento** activado.

Haz clic para enfocar la ventana usada más recientemente, cambiando de espacio si hace falta; otro clic pasa a su siguiente ventana. El botón central cierra la ventana más reciente. Las listas largas se desplazan a lo largo del dock. La superficie respeta Desenfoque/Color del tema y las esquinas elegidas.

**Dock** en **Configuración > Barra del escritorio** lo activa o desactiva. La opción `dock` de `bar-settings.json` tiene el valor predeterminado `"yes"`. No hay atajo para el dock.

Las aplicaciones fijadas permanecen totalmente opacas y sin puntos cuando están cerradas; haz clic para abrirlas en su propio ámbito de aplicación. Haz clic derecho para Mantener en el Dock / Quitar del Dock, Nueva ventana (si hay una entrada de escritorio) y Cerrar o Cerrar todas las ventanas. Escape o un clic fuera cierra el menú. Las aplicaciones sin entrada de escritorio no se pueden fijar.

Arrastra los iconos a lo largo del dock para ordenar los fijados. Arrastra una aplicación abierta a la sección de fijadas para mantenerla allí, o saca una fijada de esa sección para quitarla. Los demás iconos dejan espacio con una animación breve (instantánea con Reducir movimiento); los no fijados conservan el orden de ventanas de Hyprland. Un separador fino divide las secciones solo cuando ambas contienen aplicaciones. Los menús y los arrastres mantienen el dock visible.

Los IDs de las entradas de escritorio se guardan en orden en el archivo local `quickshell/desktop-bar/dock-pins.json`, bajo `$XDG_CONFIG_HOME` (normalmente `~/.config`), mediante escritura atómica. Las instalaciones nuevas no tienen aplicaciones fijadas. Las ventanas se asocian mediante los IDs de escritorio, StartupWMClass y las clases de las aplicaciones.

La intensidad del desenfoque se comparte con los terminales. Elija Suave, Media (predeterminada) o Fuerte en Barra del escritorio de Walker o en Configuración (SUPER + ,). Consulte [Terminal y editores](handbook:terminal) para la limitación global y los ajustes personales.

Configuración > Barra de escritorio incluye los indicadores de espacios (puntos, glifo, números y runas). Ventanas conserva los efectos y las separaciones.
