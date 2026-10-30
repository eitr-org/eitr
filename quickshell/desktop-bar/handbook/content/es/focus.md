# Focus

![Franja de pestañas de Focus con ventanas de ejemplo y dos paneles unidos.](assets/focus-strip.png)

Focus sustituye la barra por una franja de pestañas de 28 px en la parte superior
de cada monitor. Abre **Configuración > Estilo > Focus** o **Centro de control > Estilo > Focus**,
o ejecuta `eitr focus on`. `eitr focus status` muestra `on` u `off` sin consultar
Hyprland. `eitr focus off` restaura la barra, los efectos y los atajos habituales.
No hay un atajo exclusivo para alternarlo.

La preferencia se guarda en `~/.config/eitr/focus.json` (bajo `$XDG_CONFIG_HOME`
si está definido). Se conserva tras reinicios, actualizaciones y cambios de tema.
La configuración de la barra normal se guarda por separado y no se sustituye.

## Pestañas y paneles

Las ventanas abiertas, incluidas las flotantes y las del espacio especial, se
reúnen en grupos nativos de Hyprland. Un grupo llena la pantalla bajo la franja.
Se desactivan separaciones, bordes, esquinas redondeadas, desenfoque, sombras y
animaciones. La franja sigue el tema, tiene extremos cuadrados como el diseño
Pestañas y solo muestra títulos, reloj y estado de red/batería. La batería aparece
solo si existe una batería del sistema. Los títulos largos se abrevian y las
pestañas numerosas permiten desplazamiento. La pestaña resaltada identifica la
ventana enfocada; líneas del color de acento unen los paneles visibles de una
división. Los cuadros y menús de las aplicaciones pueden conservar su estilo propio.

- **SUPER + 1–9** selecciona la pestaña 1–9 del monitor enfocado.
- **SUPER + Tab / SUPER + Shift + Tab** selecciona la siguiente/anterior.
- **SUPER + backslash** divide el grupo con su siguiente pestaña, lado a lado.
- **SUPER + minus** apila esa pestaña debajo.
- **SUPER + H/J/K/L** enfoca el panel izquierdo/inferior/superior/derecho.
- **SUPER + Shift + H/J/K/L** reduce anchura/aumenta altura/reduce altura/aumenta anchura, como en el escritorio normal.
- **SUPER + Shift + backslash** devuelve la ventana enfocada a un grupo de pestañas a pantalla completa, reuniendo todos los paneles en pestañas.

La división necesita otra pestaña en el grupo enfocado. Se permiten hasta cuatro
paneles: dos pueden estar lado a lado o apilados; tres o cuatro forman una cuadrícula
2×2 (el tercero ocupa toda la fila inferior hasta añadir el cuarto). El cambio de
tamaño ajusta los divisores compartidos. El atajo de retorno restaura un grupo a pantalla completa con una pulsación. Los números siguen el orden de ventanas del compositor, también usado
por la franja. Los atajos de espacios, flotación, movimiento de ventanas y visibilidad
de barra están inactivos. Siguen disponibles lanzadores, cerrar ventana, Centro de
control y Manual. Aprender > Atajos muestra las teclas de Focus mientras está activo.

## Monitores y recuperación

Cada monitor tiene sus ventanas, franja y hasta cuatro paneles. Los atajos de pestañas
actúan en el monitor enfocado; el enfoque direccional puede cruzar a otro monitor
si no hay panel en esa dirección. Conectar un monitor crea su franja. Al desconectarlo,
Hyprland mueve sus ventanas a un monitor disponible y Focus las reúne allí. La
selección de pantallas de la barra normal no limita las franjas de Focus.

Al desactivar Focus se deshacen los grupos y se reparten las ventanas en espacios
numerados, dos por espacio, manteniendo sus monitores actuales. No se guardan las
posiciones anteriores, la geometría flotante ni el estado de pantalla completa de
las aplicaciones. Se admite un escritorio vacío y comandos on/off repetidos. Si
falla el proceso de la franja, siguen funcionando los grupos nativos y el teclado.
Ejecuta `eitr focus off` desde un terminal para recuperar el escritorio sin la franja.
Recargar Hyprland reaplica la preferencia y reúne ventanas nuevas sin deshacer las
divisiones; se restablecen los tamaños de los divisores y la orientación de dos paneles.
Los comandos fallidos muestran el error; vuelve a intentar `eitr focus off` cuando
Hyprland sea accesible. Cerrar un panel permite ampliar los restantes.
