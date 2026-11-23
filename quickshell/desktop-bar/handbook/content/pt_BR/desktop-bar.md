# Barra e espaços de trabalho

<!-- eitr-figure: bar-anatomy -->

A barra completa. O logotipo do Eitr abre a Central de controle; depois vêm Visão geral, os marcadores de espaços de trabalho, Uso de IA, Hardware e Bloqueio automático, por padrão. A data e a hora ficam centralizadas, com a mídia antes e o clima depois. **Mostrar ícones** exibe ou oculta os ícones de status à direita; as notificações ficam por último, por padrão.

Os itens de plugins podem aparecer após Bloqueio automático, antes do relógio, após o relógio ou no grupo de status. Escolha a posição em Configurações > Plugins > o plugin > Na barra, ou organize todos os ícones integrados e de plugins juntos em **Configurações > Barra da área de trabalho > Ícones**. Lá, uma prévia ao vivo reflete as mudanças na hora: arraste qualquer ícone (ou foque um item, pressione Espaço ou Enter para pegá-lo, mova com as setas dentro de ou entre **Lado esquerdo**, **Antes do relógio**, **Depois do relógio** e **Lado direito**, depois pressione Enter ou Espaço para soltar ou Esc para cancelar) e clique em **Restaurar padrão** para limpar o `iconOrder` salvo em `bar-settings.json`. Itens fixos da barra (logotipo do Eitr, Visão geral, espaços de trabalho, faixa de mídia, alfinete centralizado, indicador de captura e relógio) permanecem fixos, os painéis abrem do lado correspondente à área atual do ícone em todos os layouts e bordas, e novos ícones aparecem em sua área padrão sem perder a personalização existente. Sem ordenação personalizada, os limites são quatro após Bloqueio automático, dois de cada lado do relógio e oito no status, na ordem de posicionamento; os itens extras ficam ocultos na posição escolhida. Centered e Dynamic os revelam quando expandidos; Tabs e Islands os incluem; Drop mostra os itens de plugins posicionados no trilho do painel. O relógio permanece centralizado na tela. World clock é um plugin oficial opcional que segue a preferência de 12/24 horas da barra.

Weather é um plugin oficial integrado, instalado por padrão após o relógio. Remova-o em Eitr Store > Instalados > Plugins para ocultar o clima em todos os lugares, inclusive na página inicial de Drop. Ele continua removido após atualizações; instale-o novamente em Descobrir usando a cópia do pacote, sem download. A busca de cidades é temporária e dura apenas a sessão.

Uso de IA e Hardware também são plugins integrados instalados por padrão. Ao remover Uso de IA, somem o ícone, a página no Drop e a aba Uso nas configurações do Assistente de IA, mantendo os outros recursos do assistente disponíveis. Hardware inclui tanto o ícone na barra (e a página Desempenho no Drop) quanto o widget de área de trabalho (compacto ou detalhado); removê-lo retira ambos, enquanto desativar **Mostrar na barra** nos detalhes do plugin oculta apenas o ícone da barra e mantém ativos os widgets posicionados na área de trabalho. É possível reinstalar qualquer um pela loja sem conexão.

As setas ↗, → e ↘ comparam o ritmo de consumo com um uso uniforme. Se o consumo estiver mais rápido, o painel estima quando o limite será atingido. O ritmo aparece quando a duração e o horário de renovação são conhecidos e pelo menos 5% do período já passou.

Ilhas apresenta grupos em superfícies separadas: logotipo, Visão geral e espaços de trabalho, Uso de IA/Hardware/Bloqueio por inatividade, relógio, clima e controles de estado. Mídia e captura aparecem apenas quando ativos. O relógio permanece exatamente centrado na tela; o clima tem a sua própria superfície ao lado. As superfícies são sempre totalmente arredondadas, seja qual for a preferência de cantos, e seguem cor/transparência e desfoque.

As superfícies ficam a metade do espaçamento exterior atual do Hyprland da borda, com o espaçamento completo entre superfícies vizinhas, nas quatro posições. O espaço reservado para janelas inclui a espessura e essa metade; a ocultação automática não reserva espaço. Os intervalos deixam passar cliques. O espaço vazio nas superfícies aceita os gestos habituais de clique duplo e arrasto.

Abrir um painel faz crescer um cartão a partir da sua ilha (para o lado livre: o clima para a direita, mídia e captura para a esquerda, o estado para o centro, o relógio para os dois lados) e afasta as ilhas vizinhas; a ilha fica escondida sob o cartão até ele encolher de volta.

Os ícones de estado mantêm o botão manual de mostrar/ocultar.

Em Configurações > Janelas, o layout e os monitores usam escolhas com dois botões. O número de áreas de trabalho e Sempre mostrar usam listas suspensas; Sempre mostrar oferece de 2 até a quantidade atual. As descrições explicam cada ajuste, incluindo o layout selecionado e as opções de rolagem.

## Atualizações

O ícone de atualizações, antes de Notificações, verifica pouco depois do login e a cada seis horas. Clique para atualizar o sistema; o botão direito verifica novamente. Uma Atualização do sistema bem-sucedida o marca como atualizado até a próxima verificação, sem iniciar outra imediatamente. Sem conexão ou em caso de falha, o estado fica indisponível, nunca falsamente “atualizado”. A verificação usa uma base privada e não atualiza pacotes.

## Alterar o layout da barra

- Dê dois cliques com o botão esquerdo no **espaço vazio da barra** para alternar entre Cor do tema → Desfoque → Transparente → Site; novas instalações começam com Cor do tema. Transparente deixa só o papel de parede atrás da barra. Desfoque e Transparente olham o papel de parede atrás da barra e, onde o texto do tema ficaria difícil de ler (um papel de parede claro com um tema escuro), trocam o texto e os ícones da barra para a cor oposta do tema. Os painéis mantêm as cores do tema. Site usa as cores do site do Eitr, claras ou escuras conforme o tema.
- Dê dois cliques com o botão direito no espaço vazio para alternar Completa → Centralizada → Abas → Ilhas → Dinâmico → Gota → Completa.
- Arraste um espaço vazio para cima, baixo, esquerda ou direita para mover a barra. À esquerda e à direita, a barra é tão fina quanto em cima e embaixo: o relógio mostra a hora acima dos minutos com um ícone de calendário, e o clima só o ícone; passe o ponteiro para ver a data e a temperatura.
- **Relógio** em Configurações > Barra da área de trabalho mostra a hora no formato de 12 horas com AM/PM (padrão) ou de 24 horas, em qualquer borda.
- As mesmas opções ficam em **Configurações > Barra da área de trabalho**, nas abas Layout, Aparência, Ícones e Comportamento.
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

Passe o ponteiro sobre o relógio do modo Dinâmico para abrir um cartão com a hora, a data completa, a semana conforme a região, pontos nos dias com compromissos e o clima quando disponível. Clique no cartão para abrir o Calendário ou no clima para ver a previsão. O cartão fica aberto enquanto o ponteiro estiver sobre ele.

Com a barra no topo ou embaixo no modo Dinâmico ou Gota, os carrosséis de temas e papéis de parede se expandem a partir do relógio e voltam para ele ao fechar. Com a ocultação automática no modo Gota, a cápsula aparece primeiro e se recolhe após o fechamento. Barras laterais e telas sem barra usam a sobreposição da área de trabalho.

**Momentos da barra**, ativado por padrão em Configurações > Barra da área de trabalho > Comportamento e Walker > Configurações > Área de trabalho > Barra da área de trabalho, mostra brevemente notificações e capturas, volume e brilho, mudanças de música, mudanças de saída de áudio, conexões e desconexões Bluetooth e trocas de layout do teclado em todos os layouts. Os momentos substituem o texto do relógio no centro da tela; Completa e Abas mantêm os vizinhos fixos e cortam textos longos. Centralizada recolhida aumenta só a pílula do relógio, Ilhas aumenta a ilha do relógio e Gota aumenta sua pílula centralizada. O título da música substitui a faixa de mídia visível ou, se ela estiver oculta, o relógio; Dinâmica mantém sua ilha de mídia e seu comportamento. Avisos críticos ficam até o popup ser dispensado; clicar em um momento de notificação abre as notificações. O ponteiro mantém o momento atual até sair. Novos momentos aguardam enquanto há um painel aberto ou o ponteiro está sobre a área e expiram após seis segundos na fila. Focus não mostra momentos. Barras laterais mostram só ícones e níveis. Desativar Momentos da barra restaura os popups separados de volume e brilho, também usados com Focus.

**Estilo das ilhas** (Configurações > Barra da área de trabalho > Layout, ou Walker > Configurações > Área de trabalho > Barra da área de trabalho > Estilo das ilhas) escolhe como Ilhas, Dinâmico e Gota encontram a borda da tela: Flutuante mantém as pílulas a meio espaçamento externo da borda; Presa as encosta nela, retas do lado da borda e com laterais retas, e os painéis também crescem a partir da borda. **Estilo das laterais** escolhe como Abas e Centralizada encontram a borda: rampas de 45° ou laterais retas (com laterais retas, Abas também perdem a faixa fina entre as abas).

## O painel da Gota

Clique na cápsula da hora da Gota e a própria cápsula cresce até um painel. Arraste uma página para o lado (para a direita avança, para a esquerda volta, e as duas dão a volta) ou use as setas ou a rolagem horizontal. Esc ou um clique fora fecha. Nada nele abre outro painel: os detalhes abrem no mesmo lugar com uma seta para voltar.

O trilho de páginas dentro do cartão leva diretamente a qualquer página disponível; a cápsula selecionada usa a cor de destaque. Abaixo das páginas, o mesmo trilho mostra os itens de plugins posicionados na barra (seguindo a ordem organizada das áreas quando personalizada, ou a ordem de posicionamento por padrão), exceto o clima, que a primeira página já mostra, com seus próprios ícones e dicas. Clique em um item com painel para abri-lo aqui e use Voltar para retornar. Os trilhos ficam à esquerda/direita nas barras superiores ou inferiores e acima/abaixo nas barras laterais, com espaços que deixam os cliques passar. Trilhos longos rolam; as cápsulas deslizam após a abertura e recolhem ao fechar, instantaneamente com Reduzir movimento.

| Página | O que tem |
| :--- | :--- |
| Calendário e clima | O clima ao lado do mês. Clique no clima para a previsão completa e a busca de cidades; clique em um dia para ver os planos e adicionar um lembrete em um horário desse dia. |
| Mídia | A capa cercada por barras que seguem a música, a música, a letra, os controles e uma barra de progresso. Só enquanto algo toca. Uma transmissão ao vivo, como uma rádio, mostra Ao vivo no lugar da barra de progresso, Parar no lugar de pausar, e não busca letra. |
| OBS | Status da gravação e da transmissão com pausar, parar e entrar ao vivo, uma marca de capítulo, a pasta de gravações e o OBS. Enquanto o OBS está aberto. |
| Controles rápidos | A página Geral da Central de controle: WiFi, Bluetooth, Som e Microfone abrem ali mesmo, ações rápidas, volume e brilho. |
| Tela | O próprio painel de Tela da barra: brilho, suas telas, Luz noturna e o perfil de energia. |
| Streaming | O próprio painel de Streaming da barra, para compartilhar este PC com dispositivos Moonlight. Aparece depois que o compartilhamento é configurado. |
| Assistente | O chat com o assistente da Central de controle, quando há um assistente configurado. |
| Plugins | A página Plugins da Central de controle: os plugins instalados e suas configurações. |
| Desempenho, Uso de IA e Notificações | Os próprios painéis Hardware e Uso de IA da barra, ali mesmo; a lista de notificações. |

Em todos os modos, o relógio mostra ao lado o que está acontecendo, no lugar do ponto de gravação: uma marca de calendário quando um evento começa em menos de dez minutos (clique para os planos desse dia) e um anel enquanto um temporizador, uma fase de foco ou o cronômetro corre (clique para abrir Relógio nessa página). Uma notificação nova toca duas vezes o sino da barra; onde o sino está oculto (Centralizada recolhida, Dinâmico em repouso), um sino desliza ao lado do relógio no lugar dele. A bateria de um notebook substitui a hora por um instante pela porcentagem em vermelho nos níveis de aviso fraco e crítico (padrão 10% e 5%); onde os espaços de trabalho estão ocultos, o mesmo vale para o número do espaço de trabalho para o qual você troca.

Em volta da hora, a cápsula da Gota mostra o que está acontecendo e só abre espaço onde precisa. Antes da hora: um ponto vermelho durante uma gravação, uma marca de calendário quando um evento começa em menos de dez minutos, um anel enquanto um temporizador, uma fase de foco ou o cronômetro corre (clique para abrir Relógio), uma seta girando enquanto a barra procura atualizações e a marca de atualizações enquanto a notificação delas aparece (clique para Atualizar o sistema) e uma nota enquanto toca música (clique para Mídia). Depois dela: um sino que toca duas vezes com uma notificação nova (clique para a lista). Trocar de espaço de trabalho substitui a hora por um instante pelo número; a bateria de um notebook faz o mesmo em vermelho nos níveis de aviso fraco e crítico (padrão 10% e 5%). Arraste a nota para a direita para transformar a cápsula em uma linha da letra; arraste para qualquer lado, pause ou pare para voltar.

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

Os pontos abaixo contam as janelas, até três, e ficam esmaecidos quando nenhuma está no espaço de trabalho atual daquela tela. Passe o ponteiro sobre um aplicativo fixado fechado para ver o nome; sobre um aplicativo com janelas abertas, abre-se um cartão ao lado do ícone com uma pré-visualização ao vivo de cada janela e seu título abaixo. Clique em uma pré-visualização para focar aquela janela ou use o botão do meio para fechá-la. As pré-visualizações capturam apenas enquanto o cartão está aberto; os ícones perto do ponteiro crescem, o mais próximo mais que os outros, e o dock se alonga para mantê-los dentro, exceto com **Reduzir movimento** ativado.

Clique em um ícone do dock para focar a janela usada mais recentemente, mudando de espaço se necessário; clique de novo para ir à próxima janela dele. O botão do meio fecha a janela mais recente. Listas longas rolam ao longo do dock. Tanto o dock quanto o cartão de pré-visualizações seguem Desfoque/Cor do tema, os cantos escolhidos e **Reduzir movimento**, e o cartão permanece dentro da tela.

**Dock** em **Configurações > Barra da área de trabalho** ativa ou desativa o dock. **Pré-visualizações do dock** na mesma aba ativa ou desativa as pré-visualizações ao vivo (ativado por padrão; quando desativado, o cartão mostra apenas os títulos das janelas). As opções `dock` e `dockPreviews` em `bar-settings.json` começam em `"yes"`. Não há atalho para o dock.

Aplicativos fixados permanecem totalmente opacos e sem pontos quando fechados; clique para abri-los em seu próprio escopo de aplicativo. Clique com o botão direito para Manter no Dock / Remover do Dock, Nova janela (quando houver uma entrada de desktop) e Fechar ou Fechar todas as janelas. Escape ou um clique fora fecha o menu. Aplicativos sem entrada de desktop não podem ser fixados.

Arraste os ícones ao longo do dock para organizar os fixados. Arraste um aplicativo aberto para a seção de fixados para mantê-lo ali ou arraste um fixado para fora dessa seção para removê-lo. Os outros ícones abrem espaço com uma animação curta (instantânea com Reduzir movimento); os não fixados mantêm a ordem das janelas do Hyprland. Um divisor fino separa as seções apenas quando ambas contêm aplicativos. Menus e arrastos mantêm o dock visível.

Os IDs das entradas de desktop são salvos em ordem no arquivo local `quickshell/desktop-bar/dock-pins.json`, sob `$XDG_CONFIG_HOME` (normalmente `~/.config`), com gravação atômica. Instalações novas não têm aplicativos fixados. As janelas são associadas pelos IDs das entradas de desktop, por StartupWMClass e pelas classes dos aplicativos.

A intensidade do desfoque é compartilhada com os terminais. Escolha Leve, Média (padrão) ou Forte em Barra da área de trabalho no Walker ou nas Configurações (SUPER + ,). Veja [Terminal e editores](handbook:terminal) para a limitação global e as configurações pessoais.

Configurações > Barra da área de trabalho inclui os marcadores de espaços (pontos, glifo, números e runas). Janelas mantém os efeitos e os espaçamentos.
