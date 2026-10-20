# Ferramentas de desenvolvimento

Principal > Desenvolvimento reúne **IA**, **Nuvem**, **Contas Git**, **Monitoramento**, **LazyVim** e **VS Code**. Os seletores de projetos abrem a pasta escolhida no editor; a integração de temas atualiza os editores compatíveis já abertos, inclusive sessões do LazyVim.

**Contas Git** configura uma identidade padrão para GitHub/GitLab, regras por pasta, chaves SSH e logins separados nas CLIs dos provedores. Cada mudança de regra exige uma prévia com confirmação; ela nunca reescreve remotos de projetos nem muda contas globais das CLIs. Consulte [Contas Git](handbook:git-accounts).

## Ferramentas opcionais

Instalar > Linguagens de desenvolvimento e Ferramentas JavaScript instala o que você escolher. Java, Flutter e clientes de banco de dados não são necessários para executar a barra, o lançador ou os temas do EITR. Instalar > Bancos de dados oferece ferramentas opcionais. Instalar > Aplicativos de desenvolvimento oferece Bruno, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code e Zed; Instalar > Produtividade oferece 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack e Thunderbird. Os pacotes AUR são baixados e compilados no seu computador; algumas licenças impedem sua distribuição pelo EITR.

## Aplicativos web

Instalar > Aplicativos web > Criar aplicativo web pede um nome e um endereço e adiciona um atalho que abre o site em uma janela própria. O ícone é baixado na criação, apenas por HTTP(S). Manifestos inválidos ou ícones indisponíveis usam o ícone da página ou um ícone genérico de navegador. Não coloque credenciais no endereço. Atalhos e ícones usam seu diretório de dados XDG, inclusive um `XDG_DATA_HOME` personalizado; a remoção por qualquer menu usa esse mesmo local.

Aplicativos web precisam de Chrome ou Chromium (Instalar > Navegadores); serviços de streaming com DRM, como Netflix, exigem Chrome. Remova um com Delete em Instalar > Aplicativos web ou no menu Aplicativos.

## Assistentes de IA

Desenvolvimento > IA oferece Assistente padrão e um menu para cada assistente instalado: Claude Code, Codex, Gemini CLI, Grok Build e GitHub Copilot CLI. Instale em Instalar > CLIs de IA; sem assistentes instalados, Desenvolvimento > IA aponta para lá.

Ao iniciar uma sessão ou abrir um projeto no LazyVim ou VS Code, primeiro escolha uma pasta em `~/Development`: entre nas pastas para avançar, use Abrir para escolher a atual e Voltar para subir um nível ou retornar ao menu quando estiver no topo.

Você também pode iniciar Claude Code, Codex, Gemini CLI, Grok Build e GitHub Copilot CLI (`copilot`) por comando. Se a ferramenta não estiver instalada, o Eitr explica sua função e oferece a mesma instalação de Instalar > CLIs de IA. Digite `yes` para instalar; Enter cancela. Sem terminal interativo, o comando encerra com instruções de instalação. Binários instalados têm preferência sobre esses lançadores. Entre pela própria ferramenta; nenhum binário de assistente ou credencial acompanha o Eitr.

Desenvolvimento > IA > Assistente padrão seleciona um assistente instalado neste computador. **SUPER + Alt + A** abre esse assistente em um terminal; sem padrão, abre o seletor. O Eitr mantém as confirmações normais de permissão de cada assistente.

Ao trocar o tema, o Eitr atualiza apenas a opção de tema claro/escuro nas configurações existentes e legíveis do Claude Code, Gemini CLI e Grok Build. As demais opções e a formatação são preservadas. Clientes ausentes, não instalados ou com arquivos inválidos são ignorados; assistentes sem opção claro/escuro compatível seguem as cores do terminal.

As versões dos SDKs instalados e as fontes dos instaladores são mantidas nos manifestos da distribuição. Consulte o seletor atual; um exemplo do manual não garante a versão mais recente disponível no projeto original. A instalação pode exigir downloads.

## Monitoramento

Desenvolvimento > Monitoramento deixa seus painéis acessíveis pela busca. **Adicionar painel** pede o serviço (Grafana, Datadog, Sentry, New Relic, Prometheus ou Outro), um nome e seu endereço. Depois, o menu abre o painel no navegador. Os dados ficam apenas neste computador, em `~/.config/eitr/monitoring.json`; Delete remove um painel. Nunca inclua senhas ou tokens no endereço.

**Ferramentas de monitoramento** instala ferramentas de linha de comando: `promtool`, do Prometheus, e a Sentry CLI. Os espaços de trabalho do Amazon Managed Grafana ficam em Nuvem > AWS > sua conta > Grafana, junto às outras ferramentas AWS.

## Contas e fluxos de nuvem

O uso de IA exige um cliente instalado e configurado; entre pelo fluxo normal dele. Cotas e cobrança corporativa ou de API podem diferir dos painéis de contas pessoais compatíveis. O EITR não inclui credenciais.

Os menus de nuvem usam suas contas e perfis locais. Os perfis AWS vêm da configuração local da AWS ou do mapeamento de perfis do EITR. Google Cloud lista configurações nomeadas do gcloud, com conta e projeto. Se uma configuração não tiver projeto, ele será solicitado ao abrir ferramentas de recursos; Entrar continua disponível antes de descobrir projetos. Azure lista assinaturas ativas e seus IDs de tenant. Escolha um contexto antes da ferramenta: as ferramentas Google Cloud e Azure são buscadas dentro do menu do contexto, não na busca global.

Abrir um contexto Google limpa substituições de projeto herdadas que não se aplicam; configurações sem projeto pedem um para usar ferramentas de recursos. Voltar do terminal preserva o contexto e o projeto escolhido para uma configuração que não tinha um, sem mudar os padrões globais das CLIs. Entrar, Verificar autenticação e Atualizar ficam em cada contexto detectado. O login do Google usa a conta configurada; o do Azure usa o tenant e restaura a assinatura padrão anterior após autenticar. Atualizar no Azure renova o cache de assinaturas e mostra a selecionada.

Cada menu começa com **Adicionar conta AWS**, **Adicionar conta GCP** ou **Adicionar conta Azure**, permitindo configurar quantas contas precisar, como Desenvolvimento e Produção de uma empresa. Primeiro ele pede um nome e depois executa a configuração da CLI do provedor: perfil AWS por AWS SSO (IAM Identity Center) ou chaves de acesso, configuração gcloud separada com login e projeto, ou login Azure cujas assinaturas você nomeia. Se `gcloud` ou `az` estiver ausente, oferece instalá-lo primeiro. **Ctrl+R** renomeia uma conta.

Os nomes ficam em `~/.config/eitr/cloud-contexts.json`, associados ao perfil AWS, configuração gcloud ou ID de assinatura. O EITR não deduz ambientes nem armazena credenciais ali; Adicionar nunca muda o padrão global de uma CLI. Grafana e operações de nuvem exigem as contas e permissões correspondentes. Algumas ações só consultam dados; outras alteram recursos remotos: revise a operação e a conta antes de confirmar.

Mantenha tokens, segredos `.env` e credenciais fora de dotfiles compartilhados e capturas de tela. A configuração do shell carrega os gerenciadores compatíveis sem que os instaladores reescrevam seus perfis. Aprender mantém referências próprias de LazyVim, tmux e cmux.

## Assistentes trabalhando juntos

Desenvolvimento > IA > Permitir que assistentes trabalhem juntos vem desativado.
Ative para conectar Claude, Codex, Copilot e Grok instalados que aparentem estar conectados
às respectivas contas. A confirmação identifica os assistentes e explica que
cada transferência usa a assinatura do assistente auxiliar e conta para seus
limites. Conexões somente por chave de API ou chaveiro não são detectadas.
O Gemini não é oferecido: o Google não atende mais o Gemini CLI em contas
pessoais.

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
(`claude mcp add`, `codex mcp add`, `copilot mcp add` e `grok mcp add`), então
cada assistente grava as próprias configurações. Um servidor existente com o mesmo nome é mantido e
informado. As alterações ficam registradas somente neste
computador em `~/.local/state/eitr/assistants.json` (ou `XDG_STATE_HOME`).
Desativar remove exatamente as entradas do Eitr; se uma entrada foi editada
depois, o Eitr a mantém e informa o conflito. Reinicie as sessões dos
assistentes após mudar a opção. A verificação de ponta a ponta com contas
reais ainda será feita separadamente.
