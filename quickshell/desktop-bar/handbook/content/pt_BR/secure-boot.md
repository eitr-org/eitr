# Secure Boot com sbctl

O Eitr documenta o Secure Boot, mas **nunca cadastra chaves nem assina arquivos por você**. Um erro aqui pode impedir a inicialização ou deixar o computador sem imagem. Siga estas etapas manualmente, em um computador no qual você consiga acessar as configurações do firmware, com a senha do disco e as [instruções de recuperação](RECOVERY.md) à mão. Nada neste guia foi verificado no hardware de teste do Eitr ainda.

## Antes de começar

- Somente inicialização UEFI. Saiba como abrir as configurações do firmware (geralmente F2, Del ou F12) e defina uma senha de administrador do firmware; caso contrário, qualquer pessoa poderá desativar o Secure Boot novamente.
- Se o desbloqueio do disco por TPM estiver cadastrado, tenha a senha à mão: cadastrar chaves altera o PCR 7 do TPM, então a próxima inicialização pedirá a senha uma vez. Depois, cadastre o desbloqueio por TPM novamente (Segurança → desbloqueio do disco por TPM: remova e cadastre outra vez).
- Nas configurações do firmware, coloque o Secure Boot em **Setup Mode** (geralmente "Clear keys" ou "Reset to Setup Mode"). Não exclua chaves que você não consiga restaurar; a maioria dos firmwares oferece "Restore factory keys".

## Procedimento com sbctl

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s` salva o arquivo no banco de dados do sbctl; o hook do pacman do sbctl assina novamente os arquivos registrados após atualizações do kernel e do carregador de inicialização. Execute `sudo sbctl verify` após cada alteração; depois, ative o Secure Boot no firmware e reinicie. Faça uma cópia de segurança de `/var/lib/sbctl` offline e mantenha-a privada: ela contém as chaves de assinatura. Nunca a copie para este repositório.

## Riscos

- **Option ROMs e chaves do fabricante.** Placas de vídeo, unidades NVMe e placas de rede costumam executar firmware (Option ROMs) assinado pela autoridade certificadora UEFI da Microsoft. Cadastrar apenas suas próprias chaves, sem `-m`, pode fazer o firmware recusá-lo: o computador pode ficar sem imagem, sem disco de inicialização e, em alguns notebooks, sem acesso às configurações do firmware. Mantenha `-m`, a menos que saiba que o hardware não usa esse tipo de firmware. Como alternativa, `sbctl enroll-keys --tpm-eventlog` pode adicionar os hashes das Option ROMs usadas nesta inicialização, mas eles mudam com atualizações de hardware ou firmware.
- **Arquivos não assinados.** Todo binário EFI no caminho de inicialização precisa estar assinado com suas chaves. Esquecer um arquivo impede a inicialização; desative o Secure Boot no firmware para recuperar o acesso.
- **Inicialização dupla.** O Windows só continua inicializando com `-m`.

## Carregadores de inicialização e entradas de snapshots

- **GRUB:** reinstale com `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock` e assine o novo `grubx64.efi` e os kernels em `/boot`. Nessa configuração, o GRUB não verifica assinaturas dos kernels: as entradas de snapshots do grub-btrfs continuam inicializando, mas a proteção cobre o binário do GRUB, não cada kernel. Execute `grub-install` e `sbctl sign` novamente após atualizações do GRUB que alterem a imagem.
- **Limine:** assine o binário EFI do Limine (`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` ou o caminho em que estiver instalado). O Limine protege sua configuração e os kernels com hashes, em vez de assinaturas. Se cadastrar o hash da configuração no binário (`limine enroll-config`), será necessário cadastrá-lo e assiná-lo novamente a cada alteração em `limine.conf`, inclusive a cada nova entrada de snapshot criada pelo limine-snapper-sync. Antes de ativar o Secure Boot, confirme que as configurações de `limine-mkinitcpio-hook` fazem isso (ele usa sbctl quando instalado); caso contrário, a próxima sincronização de snapshots fará o carregador rejeitar o menu.
- **systemd-boot:** assine `systemd-bootx64.efi` e os kernels ou imagens de kernel unificadas que ele carrega. Ele não oferece suporte a entradas de inicialização de snapshots.
- Entradas de snapshots de kernels antigos também precisam passar pelas verificações do carregador. Após ativar o Secure Boot, inicialize por uma entrada de snapshot uma vez para confirmar que funciona antes de precisar dela.

## Como desfazer

1. Entre nas configurações do firmware e desative o Secure Boot, ou escolha "Restore factory keys" para restaurar o conjunto de chaves do fabricante. O sistema instalado continua inicializando com o Secure Boot desativado.
2. Se quiser, remova arquivos registrados no banco de dados do sbctl com `sudo sbctl remove-file <file>`; as assinaturas nos próprios arquivos são inofensivas.
3. Se o desbloqueio por TPM foi cadastrado com o Secure Boot ativado, o PCR 7 muda novamente: digite a senha uma vez e cadastre o desbloqueio outra vez.

Referências: [sbctl](https://github.com/Foxboron/sbctl), [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
