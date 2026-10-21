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

**Ditado offline** converte fala em texto sem enviar áudio para fora do computador. Segure **SUPER + D**, fale e solte: as palavras são digitadas onde está o cursor, no idioma falado. Durante a escuta, o ponto vermelho ao lado do clima vira uma pequena onda que acompanha sua voz, confirmando a captação; após soltar, pulsa até o texto ser digitado. O primeiro uso baixa uma única vez o modelo de voz (148 MB, conferido pelo checksum publicado) para `~/.local/share/eitr/whisper/`; depois funciona offline. A transcrição leva um momento após soltar, mais em processadores antigos.

**Principal > Ferramentas > Lembretes > Novo lembrete** pede quando (intervalo como `10m` ou `1h30m`, ou horário como `18:30`) e sobre o quê, e exibe nesse momento uma notificação que fica até ser dispensada. **Próximos lembretes** lista os pendentes; escolha um para cancelar. Eles sobrevivem a reinicializações; os vencidos com o computador desligado aparecem no próximo login. No terminal, use `eitr remind 25m Take the tea out`; `eitr remind` sozinho lista os lembretes.

## Jogos

Principal > Jogos lista **GeForce NOW**, **RetroArch** e **Steam**. Escolher um abre se já instalado ou instala caso contrário. O RetroArch vem dos pacotes oficiais do Arch com núcleos para NES, SNES, Game Boy e Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP e Dreamcast. Adicione seus jogos e, para consoles que precisem, os arquivos de BIOS; o Eitr não distribui nenhum deles. GeForce NOW é instalado por Flatpak.

**Alternar > Modo de jogo** reduz interferências da área de trabalho: desativa animações, desfoque e sombras, adia pop-ups de notificações (Não perturbe) e ativa o perfil de desempenho, se disponível. Desativar restaura exatamente o que mudou. O Steam inclui **GameMode** e **MangoHud**: adicione `gamemoderun mangohud %command%` às opções de inicialização do jogo no Steam para otimizar a CPU durante o jogo e mostrar a sobreposição de FPS.

O pacote do LocalSend inclui seus requisitos de execução: não é preciso instalar o Flutter SDK só para usá-lo. As ferramentas de desenvolvimento continuam opcionais.

Consulte [Atualizações e limpeza](handbook:maintenance) para atualizar; instalar um pacote não equivale ao fluxo de Atualização do sistema protegido por snapshots.

**Visualizador de música** em **Principal > Ferramentas** abre o cava com as cores do tema. Clique com o botão direito no equalizador de mídia para abrir o mesmo visualizador; o botão esquerdo continua abrindo os detalhes da mídia. Pressione **q** ou **Esc** para fechar. Se o cava não estiver instalado, ele será instalado primeiro.
