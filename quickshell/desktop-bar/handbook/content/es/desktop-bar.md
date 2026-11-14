# Barra y espacios de trabajo

<!-- eitr-figure: bar-anatomy -->

La barra completa. El logotipo de Eitr abre el Centro de control; le siguen Vista general, los marcadores de espacios de trabajo, Uso de IA, Hardware y Bloqueo automático. La fecha y la hora quedan centradas, con la multimedia delante y el tiempo detrás. **Mostrar iconos** muestra u oculta los iconos de estado de la derecha; las notificaciones van al final.

Los elementos de plugins pueden aparecer después del bloqueo automático, antes del reloj, después del reloj o en el grupo de estado. Elija la posición en Ajustes > Plugins > el plugin > En la barra. Los límites son cuatro después del bloqueo automático, dos a cada lado del reloj y ocho en estado, por orden de colocación; los elementos adicionales quedan ocultos en la posición elegida. Centered y Dynamic los muestran al expandirse; Tabs e Islands los incluyen; Drop oculta los elementos de plugins de la barra. El reloj permanece centrado en la pantalla. World clock es un plugin oficial opcional que respeta la preferencia de 12/24 horas.

Weather es un plugin oficial integrado, instalado por defecto después del reloj. Elimínelo en Eitr Store > Instalados > Plugins para ocultar el tiempo en todas partes, incluida la página de inicio de Drop. Sigue eliminado tras las actualizaciones; vuelva a instalarlo desde Descubrir usando la copia incluida en el paquete, sin descarga. La búsqueda de ciudades es temporal durante la sesión.

Islas presenta grupos en superficies separadas: logotipo, Vista general y espacios de trabajo, Uso de IA/Hardware/Bloqueo por inactividad, reloj, tiempo y controles de estado. Los indicadores multimedia y de captura aparecen solo cuando están activos. El reloj permanece exactamente centrado en la pantalla; el tiempo tiene su propia superficie al lado.

Las superficies son siempre totalmente redondeadas, sea cual sea la preferencia de esquinas, y siguen el color/transparencia y el desenfoque. Las superficies quedan a la mitad del espacio exterior actual de Hyprland del borde, con el espacio completo entre superficies vecinas, en los cuatro lados. La reserva para ventanas incluye el grosor y esa mitad; la ocultación automática no reserva espacio.

Los huecos dejan pasar los clics. El espacio vacío de cada superficie admite los gestos habituales de doble clic y arrastre. Abrir un panel hace crecer una tarjeta desde su isla (hacia el lado libre: el tiempo a la derecha, multimedia y captura a la izquierda, el estado hacia el centro, el reloj hacia ambos lados) y aparta las islas vecinas; la isla queda oculta bajo la tarjeta hasta que vuelve a encogerse.

Los iconos de estado conservan el botón manual para mostrar u ocultar.

En Configuración > Ventanas, la disposición y los monitores usan dos botones. El número de espacios y Siempre mostrar usan listas desplegables; Siempre mostrar ofrece de 2 al número actual de espacios. Las descripciones explican el efecto de cada ajuste, incluida la disposición elegida y las opciones de desplazamiento.

## Actualizaciones

El icono de actualizaciones, antes de Notificaciones, comprueba poco después de iniciar sesión y cada seis horas. Púlsalo para actualizar el sistema; el clic derecho vuelve a comprobar. Una actualización correcta lo marca como actualizado hasta la próxima comprobación, sin iniciar otra inmediatamente. Sin conexión o si falla, indica que el estado no está disponible, nunca un falso «actualizado». La comprobación usa una base de paquetes privada y no actualiza paquetes.

## Cambiar la disposición de la barra

- Haz doble clic izquierdo en el **espacio vacío de la barra** para recorrer Color del tema → Desenfoque → Sitio web; las instalaciones nuevas comienzan con Color del tema. Sitio web usa los colores del sitio de Eitr, claros u oscuros según el tema.
- Haz doble clic derecho en el espacio vacío para recorrer Completa → Centrada → Pestañas → Islas → Dinámico → Gota → Completa.
- Arrastra el espacio vacío hacia arriba, abajo, izquierda o derecha para mover la barra. A izquierda y derecha la barra es tan estrecha como arriba y abajo: el reloj muestra la hora sobre los minutos con un icono de calendario y el tiempo solo su icono; pasa el puntero para ver la fecha y la temperatura.
- **Reloj** en Configuración > Barra del escritorio muestra la hora en formato de 12 horas con AM/PM (predeterminado) o de 24 horas, en cualquier borde.
- Las mismas opciones están en **Configuración > Barra del escritorio**, en sus pestañas Distribución, Apariencia y Comportamiento.
- **Pantallas** (Mostrar en) coloca la barra solo en la principal, por defecto, o en todas. En todas, cada barra marca el espacio de trabajo de su pantalla; atajos como SUPER + I se abren en la pantalla en uso y las notificaciones aparecen solo en la principal. Elige la principal en el panel Pantalla.

<!-- eitr-figure: bar-layouts -->

Los seis diseños en el orden en que los recorre el doble clic derecho. En reposo, Centrada muestra solo el reloj, Dinámico tres pequeñas islas y Gota una sola cápsula con la hora; Centrada y Dinámico se despliegan al pasar el puntero.

Elige una disposición en Configuración > Barra del escritorio. Las seis funcionan en cualquier borde.

| Disposición | Funcionamiento |
| :--- | :--- |
| Completa | Completa mantiene toda la barra en el borde. Los paneles se unen a ella. |
| Centrada | Centrada muestra solo el reloj hasta pasar el puntero. La chincheta, o Mantener expandido en Configuración > Barra del escritorio (también en Walker), la mantiene abierta; los paneles flotan al lado. |
| Pestañas | Pestañas une tres pestañas con una franja fina. Los iconos de estado y el tiempo quedan visibles. |
| Islas | Islas da a cada grupo su propia cápsula y muestra siempre todos los iconos de estado. Abrir un panel amplía su isla y aparta los grupos vecinos. |
| Dinámico | Dinámico empieza con tres islas: logotipo, reloj y red/batería, más una isla multimedia entre el logotipo y el reloj mientras suena algo. Pasa el puntero para ampliar una; un panel crece desde esa misma isla. |
| Gota | Gota muestra solo la hora en una cápsula en el centro del borde. Haz clic para que crezca su panel; el clic derecho abre directamente los controles rápidos. Con la ocultación automática no queda nada en pantalla hasta que una gota cae del borde y se convierte en la cápsula. |

**Estilo de las islas** (Ajustes > Barra del escritorio > Distribución, o Walker > Ajustes > Escritorio > Barra del escritorio > Estilo de las islas) elige cómo Islas, Dinámico y Gota se encuentran con el borde de la pantalla: Flotante deja las píldoras a medio espacio exterior del borde; Unida las pega a él, rectas del lado del borde y con lados rectos, y sus paneles también crecen desde el borde. **Estilo de los lados** elige cómo Pestañas y Centrada se unen al borde: rampas de 45° o lados rectos (con lados rectos, Pestañas también pierde la franja fina entre las pestañas).

## El panel de Gota

Haz clic en la cápsula de la hora de Gota y la propia cápsula crece hasta un panel. Arrastra una página hacia un lado (a la derecha avanza, a la izquierda retrocede, y ambas dan la vuelta) o usa las flechas o el desplazamiento horizontal. Esc o un clic fuera lo cierra. Nada en él abre otro panel: los detalles se abren en el mismo sitio con una flecha para volver.

| Página | Qué contiene |
| :--- | :--- |
| Calendario y tiempo | El tiempo junto al mes. Haz clic en el tiempo para ver el pronóstico completo y buscar una ciudad; haz clic en un día para ver sus planes y añadir un recordatorio a una hora de ese día. |
| Multimedia | La portada rodeada de barras que siguen la música, la canción, su letra, los controles y una barra de progreso. Solo mientras suena algo. |
| OBS | Estado de grabación y emisión con pausa, detener y emitir en directo, una marca de capítulo, la carpeta de grabaciones y OBS. Mientras OBS está abierto. |
| Controles rápidos | WiFi, Bluetooth, Sonido y Micrófono abren sus redes y dispositivos en el mismo sitio; Modo avión, Silencio, Luz nocturna, Bloqueo por inactividad, Grabar y Configuración; volumen, micrófono y (en portátiles) brillo. |
| Temporizador y concentración | Una cuenta atrás, un cronómetro o sesiones de concentración de 25 minutos con descansos de 5. Sigue con el panel cerrado y te avisa al terminar. |
| Rendimiento, Uso de IA y Notificaciones | CPU, GPU, RAM y almacenamiento; los límites de cada asistente (haz clic en uno para verlos todos); la lista de notificaciones. |

En todos los modos, el reloj muestra a su lado lo que pasa, donde se sitúa el punto de grabación: una marca de calendario cuando un evento empieza en menos de diez minutos (haz clic para ver los planes de ese día) y un anillo mientras corre un temporizador o una sesión de concentración (haz clic para Centro de control > Herramientas > Temporizador y concentración). Una notificación nueva hace sonar dos veces la campana de la barra; donde la campana está oculta (Centrada mientras está plegada, Dinámico en reposo), aparece en su lugar una campana junto al reloj. La batería de un portátil sustituye un momento la hora por su porcentaje en rojo al 15 % y al 5 %; donde los espacios de trabajo están ocultos, también aparece el número del espacio al que cambias.

Alrededor de la hora, la cápsula de Gota muestra lo que pasa y solo deja sitio donde hace falta. Antes de la hora: un punto rojo mientras grabas, una marca de calendario cuando un evento empieza en menos de diez minutos, un anillo mientras corre un temporizador, una flecha que gira mientras la barra busca actualizaciones y la marca de actualizaciones mientras se ve su notificación (haz clic para Actualizar el sistema) y una nota mientras suena música (haz clic para Multimedia). Después: una campana que suena dos veces con una notificación nueva (haz clic para ver la lista). Al cambiar de espacio de trabajo, la hora se sustituye un momento por su número; la batería de un portátil hace lo mismo en rojo al 15 % y al 5 %. Arrastra la nota a la derecha para convertir la cápsula en una línea de la letra; arrastra hacia cualquier lado, pausa o detén para volver.

**Letras en línea** (Configuración > Barra del escritorio > Comportamiento, o Walker > Configuración > Escritorio > Barra del escritorio > Letras en línea) está desactivado por defecto. Al activarlo, Gota busca la canción en LRCLIB (lrclib.net) y envía su título, artista, álbum y duración. Las letras que envía el propio reproductor siempre tienen prioridad.

## Espacios de trabajo

En Ajustes > Ventanas > Espacios de trabajo (también Walker > Ajustes > Escritorio > Ventanas > Espacios de trabajo), elige **Monitores**, **Número de espacios de trabajo** (5–10, predeterminado 10) y **Mostrar siempre** (2 hasta el total, predeterminado 5). **Números compartidos** da a cada monitor sus propios espacios 1…N: SUPER+k cambia todos los monitores juntos; SUPER+Mayús+k mueve la ventana en su monitor actual, y todos los monitores cambian con ella a ese número. **Repartir entre monitores** divide N por igual, empezando por la pantalla principal y asignándole primero el resto; las demás siguen de izquierda a derecha y por nombre. SUPER+k enfoca la pantalla correspondiente. Las teclas superiores a N no hacen nada. El mínimo visible es relativo al rango de cada monitor; los marcadores superiores aparecen hasta el espacio actual o el mayor ocupado y luego desaparecen. Conectar, desconectar o cambiar la pantalla principal recalcula la distribución sin perder ventanas: se trasladan al número válido más cercano de su monitor. Con un monitor ambos modos se comportan igual.

Pulsa un marcador con el botón derecho para elegir Puntos, Glifo, Números o Runas, con ejemplos en vivo. Runas es el valor predeterminado y representa los espacios 1 a 10 con las diez primeras runas del Futhark antiguo (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ).

El marcador activo muestra el símbolo en el color de acento, sin fondo relleno. Las cuatro opciones caben en el menú en cualquier borde de la barra, sin desplazamiento.

**SUPER + 1–9/0** cambia de espacio; **SUPER + Shift + 1–9/0** mueve una ventana. **SUPER + Tab** abre Vista general. Pulsa una vista previa o usa flechas y Enter; 1–9/0 cambia directamente. Solo aparecen espacios numerados ocupados y sus vistas previas quedan en memoria. Escape o un clic fuera cierra Vista general.

**SUPER + S** alterna el espacio especial, independiente de Vista general. **SUPER + Shift + Space** activa o desactiva el ocultamiento automático de la barra; si la barra se ocultó desde el Centro de control, primero la muestra. Las notificaciones siguen funcionando.

Los gestos de ratón para fondo y tema en el escritorio vacío están en **Aprender > Gestos del ratón**. Si tienes dudas, usa los atajos de teclado de los carruseles.

El control Audio/Mic abre un panel con secciones separadas para la salida de audio y el micrófono. Streaming está justo antes de OBS. Un interruptor en su cabecera inicia el uso compartido, debajo siguen los detalles, y las acciones de configuración o diagnóstico están en el menú «…».

El fondo de los botones de icono aparece al pasar el puntero; los paneles se actualizan solos al abrirse, un icono de actualización gira solo mientras cargan y las ayudas aparecen cerca del puntero. Los interruptores y los botones de acción internos tienen tamaños compactos comunes.

**Visualizador de música** abre cava con los colores del tema. Haz clic derecho en el ecualizador multimedia para abrirlo; el clic izquierdo sigue abriendo los detalles multimedia. Pulsa **q** o **Esc** para cerrarlo. Si falta cava, se instala primero.

**Ocultar automáticamente**, en Configuración > Barra del escritorio, retrae la barra tras un breve retraso cuando sales de ella con el puntero. Lleva el puntero al borde de la pantalla para mostrarla. Funciona en los cuatro bordes con los modos Completa, Centrada, Pestañas, Islas, Dinámico y Gota; con Gota, una gota del color de la barra cae del borde y se convierte en la cápsula de la hora. Una notificación nueva hace aparecer la barra hasta que se cierra su aviso. Los paneles y menús abiertos, así como arrastrar la barra, la mantienen visible; después vuelve a ocultarse.

Mientras está activado, la barra no reserva espacio para las ventanas: se desliza sobre ellas en vez de moverlas. La preferencia se guarda por separado del anclaje del modo centrado y viene desactivada en instalaciones nuevas.

**Reducir movimiento**, en Configuración > Barra del escritorio, hace instantáneas la apertura y el cierre de paneles, las entradas de Vista general, las transiciones de notificaciones y las animaciones decorativas de la barra. Está desactivado por defecto y se guarda en `bar-settings.json`. Los temporizadores de actualización de datos, caducidad de notificaciones y ocultación automática mantienen su funcionamiento normal.

El estilo multimedia se guarda en `bar-settings.json`: elige Barras (predeterminado, diez barras) o Línea (una onda de audio suave y sencilla) en Configuración > Barra del escritorio. El indicador precede a los controles, mantiene un tamaño fijo en todos los diseños y gira en los bordes izquierdo y derecho. Al pasar el puntero muestra la canción; el clic izquierdo abre los detalles y el derecho abre el visualizador de música. Arrástralo a la izquierda para ver una línea de la letra en su lugar; arrastra la línea hacia cualquier lado para recuperarlo. En pausa, la línea queda plana. Reducir movimiento mantiene los niveles de audio sin transiciones y detiene el movimiento decorativo de respaldo.

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
