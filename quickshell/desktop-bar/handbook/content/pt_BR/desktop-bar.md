# Barra e espaços de trabalho

<!-- eitr-figure: bar-anatomy -->

A barra completa. O logotipo do Eitr abre a Central de controle; depois vêm Visão geral, os marcadores de espaços de trabalho, Uso de IA, Hardware e Bloqueio automático. A data e a hora ficam centralizadas, com a mídia antes e o clima depois. **Mostrar ícones** exibe ou oculta os ícones de status à direita; as notificações ficam por último.

Ilhas apresenta grupos em superfícies separadas: logotipo, Visão geral e espaços de trabalho, Uso de IA/Hardware/Bloqueio por inatividade, relógio, clima e controles de estado. Mídia e captura aparecem apenas quando ativos. O relógio permanece exatamente centrado na tela; o clima tem a sua própria superfície ao lado. As superfícies são sempre totalmente arredondadas, seja qual for a preferência de cantos, e seguem cor/transparência e desfoque.

As superfícies ficam a metade do espaçamento exterior atual do Hyprland da borda, com o espaçamento completo entre superfícies vizinhas, nas quatro posições. O espaço reservado para janelas inclui a espessura e essa metade; a ocultação automática não reserva espaço. Os intervalos deixam passar cliques. O espaço vazio nas superfícies aceita os gestos habituais de clique duplo e arrasto.

Abrir um painel faz crescer um cartão a partir da sua ilha (para o lado livre: o clima para a direita, mídia e captura para a esquerda, o estado para o centro, o relógio para os dois lados) e afasta as ilhas vizinhas; a ilha fica escondida sob o cartão até ele encolher de volta.

Os ícones de estado mantêm o botão manual de mostrar/ocultar.

Em Configurações > Janelas, o layout e os monitores usam escolhas com dois botões. O número de áreas de trabalho e Sempre mostrar usam listas suspensas; Sempre mostrar oferece de 2 até a quantidade atual. As descrições explicam cada ajuste, incluindo o layout selecionado e as opções de rolagem.

## Atualizações

O ícone de atualizações, antes de Notificações, verifica pouco depois do login e a cada seis horas. Clique para atualizar o sistema; o botão direito verifica novamente. Uma Atualização do sistema bem-sucedida o marca como atualizado até a próxima verificação, sem iniciar outra imediatamente. Sem conexão ou em caso de falha, o estado fica indisponível, nunca falsamente “atualizado”. A verificação usa uma base privada e não atualiza pacotes.

## Alterar o layout da barra

- Dê dois cliques com o botão esquerdo no **espaço vazio da barra** para alternar entre Cor do tema → Desfoque → Site; novas instalações começam com Cor do tema. Site usa as cores do site do Eitr, claras ou escuras conforme o tema.
- Dê dois cliques com o botão direito no espaço vazio para alternar Completa → Centralizada → Abas → Ilhas → Dinâmico → Gota → Completa.
- Arraste um espaço vazio para cima, baixo, esquerda ou direita para mover a barra. À esquerda e à direita, a barra é tão fina quanto em cima e embaixo: o relógio mostra a hora acima dos minutos com um ícone de calendário, e o clima só o ícone; passe o ponteiro para ver a data e a temperatura.
- **Relógio** em Configurações > Barra da área de trabalho mostra a hora no formato de 12 horas com AM/PM (padrão) ou de 24 horas, em qualquer borda.
- As mesmas opções ficam em **Configurações > Barra da área de trabalho**, nas abas Layout, Aparência e Comportamento.
- **Telas** (Mostrar em) coloca a barra apenas no monitor principal, por padrão, ou em todos os monitores. Em todos, cada barra marca o espaço de trabalho de sua própria tela; atalhos como SUPER + I abrem na tela em uso e as notificações aparecem apenas na principal. Escolha a principal no painel de Tela.

<!-- eitr-figure: bar-layouts -->

Os seis layouts na ordem em que o clique duplo direito os alterna. Em repouso, Centralizada mostra só o relógio, Dinâmico três pequenas ilhas e Gota uma única cápsula com a hora; Centralizada e Dinâmico se expandem ao passar o ponteiro.

Escolha um layout em Configurações > Barra da área de trabalho. Os seis funcionam em qualquer borda.

| Layout | Comportamento |
| :--- | :--- |
| Completa | Completa mantém toda a barra na borda. Os painéis se unem a ela. |
| Centralizada | Centralizada mostra só o relógio até passar o ponteiro. O alfinete, ou Manter expandido em Configurações > Barra da área de trabalho (também no Walker), a mantém aberta; os painéis flutuam ao lado. |
| Abas | Abas une três abas por uma faixa fina. Os ícones de estado e o clima ficam visíveis. |
| Ilhas | Ilhas dá a cada grupo sua própria cápsula e mostra sempre todos os ícones de status. Abrir um painel amplia sua ilha e afasta os grupos vizinhos. |
| Dinâmico | Dinâmico começa com três ilhas: logo, relógio e rede/bateria, mais uma ilha de mídia entre o logo e o relógio enquanto algo toca. Passe o ponteiro para ampliar uma; um painel cresce a partir dessa mesma ilha. |
| Gota | Gota mostra só a hora em uma cápsula no centro da borda. Clique para ela crescer até o painel; o clique direito abre direto os controles rápidos. Com a ocultação automática nada fica na tela até uma gota cair da borda e virar a cápsula. |

## O painel da Gota

Clique na cápsula da hora da Gota e a própria cápsula cresce até um painel. Arraste uma página para o lado (para a direita avança, para a esquerda volta, e as duas dão a volta) ou use as setas ou a rolagem horizontal. Esc ou um clique fora fecha. Nada nele abre outro painel: os detalhes abrem no mesmo lugar com uma seta para voltar.

| Página | O que tem |
| :--- | :--- |
| Calendário e clima | O clima ao lado do mês. Clique no clima para a previsão completa e a busca de cidades; clique em um dia para ver os planos e adicionar um lembrete em um horário desse dia. |
| Mídia | A capa cercada por barras que seguem a música, a música, a letra, os controles e uma barra de progresso. Só enquanto algo toca. |
| OBS | Status da gravação e da transmissão com pausar, parar e entrar ao vivo, uma marca de capítulo, a pasta de gravações e o OBS. Enquanto o OBS está aberto. |
| Controles rápidos | WiFi, Bluetooth, Som e Microfone abrem as redes e os dispositivos no mesmo lugar; Modo avião, Silêncio, Luz noturna, Bloqueio por inatividade, Gravar e Configurações; volume, microfone e (em notebooks) brilho. |
| Temporizador e foco | Uma contagem regressiva, um cronômetro ou sessões de foco de 25 minutos com pausas de 5. Continua com o painel fechado e avisa você no fim. |
| Desempenho, Uso de IA e Notificações | CPU, GPU, RAM e armazenamento; os limites de cada assistente (clique em um para ver todos); a lista de notificações. |

Em todos os modos, o relógio mostra ao lado o que está acontecendo, no lugar do ponto de gravação: uma marca de calendário quando um evento começa em menos de dez minutos (clique para os planos desse dia) e um anel enquanto um temporizador ou uma sessão de foco corre (clique para Central de controle > Ferramentas > Timer e Foco). Uma notificação nova toca duas vezes o sino da barra; onde o sino está oculto (Centralizada recolhida, Dinâmico em repouso), um sino desliza ao lado do relógio no lugar dele. A bateria de um notebook substitui a hora por um instante pela porcentagem em vermelho em 15% e 5%; onde os espaços de trabalho estão ocultos, o mesmo vale para o número do espaço de trabalho para o qual você troca.

Em volta da hora, a cápsula da Gota mostra o que está acontecendo e só abre espaço onde precisa. Antes da hora: um ponto vermelho durante uma gravação, uma marca de calendário quando um evento começa em menos de dez minutos, um anel enquanto um temporizador corre e uma nota enquanto toca música (clique para Mídia). Depois dela: um sino que toca duas vezes com uma notificação nova (clique para a lista). Trocar de espaço de trabalho substitui a hora por um instante pelo número; a bateria de um notebook faz o mesmo em vermelho em 15% e 5%. Arraste a nota para a direita para transformar a cápsula em uma linha da letra; arraste para qualquer lado, pause ou pare para voltar.

**Letras online** (Configurações > Barra da área de trabalho > Comportamento, ou Walker > Configurações > Área de trabalho > Barra da área de trabalho > Letras online) vem desligado. Ligado, a Gota busca a música no LRCLIB (lrclib.net), enviando título, artista, álbum e duração. Letras enviadas pelo próprio player sempre têm prioridade.

## Espaços de trabalho

Em Configurações > Janelas > Áreas de trabalho (também Walker > Configurações > Área de trabalho > Janelas > Áreas de trabalho), escolha **Monitores**, **Número de áreas de trabalho** (5–10, padrão 10) e **Sempre mostrar** (2 até o total, padrão 5). **Números compartilhados** dá a cada monitor suas próprias áreas 1…N: SUPER+k troca todos os monitores juntos; SUPER+Shift+k move a janela no monitor atual, e todos os monitores mudam junto para esse número. **Dividir entre monitores** distribui N igualmente, começando pelo monitor principal e dando a ele primeiro o restante; os outros seguem da esquerda para a direita e por nome. SUPER+k foca o monitor responsável. Teclas acima de N não fazem nada. O mínimo visível é relativo à faixa de cada monitor; marcadores maiores aparecem até a área atual ou a maior ocupada e depois desaparecem. Conectar, remover ou trocar o monitor principal recalcula a distribuição sem perder janelas: elas vão para o número válido mais próximo no monitor atual. Com um monitor, os dois modos têm o mesmo comportamento.

Clique com o botão direito em um marcador para escolher Pontos, Glifo, Números ou Runas, com exemplos ao vivo. Runas é o padrão e representa os espaços de 1 a 10 pelas primeiras dez runas do Futhark Antigo (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ).

O marcador ativo usa o símbolo na cor de destaque, sem fundo preenchido. As quatro opções cabem no menu em qualquer borda da barra, sem rolagem.

**SUPER + 1–9/0** muda de espaço; **SUPER + Shift + 1–9/0** move uma janela. **SUPER + Tab** abre a Visão geral. Clique em uma prévia ou use setas e Enter; 1–9/0 muda diretamente. Só aparecem espaços numerados ocupados, com prévias mantidas em memória. Escape ou um clique fora fecha a Visão geral.

**SUPER + S** alterna o espaço especial, separado da Visão geral. **SUPER + Shift + Space** liga ou desliga a ocultação automática da barra; se a barra foi ocultada pelo Centro de Controle, ela volta primeiro. As notificações continuam funcionando.

Os gestos de mouse para papéis de parede e temas no espaço vazio da área de trabalho estão em **Aprender > Gestos do mouse**. Em caso de dúvida, use os atalhos de teclado dos carrosséis.

O controle Áudio/Mic abre um painel com seções separadas para saída de áudio e microfone. Streaming fica imediatamente antes do OBS. Um interruptor no cabeçalho inicia o compartilhamento, depois vêm os detalhes, e as ações de configuração ou diagnóstico ficam no menu “…”.

O fundo dos botões de ícone aparece quando você passa o ponteiro sobre eles; os painéis se atualizam sozinhos ao abrir, um ícone de atualização gira só enquanto carregam, e as dicas aparecem perto do ponteiro. Os interruptores e botões de ação internos usam tamanhos compactos compartilhados.

**Visualizador de música** abre o cava com as cores do tema. Clique com o botão direito no equalizador de mídia para abrir o mesmo visualizador; o botão esquerdo continua abrindo os detalhes da mídia. Pressione **q** ou **Esc** para fechar. Se o cava não estiver instalado, ele será instalado primeiro.

**Ocultar automaticamente**, em Configurações > Barra da área de trabalho, recolhe a barra após um breve atraso quando o ponteiro sai. Encoste o ponteiro na borda da tela para mostrá-la. Funciona nas quatro bordas com os modos Completa, Centralizada, Abas, Ilhas, Dinâmico e Gota; com Gota, uma gota da cor da barra cai da borda e vira a cápsula da hora. Uma notificação nova traz a barra até o aviso fechar. Painéis e menus abertos, assim como arrastar a barra, mantêm a barra visível; depois ela volta a se ocultar.

Enquanto estiver ativado, a barra não reserva espaço das janelas: ela desliza sobre elas em vez de movê-las. A preferência é salva separadamente do alfinete do modo centralizado e vem desativada em novas instalações.

**Reduzir movimento**, em Configurações > Barra da área de trabalho, torna instantâneas a abertura e o fechamento dos painéis, as entradas da Visão geral, as transições de notificações e as animações decorativas da barra. Vem desativado e é salvo em `bar-settings.json`. Os temporizadores de atualização de dados, expiração de notificações e ocultação automática mantêm seu funcionamento normal.

O estilo de mídia é salvo em `bar-settings.json`: escolha Barras (padrão, dez barras) ou Linha (uma onda de áudio simples e suave) em Configurações > Barra da área de trabalho. O indicador vem antes dos controles, mantém tamanho fixo em todos os layouts e gira nas bordas esquerda e direita. Passe o ponteiro para ver a música; o clique esquerdo abre os detalhes e o direito abre o visualizador de música. Arraste-o para a esquerda para ver uma linha da letra no lugar; arraste a linha para qualquer lado para trazê-lo de volta. Em pausa, a linha fica plana. Reduzir movimento mantém os níveis de áudio sem transições e interrompe o movimento decorativo de reserva.

O modo Centralizado encontra a borda da tela com extremidades retas e as mesmas rampas de 45° suavemente arredondadas de Abas nos dois lados. As rampas giram com a barra nas quatro bordas e ignoram a preferência de cantos; os painéis separados continuam seguindo essa preferência.

## Dock de aplicativos

Toque na borda oposta à barra para revelar o dock. Ele se desdobra a partir dessa borda, com laterais retas que encontram a borda, sobre as janelas sem redimensioná-las e se esconde 350 ms após o ponteiro sair, com animação de 320 ms (instantânea com Reduzir movimento). Aparece na tela principal ou em todas quando a barra usa todas as telas. Nunca aparece sobre uma janela em tela cheia.

Os aplicativos abertos são agrupados pela classe, na ordem das janelas do Hyprland. Os ícones usam espaços de 36 px separados por 6 px, com o ícone do aplicativo ou um símbolo alternativo; os terminais de tarefas e menus do próprio Eitr compartilham um único ícone com o logo do Eitr.

Os pontos abaixo contam as janelas, até três, e ficam esmaecidos quando nenhuma está no espaço de trabalho atual daquela tela. Passe o ponteiro para ver o nome e o número de janelas; os ícones perto do ponteiro crescem, o mais próximo mais que os outros, e o dock se alonga para mantê-los dentro, exceto com **Reduzir movimento** ativado.

Clique para focar a janela usada mais recentemente, mudando de espaço se necessário; clique de novo para ir à próxima janela dele. O botão do meio fecha a janela mais recente. Listas longas rolam ao longo do dock. A superfície segue Desfoque/Cor do tema e os cantos escolhidos.

**Dock** em **Configurações > Barra da área de trabalho** ativa ou desativa o dock. A opção `dock` em `bar-settings.json` começa em `"yes"`. Não há atalho para o dock.

Aplicativos fixados permanecem totalmente opacos e sem pontos quando fechados; clique para abri-los em seu próprio escopo de aplicativo. Clique com o botão direito para Manter no Dock / Remover do Dock, Nova janela (quando houver uma entrada de desktop) e Fechar ou Fechar todas as janelas. Escape ou um clique fora fecha o menu. Aplicativos sem entrada de desktop não podem ser fixados.

Arraste os ícones ao longo do dock para organizar os fixados. Arraste um aplicativo aberto para a seção de fixados para mantê-lo ali ou arraste um fixado para fora dessa seção para removê-lo. Os outros ícones abrem espaço com uma animação curta (instantânea com Reduzir movimento); os não fixados mantêm a ordem das janelas do Hyprland. Um divisor fino separa as seções apenas quando ambas contêm aplicativos. Menus e arrastos mantêm o dock visível.

Os IDs das entradas de desktop são salvos em ordem no arquivo local `quickshell/desktop-bar/dock-pins.json`, sob `$XDG_CONFIG_HOME` (normalmente `~/.config`), com gravação atômica. Instalações novas não têm aplicativos fixados. As janelas são associadas pelos IDs das entradas de desktop, por StartupWMClass e pelas classes dos aplicativos.

A intensidade do desfoque é compartilhada com os terminais. Escolha Leve, Média (padrão) ou Forte em Barra da área de trabalho no Walker ou nas Configurações (SUPER + ,). Veja [Terminal e editores](handbook:terminal) para a limitação global e as configurações pessoais.

Configurações > Barra da área de trabalho inclui os marcadores de espaços (pontos, glifo, números e runas). Janelas mantém os efeitos e os espaçamentos.
