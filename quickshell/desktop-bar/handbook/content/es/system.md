# Orientarte en Sistema

Abre **SUPER + F > Sistema**. Las acciones se agrupan alfabéticamente; la búsqueda global las encuentra directamente sin recorrer cada grupo.

## Conectividad

**Bluetooth**, **Servicio de red**, **WiFi**. Las entradas de dispositivos abren los mismos paneles que la barra. Elegir el servicio de red prepara el próximo arranque sin reiniciar la conexión actual.

## Dispositivos y entrada

**Audio**, **Límite de carga de batería**, **Pantalla**, **Teclado**, **Iluminación**, **Micrófono**. El límite de carga requiere firmware de portátil compatible. Pantalla reúne brillo, luz nocturna, selección de monitores y perfiles de energía de portátiles compatibles.

**Iluminación** decide si los cambios de tema recolorean ventiladores, teclados y otros dispositivos OpenRGB. Está desactivado por defecto para conservar tu iluminación. Elige **Seguir el tema** para aplicar el color actual y seguir cada cambio de tema.

## Información

**Acerca de**, **Uso de IA**, **Hardware**, **Informar de un problema**, **Tiempo**. Acerca de abre el resumen EITR; Informar de un problema recoge un informe privado que lees antes de enviar. Los demás usan paneles nativos. Calendario y vista de espacios siguen en la barra y la búsqueda global sin llenar este menú. Busca **Ragnarök** para que Fenrir muerda la pantalla; un clic o Escape termina el efecto antes.

## Mantenimiento

**Limpieza**, **Restablecimiento de fábrica**, **Instantáneas**, **Actualización**. Actualizar ofrece la actualización del sistema y el canal de actualización. El restablecimiento de fábrica es destructivo y exige dos advertencias: lee antes [Restablecimiento de fábrica](handbook:factory-reset).

## Seguridad

**Llave de seguridad FIDO2**, **Huella digital**, **Desbloqueo del disco mediante TPM**, **Cortafuegos**, **Volver a la autenticación de contraseña**, **Actualizar contraseña**. La documentación de Secure Boot está en **Aprender > Manual de EITR > Secure Boot**, no en una acción separada del menú o de seguridad.

## Dotfiles

Abre tu carpeta de configuración en VS Code o en LazyVim si VS Code no está instalado. Guarda los ajustes de monitores y hardware propios del equipo en `~/.config/hypr/local.lua`, no en los valores compartidos. No pegues tokens, claves de recuperación ni contraseñas en copias de configuración.

Los capítulos siguientes detallan los procesos y límites de seguridad.

## Idioma

**Walker > Sistema > Idioma** enumera los idiomas, con el actual marcado; consulta la [Guía de idioma](handbook:language). Puedes buscar los nombres ingleses y traducidos. Primero aparecen los submenús y después las acciones, ordenados por sus títulos traducidos. Principal y Aplicaciones conservan su orden.
