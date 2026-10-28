# Central de controle

Pressione **SUPER + ,** para abrir ou fechar a Central de controle. Ele abre pela borda atual da barra e fecha com Escape ou um clique fora. Ao fechar, volta à página Geral.

Suas cinco páginas reúnem tudo que fica fora de Desenvolvimento, Aplicativos, Instalar, Aprender e Jogos; assim, a maioria das configurações dispensa o Walker. As seções recolhíveis começam fechadas; clique no título para abrir ou fechar, com a escolha lembrada até sair da sessão. Quando há um painel próprio na barra (OBS, WiFi, Bluetooth, Áudio, Tela, Hardware, Uso de IA ou Clima), a Central de controle abre esse painel.

## Geral

- **Conectividade:** ligar/desligar WiFi e Bluetooth, além do Modo avião.
- **Atalhos rápidos:** Bloqueio automático, Notificações de falhas, Não perturbe, Modo jogo (desativa efeitos, desfoque e pop-ups e ativa o perfil de desempenho até você desligá-lo) e Luz noturna. Um controle ligado fica preenchido com a cor de destaque do tema. Abaixo, Ocultar barra (SUPER+Shift+Space a traz de volta) e Protetor de tela executam uma vez.
- **Som:** volume e ganho/mudo do microfone.
- **Tela:** brilho.
- **Mídia:** capa, artista, reprodução e avanço na faixa quando compatível.
- **Energia:** Bloquear e **Energia…**, que abre Sair, Suspender, Reiniciar e Desligar.

O Modo avião lembra quais conexões bloqueou e restaura apenas essas. Não perturbe suprime pop-ups sem limpar o histórico de notificações. Bloqueio automático não é o mesmo que impedir suspensão; cuide da privacidade da tela.

## Estilo

Tema e Papel de parede abrem seus carrosséis; Fonte padrão abre a lista de fontes. O tema da tela de bloqueio, cursor (família, tamanho e cor), aparência, layout, borda e monitores da barra, marcadores de espaços, cantos e Cursor Fire do Kitty mudam diretamente no painel e compartilham suas preferências com o Walker.

## Ferramentas

Capturas (seleção, tela inteira, janela ou seleção direto para a área de transferência), gravação (controles do OBS, Gravar, Gravar + Áudio e Parar), OCR, códigos QR, seletor de cores, Transcodificar, lembretes e compartilhamento com LocalSend. O painel fecha antes de uma seleção ou gravação começar.

## Sistema

- **Dispositivos:** painéis de Áudio, Microfone, Tela (resolução, taxa de atualização e escala), Bluetooth e WiFi, Iluminação e limite de carga em notebooks.
- **Teclado:** selecionar, adicionar e remover layouts, mantendo pelo menos um.
- **Luz noturna e tela principal:** modo e programação da Luz noturna, separados do botão manual, e o monitor principal que recebe a barra.
- **Informações:** Sobre, Hardware, Uso de IA, Clima e Relatar um problema.
- **Atualizações:** canal, Atualização do sistema, mudanças de cada atualização e atualizações só de Pacman ou AUR.
- **Snapshots e limpeza:** restaurar arquivo, snapshots pessoais e de recuperação, o guia correspondente, Limpeza e Dotfiles.

Segurança, redefinição de fábrica e backend de rede continuam em Walker > Sistema, protegidos por suas próprias confirmações.

## Idioma

**Sistema > Idioma** mostra o idioma atual conforme a localidade do sistema. Abra o seletor, escolha um idioma ou Padrão do sistema e saia e entre novamente para aplicar. Ele altera apenas o idioma de mensagens da sua sessão, nunca os arquivos de localidade do sistema. Consulte o [Guia de idioma](handbook:language).

## Conversa rápida

O ícone de conversa ao lado das abas abre uma conversa descartável com o assistente padrão, escolhido em Desenvolvimento > IA. Fica oculto sem um padrão ou quando a política da organização desativa assistentes. Enter envia; Shift+Enter insere uma quebra de linha. Escape ou Voltar retorna às páginas. Nova conversa, sair da conversa ou fechar o Centro de Controle apaga as mensagens e cancela uma resposta pendente.

As respostas permitem selecionar Markdown e copiar. A conversa fica na memória; o Eitr não grava histórico nem registros. A linha abaixo da entrada identifica o provedor na nuvem ou informa que o Ratatoskr roda neste PC. Provedores recebem as mensagens e os turnos anteriores. Cada mensagem inclui apenas versão/canal do Eitr, kernel, CPU/GPU/RAM e tema como contexto não confiável. Não são coletados nomes de usuário ou máquina, arquivos, emails, nomes de WiFi, títulos de janelas ou área de transferência. O assistente usa a execução sem interface somente de leitura com a conta selecionada; não pode alterar o sistema. Falhas aparecem na conversa.

## Plugins

**Central de controle > Plugins** mostra uma linha compacta por plugin instalado, com ícone, nome e interruptor de ativação. Selecione uma linha para ver autor, versão, descrição, ações de atualização e remoção, widgets, itens da barra e prévia. Use Voltar ou Escape para retornar à lista. Ativar/Desativar preserva posições e interrompe ou restaura serviços, itens do Walker, hooks e elementos visuais; use `eitr plugin enable ID` ou `eitr plugin disable ID`. Adicionar plugin…, Atualizar e Remover abrem os fluxos revisados no terminal; remover pede confirmação. Geral mantém apenas os blocos de plugins. Falhas visuais têm uma ação independente para reativar.

Adicionar plugin… também aceita repositórios com vários plugins. O índice `eitr-plugins.json` na raiz lista seus IDs e pastas, cada uma com seu próprio `eitr-plugin.json`. Selecione um ou mais pelo nome, descrição e ícone e revise cada plugin separadamente. Recusar um não aprova os demais. Os selecionados compartilham uma cópia do repositório e ficam fixados individualmente no commit exato; atualizar um mantém os outros nos commits aprovados. Os detalhes mostram a URL do repositório e a pasta do plugin. Um único `eitr-plugin.json` na raiz continua funcionando como antes.
