# Encontrar un ajuste

Pulsa **SUPER + ,** para abrir Configuración. Escribe en la búsqueda lateral para encontrar una página; la pestaña correspondiente se abre directamente. Sistema es la vista general, no una carpeta con todos los ajustes.

<!-- eitr-figure: settings-window -->

La ventana de Configuración tiene una barra lateral con búsqueda y tarjetas para controles relacionados. Permanece abierta al pulsar fuera. Ciérrala con Escape, su botón de cierre o el atajo habitual para cerrar ventanas.

Los enlaces al pie de los paneles cierran el panel y abren la página correspondiente de Configuración. Todos los ajustes en el Centro de control hace lo mismo; **SUPER + I** abre los controles rápidos. Consulta [Centro de control](handbook:control-center).

Elige Colores de Ajustes en Configuración > Apariencia > Tema y fondo de pantalla: Colores del tema sigue el escritorio; Sitio web de Eitr usa la paleta del sitio. Afecta a Configuración, el Manual y Temas y plugins, no al tema del escritorio.

El catálogo separado Temas y plugins se abre con SUPER + F2 o Más temas en Apariencia.

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
| Apps predeterminadas | [Apps predeterminadas](handbook:apps) |
| Usuario | [Usuario](handbook:security) |
| Git y nube | [Git y nube](handbook:git-accounts) |
| Seguridad | [Seguridad](handbook:security) |
| Actualizaciones | [Actualizaciones](handbook:maintenance) |
| Comprobar este PC | [Comprobar este PC](handbook:troubleshooting) |
| Acerca de | [Acerca de](handbook:information) |

## Cambiar tu foto de perfil

Abre Configuración > Usuario (o pulsa tu foto en el resumen Sistema de Configuración) y elige Cambiar foto. El selector de archivos del sistema se abre flotante y centrado sobre Configuración, mostrando solo imágenes; al elegir una, el editor de recorte se abre en una hoja sobre Configuración. Arrastra la vista circular para mover la imagen; usa la rueda, el deslizador o +/− para ampliar de 1× a 4×, y las flechas para moverla.

Guardar (o Enter) aplica el recorte; Cancelar o Escape cierra la hoja sin aplicarlo. Eliminar, junto a Cambiar foto, elimina la foto.

La foto siempre aparece como un círculo en el Centro de control, el bloqueo y el inicio de sesión. El Centro de control solo muestra la foto en la parte superior de su navegación; sin foto no muestra nada ahí, igual que el bloqueo y el inicio de sesión. Configuración muestra en su lugar la inicial de tu nombre sobre un círculo del color de acento.

Se aceptan PNG, JPEG, WebP, GIF (primer fotograma) y BMP hasta 40 MB y 12000 píxeles por lado. Eitr aplica la orientación, elimina metadatos, guarda un PNG de 512×512 en `~/.face` y actualiza AccountsService para SDDM. Si falla la actualización, la foto guardada sigue funcionando en el bloqueo; la interfaz o CLI muestra el error del inicio de sesión.

## Usar Walker como alternativa

**SUPER + F** abre Walker. Su menú Configuración conserva carpetas como Estilo, Dispositivos y entrada y Sistema. Son rutas de Walker, no páginas de la aplicación Configuración.

<!-- eitr-figure: launcher -->

El menú Configuración de Walker es una alternativa con sus propias carpetas. > abre un submenú; la descripción bajo una acción explica qué hace.

Walker muestra carpetas antes que acciones. Escribe para buscar, pulsa Enter para abrir y Shift + Backspace para volver. El idioma se elige en Walker > Configuración > Idioma; consulta [Idioma](handbook:language).
