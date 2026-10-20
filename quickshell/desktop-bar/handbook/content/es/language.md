# Idioma

Eitr sigue el idioma de los mensajes del sistema. **Centro de control > Sistema > Idioma** muestra el idioma que se usa para la configuración regional actual y abre un selector de idioma; **Walker > Sistema > Idioma** enumera las mismas opciones, con la actual marcada. Elige un idioma o **Predeterminado del sistema** y cierra la sesión y vuelve a iniciarla. Eitr nunca cierra tu sesión automáticamente.

Eitr comprueba **LC_ALL**, después **LC_MESSAGES** y, por último, **LANG**. Las variables vacías se ignoran. `LC_MESSAGES` cambia los mensajes sin modificar los formatos de fecha, números o moneda; `LC_ALL` reemplaza todas las categorías regionales y normalmente se deja sin definir. `C`, `POSIX` y los idiomas no disponibles usan inglés. Los mensajes sin traducción aparecen en inglés; los capítulos que faltan utilizan el capítulo completo en inglés.

## Cambiar el idioma del sistema

Si también necesitas cambiar los ajustes de todo el sistema, usa su configuración regional. En Arch Linux, habilita la configuración regional que quieras en `/etc/locale.gen` y genera las configuraciones instaladas con `sudo locale-gen`. Después, establece el idioma en `/etc/locale.conf`, por ejemplo:

```text
LANG=pt_BR.UTF-8
```

Los idiomas iniciales son `pt_BR.UTF-8` (portugués brasileño), `es_ES.UTF-8` (español), `de_DE.UTF-8` (alemán) y `fr_FR.UTF-8` (francés). Las variantes regionales pueden utilizar la traducción del idioma base. Ejecuta `locale` en un terminal para comprobar las variables que reemplazan la configuración y `locale -a` para listar las configuraciones instaladas. Cierra sesión y vuelve a entrar para aplicar el idioma al escritorio, los menús y los nuevos terminales. El selector solo escribe `~/.config/environment.d/90-eitr-language.conf`: establece `LC_MESSAGES` y vacía `LC_ALL` para la próxima sesión, conservando los formatos de fecha y números. **Predeterminado del sistema** elimina esa preferencia. No modifica `/etc/locale.conf` ni genera configuraciones regionales; las aplicaciones abiertas conservan su idioma actual.

## Contribuir con una traducción

El texto en inglés es la fuente. Los catálogos están en `i18n/catalogs/<locale>/`; edita los valores traducidos y conserva las claves en inglés. Los mensajes de Python y shell usan un único dominio gettext: `eitr`. Conserva los marcadores `%1` y `{name}`, los glifos, los nombres de paquetes, los comandos y las rutas. Las palabras que se escriben para confirmar acciones destructivas deben coincidir con las que acepta la comprobación.

Los capítulos del manual están en `quickshell/desktop-bar/handbook/content/<locale>/<chapter-id>.md`. Conserva los enlaces `handbook:`, los bloques de código y los comandos. Las tablas de teclado y ratón se generan a partir de las fuentes oficiales de los atajos; traduce sus mensajes en el catálogo del manual en vez de mantener otra lista de teclas.

Ejecuta `python3 tools/i18n-build.py --check`, genera el manual con `python3 quickshell/desktop-bar/scripts/handbook-build.py` y ejecuta su opción `--check`, además de `bash tools/check.sh`. Las comprobaciones enumeran los mensajes que faltan y los marcadores modificados. Revisa las traducciones largas en vistas previas fuera de pantalla antes de enviar tu contribución.

Después de traducir por completo un capítulo modificado, actualiza su entrada en `source-hashes.json` con el SHA-256 de la fuente inglesa. La comprobación detecta fuentes modificadas o sin registrar; regenerar los catálogos no confirma los cambios de la fuente.

La fila Predeterminado del sistema muestra el nombre nativo resuelto desde `/etc/locale.conf`: `LC_ALL`, después `LC_MESSAGES` y `LANG`, ignorando valores vacíos. Ignora las sustituciones de la sesión. English fuerza el inglés; Predeterminado del sistema sigue al sistema. Si no se puede leer la configuración regional, conserva la etiqueta simple.
