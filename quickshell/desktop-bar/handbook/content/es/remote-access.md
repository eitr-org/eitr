# Acceso remoto

Abra Configuración > Streaming para Sunshine y Moonlight, o Walker > Configuración > Dispositivos > Streaming para las mismas acciones. Compartir permanece desactivado hasta
que lo active. Se controla la sesión de Eitr iniciada y despierta. El uso sin
monitor, antes del inicio de sesión y wake on LAN quedan para después. Si este equipo
se bloquea mientras comparte, la pantalla remota muestra la pantalla de bloqueo:
quien esté conectado la ve y puede escribir la contraseña. Deje de compartir
antes de ausentarse si necesita privacidad.

Las carpetas de configuración agrupan los ajustes. Streaming > Configuración para compartir contiene Configurar uso compartido, Ajustes de uso compartido, Iniciar al entrar, Desactivar inicio al entrar, Estado detallado y Restaurar configuración de uso compartido. Las acciones habituales de uso compartido (Iniciar uso compartido, Detener uso compartido, Emparejar un dispositivo, Estado del uso compartido y Conectar a otro PC) siguen directamente en Streaming. Tailscale es el plugin oficial de Tailscale, con su propio panel en la barra.

Estado detallado abre un terminal de diagnóstico que permanece abierto hasta que pulses Esc.

## Sunshine en Eitr

En Compartir este PC elija Configurar uso compartido. El responsable de la versión compila el
paquete nativo firmado de Eitr desde las fuentes oficiales; no se compila AUR al
primer clic. Flatpak y AppImage no permiten captura KMS. Se conservan los ajustes
y dispositivos emparejados. No ejecute otra instancia a la vez.

Lea el aviso de control total y escriba `yes` solo si acepta captura KMS y entrada
virtual de teclado, ratón y mando. El estado original se guarda en
`/var/lib/eitr/remote-access`. Se añade una regla udev para uinput, se carga uinput
al arrancar, se concede acceso al usuario y se aplica `cap_sys_admin+p` a Sunshine.

Restaurar configuración de uso compartido restaura los archivos y la ACL originales y elimina los permisos de captura. Si la configuración cargó uinput, la restauración también lo descarga. Si otra
aplicación lo usa, se informa del fallo y se conserva el registro para cerrar
la aplicación y reintentar.

Iniciar uso compartido pide confirmación y abre `https://localhost:47990`. Acepte el
certificado local autofirmado solo en esa dirección. Defina usuario y contraseña
segura antes de emparejar. Abrir ajustes vuelve aquí; Emparejar un dispositivo abre la página
del PIN. Introduzca solo el PIN de su propio Moonlight. Eitr impone `upnp=off`.
No configure redirección de puertos en el router.

TCP 47984, 47989 y 48010 y UDP 47998-48000 solo admiten subredes LAN privadas
directamente conectadas y `tailscale0`. TCP 47990 solo es accesible desde este PC,
aunque otra regla lo permitiese. Las redes se identifican en cada inicio; detenga
y vuelva a iniciar al cambiar de red. Use solo una red doméstica de confianza.

Detener uso compartido también desactiva el inicio automático y cierra los puertos, incluso
las conexiones existentes. Los fallos del servicio los cierran; las aperturas no
sobreviven al reinicio. Tras el primer inicio, Iniciar y Detener uso compartido cambian al instante, sin preguntas ni contraseña. Iniciar al acceder es opcional y cambia al instante desde el panel Streaming o el menú;
Desactivar inicio al acceder mantiene el inicio manual.

Estado del uso compartido muestra errores.

La primera vez, la transmisión permanece bloqueada mientras define la contraseña. Vuelva al terminal y confirme que la ha definido; su contraseña de administrador activa entonces el control remoto.

Una actualización del paquete Sunshine reemplaza el ejecutable y borra su capacidad
de captura; después, la actualización se la devuelve a la cuenta que configuró el uso
compartido. Si aun así no se inicia, el interruptor de Streaming indica el motivo:
vuelva a configurar el uso compartido o cierre sesión y vuelva a entrar tras la primera
configuración. Se conserva el registro original de restauración.

Sunshine usa la capacidad KMS solo como root o con la cuenta que configuró el uso compartido: la configuración establece `root:eitr-sharing`, modo `0750`, y añade tu cuenta al grupo del sistema. Cierra sesión y vuelve a entrar antes de iniciar para actualizar los grupos del servicio de usuario. La configuración mantiene el proceso activo; reiniciarlo antes de volver a entrar puede fallar.

Detener conserva los permisos. Restaurar elimina la pertenencia al grupo y todas las capacidades del ejecutable y restablece `root:root`, modo `0755`, también para registros antiguos. Tras actualizar el paquete, Configurar uso compartido corrige propietario y modo antes de conceder la capacidad.

## Moonlight en un Mac

Instálelo desde [Moonlight](https://moonlight-stream.org/). Para la primera prueba,
use la misma red doméstica. Añada la dirección LAN de Eitr si no se descubre.
Seleccione el PC, lea el PIN y use Emparejar un dispositivo en Eitr. Elija Desktop para
controlar aplicaciones y juegos. Seleccione la pantalla en Sunshine y pruebe ambos
monitores. Gaming > Moonlight y Conectar a otro PC instalan o abren el cliente
en Eitr para conectarse en sentido inverso. Las instalaciones nuevas incluyen estas aplicaciones; compartir permanece desactivado hasta que tú lo actives explícitamente.

Atajos con SUPER desde el Mac: en los ajustes de Moonlight, activa **Capture system keyboard shortcuts** (en pantalla completa o siempre). Solo así Moonlight envía la tecla Comando del Mac como SUPER; si no, los atajos con Comando se quedan en el Mac. Ctrl+Alt+Mayús+K activa o desactiva la captura durante una sesión.

## Tailscale en ambos equipos

Instale el plugin oficial **Tailscale** (Temas y plugins > Plugins) y coloque su icono
desde Centro de control > Plugins. El paso **Configurar** de su panel instala Tailscale,
activa e inicia `tailscaled.service` y nombra operador a su usuario. Por eso iniciar
sesión, conectar y desconectar no piden contraseña. Iniciar sesión abre la página de
acceso de Tailscale en el navegador. El panel muestra la dirección Tailscale de este PC,
cada dispositivo y si su ruta es directa, por relé o inactiva, hace ping a un
dispositivo, envía archivos con Taildrop, abre un informe detallado y deshace la
configuración de Eitr (vuelven el operador y el estado del servicio anteriores; la
cuenta de Tailscale y los paquetes se mantienen).

Las rutas por relé pueden aumentar la latencia y reducir la calidad.

Instale [Tailscale en el Mac](https://tailscale.com/download/mac), acceda a la misma
tailnet y conecte ambos equipos. Añada la dirección Tailscale de Eitr en Moonlight
y use el mismo emparejamiento de Sunshine. La política de la tailnet debe permitir
los puertos de streaming. Los ajustes web de Sunshine siguen siendo locales.

## Qué se ha probado

Las pruebas automáticas usan simulaciones. En un escritorio real (con uno y luego
dos monitores) y un MacBook con Moonlight: configuración, empezar a compartir,
emparejamiento por dirección, imagen, teclado, ratón, audio, la pantalla de bloqueo
(desbloqueada desde el Mac), inicio al iniciar sesión, Dejar de compartir y
Restaurar la configuración en la red de casa, y la configuración, el inicio de
sesión y la conexión de Tailscale desde fuera. No se han probado mandos, otras
tarjetas gráficas ni otros clientes.

Streaming está junto a Conexiones en Dispositivos. Sunshine muestra el estado de uso compartido, configuración, inicio/parada, inicio de sesión, emparejamiento, ajustes, diagnóstico y restauración. Moonlight muestra el estado de instalación y un botón para instalar/abrir. Tailscale es un plugin con su propio panel.
