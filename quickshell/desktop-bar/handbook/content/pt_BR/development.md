# Ferramentas de desenvolvimento

Principal > Desenvolvimento reúne **IA**, **Nuvem**, **Contas Git**, **Monitoramento**, **LazyVim** e **VS Code**. Os seletores de projetos abrem a pasta escolhida no editor; a integração de temas atualiza os editores compatíveis já abertos, inclusive sessões do LazyVim.

**Contas Git** configura uma identidade padrão para GitHub/GitLab, regras por pasta, chaves SSH e logins separados nas CLIs dos provedores. Cada mudança de regra exige uma prévia com confirmação; ela nunca reescreve remotos de projetos nem muda contas globais das CLIs. Consulte [Contas Git](handbook:git-accounts).

## Ferramentas opcionais

Instalar > Linguagens de desenvolvimento e Ferramentas JavaScript instala o que você escolher. Java, Flutter e clientes de banco de dados não são necessários para executar a barra, o lançador ou os temas do EITR. Instalar > Bancos de dados oferece ferramentas opcionais. Instalar > Aplicativos de desenvolvimento oferece Bruno, Cursor, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code e Zed; Instalar > Produtividade oferece 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack e Thunderbird. Os pacotes AUR são baixados e compilados no seu computador; algumas licenças impedem sua distribuição pelo EITR.


Linguagens também oferece **mise (vários runtimes)** como pacote Arch opcional. Ative manualmente com `eval "$(mise activate zsh)"` em `~/.zshrc`; pode haver conflito com nvm/uv para o mesmo runtime. Os gerenciadores existentes permanecem iguais.

## Aplicativos web

Instalar > Aplicativos web > Criar aplicativo web pede um nome e um endereço e adiciona um atalho que abre o site em uma janela própria. O ícone é baixado na criação, apenas por HTTP(S). Manifestos inválidos ou ícones indisponíveis usam o ícone da página ou um ícone genérico de navegador. Não coloque credenciais no endereço. Atalhos e ícones usam seu diretório de dados XDG, inclusive um `XDG_DATA_HOME` personalizado; a remoção por qualquer menu usa esse mesmo local.
Com vários perfis de navegador, a criação de um aplicativo web pergunta em qual perfil ele será aberto; para mudar, remova e adicione o aplicativo novamente.

Aplicativos web precisam de Chrome, Chromium, Edge, Brave ou Vivaldi (Instalar > Navegadores); serviços de streaming com DRM, como Netflix, exigem Chrome. Remova um com Delete em Instalar > Aplicativos web ou no menu Aplicativos.

Instalar > Navegadores também oferece Brave (AUR). Instalar > Produtividade oferece Basecamp e Notion como aplicativos web opcionais. As receitas contêm apenas nome e URL; o ícone do site é baixado na sua máquina ao instalar. Nada vem pré-instalado.

## Assistentes de IA

Os lançadores interativos (incluindo SUPER + A) começam na sua pasta pessoal. O Eitr configura a confiança nessa pasta quando há suporte seguro e passa orientações sobre o Manual pelas opções de instruções adicionais compatíveis. As limitações estão em distro/ASSISTANT-STARTUP.md. O chat rápido somente leitura inclui uma introdução ao Eitr e trechos relevantes do Manual traduzido; ele avisa quando a pergunta não está coberta.

Cada assistente na nuvem tem um submenu Contas em Desenvolvimento > IA. Padrão usa a configuração e o login existentes sem mover arquivos. Adicionar conta… solicita um nome, mostra uma revisão e abre o login da própria CLI com uma janela privada do navegador quando compatível (navegadores desconhecidos usam a abertura normal). Enter confirma; Esc cancela. Selecione uma conta para alternar manualmente as próximas sessões interativas, Pergunte à IA e os auxiliares somente leitura; sessões em execução mantêm sua conta. Delete remove uma conta adicionada e sua configuração local após confirmação; Padrão não pode ser removida. Remover a conta selecionada retorna a Padrão sem encerrar o login de outra conta. Antigravity oferece apenas Padrão porque sua CLI não permite substituir a pasta de configuração. Ratatoskr tem uma conta local. Nomes e seleção ficam neste PC em `eitr/ai-accounts.json` (0600); as pastas separadas ficam em `$XDG_DATA_HOME/eitr/ai-accounts/` (0700). Uso de IA agrupa as contas por assistente e mostra Sem dados quando o uso não pode ser lido ou não é compatível.

Desenvolvimento > IA oferece um menu para cada assistente instalado: Claude Code, Codex, Gemini CLI, Grok Build e GitHub Copilot CLI. Instale em Instalar > CLIs de IA; sem assistentes instalados, Desenvolvimento > IA aponta para lá.

Ao abrir um projeto no LazyVim ou VS Code, primeiro escolha uma pasta em `~/Development`: entre nas pastas para avançar, use Abrir para escolher a atual e Voltar para subir um nível ou retornar ao menu quando estiver no topo.

Você também pode iniciar Claude Code, Codex, Gemini CLI, Grok Build e GitHub Copilot CLI (`copilot`) por comando. Se a ferramenta não estiver instalada, o Eitr explica sua função e oferece a mesma instalação de Instalar > CLIs de IA. Enter confirma a instalação; Esc cancela. Sem terminal interativo, o comando encerra com instruções de instalação. Binários instalados têm preferência sobre esses lançadores. Entre pela própria ferramenta; nenhum binário de assistente ou credencial acompanha o Eitr.

Desenvolvimento > Assistente padrão seleciona um assistente instalado neste computador. **SUPER + A** abre esse assistente em um terminal; sem padrão, abre o seletor. Os assistentes interativos abrem com acesso total por padrão: podem alterar arquivos e executar comandos sem perguntar. Use **Sistema > Segurança > Acesso dos assistentes > Perguntar antes de alterar** para restaurar as permissões normais. A preferência fica apenas neste PC em `eitr/ai.json`. Restrições da organização forçam as perguntas. Sudo continua exigindo sua senha. Colaboração sem janela e lembretes por voz continuam somente leitura.

Ao trocar o tema, o Eitr atualiza apenas a opção de tema claro/escuro nas configurações existentes e legíveis do Claude Code, Gemini CLI e Grok Build. As demais opções e a formatação são preservadas. Clientes ausentes, não instalados ou com arquivos inválidos são ignorados; assistentes sem opção claro/escuro compatível seguem as cores do terminal.

As versões dos SDKs instalados e as fontes dos instaladores são mantidas nos manifestos da distribuição. Consulte o seletor atual; um exemplo do manual não garante a versão mais recente disponível no projeto original. A instalação pode exigir downloads.

### Ratatoskr

Desenvolvimento > Assistente padrão sempre oferece **Ratatoskr (local, experimental)**, que não precisa de conta nem assinatura. Na primeira vez, um terminal explica os downloads únicos antes de mudar qualquer coisa: o pacote do Arch `ollama` (cerca de 15 MB) e o modelo de linguagem `qwen3:4b` (cerca de 2,5 GB, licença Apache-2.0). Uma única confirmação (Enter confirma; Esc cancela) instala o pacote, cria o serviço de usuário `eitr-ollama.service`, baixa o modelo mostrando o progresso e o define como padrão. Se uma etapa falhar, a saída fica na tela e o padrão anterior é mantido.

Tudo fica neste PC: o serviço escuta só em `127.0.0.1:11434`, inicia quando necessário e guarda os modelos em `~/.local/share/eitr/ollama`. Ele é visivelmente menos confiável que os assistentes na nuvem, principalmente com frases incomuns, e mais lento no processador. Os lembretes por voz validam as respostas dele como as de qualquer outro assistente, então uma resposta errada não muda nada. **SUPER + A** abre um chat com o modelo; `/bye` o fecha. Ele nunca é ajudante dos assistentes trabalhando juntos e não tem entrada em Uso de IA.

Selecione **Ratatoskr** no mesmo menu e pressione **Delete**. A remoção pergunta uma vez e então exclui o serviço e os modelos, redefine o padrão se ele era o local e desinstala o `ollama` se a configuração o instalou. A chave e o histórico de chat do próprio Ollama em `~/.ollama` são mantidos.

## Monitoramento

Desenvolvimento > Monitoramento deixa seus painéis acessíveis pela busca. **Adicionar painel** pede o serviço (Grafana, Datadog, Sentry, New Relic, Prometheus ou Outro), um nome e seu endereço. Depois, o menu abre o painel no navegador. Os dados ficam apenas neste computador, em `~/.config/eitr/monitoring.json`; Delete remove um painel. Nunca inclua senhas ou tokens no endereço.

**Ferramentas de monitoramento** instala ferramentas de linha de comando: `promtool`, do Prometheus, e a Sentry CLI. Os espaços de trabalho do Amazon Managed Grafana ficam em Nuvem > AWS > sua conta > Grafana, junto às outras ferramentas AWS.

## Contas e fluxos de nuvem

O uso de IA exige um cliente instalado e configurado; entre pelo fluxo normal dele. Cotas e cobrança corporativa ou de API podem diferir dos painéis de contas pessoais compatíveis. O EITR não inclui credenciais.

Os menus de nuvem usam suas contas e perfis locais. Os perfis AWS vêm da configuração local da AWS ou do mapeamento de perfis do EITR. Google Cloud lista configurações nomeadas do gcloud, com conta e projeto. Se uma configuração não tiver projeto, ele será solicitado ao abrir ferramentas de recursos; Entrar continua disponível antes de descobrir projetos. Azure lista assinaturas ativas e seus IDs de tenant. Escolha um contexto antes da ferramenta: as ferramentas Google Cloud e Azure são buscadas dentro do menu do contexto, não na busca global.

As contas AWS precisam de uma seção correspondente `[default]` ou `[profile NAME]` no arquivo de configuração AWS (`~/.aws/config`, ou `AWS_CONFIG_FILE` quando definido). Perfis presentes apenas no arquivo de credenciais são excluídos, assim como perfis de configuração que definem `endpoint_url` (mesmo vazio), incluindo configurações de serviço aninhadas e grupos `[services NAME]` referenciados, pois podem apontar para serviços compatíveis com S3, como Cloudflare R2. `EITR_AWS_PROFILES` pode nomear ou restringir os perfis elegíveis, mas não incluir os excluídos. O EITR não altera nenhum dos arquivos AWS.

Abrir um contexto Google limpa substituições de projeto herdadas que não se aplicam; configurações sem projeto pedem um para usar ferramentas de recursos. Voltar do terminal preserva o contexto e o projeto escolhido para uma configuração que não tinha um, sem mudar os padrões globais das CLIs. Entrar, Verificar autenticação e Atualizar ficam em cada contexto detectado. O login do Google usa a conta configurada; o do Azure usa o tenant e restaura a assinatura padrão anterior após autenticar. Atualizar no Azure renova o cache de assinaturas e mostra a selecionada.

Cada menu oferece **Adicionar conta AWS**, **Adicionar conta GCP** ou **Adicionar conta Azure**, permitindo configurar quantas contas precisar, como Desenvolvimento e Produção de uma empresa. Primeiro ele pede um nome e depois executa a configuração da CLI do provedor: perfil AWS por AWS SSO (IAM Identity Center) ou chaves de acesso, configuração gcloud separada com login e projeto, ou login Azure cujas assinaturas você nomeia. Se `gcloud` ou `az` estiver ausente, oferece instalá-lo primeiro. **Ctrl+R** renomeia uma conta.

Os nomes ficam em `~/.config/eitr/cloud-contexts.json`, associados ao perfil AWS, configuração gcloud ou ID de assinatura. O EITR não deduz ambientes nem armazena credenciais ali; Adicionar nunca muda o padrão global de uma CLI. Grafana e operações de nuvem exigem as contas e permissões correspondentes. Algumas ações só consultam dados; outras alteram recursos remotos: revise a operação e a conta antes de confirmar.

Mantenha tokens, segredos `.env` e credenciais fora de dotfiles compartilhados e capturas de tela. A configuração do shell carrega os gerenciadores compatíveis sem que os instaladores reescrevam seus perfis. Aprender mantém referências próprias de LazyVim, tmux e cmux.

## Assistentes trabalhando juntos

Desenvolvimento > IA > Permitir que assistentes trabalhem juntos vem desativado.
Ative para conectar Claude, Codex, Copilot, Grok e Gemini CLI instalados que
aparentem estar conectados. Cada transferência usa a assinatura ou cobrança
por API do auxiliar e conta para seus limites. Nos outros clientes, conexões
somente por chave de API ou chaveiro não são detectadas.

O Gemini só é detectado com `GEMINI_API_KEY` ou `GOOGLE_API_KEY` não vazia,
ou `security.auth.selectedType` igual a `gemini-api-key` ou `vertex-ai` em
`~/.gemini/settings.json`. Login pessoal do Google não conta: o Google não o
atende mais. O Gemini roda sem interface no modo plan, sem servidores MCP nem
extensões. O Eitr o testou com uma chave de API gratuita: ele respondeu a uma
pergunta somente leitura e a outra feita pela ponte. O modo plan
é documentado como somente leitura; o Eitr ainda não verificou seu comportamento
com arquivos, shell ou arquivos de plano.

Peça ao assistente para consultar o outro em uma revisão, explicação ou
sugestão. Aprove cada transferência na solicitação normal do assistente que
faz a chamada; o Eitr nunca autoriza essas ferramentas antecipadamente. Não
ative aprovação automática de ferramentas para o servidor assistants. Os
auxiliares apenas leem; as edições ficam com o assistente principal. Um
auxiliar não pode chamar outro. Uma notificação identifica quem consultou
quem, e cada solicitação tem um prazo de três minutos. O auxiliar lê o
diretório de trabalho atual de quem chama; a pergunta e o contexto podem ser
enviados ao provedor desse assistente.

A opção registra um servidor MCP `assistants` pelo comando de cada assistente
(`claude mcp add`, `codex mcp add`, `copilot mcp add` e `grok mcp add`, `gemini mcp add -s user`), então
cada assistente grava as próprias configurações. Um servidor existente com o mesmo nome é mantido e
informado. As alterações ficam registradas somente neste
computador em `~/.local/state/eitr/assistants.json` (ou `XDG_STATE_HOME`).
Desativar remove exatamente as entradas do Eitr; se uma entrada foi editada
depois, o Eitr a mantém e informa o conflito. Reinicie as sessões dos
assistentes após mudar a opção. A verificação de ponta a ponta com contas
reais ainda será feita separadamente.

Antigravity CLI (`agy`) está disponível para contas pessoais do Google em Instalar > CLIs de IA e pelo lançador de primeiro uso. Nunca é incluído na distribuição. Ele é instalado pelo instalador oficial do Google, que verifica o download, e você entra com sua conta Google. Ainda não é oferecido como auxiliar de assistentes trabalhando juntos. Um `agy` já instalado pode ser aberto normalmente. Gemini CLI exige uma chave da API Gemini ou conta Google Cloud/empresa. Antigravity não é auxiliar de colaboração: o modo sem interface nega até leituras. As únicas liberações ignoram permissões ou mudam regras globais. O Eitr o reavaliará quando houver permissões por execução ou modo sem interface somente de leitura.

### Provedores adicionais

Desenvolvimento > Nuvem também lista Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify e IBM Cloud (`ibmcloud`). Adicione uma conta com nome em letras minúsculas, dígitos ou hífens. São espaços privados em `~/.config/eitr/cloud-accounts/<provider>/<name>`; configurações existentes dos provedores nunca são importadas. O provedor e o espaço escolhido aparecem no seletor de ferramentas e no terminal. Ao voltar do terminal, o mesmo espaço permanece selecionado; Shift+Backspace volta à lista de contas. Escolher um espaço nunca altera o padrão global da CLI.

Se ausentes, `wrangler`, `doctl` e `hcloud` são oferecidos pelos repositórios oficiais do Arch (`doctl` e `hcloud` em extra). Oracle Cloud e IBM Cloud usam seus instaladores oficiais de shell por HTTPS em `distro/installers.json`; Oracle recebe `--accept-all-defaults`. Vercel (`vercel`) e Netlify (`netlify-cli`, comando `netlify`) usam a receita existente de NVM/npm. A instalação exige confirmação. O login e as ações de conta executam apenas no espaço privado escolhido. DigitalOcean e Hetzner listam contextos nativos; Oracle lista perfis do `~/.oci/config` desse espaço. A seleção de contexto/perfil é salva localmente e passada por comando, sem alterar padrões globais. Vercel e Netlify oferecem sua ação nativa de troca; depois informe o rótulo da equipe/conta escolhida. Vercel também pede um escopo antes do login e passa `--scope TEAM` nos comandos seguintes. IBM oferece login por SSO e chave de API, mostra `ibmcloud target` e seleciona explicitamente conta e região. O contexto/perfil/escopo/conta e a região salva continuam visíveis ao voltar ao menu. Esses rótulos são seleções locais, não identidades remotas verificadas. Credenciais e variáveis de provedor existentes não são herdadas. Os consoles no navegador têm sessões próprias; confira a conta antes de agir.

Os sete provedores com espaços privados usam ícones neutros para recursos e ações, com descrições curtas. As contas aparecem primeiro em ordem alfabética, seguidas de Adicionar conta; as ferramentas são ordenadas alfabeticamente pelos nomes traduzidos. O seletor mostra a conta, o contexto e a região salva, e cada relatório somente leitura repete esse contexto acima da saída. Os relatórios mantêm o paginador compartilhado com a AWS; nenhum comando de recursos ou pesquisa de logs adicional é introduzido.

| Provedor | Login | Lista / troca / contexto por comando |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

A navegação na nuvem usa menus reais do Elephant. Shift+Backspace volta ao menu anterior: um serviço ou seletor de recurso volta ao menu que o contém, o menu da conta volta à lista de contas do provedor e essa lista volta a Cloud. A conta e o contexto selecionados permanecem visíveis. O Eitr salva essa seleção de navegação em `~/.config/eitr/cloud-navigation.json`; os padrões globais das CLIs dos provedores permanecem inalterados. Os relatórios mantêm o paginador, as buscas de logs mantêm o fzf e a configuração mantém os formulários de terminal com revisão. As buscas de texto livre ainda aceitam texto no Walker; não são listas de navegação.

Exclua uma conta com a tecla Delete na linha da conta ou **Excluir conta** no menu dela. A confirmação identifica o provedor e a conta: remove o acesso desse provedor a essa conta neste computador, sem afetar a conta remota. Cancelar não altera nada. Apenas a pasta privada da conta selecionada no Eitr é removida; links simbólicos, caminhos fora da raiz do provedor e contas com uma ação do Eitr em execução são recusados. AWS, Azure e Google Cloud não recebem essa ação. A confirmação abre no Walker com Cancelar e Confirmar; nenhum terminal é aberto.

Os relatórios somente leitura usam o ambiente privado da conta selecionada e o paginador de nuvem existente. Cloudflare: conta, buckets R2, bancos D1, namespaces KV, projetos Pages e filas. DigitalOcean: Droplets, aplicativos, bancos de dados, Kubernetes, volumes, domínios, balanceadores de carga e saldo. Hetzner: servidores, volumes, redes, firewalls, balanceadores de carga, IPs primários e snapshots. Oracle: compartimentos, instâncias, buckets e VCNs. Vercel: projetos, implantações e domínios. Netlify: status e sites. IBM: conta, destino, grupos de recursos e instâncias de serviço. DigitalOcean e Hetzner sempre passam o contexto escolhido; Oracle passa o perfil e a autenticação por token de segurança, lendo a tenancy somente do perfil privado dessa conta. A listagem de buckets consulta primeiro o namespace. Vercel passa o escopo da equipe selecionada. Os erros ficam legíveis e nunca provocam nova tentativa com outra conta. As buscas em logs mantêm o visualizador fzf existente. As verificações ao vivo com contas reais continuam pendentes.

Os formulários de contas de nuvem, Git Accounts (adicionar e editar), painéis de monitoramento e aplicativos web mostram as etapas à esquerda e a resposta atual à direita. Use as setas ou Tab para selecionar uma etapa e Enter para responder. A revisão lista todas as respostas antes de aplicar qualquer alteração; volte a uma etapa com a seta para a esquerda ou as outras setas e use PgUp/PgDn para rolar revisões longas. Esc ou Ctrl+C cancela sem salvar. O login do provedor começa após a revisão; se falhar ou for interrompido, a nova conta é descartada. O Google Cloud pede um ID de projeto opcional antes do login; o Azure pede um nome opcional para as assinaturas antes do login e, sem ele, mantém os nomes existentes. O Vercel pede o escopo antes do login.

## Docker

Docker, docker-compose e Lazydocker estão instalados, mas o serviço Docker vem desativado. Ative-o com `sudo systemctl enable --now docker.service`.

Se `docker ps` indicar permissão negada, adicione seu usuário com `sudo usermod -aG docker $USER`. Participar do grupo docker equivale a ter privilégios de root. Saia da sessão e entre novamente, ou use `newgrp docker` em um terminal. Confira seus grupos com `id -nG`.
