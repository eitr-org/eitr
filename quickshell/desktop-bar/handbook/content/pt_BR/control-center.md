# Central de controle

Configurações e painéis da barra compartilham os controles de seleção. Opções curtas usam segmentos; listas maiores abrem como listas suspensas flutuantes com rolagem. Os interruptores mantêm suas ações. Rótulos dourados e letras entalhadas pertencem à família de janelas das Configurações: Configurações, o Manual e Temas e plugins.

As listas suspensas permitem digitar para navegar quando o seletor ou a lista tem foco. Digite o início de um rótulo para destacar a primeira opção correspondente; maiúsculas e acentos são ignorados. Teclas digitadas em até 800 ms formam o prefixo; após uma pausa, começa um novo prefixo. Repetir uma letra percorre as opções correspondentes. Enter aplica a opção destacada e Esc cancela. As listas mostram no máximo oito linhas e permitem rolagem. Abrem abaixo do campo, mesmo além da borda de um painel da barra, ou acima quando há mais espaço na tela nessa direção.

**SUPER + ,** abre Configurações em **Sistema**, com perfil e visão geral. Temas e Plugins têm sua própria janela de catálogo. **SUPER + I** abre a Central de controle.

## Configurações

Os grupos são Visão geral, Dispositivos, Área de trabalho, Aplicativos e teclas, Contas e segurança e Sistema. Títulos com runas e um marcador dourado deslizante ajudam na navegação. Cada página tem título, descrição e cartões de ajustes. A janela continua opaca. O Manual e Temas e plugins usam a mesma moldura, barra lateral, cabeçalho de página e cartões, e seguem a mesma escolha de cores.

Conexões tem abas **Wi-Fi** (com a escolha do backend) e **Bluetooth**. Monitores separa **Telas** e **Luz noturna**. Aparência separa **Tema e papel de parede**, **Fontes e cursor** e **Terminal**. Esquerda/Direita muda a aba com foco; a busca abre a aba correspondente. `settings show connections/bluetooth` abre Bluetooth; `network` continua como alias. Os cartões mostram layouts da barra, bordas, superfícies, visualizadores, espaçamentos, cantos e telas de bloqueio. **Cores das configurações** permite escolher **Cores do tema** ou **Site do Eitr** para as Configurações, o Manual e Temas e plugins. A preferência local fica em `eitr/settings-app.json`; `settings palette theme` e `settings palette website` também mudam essa escolha, sem alterar as cores do desktop.

Sistema mostra uma visão geral com sua foto, uso de CPU/GPU/RAM, tela principal, tempo de atividade, versão do Eitr, canal de atualização e paleta do tema. O hardware só é atualizado enquanto esta página está visível. A imagem grande mostra o papel de parede por enquanto. O serviço de dados compartilhado não fornece taxas de transferência de rede.

**SUPER + F2**, **Mais temas** em Aparência e o **+** do carrossel abrem o catálogo separado com barra lateral **Temas e plugins** e botão de fechar. Configurações permanece aberta ao clicar fora; Escape ou Fechar a encerram. **SUPER + I** abre a Central de controle.

Pressione **SUPER + I** para abrir ou fechar a Central de controle. Ele abre pela borda atual da barra e fecha com Escape ou um clique fora. Ao fechar, volta à página Geral. Com a barra no modo Full à esquerda ou à direita, a Central começa no topo da tela, com o conteúdo espaçado dentro da superfície unida à barra.

Suas páginas são Geral, Plugins e Ferramentas. O botão de engrenagem abaixo delas, **Todas as configurações**, fecha a Central de controle e abre as Configurações, que reúnem aparência, barra, dispositivos, teclado, telas e sistema. As seções recolhíveis geralmente começam fechadas; clique no título para abrir ou fechar, com a escolha lembrada até sair da sessão. Quando a barra tem um painel próprio, como OBS, WiFi ou Bluetooth, a Central de controle o abre.

## Geral

- **Conectividade:** ligar/desligar WiFi e Bluetooth, além do Modo avião.
- **Ações rápidas:** Bloqueio automático, Notificações de falhas, Não perturbe, Modo jogo (desativa efeitos, desfoque e pop-ups e ativa o perfil de desempenho até você desligá-lo) e Luz noturna. Um controle ligado fica preenchido com a cor de destaque do tema. Abaixo, Ocultar barra (SUPER+Shift+Space a traz de volta) e Protetor de tela executam uma vez.
- **Som:** volume e ganho/mudo do microfone, e dois interruptores opcionais, desligados por padrão: **Sons de notificação** (um aviso, outro para notificações urgentes; as de baixa prioridade ficam em silêncio) e, em PCs com bateria, **Sons do carregador** ao conectar ou desconectar. Nenhum toca em Não perturbe nem no Modo jogo.
- **Tela:** brilho, em notebooks com tela integrada.
- **Mídia:** capa, artista, reprodução e avanço na faixa quando compatível.
- **Energia:** Bloquear e **Energia…**, que abre Sair, Suspender, Reiniciar e Desligar.

O Modo avião lembra quais conexões bloqueou e restaura apenas essas. Não perturbe suprime pop-ups sem limpar o histórico de notificações. Bloqueio automático não é o mesmo que impedir suspensão; cuide da privacidade da tela.

## Ferramentas

Capturas (seleção, tela inteira, janela ou seleção direto para a área de transferência), gravação (controles do OBS, Gravar, Gravar + Áudio e Parar), OCR, códigos QR, seletor de cores, Transcodificar, lembretes e compartilhamento com LocalSend. O painel fecha antes de uma seleção ou gravação começar.

## Conversa rápida

O ícone de conversa ao lado das abas abre uma conversa descartável com o assistente padrão, escolhido em Desenvolvimento > IA. Fica oculto sem um padrão ou quando a política da organização desativa assistentes. Enter envia; Shift+Enter insere uma quebra de linha. Escape ou Voltar retorna às páginas. Nova conversa, sair da conversa ou fechar o Centro de Controle apaga as mensagens e cancela uma resposta pendente.

As respostas permitem selecionar Markdown e copiar. A conversa fica na memória; o Eitr não grava histórico nem registros. A linha abaixo da entrada identifica o provedor na nuvem ou informa que o Ratatoskr roda neste PC. Provedores recebem as mensagens e os turnos anteriores. Cada mensagem inclui apenas versão/canal do Eitr, kernel, CPU/GPU/RAM e tema como contexto não confiável. Não são coletados nomes de usuário ou máquina, arquivos, emails, nomes de WiFi, títulos de janelas ou área de transferência. O assistente usa a execução sem interface somente de leitura com a conta selecionada; não pode alterar o sistema. Falhas aparecem na conversa.

## Plugins

**Configurações > Estilo > Temas e plugins** no Walker, **Mais temas** na página Aparência das Configurações ou **SUPER + F2** abre a janela Temas e plugins. O grupo Plugins lista os plugins instalados, oficiais e da comunidade, instala e atualiza após uma revisão na janela, verifica atualizações e remove plugins instalados após confirmação. Os fluxos de terminal abaixo continuam disponíveis.

**Central de controle > Plugins** mostra uma linha compacta por plugin instalado, com ícone, nome e interruptor de ativação. Selecione uma linha para ver autor, versão, descrição, ações de atualização e remoção, widgets, itens da barra e prévia. Use Voltar ou Escape para retornar à lista. Ativar/Desativar preserva posições e interrompe ou restaura serviços, itens do Walker, hooks e elementos visuais; use `eitr plugin enable ID` ou `eitr plugin disable ID`. Adicionar plugins, Atualizar e Remover abrem os fluxos revisados no terminal; remover pede confirmação. Geral mantém apenas os blocos de plugins. Falhas visuais têm uma ação independente para reativar.

Adicionar plugins também aceita repositórios com vários plugins. O índice `eitr-plugins.json` na raiz lista seus IDs e pastas, cada uma com seu próprio `eitr-plugin.json`. Selecione um ou mais pelo nome, descrição e ícone e revise cada plugin separadamente. Recusar um não aprova os demais. Os selecionados compartilham uma cópia do repositório e ficam fixados individualmente no commit exato; atualizar um mantém os outros nos commits aprovados. Os detalhes mostram a URL do repositório e a pasta do plugin. Um único `eitr-plugin.json` na raiz continua funcionando como antes.

A Atualização do sistema apenas verifica novos commits dos plugins, mesmo quando os pacotes estão atualizados, e informa a quantidade e onde atualizar. Ela não revisa nem atualiza plugins; erros de rede são ignorados silenciosamente. Use **Atualizar plugins** em **Central de controle > Plugins**, ao lado de Adicionar plugins, ou **Plugins > Atualizar plugins**, ou execute `eitr plugin update`. A marca ↑ na linha e “Atualização disponível” nos detalhes refletem a última verificação do commit aprovado. A ação separada mantém os diffs, alertas de risco e confirmações por plugin.

A lista de Plugins mostra “Este plugin tem erros” e a primeira mensagem. Selecione o plugin e escolha Ver detalhes dos erros para saber mais; use o interruptor para desativá-lo com um clique. Só são identificados os erros que indicam um arquivo na pasta do plugin. Plugins têm as mesmas permissões do desktop, então instale apenas aqueles em que você confia.

## Fotos de perfil

Abra Configurações > Usuário (ou clique na sua foto na visão geral Sistema das Configurações) e escolha Alterar foto. O seletor de arquivos do sistema abre flutuante, centralizado sobre as Configurações, mostrando só imagens; ao escolher uma, o editor de recorte abre em uma folha sobre as Configurações. Arraste a prévia circular para mover a imagem; use a roda, o controle deslizante ou +/− para ampliar de 1× a 4×, e as setas para mover. Salvar (ou Enter) aplica o recorte; Cancelar ou Esc fecha a folha sem aplicá-lo. Remover, ao lado de Alterar foto, apaga a foto.

A foto aparece sempre como um círculo no Centro de Controle, no bloqueio e na tela de login. O Centro de Controle apenas exibe a foto no topo da navegação; sem foto, não mostra nada ali, assim como o bloqueio e a tela de login. As Configurações mostram em vez disso a inicial do seu nome sobre um círculo na cor de destaque. PNG, JPEG, WebP, GIF (primeiro quadro) e BMP são aceitos até 40 MB e 12000 pixels por lado. O Eitr aplica a orientação, remove metadados, salva um PNG de 512×512 em `~/.face` e atualiza o AccountsService para o SDDM. Se a atualização falhar, a foto salva continua funcionando no bloqueio; a interface ou CLI informa o erro da tela de login.

## Mais páginas de Configurações

Atalhos lista toda a referência de Aprender com busca. Aplicativos padrão permite escolher programas instalados para navegador, arquivos, texto, imagens, vídeo, música, e-mail e PDF; Terminal usa a preferência de Aparência > Terminal. Usuário mostra sua foto e seu nome com Alterar foto e Remover. Git e nuvem mostra identidades, regras de pastas e contextos; os botões abrem os fluxos existentes do Walker. Segurança mantém as confirmações para mudanças privilegiadas. Atualizações mostra o canal e os pacotes pendentes; Atualizar sistema abre o fluxo existente. Verificar este PC executa diagnósticos somente de leitura apenas ao pressionar o botão. Sobre mostra versão, kernel, hardware, licença e links. Todas as páginas permitem rolar até a última linha e abrem o Manual.
