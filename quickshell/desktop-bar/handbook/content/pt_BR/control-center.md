# Central de controle

Pressione **SUPER + I** para abrir ou fechar a Central de controle. Ele abre pela borda atual da barra e fecha com Escape ou um clique fora. Ao fechar, volta à página Geral. Com a barra no modo Full à esquerda ou à direita, a Central começa no topo da tela, com o conteúdo espaçado dentro da superfície unida à barra.

Suas páginas são Geral, Plugins e Ferramentas. O botão de engrenagem abaixo delas, **Todas as configurações**, fecha a Central de controle e abre as Configurações, que reúnem aparência, barra, dispositivos, teclado, telas e sistema. As seções recolhíveis geralmente começam fechadas; clique no título para abrir ou fechar, com a escolha lembrada até sair da sessão. Quando a barra tem um painel próprio, como OBS, WiFi ou Bluetooth, a Central de controle o abre.

## Geral

<!-- eitr-figure: control-center -->

A página Geral. Os botões à esquerda alternam entre Geral, Plugins e Ferramentas; a engrenagem abaixo abre Configurações. Um controle ligado fica preenchido com a cor de destaque do tema.

- **Conectividade:** WiFi e Bluetooth abrem ali mesmo suas redes e dispositivos, cada um com seu interruptor e uma seta para voltar; além do Modo avião.
- **Ações rápidas:** Bloqueio automático, Não perturbe, Modo jogo (desativa efeitos, desfoque e pop-ups e ativa o perfil de desempenho até você desligá-lo) e Luz noturna.
- **Tela:** Ocultar barra (SUPER+Shift+Space a traz de volta) e Iniciar protetor de tela executam uma vez.
- **Som:** Som e Microfone abrem seus dispositivos ali mesmo; volume e ganho/mudo do microfone, e dois interruptores opcionais, desligados por padrão: **Sons de notificação** (um aviso, outro para notificações urgentes; as de baixa prioridade ficam em silêncio) e, em PCs com bateria, **Sons do carregador** ao conectar ou desconectar. Nenhum toca em Não perturbe nem no Modo jogo. Walker > Configurações > Dispositivos > Sons de eventos oferece os mesmos interruptores.
- **Tela:** brilho, em notebooks com tela integrada.
- **Mídia:** capa, artista, reprodução e avanço na faixa quando compatível.
- **Energia:** Bloquear e **Energia…**, que abre Sair, Suspender, Reiniciar e Desligar.

O Modo avião lembra quais conexões bloqueou e restaura apenas essas. Não perturbe suprime pop-ups sem limpar o histórico de notificações. Bloqueio automático não é o mesmo que impedir suspensão; cuide da privacidade da tela.

## Ferramentas

Timer e Foco (um resumo compacto mostrando o temporizador, a fase de foco ou o cronômetro ativo, botões rápidos para iniciar/parar um timer de 5 minutos ou foco e Abrir Relógio), capturas (seleção, tela inteira, janela ou seleção direto para a área de transferência), gravação (controles do OBS, Gravar, Gravar + Áudio e Parar), OCR, códigos QR, seletor de cores, Transcodificar, lembretes e compartilhamento com LocalSend. O painel fecha antes de uma seleção ou gravação começar.

**Diagnóstico:** **Info da janela** inspeciona a última janela ativa (aplicativo, título, classe, PID, área de trabalho, geometria e estado flutuante/fixada/tela cheia) e permite alternar flutuante/lado a lado, fixar/desafixar, mover para outra área de trabalho ou fechar; também disponível em **Walker > Ferramentas > Info da janela**. **Teste de velocidade** executa sob demanda um teste sequencial de gravação/leitura de 256 MB em disco na pasta de cache da unidade raiz, ou um teste de latência, download e upload via HTTPS contra `speed.cloudflare.com`; ambos podem ser cancelados durante a execução.

## Conversa rápida

O ícone de conversa ao lado das abas abre uma conversa descartável com o assistente padrão, escolhido em Desenvolvimento > IA. Fica oculto sem um padrão ou quando a política da organização desativa assistentes. Enter envia; Shift+Enter insere uma quebra de linha. Escape ou Voltar retorna às páginas. Nova conversa, sair da conversa ou fechar o Centro de Controle apaga as mensagens e cancela uma resposta pendente.

As respostas permitem selecionar Markdown e copiar. A conversa fica na memória; o Eitr não grava histórico nem registros. A linha abaixo da entrada identifica o provedor na nuvem ou informa que o Ollama roda neste PC. Provedores recebem as mensagens e os turnos anteriores. O resumo da máquina inclui versão/canal do Eitr, kernel, CPU/GPU/RAM e tema como contexto não confiável.

Não são coletados nomes de usuário ou máquina, arquivos, emails, nomes de WiFi, títulos de janelas ou área de transferência. O assistente usa a execução sem interface somente de leitura com a conta selecionada; não pode alterar o sistema. Falhas aparecem na conversa.

O assistente também recebe a introdução do Manual e trechos traduzidos relevantes, uma lista fixa de ferramentas instaladas e a informação de que há um monitor HDR conectado. Isso indica disponibilidade, não se um serviço está configurado. O assistente não pode executar comandos nem alterar configurações.

## Plugins

**Central de controle > Plugins** mostra uma linha compacta por plugin instalado, com ícone, nome e interruptor de ativação. Selecione uma linha para ver autor, versão, descrição, ações de atualização e remoção, widgets (com título, quantas cópias estão posicionadas e um botão para adicionar), itens da barra (cada um com seu interruptor **Mostrar na barra** e posição) e prévia. Desativar **Mostrar na barra** oculta esse item em todos os layouts mantendo o plugin e seus widgets de área de trabalho ativos. Use Voltar ou Escape para retornar à lista. Ativar/Desativar preserva posições e interrompe ou restaura serviços, itens do Walker, hooks e elementos visuais; use `eitr plugin enable ID` ou `eitr plugin disable ID`.

Adicionar plugins, Atualizar e Remover abrem os fluxos revisados no terminal; remover pede confirmação. Geral mantém apenas os blocos de plugins. Falhas visuais têm uma ação independente para reativar.

Para instalação, revisão e atualizações seguras, veja [Apps e instalação](handbook:apps).

Para Configurações (**SUPER + ,**) e fotos de perfil, veja [Configurações](handbook:system).
