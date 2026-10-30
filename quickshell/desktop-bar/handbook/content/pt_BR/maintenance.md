# Atualizações, limpeza e recuperação

O terminal mostra cada etapa de verificação e criação de snapshots enquanto ela é executada. Se tudo estiver atualizado, a mensagem permanece visível por três segundos antes de o terminal fechar.

As etapas de espera da Atualização do sistema exibem uma runa girando e um arco-íris Bifröst fluido em terminais truecolor, ou a cor de destaque do tema nos demais, seguido de frases nórdicas traduzidas e do tempo decorrido. Etapas concluídas deixam uma marca e o texto sem cor.

Abra **Configurações > Sistema > Manutenção**. Revise a saída do terminal e mantenha backups independentes antes de alterar o sistema. Snapshots não são backups em outro disco.

A atualização do sistema verifica primeiro os pacotes oficiais com checkupdates em um banco temporário separado, os pacotes AUR (incluindo os de desenvolvimento) e os Flatpaks do usuário. Se todas as verificações confirmarem que não há atualizações, termina sem snapshots, atualização ou pedido de reinicialização. Se uma verificação falhar ou faltar uma ferramenta, o fluxo normal continua.

## Atualização

**Configurações > Sistema > Atualização do sistema** é o fluxo normal de atualização completa de pacotes. Em uma nova instalação configurada do EITR, verifica o suporte a snapshots e cria snapshots anteriores e posteriores com arquivos de inicialização. Se a proteção falhar, a atualização não começa. Um desktop Arch existente sem a política da distribuição não precisa dessa configuração apenas para atualizar. A Atualização do sistema também atualiza aplicativos Flatpak, como GeForce NOW; falhas do Flatpak são informadas sem desfazer a atualização do sistema.

Antes de atualizar, a Atualização do sistema e as atualizações de pacotes oficiais pelo terminal verificam notícias do Arch Linux publicadas desde a última atualização. Elas anunciam atualizações que exigem uma etapa manual. Havendo notícias, os títulos e links são mostrados e aparece **Continuar a atualização? [y/N]**: Enter cancela antes de qualquer alteração, para você ler a publicação primeiro. Sem notícias ou sem internet, o processo continua.

**Configurações > Sistema > Canal de atualização** lista os dois canais e marca o atual; escolher o outro pede sua senha em um terminal e muda o canal das atualizações do próprio Eitr. O padrão Stable recebe versões após serem testadas. Testing recebe novas compilações assim que são publicadas, para experimentar mudanças antes; o restante continua vindo do Arch. Voltar para Stable mantém uma versão mais recente do Eitr até o canal alcançar essa versão. No terminal, `eitr channel` mostra o canal; `eitr channel testing` ou `eitr channel stable` faz a troca.

Se uma atualização impedir a inicialização, a **proteção de inicialização** a desfaz: após duas tentativas consecutivas que não cheguem à tela de login, a próxima restaura o sistema e os arquivos de inicialização anteriores à atualização e reinicia. Sua pasta pessoal não é alterada, e o próximo login informa o ocorrido. Funciona em computadores instalados pelo instalador do Eitr; veja [Recuperação e snapshots](handbook:recovery).

**Snapshots da pasta pessoal** guardam versões anteriores dos seus arquivos: ative-os em **Configurações > Sistema > Manutenção > Instantâneos > Snapshots da pasta pessoal**. São feitos a cada hora durante um dia e diariamente durante uma semana; os mais antigos são removidos quando falta espaço. Caches, Downloads, discos de VMs e jogos ficam de fora. Para recuperar um arquivo, escolha **Restaurar um arquivo ou pasta**, digite o caminho e escolha uma data. A versão anterior aparece ao lado da atual, sem substituí-la.

A Atualização do sistema inclui pacotes oficiais, AUR e Flatpak com snapshots nas instalações compatíveis da distribuição. Para casos raros, como atualizar apenas pacotes oficiais quando uma compilação AUR falha, ou pular o snapshot, use um terminal: `eitr update pacman`, `eitr update aur` ou `eitr update full` (sem snapshots automáticos), ou diretamente `sudo pacman -Syu` / `yay -Sua`. Flatpaks, runtimes de desenvolvimento e dados pessoais separados não são cobertos por snapshots da raiz.

Evite atualizações parciais do Arch. Leia as mensagens dos pacotes em vez de aceitar uma remoção inesperada sem conferir. Tarefas bem-sucedidas fecham automaticamente; falhas ficam visíveis para você investigar sem perder a saída.

Após uma atualização bem-sucedida, uma notificação pede a conclusão quando necessário: **Reiniciar agora** após atualizações de kernel, firmware, microcódigo, systemd, glibc, driver de vídeo ou criptografia de disco; ou **Sair agora** após atualizações do desktop, como EITR, Hyprland, Quickshell, Walker ou PipeWire. **Mais tarde** permite continuar trabalhando; as novas versões passam a valer na próxima reinicialização ou sessão.

## Limpeza e snapshots

Limpeza executa a manutenção e mantém o relatório aberto para leitura. Revise as propostas; um pacote órfão não é necessariamente inútil. Instantâneos oferece os fluxos existentes de estado e configuração do Snapper. Veja [Recuperação e snapshots](handbook:recovery) para layouts compatíveis e limites dos carregadores de inicialização.

## Redefinição de fábrica

Somente uma instalação compatível da distribuição com o ponto de restauração do primeiro login pode ser redefinida. Essa base privada fica separada das listas e da limpeza normais do Snapper. O root ainda pode excluí-la, e uma falha no disco pode destruí-la. São exigidos dois avisos separados e uma confirmação digitada. Leia [Redefinição de fábrica](handbook:factory-reset) para saber exatamente o que Apagar Tudo e Manter os Meus Arquivos preservam.

## Energia

Principal > Energia e Central de controle > Geral (em **Energia…**) oferecem bloqueio, encerramento de sessão, suspensão, reinicialização e desligamento. Salve seu trabalho primeiro. Essas ações realmente são executadas; não são demonstrações.

## Espelhos de pacotes

Em Configurações > Sistema > Manutenção, escolha Escolher espelhos mais rápidos. O terminal explica a alteração; Enter confirma e Esc cancela. O Reflector seleciona até dez espelhos HTTPS sincronizados nas últimas 12 horas, ordenados pela velocidade de download. Prefere o país identificado pelo fuso horário do sistema, quando conhecido, e tenta espelhos mundiais se houver poucos candidatos. Os três servidores mundiais incluídos sempre ficam no final; se a classificação falhar, a lista não muda, incluindo espelhos próprios. Cada execução do reflector tem limite de dois minutos.

A lista anterior é salva ao lado de `/etc/pacman.d/mirrorlist` como `mirrorlist.eitr-<timestamp>.bak`. Quando existe um backup, o mesmo fluxo oferece restauração: digite `restore` e pressione Enter. A restauração também salva a lista atual. O resultado permanece visível até Esc.

Novas instalações agendam uma tentativa em segundo plano dois minutos após cada inicialização, até três tentativas com conexão. Inicializações sem conexão são ignoradas em silêncio e não contam; uma classificação bem-sucedida encerra as tentativas. O login nunca espera pela classificação. Use o menu depois se todas as tentativas falharem. Apenas os espelhos Arch mudam; os repositórios Eitr e Flatpak permanecem iguais.

Status somente de leitura: `/usr/lib/eitr/eitr-system mirrors-status` imprime JSON com `last_ranking_time` (UTC, ou null antes do primeiro sucesso), `mirror_count`, `shipped_fallback` e `backup_available`. Lê arquivos locais sem rede nem sudo.

A Atualização do sistema verifica novos commits dos plugins ao terminar, sem alterar versões aprovadas. Revise e instale separadamente em **Central de controle > Plugins > Atualizar plugins**, **Plugins > Atualizar plugins** ou `eitr plugin update`. Falhas de rede são ignoradas silenciosamente; os hooks after-update permanecem iguais.
