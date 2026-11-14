# Encontrar uma configuração

Pressione **SUPER + ,** para abrir Configurações. Sistema é a visão geral, não uma pasta com todas as configurações.

Pesquise uma configuração individual, como **Tamanho do ponteiro**, ou uma página na barra lateral de Configurações. Os resultados mostram a página e a aba abaixo do nome. Use Cima/Baixo e Enter, ou clique, para abrir a aba, rolar até o controle e destacá-lo brevemente. Esc limpa a pesquisa primeiro. Com movimento reduzido, o destaque aparece e desaparece sem transição.

<!-- eitr-figure: settings-window -->

A janela Configurações tem uma barra lateral com busca e cartões para controles relacionados. Clicar fora não a fecha. Use Esc, o botão de fechar ou o atalho normal para fechar janelas.

Links no rodapé dos painéis fecham o painel e abrem a página correspondente de Configurações. Todas as configurações na Central de controle faz o mesmo; **SUPER + I** abre os controles rápidos. Veja [Central de controle](handbook:control-center).

Escolha Cores das configurações em Configurações > Aparência > Tema e papel de parede: Cores do tema acompanha o desktop; Site do Eitr usa a paleta do site. Isso afeta Configurações, o Manual e Eitr Store, não o tema da área de trabalho. Walker > Configurações > Área de trabalho > Aparência > Cores das configurações abre essa escolha.

O catálogo separado Eitr Store abre com SUPER + F2 ou Mais temas em Aparência.

## Escolher uma página

Use os nomes de página abaixo. Os capítulos vinculados explicam os passos.

| Página | Saiba mais |
| :--- | :--- |
| Sistema | [Sistema](handbook:information) |
| Telas — Telas, Luz noturna | [Telas](handbook:devices) |
| Som | [Som](handbook:devices) |
| Conexões — Wi-Fi, Bluetooth | [Conexões](handbook:connectivity) |
| Streaming | [Streaming](handbook:remote-access) |
| Entrada | [Entrada](handbook:devices) |
| Aparência — Tema e papel de parede, Fontes e cursor, Terminal | [Aparência](handbook:appearance) |
| Barra da área de trabalho | [Barra da área de trabalho](handbook:desktop-bar) |
| Janelas | [Janelas](handbook:appearance) |
| Tela de bloqueio | [Tela de bloqueio](handbook:appearance) |
| Notificações | [Notificações](handbook:information) |
| Focus | [Focus](handbook:focus) |
| Assistente de IA | [Assistente de IA](handbook:development) |
| Atalhos de teclado | [Atalhos de teclado](handbook:shortcuts) |
| Regras de janelas | [Regras de janelas](handbook:apps) |
| Apps padrão | [Apps padrão](handbook:apps) |
| Usuários | [Usuários](handbook:security) |
| Segurança | [Segurança](handbook:security) |
| Atualizações | [Atualizações](handbook:maintenance) |
| Verificar este PC | [Verificar este PC](handbook:troubleshooting) |
| Sobre | [Sobre](handbook:information) |

## Alterar sua foto de perfil

Abra Configurações > Usuários (ou clique na sua foto na visão geral Sistema das Configurações) e clique na sua foto. O seletor de arquivos do sistema abre flutuante, centralizado sobre as Configurações, mostrando só imagens; ao escolher uma, o editor de recorte abre em uma folha sobre as Configurações. Arraste a prévia circular para mover a imagem; use a roda, o controle deslizante ou +/− para ampliar de 1× a 4×, e as setas para mover.

Salvar (ou Enter) aplica o recorte; Cancelar ou Esc fecha a folha sem aplicá-lo. O ícone de lixeira abaixo da sua foto a remove depois que você confirma.

A foto aparece sempre como um círculo no Centro de Controle, no bloqueio e na tela de login. O Centro de Controle apenas exibe a foto no topo da navegação; sem foto, não mostra nada ali, assim como o bloqueio e a tela de login. As Configurações mostram em vez disso a inicial do seu nome sobre um círculo na cor de destaque.

PNG, JPEG, WebP, GIF (primeiro quadro) e BMP são aceitos até 40 MB e 12000 pixels por lado. O Eitr aplica a orientação, remove metadados, salva um PNG de 512×512 em `~/.face` e atualiza o AccountsService para o SDDM. Se a atualização falhar, a foto salva continua funcionando no bloqueio; a interface ou CLI informa o erro da tela de login.

## Alterar sua senha

Abra Configurações > Usuários e escolha Alterar senha ao lado do seu nome. Digite a senha atual e depois a nova duas vezes: Enter passa para o próximo campo e confirma no último; Esc cancela. As regras de senha do sistema decidem o que é aceito, e uma senha recusada mostra o motivo. O Eitr também muda o chaveiro de login para a nova senha, para que as senhas salvas continuem sendo desbloqueadas ao entrar. A frase de criptografia do disco é separada e continua a mesma. Walker > Configurações > Segurança > Atualizar senha faz o mesmo em um terminal.

## Gerenciar contas

Administradores têm as abas **Usuários** e **Gerenciar** em Configurações > Usuários. Contas padrão veem apenas a lista de usuários. Gerenciar oferece Criar usuário…, Alterar tipo, Definir senha de outras contas e Remover com uma opção para a pasta pessoal. Confirme na folha e depois pressione Enter no terminal de tarefa para continuar ou Esc para cancelar; digite senhas apenas nesse terminal. Pastas pessoais são mantidas por padrão. Veja [Contas de usuário](handbook:security) para permissões, limitações do chaveiro e proteções de remoção.

## Usar o Walker como alternativa

**SUPER + F** abre o Walker. O menu Configurações segue os grupos do aplicativo Configurações: Dispositivos, Área de trabalho, Apps e teclas, Contas e segurança e Sistema, com Central de controle e Dotfiles no fim. Apps e teclas abre as páginas Apps padrão e Atalhos de teclado do aplicativo Configurações.

<!-- eitr-figure: launcher -->

O menu Configurações do Walker é uma alternativa com suas próprias pastas. > abre um submenu; a descrição abaixo de uma ação explica o que ela faz.

O Walker mostra pastas antes das ações. Digite para buscar, pressione Enter para abrir e Shift + Backspace para voltar. O idioma continua em Walker > Configurações > Dispositivos > Idioma; veja [Idioma](handbook:language).
