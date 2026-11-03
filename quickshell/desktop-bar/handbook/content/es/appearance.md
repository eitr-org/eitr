# Temas, fondos de pantalla y estilo

## Catálogo de temas y plugins

La barra lateral agrupa Temas y Plugins en Instalados y Obtener más, con sus
cantidades. A la derecha, el título, la
descripción y los filtros preceden una lista con desplazamiento independiente.
Arriba/Abajo recorre las filas; Derecha o Tab entra al contenido. Izquierda desde
la primera columna vuelve a la barra. Por debajo de 760 px se muestran iconos
con etiquetas al pasar el puntero, sin títulos de grupo ni texto.

Abre **Configuración > Estilo > Temas y plugins** o **SUPER + F2**. El catálogo es una ventana que recuerda su tamaño. Mantén SUPER y arrastra con el botón izquierdo para moverla o con el derecho para cambiar su tamaño. Los atajos normales permiten organizarla en mosaico o enviarla a otro espacio de trabajo. Abrirla de nuevo enfoca la ventana existente, incluso en otro espacio. SUPER + F2 la cierra si tiene el foco. También se cierra con su botón, Escape (tras cerrar cualquier confirmación) o el atajo normal para cerrar ventanas.
Instalados muestra cada tema como Integrado, Oficial, De terceros o Tuyos en una
galería de vistas previas. Pulsa un tema instalado para aplicarlo con el flujo
habitual; una marca indica el actual. Todos, Oscuros y Claros filtran la galería.
Instalados se actualiza al abrir la ventana y después de cada acción. Al abrir se comprueban los metadatos en segundo plano y aparecen indicadores de actualización. No hay comprobaciones periódicas de red; Actualizar reemplaza un tema del catálogo. Vuelve a aplicar un tema
activo actualizado para refrescar el escritorio. Eliminar pide confirmación en
la ventana y rechaza el tema activo: aplica otro primero. Los integrados y tuyos se conservan.

Obtener más muestra el repositorio oficial `eitr-org/eitr-themes`. Selecciona varios
temas pulsando sus vistas previas. La barra inferior abre la revisión con vistas
previas, origen y tamaño total; Limpiar borra la selección. Las flechas navegan
entre tarjetas y Espacio selecciona descargas. Enter aplica un tema instalado o
abre la revisión si hay descargas seleccionadas. Enter o Instalar confirma;
Escape cierra primero la revisión y después la ventana. Descargas, progreso y errores aparecen en la ventana. Las vistas previas
solo se descargan para tarjetas visibles y usan la caché del usuario. Si el repositorio
no responde, Reintentar lo recarga; Instalados funciona sin conexión.

La página Plugins muestra los plugins instalados y el repositorio oficial
`eitr-org/eitr-plugins` en tarjetas con captura, icono centrado o símbolo genérico.
Las etiquetas indican los plugins instalados y desactivados. La eliminación se
confirma en la ventana. Para instalar, usa **Walker > Plugins**. La instalación y
las actualizaciones siguen usando los flujos de revisión existentes; el catálogo
todavía no instala plugins ni acepta repositorios de terceros.

## Temas y fondos de pantalla

Abre **Configuración > Estilo > Tema** o **SUPER + Ctrl + Shift + N** para los menús Oscuro/Claro de Walker. El carrusel de temas del escritorio (doble clic derecho en el escritorio, Centro de control > Estilo > Tema o IPC appearance) muestra todos los temas. El Sol sobre la tarjeta seleccionada muestra solo los temas claros y la Luna solo los oscuros; pulsa de nuevo el seleccionado para volver a verlos todos. Ctrl+Tab alterna entre todos, oscuros y claros. Escribe para buscar entre los temas mostrados; flechas/Tab navegan y Enter aplica. Backspace edita la búsqueda o cierra si está vacía; Escape borra la búsqueda antes de cerrar. El carrusel de fondos no tiene búsqueda de temas.

**SUPER + Ctrl + N** abre los fondos y **SUPER + Shift + N** pasa al siguiente. Una marca señala la elección activa en Walker. Los cambios no muestran notificaciones de éxito. Los monitores ultrawide, al menos el doble de anchos que de altos, usan la versión 21:9 para recortar menos; los demás usan la versión 4K 16:9.

Eitr tiene cuatro fondos: Primordial Drop (predeterminado), Runestone, Élivágar y Venom Rootlight. Se eligen con los mismos controles; la paleta no cambia. El segundo fondo, Runestone, está animado: las auroras se desplazan lentamente tras el anillo de runas, se actualizan más despacio detrás de ventanas normales, se pausan detrás de aplicaciones a pantalla completa y permanecen fijas en el bloqueo. La renderización por software (por ejemplo, en una VM sin aceleración 3D) usa el fondo estático seleccionado; ocurre lo mismo si no se puede detectar el renderizador. Graphite se ha retirado; las selecciones guardadas de Graphite cambian a Eitr y su fondo predeterminado.

Los 25 temas incluidos ofrecen diez paletas oscuras de los reinos: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim y Vanaheim. Cada tema de los reinos tiene de dos a cinco fondos originales, con estilos variados de tinta, gouache, sombreado cel y pintura, en las dos proporciones. El primer fondo es la vista previa del tema.

Eitr Light es la versión clara de Primordial Venom, con superficies verde pálido, texto verde oscuro, acentos amarillo verdoso de veneno y detalles de jade/esmeralda. Sus tres fondos estáticos son Primordial Drop, Élivágar y Venom Rootlight, cada uno con una composición panorámica propia. Selecciónalo en la categoría Clara; Eitr sigue siendo el predeterminado. Fondo del tema usa la imagen estática seleccionada en la pantalla de bloqueo.

Si Hyprpaper no puede mostrar el fondo seleccionado, la barra dibuja la misma imagen fija en cada pantalla afectada, incluidas las variantes ultrapanorámicas. Las opciones de fondo y tema siguen aplicándose en el modo Focus; la alternativa cambia sin la animación de revelado.

## Tus propios fondos, temas y pantallas de bloqueo

Tus imágenes, temas y pantallas de bloqueo se quedan en este equipo, en `~/.local/share/eitr/` (`wallpapers`, `themes` y `lockscreens`). Eitr nunca los sube ni los comparte, y las actualizaciones nunca los cambian. Aparecen junto a los distribuidos, marcados como **Tuyo**, y solo ellos se pueden eliminar: selecciona uno, pulsa **Supr** y después Enter para confirmar o Escape para conservarlo.

- **Configuración > Estilo > Fondo de pantalla > Añadir mi fondo de pantalla** acepta un archivo de imagen o una dirección https. Las descargas se detienen en 50 MB y Eitr guarda una copia solo tras comprobar que el archivo es una imagen JPEG, PNG o WebP. La dirección de una página web sirve si la página ofrece una imagen principal; si no, copia la dirección de la propia imagen. La imagen se aplica al momento y aparece en la lista de fondos, en el carrusel y con SUPER + Mayús + N. Eliminar el fondo en uso cambia antes al primer fondo del tema. Elige si tu fondo aparece con todos los temas o solo con el tema actual.
- **Configuración > Estilo > Tema > Crear tema** pide una imagen (el fondo actual, uno tuyo, uno del tema u otro archivo o dirección https), claro u oscuro (Automático sigue el brillo de la imagen) y un nombre. Tras el resumen, Eitr crea una paleta completa a partir de la imagen, manteniendo el texto bien legible sobre el fondo, y aplica el tema a la barra, el terminal, el lanzador, las apps y los iconos. Después aparece una lista de colores: elige Acento, Fondo, Texto o uno de los seis colores del terminal, escribe seis dígitos hexadecimales y el cambio se aplica al momento; Escape termina. **Ctrl + E** sobre uno de tus temas vuelve a abrir la lista. Eliminar el tema en uso vuelve antes al tema que usabas antes de crearlo.
- **Configuración > Estilo > Pantalla de bloqueo > Crear pantalla de bloqueo** usa el diseño Theme Wallpaper o Material con tu imagen, un color de acento opcional y un saludo opcional bajo el reloj, y después muestra una vista previa. Se selecciona como cualquier diseño. La pantalla de inicio de sesión no puede leer tu carpeta personal: muestra el mismo diseño, con tu imagen en Theme Wallpaper y la imagen propia del diseño en Material. Eliminar la pantalla de bloqueo en uso selecciona antes su diseño.

## Barra y esquinas

**Configuración > Estilo > Barra del escritorio** elige desenfoque o color del tema, disposición completa o centrada y borde. Walker sigue esa apariencia. **Configuración > Estilo > Esquinas** elige esquinas cuadradas, redondeadas o muy redondeadas para las superficies EITR y las decoraciones del compositor. Las aplicaciones externas pueden conservar sus controles propios; los indicadores circulares siguen siendo circulares.

## Fuentes

**Configuración > Estilo > Fuentes** muestra familias instaladas utilizables, no cada variante negrita o cursiva. Las familias para documentos o sustitución quedan ocultas. JetBrainsMono Nerd Font es la predeterminada. La selección actualiza las aplicaciones compatibles y activa ligaduras donde se admiten. Eliminar una familia elimina sus variantes instaladas compatibles; no se puede eliminar la última opción utilizable. Puede ser necesario revisar a qué paquete pertenece.

## Cursor

**Configuración > Estilo > Cursor** ofrece Bibata Modern, Breeze y Vanilla DMZ. Color permite automático, oscuro o claro; Tamaño define el tamaño del puntero. Automático sigue la categoría clara u oscura del tema sin cambiar la familia elegida. Los colores establecidos expresamente se conservan. La fila seleccionada tiene una marca a la izquierda; las demás familias muestran vistas previas. Si faltan recursos, aparece un error en lugar de guardar una elección inválida.

El menú de arranque de Limine usa los colores del tema actual, el título EITR y una fuente mayor. Las instalaciones nuevas lo configuran; tras cambiar de tema se actualiza al apagar. Si no se puede leer tu tema, usa los colores predeterminados. Nunca se cambian las entradas de arranque y se guarda una copia de `limine.conf` antes de cada cambio. No se aplica el estilo con Secure Boot activo: modificar una configuración de Limine cuyo hash esté registrado impediría arrancar.

**Configuración > Estilo > Pantalla de bloqueo** define el diseño del bloqueo y del inicio de sesión. Los cambios de tema conservan tus preferencias.

Los diseños disponibles son Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing y Theme Wallpaper. Después aparecen tus propias pantallas de bloqueo; las vistas previas no bloquean la sesión. Elegir un diseño retirado pasa a Clockwork Tape. Las instalaciones nuevas empiezan con Eitr.

Eitr muestra la marca EITR en el color de acento de tu tema dentro del anillo dorado de runas de la pantalla de arranque, que avanza cada segundo, sobre un cielo estrellado con la Vía Láctea, alguna estrella fugaz de vez en cuando y la aurora del escritorio sobre negro puro (en una pantalla OLED esos píxeles quedan apagados). El reloj muestra horas y minutos con los numerales nórdicos propios de Eitr y sigue la preferencia de 12 o 24 horas. Cada carácter que escribes talla una runa en el campo de contraseña (siempre las mismas runas, en orden, así que solo se ve la longitud); las flechas, Inicio y Fin mueven el cursor de bloque, y Retroceso o Supr desmoronan la runa de al lado. La autenticación correcta desbloquea la sesión inmediatamente. Enviar la contraseña, un inicio de sesión fallido y cambiar de cuenta borran las runas al instante, sin desmoronarlas. Reducir movimiento mantiene todo quieto y omite los efectos de grabado y desmoronamiento. En una vista previa, Intro y Esc la cierran inmediatamente sin desbloquear nada.

Las ilustraciones se preparan para 4K (3840×2160, 16:9). Coffee y Pillow mantienen un anime tranquilo con ropa nórdica; Material y Clockwork usan adornos rúnicos discretos. Nothing conserva su diseño. QML y SVG siguen siendo escalables.

Compara los nueve diseños con `bash quickshell/lockscreen/scripts/gallery.sh`. No cambia tu bloqueo elegido; las acciones de autenticación y energía están desactivadas en la galería. Clockwork usa QML procedural; Coffee, Pillow, Material y Nothing conservan los diseños con licencia, ilustraciones nuevas y la fuente JetBrainsMono Nerd Font instalada. No hacen falta vídeos ni fuentes incluidos aparte.

**Fondo de pantalla del tema** usa el fondo actual con reloj arriba a la izquierda y controles de contraseña abajo a la derecha. Su vista previa en Walker muestra la imagen actual. Los cambios posteriores aparecen al bloquear o previsualizar de nuevo; Ctrl+P muestra todo el diseño sin bloquear. El inicio de sesión no puede leer tu carpeta personal: muestra una copia que Eitr guarda al elegir este diseño y cada vez que cambias el fondo. Si no está disponible, usa otro fondo del tema actual o el predeterminado Eitr.

En equipos con varias cuentas, la pantalla de inicio muestra el usuario seleccionado. Haz clic en la mitad izquierda o derecha del selector, o pulsa Ctrl+Left / Ctrl+Right, para elegir otra cuenta; Enter sigue enviando la contraseña y Escape conserva su comportamiento. Con una cuenta, el diseño de inicio no cambia. La pantalla de bloqueo muestra el nombre real de la sesión bloqueada cuando está disponible y solo acepta la contraseña de esa cuenta. Cambiar de usuario (Ctrl+Alt+U) abre el inicio de SDDM y mantiene bloqueada la sesión original. Al volver a la sesión bloqueada, haz clic una vez en el campo de contraseña antes de escribir. Solo aparece si hay varias cuentas elegibles y SDDM permite el cambio. Las vistas previas y la galería usan tres cuentas ficticias y nunca autentican.

La barra lateral del catálogo cambia entre Temas y Plugins. La pestaña Oficial combina los elementos integrados y los repositorios Eitr; Comunidad muestra el índice comunitario. Instalados muestra los elementos locales y su origen. Las tarjetas muestran muestras de la paleta cuando están disponibles. Selecciona temas, revisa sus fuentes y el tamaño total e instálalos juntos. Los plugins comunitarios se muestran; su instalación y añadir una dirección Git llegarán después.

Eliminar un tema integrado lo oculta de los selectores de esta máquina. En Instalados, activa Mostrar ocultos y elige Restaurar. Eitr y el tema actual no se pueden ocultar. Eliminar un tema descargado borra su paquete instalado.
