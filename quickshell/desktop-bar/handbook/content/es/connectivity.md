# WiFi, Bluetooth y modo avión

Abre Configuración > Conexiones y elige Wi-Fi o Bluetooth. Los iconos de la barra abren paneles rápidos para los mismos dispositivos. Abrirlos no cambia el servicio de red ni desconecta nada.

## Conectarte a Wi-Fi

Abre Configuración > Conexiones > Wi-Fi, activa Wi-Fi y elige una red en Otras redes. Introduce su contraseña si se solicita. Buscar vuelve a explorar. Red conectada muestra la conexión actual; Redes conocidas conserva las redes guardadas, incluso sin conexión. Desconectar termina la conexión; Olvidar elimina una red guardada tras confirmar. El progreso y los errores aparecen junto a la red.

La parte superior muestra estado, ping, banda WiFi, dirección IP y puerta de enlace. Compartir mediante QR usa una contraseña WiFi proporcionada y mantiene la imagen en memoria. Las credenciales empresariales no se comparten como un QR de red personal.

Admite PEAP/MSCHAPv2 y TTLS/PAP para redes empresariales. Pide al administrador usuario, certificado de la autoridad certificadora y dominio del servidor de autenticación. No desactives la validación del certificado. Otros métodos requieren configuración avanzada. Consulta [Servicios de red](handbook:network-backends).

Elige el servicio WiFi en Configuración > Conexiones > Wi-Fi > Backend WiFi; Walker > Configuración > Conectividad > Servicio de red es una alternativa. Lee [Servicios de red](handbook:network-backends) antes de cambiar. Se aplica tras reiniciar y mantiene la conexión actual.

## Emparejar un dispositivo Bluetooth

Abre Configuración > Conexiones > Bluetooth y actívalo. Elige Buscar y selecciona un dispositivo para emparejarlo y conectarlo. Dispositivos conectados, Dispositivos conocidos y Otros dispositivos son listas separadas. Usa Mostrar dispositivos sin nombre si el tuyo no tiene nombre. Desconectar conserva el emparejamiento; Olvidar lo elimina. La búsqueda termina a los 20 segundos, al salir de la página o al cerrar el panel.

Emparejar puede requerir un PIN o un agente de confirmación. El escritorio actual usa el agente Blueman para esos diálogos. Reconectar un dispositivo ya emparejado no demuestra que funcione un emparejamiento nuevo. Mantén ese agente hasta probar un emparejamiento con PIN o confirmación. La cobertura del agente en instalaciones nuevas sigue pendiente de comprobar.

## Modo avión

Centro de control > General bloquea WiFi y Bluetooth mediante rfkill. Desactivarlo restaura solo las radios que bloqueó. Los bloqueos físicos o externos no se anulan silenciosamente. Activa una radio individualmente si hace falta.

## VPN

Abra Install > VPN para Tailscale, WireGuard o NetworkManager VPN. Tailscale conserva su panel de acceso remoto y su configuración.

WireGuard instala el paquete oficial `wireguard-tools` mediante la comprobación habitual de actualizaciones pendientes. Importe una configuración indicando el nombre y la ruta completa de un archivo `.conf`; revise nombre, destinos y cantidad de pares. Nunca se muestran claves. Se rechazan hooks ejecutables y SaveConfig. Con NetworkManager se importa allí; con iwd se guarda de forma privada en `/etc/wireguard` para wg-quick, sin sobrescribir perfiles existentes.

NetworkManager VPN instala `networkmanager-openvpn` y `networkmanager-openconnect`. NetworkManager incluye WireGuard sin otro complemento. Con iwd se explica el requisito y se abre la selección existente del servicio, sin cambiarlo. Consulte [Servicios de red](handbook:network-backends). La importación acepta `.ovpn` para OpenVPN y archivos compatibles con el importador OpenConnect. Los errores no muestran el contenido.

Los perfiles permanecen desconectados salvo que elija conectarlos tras importar. La conexión automática al arrancar está desactivada. Vuelva al menú y elija conectar o desconectar con el nombre guardado. No se añade un control VPN al centro de control. Las pruebas usan simulaciones; no se han verificado conexiones reales en hardware.
