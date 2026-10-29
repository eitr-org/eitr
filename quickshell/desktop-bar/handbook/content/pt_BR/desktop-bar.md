# Barra e espaços de trabalho

A barra mantém data e hora centralizadas. À esquerda fica primeiro o logotipo do Eitr, que abre a Central de controle, seguido de Visão geral, marcadores de espaços de trabalho, Uso de IA, Hardware e Bloqueio automático; à direita, os controles de dispositivos e status. Clique em **Mostrar ícones** para exibir ou ocultar esse grupo da direita.

Ilhas apresenta grupos em superfícies separadas: logotipo, Visão geral e espaços de trabalho, Uso de IA/Hardware/Bloqueio por inatividade, relógio, clima e controles de estado. Mídia e captura aparecem apenas quando ativos. O relógio permanece exatamente centrado na tela; o clima tem a sua própria superfície ao lado. As superfícies seguem a preferência de cantos, cor/transparência e desfoque. As superfícies ficam a metade do espaçamento exterior atual do Hyprland da borda, com o espaçamento completo entre superfícies vizinhas, nas quatro posições. O espaço reservado para janelas inclui a espessura e essa metade; a ocultação automática não reserva espaço. Os intervalos deixam passar cliques. O espaço vazio nas superfícies aceita os gestos habituais de clique duplo e arrasto. Os painéis usam superfícies destacadas como Abas, nas posições de Completa, com revelação de 320 ms. Os ícones de estado mantêm o botão manual de mostrar/ocultar.

## Atualizações

O ícone de atualizações fica no grupo da direita, antes de Notificações, e verifica atualizações de pacotes e do AUR logo após o login e a cada seis horas. Ao encontrar atualizações, uma notificação oferece executar a Atualização do sistema. Ele gira durante a consulta e depois mostra uma marca de verificação quando tudo está atualizado, ou um ícone de atualização cuja dica informa a quantidade e o tamanho do download. Clique para atualizar o sistema; clique com o botão direito para consultar novamente. A consulta se repete automaticamente ao terminar a atualização. Sem rede, ele indica sistema atualizado e consulta no próximo login. Usa uma cópia privada dos bancos de pacotes para nunca deixar o sistema parcialmente atualizado.

## Posição e aparência

- Dê dois cliques com o botão esquerdo no **espaço vazio da barra** para alternar Desfoque/Cor do tema; novas instalações começam com Cor do tema.
- Dê dois cliques com o botão direito no espaço vazio para alternar Completa → Centralizada → Abas → Ilhas → Completa.
- Arraste um espaço vazio para cima, baixo, esquerda ou direita para mover a barra.
- As mesmas opções ficam em **Estilo > Barra da área de trabalho** e Central de controle > Estilo.
- **Telas** (Mostrar em) coloca a barra apenas no monitor principal, por padrão, ou em todos os monitores. Em todos, cada barra marca o espaço de trabalho de sua própria tela; atalhos como SUPER + , abrem na tela em uso e as notificações aparecem apenas na principal. Escolha a principal no painel de Tela.

O modo centralizado mostra o relógio até você passar o ponteiro. Os ícones se expandem na ordem habitual. O alfinete entre a mídia e o relógio mantém a barra aberta; painéis abertos também a mantêm expandida. No modo completo, os painéis se unem à barra; no centralizado, ficam ao lado. Ambos abrem e fecham com a mesma animação fluida. Cada lado se ajusta ao conteúdo, e o relógio permanece no centro da tela nas quatro bordas.

Abas mostra uma faixa contínua de 7 px e três abas ajustadas ao conteúdo dos grupos esquerdo, central e direito. As abas mantêm a profundidade completa (30 px na horizontal), junções trapezoidais fixas com inclinações retas de 45° fora do espaçamento interno das abas. O relógio fica exatamente no centro da tela mesmo com mídia. Os painéis flutuam ao lado da barra em superfícies arredondadas separadas, alinhadas à esquerda, ao centro ou à direita como no modo Completa e afastadas das bordas da tela pela margem externa, com o espaçamento atual entre janelas do Hyprland e a mesma animação de 320 ms do modo Centralizado. Os espaços deixam os cliques passar; toda a profundidade das abas fica reservada para as janelas. Clique duplo direito alterna Completa → Centralizada → Abas → Ilhas → Completa. As duas dobras são levemente suavizadas e independentes da preferência de cantos; as extremidades da tela ficam quadradas e preenchidas. Abas sempre mostra todos os controles à direita sem seta para ocultar. O clima fica oculto até passar o ponteiro sobre a aba central e desliza após o relógio fixo em 320 ms. Recolhe após um breve atraso ao sair e permanece visível enquanto seu painel está aberto. Apenas o lado posterior cresce ao longo do eixo da barra, com 4 px após o último item visível.

## Espaços de trabalho

A barra começa em 1–5 e cresce até o espaço atual ou o maior ocupado, com limite de 10. Marcadores superiores vazios desaparecem quando não são mais necessários. Clique com o botão direito em um marcador para escolher Pontos, Glifo, Números ou Runas, com exemplos ao vivo. Runas é o padrão e representa os espaços de 1 a 10 pelas primeiras dez runas do Futhark Antigo (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ). O marcador ativo usa o símbolo na cor de destaque, sem fundo preenchido.

**SUPER + 1–9/0** muda de espaço; **SUPER + Shift + 1–9/0** move uma janela. **SUPER + Tab** abre a Visão geral. Clique em uma prévia ou use setas e Enter; 1–9/0 muda diretamente. Só aparecem espaços numerados ocupados, com prévias mantidas em memória. Escape ou um clique fora fecha a Visão geral.

**SUPER + S** alterna o espaço especial, separado da Visão geral. **SUPER + Shift + Space** oculta/exibe a barra, sem interromper o serviço de notificações.

Os gestos de mouse para papéis de parede e temas no espaço vazio da área de trabalho estão em **Aprender > Gestos do mouse**. Em caso de dúvida, use os atalhos de teclado dos carrosséis.

O controle Áudio/Mic abre um painel com seções separadas para saída de áudio e microfone. Tailscale e Streaming ficam imediatamente antes do OBS. Um interruptor no cabeçalho conecta o Tailscale ou inicia o compartilhamento, depois vêm detalhes e dispositivos, e as ações de configuração ou diagnóstico ficam no menu “…”. O fundo dos botões de ícone aparece quando você passa o ponteiro sobre eles; os painéis se atualizam sozinhos ao abrir, um ícone de atualização gira só enquanto carregam, e as dicas aparecem perto do ponteiro. Os interruptores e botões de ação internos usam tamanhos compactos compartilhados.

**Visualizador de música** em **Principal > Ferramentas** abre o cava com as cores do tema. Clique com o botão direito no equalizador de mídia para abrir o mesmo visualizador; o botão esquerdo continua abrindo os detalhes da mídia. Pressione **q** ou **Esc** para fechar. Se o cava não estiver instalado, ele será instalado primeiro.

**Ocultar automaticamente**, em Estilo > Barra da área de trabalho e Central de controle > Estilo, recolhe a barra após um breve atraso quando o ponteiro sai. Encoste o ponteiro na borda da tela para mostrá-la. Funciona nas quatro bordas com os modos Completa, Centralizada, Abas e Ilhas. Painéis e menus abertos, assim como arrastar a barra, mantêm a barra visível; depois ela volta a se ocultar. Enquanto estiver ativado, a barra não reserva espaço das janelas: ela desliza sobre elas em vez de movê-las. A preferência é salva separadamente do alfinete do modo centralizado e vem desativada em novas instalações.

**Reduzir movimento**, em Estilo > Barra da área de trabalho e Central de controle > Estilo > Barra, torna instantâneas a abertura e o fechamento dos painéis, as entradas da Visão geral, as transições de notificações e as animações decorativas da barra. Vem desativado e é salvo em `bar-settings.json`. Os temporizadores de atualização de dados, expiração de notificações e ocultação automática mantêm seu funcionamento normal.

O estilo de mídia é salvo em `bar-settings.json`: escolha Barras (padrão, oito barras) ou Linha (uma onda de áudio simples e suave) em Estilo > Barra da área de trabalho ou Central de controle > Estilo > Barra. O indicador vem antes dos controles, mantém tamanho fixo em todos os layouts e gira nas bordas esquerda e direita. Passe o ponteiro para ver a música; o clique esquerdo abre os detalhes e o direito abre o visualizador de música. Em pausa, a linha fica plana. Reduzir movimento mantém os níveis de áudio sem transições e interrompe o movimento decorativo de reserva.

O modo Centralizado encontra a borda da tela com extremidades retas e as mesmas rampas de 45° suavemente arredondadas de Abas nos dois lados. As rampas giram com a barra nas quatro bordas e ignoram a preferência de cantos; os painéis separados continuam seguindo essa preferência.

## Dock de aplicativos

Toque na borda oposta à barra para revelar o dock. Ele se desdobra a partir dessa borda, com laterais retas que encontram a borda, sobre as janelas sem redimensioná-las e se esconde 350 ms após o ponteiro sair, com animação de 320 ms (instantânea com Reduzir movimento). Aparece na tela principal ou em todas quando a barra usa todas as telas. Nunca aparece sobre uma janela em tela cheia.

Os aplicativos abertos são agrupados pela classe, na ordem das janelas do Hyprland. Os ícones usam espaços de 36 px separados por 6 px, com o ícone do aplicativo ou um símbolo alternativo. Os pontos abaixo contam as janelas, até três, e ficam esmaecidos quando nenhuma está no espaço de trabalho atual daquela tela. Passe o ponteiro para ver o nome e o número de janelas. Clique para focar a janela usada mais recentemente, mudando de espaço se necessário; clique de novo para ir à próxima janela dele. O botão do meio fecha a janela mais recente. Listas longas rolam ao longo do dock. A superfície segue Desfoque/Cor do tema e os cantos escolhidos.

**Dock** em **Estilo > Barra da área de trabalho** e **Central de controle > Estilo > Barra** ativa ou desativa o dock. A opção `dock` em `bar-settings.json` começa em `"yes"`. Ainda não há atalho nem controle para fixar aplicativos.
