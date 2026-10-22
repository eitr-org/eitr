# Aplicativos e instalação

Antes de instalar pacotes oficiais, o terminal informa que está verificando atualizações pendentes do sistema. Essa verificação pode demorar um pouco antes de pedir a senha de administrador. Instalações via Flatpak também indicam a etapa de preparação.

**SUPER + Space** e Principal > Aplicativos abrem a mesma lista. Enter inicia o aplicativo. Delete fica disponível em Aplicativos e pede confirmação para desinstalar. A busca global de **SUPER + F** abre aplicativos, mas não oferece desinstalação. Não há um menu separado baseado em aplicativos fixados.

Digitar no menu principal busca aplicativos instalados e ações de todos os submenus. Dentro de um submenu, como Sistema ou Instalar, a busca abrange esse submenu e seus descendentes. As linhas de submenu terminam em **>**; **Shift + Backspace** volta ao menu anterior.

## Instalar

Pressione Delete em uma entrada instalada nas listas de aplicativos e ferramentas de Instalar para desinstalá-la após a confirmação. Aplicativos Web mantêm sua ação de remoção. Pacotes (Pacman e Yay) continuam apenas com instalação, sem ação Delete. Dependências necessárias ao sistema nunca são removidas recursivamente; o pacman recusa remoções que quebrariam outro pacote.

Pacotes de linguagens gerenciadas mostram o aviso completo de remoção em um terminal antes de pedir confirmação com [y/N]; Enter cancela. Remover Node inclui todas as versões gerenciadas pelo NVM e suas ferramentas npm globais. A remoção de Python afeta as versões gerenciadas pelo uv e o próprio uv, não o Python do sistema. Java remove as versões atuais do Java e do Maven no SDKMAN; Rust remove apenas sua versão estável. Rails e Laravel removem suas ferramentas de framework, mantendo Ruby, PHP e Composer. Projetos, configurações e credenciais são mantidos, mas ferramentas e ambientes dependentes podem deixar de funcionar. A remoção de assistentes nativos mantém versões em cache e configurações.


Aplicativos presentes no sistema mostram **Instalado** abaixo do nome; escolhê-los informa isso em vez de reinstalar. Também são reconhecidas ferramentas instaladas por seus próprios gerenciadores, como Java pelo SDKMAN ou Node.js pelo NVM. Pacotes que exigem um ambiente de execução, como o Java do DBeaver, só adicionam um ambiente pequeno quando nenhum pacote já o fornece.

- **CLIs de IA:** clientes opcionais de IA por linha de comando.
- **Navegadores:** opções compatíveis de navegador.
- **Bases de dados:** ferramentas opcionais como DBeaver, clientes de banco de dados e Valkey, o servidor compatível com Redis distribuído pelo Arch no lugar do Redis.
- **Linguagens de desenvolvimento:** ferramentas opcionais; Java/Flutter não são dependências obrigatórias da área de trabalho.
- **Ferramentas de JavaScript:** ambientes de execução e ferramentas opcionais de JavaScript.
- **Pacotes > Pacman** e **Pacotes > Yay (AUR):** busque pacotes oficiais do Arch ou comunitários do AUR, identificados por origem e estado de instalação. A busca fica acima, os pacotes no meio e os detalhes da seleção abaixo. **Ctrl+B** alterna para o arquivo de compilação (PKGBUILD), **Ctrl+O** abre a página no navegador, **Tab** seleciona vários pacotes e **Enter** instala. Pacotes AUR são compilados neste computador a partir desse arquivo: leia-o antes. Eles não são pacotes oficiais do Arch.

Os terminais de instalação, atualização e configuração mostram o banner do EITR no tema atual. Tarefas bem-sucedidas normalmente fecham; falhas permanecem visíveis. Relatórios como Limpeza ficam abertos para leitura. Terminais comuns e Sobre não exibem o banner de tarefas.

Pressione **Esc** para fechar terminais de tarefas, contas, relatórios e Sobre que aguardam uma tecla. Enter continua sendo usado para respostas e confirmações, incluindo confirmar que a chave de recuperação foi anotada e desligar o instalador.

## Ferramentas

**Calculadora** em Aplicativos, ou a tecla de calculadora do teclado, abre a calculadora do Eitr com as cores do tema atual. Digite ou clique: `+ − × ÷`, `^` para potências, `%` para porcentagem (`200×15%`), `√` e parênteses. Um número antes de um parêntese multiplica (`2(3+4)`). Enter mostra o resultado, Backspace remove um caractere, Escape limpa (duas vezes fecha) e Ctrl+C ou **Copiar** copia o resultado. A expressão é calculada diretamente, sem executá-la como código.

**Ditado offline** converte fala em texto sem enviar áudio para fora do computador. Segure **SUPER + D**, fale e solte: as palavras são digitadas onde está o cursor, no idioma falado. Durante a escuta, o ponto vermelho à esquerda do relógio vira uma pequena onda que acompanha sua voz, confirmando a captação; após soltar, pulsa até o texto ser digitado. O primeiro uso baixa uma única vez o modelo de voz (148 MB, conferido pelo checksum publicado) para `~/.local/share/eitr/whisper/`; depois funciona offline. A transcrição leva um momento após soltar, mais em processadores antigos. A gravação termina ao soltar D, mesmo que SUPER tenha sido solto antes, ou após 120 segundos; as palavras são então transcritas normalmente.

**Principal > Ferramentas > Lembretes > Novo lembrete** pede quando (intervalo como `10m` ou `1h30m`, ou horário como `18:30`) e sobre o quê, e exibe nesse momento uma notificação que fica até ser dispensada. **Próximos lembretes** lista os pendentes; escolha um para cancelar. Eles sobrevivem a reinicializações; os vencidos com o computador desligado aparecem no próximo login. No terminal, use `eitr remind 25m Take the tea out`; `eitr remind` sozinho lista os lembretes.

## Jogos

Principal > Jogos lista **GeForce NOW**, **RetroArch** e **Steam**. Escolher um abre se já instalado ou instala caso contrário. O RetroArch vem dos pacotes oficiais do Arch com núcleos para NES, SNES, Game Boy e Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP e Dreamcast. Adicione seus jogos e, para consoles que precisem, os arquivos de BIOS; o Eitr não distribui nenhum deles. GeForce NOW é instalado por Flatpak.

**Alternar > Modo de jogo** reduz interferências da área de trabalho: desativa animações, desfoque e sombras, adia pop-ups de notificações (Não perturbe) e ativa o perfil de desempenho, se disponível. Desativar restaura exatamente o que mudou. O Steam inclui **GameMode** e **MangoHud**: adicione `gamemoderun mangohud %command%` às opções de inicialização do jogo no Steam para otimizar a CPU durante o jogo e mostrar a sobreposição de FPS.

O pacote do LocalSend inclui seus requisitos de execução: não é preciso instalar o Flutter SDK só para usá-lo. As ferramentas de desenvolvimento continuam opcionais.

Consulte [Atualizações e limpeza](handbook:maintenance) para atualizar; instalar um pacote não equivale ao fluxo de Atualização do sistema protegido por snapshots.

**Visualizador de música** em **Principal > Ferramentas** abre o cava com as cores do tema. Clique com o botão direito no equalizador de mídia para abrir o mesmo visualizador; o botão esquerdo continua abrindo os detalhes da mídia. Pressione **q** ou **Esc** para fechar. Se o cava não estiver instalado, ele será instalado primeiro.

## Lembretes por voz

Segure **SUPER + Shift + D**, fale e solte, ou digite em Principal > Ferramentas > Lembretes > Fale com o assistente…. O Eitr transcreve localmente com o mesmo modelo offline do ditado e consulta o assistente escolhido em Desenvolvimento > Assistente padrão. Só a transcrição e o contexto dos lembretes vão ao provedor; o áudio fica local e é apagado após a transcrição. O assistente roda sem janela pelo caminho somente leitura do Eitr. O Eitr valida o JSON e executa as ações; o assistente não recebe ferramentas para alterar nada.

Diga “Me lembre de ligar amanhã às 15h” ou “Dentista em 30 de outubro às 15h, avise 30 minutos antes”. Compromissos avisam uma hora antes por padrão (ou com a antecedência pedida) e no horário; lembretes simples só no horário. Dados ausentes ou ambiguidade abrem um terminal com opções numeradas completas. Digite o número ou dite com SUPER + D; Esc cancela. Uma notificação informa o resultado. Você também pode pedir para listar ou cancelar lembretes.

Novo lembrete aceita `tomorrow 15:00`, dias da semana em inglês (09:00 sem horário), `2026-10-30 09:00` e `Oct 30 15:00`. Use aspas nas datas com espaços na CLI. Cada alerta tem seu timer; cancelar remove todos. Alertas perdidos aparecem no próximo login. O calendário marca os dias dos eventos; clique para ver horários e títulos atualizados imediatamente.

Lembretes recorrentes aceitam `every day 08:00`, `every Monday 09:30`, `weekdays 07:00`, `every Monday and Thursday 09:30`, `every week`, `every month on the 15th` e `every year` (09:00 por padrão). No terminal, use aspas: `eitr remind "every day 08:00" Stretch`. O assistente aceita intervalos, data final ou número de ocorrências. Datas inexistentes usam o último dia do mês. O horário local e os alertas relativos são preservados. Só a próxima ocorrência tem temporizadores; após um período desligado, aparece um aviso perdido e as ocorrências passadas são puladas, contando para o limite. A lista mostra o próximo horário e a regra. Cancele uma ocorrência ou todas as futuras: `eitr remind cancel ID occurrence` ou `eitr remind cancel ID series`. O calendário marca os dias e mostra ↻ sem mudar de altura. A sincronização Google/Outlook continua planejada e exige login.

## Plugins

Um plugin é um repositório Git com scripts, itens do Walker e, opcionalmente, um serviço do usuário. Plugins executam com todas as permissões da sua conta. O Eitr não revisou seu código: confie no autor e no repositório antes de aprovar uma instalação ou atualização.

Principal > Instalar > Plugins > Adicionar plugin… pede uma URL Git HTTPS ou, para um repositório privado, uma SSH como `git@github.com:you/plugin.git` (usa suas chaves SSH pelo agente). A revisão começa com o aviso de confiança e depois mostra autor do manifesto, repositório, commit exato, autor e data do Git, itens e serviço em segundo plano. Pressione `y` para instalar; Enter ou Esc cancela. Nenhum código do plugin roda antes da aprovação. Principal > Ferramentas > Plugins lista as ações; digitar em Ferramentas também as pesquisa. O menu vazio mostra Nenhum plugin instalado.

Atualização do sistema verifica plugins mesmo sem atualizações de pacotes. Cada atualização mostra os commits anterior e novo, seus assuntos e os arquivos alterados, e pergunta com `[y/N]`; Enter recusa. Atualizações não interativas ignoram plugins. Instalar > Plugins > o plugin oferece Atualizar e Remover; a remoção pede confirmação e apaga arquivos, itens e serviço. Os mesmos fluxos estão em `eitr plugin list`, `eitr plugin add URL`, `eitr plugin update [ID]` e `eitr plugin remove ID`.

Plugins ficam apenas em `$XDG_DATA_HOME/eitr/plugins/<id>/` (padrão `~/.local/share/eitr/plugins/`); aprovações em `$XDG_STATE_HOME/eitr/plugins.json`. Serviços usam `$XDG_CONFIG_HOME/systemd/user/eitr-plugin-<id>.service`. Nunca use sudo. Atualizações validam um candidato separado e preservam o commit aprovado em caso de recusa ou falha. Um plugin pode modificar seus arquivos; removê-lo não desfaz essas alterações.

### Referência do manifesto

A raiz contém `eitr-plugin.json`. Somente estas chaves são aceitas: `id` (letras minúsculas e dígitos separados por hífens simples), `name`, `description` (até 72 caracteres), `author`, `version`, `rows` (1–20) e `service` opcional. Cada item exige `title`, `description` (ambos até 72 caracteres) e `run`; aceita `icon` e `arguments` (lista de strings fixas) opcionais. Um serviço aceita apenas `run` e `arguments` opcional. Comandos usam argv, nunca strings de shell. `run` deve apontar para um executável dentro do repositório: caminhos absolutos, `..` e links simbólicos externos são recusados. Chaves JSON desconhecidas ou duplicadas são recusadas. Submódulos não são inicializados.

O exemplo em `distro/plugins/example/` contém manifesto e `notify.sh`, uma ação de notificação e nenhum serviço. Copie-o para seu repositório Git, faça commit e publique uma URL Git HTTPS para testar a instalação completa. É documentação; não é instalado automaticamente.
