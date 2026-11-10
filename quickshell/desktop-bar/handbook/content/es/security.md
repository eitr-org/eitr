# Seguridad y bloqueo

**SUPER + M** bloquea la pantalla inmediatamente. Haz clic en el icono de Bloqueo automático a la izquierda de la barra (tras Uso de IA) para activar o desactivar el bloqueo por inactividad; su descripción muestra el estado. Activado, la pantalla se bloquea tras 15 minutos de inactividad, se apaga a los 30 y el equipo se suspende a los 60. El Centro de control ofrece el mismo ajuste y un botón Bloquear.

Veinte segundos antes del bloqueo, las pantallas compatibles atenúan su brillo a aproximadamente el 30 % del nivel anterior (nunca a cero). La actividad restaura el nivel anterior exacto, incluso después del bloqueo; desactivar el bloqueo automático también lo restaura. Se omiten los monitores externos sin control de brillo DDC.

## Contraseña y autenticación alternativa

**Configuración > Usuarios > Cambiar contraseña** cambia la contraseña de tu cuenta y mantiene el llavero de inicio de sesión abriéndose con ella. Huella digital y Llave de seguridad FIDO2 tienen procesos separados de registro y activación. Una llave FIDO2 es un dispositivo físico, no el lector de huellas del portátil. Regístrala primero y después activa la autenticación. El auxiliar guarda una copia de los ajustes PAM; conserva una contraseña válida y una forma de acceder a un TTY.

Volver a la autenticación por contraseña restaura el acceso solo mediante contraseña. Estos cambios afectan los servicios PAM compatibles de bloqueo, inicio de sesión y sudo; requieren hardware compatible y los auxiliares instalados. La autenticación por huella puede retrasar brevemente la solicitud de contraseña. Leer esta página no modifica PAM.

## Solicitudes de la contraseña de administrador

Cuando una aplicación o el propio Eitr necesita permisos de administrador (instalar software, cambiar ajustes del sistema), una solicitud de contraseña con el tema de la barra cubre la pantalla que estás usando. Muestra quién lo pide, qué cuenta se autentica (con una opción para elegir si puede hacerlo más de una) y Detalles de la solicitud con la acción de polkit. Intro autentica; Escape o Cancelar lo rechaza; hacer clic fuera de la solicitud no hace nada. Una contraseña incorrecta muestra un error y permite volver a intentarlo. Varias solicitudes esperan su turno, una a la vez. La contraseña va directamente al sistema y nunca se guarda ni se registra.

Si la barra no puede ofrecer esta solicitud poco después de iniciar sesión, el diálogo de contraseña de KDE la sustituye durante la sesión, para que las peticiones de administrador sigan funcionando.

## Cortafuegos

Las nuevas instalaciones comienzan con el cortafuegos activado. Rechaza conexiones entrantes salvo las respuestas a conexiones iniciadas por tu equipo, el descubrimiento de nombres locales y las aplicaciones de intercambio que instala Eitr: KDE Connect (puertos 1714-1764) y LocalSend (53317). Las máquinas virtuales y los contenedores de tu equipo siguen pudiendo acceder a él, y el tráfico saliente nunca se filtra. Cuando SSH está habilitado, SSH también se mantiene accesible.

**Configuración > Seguridad > Protección > Cortafuegos** muestra si está encendido y lo cambia después de confirmar. Los equipos configurados antes de que existiera el cortafuegos comienzan con él apagado. Para permitir que otra aplicación acepte conexiones, añade un archivo a `/etc/eitr/firewall.d/`, por ejemplo `game.nft`, con este contenido:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

luego apaga el cortafuegos y vuelve a encenderlo.

## Cifrado de discos y TPM

El cifrado de discos es una opción del instalador. Desbloqueo del disco mediante TPM puede agregar una ranura TPM2 a una raíz LUKS2 compatible; el instalador no lo registra automáticamente. Guarda la contraseña y la clave de recuperación sin conexión. Nunca las guardes en capturas de pantalla o archivos de repositorio. Los cambios de firmware/Secure Boot pueden requerir la contraseña en el próximo arranque.

Lee [Recuperación e instantáneas](handbook:recovery) antes de cambiar la autenticación o configuración de TPM. [Secure Boot](handbook:secure-boot) es un proceso avanzado, manual: EITR no registra claves en el firmware ni firma archivos de arranque por ti. Un error puede impedir el arranque e incluso el acceso a la configuración del firmware en algunos equipos.

## Cuentas de usuario

**Configuración > Usuarios > Crear usuario…** crea un acceso independiente. Introduce el nombre de usuario, el nombre completo opcional, el tipo de cuenta y la contraseña; revisa los datos y pulsa Enter para crearla. Esc cancela antes de aplicar. Las cuentas estándar no pueden usar sudo; las de administrador se añaden a wheel y reciben una regla de sudo protegida por contraseña.

La carpeta personal nueva no contiene archivos de tu cuenta. En el primer inicio de Hyprland mediante UWSM, Eitr ejecuta la configuración de escritorio por usuario del instalador y adopta la estructura del paquete con la identidad del nuevo usuario. La configuración de la shell puede necesitar internet. Si falla, conserva el marcador para el siguiente inicio; si termina correctamente, no vuelve a ejecutarse. Los errores de creación dejan la cuenta incompleta bloqueada y caducada para su revisión manual.

Los administradores ven las pestañas **Usuarios** y **Administrar** en Configuración > Usuarios; las cuentas estándar solo ven la lista de usuarios. Un Administrador pertenece a wheel y tiene una regla sudo de Eitr; una cuenta Estándar no tiene ninguna de las dos cosas. Administrar permite crear cuentas, cambiar su tipo, establecer la contraseña de otra cuenta y eliminar cuentas. Cada acción abre una hoja de confirmación y después un terminal de tareas: Enter continúa y Esc cancela. El restablecimiento pide la nueva contraseña dos veces en el terminal; el llavero de inicio de sesión de la otra cuenta no puede actualizarse y conserva su contraseña anterior. Para tu propia cuenta, usa Cambiar contraseña en Usuarios. La eliminación conserva la carpeta personal por defecto; elige Eliminar carpeta personal para borrar sus archivos. No puedes eliminar tu propia cuenta, una cuenta con una sesión activa ni el último administrador; este tampoco puede convertirse en estándar. Solo se gestionan cuentas humanas (UID 1000–65533). La lista se actualiza al volver del terminal.

Las cuentas cuyo grupo principal es wheel no pueden convertirse en estándar aquí; cambia primero su grupo principal mediante administración manual.

## Fotos de perfil

Configuración > Usuarios muestra cada cuenta de este PC. Pulsa allí tu foto para cambiarla, o usa el icono de papelera debajo para quitarla. Consulta [Configuración](handbook:system) para elegir una imagen y recortarla. El Centro de control solo muestra la foto.
