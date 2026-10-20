# Captura y uso compartido

Las herramientas de captura están en Principal > Herramientas > Captura y Centro de control > Herramientas.

## Capturas de pantalla y extracción

- **Print:** captura completa en el editor flotante.
- **SUPER + Print:** selección congelada en el editor flotante.
- **SUPER + Shift + Print:** captura de la ventana activa en el editor.
- **SUPER + Ctrl + Print:** extraer texto de una selección con OCR.
- **SUPER + Alt + Print:** decodificar un código QR de una selección.
- **SUPER + =:** elegir y copiar un color.

Tras una captura, un breve relámpago ilumina la región capturada. Empieza después de obtener la imagen, por lo que nunca aparece en ella.

Revisa el contenido antes de guardar o compartir. El OCR puede equivocarse; los códigos QR pueden contener credenciales privadas o URL no fiables. Usar un editor no garantiza que se haya eliminado el texto sensible del fondo.

## Grabación y transmisión

Grabación de pantalla abre los controles de OBS. Usan tu escena configurada y el permiso de captura de Wayland guardado; la escena debe incluir una fuente de monitor visible. Iniciar la captura prepara OBS y cierra el panel antes de empezar. Los controles usan WebSocket de OBS, desactivado por defecto: Eitr lo activa con contraseña la primera vez que OBS está cerrado. Si está abierto en ese momento, ciérralo una vez y vuelve a intentarlo.

Las grabaciones se guardan en **Videos/Records** dentro de tu carpeta personal. OBS usa por defecto la propia carpeta personal; Eitr solo cambia ese valor predeterminado y conserva una carpeta que hayas elegido en OBS > Ajustes > Salida.

Mientras OBS graba o transmite, aparece un punto rojo junto al tiempo meteorológico. Pulsa para ver tiempo transcurrido, tamaño de archivo, pausar/reanudar, detener, añadir un marcador de capítulo (requiere Hybrid MP4 de OBS), controlar micrófono y cámara de OBS y elegir escena. Una transmisión muestra un contador LIVE con su propio botón de parada. Al terminar una grabación, la notificación ofrece Abrir carpeta y Copiar ruta. Revisa las opciones de audio/micrófono y el monitor antes de comenzar. La cámara requiere una fuente de cámara en OBS. Los interruptores de audio de grabación afectan a las entradas de OBS, no al volumen del sistema.

El manual nunca inicia grabaciones ni transmisiones. Compartir y capturar la pantalla siguen siendo acciones explícitas. Transcodificar abre el flujo existente de conversión de imágenes y vídeos; revisa las rutas de salida antes de sustituir archivos.

OBS pregunta una vez qué pantalla grabar. En el selector habitual de pantalla compartida, **Allow restore token** está marcado por defecto para que OBS pueda recordar tu elección. La pantalla guardada no sigue el ajuste de pantalla principal de la barra. Los archivos `~/.config/hypr/xdph.conf` existentes se conservan, por lo que tu configuración del portal puede cambiar este comportamiento.

En una configuración nueva de OBS, Eitr crea la colección Untitled con una Scene: captura de pantalla, cámara oculta y audio predeterminado del escritorio y del micrófono. En el primer uso, el sistema te pregunta qué pantalla compartir; OBS guarda ese permiso. La cámara permanece apagada hasta que la actives. Las colecciones existentes nunca se modifican.

## Compartir

Principal > Herramientas > Compartir ofrece LocalSend y las herramientas de transferencia existentes. Enviar un archivo requiere elegir destino o dispositivo. Comprueba los destinatarios y evita compartir claves privadas, códigos de recuperación, tokens o una carpeta personal/de configuración completa sin revisar.
