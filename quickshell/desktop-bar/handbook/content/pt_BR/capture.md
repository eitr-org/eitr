# Captura e compartilhamento

As ferramentas de captura ficam em Principal > Ferramentas > Captura e Central de controle > Ferramentas.

## Capturas de tela e extração

- **Print:** captura completa no editor flutuante.
- **SUPER + Print:** seleção congelada no editor flutuante.
- **SUPER + Shift + Print:** captura da janela ativa no editor.
- **SUPER + Ctrl + Print:** extrair texto de uma seleção com OCR.
- **SUPER + Alt + Print:** decodificar um código QR de uma seleção.
- **SUPER + =:** selecionar e copiar uma cor.

Após a captura, um breve relâmpago atinge a região capturada. O efeito começa depois que a imagem é obtida, portanto nunca aparece nela.

Revise o conteúdo antes de salvar ou compartilhar. O OCR pode errar; códigos QR podem conter credenciais privadas ou URLs não confiáveis. Usar um editor não garante que textos sensíveis ao fundo tenham sido removidos.

## Gravação e transmissão

Gravação de tela abre os controles do OBS. Eles usam sua cena configurada e a permissão de captura do Wayland já salva; a cena deve incluir uma fonte de monitor visível. Iniciar a captura prepara o OBS e fecha o painel antes de gravar. Os controles usam o WebSocket do OBS, desativado por padrão: o Eitr o ativa com senha na primeira vez em que o OBS está fechado. Se estiver aberto nesse momento, feche-o uma vez e tente novamente.

As gravações vão para **Videos/Records** na sua pasta pessoal. O padrão do OBS é a própria pasta pessoal; o Eitr só altera esse padrão, preservando uma pasta que você tenha escolhido em OBS > Configurações > Saída.

Durante uma gravação ou transmissão, aparece um ponto vermelho ao lado do clima. Clique para ver tempo decorrido, tamanho do arquivo, pausar/retomar, parar, adicionar marcador de capítulo (exige o formato Hybrid MP4 do OBS), controlar microfone e câmera do OBS e escolher a cena. Uma transmissão mostra um cronômetro LIVE com seu próprio botão de parada. Ao encerrar uma gravação, a notificação oferece Abrir pasta e Copiar caminho. Confira as opções de áudio/microfone e o monitor selecionado antes de começar. A webcam exige uma fonte de câmera no OBS. Os botões de áudio da gravação alteram entradas do OBS, não o volume do sistema.

O manual nunca inicia gravações ou transmissões. Compartilhar e capturar a tela continuam sendo ações explícitas. Transcodificar abre o fluxo existente de conversão de imagens e vídeos; revise os caminhos de saída antes de substituir arquivos.

Em uma configuração nova do OBS, o Eitr cria a coleção Untitled com uma Scene: captura de tela, câmera oculta e áudio padrão do sistema e do microfone. No primeiro uso, o sistema pergunta qual tela você quer compartilhar; o OBS salva essa permissão. A câmera fica desligada até você ativá-la. Coleções existentes nunca são alteradas.

## Compartilhar

Principal > Ferramentas > Compartilhar oferece LocalSend e as ferramentas de transferência existentes. Enviar um arquivo exige escolher o destino ou dispositivo. Verifique os destinatários e evite compartilhar chaves privadas, códigos de recuperação, tokens ou uma pasta pessoal/de configurações inteira sem revisão.
