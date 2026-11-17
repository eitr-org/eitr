# Backup e restauração

Leve suas configurações do desktop, pastas pessoais escolhidas e listas de aplicativos instalados para outro computador ou uma instalação limpa do Eitr em um único arquivo criptografado `.eitrbackup`.

Os snapshots de [Recuperação e snapshots](handbook:recovery) permanecem no mesmo disco para reverter atualizações. Backup e restauração cria um arquivo portátil compactado com `zstd` e criptografado com frase secreta `age` para guardar em disco externo ou na nuvem.

## Abrir Backup e restauração

- **Configurações**: pressione **SUPER + ,** e abra **Sistema > Backup e restauração**.
- **Walker**: pressione **SUPER + F** e escolha **Configurações > Sistema > Backup e restauração**.
- **Terminal**: execute `eitr backup` (ou `eitr-backup wizard`).

## Criar um backup

1. Escolha as categorias:
   - **Configurações do Eitr**: preferências do desktop, sobrescritas em `~/.config/eitr/overrides`, temas, papéis de parede e telas de bloqueio próprios.
   - **Configurações de apps**: pastas em `~/.config` fora do Eitr (sem perfis de navegador nem caches).
   - **Pastas pessoais**: pastas principais de `$HOME`, desmarcadas por padrão, além de **Adicionar pasta…** para subpastas em `$HOME`. Os tamanhos são calculados em segundo plano.
   - **Apps instalados**: listas de pacotes oficiais, AUR, Flatpak, plugins do Eitr e itens da Store fora da base do sistema.
   - **Ajustes da máquina**: desativado por padrão; sobrescritas locais de monitores e `hypr/local.lua` deste PC.
2. Revise ou desmarque pastas de aplicativos e apps individuais (com busca e agrupamento por origem).
3. Escolha o destino. Unidades externas aparecem antes de `~/Backups`. Salvar apenas no mesmo disco mostra aviso; falta de espaço livre recusa antes de gravar qualquer arquivo.
4. Digite a frase secreta duas vezes. Ela nunca vai para argumentos, variáveis de ambiente ou arquivos salvos.
5. Confira o resumo na tela **Revisar** e pressione **Enter** para gravar o arquivo atomicamente, ou **Esc** para cancelar sem alterar nada.

### O que fica de fora

- Perfis e caches de navegadores, arquivos de trava, sockets e temporários.
- Código do sistema, padrões e saídas geradas (reconstruídos após a restauração).
- Credenciais fora das preferências: chaves SSH e GPG, chaveiros, CLIs em nuvem (`~/.aws`, `~/.azure`, `~/.config/gcloud`, `~/.config/gh`) e segredos de Git ou Wi-Fi.

## Restaurar de um backup

1. Escolha um arquivo (unidades conectadas, `~/Backups`, último local ou caminho manual) e informe a frase secreta.
2. O Eitr lê primeiro `manifest.json` e permite desmarcar categorias, pastas ou apps antes de gravar qualquer coisa.
3. Confirme a **Revisar**. Arquivos substituídos são salvos antes com um registro em `~/.local/state/eitr/restore-backups/<id>/`.
4. Os apps são reinstalados em ordem: pacotes oficiais disponíveis em uma única transação do `pacman` (ausentes são ignorados e listados), pacotes AUR um por vez via `yay`, Flatpaks, e plugins do Eitr e itens da Store **sempre mediante aprovação normal de revisão**.
5. Temas e configurações geradas são reconstruídos preservando papéis de parede por monitor, e o Hyprland recarrega se estiver ativo.
6. Após restaurar, entre novamente nos navegadores, CLIs em nuvem (`gh`, `gcloud`, `aws`, `az`) e chaves SSH/GPG guardadas fora do backup.

## Desfazer uma restauração

```sh
eitr backup undo <id>
```

Encontre `<id>` em **Configurações > Sistema > Backup e restauração** ou com `eitr-backup status`. O undo devolve arquivos substituídos, remove arquivos adicionados e regenera o tema.

## Referência de CLI

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

As frases secretas são pedidas em `/dev/tty` sem eco ou passadas com `--passphrase-fd N`. Formatos de arquivo mais novos que a versão instalada falham com clareza sem tocar no sistema.
