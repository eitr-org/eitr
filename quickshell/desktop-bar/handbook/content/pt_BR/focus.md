# Focus

![Faixa de abas do Focus com janelas de exemplo e dois painéis unidos.](assets/focus-strip.png)

O Focus troca a barra por uma faixa de abas de 28 px no topo de cada monitor.
Abra **Estilo > Focus** ou **Central de controle > Estilo > Focus**, ou execute
`eitr focus on`. `eitr focus status` mostra `on` ou `off` sem consultar o
Hyprland. `eitr focus off` restaura a barra, os efeitos e os atalhos normais.
Não há atalho exclusivo para alternar o modo.

A preferência fica em `~/.config/eitr/focus.json` (sob `$XDG_CONFIG_HOME`, quando
definido). Reinicializações, atualizações e mudanças de tema a preservam. As
preferências da barra normal ficam separadas e não são substituídas.

## Abas e painéis

As janelas abertas, incluindo as flutuantes e as da área de trabalho especial,
são reunidas em grupos nativos do Hyprland. Um grupo ocupa toda a tela abaixo
da faixa. Espaçamentos, bordas, cantos arredondados, desfoque, sombras e animações
ficam desativados. A faixa acompanha o tema, tem bordas retas como o layout Abas
e mostra apenas títulos, relógio e estado da rede/bateria. A bateria só aparece
se houver uma bateria do sistema. Títulos longos são abreviados; muitas abas
permitem rolagem. A aba em destaque identifica a janela em foco. Linhas na cor
de destaque unem os painéis visíveis da divisão. Aplicativos podem manter o
estilo interno de suas próprias caixas e menus.

- **SUPER + 1–9** seleciona a aba 1–9 do monitor em foco.
- **SUPER + Tab / SUPER + Shift + Tab** avança/volta uma aba.
- **SUPER + backslash** divide o grupo com sua próxima aba, lado a lado.
- **SUPER + minus** empilha essa próxima aba abaixo.
- **SUPER + H/J/K/L** muda o foco para esquerda/baixo/cima/direita.
- **SUPER + Shift + H/J/K/L** redimensiona para mais estreito/alto/baixo/largo, como no modo normal.
- **SUPER + Shift + backslash** devolve a janela em foco a um grupo de abas em tela cheia, reunindo todos os painéis nas abas.

Dividir exige outra aba no grupo em foco. O limite é quatro painéis: dois ficam
lado a lado ou empilhados; três ou quatro usam uma grade 2×2 (o terceiro ocupa
toda a linha inferior até surgir o quarto). O redimensionamento ajusta os
divisores compartilhados da grade. O atalho de retorno restaura um único grupo em tela cheia com uma tecla. A numeração segue a ordem de janelas do compositor, também usada
pela faixa. Os atalhos normais de áreas de trabalho, flutuação, movimentação e
visibilidade da barra ficam inativos. Lançadores, fechar janela, Central de
Controle e Manual continuam disponíveis. Aprender > Atalhos mostra as teclas do Focus enquanto ele está ativo.

## Monitores e recuperação

Cada monitor tem suas janelas, faixa e até quatro painéis. Atalhos de abas agem
no monitor em foco; o foco direcional pode passar a outro monitor quando não há
painel nessa direção. Conectar um monitor cria sua faixa. Ao desconectá-lo, o
Hyprland move suas janelas para um monitor disponível, onde o Focus as reúne.
A seleção de monitores da barra normal não limita as faixas do Focus.

Desativar o Focus desfaz os grupos e distribui as janelas por áreas numeradas,
duas por área, mantendo seus monitores atuais. Posições anteriores, geometria
flutuante e estado de tela cheia dos aplicativos não são preservados. Uma área
vazia e comandos on/off repetidos são aceitos. Se o processo da faixa falhar,
os grupos nativos e a navegação por teclado continuam funcionando. Execute
`eitr focus off` em um terminal para recuperar a área de trabalho sem a faixa.
Recarregar o Hyprland reaplica a preferência e reúne novas janelas sem desfazer
as divisões existentes; os tamanhos dos divisores e a orientação de dois painéis
voltam ao padrão. Uma falha de comando mostra o erro; tente `eitr focus off`
novamente quando o Hyprland estiver acessível. Fechar um painel expande os restantes.
