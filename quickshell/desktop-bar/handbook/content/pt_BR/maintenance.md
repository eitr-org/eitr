# Atualizações, limpeza e recuperação

Abra **Sistema > Manutenção**. Revise a saída do terminal e mantenha backups independentes antes de alterar o sistema. Snapshots não são backups em outro disco.

A atualização do sistema verifica primeiro os pacotes oficiais com checkupdates em um banco temporário separado, os pacotes AUR (incluindo os de desenvolvimento) e os Flatpaks do usuário. Se todas as verificações confirmarem que não há atualizações, termina sem snapshots, atualização ou pedido de reinicialização. Se uma verificação falhar ou faltar uma ferramenta, o fluxo normal continua.

## Atualização

**Atualizar > Atualização do sistema** é o fluxo normal de atualização completa de pacotes. Em uma nova instalação configurada do EITR, verifica o suporte a snapshots e cria snapshots anteriores e posteriores com arquivos de inicialização. Se a proteção falhar, a atualização não começa. Um desktop Arch existente sem a política da distribuição não precisa dessa configuração apenas para atualizar. A Atualização do sistema também atualiza aplicativos Flatpak, como GeForce NOW; falhas do Flatpak são informadas sem desfazer a atualização do sistema.

Antes de atualizar, a Atualização do sistema (e as atualizações do Pacman em Avançado) verifica notícias do Arch Linux publicadas desde a última atualização. Elas anunciam atualizações que exigem uma etapa manual. Havendo notícias, os títulos e links são mostrados e aparece **Continuar a atualização? [y/N]**: Enter cancela antes de qualquer alteração, para você ler a publicação primeiro. Sem notícias ou sem internet, o processo continua.

**Atualizar > Canal de atualização** lista os dois canais e marca o atual; escolher o outro pede sua senha em um terminal e muda o canal das atualizações do próprio Eitr. O padrão Stable recebe versões após serem testadas. Testing recebe novas compilações assim que são publicadas, para experimentar mudanças antes; o restante continua vindo do Arch. Voltar para Stable mantém uma versão mais recente do Eitr até o canal alcançar essa versão. No terminal, `eitr channel` mostra o canal; `eitr channel testing` ou `eitr channel stable` faz a troca.

Se uma atualização impedir a inicialização, a **proteção de inicialização** a desfaz: após duas tentativas consecutivas que não cheguem à tela de login, a próxima restaura o sistema e os arquivos de inicialização anteriores à atualização e reinicia. Sua pasta pessoal não é alterada, e o próximo login informa o ocorrido. Funciona em computadores instalados pelo instalador do Eitr; veja [Recuperação e snapshots](handbook:recovery).

**Snapshots da pasta pessoal** guardam versões anteriores dos seus arquivos: ative-os em **Sistema > Manutenção > Instantâneos > Snapshots da pasta pessoal**. São feitos a cada hora durante um dia e diariamente durante uma semana; os mais antigos são removidos quando falta espaço. Caches, Downloads, discos de VMs e jogos ficam de fora. Para recuperar um arquivo, escolha **Restaurar um arquivo ou pasta**, digite o caminho e escolha uma data. A versão anterior aparece ao lado da atual, sem substituí-la.

**Atualizar > Avançado** oferece **Pacman + Yay**, **Pacman** e **Yay (AUR)**. Essas opções não criam snapshots automáticos intencionalmente. Comandos diretos de pacman/yay também ignoram o fluxo protegido. Flatpaks, runtimes de desenvolvimento e dados pessoais separados não são cobertos por snapshots da raiz.

Evite atualizações parciais do Arch. Leia as mensagens dos pacotes em vez de aceitar uma remoção inesperada sem conferir. Tarefas bem-sucedidas fecham automaticamente; falhas ficam visíveis para você investigar sem perder a saída.

Após uma atualização bem-sucedida, uma notificação pede a conclusão quando necessário: **Reiniciar agora** após atualizações de kernel, firmware, microcódigo, systemd, glibc, driver de vídeo ou criptografia de disco; ou **Sair agora** após atualizações do desktop, como EITR, Hyprland, Quickshell, Walker ou PipeWire. **Mais tarde** permite continuar trabalhando; as novas versões passam a valer na próxima reinicialização ou sessão.

## Limpeza e snapshots

Limpeza executa a manutenção e mantém o relatório aberto para leitura. Revise as propostas; um pacote órfão não é necessariamente inútil. Instantâneos oferece os fluxos existentes de estado e configuração do Snapper. Veja [Recuperação e snapshots](handbook:recovery) para layouts compatíveis e limites dos carregadores de inicialização.

## Redefinição de fábrica

Somente uma instalação compatível da distribuição com o ponto de restauração do primeiro login pode ser redefinida. Essa base privada fica separada das listas e da limpeza normais do Snapper. O root ainda pode excluí-la, e uma falha no disco pode destruí-la. São exigidos dois avisos separados e uma confirmação digitada. Leia [Redefinição de fábrica](handbook:factory-reset) para saber exatamente o que Apagar Tudo e Manter os Meus Arquivos preservam.

## Energia

Principal > Energia e Central de controle > Geral oferecem bloqueio, encerramento de sessão, suspensão, reinicialização e desligamento. Salve seu trabalho primeiro. Essas ações realmente são executadas; não são demonstrações.
