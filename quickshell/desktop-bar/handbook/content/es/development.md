# Herramientas de desarrollo

Principal > Desarrollo agrupa **IA**, **Nube**, **Cuentas de Git**, **Monitorización**, **LazyVim** y **VS Code**. Los selectores de proyectos abren la carpeta elegida en el editor; la integración de temas actualiza los editores compatibles abiertos, incluidas las sesiones de LazyVim.

**Cuentas de Git** configura una identidad predeterminada de GitHub/GitLab, reglas por carpeta, claves SSH y sesiones separadas en las CLI de proveedores. Cada cambio de reglas exige confirmar una vista previa; nunca reescribe remotos de proyectos ni cambia las cuentas globales de las CLI. Consulta [Cuentas Git](handbook:git-accounts).

## Herramientas opcionales

Instalar > Lenguajes de desarrollo y Herramientas JavaScript instala las herramientas que elijas. Java, Flutter y clientes de bases de datos no son necesarios para ejecutar la barra, el lanzador o los temas de EITR. Instalar > Bases de datos ofrece herramientas opcionales. Instalar > Aplicaciones de desarrollo ofrece Bruno, Cursor, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code y Zed; Instalar > Productividad ofrece 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack y Thunderbird. Los paquetes AUR se descargan y compilan en tu equipo; algunas licencias impiden que EITR los distribuya.


Lenguajes también ofrece **mise (muchos entornos)** como paquete opcional de Arch. Actívalo manualmente con `eval "$(mise activate zsh)"` en `~/.zshrc`; puede entrar en conflicto con nvm/uv para el mismo entorno. Los gestores existentes no cambian.

## Aplicaciones web

Instalar > Aplicaciones web > Crear aplicación web pide un nombre y una dirección y añade un acceso que abre el sitio en una ventana propia. El icono se descarga al crearla, solo por HTTP(S). Si el manifiesto es incorrecto o el icono no está disponible, se usa el icono de la página o uno genérico del navegador. No incluyas credenciales en la dirección. Accesos e iconos usan tu directorio de datos XDG, incluido un `XDG_DATA_HOME` personalizado; eliminarlos desde cualquiera de los menús usa la misma ubicación.
Si hay varios perfiles del navegador, al crear una aplicación web se pregunta con qué perfil se abrirá; para cambiarlo, elimina la aplicación y vuelve a añadirla.

Las aplicaciones web necesitan Chrome, Chromium, Edge, Brave o Vivaldi (Instalar > Navegadores); los servicios de streaming con DRM, como Netflix, necesitan Chrome. Elimínalas con Delete en Instalar > Aplicaciones web o en el menú Aplicaciones.

Instalar > Navegadores también ofrece Brave (AUR). Instalar > Productividad ofrece Basecamp y Notion como aplicaciones web opcionales. Las recetas solo contienen un nombre y una URL; el icono del sitio se descarga en tu equipo al instalar. Nada viene preinstalado.

## Asistentes de IA

Cada asistente en la nube tiene un submenú Cuentas en Desarrollo > IA. Predeterminada usa la configuración y el inicio de sesión existentes sin mover archivos. Añadir cuenta… pide un nombre, muestra una revisión y abre el inicio de sesión de la CLI con una ventana privada del navegador cuando es compatible (los navegadores desconocidos usan la apertura normal). Enter confirma; Esc cancela. Seleccione una cuenta para cambiar manualmente las próximas sesiones interactivas, Preguntar a la IA y los asistentes de solo lectura; las sesiones abiertas conservan su cuenta. Delete elimina una cuenta añadida y su configuración local tras confirmar; Predeterminada no se puede eliminar. Eliminar la cuenta seleccionada vuelve a Predeterminada sin cerrar otra sesión. Antigravity solo ofrece Predeterminada porque su CLI no permite cambiar la carpeta de configuración. Ratatoskr tiene una cuenta local. Los nombres y la selección se guardan en este PC en `eitr/ai-accounts.json` (0600); las carpetas separadas están en `$XDG_DATA_HOME/eitr/ai-accounts/` (0700). Uso de IA agrupa las cuentas por asistente y muestra Sin datos si el uso no se puede leer o no es compatible.

Desarrollo > IA ofrece un menú para cada asistente instalado: Claude Code, Codex, Gemini CLI, Grok Build y GitHub Copilot CLI. Instálalos desde Instalar > CLI de IA; si no hay ninguno, Desarrollo > IA enlaza allí.

Iniciar una sesión o abrir un proyecto en LazyVim o VS Code pide primero una carpeta bajo `~/Development`: entra en carpetas para profundizar, usa Abrir para elegir la actual y Atrás para subir un nivel o volver al menú desde el nivel superior.

También puedes iniciar Claude Code, Codex, Gemini CLI, Grok Build y GitHub Copilot CLI (`copilot`) por comando. Si falta la herramienta, Eitr explica su función y ofrece la misma instalación que Instalar > CLI de IA. Enter confirma la instalación; Esc cancela. Sin terminal interactivo, el comando termina con instrucciones de instalación. Los binarios instalados tienen prioridad sobre estos lanzadores. Inicia sesión desde cada herramienta; Eitr no incluye binarios de asistentes ni credenciales.

Desarrollo > Asistente predeterminado selecciona un asistente instalado en este equipo. **SUPER + A** lo abre en un terminal; si no hay uno predeterminado, abre el selector. Los asistentes interactivos se abren con acceso completo por defecto: pueden cambiar archivos y ejecutar comandos sin preguntar. Elige **Sistema > Seguridad > Acceso del asistente > Preguntar antes de cambiar** para restaurar los permisos normales. La preferencia se guarda solo en este PC en `eitr/ai.json`. Las restricciones de organización fuerzan las preguntas. Sudo sigue necesitando tu contraseña. La colaboración sin ventana y los recordatorios de voz siguen siendo de solo lectura.

Al cambiar el tema, Eitr solo actualiza el ajuste claro/oscuro de los archivos existentes y legibles de Claude Code, Gemini CLI y Grok Build. Conserva las demás opciones y el formato. Omite clientes no instalados y archivos ausentes o dañados; los asistentes sin ajuste claro/oscuro compatible usan los colores del terminal.

Las versiones instaladas de los SDK y las fuentes de los instaladores se mantienen en los manifiestos de la distribución. Consulta el selector actual: un ejemplo del manual no promete la última versión del proyecto original. La instalación puede necesitar descargas.

### Ratatoskr

Desarrollo > Asistente predeterminado siempre ofrece **Ratatoskr (local, experimental)**, que no necesita cuenta ni suscripción. La primera vez, un terminal explica las descargas únicas antes de cambiar nada: el paquete de Arch `ollama` (unos 15 MB) y el modelo de lenguaje `qwen3:4b` (unos 2,5 GB, licencia Apache-2.0). Una sola confirmación (Enter confirma; Esc cancela) instala el paquete, crea el servicio de usuario `eitr-ollama.service`, descarga el modelo mostrando el progreso y lo deja como predeterminado. Si un paso falla, su salida queda en pantalla y se conserva el predeterminado anterior.

Todo queda en este PC: el servicio escucha solo en `127.0.0.1:11434`, se inicia cuando hace falta y guarda sus modelos en `~/.local/share/eitr/ollama`. Es notablemente menos fiable que los asistentes en la nube, sobre todo con frases poco habituales, y más lento en el procesador. Los recordatorios por voz validan sus respuestas como las de cualquier otro asistente, así que una respuesta incorrecta no cambia nada. **SUPER + A** abre un chat con el modelo; `/bye` lo cierra. Nunca es ayudante de los asistentes que trabajan juntos y no tiene entrada en Uso de IA.

Selecciona **Ratatoskr** en el mismo menú y pulsa **Delete**. La eliminación pregunta una vez y luego elimina el servicio y los modelos, restablece el predeterminado si era el local y desinstala `ollama` si lo instaló la configuración. La clave propia y el historial de chat de Ollama en `~/.ollama` se conservan.

## Monitorización

Desarrollo > Monitorización deja tus paneles al alcance de una búsqueda. **Añadir panel** pide el servicio (Grafana, Datadog, Sentry, New Relic, Prometheus u Otro), un nombre y su dirección. Después, el menú abre el panel en el navegador. Se guardan solo en este equipo, en `~/.config/eitr/monitoring.json`; Delete elimina uno. Nunca incluyas contraseñas ni tokens en una dirección.

**Herramientas de monitorización** instala utilidades de línea de comandos: `promtool` de Prometheus y la Sentry CLI. Los espacios de trabajo de Amazon Managed Grafana están en Nube > AWS > tu cuenta > Grafana, junto a las demás herramientas AWS.

## Cuentas y flujos de nube

El uso de IA requiere un cliente instalado y configurado; inicia sesión con su procedimiento habitual. Las cuotas y la facturación de API o empresarial pueden diferir de los paneles compatibles para cuentas personales. EITR no incluye credenciales.

Los menús de nube usan tus cuentas y perfiles locales. Los perfiles AWS vienen de la configuración local de AWS o del mapeo de perfiles de EITR. Google Cloud muestra configuraciones de gcloud con nombre, cuenta y proyecto. Una configuración sin proyecto te pide elegirlo al abrir herramientas de recursos; Iniciar sesión sigue disponible antes de descubrir proyectos. Azure muestra suscripciones habilitadas y sus IDs de inquilino. Selecciona un contexto antes de una herramienta: las de Google Cloud y Azure se buscan dentro del menú del contexto, no en la búsqueda global.

Las cuentas AWS deben tener una sección correspondiente `[default]` o `[profile NAME]` en el archivo de configuración AWS (`~/.aws/config`, o `AWS_CONFIG_FILE` si está definido). Se excluyen los perfiles que solo aparecen en el archivo de credenciales y los perfiles de configuración que definen `endpoint_url` (incluso vacío), incluidos los ajustes de servicio anidados y los grupos `[services NAME]` referenciados, porque pueden usar servicios compatibles con S3, como Cloudflare R2. `EITR_AWS_PROFILES` puede nombrar o restringir los perfiles válidos, pero no incluir los excluidos. EITR no modifica ninguno de los archivos AWS.

Abrir un contexto de Google elimina sustituciones de proyecto heredadas que no correspondan; las configuraciones sin proyecto piden uno para las herramientas de recursos. Al volver de la terminal se conserva el contexto y el proyecto elegido para una configuración sin proyecto, sin cambiar valores globales de las CLI. Iniciar sesión, Comprobar autenticación y Actualizar están en cada contexto detectado. El acceso de Google usa tu cuenta configurada; el de Azure usa su inquilino y restaura la suscripción predeterminada anterior tras autenticarse. Actualizar en Azure renueva la caché de suscripciones y muestra la seleccionada.

Cada menú ofrece **Añadir cuenta AWS**, **Añadir cuenta GCP** o **Añadir cuenta Azure**, para configurar tantas cuentas como necesites, como Desarrollo y Producción de una empresa. Primero pide un nombre y luego ejecuta la configuración de la CLI del proveedor: perfil AWS mediante AWS SSO (IAM Identity Center) o claves de acceso, configuración gcloud independiente con sesión y proyecto, o sesión de Azure cuyas suscripciones nombras. Si falta `gcloud` o `az`, ofrece instalarlo primero. **Ctrl+R** cambia el nombre de una cuenta.

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
extensiones. Eitr lo ha probado con una clave de API gratuita: respondió a una
pregunta de solo lectura y a otra hecha a través del puente. El modo plan está documentado como solo lectura; Eitr no ha verificado
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

Desarrollo > Nube también incluye Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify e IBM Cloud (`ibmcloud`). Añade una cuenta con un nombre en minúsculas, dígitos o guiones. Son espacios privados en `~/.config/eitr/cloud-accounts/<provider>/<name>`; nunca se importan configuraciones existentes del proveedor. El proveedor y el espacio seleccionado aparecen en el selector de herramientas y el terminal. Al volver del terminal se conserva el espacio; Shift+Backspace vuelve a la lista de cuentas. Elegir un espacio nunca cambia el valor global predeterminado de la CLI.

Si faltan, se ofrecen `wrangler`, `doctl` y `hcloud` desde los repositorios oficiales de Arch (`doctl` y `hcloud` en extra). Oracle Cloud e IBM Cloud usan sus instaladores oficiales de shell por HTTPS desde `distro/installers.json`; Oracle recibe `--accept-all-defaults`. Vercel (`vercel`) y Netlify (`netlify-cli`, comando `netlify`) usan la receta existente de NVM/npm. La instalación requiere confirmación. El inicio de sesión y las acciones de cuenta se ejecutan solo en el espacio privado elegido. DigitalOcean y Hetzner enumeran contextos nativos; Oracle enumera perfiles de `~/.oci/config` de ese espacio. La selección de contexto/perfil se guarda localmente y se pasa por comando, sin cambiar valores globales. Vercel y Netlify ofrecen su acción nativa de cambio; después se introduce la etiqueta del equipo/cuenta elegido. Vercel también pide un ámbito antes del inicio de sesión y pasa `--scope TEAM` en los comandos posteriores. IBM ofrece acceso por SSO y clave API, muestra `ibmcloud target` y selecciona explícitamente cuenta y región. El contexto/perfil/ámbito/cuenta y la región guardada siguen visibles al volver al menú. Estas etiquetas son selecciones locales, no identidades remotas verificadas. No se heredan credenciales ni variables del proveedor existentes. Las consolas del navegador tienen sesiones propias; comprueba la cuenta antes de actuar.

Los siete proveedores con espacios privados usan iconos neutros para recursos y acciones, con descripciones breves. Las cuentas aparecen primero en orden alfabético, seguidas de Añadir cuenta; las herramientas se ordenan alfabéticamente por sus nombres traducidos. El selector muestra la cuenta, el contexto y la región guardada, y cada informe de solo lectura repite ese contexto sobre su salida. Los informes mantienen el paginador compartido con AWS; no se añaden comandos de recursos ni búsquedas de registros.

| Proveedor | Inicio de sesión | Lista / cambio / contexto por comando |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

La navegación por la nube usa menús reales de Elephant. Shift+Backspace vuelve al menú anterior: un servicio o selector de recursos vuelve al menú que lo contiene, el menú de la cuenta vuelve a la lista de cuentas del proveedor y esa lista vuelve a Cloud. La cuenta y el contexto seleccionados siguen visibles. Eitr guarda esta selección de navegación en `~/.config/eitr/cloud-navigation.json`; los valores globales de las CLI de los proveedores no cambian. Los informes conservan su paginador, las búsquedas de registros conservan fzf y la configuración conserva los formularios de terminal con revisión. Las búsquedas de texto libre siguen aceptando texto en Walker; no son listas de navegación.

Elimina una cuenta con la tecla Delete en su fila o **Eliminar cuenta** en su menú. La confirmación identifica al proveedor y la cuenta: elimina el inicio de sesión de ese proveedor para esa cuenta en este equipo, sin afectar a la cuenta remota. Cancelar no cambia nada. Solo se elimina la carpeta privada de la cuenta seleccionada en Eitr; se rechazan enlaces simbólicos, rutas fuera de la raíz del proveedor y cuentas con una acción de Eitr en ejecución. AWS, Azure y Google Cloud no reciben esta acción. La confirmación se abre en Walker con Cancelar y Confirmar; no se abre un terminal.

Los informes de solo lectura usan el entorno privado de la cuenta seleccionada y el paginador de nube existente. Cloudflare: cuenta, buckets R2, bases D1, espacios de nombres KV, proyectos Pages y colas. DigitalOcean: Droplets, aplicaciones, bases de datos, Kubernetes, volúmenes, dominios, balanceadores de carga y saldo. Hetzner: servidores, volúmenes, redes, cortafuegos, balanceadores de carga, IP primarias e instantáneas. Oracle: compartimentos, instancias, buckets y VCN. Vercel: proyectos, despliegues y dominios. Netlify: estado y sitios. IBM: cuenta, destino, grupos de recursos e instancias de servicio. DigitalOcean y Hetzner siempre pasan el contexto elegido; Oracle pasa el perfil y la autenticación por token de seguridad, leyendo la tenancy solo del perfil privado de esa cuenta. La lista de buckets consulta primero el espacio de nombres. Vercel pasa el ámbito del equipo seleccionado. Los errores siguen siendo legibles y nunca provocan un reintento con otra cuenta. Las búsquedas de registros mantienen el visor fzf existente. Las comprobaciones en vivo con cuentas reales siguen pendientes.

Los formularios de cuentas de nube, Git Accounts (añadir y editar), paneles de monitorización y aplicaciones web muestran los pasos a la izquierda y la respuesta actual a la derecha. Usa las flechas o Tab para seleccionar un paso y Enter para responder. La revisión muestra todas las respuestas antes de aplicar cambios; vuelve a un paso con Izquierda o las demás flechas y usa PgUp/PgDn para desplazar revisiones largas. Esc o Ctrl+C cancela sin guardar. El inicio de sesión del proveedor comienza tras la revisión; si falla o se interrumpe, se descarta la cuenta nueva. Google Cloud pide un ID de proyecto opcional antes de iniciar sesión; Azure pide una etiqueta opcional para las suscripciones y, si está vacía, conserva sus nombres. Vercel pide el ámbito antes de iniciar sesión.
