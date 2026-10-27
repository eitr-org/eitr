# Seguridad y bloqueo

**SUPER + M** bloquea la pantalla inmediatamente. Haz clic en el icono de Bloqueo automático a la izquierda de la barra (tras Uso de IA) para activar o desactivar el bloqueo por inactividad; su descripción muestra el estado. Activado, la pantalla se bloquea tras 15 minutos de inactividad, se apaga a los 30 y el equipo se suspende a los 60. El Centro de control ofrece el mismo ajuste y un botón Bloquear.

Veinte segundos antes del bloqueo, las pantallas compatibles atenúan su brillo a aproximadamente el 30 % del nivel anterior (nunca a cero). La actividad restaura el nivel anterior exacto, incluso después del bloqueo; desactivar el bloqueo automático también lo restaura. Se omiten los monitores externos sin control de brillo DDC.

## Contraseña y autenticación alternativa

**Sistema > Seguridad > Actualizar contraseña** cambia la contraseña de tu cuenta. Huella digital y FIDO2 tienen procesos separados de registro y activación. Una llave FIDO2 es un dispositivo físico, no el lector de huellas del portátil. Regístrala primero y después activa la autenticación. El auxiliar guarda una copia de los ajustes PAM; conserva una contraseña válida y una forma de acceder a un TTY.

Volver a la autenticación por contraseña restaura el acceso solo mediante contraseña. Estos cambios afectan los servicios PAM compatibles de bloqueo, inicio de sesión y sudo; requieren hardware compatible y los auxiliares instalados. La autenticación por huella puede retrasar brevemente la solicitud de contraseña. Leer esta página no modifica PAM.

## Cortafuegos

Las nuevas instalaciones comienzan con el cortafuegos activado. Rechaza conexiones entrantes salvo las respuestas a conexiones iniciadas por tu equipo, el descubrimiento de nombres locales y las aplicaciones de intercambio que instala Eitr: KDE Connect (puertos 1714-1764) y LocalSend (53317). Las máquinas virtuales y los contenedores de tu equipo siguen pudiendo acceder a él, y el tráfico saliente nunca se filtra. Cuando SSH está habilitado, SSH también se mantiene accesible.

**Sistema > Seguridad > Cortafuegos** muestra si está encendido y lo cambia después de confirmar. Los equipos configurados antes de que existiera el cortafuegos comienzan con él apagado. Para permitir que otra aplicación acepte conexiones, añade un archivo a `/etc/eitr/firewall.d/`, por ejemplo `game.nft`, con este contenido:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

luego apaga el cortafuegos y vuelve a encenderlo.

## Cifrado de discos y TPM

El cifrado de discos es una opción del instalador. Desbloqueo del disco mediante TPM puede agregar una ranura TPM2 a una raíz LUKS2 compatible; el instalador no lo registra automáticamente. Guarda la contraseña y la clave de recuperación sin conexión. Nunca las guardes en capturas de pantalla o archivos de repositorio. Los cambios de firmware/Secure Boot pueden requerir la contraseña en el próximo arranque.

Lee [Recuperación e instantáneas](handbook:recovery) antes de cambiar la autenticación o configuración de TPM. [Secure Boot](handbook:secure-boot) es un proceso avanzado, manual: EITR no registra claves en el firmware ni firma archivos de arranque por ti. Un error puede impedir el arranque e incluso el acceso a la configuración del firmware en algunos equipos.
