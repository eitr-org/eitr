# Solução de problemas

## Verificar este PC

Abra **Configurações > Sistema > Manutenção > Verificar este PC** ou `eitr check`. As verificações só leem, sem reparar ou reiniciar nada. Não atualizam listas de pacotes. DNS usa a rede. `eitr check --json` mostra detalhes técnicos sem perguntas.

**Verificações aprofundadas (pede sua senha)**: Para verificações aprofundadas pressione Enter; Esc pula esta etapa. `sudo /usr/lib/eitr/eitr-system selfcheck-deeper` pede sua senha no mesmo terminal. Os resultados substituem as verificações correspondentes que foram puladas. Lê Snapper, pares pré/pós, a última atualização de pacotes bem-sucedida, qgroups Btrfs existentes, JSON da proteção de boot, um manifesto de fábrica já montado e chaves Arch Linux/Eitr com `pacman-key --list-keys`. Nunca ativa cotas nem monta o ponto de fábrica. Dados ausentes são pulados com motivo; o manifesto não verifica a integridade do arquivo. `fsck.vfat -n` verifica somente uma ESP FAT identificada sem ambiguidade e não montada para escrita; caso contrário pede que seja desmontada e pula a verificação.

Unidades com falha mostram até três nomes e um comando de estado. Descrições de snapshots não comprovam etapas posteriores; logs de hooks não têm datas. A barra não tem consulta estruturada de erros. Depois **Enter** copia o relatório com dados ocultados e **Esc** fecha. Revise antes de compartilhar; copiar exige `wl-copy`.


## Uma ação informa que falta uma ferramenta

Novas instalações incluem as dependências do desktop, mas uma instalação Arch existente pode não ter todas. Leia o erro e instale o pacote correspondente em Instalar > Pacotes > Pacman ou por uma atualização completa normal. Não remova BlueZ/iwd/PipeWire/WirePlumber só porque os controles estão em painéis nativos: os painéis ainda dependem desses serviços.

Este manual não precisa de `less`: é Markdown incluído em uma sobreposição nativa. Se informar um catálogo ausente ou desatualizado, atualize os arquivos do desktop EITR.

## Falta um auxiliar pertencente ao root

Troca de serviço de rede, segurança, limites de bateria e recuperação exigem auxiliares revisados pertencentes ao root. Uma instalação só de dotfiles pode ainda não ter os pacotes necessários. Consulte o capítulo relevante; nunca contorne a verificação executando como root um auxiliar baixado que o usuário pode modificar. Abrir o seletor não deve desconectar sua rede.

## Problemas de configuração ou serviços

O Quickshell mostra um erro de recarga legível e, quando possível, mantém a configuração anterior que funcionava. Corrija o arquivo indicado; não reinicie repetidamente o gerenciador de login. **Nunca reinicie o SDDM durante sua sessão do desktop.**

Reiniciar o Elephant recarrega os menus. Seu serviço deve manter `KillMode=process` para auxiliares e inicializações sem uwsm. Em uma sessão uwsm, aplicativos e terminais lançados usam escopos de aplicação separados. Temas regeneram estilos: se uma alteração desaparecer, corrija o gerador e o arquivo gerado.

## Os dados de WiFi pararam de atualizar

A barra compartilha um único processo de leitura de WiFi entre as telas. Se ele
encerrar, os últimos dados válidos ficam marcados como desatualizados enquanto o
processo tenta reiniciar com intervalos crescentes. Após seis tentativas sem
sucesso, ele aguarda uma nova tentativa explícita. Os controles nativos continuam
disponíveis. As ações de WiFi compartilham uma fila ordenada e o estado de ocupado entre as telas. Se uma ação exceder o prazo ou o processo encerrar, o resultado é desconhecido: atualize o estado antes de tentar novamente explicitamente. As escritas nunca são repetidas automaticamente. A geração de QR mantém seu auxiliar separado.

Para consultar o estado técnico, use
`eitr-shell desktop-bar ipc call -- data status`. A saída informa a idade dos
dados, códigos de erro, leituras em andamento, observadores e reinícios, sem nomes
ou endereços de rede. Tente novamente com
`eitr-shell desktop-bar ipc call -- data retry`.

A captura do OBS usa o mesmo processo compartilhado entre as telas. Uma única
verificação é executada a cada 2 segundos somente enquanto uma janela ou um
processo do OBS é conhecido. Os detalhes da gravação são atualizados a cada
2 segundos somente enquanto um painel de gravação está aberto e também fornecem
o estado compartilhado. Um estado desconhecido mantém o último estado de captura
conhecido e desativa os controles até uma atualização bem-sucedida. As ações de
captura e as alterações de opções compartilham uma fila ordenada; se o prazo
expirar ou o processo encerrar, o resultado fica desconhecido e a ação nunca é
repetida automaticamente. O comando independente do OBS continua disponível para
o Walker e os atalhos de captura de tela.

Bateria, perfis de energia e modo avião também compartilham este processo. A bateria é lida a cada 30 segundos; perfis e rádios são lidos somente enquanto os painéis correspondentes estão abertos. Baterias de periféricos não ativam controles de notebook. Os ganchos e avisos de bateria fraca mantêm seus limites. As ações de perfil e modo avião são ordenadas, informam erros ao painel solicitante e nunca são repetidas após um resultado desconhecido. Os comandos independentes continuam disponíveis.

## Verificações de instalação e recuperação

O EITR ainda está em beta: testes em VMs não comprovam cada adaptador WiFi, agente Bluetooth, TPM, GPU, leitor de impressão digital ou configuração de Secure Boot. O código atual dos serviços WiFi e da autenticação corporativa é testado com simulações; teste a autenticação real antes de depender dela. Mudar manifestos do repositório não muda ISOs existentes: reconstrua o payload e a ISO para levar essas alterações a novas instalações.

Faça backup dos outros discos antes de instalar em um SSD separado e confira cuidadosamente o disco de destino. O instalador apaga o disco que você confirmar. Guarde senhas de criptografia e chaves de recuperação offline. Snapshots nesse mesmo SSD não são backups independentes. Comece por [Recuperação e snapshots](handbook:recovery).

## Relatar um problema

**Configurações > Sistema > Informações > Relatar um problema** coleta versões do EITR e dos pacotes, hardware gráfico, erros do Hyprland, serviços com falha, avisos recentes, falhas da última semana, erros da inicialização anterior, log da instalação e mudanças recentes de pacotes em `~/Documents/eitr-problem-report-<time>.txt`, legível somente por você. Remove usuário, nome do computador, caminho da pasta pessoal, e-mail, IP e MAC; os logs ainda podem citar aplicativos ou arquivos. Leia antes de enviar.

Nada é enviado automaticamente. O terminal mostra somente onde salvou o relatório e oferece formas de enviar ou ler primeiro:

1. **Enviar por e-mail** para `reports@eitr.info`: seu aplicativo de e-mail abre uma mensagem com resumo; anexe o arquivo salvo.
2. **Abrir uma issue no GitHub** exige uma conta GitHub e abre uma nova issue do projeto. As issues são públicas.
3. **Copiar o relatório** para colar onde quiser.
4. **Ler o relatório** abre o editor de texto.

O relatório é usado somente para identificar e corrigir o problema e é excluído quando ele é resolvido. Um e-mail também compartilha seu endereço; responda a ele a qualquer momento para pedir a exclusão do relatório.

### Quando um componente falha

As Notificações de falhas ficam ativadas por padrão. Um serviço de usuário acompanha novos registros legíveis do systemd-coredump dos seus próprios programas. Cada falha oferece Relatar um problema, Ignorar e Silenciar este programa; Perguntar à IA aparece quando há um assistente padrão instalado e selecionado. Falhas repetidas de um programa geram no máximo uma notificação a cada cinco minutos. Uma falha que encerra a sessão é oferecida no próximo login, mas não as de programas que falham no minuto seguinte a sair, reiniciar ou desligar: eles estão apenas perdendo a área de trabalho. Ative ou desative em Principal > Ações rápidas ou Central de controle > Ações rápidas. As preferências e os caminhos silenciados ficam em `~/.config/eitr/crash-help.json`; remova um caminho de `ignored` para voltar a receber avisos.

Perguntar à IA abre seu assistente padrão apenas com programa, sinal e rastreamento de pilha do `coredumpctl info`, pedindo uma explicação e uma sugestão de correção sem alterar o sistema sem sua autorização. Nenhum despejo de memória é enviado ao assistente. Ao escolher essa ação, o assistente pode enviar o resumo ao provedor. Relatar um problema anexa o mesmo resumo ao fluxo existente: revise antes de compartilhar; nada é enviado automaticamente.

## Personalizações e atualizações

O código do EITR fica em `/usr/share/eitr` e é atualizado pelo pacote `eitr-desktop`; suas configurações ficam em `~/.config`. Coloque mudanças duradouras onde as atualizações não mexem:

- Monitores, dispositivos, atalhos e regras adicionais: `~/.config/hypr/local.lua`.
- Complementos do shell: `~/.config/eitr/shell.local.zsh`.
- Opções do terminal: `~/.config/kitty/local.conf`.
- Cores do launcher: `~/.config/walker/style.override.css`.
- Substituição completa de um arquivo distribuído: mesmo caminho relativo em `~/.config/eitr/overrides`. Esse arquivo deixa de receber correções das atualizações.

Arquivos como `kitty/theme.conf` e o estilo do Walker são regenerados ao trocar temas e uma vez após cada atualização do pacote. As cópias anteriores ficam em `~/.local/state/eitr/generated-backups`. Se uma atualização muda o formato de uma preferência, ela é convertida uma vez no login; uma falha é informada e tentada novamente no próximo login (`~/.local/state/eitr/migrations.log`). `eitr-config status` lista configurações e substituições ativas.

Terminais de tarefas que falharam oferecem **A: perguntar à IA** quando há um assistente padrão; **Esc** fecha. Só as últimas 200 linhas ficam na memória, sem sequências ANSI e com linhas de segredos evidentes ocultadas antes do envio: um assistente na nuvem envia essa saída ao provedor, enquanto Ratatoskr a mantém neste PC.


A topologia das telas, o brilho e a luz noturna também compartilham o broker. Eventos dos monitores e mudanças na preferência de tela principal atualizam a geometria em todas as telas. O brilho e a luz noturna são atualizados apenas enquanto observados; o brilho DDC não é consultado periodicamente. Os testes de tela mantêm a reversão automática independente mesmo se a barra ou o broker encerrar. Os comandos de tela e de redução/restauração do brilho por inatividade continuam disponíveis.
