# WiFi, Bluetooth y modo avión

Abre los iconos de la barra o **Sistema > Conectividad**. Abrir un panel nunca cambia el servicio de red ni desconecta un dispositivo por sí solo.

## WiFi

El panel separa las redes conectadas, conocidas y otras redes. Elige una disponible para conectar; los campos de contraseña ocultan su contenido. Las redes guardadas sin conexión siguen visibles, sin un porcentaje de señal inventado. Desconectar está en la fila conectada; olvidar una red guardada pide confirmación.

La parte superior muestra estado, ping, banda WiFi, dirección IP y puerta de enlace. Compartir mediante QR usa una contraseña WiFi proporcionada y mantiene la imagen en memoria. Las credenciales empresariales no se comparten como un QR de red personal.

Admite PEAP/MSCHAPv2 y TTLS/PAP para redes empresariales. Pide al administrador usuario, certificado de la autoridad certificadora y dominio del servidor de autenticación. No desactives la validación del certificado. Otros métodos requieren configuración avanzada. Consulta [Servicios de red](handbook:network-backends).

## Bluetooth

Activa o desactiva el adaptador, busca, empareja, conecta, desconecta u olvida dispositivos. Los conectados, conocidos y recién descubiertos se agrupan por separado. La búsqueda iniciada por el panel termina a los 20 segundos o al cerrarlo.

Emparejar puede requerir un PIN o un agente de confirmación. El escritorio actual usa el agente Blueman para esos diálogos. Reconectar un dispositivo ya emparejado no demuestra que funcione un emparejamiento nuevo. Mantén ese agente hasta probar un emparejamiento con PIN o confirmación. La cobertura del agente en instalaciones nuevas sigue pendiente de comprobar.

## Modo avión

Centro de control > General bloquea WiFi y Bluetooth mediante rfkill. Desactivarlo restaura solo las radios que bloqueó. Los bloqueos físicos o externos no se anulan silenciosamente. Activa una radio individualmente si hace falta.
