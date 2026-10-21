# Aplicaciones e instalación

Antes de instalar paquetes oficiales, el terminal indica que está buscando actualizaciones pendientes del sistema. Esta comprobación puede tardar un poco antes de pedirte la contraseña de administrador. Las instalaciones con Flatpak también muestran su etapa de preparación.

**SUPER + Space** y Principal > Aplicaciones abren la misma lista. Enter inicia una aplicación. Delete está disponible en Aplicaciones y pide confirmar la desinstalación. La búsqueda global con **SUPER + F** abre aplicaciones sin ofrecer desinstalarlas. No hay un menú separado de aplicaciones fijadas.

Escribir en el menú principal busca aplicaciones instaladas y acciones de todos los submenús. Dentro de un submenú, como Sistema o Instalar, busca en él y todos sus descendientes. Las filas de submenú terminan en **>**; **Shift + Backspace** vuelve al menú superior.

## Instalar

Pulsa Delete en una entrada instalada de las listas de aplicaciones y herramientas de Instalar para desinstalarla tras confirmar. Aplicaciones web conserva su acción de eliminación. Paquetes (Pacman y Yay) sigue siendo solo para instalar, sin acción Delete. Nunca se eliminan dependencias necesarias del sistema de forma recursiva; pacman rechaza las eliminaciones que romperían otro paquete.

Los paquetes de lenguajes gestionados muestran el aviso completo de eliminación en un terminal antes de pedir confirmación con [y/N]; Enter cancela. Eliminar Node incluye todas las versiones gestionadas por NVM y sus herramientas npm globales. Eliminar Python afecta a las versiones gestionadas por uv y al propio uv, no a Python del sistema. Java elimina las versiones actuales de Java y Maven en SDKMAN; Rust elimina solo su cadena de herramientas estable. Rails y Laravel eliminan sus herramientas de framework y conservan Ruby, PHP y Composer. Se conservan tus proyectos, la configuración y las credenciales, pero algunas herramientas y entornos dependientes podrían dejar de funcionar. La eliminación de asistentes nativos conserva las versiones en caché y la configuración.


Las aplicaciones presentes muestran **Instalado** bajo el nombre; elegirlas lo indica en vez de reinstalarlas. También se reconocen herramientas instaladas por sus propios gestores, como Java mediante SDKMAN o Node.js mediante NVM. Los paquetes que necesitan un entorno de ejecución, como Java para DBeaver, añaden uno pequeño solo si ningún paquete lo proporciona aún.

- **CLI de IA:** clientes opcionales de IA por línea de comandos.
- **Navegadores:** opciones compatibles de navegador.
- **Bases de datos:** herramientas opcionales como DBeaver, clientes de bases de datos y Valkey, el servidor compatible con Redis que Arch distribuye en su lugar.
- **Lenguajes de desarrollo:** herramientas opcionales; Java/Flutter no son dependencias obligatorias del escritorio.
- **Herramientas de JavaScript:** entornos de ejecución y herramientas opcionales de JavaScript.
- **Paquetes > Pacman** y **Paquetes > Yay (AUR):** busca paquetes oficiales de Arch o comunitarios de AUR, indicando origen y estado de instalación. La búsqueda está arriba, los paquetes debajo y los detalles de la selección al final. **Ctrl+B** alterna al archivo de compilación (PKGBUILD), **Ctrl+O** abre su página en el navegador, **Tab** selecciona varios y **Enter** instala. Los paquetes de AUR se compilan en este equipo a partir de ese archivo: revísalo primero. No son paquetes oficiales de Arch.

Las terminales de instalación, actualización y configuración muestran el banner de EITR con el tema actual. Las tareas correctas suelen cerrarse; los fallos quedan visibles. Informes como Limpieza permanecen abiertos para leerlos. Las terminales normales y Acerca de no muestran el banner.

Pulsa **Esc** para cerrar los terminales de tareas, cuentas, informes y Acerca de que esperan una tecla. Enter sigue sirviendo para respuestas y confirmaciones, como confirmar que has anotado la clave de recuperación y apagar el instalador.

## Herramientas

**Calculadora** en Aplicaciones, o la tecla de calculadora, abre la calculadora de Eitr con los colores del tema. Escribe o pulsa: `+ − × ÷`, `^` para potencias, `%` para porcentaje (`200×15%`), `√` y paréntesis. Un número antes de un paréntesis multiplica (`2(3+4)`). Enter muestra el resultado, Backspace borra un carácter, Escape limpia (dos veces cierra) y Ctrl+C o **Copiar** copia el resultado. Calcula la expresión sin ejecutarla como código.

**Dictado sin conexión** convierte voz a texto sin enviarla fuera del equipo. Mantén **SUPER + D**, habla y suelta: las palabras se escriben en el cursor, en el idioma hablado. Al escuchar, el punto rojo a la izquierda del reloj se convierte en una pequeña onda que sigue tu voz para confirmar que la capta; al soltar, pulsa hasta escribir el texto. El primer uso descarga una sola vez el modelo de voz (148 MB, comprobado con su checksum publicado) en `~/.local/share/eitr/whisper/`; después funciona sin conexión. Transcribir tarda un momento al soltar, más con procesadores antiguos.

**Principal > Herramientas > Recordatorios > Nuevo recordatorio** pide cuándo (un intervalo como `10m` o `1h30m`, o una hora como `18:30`) y el contenido; muestra entonces una notificación que permanece hasta descartarla. **Próximos recordatorios** lista los pendientes; elige uno para cancelarlo. Sobreviven a reinicios; los vencidos con el equipo apagado aparecen al iniciar sesión. En la terminal: `eitr remind 25m Take the tea out`; `eitr remind` solo los lista.

## Juegos

Principal > Juegos muestra **GeForce NOW**, **RetroArch** y **Steam**. Elegir uno lo abre si está instalado, o lo instala si no. RetroArch viene de los paquetes oficiales de Arch con núcleos para NES, SNES, Game Boy y Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP y Dreamcast. Añade tus juegos y, cuando una consola los requiera, sus archivos BIOS; Eitr no distribuye ninguno. GeForce NOW se instala con Flatpak.

**Alternar > Modo de juego** reduce interferencias del escritorio: desactiva animaciones, desenfoque y sombras, aplaza notificaciones emergentes (No molestar) y activa el perfil de rendimiento cuando existe. Desactivarlo restaura exactamente sus cambios. Steam incluye **GameMode** y **MangoHud**: añade `gamemoderun mangohud %command%` a las opciones de lanzamiento del juego en Steam para optimizar la CPU y mostrar la superposición de FPS.

El paquete de LocalSend incluye sus requisitos de ejecución; no necesitas Flutter SDK solo para usarlo. Las herramientas de desarrollo siguen siendo opcionales.

Consulta [Actualizaciones y limpieza](handbook:maintenance) para actualizar; instalar un paquete no equivale a la Actualización del sistema protegida por instantáneas.

**Visualizador de música** en **Principal > Herramientas** abre cava con los colores del tema. Haz clic derecho en el ecualizador multimedia para abrirlo; el clic izquierdo sigue abriendo los detalles multimedia. Pulsa **q** o **Esc** para cerrarlo. Si falta cava, se instala primero.

## Recordatorios por voz

Mantén **SUPER + Shift + D**, habla y suelta, o escribe en Principal > Herramientas > Recordatorios > Dile al asistente…. Eitr transcribe localmente con el modelo sin conexión del dictado y consulta al asistente elegido en Desarrollo > Asistente predeterminado. Solo la transcripción y el contexto de los recordatorios van a su proveedor; el audio queda local y se elimina tras transcribirlo. El asistente funciona sin ventana por la vía de solo lectura de Eitr. Eitr valida su JSON y ejecuta las acciones; el asistente no recibe herramientas para cambiar nada.

Di «Recuérdame llamar mañana a las 15:00» o «Dentista el 30 de octubre a las 15:00, avisa 30 minutos antes». Las citas avisan una hora antes por defecto (o con el margen indicado) y a la hora del evento; los recordatorios simples solo a su hora. Si faltan datos o hay ambigüedad, se abre un terminal con opciones numeradas completas. Escribe el número o díctalo con SUPER + D; Esc cancela. Una notificación muestra el resultado. También puedes pedir listar o cancelar recordatorios.

Nuevo recordatorio acepta `tomorrow 15:00`, días de la semana en inglés (09:00 sin hora), `2026-10-30 09:00` y `Oct 30 15:00`. Pon entre comillas las fechas con espacios en la CLI. Cada aviso tiene su temporizador; cancelar los elimina todos. Los avisos perdidos aparecen al iniciar sesión. El calendario marca los días con eventos; pulsa un día para ver horas y títulos, actualizados al instante. Aún no hay repetición ni sincronización con calendarios externos.
