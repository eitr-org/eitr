# Temas, papéis de parede e estilo

Configurações (**SUPER + ,**) inclui os controles de Aparência; **Mais temas** abre o catálogo separado de Eitr Store (**SUPER + F2**).

## Layout das janelas

Escolha **Ladrilhos** (padrão, dwindle do Hyprland) ou **Rolagem** em **Configurações > Janelas > Layout das janelas** ou **Walker > Configurações > Área de trabalho > Janelas > Layout das janelas**. Rolagem organiza as janelas em colunas sobre uma faixa móvel. A escolha é salva localmente e permanece após trocas de tema, recargas e reinicializações; a seleção recarrega a configuração do compositor sem reiniciar a sessão.

Rolagem mostra Direção (Direita, Esquerda, Baixo, Cima), Largura padrão da coluna (Um terço, Metade, Dois terços, Inteira) e Ajuste do foco. Centralizar centraliza a coluna em foco; Ajustar a traz para a tela com o mínimo de movimento. Seguir o foco permite mover a faixa quando o foco muda, inclusive por cliques. Tela cheia com uma coluna permite que uma única coluna preencha a tela sem ativar o modo de tela cheia do aplicativo. Os padrões são Direita, Metade, Ajustar e os dois interruptores ligados. As opções continuam salvas ao voltar para Ladrilhos. O menu Layout das janelas do Walker oferece cada uma como submenu.

Somente em Rolagem: **SUPER + ALT + setas** muda o foco; **SUPER + ALT + SHIFT + Esquerda/Direita** troca as colunas; **SUPER + ALT + Equal/Minus** alterna a largura entre um terço, metade, dois terços e inteira. O ciclo redimensiona a coluna em foco; a largura padrão vale para colunas novas. Veja a [referência de teclado](handbook:shortcuts).


## Eitr Store

Abra a Eitr Store pelo lançador de aplicativos, SUPER + F2, menu Desktop do Walker ou Mais temas nas Configurações. A janela independente pode ser movida e redimensionada e usa a paleta das Configurações, com o cabeçalho EITR / STORE. Fechar ou pressionar Escape descarta seleções e revisões temporárias.

Temas, Plugins, Telas de bloqueio e Papéis de parede têm Instalado e Descobrir. Descobrir reúne cartões oficiais e da comunidade com selos de origem. Use Todos / Oficial / Comunidade para filtrar; a busca abrange as categorias carregadas da visualização atual. Temas também têm Claro/Escuro. Cima/Baixo muda a linha, Direita ou Tab entra na grade e Esquerda retorna; Ctrl+F foca a busca.

A busca fica acima da grade em Instalado e Descobrir. Escape ou o botão de limpar apaga a consulta. O botão de filtro ao lado oferece Todos / Claro / Escuro para temas; um ponto indica um filtro ativo.

Clique em um tema, bloqueio ou papel de parede instalado para usá-lo. Cartões em Descobrir abrem detalhes, imagens e fontes. Selecione temas ou pacotes de imagens e revise antes de confirmar a instalação. Atualizar todos atualiza temas em sequência e revisa cada plugin. Remover sempre pede confirmação; o tema e o bloqueio atuais ficam protegidos.

Plugins têm todas as permissões da sua conta. Cada instalação e atualização mostra fonte, commit fixado, autor, arquivos, comandos, pacotes e avisos. Revise o código e, se quiser, a orientação da IA. Commits da comunidade são fixados no índice. Revisões expiram após 15 minutos e ao fechar. Instalado > Adicionar aceita endereços Git HTTPS ou SSH de temas e plugins. Os cartões instalados abrem configurações, ativação, atualização e remoção; pacotes instalados pelo plugin sem uso podem ser removidos.

Bloqueios continuam sendo pacotes oficiais assinados. Instalar e remover exige senha de administrador. Eitr é integrado; desenhos usados pela sessão ou pelo login não podem ser removidos. Seus bloqueios próprios ficam no disco e reaparecem ao reinstalar o desenho.

Papéis de parede mostra imagens incluídas, próprias e cartões de pacotes. Clicar em um pacote usa sua primeira imagem; as imagens individuais também aparecem. Pacotes da comunidade contêm apenas imagens JPEG, PNG ou WebP verificadas. Elas entram no seletor e carrossel existentes; remover um pacote apaga somente seus arquivos. Protetores de tela não estão incluídos.


Repositório de temas: `eitr-org/eitr-themes`.

Escolha outro papel de parede antes de remover um pacote usado por uma seleção salva.

## Escolher tema e papel de parede

Escolha tema e papel de parede em Configurações > Aparência > Tema e papel de parede. Para os menus Escuro/Claro do Walker, use **Walker > Configurações > Área de trabalho > Aparência > Tema** ou **SUPER + Ctrl + Shift + N**. Um clique duplo direito no desktop vazio abre o carrossel. O Sol filtra temas claros e a Lua escuros; clique de novo no filtro ativo para mostrar todos.

O + abre o catálogo separado com o mesmo filtro. Ctrl+Tab alterna filtros, digitar busca, setas/Tab movem e Enter aplica. Backspace edita a busca, mesmo até ficar vazia; Esc limpa antes de fechar.

**SUPER + Ctrl + N** abre os papéis de parede e **SUPER + Shift + N** avança para o próximo. Uma marca indica a escolha ativa no Walker. As trocas não exibem notificações de sucesso. Monitores ultrawide, com largura de pelo menos duas vezes a altura, usam a versão 21:9 de cada imagem para reduzir o recorte; os demais usam a versão 4K 16:9.

O Eitr tem quatro papéis de parede: Fiorde da aurora (padrão), Fiorde ao entardecer, Rune Seal e Runestone. Escolha pelos mesmos controles; a paleta permanece igual. O quarto, Runestone, é animado: auroras se movem lentamente atrás do anel de runas, atualizam mais devagar atrás de janelas comuns, pausam atrás de aplicativos em tela cheia e ficam estáticas na tela de bloqueio.

A renderização por software (por exemplo, numa VM sem aceleração 3D) usa o papel de parede estático selecionado; o mesmo acontece se não for possível detectar o renderizador. Graphite foi removido; seleções salvas do Graphite mudam para Eitr e seu papel de parede padrão.

Os 13 temas integrados ficam disponíveis offline. Instale os 14 temas extras, incluindo os claros Freyja e Skaði, pelo catálogo oficial `eitr-org/eitr-themes`. Contas existentes receberam os 12 primeiros em segundo plano, com novas tentativas após falhas de rede, sem mudar o tema atual nem o papel de parede salvo. Contas novas recebem apenas os integrados.

Os 13 temas incluídos oferecem dez paletas escuras dos reinos: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim e Vanaheim. Cada tema dos reinos tem de dois a cinco papéis de parede originais, com estilos variados de tinta, guache, cel shading e pintura, nas duas proporções. O primeiro papel de parede geralmente corresponde à prévia do tema; Svartalfheim mantém sua prévia independente.

Eitr Light é a versão clara de Primordial Venom, com superfícies verde-claras, texto verde-escuro, detalhes em amarelo-esverdeado de veneno e realces de jade/esmeralda. Seus quatro papéis de parede estáticos são Fiorde ao entardecer (padrão), The Gates of Yggdrasil, Rune Seal e Primordial Drop, cada um com uma composição panorâmica própria. Selecione-o na categoria Clara; Eitr continua sendo o padrão. Papel de parede do tema usa a imagem estática selecionada na tela de bloqueio.

Se o Hyprpaper não conseguir exibir o papel de parede selecionado, a barra desenha a mesma imagem estática em cada tela afetada, incluindo as versões ultrawide. As escolhas de papel de parede e tema continuam valendo no modo Focus; a alternativa troca a imagem sem a animação de revelação.

## Seus próprios papéis de parede, temas e telas de bloqueio

Suas imagens, temas e telas de bloqueio ficam neste computador, em `~/.local/share/eitr/` (`wallpapers`, `themes` e `lockscreens`). O Eitr nunca os envia nem compartilha, e as atualizações nunca os alteram. Eles aparecem ao lado dos distribuídos, marcados como **Seu**, e só eles podem ser excluídos: selecione um, pressione **Delete** e depois Enter para confirmar ou Esc para mantê-lo.

- **Walker > Configurações > Área de trabalho > Aparência > Papel de parede > Adicionar meu papel de parede** aceita um arquivo de imagem ou um endereço https. Downloads param em 50 MB, e o Eitr só guarda uma cópia depois de verificar que o arquivo é uma imagem JPEG, PNG ou WebP. O endereço de uma página funciona quando a página oferece uma imagem principal; senão, copie o endereço da própria imagem. A imagem é aplicada na hora e aparece na lista de papéis de parede, no carrossel e com SUPER + Shift + N. Excluir o papel de parede em uso muda antes para o primeiro papel de parede do tema. Escolha se o papel de parede aparece com todos os temas ou só com o tema atual.
- **Walker > Configurações > Área de trabalho > Aparência > Tema > Criar tema** pede uma imagem (o papel de parede atual, um seu, um do tema ou outro arquivo ou endereço https), claro ou escuro (Automático segue o brilho da imagem) e um nome. Depois da revisão, o Eitr cria uma paleta completa a partir da imagem, mantendo o texto bem legível sobre o fundo, e aplica o tema à barra, ao terminal, ao lançador, aos apps e aos ícones. Em seguida vem uma lista de cores: escolha Destaque, Fundo, Texto ou uma das seis cores do terminal, digite seis dígitos hexadecimais e a alteração é aplicada na hora; Esc conclui. **Ctrl + E** em um dos seus temas abre a lista de novo. Excluir o tema em uso volta antes ao tema usado antes de criá-lo.
- **Walker > Configurações > Área de trabalho > Tela de bloqueio > Criar tela de bloqueio** usa o desenho Theme Wallpaper ou Material com sua imagem, uma cor de destaque opcional e uma saudação opcional abaixo do relógio, e depois mostra uma prévia. Ela é selecionada como qualquer desenho. A tela de login não consegue ler sua pasta pessoal: mostra o mesmo desenho, com sua imagem no Theme Wallpaper e a imagem do próprio desenho no Material. Excluir a tela de bloqueio em uso seleciona antes o desenho dela.

## Alterar o layout da barra

**Configurações > Barra da área de trabalho** escolhe layout, posição e aparência; veja [Barra da área de trabalho](handbook:desktop-bar). **Configurações > Janelas > Cantos** escolhe Quadrados, Arredondados ou Muito arredondados. Espaçamento das janelas e Reduzir movimento ficam na mesma página Janelas. Aplicativos externos podem manter seu estilo interno.

<!-- eitr-figure: window-style -->

Espaçamento das janelas e Cantos como **Configurações > Janelas** os mostra, com suas escolhas atuais marcadas. Por padrão, há 6 px entre janelas e 12 px nas bordas da tela.

Em **Configurações > Janelas > Espaçamento das janelas** ou **Walker > Configurações > Área de trabalho > Janelas > Espaçamento das janelas**, escolha Nenhum, Pequeno, Médio (padrão) ou Grande. A preferência local permanece após trocas de tema e recarregamentos.

## Alterar fontes

Escolha uma fonte instalada em Configurações > Aparência > Fontes e cursor. JetBrainsMono Nerd Font é o padrão. A escolha atualiza os apps compatíveis; alguns mantêm sua própria fonte. Para remover uma família, use Walker > Configurações > Área de trabalho > Aparência > Fontes e revise seus pacotes. A última família utilizável não pode ser removida.

## Alterar o ponteiro

Abra Configurações > Aparência > Fontes e cursor. Família do ponteiro escolhe Bibata Modern, Breeze ou Vanilla DMZ. Cor do ponteiro oferece Automático, Escuro ou Claro; Automático acompanha o tema sem trocar a família. Tamanho do ponteiro ajusta o tamanho. Escolhas explícitas de cor e tamanho sobrevivem às trocas de tema. A página mostra o ponteiro escolhido se seus arquivos estiverem disponíveis.

## Escolher uma tela de bloqueio

**Configurações > Tela de bloqueio** define o desenho da tela de bloqueio e da tela de login. As preferências existentes são mantidas nas trocas de tema.

Os desenhos disponíveis são Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing e Theme Wallpaper. Depois vêm as suas próprias telas de bloqueio; prévias não bloqueiam a sessão. Uma escolha removida da distribuição passa para Clockwork Tape. Novas instalações começam com Eitr.

Eitr mostra a marca EITR na cor de destaque do seu tema dentro do anel dourado de runas da tela de inicialização, que avança a cada segundo, sobre um céu estrelado com a Via Láctea, uma estrela cadente de vez em quando e a aurora da área de trabalho sobre preto puro (numa tela OLED esses pixels ficam apagados).

O relógio mostra horas e minutos com os numerais nórdicos do próprio Eitr e segue a preferência de 12 ou 24 horas. Cada caractere digitado entalha uma runa no campo de senha (sempre as mesmas runas, em ordem, então só o tamanho aparece); as setas, Home e End movem o cursor em bloco, e Backspace ou Delete esfarelam a runa ao lado.

A autenticação bem-sucedida desbloqueia a sessão imediatamente. Enviar a senha, uma falha de login e trocar de conta limpam as runas instantaneamente, sem esfarelar. Reduzir movimento deixa tudo parado e pula os efeitos de gravação e esfarelamento. Numa prévia, Enter e Esc a fecham imediatamente sem desbloquear nada.

A arte tem resolução alvo de 4K (3840×2160, 16:9). Coffee e Pillow mantêm o estilo anime tranquilo com roupas nórdicas; Material e Clockwork usam ornamentos rúnicos discretos. Nothing mantém seu desenho. QML e SVG continuam escaláveis.

Compare os nove desenhos com `bash quickshell/lockscreen/scripts/gallery.sh`. Isso não altera a tela de bloqueio escolhida; autenticação e ações de energia ficam desativadas na galeria. Clockwork usa QML procedural; Coffee, Pillow, Material e Nothing mantêm os layouts licenciados com arte nova e a fonte JetBrainsMono Nerd Font instalada. Não são necessários vídeos nem fontes incluídas separadamente.

**Papel de parede do tema** usa o papel de parede atual com relógio no alto à esquerda e senha no canto inferior direito. A prévia do Walker mostra a imagem atual. Mudanças posteriores aparecem no próximo bloqueio ou prévia; Ctrl+P mostra o layout inteiro sem bloquear. A tela de login não pode ler sua pasta pessoal, então usa uma cópia salva pelo Eitr ao escolher esse desenho e a cada troca de papel de parede. Se ela estiver indisponível, usa outro papel do tema atual ou o padrão Eitr.

Em PCs com várias contas, a tela de login mostra o usuário selecionado. Clique na metade esquerda ou direita do seletor, ou pressione Ctrl+Left / Ctrl+Right, para escolher outra conta; Enter continua enviando a senha e Escape mantém seu comportamento. Com uma conta, o layout de login não muda. A tela de bloqueio mostra o nome real da sessão bloqueada quando disponível e só aceita a senha dessa conta.

Com várias telas, a tela de login aparece apenas na maior; as outras ficam pretas.

Trocar usuário (Ctrl+Alt+U) abre o login do SDDM e mantém a sessão original bloqueada. Ao voltar para a sessão bloqueada, clique uma vez no campo de senha antes de digitar. A ação só aparece quando há várias contas elegíveis e o SDDM permite a troca. As prévias e a galeria usam três contas fictícias e nunca autenticam.

## Notas técnicas

O menu de inicialização do Limine usa as cores do tema atual, o título EITR e uma fonte maior. Novas instalações configuram isso; após trocar o tema, o menu acompanha no próximo desligamento. Se não for possível ler seu tema, usa as cores do padrão. As entradas de inicialização nunca são alteradas, e `limine.conf` recebe um backup antes de cada mudança. O estilo não é aplicado com Secure Boot ativo, pois alterar uma configuração do Limine cujo hash foi cadastrado impediria a inicialização.

## Prévias e atribuições de papéis de parede

Em Configurações > Aparência > Tema e papel de parede, clique em uma imagem para visualizar seu quadro estático na área de trabalho. Aplicar salva; Cancelar prévia, sair da página ou fechar restaura a escolha salva. A paleta não muda. Walker > Configurações > Área de trabalho > Aparência > Papel de parede abre o carrossel na imagem selecionada. As setas mostram a prévia; Enter aplica; Escape ou clicar fora cancela.

Acima dos papéis de parede do carrossel, **Este tema** e **Todos os temas** alternam entre os papéis de parede do tema atual e os de todos os temas instalados (Ctrl+Tab também alterna). O nome de cada papel de parede aparece embaixo dele (com todos os temas, também o tema de onde vem), e digitar busca nomes e temas; suas próprias imagens vêm por último. Escolher um muda só o papel de parede; as cores do tema continuam.

Papel de parede por tela em Configurações > Aparência > Tema e papel de parede (ou Walker > Configurações > Área de trabalho > Aparência > Papel de parede por tela) vem desligado: escolher ou visualizar um papel de parede muda todas as telas. Ligue para mudar apenas a tela que você está usando ao escolher a imagem. Uma tela sem escolha própria usa o papel de parede global.

As atribuições e o interruptor ficam nesta máquina. Desligar restaura imediatamente o papel de parede global em todas as telas, mantendo as escolhas por tela; ligar novamente restaura essas escolhas. Login e reconexão restauram cada saída separadamente. Trocar de tema limpa todas as escolhas por tela, mantém o interruptor e usa o papel de parede do novo tema. Escolher apenas um papel de parede mantém as escolhas por tela. Arquivos indisponíveis são removidos das atribuições. A animação Runestone volta após a prévia; a renderização por software usa a mesma imagem estática.
