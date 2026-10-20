# Snapshots de recuperação do Eitr

Snapshots são pontos de recuperação, **não backups em outro dispositivo**. Uma falha no disco pode destruir o sistema e seus snapshots juntos. Mantenha backups independentes.

O Eitr oferece suporte ao Snapper em uma raiz Btrfs com `/usr`, `/etc` e `/var/lib/pacman` no mesmo subvolume raiz. `/home` pode ser separado: ele não é coberto pelo snapshot da raiz. Layouts incompatíveis bloqueiam a atualização antes de qualquer alteração. `install.sh` não formata discos nem reorganiza subvolumes existentes; somente `eitr-guided-install`, na ISO, apaga o disco que você confirmar e cria esse layout (veja a seção de instalação guiada no README).

## Antes das atualizações

O instalador habilita `/etc/eitr/system-update-policy.conf`. Antes de Sistema → Manutenção → Atualizar → Atualizar o sistema atualizar os pacotes oficiais e do AUR, o fluxo:

1. Verifica o layout compatível e a configuração de raiz do Snapper.
2. Arquiva `/boot` e `/efi` somente quando são montagens separadas (um diretório `/boot` dentro da raiz Btrfs já está no snapshot da raiz). Os arquivos ficam em `/var/lib/eitr/boot-backups/<snapshot-number>/`, acessíveis apenas ao root.
3. Cria um snapshot da raiz anterior à atualização.
4. Aborta a atualização se o backup de inicialização ou a criação do snapshot falhar.

Quando a atualização termina, falha ou é recusada, o fluxo cria o snapshot posterior correspondente; sua descrição registra o resultado ("after package upgrade", "after failed package upgrade"). Se o processo for encerrado antes disso, a próxima Atualização do sistema fecha primeiro o snapshot anterior pendente com um posterior descrito como "after interrupted package upgrade". Uma atualização com falha preserva o snapshot anterior e os arquivos de inicialização em qualquer caso. Atualizações de Flatpaks, runtimes SDKMAN/NVM e arquivos em subvolumes pessoais separados não são protegidos por esses snapshots. Atualizações avançadas e comandos diretos do pacman/yay intencionalmente não criam snapshots automáticos. Para adotar essa política, remova os hooks antigos de snapshots do Eitr caso os tenha instalado manualmente.

Novas configurações do Snapper mantêm até 10 snapshots numerados comuns e 5 importantes pelo temporizador de limpeza. As políticas existentes são preservadas. A cada Atualização do sistema, os arquivos de inicialização são reduzidos aos 10 mais recentes, seguindo o limite padrão de snapshots. Um arquivo pode sobreviver ao snapshot se o Snapper o excluir primeiro: confira se o snapshot existe antes de restaurá-lo. Um disco cheio impede atualizações em vez de ignorar a proteção.

## Proteção de inicialização

Após uma Atualização do sistema bem-sucedida no layout da instalação guiada do Eitr, a proteção de inicialização mantém pronto o snapshot anterior à atualização (`/var/lib/eitr/boot-guard.json`). `eitr-boot-guard.service` conta cada tentativa no início da inicialização; `eitr-boot-guard-healthy.service` considera a tentativa bem-sucedida após a tela de login permanecer aberta por 45 segundos, desarmando a proteção.

Se duas inicializações consecutivas após a atualização não chegarem a esse ponto, a terceira restaura automaticamente, seguindo as etapas testadas da redefinição de fábrica:

1. Os arquivos de inicialização do snapshot (`/var/lib/eitr/boot-backups/<number>/boot.tar`) são copiados para a partição EFI após guardar os atuais para poder restaurá-los.
2. O subvolume raiz com falha é renomeado para `@eitr-guard-failed`; uma cópia gravável do snapshot se torna `@`, e o armazenamento `.snapshots` do Snapper é movido para ela.
3. O computador reinicia no sistema restaurado. Se qualquer etapa falhar, os subvolumes e os arquivos de inicialização voltam ao estado anterior, e não ocorre reinicialização.

O sistema restaurado exclui `@eitr-guard-failed` ao chegar à tela de login, e o próximo login mostra uma notificação. As pastas pessoais não são alteradas. A proteção não pode ajudar se o próprio kernel não iniciar; nesse caso, inicialize pelo snapshot da atualização no menu de inicialização (abaixo). Outros layouts de disco nunca recebem essa proteção.

## Alterações na autenticação

Segurança → ativar impressão digital/FIDO2 salva cópias de `/etc/pam.d/hyprlock`, `sddm` e `sudo` em `/var/lib/eitr/pam-backups/<timestamp>/` antes de editá-los e restaura os três se alguma gravação falhar. A impressão digital é adicionada aos três, então o modo "somente senha" também vale para a tela de bloqueio; pam_fprintd pode atrasar a solicitação de senha por até 10 segundos. Para retornar a uma política anterior usando um shell root funcional ou um TTY:

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## Desbloqueio do disco por TPM

Segurança → Desbloqueio do disco por TPM pode adicionar um slot de chave TPM2 a uma raiz LUKS2 para desbloquear o disco na inicialização sem digitar a senha. Nada disso é executado pelo instalador. O auxiliar root (`luks-tpm-check`, `luks-recovery-key`, `luks-tpm-enroll`, `luks-tpm-remove`) recusa a operação, a menos que o dispositivo seja LUKS2, um dispositivo TPM2 apareça em `systemd-cryptenroll --tpm2-device=list` e já exista um slot de senha ou recuperação. Ele somente **adiciona** um slot; a senha permanece.

- **Primeiro, a chave de recuperação.** O fluxo do Walker oferece `systemd-cryptenroll --recovery-key`; a chave é exibida uma única vez no terminal e nunca é armazenada. Anote-a offline. Ela funciona na solicitação normal de senha.
- **Escolha do PCR.** O Eitr vincula o desbloqueio ao PCR 7 (estado e chaves do Secure Boot). Atualizações do firmware raramente o alteram, mas trocar uma chave do Secure Boot o altera. O PCR 7 só oferece proteção significativa com o Secure Boot ativado usando suas próprias chaves (veja [SECURE-BOOT.md](SECURE-BOOT.md)); caso contrário, qualquer pessoa pode inicializar o computador com uma linha de comando do kernel modificada e obter o disco desbloqueado. Para maior proteção, faça o cadastro manualmente com um PIN: `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`.
- **Initramfs.** O hook `encrypt` do busybox não usa tokens TPM2, então o cadastro é recusado enquanto ele estiver configurado. Trocar para `systemd` e `sd-encrypt` em `HOOKS` (substituindo `cryptdevice=` por `rd.luks.name=<LUKS-UUID>=root` na linha de comando do kernel, ou usando `/etc/crypttab.initramfs`) é uma alteração crítica de inicialização que o Eitr deixa sob sua responsabilidade. Faça a alteração, execute `sudo mkinitcpio -P`, atualize a entrada de inicialização e confirme que uma inicialização com senha funciona **antes** de cadastrar o TPM.

Se o TPM parar de desbloquear (mudança no firmware ou no Secure Boot, ou redefinição do TPM), a solicitação de senha aparece como antes. Digite-a, remova o cadastro e faça-o novamente. Para desfazer completamente, use a opção de remover o desbloqueio por TPM ou, em qualquer shell funcional:

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## Redefinição de fábrica

Computadores instalados com a ISO do Eitr também mantêm um ponto de restauração somente leitura do primeiro login, fora do Snapper. Walker → Sistema → Manutenção → Redefinição de fábrica retorna a esse ponto, com ou sem os arquivos das pastas pessoais; veja [FACTORY-RESET.md](FACTORY-RESET.md).

## Inspecionar pontos de recuperação

Use Walker → Sistema → Manutenção → Instantâneos ou execute estas verificações somente leitura:

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

Se o desktop falhar, mas o sistema ainda iniciar, mude para um console de texto ou use uma conexão SSH que você mesmo configurou. Se o sistema não iniciar, use a ISO oficial do instalador do Arch e monte o sistema de arquivos Btrfs. Identifique o disco, o mapeamento de criptografia, o subvolume raiz, o número do snapshot e a montagem EFI corretos antes de alterar qualquer coisa. Não copie comandos de outro computador sem conferir.

## Snapshots da pasta pessoal

Desativados por padrão. **Sistema > Manutenção > Instantâneos > Snapshots da pasta pessoal** os ativa (pedindo confirmação; desativá-los os exclui). A configuração `home` do Snapper mantém então um snapshot de `/home` por hora durante um dia e um por dia durante uma semana, excluindo os mais antigos quando o espaço livre cai abaixo de 20%.

Caches, `~/Downloads`, pastas de discos de VMs (`~/.local/share/libvirt/images`, GNOME Boxes, `~/VirtualBox VMs`) e a biblioteca do Steam ficam de fora: na próxima inicialização, antes de qualquer login, `eitr-home-exclusions.service` os transforma em subvolumes Btrfs aninhados, que os snapshots pessoais não incluem. Seus arquivos são preservados com reflinks, sem espaço adicional para a movimentação. O modo Manter os Meus Arquivos da redefinição de fábrica leva esses subvolumes para a pasta pessoal restaurada: os ocultos vão para "Settings before reset", e os caches são descartados. Se algum não puder ser movido, a pasta pessoal anterior será preservada para análise, em vez de excluída.

**Instantâneos > Restaurar um arquivo ou pasta** (ou `eitr restore PATH`) lista os snapshots que contêm o caminho e copia a versão escolhida ao lado da atual como `NAME (restored DATE)`, ou para o local original se tiver sido excluída. Nada é sobrescrito.

## O que cada atualização mudou

Antes de reverter, confira o que seria desfeito. **Sistema > Manutenção > Instantâneos > O que cada atualização mudou** (ou `eitr snapshots changes`) lista cada par anterior/posterior de atualização, com as quantidades de pacotes atualizados, rebaixados, instalados e removidos. `eitr snapshots changes <before number>` lista todos os pacotes de uma atualização com as versões anterior e nova. A comparação usa os bancos de dados de pacotes dentro dos dois snapshots; se ainda não houver snapshot posterior, compara com o sistema em execução.

## Inicializar por um snapshot antigo

Com GRUB ou Limine, o menu de inicialização pode listar snapshots somente leitura do Snapper para inspecionar e reverter uma atualização com falha sem mídia externa. O instalador só oferece isso após você digitar `yes`; em uma instalação existente, execute `bash distro/bootloader/setup.sh` (`--check` apenas informa o estado). Confira em Walker → Sistema → Manutenção → Instantâneos → estado dos snapshots inicializáveis ou com `sudo /usr/lib/eitr/eitr-system snapshots-boot-status`.

| Carregador de inicialização | Integração | Pacotes (`distro/bootloader/`) |
|---|---|---|
| GRUB | `grub-btrfsd.service` recria o submenu "Arch Linux snapshots" quando o Snapper adiciona ou remove um snapshot | `grub-btrfs`, `inotify-tools` (oficiais) |
| Limine | `limine-snapper-sync.service` adiciona entradas de snapshots em `limine.conf` | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **Sem suporte.** Carrega apenas kernels da partição EFI/XBOOTLDR e não abre snapshots Btrfs | Use o procedimento com mídia externa abaixo |

A detecção lê os arquivos do GRUB, Limine e systemd-boot em `/boot`, `/efi` e `/boot/efi`. Se mais de um carregador estiver configurado (por exemplo, arquivos antigos do systemd-boot junto ao GRUB), a configuração recusa a operação em vez de adivinhar; remova os arquivos obsoletos ou configure as entradas manualmente. Primeiro, ela copia `grub.cfg`/`limine.conf` para `/var/lib/eitr/boot-config-backups/<timestamp>/` e habilita o serviço para a próxima inicialização:

- **GRUB:** a configuração executa `grub-mkconfig -o /boot/grub/grub.cfg` uma vez. Se `/boot` for uma partição separada, as entradas de snapshots inicializam o kernel *atual*; após atualizar o kernel, restaure também o arquivo de inicialização correspondente (abaixo).
- **Limine:** `limine-snapper-sync` gerencia as entradas criadas por `limine-entry-tool` (do `limine-mkinitcpio-hook`) e mantém cópias do kernel de cada snapshot na partição EFI; ela precisa ter espaço (o projeto recomenda 4 GiB). Revise `/etc/default/limine` (`SNAPPER_CONFIG_NAME="root"` e `ESP_PATH`, se não detectado), execute `sudo limine-update`, confira o menu e execute `sudo systemctl start limine-snapper-sync.service`. O Eitr não executa `limine-update` por você, pois isso reescreve o menu de inicialização.

Para desfazer, desative o serviço e restaure a cópia de segurança, por exemplo com `sudo systemctl disable grub-btrfsd.service` e `sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`.

### Snapshots somente leitura

Snapshots do Snapper são somente leitura. Um snapshot inicializado diretamente não pode gravar em `/var`, então o SDDM e outros serviços podem falhar; entre em um console de texto (Ctrl+Alt+F3) se o login gráfico não iniciar. Uma camada de sobreposição no initramfs permite gravar no snapshot em RAM (as alterações desaparecem ao reiniciar). O Eitr não edita `HOOKS`: adicione a camada, regenere e lembre que somente snapshots criados depois conterão o hook:

- GRUB: acrescente `grub-btrfs-overlayfs` a `HOOKS=(...)` em `/etc/mkinitcpio.conf` e execute `sudo mkinitcpio -P`.
- Limine: adicione `btrfs-overlayfs` após `filesystems` (ou `sd-btrfs-overlayfs` com hooks do systemd) e execute `sudo limine-update`.

### Reverter definitivamente

1. Escolha o snapshot "before package upgrade" mais recente na lista do menu de inicialização e confirme que o sistema funciona nele.
2. **Limine:** execute `sudo limine-snapper-restore` e escolha o snapshot. Ele restaura com o `RESTORE_METHOD` configurado e adiciona uma entrada de segurança para o sistema substituído, permitindo desfazer a própria restauração pelo menu de inicialização.
3. **GRUB:** `snapper rollback` só funciona quando a raiz é montada pelo subvolume padrão do Btrfs. Layouts do Arch costumam usar `rootflags=subvol=@` (confira `findmnt -no OPTIONS /` e `/etc/fstab`), então o rollback não teria efeito. Substitua o subvolume raiz usando mídia externa após inspecionar os subvolumes no nível superior do sistema de arquivos. O exemplo a seguir serve **somente** para a instalação guiada do Eitr, em que o Snapper criou o subvolume aninhado `@/.snapshots`; outros layouts exigem seus caminhos reais:

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   Se algum comando falhar, pare e inspecione; não exclua a raiz preservada. Verifique se o armazenamento de snapshots está presente na raiz restaurada e revise seu fstab antes de prosseguir. Se `/boot` for separado, restaure o arquivo correspondente de `/var/lib/eitr/boot-backups/<number>/`, reinicie pela entrada normal, execute `sudo grub-mkconfig -o /boot/grub/grub.cfg` e só exclua `@.broken` com `sudo btrfs subvolume delete` depois de verificar o sistema restaurado.

## Restaurar com segurança usando mídia externa

1. Salve os arquivos mais recentes de que precisar. Monte o nível superior do sistema de arquivos Btrfs e inspecione seus subvolumes; localize o subvolume `snapshot` do ponto escolhido. Os caminhos dependem de onde `.snapshots` está montado.
2. Preserve o subvolume raiz com falha renomeando-o. Crie um **snapshot Btrfs gravável** do ponto de recuperação escolhido no caminho original da raiz, de acordo com os rootflags e o fstab do carregador instalado.
3. Monte essa raiz restaurada e suas partições reais de inicialização/EFI. Restaure os arquivos de inicialização correspondentes se kernel, initramfs ou carregador tiverem mudado. Eles devem corresponder ao snapshot raiz escolhido; nunca misture um kernel mais novo com módulos antigos.
4. Revise o fstab e a configuração do carregador; regenere o initramfs ou repare entradas com `arch-chroot` conforme a necessidade desse computador. Reinicie somente quando a raiz e os arquivos de inicialização forem compatíveis.

Este procedimento manual considera o layout do disco; **não é uma implementação de reversão com um clique já verificada**. O comando `rollback` do Snapper sozinho não basta para layouts arbitrários de subvolumes e carregadores do Arch. As entradas de snapshots do GRUB e do Limine descritas acima ainda exigem validação em hardware real antes de afirmar que oferecem recuperação automática.

Referências: [grub-btrfs](https://github.com/Antynea/grub-btrfs), [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync), [conceitos de recuperação do Snapper](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html), [guia de instalação do Arch](https://wiki.archlinux.org/title/Installation_guide).
