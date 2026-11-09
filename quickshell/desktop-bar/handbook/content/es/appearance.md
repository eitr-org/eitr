# Temas, fondos de pantalla y estilo

Configuración (**SUPER + ,**) incluye los controles de Apariencia; **Más temas** abre el catálogo independiente de temas y plugins (**SUPER + F2**).

## Catálogo de temas y plugins

El catálogo comparte el marco, la barra lateral, el encabezado de página y las
tarjetas de la ventana de Configuración. Sigue los colores del tema, o la paleta
del sitio web de Eitr cuando Configuración la elige, con la tipografía Cinzel
incluida.

La barra lateral enumera Instalado, Oficial y Comunidad bajo Temas y bajo Plugins.
A la derecha están el título, la descripción, el filtro Todas, Claro y Oscuro para
los temas y una galería con desplazamiento independiente. Arriba/Abajo recorre las
filas; Derecha o Tab entra al contenido. Izquierda desde la primera columna vuelve
a la barra lateral.

Abre **Más temas** en Configuración > Apariencia > Tema y fondo de pantalla o pulsa **SUPER + F2**. Temas y plugins es una ventana independiente. Consulta [Configuración](handbook:system) para navegar.

El catálogo es una ventana que recuerda su tamaño. Mantén SUPER y arrastra con el botón izquierdo para moverla o con el derecho para cambiar su tamaño. Los atajos normales permiten organizarla en mosaico o enviarla a otro espacio de trabajo. Abrirla de nuevo enfoca la ventana existente, incluso en otro espacio.

SUPER + F2 la cierra si tiene el foco. También se cierra con su botón, Escape (tras cerrar cualquier confirmación) o el atajo normal para cerrar ventanas. Instalados muestra cada tema como Integrado, Oficial, De terceros o Tuyos en una
galería de vistas previas. Pulsa un tema instalado para aplicarlo con el flujo
habitual; una marca indica el actual.

Todos, Oscuros y Claros filtran la galería. Instalados se actualiza al abrir la ventana y después de cada acción. Al abrir se comprueban los metadatos en segundo plano y aparecen indicadores de actualización. No hay comprobaciones periódicas de red; Actualizar reemplaza un tema del catálogo. Vuelve a aplicar un tema
activo actualizado para refrescar el escritorio.

Eliminar pide confirmación en
la ventana y rechaza el tema activo: aplica otro primero. Los integrados y tuyos se conservan.

Oficial reúne los temas integrados y el repositorio `eitr-org/eitr-themes`;
Comunidad muestra temas de la comunidad. Pulsa una tarjeta de estas pestañas
para ver sus detalles: vista previa, descripción, paleta (pasa el puntero para
ver valores hexadecimales), origen, tamaño, responsable y licencia. Los fondos
aparecen como miniaturas; los comunitarios usan tarjetas con nombre y tamaño.

Pulsa uno para ampliarlo, usa Anterior/Siguiente para recorrerlos y Atrás para
volver. Escape, el botón de cierre o un clic fuera cierra los detalles y devuelve
el foco a la tarjeta. Los fondos remotos completos solo se descargan al abrirlos;
las imágenes instaladas se leen localmente.

Instalar en la tarjeta alterna la selección y muestra Seleccionado con una marca. Las tarjetas instaladas muestran Instalado y Actual cuando corresponde. Selecciona
varios temas y usa Revisar e instalar en la ventana emergente bajo las tarjetas para revisar vistas previas,
orígenes y tamaño total; Limpiar borra la selección. Las flechas navegan, Espacio
alterna la selección y Enter abre detalles en Oficial o Comunidad.

Usa Tab hasta
Revisar e instalar en esa ventana emergente y Enter para revisar. Enter sigue aplicando temas
en Instalados y confirma una revisión abierta. Instalar en los detalles revisa
solo ese tema; después ofrece Aplicar, o Actual si está activo. Escape cancela la
revisión antes de cerrar detalles o ventana. Descargas, progreso y errores quedan
en la ventana.

Las vistas previas visibles y galerías abiertas usan la caché. Si el repositorio no responde, Reintentar lo recarga; Instalados funciona sin conexión.

Los tamaños de fondos comunitarios fuera de la caché aparecen como Tamaño no disponible
hasta abrirlos: obtenerlos con Git descargaría el archivo completo. Los tamaños en caché se muestran.

La página Plugins muestra los plugins instalados y el repositorio oficial
`eitr-org/eitr-plugins` en tarjetas con captura, icono centrado o símbolo genérico.
Las etiquetas indican los plugins instalados y desactivados. La eliminación se
confirma en la ventana.

El catálogo instala y actualiza plugins dentro de la ventana. Las tarjetas Oficial y Comunidad abren detalles con imágenes, vídeos y componentes. Los vídeos empiezan silenciados y se detienen al cerrar. Instalar y Actualizar muestran fuente, commit completo, autor, archivos, comandos, avisos y cambios; la revisión opcional por IA aparece como texto.

Los plugins tienen todos los permisos de tu cuenta. Enter confirma y Escape cancela. Se instala exactamente el commit revisado; Comunidad usa el commit fijado en el índice. La revisión caduca en 15 minutos y se descarta al cerrar el catálogo. Instalados > Añadir desde una dirección Git acepta HTTPS o SSH para plugins y temas de datos, sin terminal.

Los temas integrados vienen con Eitr y no se pueden eliminar. La papelera de un tema descargado borra su paquete instalado; el tema actual no se puede eliminar.

Escribe en cualquier parte del catálogo, o pulsa Ctrl+F o /, para buscar en la página actual por nombre o descripción. Las palabras pueden ir en cualquier orden; Escape borra primero la búsqueda.

## Elegir tema y fondo

Elige tema y fondo en Configuración > Apariencia > Tema y fondo de pantalla. Para los menús Oscuro/Claro de Walker, usa **Walker > Configuración > Estilo > Tema** o **SUPER + Ctrl + Shift + N**. Un doble clic derecho en el escritorio vacío abre el carrusel. El Sol filtra temas claros y la Luna oscuros; pulsa otra vez el filtro activo para ver todos.

El + abre el catálogo separado con el mismo filtro. Ctrl+Tab recorre filtros, escribir busca, flechas/Tab mueven y Enter aplica. Backspace edita la búsqueda o cierra si está vacía; Escape la borra antes de cerrar.

**SUPER + Ctrl + N** abre los fondos y **SUPER + Shift + N** pasa al siguiente. Una marca señala la elección activa en Walker. Los cambios no muestran notificaciones de éxito. Los monitores ultrawide, al menos el doble de anchos que de altos, usan la versión 21:9 para recortar menos; los demás usan la versión 4K 16:9.

Eitr tiene cuatro fondos: Fiordo de la aurora (predeterminado), Fiordo al atardecer, Rune Seal y Runestone. Se eligen con los mismos controles; la paleta no cambia. El cuarto fondo, Runestone, está animado: las auroras se desplazan lentamente tras el anillo de runas, se actualizan más despacio detrás de ventanas normales, se pausan detrás de aplicaciones a pantalla completa y permanecen fijas en el bloqueo.

La renderización por software (por ejemplo, en una VM sin aceleración 3D) usa el fondo estático seleccionado; ocurre lo mismo si no se puede detectar el renderizador. Graphite se ha retirado; las selecciones guardadas de Graphite cambian a Eitr y su fondo predeterminado.

Los 13 temas integrados están disponibles sin conexión. Instala los 14 temas adicionales, entre ellos los claros Freyja y Skaði, desde el catálogo oficial `eitr-org/eitr-themes`. Las cuentas existentes recibieron los 12 primeros en segundo plano, con reintentos sin conexión, sin cambiar el tema actual ni el fondo guardado. Las cuentas nuevas reciben solo los integrados.

Los 13 temas incluidos ofrecen diez paletas oscuras de los reinos: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim y Vanaheim. Cada tema de los reinos tiene de dos a cinco fondos originales, con estilos variados de tinta, gouache, sombreado cel y pintura, en las dos proporciones. El primer fondo suele coincidir con la vista previa del tema; Svartalfheim conserva su vista previa independiente.

Eitr Light es la versión clara de Primordial Venom, con superficies verde pálido, texto verde oscuro, acentos amarillo verdoso de veneno y detalles de jade/esmeralda. Sus cuatro fondos estáticos son Fiordo al atardecer (predeterminado), The Gates of Yggdrasil, Rune Seal y Primordial Drop, cada uno con una composición panorámica propia. Selecciónalo en la categoría Clara; Eitr sigue siendo el predeterminado. Fondo del tema usa la imagen estática seleccionada en la pantalla de bloqueo.

Si Hyprpaper no puede mostrar el fondo seleccionado, la barra dibuja la misma imagen fija en cada pantalla afectada, incluidas las variantes ultrapanorámicas. Las opciones de fondo y tema siguen aplicándose en el modo Focus; la alternativa cambia sin la animación de revelado.

## Tus propios fondos, temas y pantallas de bloqueo

Tus imágenes, temas y pantallas de bloqueo se quedan en este equipo, en `~/.local/share/eitr/` (`wallpapers`, `themes` y `lockscreens`). Eitr nunca los sube ni los comparte, y las actualizaciones nunca los cambian. Aparecen junto a los distribuidos, marcados como **Tuyo**, y solo ellos se pueden eliminar: selecciona uno, pulsa **Supr** y después Enter para confirmar o Escape para conservarlo.

- **Walker > Configuración > Estilo > Fondo de pantalla > Añadir mi fondo de pantalla** acepta un archivo de imagen o una dirección https. Las descargas se detienen en 50 MB y Eitr guarda una copia solo tras comprobar que el archivo es una imagen JPEG, PNG o WebP. La dirección de una página web sirve si la página ofrece una imagen principal; si no, copia la dirección de la propia imagen. La imagen se aplica al momento y aparece en la lista de fondos, en el carrusel y con SUPER + Mayús + N. Eliminar el fondo en uso cambia antes al primer fondo del tema. Elige si tu fondo aparece con todos los temas o solo con el tema actual.
- **Walker > Configuración > Estilo > Tema > Crear tema** pide una imagen (el fondo actual, uno tuyo, uno del tema u otro archivo o dirección https), claro u oscuro (Automático sigue el brillo de la imagen) y un nombre. Tras el resumen, Eitr crea una paleta completa a partir de la imagen, manteniendo el texto bien legible sobre el fondo, y aplica el tema a la barra, el terminal, el lanzador, las apps y los iconos. Después aparece una lista de colores: elige Acento, Fondo, Texto o uno de los seis colores del terminal, escribe seis dígitos hexadecimales y el cambio se aplica al momento; Escape termina. **Ctrl + E** sobre uno de tus temas vuelve a abrir la lista. Eliminar el tema en uso vuelve antes al tema que usabas antes de crearlo.
- **Walker > Configuración > Estilo > Pantalla de bloqueo > Crear pantalla de bloqueo** usa el diseño Theme Wallpaper o Material con tu imagen, un color de acento opcional y un saludo opcional bajo el reloj, y después muestra una vista previa. Se selecciona como cualquier diseño. La pantalla de inicio de sesión no puede leer tu carpeta personal: muestra el mismo diseño, con tu imagen en Theme Wallpaper y la imagen propia del diseño en Material. Eliminar la pantalla de bloqueo en uso selecciona antes su diseño.

## Cambiar la disposición de la barra

**Configuración > Barra del escritorio** elige disposición, posición y apariencia; consulta [Barra del escritorio](handbook:desktop-bar). **Configuración > Ventanas > Esquinas** elige Cuadradas, Redondeadas o Muy redondeadas. Espaciado de ventanas y Reducir movimiento están en la misma página Ventanas. Las aplicaciones externas pueden conservar su estilo interno.

<!-- eitr-figure: window-style -->

Espaciado de ventanas y Esquinas tal como los muestra **Configuración > Ventanas**, con tu elección actual marcada. Por defecto hay 6 px entre ventanas y 12 px en los bordes de la pantalla.

En **Configuración > Ventanas > Espaciado de ventanas** o **Walker > Configuración > Estilo > Espaciado de ventanas** puedes elegir Ninguno, Pequeño, Predeterminado o Grande. La selección local se conserva al cambiar el tema o recargar.

## Cambiar fuentes

Elige una fuente instalada en Configuración > Apariencia > Fuentes y cursor. JetBrainsMono Nerd Font es la predeterminada. La elección actualiza las apps compatibles; algunas mantienen su propia fuente. Para eliminar una familia, usa Walker > Configuración > Estilo > Fuentes y revisa sus paquetes. No se puede eliminar la última familia utilizable.

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

La pantalla de bloqueo muestra el nombre real de la sesión bloqueada cuando está disponible y solo acepta la contraseña de esa cuenta. Cambiar de usuario (Ctrl+Alt+U) abre el inicio de SDDM y mantiene bloqueada la sesión original. Al volver a la sesión bloqueada, haz clic una vez en el campo de contraseña antes de escribir.

Solo aparece si hay varias cuentas elegibles y SDDM permite el cambio. Las vistas previas y la galería usan tres cuentas ficticias y nunca autentican.

## Notas técnicas

El menú de arranque de Limine usa los colores del tema actual, el título EITR y una fuente mayor. Las instalaciones nuevas lo configuran; tras cambiar de tema se actualiza al apagar. Si no se puede leer tu tema, usa los colores predeterminados. Nunca se cambian las entradas de arranque y se guarda una copia de `limine.conf` antes de cada cambio. No se aplica el estilo con Secure Boot activo: modificar una configuración de Limine cuyo hash esté registrado impediría arrancar.
