# Encontrar un ajuste

Pulsa **SUPER + ,** para abrir Configuración. Sistema es la vista general, no una carpeta con todos los ajustes.

Busca un ajuste individual, como **Tamaño del puntero**, o una página en la barra lateral de Ajustes. Los resultados muestran la página y la pestaña debajo del nombre. Usa Arriba/Abajo y Entrar, o haz clic, para abrir la pestaña, desplazar hasta el control y resaltarlo brevemente. Escape borra primero la búsqueda. Con movimiento reducido, el resaltado aparece y desaparece sin fundido.

<!-- eitr-figure: settings-window -->

La ventana de Configuración tiene una barra lateral con búsqueda y tarjetas para controles relacionados. Permanece abierta al pulsar fuera. Ciérrala con Escape, su botón de cierre o el atajo habitual para cerrar ventanas.

Los enlaces al pie de los paneles cierran el panel y abren la página correspondiente de Configuración. Todos los ajustes en el Centro de control hace lo mismo; **SUPER + I** abre los controles rápidos. Consulta [Centro de control](handbook:control-center).

Elige Colores de Ajustes en Configuración > Apariencia > Tema y fondo de pantalla: Colores del tema sigue el escritorio; Sitio web de Eitr usa la paleta del sitio. Afecta a Configuración, el Manual y Eitr Store, no al tema del escritorio. Walker > Configuración > Escritorio > Apariencia > Colores de Configuración abre esta opción.

El catálogo separado Eitr Store se abre con SUPER + F2 o Más temas en Apariencia.

## Elegir una página

Usa los siguientes nombres de página. Los capítulos enlazados explican los pasos.

| Página | Más información |
| :--- | :--- |
| Sistema | [Sistema](handbook:information) |
| Pantallas — Pantallas, Luz nocturna | [Pantallas](handbook:devices) |
| Sonido | [Sonido](handbook:devices) |
| Conexiones — Wi-Fi, Bluetooth | [Conexiones](handbook:connectivity) |
| Streaming | [Streaming](handbook:remote-access) |
| Entrada | [Entrada](handbook:devices) |
| Apariencia — Tema y fondo de pantalla, Fuentes y cursor, Terminal | [Apariencia](handbook:appearance) |
| Barra del escritorio | [Barra del escritorio](handbook:desktop-bar) |
| Ventanas | [Ventanas](handbook:appearance) |
| Pantalla de bloqueo | [Pantalla de bloqueo](handbook:appearance) |
| Notificaciones | [Notificaciones](handbook:information) |
| Focus | [Focus](handbook:focus) |
| Asistente de IA | [Asistente de IA](handbook:development) |
| Atajos de teclado | [Atajos de teclado](handbook:shortcuts) |
| Reglas de ventanas | [Reglas de ventanas](handbook:apps) |
| Apps predeterminadas | [Apps predeterminadas](handbook:apps) |
| Usuarios | [Usuarios](handbook:security) |
| Seguridad | [Seguridad](handbook:security) |
| Actualizaciones | [Actualizaciones](handbook:maintenance) |
| Comprobar este PC | [Comprobar este PC](handbook:troubleshooting) |
| Acerca de | [Acerca de](handbook:information) |

## Cambiar tu foto de perfil

Abre Configuración > Usuarios (o pulsa tu foto en el resumen Sistema de Configuración) y pulsa tu foto. El selector de archivos del sistema se abre flotante y centrado sobre Configuración, mostrando solo imágenes; al elegir una, el editor de recorte se abre en una hoja sobre Configuración. Arrastra la vista circular para mover la imagen; usa la rueda, el deslizador o +/− para ampliar de 1× a 4×, y las flechas para moverla.

Guardar (o Enter) aplica el recorte; Cancelar o Escape cierra la hoja sin aplicarlo. El icono de papelera debajo de tu foto la quita después de confirmar.

La foto siempre aparece como un círculo en el Centro de control, el bloqueo y el inicio de sesión. El Centro de control solo muestra la foto en la parte superior de su navegación; sin foto no muestra nada ahí, igual que el bloqueo y el inicio de sesión. Configuración muestra en su lugar la inicial de tu nombre sobre un círculo del color de acento.

Se aceptan PNG, JPEG, WebP, GIF (primer fotograma) y BMP hasta 40 MB y 12000 píxeles por lado. Eitr aplica la orientación, elimina metadatos, guarda un PNG de 512×512 en `~/.face` y actualiza AccountsService para SDDM. Si falla la actualización, la foto guardada sigue funcionando en el bloqueo; la interfaz o CLI muestra el error del inicio de sesión.

## Cambiar tu contraseña

Abre Configuración > Usuarios y elige Cambiar contraseña junto a tu nombre. Escribe tu contraseña actual y luego la nueva dos veces: Intro pasa al campo siguiente y confirma en el último; Escape cancela. Las reglas de contraseñas del sistema deciden qué se acepta, y una contraseña rechazada muestra el motivo. Eitr también cambia el llavero de inicio de sesión a la nueva contraseña, para que las contraseñas guardadas se sigan desbloqueando al iniciar sesión. La frase de cifrado del disco es independiente y no cambia. Walker > Configuración > Seguridad > Actualizar contraseña hace lo mismo en un terminal.

## Administrar cuentas

Los administradores tienen las pestañas **Usuarios** y **Administrar** en Configuración > Usuarios. Las cuentas estándar solo ven la lista de usuarios. Administrar ofrece Crear usuario…, Cambiar tipo, Establecer contraseña de otras cuentas y Eliminar con una opción para la carpeta personal. Confirma en la hoja y después pulsa Enter en el terminal de tareas para continuar o Esc para cancelar; introduce contraseñas solo en ese terminal. Las carpetas personales se conservan por defecto. Consulta [Cuentas de usuario](handbook:security) para conocer los permisos, las limitaciones del llavero y las protecciones de eliminación.

## Usar Walker como alternativa

**SUPER + F** abre Walker. Su menú Configuración sigue los grupos de la aplicación Configuración: Dispositivos, Escritorio, Apps y teclas, Cuentas y seguridad y Sistema, con Centro de control y Dotfiles al final. Apps y teclas abre las páginas Apps predeterminadas y Atajos de teclado de la aplicación Configuración.

<!-- eitr-figure: launcher -->

El menú Configuración de Walker es una alternativa con sus propias carpetas. > abre un submenú; la descripción bajo una acción explica qué hace.

Walker muestra carpetas antes que acciones. Escribe para buscar, pulsa Enter para abrir y Shift + Backspace para volver. El idioma se elige en Walker > Configuración > Dispositivos > Idioma; consulta [Idioma](handbook:language).
