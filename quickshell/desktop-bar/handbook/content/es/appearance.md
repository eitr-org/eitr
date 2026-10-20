# Temas, fondos de pantalla y estilo

## Temas y fondos de pantalla

Abre **Estilo > Tema** o **SUPER + Ctrl + Shift + N**. Elige oscuro o claro y después un tema. Escribe dentro del carrusel de temas para filtrar; las flechas o Tab navegan y Enter aplica. Backspace edita primero la búsqueda; Escape la borra antes de cerrar. El selector de categoría y el carrusel de fondos no tienen búsqueda de temas.

**SUPER + Ctrl + N** abre los fondos y **SUPER + Shift + N** pasa al siguiente. Una marca señala la elección activa en Walker. Los cambios no muestran notificaciones de éxito. Los monitores ultrawide, al menos el doble de anchos que de altos, usan la versión 21:9 para recortar menos; los demás usan la versión 4K 16:9.

Norse incluye dibujos de cuervo, valquiria, Odin, Fenrir y Jörmungandr sobre fondo negro. Selecciónalos con los mismos controles; las ilustraciones adicionales no cambian la paleta. El primer fondo, la piedra rúnica, está animado: las auroras se desplazan lentamente tras el anillo de runas. Se pausan detrás de aplicaciones a pantalla completa; el bloqueo muestra la imagen fija.

## Barra y esquinas

**Estilo > Barra del escritorio** elige desenfoque o color del tema, disposición completa o centrada y borde. Walker sigue esa apariencia. **Estilo > Esquinas** elige esquinas cuadradas, redondeadas o muy redondeadas para las superficies EITR y las decoraciones del compositor. Las aplicaciones externas pueden conservar sus controles propios; los indicadores circulares siguen siendo circulares.

## Fuentes

**Estilo > Fuentes** muestra familias instaladas utilizables, no cada variante negrita o cursiva. Las familias para documentos o sustitución quedan ocultas. JetBrainsMono Nerd Font es la predeterminada. La selección actualiza las aplicaciones compatibles y activa ligaduras donde se admiten. Eliminar una familia elimina sus variantes instaladas compatibles; no se puede eliminar la última opción utilizable. Puede ser necesario revisar a qué paquete pertenece.

## Cursor

**Estilo > Cursor** ofrece Bibata Modern, Breeze y Vanilla DMZ. Color permite automático, oscuro o claro; Tamaño define el tamaño del puntero. Automático sigue la categoría clara u oscura del tema sin cambiar la familia elegida. Los colores establecidos expresamente se conservan. La fila seleccionada tiene una marca a la izquierda; las demás familias muestran vistas previas. Si faltan recursos, aparece un error en lugar de guardar una elección inválida.

El menú de arranque de Limine usa los colores del tema actual, el título EITR y una fuente mayor. Las instalaciones nuevas lo configuran; tras cambiar de tema se actualiza al apagar. Si no se puede leer tu tema, usa los colores predeterminados. Nunca se cambian las entradas de arranque y se guarda una copia de `limine.conf` antes de cada cambio. No se aplica el estilo con Secure Boot activo: modificar una configuración de Limine cuyo hash esté registrado impediría arrancar.

**Estilo > Pantalla de bloqueo** define el diseño del bloqueo y del inicio de sesión. Los cambios de tema conservan tus preferencias.

Los diseños disponibles son Clockwork Neo Orbital, Clockwork Tape, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing y Theme Wallpaper. El selector muestra solo los distribuidos; las vistas previas no bloquean la sesión. Elegir un diseño retirado pasa a Clockwork Tape, el predeterminado de las instalaciones nuevas.

Las ilustraciones se preparan para 4K (3840×2160, 16:9). Coffee y Pillow mantienen un anime tranquilo con ropa nórdica; Material y Clockwork usan adornos rúnicos discretos. Nothing conserva su diseño. QML y SVG siguen siendo escalables.

Compara los ocho diseños con `bash quickshell/lockscreen/scripts/gallery.sh`. No cambia tu bloqueo elegido; las acciones de autenticación y energía están desactivadas en la galería. Clockwork usa QML procedural; Coffee, Pillow, Material y Nothing conservan los diseños con licencia, ilustraciones nuevas y la fuente JetBrainsMono Nerd Font instalada. No hacen falta vídeos ni fuentes incluidos aparte.

**Fondo de pantalla del tema** usa el fondo actual con reloj arriba a la izquierda y controles de contraseña abajo a la derecha. Su vista previa en Walker muestra la imagen actual. Los cambios posteriores aparecen al bloquear o previsualizar de nuevo; Ctrl+P muestra todo el diseño sin bloquear. El inicio de sesión no puede leer tu carpeta personal: muestra una copia que Eitr guarda al elegir este diseño y cada vez que cambias el fondo. Si no está disponible, usa otro fondo del tema actual o el predeterminado Norse.
