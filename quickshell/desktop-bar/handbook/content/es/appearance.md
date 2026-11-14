# Temas, fondos de pantalla y estilo

Configuración (**SUPER + ,**) incluye los controles de Apariencia; **Más temas** abre el catálogo independiente de Eitr Store (**SUPER + F2**).

## Distribución de ventanas

Elige **Mosaico** (predeterminado, dwindle de Hyprland) o **Desplazamiento** en **Configuración > Ventanas > Distribución de ventanas** o **Walker > Configuración > Escritorio > Ventanas > Distribución de ventanas**. Desplazamiento organiza las ventanas en columnas sobre una cinta móvil. La selección se guarda localmente y persiste tras cambios de tema, recargas y reinicios; los cambios recargan la configuración del compositor sin reiniciar la sesión.

Desplazamiento muestra Dirección (Derecha, Izquierda, Abajo, Arriba), Anchura predeterminada de columna (Un tercio, Mitad, Dos tercios, Completa) y Ajuste del foco. Centrar centra la columna enfocada; Ajustar la muestra con el mínimo movimiento. Seguir el foco permite mover la cinta al cambiar el foco, incluidos los clics. Pantalla completa con una columna permite que una columna única ocupe la pantalla, sin activar la pantalla completa de la aplicación. Valores predeterminados: Derecha, Mitad, Ajustar y ambos interruptores activados. Las opciones se conservan al volver a Mosaico. El menú Distribución de ventanas de Walker ofrece cada una como submenú.

Solo en Desplazamiento: **SUPER + ALT + flechas** enfoca ventanas; **SUPER + ALT + SHIFT + Izquierda/Derecha** intercambia columnas; **SUPER + ALT + Equal/Minus** alterna entre un tercio, mitad, dos tercios y anchura completa. El ciclo redimensiona la columna enfocada; la anchura predeterminada se aplica a columnas nuevas. Consulta la [referencia de teclado](handbook:shortcuts).


## Eitr Store

Abre Eitr Store desde el lanzador, SUPER + F2, el menú Escritorio de Walker o Más temas en Configuración. Es una ventana independiente que se puede mover y redimensionar, con la paleta de Configuración y la cabecera EITR / STORE. Cerrar o pulsar Escape descarta selecciones y revisiones temporales.

Temas, Plugins, Pantallas de bloqueo y Fondos tienen Instalado y Descubrir. Descubrir combina tarjetas oficiales y comunitarias con insignias de origen. Filtra con Todos / Oficial / Comunidad; la búsqueda abarca las categorías cargadas de la vista actual. Los temas también se filtran por claro/oscuro. Arriba/Abajo cambia de fila; Derecha o Tab entra en la cuadrícula y la izquierda vuelve; Ctrl+F enfoca la búsqueda.

Pulsa un tema, bloqueo o fondo instalado para usarlo. Las tarjetas de Descubrir muestran detalles, imágenes y fuentes. Selecciona temas o paquetes de fondos y revisa antes de confirmar la instalación. Actualizar todo actualiza temas en secuencia y revisa cada plugin. Eliminar siempre pide confirmación; no se pueden eliminar el tema ni el bloqueo actuales.

Los plugins tienen todos los permisos de tu cuenta. Cada instalación y actualización muestra fuente, commit fijado, autor, archivos, comandos, paquetes y advertencias. Revisa el código y, si quieres, el consejo de IA. Los commits comunitarios están fijados en el índice. La revisión caduca a los 15 minutos y al cerrar. Instalado > Añadir acepta direcciones Git HTTPS o SSH de temas y plugins. Las tarjetas instaladas abren ajustes, activación, actualización y eliminación; se pueden retirar paquetes del plugin que ya no se usan.

Los bloqueos siguen siendo paquetes oficiales firmados; instalar y eliminar exige contraseña de administrador. Eitr está integrado; los diseños usados en la sesión o el acceso no se eliminan. Tus bloqueos propios se conservan y regresan al reinstalar el diseño.

Fondos muestra imágenes incluidas, propias y tarjetas de paquetes. Pulsar un paquete usa su primera imagen; también están disponibles las imágenes individuales. Los paquetes comunitarios contienen solo imágenes JPEG, PNG o WebP verificadas. Aparecen en el selector y carrusel existentes; eliminar un paquete borra solo sus archivos. No incluye salvapantallas.


Repositorio de temas: `eitr-org/eitr-themes`.

Elige otro fondo antes de eliminar un paquete usado por una selección guardada.

## Elegir tema y fondo

Elige tema y fondo en Configuración > Apariencia > Tema y fondo de pantalla. Para los menús Oscuro/Claro de Walker, usa **Walker > Configuración > Escritorio > Apariencia > Tema** o **SUPER + Ctrl + Shift + N**. Un doble clic derecho en el escritorio vacío abre el carrusel. El Sol filtra temas claros y la Luna oscuros; pulsa otra vez el filtro activo para ver todos.

El + abre el catálogo separado con el mismo filtro. Ctrl+Tab recorre filtros, escribir busca, flechas/Tab mueven y Enter aplica. Backspace edita la búsqueda, incluso hasta dejarla vacía; Escape la borra antes de cerrar.

**SUPER + Ctrl + N** abre los fondos y **SUPER + Shift + N** pasa al siguiente. Una marca señala la elección activa en Walker. Los cambios no muestran notificaciones de éxito. Los monitores ultrawide, al menos el doble de anchos que de altos, usan la versión 21:9 para recortar menos; los demás usan la versión 4K 16:9.

Eitr tiene cuatro fondos: Fiordo de la aurora (predeterminado), Fiordo al atardecer, Rune Seal y Runestone. Se eligen con los mismos controles; la paleta no cambia. El cuarto fondo, Runestone, está animado: las auroras se desplazan lentamente tras el anillo de runas, se actualizan más despacio detrás de ventanas normales, se pausan detrás de aplicaciones a pantalla completa y permanecen fijas en el bloqueo.

La renderización por software (por ejemplo, en una VM sin aceleración 3D) usa el fondo estático seleccionado; ocurre lo mismo si no se puede detectar el renderizador. Graphite se ha retirado; las selecciones guardadas de Graphite cambian a Eitr y su fondo predeterminado.

Los 13 temas integrados están disponibles sin conexión. Instala los 14 temas adicionales, entre ellos los claros Freyja y Skaði, desde el catálogo oficial `eitr-org/eitr-themes`. Las cuentas existentes recibieron los 12 primeros en segundo plano, con reintentos sin conexión, sin cambiar el tema actual ni el fondo guardado. Las cuentas nuevas reciben solo los integrados.

Los 13 temas incluidos ofrecen diez paletas oscuras de los reinos: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim y Vanaheim. Cada tema de los reinos tiene de dos a cinco fondos originales, con estilos variados de tinta, gouache, sombreado cel y pintura, en las dos proporciones. El primer fondo suele coincidir con la vista previa del tema; Svartalfheim conserva su vista previa independiente.

Eitr Light es la versión clara de Primordial Venom, con superficies verde pálido, texto verde oscuro, acentos amarillo verdoso de veneno y detalles de jade/esmeralda. Sus cuatro fondos estáticos son Fiordo al atardecer (predeterminado), The Gates of Yggdrasil, Rune Seal y Primordial Drop, cada uno con una composición panorámica propia. Selecciónalo en la categoría Clara; Eitr sigue siendo el predeterminado. Fondo del tema usa la imagen estática seleccionada en la pantalla de bloqueo.

Si Hyprpaper no puede mostrar el fondo seleccionado, la barra dibuja la misma imagen fija en cada pantalla afectada, incluidas las variantes ultrapanorámicas. Las opciones de fondo y tema siguen aplicándose en el modo Focus; la alternativa cambia sin la animación de revelado.

## Tus propios fondos, temas y pantallas de bloqueo

Tus imágenes, temas y pantallas de bloqueo se quedan en este equipo, en `~/.local/share/eitr/` (`wallpapers`, `themes` y `lockscreens`). Eitr nunca los sube ni los comparte, y las actualizaciones nunca los cambian. Aparecen junto a los distribuidos, marcados como **Tuyo**, y solo ellos se pueden eliminar: selecciona uno, pulsa **Supr** y después Enter para confirmar o Escape para conservarlo.

- **Walker > Configuración > Escritorio > Apariencia > Fondo de pantalla > Añadir mi fondo de pantalla** acepta un archivo de imagen o una dirección https. Las descargas se detienen en 50 MB y Eitr guarda una copia solo tras comprobar que el archivo es una imagen JPEG, PNG o WebP. La dirección de una página web sirve si la página ofrece una imagen principal; si no, copia la dirección de la propia imagen. La imagen se aplica al momento y aparece en la lista de fondos, en el carrusel y con SUPER + Mayús + N. Eliminar el fondo en uso cambia antes al primer fondo del tema. Elige si tu fondo aparece con todos los temas o solo con el tema actual.
- **Walker > Configuración > Escritorio > Apariencia > Tema > Crear tema** pide una imagen (el fondo actual, uno tuyo, uno del tema u otro archivo o dirección https), claro u oscuro (Automático sigue el brillo de la imagen) y un nombre. Tras el resumen, Eitr crea una paleta completa a partir de la imagen, manteniendo el texto bien legible sobre el fondo, y aplica el tema a la barra, el terminal, el lanzador, las apps y los iconos. Después aparece una lista de colores: elige Acento, Fondo, Texto o uno de los seis colores del terminal, escribe seis dígitos hexadecimales y el cambio se aplica al momento; Escape termina. **Ctrl + E** sobre uno de tus temas vuelve a abrir la lista. Eliminar el tema en uso vuelve antes al tema que usabas antes de crearlo.
- **Walker > Configuración > Escritorio > Pantalla de bloqueo > Crear pantalla de bloqueo** usa el diseño Theme Wallpaper o Material con tu imagen, un color de acento opcional y un saludo opcional bajo el reloj, y después muestra una vista previa. Se selecciona como cualquier diseño. La pantalla de inicio de sesión no puede leer tu carpeta personal: muestra el mismo diseño, con tu imagen en Theme Wallpaper y la imagen propia del diseño en Material. Eliminar la pantalla de bloqueo en uso selecciona antes su diseño.

## Cambiar la disposición de la barra

**Configuración > Barra del escritorio** elige disposición, posición y apariencia; consulta [Barra del escritorio](handbook:desktop-bar). **Configuración > Ventanas > Esquinas** elige Cuadradas, Redondeadas o Muy redondeadas. Espaciado de ventanas y Reducir movimiento están en la misma página Ventanas. Las aplicaciones externas pueden conservar su estilo interno.

<!-- eitr-figure: window-style -->

Espaciado de ventanas y Esquinas tal como los muestra **Configuración > Ventanas**, con tu elección actual marcada. Por defecto hay 6 px entre ventanas y 12 px en los bordes de la pantalla.

En **Configuración > Ventanas > Espaciado de ventanas** o **Walker > Configuración > Escritorio > Ventanas > Espaciado de ventanas** puedes elegir Ninguno, Pequeño, Mediano (predeterminado) o Grande. La selección local se conserva al cambiar el tema o recargar.

## Cambiar fuentes

Elige una fuente instalada en Configuración > Apariencia > Fuentes y cursor. JetBrainsMono Nerd Font es la predeterminada. La elección actualiza las apps compatibles; algunas mantienen su propia fuente. Para eliminar una familia, usa Walker > Configuración > Escritorio > Apariencia > Fuentes y revisa sus paquetes. No se puede eliminar la última familia utilizable.

## Cambiar el puntero

Abre Configuración > Apariencia > Fuentes y cursor. Familia del puntero elige Bibata Modern, Breeze o Vanilla DMZ. Color del puntero ofrece Automático, Oscuro o Claro; Automático sigue el tema sin cambiar la familia. Tamaño del puntero ajusta su tamaño. Las elecciones explícitas de color y tamaño se conservan al cambiar de tema. La página muestra el puntero elegido si sus archivos están disponibles.

## Elegir una pantalla de bloqueo

**Configuración > Pantalla de bloqueo** define el diseño del bloqueo y del inicio de sesión. Los cambios de tema conservan tus preferencias.

Los diseños disponibles son Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing y Theme Wallpaper. Después aparecen tus propias pantallas de bloqueo; las vistas previas no bloquean la sesión. Elegir un diseño retirado pasa a Clockwork Tape. Las instalaciones nuevas empiezan con Eitr.

Eitr muestra la marca EITR en el color de acento de tu tema dentro del anillo dorado de runas de la pantalla de arranque, que avanza cada segundo, sobre un cielo estrellado con la Vía Láctea, alguna estrella fugaz de vez en cuando y la aurora del escritorio sobre negro puro (en una pantalla OLED esos píxeles quedan apagados).

El reloj muestra horas y minutos con los numerales nórdicos propios de Eitr y sigue la preferencia de 12 o 24 horas. Cada carácter que escribes talla una runa en el campo de contraseña (siempre las mismas runas, en orden, así que solo se ve la longitud); las flechas, Inicio y Fin mueven el cursor de bloque, y Retroceso o Supr desmoronan la runa de al lado.

La autenticación correcta desbloquea la sesión inmediatamente. Enviar la contraseña, un inicio de sesión fallido y cambiar de cuenta borran las runas al instante, sin desmoronarlas. Reducir movimiento mantiene todo quieto y omite los efectos de grabado y desmoronamiento. En una vista previa, Intro y Esc la cierran inmediatamente sin desbloquear nada.

Las ilustraciones se preparan para 4K (3840×2160, 16:9). Coffee y Pillow mantienen un anime tranquilo con ropa nórdica; Material y Clockwork usan adornos rúnicos discretos. Nothing conserva su diseño. QML y SVG siguen siendo escalables.

Compara los nueve diseños con `bash quickshell/lockscreen/scripts/gallery.sh`. No cambia tu bloqueo elegido; las acciones de autenticación y energía están desactivadas en la galería. Clockwork usa QML procedural; Coffee, Pillow, Material y Nothing conservan los diseños con licencia, ilustraciones nuevas y la fuente JetBrainsMono Nerd Font instalada. No hacen falta vídeos ni fuentes incluidos aparte.

**Fondo de pantalla del tema** usa el fondo actual con reloj arriba a la izquierda y controles de contraseña abajo a la derecha. Su vista previa en Walker muestra la imagen actual. Los cambios posteriores aparecen al bloquear o previsualizar de nuevo; Ctrl+P muestra todo el diseño sin bloquear. El inicio de sesión no puede leer tu carpeta personal: muestra una copia que Eitr guarda al elegir este diseño y cada vez que cambias el fondo. Si no está disponible, usa otro fondo del tema actual o el predeterminado Eitr.

En equipos con varias cuentas, la pantalla de inicio muestra el usuario seleccionado. Haz clic en la mitad izquierda o derecha del selector, o pulsa Ctrl+Left / Ctrl+Right, para elegir otra cuenta; Enter sigue enviando la contraseña y Escape conserva su comportamiento. Con una cuenta, el diseño de inicio no cambia.

Con varias pantallas, la pantalla de inicio de sesión aparece solo en la más grande; las demás quedan en negro.

La pantalla de bloqueo muestra el nombre real de la sesión bloqueada cuando está disponible y solo acepta la contraseña de esa cuenta. Cambiar de usuario (Ctrl+Alt+U) abre el inicio de SDDM y mantiene bloqueada la sesión original. Al volver a la sesión bloqueada, haz clic una vez en el campo de contraseña antes de escribir.

Solo aparece si hay varias cuentas elegibles y SDDM permite el cambio. Las vistas previas y la galería usan tres cuentas ficticias y nunca autentican.

## Notas técnicas

El menú de arranque de Limine usa los colores del tema actual, el título EITR y una fuente mayor. Las instalaciones nuevas lo configuran; tras cambiar de tema se actualiza al apagar. Si no se puede leer tu tema, usa los colores predeterminados. Nunca se cambian las entradas de arranque y se guarda una copia de `limine.conf` antes de cada cambio. No se aplica el estilo con Secure Boot activo: modificar una configuración de Limine cuyo hash esté registrado impediría arrancar.

## Vistas previas y asignaciones de fondos

En Ajustes > Apariencia > Tema y fondo, pulsa una imagen para previsualizar su fotograma fijo en el escritorio. Aplicar la guarda; Cancelar vista previa, cambiar de página o cerrar restaura la elección guardada. La paleta no cambia. Walker > Ajustes > Escritorio > Apariencia > Fondo abre el carrusel en la imagen seleccionada. Las flechas previsualizan; Intro aplica; Escape o pulsar fuera cancela.

Sobre los fondos del carrusel, **Este tema** y **Todos los temas** alternan entre los fondos del tema actual y los de todos los temas instalados (también con Ctrl+Tab). Debajo de cada fondo aparece su nombre (con todos los temas, también el tema del que viene), y al escribir se buscan nombres y temas; tus propias imágenes van al final. Elegir uno cambia solo el fondo; los colores del tema se mantienen.

Fondo por pantalla en Configuración > Apariencia > Tema y fondo (o Walker > Configuración > Escritorio > Apariencia > Fondo por pantalla) está desactivado de forma predeterminada: elegir o previsualizar un fondo cambia todas las pantallas. Actívalo para cambiar solo la pantalla que usas al elegir la imagen. Las pantallas sin selección propia usan el fondo global.

Las asignaciones y el interruptor son locales. Desactivarlo restaura de inmediato el fondo global en todas las pantallas y conserva sus selecciones; al activarlo vuelven. El inicio de sesión y la reconexión restauran cada salida por separado. Cambiar de tema borra todas las selecciones por pantalla, conserva el interruptor y usa el fondo del tema nuevo. Elegir solo un fondo conserva las selecciones por pantalla. Se eliminan las asignaciones de archivos no disponibles. Runestone reanuda su animación al terminar la vista previa; el renderizado por software usa la misma imagen fija.
