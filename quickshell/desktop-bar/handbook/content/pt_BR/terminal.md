# Terminal e editores

**SUPER + Enter** abre o terminal escolhido (Kitty por padrão). **SUPER + Ctrl + Enter** abre ou conecta à sessão principal do tmux. **SUPER + P** busca arquivos por correspondência aproximada; **SUPER + Ctrl + P** busca no conteúdo. Aprender > Comandos Cmux, Comandos Tmux e Comandos LazyVim são referências pesquisáveis; selecionar um comando o copia, sem executá-lo.

O Kitty mostra uma trilha curta em saltos de pelo menos duas células, como Enter, Home/End ou movimentos entre palavras. Ela começa após o cursor ficar parado por 3 ms e desaparece em 0,05–0,15 segundo. Ajuste `cursor_trail`, `cursor_trail_decay` ou `cursor_trail_start_threshold` em `~/.config/kitty/local.conf`; `cursor_trail 0` desativa a trilha. Suas opções têm prioridade sobre as do pacote e são mantidas nas trocas de tema.

### Fogo do cursor

**Estilo > Terminal > Fogo do cursor** oferece **Desativado** (padrão) e **Ativado**. Ativado usa o efeito `cursor-trail-blaze` integrado do Kitty nos movimentos do cursor, sem detectar velocidade de digitação. Desativado restaura a trilha rápida normal e a seleção pessoal de shader.

O efeito exige Kitty 0.49+ e `shader-slang`, incluídos nas dependências do Eitr. A ativação valida o shader antes de salvar ou recarregar o Kitty. A preferência local fica em `~/.config/eitr/terminal.json`; o auxiliar escreve `kitty/cursor-fire.conf`, incluído por último pelo carregador do usuário. Ativado, escolhe o shader de fogo e reduz o limiar para uma célula. Fontes, temas e configurações pessoais permanecem intactos.

## Escolher o terminal

**Estilo > Terminal** no Walker e **Central de controle > Estilo > Terminal** oferecem
**Kitty** (padrão) e **Ghostty**. O campo local `terminal` em
`~/.config/eitr/terminal.json` controla Super+Enter, tmux, sessões do usuário,
terminais de IA/projetos e ações do Walker para abrir no terminal. Se Ghostty não
estiver instalado, escolhê-lo abre o fluxo normal de instalação do pacote oficial:
Enter instala e Esc cancela. Kitty continua selecionado até a instalação terminar
com sucesso. Se Ghostty for removido depois, os lançamentos usam Kitty.
Ghostty é opcional e não faz parte do conteúdo da ISO.

Trocar o tema regenera `~/.config/ghostty/eitr.conf` com as 16 cores ANSI e as cores
de fundo, texto, seleção e cursor de texto. Alterar a fonte atualiza a família
escolhida; o tamanho padrão é 10 pontos. Ghostty usa o mesmo zsh e prompt, com
75% de opacidade e sem espaçamento interno em janelas normais. Hyprland fornece
desfoque, decorações e regras normais de janela. Família, tamanho e escolha
Auto/Claro/Escuro do ponteiro em `eitr/cursor.json` continuam valendo pelo GTK e
compositor, separados do cursor de texto.

O lançador do Eitr carrega o arquivo gerado. Coloque ajustes pessoais como
`font-size = 12` ou `cursor-style = bar` em `~/.config/ghostty/local.conf`, carregado
por último e preservado nas trocas de tema. Sessões abertas recebem o sinal de
recarga suportado após mudar tema ou fonte. Algumas opções só afetam novas janelas.
O rastro e o Fogo do cursor do Kitty são exclusivos dele; Ghostty não tem uma
opção Blaze integrada equivalente.

Os terminais de tarefas, menus, status e configuração do Eitr sempre usam Kitty,
incluindo `eitr-menu-terminal`, `eitr-plugins` e `fif-terminal`: suas opções
`--class`, `--hold`, `--title` e regras de janelas flutuantes dependem do Kitty.
Escolher Ghostty não os altera.


## O comando eitr

`eitr` reúne as ferramentas do Eitr; execute-o sem argumentos para listar opções. Usa os mesmos scripts dos menus, mantendo o mesmo comportamento.

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Eitr" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
eitr about
```

`eitr about` abre a janela de informações do Eitr ou traz a janela existente para o primeiro plano.

`eitr config` e `eitr git` encaminham argumentos para `eitr-config` e `eitr-git`. Cada comando oferece `--help`.

## Seus próprios hooks

Um hook é um pequeno script seu que o Eitr executa em um momento específico, permitindo ampliar o comportamento sem alterar o Eitr. Coloque um executável com o nome desse momento em `~/.config/eitr/hooks/`:

| Arquivo | Quando executa | Argumento recebido |
| --- | --- | --- |
| `post-update` | após Atualização do sistema ou atualização pacman/AUR | `system`, `pacman`, `yay` ou `full` |
| `theme-set` | após trocar o tema | nome da pasta do tema |
| `battery-low` | uma vez sempre que a bateria cai para 15% | percentual |
| `post-boot` | no primeiro login após cada inicialização | nenhum |

Por exemplo, para recolorir o Spotify com Spicetify a cada troca de tema, crie `~/.config/eitr/hooks/theme-set`:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

Torne-o executável com `chmod +x ~/.config/eitr/hooks/theme-set`. Cada hook pode levar até 60 segundos; saída e falhas vão para `~/.local/state/eitr/hooks.log`. Uma falha nunca interrompe a atualização ou troca de tema. `eitr hook list` lista os hooks existentes; `eitr hook run theme-set eitr` testa um. Atualizações nunca alteram essa pasta.

## cmux TUI

Execute `cmux` no Kitty ou `cmux --session work` para nomear a sessão. cmux TUI é opcional, ao lado do tmux; não substitui Kitty nem seus atalhos. Novas instalações incluem um binário oficial com versão fixada em `/usr/bin/cmux`; instalações pessoais anteriores podem ter prioridade no PATH. Confira com `command -v cmux`. `less` é incluído para ler saídas e arquivos de texto.

O prefixo padrão é **Ctrl-b**: solte as teclas e pressione a próxima.

| Atalho | Ação |
| --- | --- |
| Ctrl-b ? | Mostrar atalhos atuais |
| Ctrl-b W | Criar espaço de trabalho |
| Ctrl-b c | Criar tela |
| Ctrl-b % / Ctrl-b " | Dividir à direita / abaixo |
| Ctrl-b t | Nova aba de terminal |
| Ctrl-b h/j/k/l | Focar esquerda/abaixo/acima/direita |
| Ctrl-b s | Mostrar/ocultar barra lateral |
| Ctrl-b d | Sair localmente ou desconectar de um servidor |

Para continuar a sessão sem a interface, execute `cmux --headless --session work` e depois `cmux attach --session work` para reconectar. Abas de navegador exigem Chrome/Chromium. Fechar abas, painéis ou espaços pode afetar tarefas em execução; confira antes. Aprender > Comandos Cmux inclui comandos de sessão, navegação, mouse e fechamento. Os padrões podem mudar ou ser personalizados; **Ctrl-b ?** é a referência atual.

## Terminais de tarefas

Terminais abertos por menus e pelas notificações de atualização e relatório ficam centralizados sobre suas janelas, com fundo sólido do tema. Sessões de assistentes de IA e projetos LazyVim, em Desenvolvimento, abrem como janelas normais em mosaico, com fundo translúcido, assim como terminais abertos por você. Terminais comuns são interativos e não exibem marca. Instalação, atualização e configuração mostram o banner rúnico do EITR; tarefas bem-sucedidas normalmente fecham, falhas permanecem até serem dispensadas. Relatórios informativos podem ficar abertos. Reiniciar o Elephant não deve fechar aplicativos lançados: aplicativos e terminais abertos por menus, atalhos e botões da barra usam escopos de aplicação separados em uma sessão uwsm. Sem uwsm, eles são iniciados diretamente. O Elephant mantém o encerramento somente do processo para auxiliares da área de trabalho e inicializações sem uwsm.

Pressione **Esc** para fechar terminais de tarefas, contas, relatórios e Sobre que aguardam uma tecla. Enter continua sendo usado para respostas e confirmações, incluindo confirmar que a chave de recuperação foi anotada e desligar o instalador.

## Histórico do shell

`history` lista comandos recentes. No zsh, confira o caminho real com:

```sh
printf '%s\n' "$HISTFILE"
```

Para abri-lo no Neovim:

```sh
nvim "$HISTFILE"
```

O histórico pode conter tokens e credenciais; não o copie para relatórios de problemas. Feche outros shells antes de editar manualmente, pois podem gravar o histórico ainda em memória. O histórico estendido do zsh pode conter horários e comandos de várias linhas: remova a entrada inteira, não um fragmento arbitrário. Faça um backup privado se precisar desfazer.

## Aparência dos editores

Trocas de tema atualizam as preferências geradas de VS Code e LazyVim. Sessões LazyVim compatíveis atualizam sem reabrir. Suas personalizações e plugins podem escolher cores próprias; confira a configuração se um editor não acompanhar o desktop. A fonte padrão só é integrada onde o aplicativo oferece suporte.
