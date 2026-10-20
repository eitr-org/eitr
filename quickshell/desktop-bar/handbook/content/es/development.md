# Herramientas de desarrollo

Principal > Desarrollo agrupa **IA**, **Nube**, **Cuentas de Git**, **Monitorización**, **LazyVim** y **VS Code**. Los selectores de proyectos abren la carpeta elegida en el editor; la integración de temas actualiza los editores compatibles abiertos, incluidas las sesiones de LazyVim.

**Cuentas de Git** configura una identidad predeterminada de GitHub/GitLab, reglas por carpeta, claves SSH y sesiones separadas en las CLI de proveedores. Cada cambio de reglas exige confirmar una vista previa; nunca reescribe remotos de proyectos ni cambia las cuentas globales de las CLI. Consulta [Cuentas Git](handbook:git-accounts).

## Herramientas opcionales

Instalar > Lenguajes de desarrollo y Herramientas JavaScript instala las herramientas que elijas. Java, Flutter y clientes de bases de datos no son necesarios para ejecutar la barra, el lanzador o los temas de EITR. Instalar > Bases de datos ofrece herramientas opcionales. Instalar > Aplicaciones de desarrollo ofrece Bruno, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code y Zed; Instalar > Productividad ofrece 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack y Thunderbird. Los paquetes AUR se descargan y compilan en tu equipo; algunas licencias impiden que EITR los distribuya.

## Aplicaciones web

Instalar > Aplicaciones web > Crear aplicación web pide un nombre y una dirección y añade un acceso que abre el sitio en una ventana propia. El icono se descarga al crearla, solo por HTTP(S). Si el manifiesto es incorrecto o el icono no está disponible, se usa el icono de la página o uno genérico del navegador. No incluyas credenciales en la dirección. Accesos e iconos usan tu directorio de datos XDG, incluido un `XDG_DATA_HOME` personalizado; eliminarlos desde cualquiera de los menús usa la misma ubicación.

Las aplicaciones web necesitan Chrome o Chromium (Instalar > Navegadores); los servicios de streaming con DRM, como Netflix, necesitan Chrome. Elimínalas con Delete en Instalar > Aplicaciones web o en el menú Aplicaciones.

## Asistentes de IA

Desarrollo > IA ofrece un menú para cada asistente instalado: Claude Code, Codex, Gemini CLI, Grok Build y GitHub Copilot CLI. Instálalos desde Instalar > CLI de IA; si no hay ninguno, Desarrollo > IA enlaza allí.

Iniciar una sesión o abrir un proyecto en LazyVim o VS Code pide primero una carpeta bajo `~/Development`: entra en carpetas para profundizar, usa Abrir para elegir la actual y Atrás para subir un nivel o volver al menú desde el nivel superior.

También puedes iniciar Claude Code, Codex, Gemini CLI, Grok Build y GitHub Copilot CLI (`copilot`) por comando. Si falta la herramienta, Eitr explica su función y ofrece la misma instalación que Instalar > CLI de IA. Escribe `yes` para instalar; Intro cancela. Sin terminal interactivo, el comando termina con instrucciones de instalación. Los binarios instalados tienen prioridad sobre estos lanzadores. Inicia sesión desde cada herramienta; Eitr no incluye binarios de asistentes ni credenciales.

Desarrollo > Asistente predeterminado selecciona un asistente instalado en este equipo. **SUPER + Alt + A** lo abre en un terminal; si no hay uno predeterminado, abre el selector. Eitr mantiene las solicitudes normales de permiso de cada asistente.

Al cambiar el tema, Eitr solo actualiza el ajuste claro/oscuro de los archivos existentes y legibles de Claude Code, Gemini CLI y Grok Build. Conserva las demás opciones y el formato. Omite clientes no instalados y archivos ausentes o dañados; los asistentes sin ajuste claro/oscuro compatible usan los colores del terminal.

Las versiones instaladas de los SDK y las fuentes de los instaladores se mantienen en los manifiestos de la distribución. Consulta el selector actual: un ejemplo del manual no promete la última versión del proyecto original. La instalación puede necesitar descargas.

## Monitorización

Desarrollo > Monitorización deja tus paneles al alcance de una búsqueda. **Añadir panel** pide el servicio (Grafana, Datadog, Sentry, New Relic, Prometheus u Otro), un nombre y su dirección. Después, el menú abre el panel en el navegador. Se guardan solo en este equipo, en `~/.config/eitr/monitoring.json`; Delete elimina uno. Nunca incluyas contraseñas ni tokens en una dirección.

**Herramientas de monitorización** instala utilidades de línea de comandos: `promtool` de Prometheus y la Sentry CLI. Los espacios de trabajo de Amazon Managed Grafana están en Nube > AWS > tu cuenta > Grafana, junto a las demás herramientas AWS.

## Cuentas y flujos de nube

El uso de IA requiere un cliente instalado y configurado; inicia sesión con su procedimiento habitual. Las cuotas y la facturación de API o empresarial pueden diferir de los paneles compatibles para cuentas personales. EITR no incluye credenciales.

Los menús de nube usan tus cuentas y perfiles locales. Los perfiles AWS vienen de la configuración local de AWS o del mapeo de perfiles de EITR. Google Cloud muestra configuraciones de gcloud con nombre, cuenta y proyecto. Una configuración sin proyecto te pide elegirlo al abrir herramientas de recursos; Iniciar sesión sigue disponible antes de descubrir proyectos. Azure muestra suscripciones habilitadas y sus IDs de inquilino. Selecciona un contexto antes de una herramienta: las de Google Cloud y Azure se buscan dentro del menú del contexto, no en la búsqueda global.

Abrir un contexto de Google elimina sustituciones de proyecto heredadas que no correspondan; las configuraciones sin proyecto piden uno para las herramientas de recursos. Al volver de la terminal se conserva el contexto y el proyecto elegido para una configuración sin proyecto, sin cambiar valores globales de las CLI. Iniciar sesión, Comprobar autenticación y Actualizar están en cada contexto detectado. El acceso de Google usa tu cuenta configurada; el de Azure usa su inquilino y restaura la suscripción predeterminada anterior tras autenticarse. Actualizar en Azure renueva la caché de suscripciones y muestra la seleccionada.

Cada menú comienza con **Añadir cuenta AWS**, **Añadir cuenta GCP** o **Añadir cuenta Azure**, para configurar tantas cuentas como necesites, como Desarrollo y Producción de una empresa. Primero pide un nombre y luego ejecuta la configuración de la CLI del proveedor: perfil AWS mediante AWS SSO (IAM Identity Center) o claves de acceso, configuración gcloud independiente con sesión y proyecto, o sesión de Azure cuyas suscripciones nombras. Si falta `gcloud` o `az`, ofrece instalarlo primero. **Ctrl+R** cambia el nombre de una cuenta.

Los nombres se guardan en `~/.config/eitr/cloud-contexts.json`, asociados al perfil AWS, configuración gcloud o ID de suscripción. EITR no deduce entornos ni guarda credenciales allí; Añadir nunca cambia el valor global predeterminado de una CLI. Grafana y las operaciones de nube requieren sus cuentas y permisos correspondientes. Algunas acciones solo consultan datos; otras modifican recursos remotos: revisa la operación y la cuenta antes de confirmar.

Mantén tokens, secretos `.env` y credenciales fuera de dotfiles compartidos y capturas. La configuración del shell carga gestores compatibles sin que los instaladores reescriban tus perfiles. Aprender conserva referencias específicas de LazyVim, tmux y cmux.

## Asistentes trabajando juntos

Desarrollo > IA > Permitir que los asistentes trabajen juntos está desactivado
por defecto. Conecta Claude, Codex, Copilot, Grok y Gemini CLI instalados que
parezcan tener sesión iniciada. Cada transferencia usa la suscripción o
facturación API del auxiliar y cuenta para sus límites. En los otros clientes
no se detectan sesiones solo con clave API o llavero.

Gemini solo se detecta con `GEMINI_API_KEY` o `GOOGLE_API_KEY` no vacía, o
`security.auth.selectedType` con valor `gemini-api-key` o `vertex-ai` en
`~/.gemini/settings.json`. El acceso personal de Google no cuenta: Google ya
no lo sirve. Gemini usa el modo plan sin interfaz, sin servidores MCP ni
extensiones. Eitr todavía no lo ha probado; informa de problemas con Informar
un problema. Queda pendiente una prueba real con clave de pago o cuenta de
empresa. El modo plan está documentado como solo lectura; Eitr no ha verificado
su comportamiento con archivos, shell o archivos de plan.

Pide a tu asistente que consulte al otro para una revisión, explicación o
sugerencia. Aprueba cada transferencia mediante la solicitud normal del
asistente que llama; Eitr nunca autoriza previamente estas herramientas. No
actives la aprobación automática de herramientas del servidor assistants.
Los auxiliares solo leen; las ediciones corresponden al asistente principal.
Un auxiliar no puede llamar a otro. Una notificación identifica quién
consultó a quién y cada solicitud tiene un límite de tres minutos. El
auxiliar lee el directorio de trabajo actual de quien llama; la pregunta y
el contexto pueden enviarse al proveedor de ese asistente.

La opción registra un servidor MCP `assistants` con el comando de cada
asistente (`claude mcp add`, `codex mcp add`, `copilot mcp add` y `grok mcp add`, `gemini mcp add -s user`), así
que cada asistente escribe sus propios ajustes. Un servidor existente con el mismo nombre se
conserva y se notifica. Los cambios se registran solo en este equipo, en
`~/.local/state/eitr/assistants.json` (o `XDG_STATE_HOME`). Desactivar elimina
exactamente las entradas de Eitr; si una entrada se editó después, Eitr la
conserva y notifica el conflicto. Reinicia las sesiones de los asistentes
tras cambiar la opción. La verificación de extremo a extremo con cuentas
reales queda pendiente de una comprobación separada.

Antigravity CLI (`agy`) está disponible para cuentas personales de Google en Instalar > CLI de IA y mediante el lanzador de primer uso. Nunca se incluye en la distribución. Se instala con el instalador oficial de Google, que verifica la descarga, e inicias sesión con tu cuenta de Google. Todavía no se ofrece como auxiliar de asistentes trabajando juntos. Un `agy` ya instalado puede iniciarse normalmente. Gemini CLI requiere una clave de API Gemini o cuenta Google Cloud/empresa. Antigravity no es un auxiliar de colaboración: el modo sin interfaz deniega incluso lecturas. Solo puede desbloquearse omitiendo permisos o cambiando reglas globales. Eitr lo reconsiderará cuando tenga permisos por ejecución o un modo sin interfaz de solo lectura.

### Proveedores adicionales

Desarrollo > Nube también incluye Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify e IBM Cloud (`ibmcloud`). Añade una cuenta con un nombre en minúsculas, dígitos o guiones. Son espacios privados en `~/.config/eitr/cloud-accounts/<provider>/<name>`; nunca se importan configuraciones existentes del proveedor. El proveedor y el espacio seleccionado aparecen en el selector de herramientas y el terminal. Al volver del terminal se conserva el espacio; Escape vuelve a la lista de cuentas. Elegir un espacio nunca cambia el valor global predeterminado de la CLI.

Si faltan, se ofrecen `wrangler`, `doctl` y `hcloud` desde los repositorios oficiales de Arch (`doctl` y `hcloud` en extra). Oracle Cloud e IBM Cloud usan sus instaladores oficiales de shell por HTTPS desde `distro/installers.json`; Oracle recibe `--accept-all-defaults`. Vercel (`vercel`) y Netlify (`netlify-cli`, comando `netlify`) usan la receta existente de NVM/npm. La instalación requiere confirmación. El inicio de sesión y las acciones de cuenta se ejecutan solo en el espacio privado elegido. DigitalOcean y Hetzner enumeran contextos nativos; Oracle enumera perfiles de `~/.oci/config` de ese espacio. La selección de contexto/perfil se guarda localmente y se pasa por comando, sin cambiar valores globales. Vercel y Netlify ofrecen su acción nativa de cambio; después se introduce la etiqueta del equipo/cuenta elegido. Vercel también pide un ámbito después del inicio de sesión y pasa `--scope TEAM` en los comandos posteriores. IBM ofrece acceso por SSO y clave API, muestra `ibmcloud target` y selecciona explícitamente cuenta y región. El contexto/perfil/ámbito/cuenta y la región guardada siguen visibles al volver al menú. Estas etiquetas son selecciones locales, no identidades remotas verificadas. No se heredan credenciales ni variables del proveedor existentes. Las consolas del navegador tienen sesiones propias; comprueba la cuenta antes de actuar. Quedan pendientes las vistas de recursos y la verificación de identidad/proyectos remotos; no se probaron instalaciones ni inicios de sesión reales.

| Proveedor | Inicio de sesión | Lista / cambio / contexto por comando |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

Los informes de recursos de nube usan un paginador para leer; no eligen recursos ni ejecutan operaciones. Las búsquedas de registros y eventos conservan fzf. Las opciones que determinan la siguiente acción siguen en listas Walker.
