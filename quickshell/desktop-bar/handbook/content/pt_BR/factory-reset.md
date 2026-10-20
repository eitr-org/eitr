# Redefinição de fábrica

Computadores instalados com a ISO do Eitr podem voltar ao estado do primeiro login em Walker → Sistema → Manutenção → Redefinição de fábrica. A redefinição é local: restaura uma cópia somente leitura salva no mesmo disco. Isso não é um backup nem um apagamento seguro; uma falha no disco perde tanto o sistema quanto seu ponto de restauração.

## O ponto de restauração

A última etapa do instalador guiado executa `eitr-factory-reset capture`, que salva a instalação concluída no subvolume Btrfs de nível superior `@eitr-factory`:

| Caminho | Conteúdo |
|---|---|
| `root` | snapshot somente leitura de `@` (sistema, contas e configurações) |
| `home` | snapshot somente leitura de `@home` (pastas pessoais preparadas na instalação) |
| `boot.tar` | arquivos da partição EFI: Limine, seu menu, kernel e initramfs |
| `manifest.json` | data de criação, UUIDs do sistema de arquivos e da partição EFI, contas e SHA-256 de `boot.tar` |

O próprio `@eitr-factory` também se torna somente leitura. Ele fica ao lado de `@`, não em `@/.snapshots`: o Snapper nunca o lista nem o remove na limpeza, e o Walker não oferece uma opção para excluí-lo. O root ainda pode excluí-lo, e uma formatação ou falha no disco o destrói. Seus snapshots compartilham dados com o sistema em execução; ocupam pouco espaço inicialmente e crescem conforme as atualizações substituem os arquivos originais.

`capture` se recusa a substituir um ponto de restauração existente. Instalações feitas sem a ISO não possuem um, e a Redefinição de fábrica informa isso.

## Os dois modos de redefinição

**Apagar Tudo** devolve o computador ao primeiro login: aplicativos instalados depois, configurações alteradas, contas adicionadas posteriormente e todos os arquivos nas pastas pessoais são removidos.

**Manter os Meus Arquivos** restaura o sistema, os aplicativos e as configurações, preservando as pastas pessoais. Para cada conta presente no ponto de restauração, as entradas ocultas atuais (`~/.config`, `~/.local`, `~/.ssh`, perfis de navegador e outras) são movidas para uma pasta visível chamada `Settings before reset <date time>` na pasta pessoal; depois, as entradas ocultas do ponto de restauração são copiadas de volta. Nada da pasta pessoal é excluído. Contas adicionadas após a instalação são removidas do sistema, mas suas pastas permanecem em `/home`.

Ambos os modos mantêm a senha de criptografia do disco (o cabeçalho LUKS nunca é alterado) e a senha atual de cada conta também presente no ponto de restauração. O slot de desbloqueio por TPM permanece no cabeçalho LUKS, mas o initramfs restaurado solicita a senha até que esse desbloqueio seja configurado novamente. Os logs (`@log`) e o cache de pacotes (`@pkg`) são preservados.

## Confirmação

A ação do Walker mostra dois avisos separados em um terminal:

1. O que a redefinição escolhida remove e preserva. Somente `y` ou `yes` permite continuar; Enter cancela.
2. Qual computador será redefinido, que ele reiniciará imediatamente e que o trabalho não salvo será perdido. É necessário digitar exatamente `RESET MY COMPUTER`.

O auxiliar pertencente ao root (`/usr/lib/eitr/eitr-factory-reset`) verifica novamente a frase digitada e valida estes pontos antes de alterar qualquer coisa:

- `/` é o subvolume `@` e `/home` é `@home` no mesmo sistema de arquivos Btrfs; `/boot` é a partição EFI em FAT.
- O ponto de restauração e seus snapshots continuam somente leitura; o manifesto identifica esse sistema de arquivos e essa partição EFI, e `boot.tar` corresponde ao SHA-256 registrado.
- O Secure Boot está desativado: os arquivos de inicialização restaurados não estão assinados com as chaves cadastradas.
- Não há outra redefinição pendente.

`sudo /usr/lib/eitr/eitr-factory-reset status` (Walker → Status da redefinição) realiza as mesmas verificações sem alterar nada.

## Como a redefinição funciona

A raiz e a pasta pessoal em uso nunca são modificadas. Em um novo subvolume de nível superior, `@eitr-reset-previous`, o auxiliar:

1. Cria um snapshot gravável da raiz do ponto de restauração, recria nele o subvolume `.snapshots` do Snapper, copia as senhas atuais e habilita `eitr-factory-reset-finish.service` nesse novo sistema.
2. Cria a nova pasta pessoal: um snapshot gravável da pasta pessoal do ponto de restauração (Apagar Tudo), ou um snapshot do `@home` atual com as configurações separadas conforme descrito acima (Manter os Meus Arquivos).
3. Arquiva os arquivos atuais da partição EFI em `boot.tar` e extrai o arquivo do ponto de restauração, preparando-o para a cópia.

Uma falha até esse ponto exclui `@eitr-reset-previous` e deixa o computador intacto. Em seguida, o auxiliar copia os arquivos de inicialização restaurados para a partição EFI (se falhar, restaura o arquivo que acabou de criar), renomeia `@` e `@home` para `old@` e `old@home` dentro de `@eitr-reset-previous`, renomeia os subvolumes preparados para `@` e `@home` e reinicia. Se uma renomeação falhar, os nomes anteriores e os arquivos de inicialização são restaurados.

Na próxima inicialização, `eitr-factory-reset-finish.service` confirma que a raiz em execução é a restaurada, exclui `@eitr-reset-previous` (inclusive os snapshots do Snapper do sistema antigo) e se desativa.

## Recuperação de uma redefinição interrompida

Uma queda de energia durante as renomeações pode deixar `@` ou `@home` ausente. Inicialize pela ISO do Eitr, pressione Escape para sair do assistente, desbloqueie o disco se estiver criptografado (`cryptsetup open /dev/<partition> root`) e inspecione:

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # or the Btrfs partition itself
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- `@` e `@home` existem e `@eitr-reset-previous/new-root` não existe mais: a troca terminou. Reinicie; o serviço de finalização fará a limpeza.
- `@` ou `@home` está ausente: renomeie o `@eitr-reset-previous/old@` ou `old@home` correspondente de volta (`mv /mnt/@eitr-reset-previous/old@ /mnt/@`), extraia `@eitr-reset-previous/boot.tar` na partição EFI para corresponder ao sistema antigo e reinicie.

Só exclua `@eitr-reset-previous` com `btrfs subvolume delete --recursive` depois que o sistema iniciar corretamente; até lá, ele guarda o sistema anterior.

## Verificação

Testado em VMs UEFI sem rede (veja [LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)): os dois modos em uma instalação não criptografada com apagamento do disco e em uma instalação LUKS2 ao lado de um disco com estrutura semelhante à do Windows. Cada teste foi seguido de inicialização, login e limpeza pelo serviço de finalização bem-sucedidos. Ainda não testado: hardware real, queda de energia durante a troca e preservação do ponto de restauração durante atualizações online do sistema (as VMs não tinham rede).
