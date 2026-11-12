# Central de controle

Pressione **SUPER + I** para abrir ou fechar a Central de controle. Ele abre pela borda atual da barra e fecha com Escape ou um clique fora. Ao fechar, volta à página Geral. Com a barra no modo Full à esquerda ou à direita, a Central começa no topo da tela, com o conteúdo espaçado dentro da superfície unida à barra.

Suas páginas são Geral, Plugins e Ferramentas. O botão de engrenagem abaixo delas, **Todas as configurações**, fecha a Central de controle e abre as Configurações, que reúnem aparência, barra, dispositivos, teclado, telas e sistema. As seções recolhíveis geralmente começam fechadas; clique no título para abrir ou fechar, com a escolha lembrada até sair da sessão. Quando a barra tem um painel próprio, como OBS, WiFi ou Bluetooth, a Central de controle o abre.

## Geral

<!-- eitr-figure: control-center -->

A página Geral. Os botões à esquerda alternam entre Geral, Plugins e Ferramentas; a engrenagem abaixo abre Configurações. Um controle ligado fica preenchido com a cor de destaque do tema.

- **Conectividade:** ligar/desligar WiFi e Bluetooth, além do Modo avião.
- **Ações rápidas:** Bloqueio automático, Não perturbe, Modo jogo (desativa efeitos, desfoque e pop-ups e ativa o perfil de desempenho até você desligá-lo) e Luz noturna.
- **Tela:** Ocultar barra (SUPER+Shift+Space a traz de volta) e Iniciar protetor de tela executam uma vez.
- **Som:** volume e ganho/mudo do microfone, e dois interruptores opcionais, desligados por padrão: **Sons de notificação** (um aviso, outro para notificações urgentes; as de baixa prioridade ficam em silêncio) e, em PCs com bateria, **Sons do carregador** ao conectar ou desconectar. Nenhum toca em Não perturbe nem no Modo jogo. Walker > Configurações > Dispositivos > Sons de eventos oferece os mesmos interruptores.
- **Tela:** brilho, em notebooks com tela integrada.
- **Mídia:** capa, artista, reprodução e avanço na faixa quando compatível.
- **Energia:** Bloquear e **Energia…**, que abre Sair, Suspender, Reiniciar e Desligar.

O Modo avião lembra quais conexões bloqueou e restaura apenas essas. Não perturbe suprime pop-ups sem limpar o histórico de notificações. Bloqueio automático não é o mesmo que impedir suspensão; cuide da privacidade da tela.

## Ferramentas

Timer e Foco (uma contagem regressiva, um cronômetro ou sessões de foco de 25 minutos com pausas de 5 minutos; um anel ao lado do relógio mostra que está rodando e o abre), capturas (seleção, tela inteira, janela ou seleção direto para a área de transferência), gravação (controles do OBS, Gravar, Gravar + Áudio e Parar), OCR, códigos QR, seletor de cores, Transcodificar, lembretes e compartilhamento com LocalSend. O painel fecha antes de uma seleção ou gravação começar.

## Conversa rápida

O ícone de conversa ao lado das abas abre uma conversa descartável com o assistente padrão, escolhido em Desenvolvimento > IA. Fica oculto sem um padrão ou quando a política da organização desativa assistentes. Enter envia; Shift+Enter insere uma quebra de linha. Escape ou Voltar retorna às páginas. Nova conversa, sair da conversa ou fechar o Centro de Controle apaga as mensagens e cancela uma resposta pendente.

As respostas permitem selecionar Markdown e copiar. A conversa fica na memória; o Eitr não grava histórico nem registros. A linha abaixo da entrada identifica o provedor na nuvem ou informa que o Ratatoskr roda neste PC. Provedores recebem as mensagens e os turnos anteriores. O resumo da máquina inclui versão/canal do Eitr, kernel, CPU/GPU/RAM e tema como contexto não confiável.

Não são coletados nomes de usuário ou máquina, arquivos, emails, nomes de WiFi, títulos de janelas ou área de transferência. O assistente usa a execução sem interface somente de leitura com a conta selecionada; não pode alterar o sistema. Falhas aparecem na conversa.

O assistente também recebe a introdução do Manual e trechos traduzidos relevantes, uma lista fixa de ferramentas instaladas e a informação de que há um monitor HDR conectado. Isso indica disponibilidade, não se um serviço está configurado. O assistente não pode executar comandos nem alterar configurações.

## Plugins

**Central de controle > Plugins** mostra uma linha compacta por plugin instalado, com ícone, nome e interruptor de ativação. Selecione uma linha para ver autor, versão, descrição, ações de atualização e remoção, widgets, itens da barra e prévia. Use Voltar ou Escape para retornar à lista. Ativar/Desativar preserva posições e interrompe ou restaura serviços, itens do Walker, hooks e elementos visuais; use `eitr plugin enable ID` ou `eitr plugin disable ID`.

Adicionar plugins, Atualizar e Remover abrem os fluxos revisados no terminal; remover pede confirmação. Geral mantém apenas os blocos de plugins. Falhas visuais têm uma ação independente para reativar.

Para instalação, revisão e atualizações seguras, veja [Apps e instalação](handbook:apps).

Para Configurações (**SUPER + ,**) e fotos de perfil, veja [Configurações](handbook:system).
