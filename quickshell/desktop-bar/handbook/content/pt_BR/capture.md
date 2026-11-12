# Captura e compartilhamento

Capturas de tela e gravações ficam em Principal > Ferramentas > Capturar; Cor, Reconhecer texto, Código QR e Transcodificar ficam direto em Principal > Ferramentas. Central de controle > Ferramentas oferece as mesmas ações.

## Capturas de tela e extração

- **Print:** captura completa no editor flutuante.
- **SUPER + Print:** seleção congelada no editor flutuante.
- **SUPER + Shift + Print:** captura da janela ativa no editor.
- **SUPER + Ctrl + Print:** extrair texto de uma seleção com OCR.
- **SUPER + Alt + Print:** decodificar um código QR de uma seleção.
- **SUPER + =:** selecionar e copiar uma cor.

Após a captura, um breve relâmpago atinge a região capturada. O efeito começa depois que a imagem é obtida, portanto nunca aparece nela.

Revise o conteúdo antes de salvar ou compartilhar. O OCR pode errar; códigos QR podem conter credenciais privadas ou URLs não confiáveis. Usar um editor não garante que textos sensíveis ao fundo tenham sido removidos.

As capturas salvas oferecem ações na notificação para abrir a imagem, editá-la no editor de capturas (salvando por cima), embelezá-la, fixá-la na tela ou abrir a pasta de capturas.

**Embelezar** coloca a captura sobre um fundo (o degradê do tema, alguns predefinidos, a cor de destaque ou nenhum) com margem, cantos arredondados e sombra ajustáveis; **Copiar imagem** coloca a imagem em tamanho real na área de transferência e **Salvar imagem** grava ao lado do original como `NAME-beautified.png`.

**Fixar na tela** deixa a captura flutuando acima de todas as janelas e em todos os espaços de trabalho, como referência. Arraste para mover e role sobre ela para redimensionar; feche com o botão ×, Esc ou um clique do meio.

## Gravação e transmissão

Gravação de tela abre os controles do OBS. Eles usam sua cena configurada e a permissão de captura do Wayland já salva; a cena deve incluir uma fonte de monitor visível. Iniciar a captura prepara o OBS e fecha o painel antes de gravar. Os controles usam o WebSocket do OBS, desativado por padrão: o Eitr o ativa com senha na primeira vez em que o OBS está fechado. Se estiver aberto nesse momento, feche-o uma vez e tente novamente.

As gravações vão para **Videos/Records** na sua pasta pessoal. O padrão do OBS é a própria pasta pessoal; o Eitr só altera esse padrão, preservando uma pasta que você tenha escolhido em OBS > Configurações > Saída.

Durante uma gravação ou transmissão, aparece um ponto vermelho à esquerda do relógio. Clique para ver tempo decorrido, tamanho do arquivo, pausar/retomar, parar, adicionar marcador de capítulo (exige o formato Hybrid MP4 do OBS), controlar microfone e câmera do OBS e escolher a cena. Uma transmissão mostra um cronômetro LIVE com seu próprio botão de parada.

Ao encerrar uma gravação, a notificação oferece Reproduzir gravação, Abrir pasta e Copiar caminho. Confira as opções de áudio/microfone e o monitor selecionado antes de começar. A webcam exige uma fonte de câmera no OBS. Os botões de áudio da gravação alteram entradas do OBS, não o volume do sistema.

O manual nunca inicia gravações ou transmissões. Compartilhar e capturar a tela continuam sendo ações explícitas. Transcodificar abre o fluxo existente de conversão de imagens e vídeos; revise os caminhos de saída antes de substituir arquivos.

Com o OBS fechado, Gravar captura a tela que está em foco: o Eitr responde ele mesmo ao pedido de tela do OBS, sem seletor, e ajusta a resolução base do OBS ao tamanho dessa tela (uma saída reduzida mantém a proporção). Uma janela do OBS que você mesmo abriu continua gravando o que já captura; quando a gravação termina, o Eitr fecha o OBS que ele abriu, então a próxima volta a seguir o seu foco. Outros apps que compartilham sua tela, como uma chamada de vídeo, continuam mostrando o seletor do Hyprland. Um `~/.config/hypr/xdph.conf` que você mesmo alterou é mantido; aí o seletor pode perguntar toda vez.

Em uma configuração nova do OBS, o Eitr cria a coleção Untitled com uma Scene: captura de tela, câmera oculta e áudio padrão do sistema e do microfone. A câmera fica desligada até você ativá-la. Coleções existentes nunca são alteradas.

## Compartilhar

Principal > Ferramentas > Compartilhar oferece LocalSend e as ferramentas de transferência existentes. Enviar um arquivo exige escolher o destino ou dispositivo. Verifique os destinatários e evite compartilhar chaves privadas, códigos de recuperação, tokens ou uma pasta pessoal/de configurações inteira sem revisão.
