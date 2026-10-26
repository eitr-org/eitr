# Dispositivos e entrada

Encontre estes controles em **Sistema > Dispositivos e entrada** ou nos ícones correspondentes da barra. A Central de controle também oferece os botões e controles deslizantes de uso diário.

## Áudio e microfone

Volume seleciona a saída padrão e controla o volume geral e dos aplicativos em reprodução. Os dispositivos aparecem com nome legível e ícone do tipo; clique no dispositivo atual para escolher outro e use o botão de lápis de um dispositivo para renomeá-lo neste computador. Microfone seleciona a entrada padrão, o ganho e o mudo. O medidor de nível do microfone funciona somente enquanto o painel está aberto e não grava áudio em disco. Abrir outras configurações não inicia o monitoramento do microfone.

Os controles deslizantes chegam a 100%; um valor maior já existente só muda quando você move o controle. Trocar o dispositivo de áudio padrão pode afetar uma chamada: faça isso conscientemente. Os controles de reprodução são separados da seleção do dispositivo padrão.

## Tela e brilho

O painel de Tela lista os monitores ativos. Clique em um para abrir as configurações dentro do cartão; clique novamente para fechar. O monitor **Principal** recebe a barra, os painéis e as notificações: ative **Tela principal** nas configurações de outro monitor para movê-los. Se ele for desconectado, outro aparecerá como **Principal** e receberá a barra até sua volta; sua escolha será mantida.

As configurações incluem resolução, taxa de atualização, escala e, com vários monitores, posição em relação a outro ou espelhamento. O principal fica onde está e os demais são posicionados ao redor dele; por isso, sua linha de Posição apenas informa isso. Um monitor pode ficar ao lado de qualquer outro, exceto de um já posicionado em relação a ele.

Cada configuração mostra o valor atual em uma linha; clique para ver as opções. Posição, alinhamento, escala, espelhamento e monitor principal são aplicados e salvos imediatamente. Uma nova **resolução ou taxa de atualização** pode deixar a tela preta; nesses casos, o painel pergunta **Manter estas configurações?** na parte inferior. Sem clicar em **Manter** em 15 segundos, a alteração é desfeita automaticamente, mesmo com o painel fechado. As configurações deste computador ficam em `~/.config/hypr/displays.json`.

É possível organizar qualquer quantidade de monitores: coloque cada um à esquerda, à direita, acima ou abaixo de outro e alinhe pelo topo, meio ou base (esquerda, centro ou direita quando empilhados). A disposição é lembrada: ao mudar a resolução ou escala de um monitor, seus vizinhos acompanham a mudança. Opções que causariam sobreposição são recusadas com uma mensagem. Cada monitor conectado recebe uma posição exata, de modo que mudar um não faz o Hyprland reposicionar os demais.

**Editar layout manualmente** abre `~/.config/hypr/local.lua` para configurações que o painel não cobre, como telas giradas ou espaços de trabalho fixados em um monitor. Um arquivo novo contém exemplos comentados de três monitores, orientação vertical, empilhamento, espelhamento e notebook conectado a uma base. Nada muda até você descomentar um exemplo e executar `hyprctl reload`. Monitores definidos nesse arquivo têm prioridade sobre o painel; remova essas definições para voltar a gerenciá-los aqui.

O brilho prioriza um controle nativo de iluminação disponível; caso contrário, tenta controlar um monitor externo por DDC. A disponibilidade depende do monitor e das permissões. A Luz noturna tem um botão manual e uma programação opcional com horários editáveis.

**HDR** aparece apenas em monitores cujo EDID informa suporte a PQ ou HLG. Exibe a área de trabalho em HDR; jogos podem usar HDR mesmo com a opção desativada. Ativar ou desativar HDR também pede confirmação em 15 segundos; sem ela, a alteração é desfeita. Com HDR ativo, **Brilho do conteúdo SDR** ajusta o conteúdo SDR de 1,0× a 2,0× e salva imediatamente. Jogos HDR em tela cheia ainda podem alternar o monitor automaticamente quando o HDR da área de trabalho está desativado.

## Teclado

Adicione e remova layouts no Walker: Sistema > Dispositivos e entrada > Teclado. Adicionar layout lista todos os idiomas e variantes (digite para buscar); selecione um layout e pressione Delete para removê-lo. São permitidos até quatro, sem duplicatas, e pelo menos um deve permanecer. **Alt + Shift** alterna entre eles. Com dois ou mais, a barra mostra o código do layout ativo (como US ou BR); clique nele, ou use a Central de controle, para trocar. O layout do teclado é independente do idioma e da localidade do sistema.

A área de trabalho começa com o teclado escolhido no instalador. A opção US inclui US e US International; basta Alt + Shift para acessar os acentos.

### Navegação opcional com Caps Lock

A configuração opcional do keyd em `distro/keyd/navigation.conf.example` faz um toque em Caps Lock enviar Escape. Segure Caps Lock e pressione H/J/K/L para esquerda/baixo/cima/direita. As outras teclas mantêm seu comportamento normal.

Para restaurar essa preferência após reinstalar, instale o exemplo como `/etc/keyd/navigation.conf` e ative `keyd.service`. Ele se aplica a todos os teclados, inclusive fora do Hyprland, e não é ativado por padrão. Para desfazer, remova a configuração e recarregue o keyd; desative o serviço se nenhum outro mapeamento o usar. A escolha do idioma e do layout continua separada.

## Energia e bateria de notebooks

Os controles de bateria e perfil de energia aparecem apenas quando há uma bateria do sistema, não apenas um fone ou mouse sem fio. Economia/Equilibrado/Desempenho exigem power-profiles-daemon; perfis sem suporte ficam indisponíveis. Estimativas e saúde da bateria só aparecem quando o hardware fornece esses dados.

O Limite de carga da bateria exige uma interface sysfs compatível no firmware e uma confirmação digitada. Desativado permite carregar até 100%. Nem todo notebook oferece esse recurso.

Uma notificação avisa ao chegar a 10% e outra, urgente, a 5%, uma vez a cada descarga. Em notebooks, o instalador também adiciona o firmware de áudio necessário aos modelos mais recentes (`sof-firmware`) e, nos modelos Intel, `thermald` para controlar o calor.

Estes recursos são **experimentais** até os primeiros usuários confirmarem seu funcionamento em notebooks reais: teclas de iluminação do teclado e fechamento da tampa com monitor externo conectado. Nesse caso, a tela do notebook é desligada e a área de trabalho vai para o monitor externo; abrir a tampa a traz de volta. Sem monitor externo, fechar a tampa suspende normalmente. A hibernação não é configurada automaticamente.
