# Temas, papéis de parede e estilo

## Temas e papéis de parede

Abra **Configurações > Estilo > Tema** ou **SUPER + Ctrl + Shift + N**. Escolha escuro ou claro e depois um tema. Digite no carrossel de temas para filtrar; setas ou Tab navegam e Enter aplica. Backspace primeiro edita a busca; Escape a limpa antes de fechar. O seletor de categoria e o carrossel de papéis de parede não têm busca de temas.

**SUPER + Ctrl + N** abre os papéis de parede e **SUPER + Shift + N** avança para o próximo. Uma marca indica a escolha ativa no Walker. As trocas não exibem notificações de sucesso. Monitores ultrawide, com largura de pelo menos duas vezes a altura, usam a versão 21:9 de cada imagem para reduzir o recorte; os demais usam a versão 4K 16:9.

O Eitr tem quatro papéis de parede: Primordial Drop (padrão), Runestone, Élivágar e Venom Rootlight. Escolha pelos mesmos controles; a paleta permanece igual. O segundo, Runestone, é animado: auroras se movem lentamente atrás do anel de runas, atualizam mais devagar atrás de janelas comuns, pausam atrás de aplicativos em tela cheia e ficam estáticas na tela de bloqueio. A renderização por software (por exemplo, numa VM sem aceleração 3D) usa o papel de parede estático selecionado; o mesmo acontece se não for possível detectar o renderizador. Graphite foi removido; seleções salvas do Graphite mudam para Eitr e seu papel de parede padrão.

Os 24 temas incluídos oferecem dez paletas escuras dos reinos: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim e Vanaheim. Cada tema dos reinos tem de dois a cinco papéis de parede originais, com estilos variados de tinta, guache, cel shading e pintura, nas duas proporções. O primeiro papel de parede é a prévia do tema.

Se o Hyprpaper não conseguir exibir o papel de parede selecionado, a barra desenha a mesma imagem estática em cada tela afetada, incluindo as versões ultrawide. As escolhas de papel de parede e tema continuam valendo no modo Focus; a alternativa troca a imagem sem a animação de revelação.

## Seus próprios papéis de parede, temas e telas de bloqueio

Suas imagens, temas e telas de bloqueio ficam neste computador, em `~/.local/share/eitr/` (`wallpapers`, `themes` e `lockscreens`). O Eitr nunca os envia nem compartilha, e as atualizações nunca os alteram. Eles aparecem ao lado dos distribuídos, marcados como **Seu**, e só eles podem ser excluídos: selecione um, pressione **Delete** e depois Enter para confirmar ou Esc para mantê-lo.

- **Configurações > Estilo > Papel de parede > Adicionar meu papel de parede** aceita um arquivo de imagem ou um endereço https. Downloads param em 50 MB, e o Eitr só guarda uma cópia depois de verificar que o arquivo é uma imagem JPEG, PNG ou WebP. O endereço de uma página funciona quando a página oferece uma imagem principal; senão, copie o endereço da própria imagem. A imagem é aplicada na hora e aparece na lista de papéis de parede, no carrossel e com SUPER + Shift + N. Excluir o papel de parede em uso muda antes para o primeiro papel de parede do tema. Escolha se o papel de parede aparece com todos os temas ou só com o tema atual.
- **Configurações > Estilo > Tema > Criar tema** pede uma imagem (o papel de parede atual, um seu, um do tema ou outro arquivo ou endereço https), claro ou escuro (Automático segue o brilho da imagem) e um nome. Depois da revisão, o Eitr cria uma paleta completa a partir da imagem, mantendo o texto bem legível sobre o fundo, e aplica o tema à barra, ao terminal, ao lançador, aos apps e aos ícones. Em seguida vem uma lista de cores: escolha Destaque, Fundo, Texto ou uma das seis cores do terminal, digite seis dígitos hexadecimais e a alteração é aplicada na hora; Esc conclui. **Ctrl + E** em um dos seus temas abre a lista de novo. Excluir o tema em uso volta antes ao tema usado antes de criá-lo.
- **Configurações > Estilo > Tela de bloqueio > Criar tela de bloqueio** usa o desenho Theme Wallpaper ou Material com sua imagem, uma cor de destaque opcional e uma saudação opcional abaixo do relógio, e depois mostra uma prévia. Ela é selecionada como qualquer desenho. A tela de login não consegue ler sua pasta pessoal: mostra o mesmo desenho, com sua imagem no Theme Wallpaper e a imagem do próprio desenho no Material. Excluir a tela de bloqueio em uso seleciona antes o desenho dela.

## Barra e cantos

**Configurações > Estilo > Barra da área de trabalho** escolhe desfoque ou cor do tema, layout completo ou centralizado e borda. O Walker acompanha essa aparência. **Configurações > Estilo > Cantos** escolhe cantos quadrados, arredondados ou muito arredondados para as superfícies do EITR e decorações do compositor. Aplicativos de terceiros podem manter seus controles próprios; pontos de estado circulares continuam circulares.

## Fontes

**Configurações > Estilo > Fontes** lista famílias de fontes instaladas utilizáveis, não cada variante em negrito ou itálico. Famílias de documentos e de reserva ficam ocultas. JetBrainsMono Nerd Font é o padrão. A seleção atualiza os aplicativos compatíveis; ligaturas são ativadas quando disponíveis. Remover uma família remove suas variantes instaladas compatíveis; a última opção utilizável não pode ser removida. Pode ser necessário conferir a qual pacote a fonte pertence.

## Cursor

**Configurações > Estilo > Cursor** oferece Bibata Modern, Breeze e Vanilla DMZ. Cor oferece automático, escuro e claro; Tamanho define o tamanho do ponteiro. Automático segue a categoria clara ou escura do tema sem trocar a família escolhida. Cores definidas explicitamente são preservadas. A linha selecionada tem uma marca à esquerda; outras famílias mostram prévias. Recursos ausentes geram um erro em vez de salvar uma escolha inválida.

O menu de inicialização do Limine usa as cores do tema atual, o título EITR e uma fonte maior. Novas instalações configuram isso; após trocar o tema, o menu acompanha no próximo desligamento. Se não for possível ler seu tema, usa as cores do padrão. As entradas de inicialização nunca são alteradas, e `limine.conf` recebe um backup antes de cada mudança. O estilo não é aplicado com Secure Boot ativo, pois alterar uma configuração do Limine cujo hash foi cadastrado impediria a inicialização.

**Configurações > Estilo > Tela de bloqueio** define o desenho da tela de bloqueio e da tela de login. As preferências existentes são mantidas nas trocas de tema.

Os desenhos disponíveis são Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing e Theme Wallpaper. Depois vêm as suas próprias telas de bloqueio; prévias não bloqueiam a sessão. Uma escolha removida da distribuição passa para Clockwork Tape. Novas instalações começam com Eitr.

Eitr mostra a marca EITR na cor de destaque do seu tema dentro do anel dourado de runas da tela de inicialização, que avança a cada segundo, sobre um céu estrelado com a Via Láctea, uma estrela cadente de vez em quando e a aurora da área de trabalho sobre preto puro (numa tela OLED esses pixels ficam apagados). O relógio mostra horas e minutos com os numerais nórdicos do próprio Eitr e segue a preferência de 12 ou 24 horas. Cada caractere digitado entalha uma runa no campo de senha (sempre as mesmas runas, em ordem, então só o tamanho aparece); as setas, Home e End movem o cursor em bloco, e Backspace ou Delete esfarelam a runa ao lado. Depois que a senha é aceita e a sessão já está desbloqueada, um raio cai no meio da tela e a tela de bloqueio queima a partir dali como papel, até revelar a área de trabalho. Reduzir movimento deixa tudo parado e pula esses efeitos. Numa prévia, Enter mostra o efeito de desbloqueio sem desbloquear nada e Esc a fecha.

A arte tem resolução alvo de 4K (3840×2160, 16:9). Coffee e Pillow mantêm o estilo anime tranquilo com roupas nórdicas; Material e Clockwork usam ornamentos rúnicos discretos. Nothing mantém seu desenho. QML e SVG continuam escaláveis.

Compare os nove desenhos com `bash quickshell/lockscreen/scripts/gallery.sh`. Isso não altera a tela de bloqueio escolhida; autenticação e ações de energia ficam desativadas na galeria. Clockwork usa QML procedural; Coffee, Pillow, Material e Nothing mantêm os layouts licenciados com arte nova e a fonte JetBrainsMono Nerd Font instalada. Não são necessários vídeos nem fontes incluídas separadamente.

**Papel de parede do tema** usa o papel de parede atual com relógio no alto à esquerda e senha no canto inferior direito. A prévia do Walker mostra a imagem atual. Mudanças posteriores aparecem no próximo bloqueio ou prévia; Ctrl+P mostra o layout inteiro sem bloquear. A tela de login não pode ler sua pasta pessoal, então usa uma cópia salva pelo Eitr ao escolher esse desenho e a cada troca de papel de parede. Se ela estiver indisponível, usa outro papel do tema atual ou o padrão Eitr.

Em PCs com várias contas, a tela de login mostra o usuário selecionado. Clique na metade esquerda ou direita do seletor, ou pressione Ctrl+Left / Ctrl+Right, para escolher outra conta; Enter continua enviando a senha e Escape mantém seu comportamento. Com uma conta, o layout de login não muda. A tela de bloqueio mostra o nome real da sessão bloqueada quando disponível e só aceita a senha dessa conta. Trocar usuário (Ctrl+Alt+U) abre o login do SDDM e mantém a sessão original bloqueada. Ao voltar para a sessão bloqueada, clique uma vez no campo de senha antes de digitar. A ação só aparece quando há várias contas elegíveis e o SDDM permite a troca. As prévias e a galeria usam três contas fictícias e nunca autenticam.
