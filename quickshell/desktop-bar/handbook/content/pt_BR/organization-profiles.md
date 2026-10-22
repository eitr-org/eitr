# Perfis de organização

Use a ISO oficial sem alterações. Em um pendrive FAT32 chamado `EITRANSWERS`, coloque `eitr-profile.json` ao lado ou no lugar de `eitr-answers.json`. Apenas o perfil mantém o assistente normal, com todas as mudanças na revisão. Com ambos, o instalador mostra a operação no disco e o perfil antes da contagem de 15 segundos. Ctrl+C cancela antes de alterar o disco. Mantenha o pendrive conectado até desligar.

Exemplo completo: substitua os hashes de exemplo pelos valores reais de `sha256sum` e copie os arquivos indicados para o pendrive.

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Somente `version` e `name` são obrigatórios. Chaves desconhecidas ou duplicadas são recusadas. Remova seções opcionais desnecessárias. Os caminhos são relativos ao pendrive: caminhos absolutos, links simbólicos e `..` são proibidos. Todos os arquivos precisam existir e corresponder ao SHA-256 em minúsculas antes de qualquer mudança no disco. O papel de parede deve ser PNG, JPEG ou WebP válido. A chave deve conter exatamente uma chave pública OpenPGP. O servidor exige HTTPS sem credenciais. A chave é importada e assinada localmente pelo pacman: use somente uma chave confiável. Pacotes e scripts são código administrativo confiável, sem isolamento.

`remove` aceita somente a lista revisada `distro/removable-apps.json`; a revisão de cada pacote está em `distro/PROFILE-PACKAGE-REVIEW.md`. Pacotes protegidos ou desconhecidos recusam o perfil inteiro. O pacman verifica dependências, sem remoção recursiva nem ignorar dependências. Políticas de grupo excluem os pacotes permitidos do grupo: `gaming`, `media`, `development`, `sharing`, `remote_access`. `false` desativa; `true` permite. A política `update_channel` aceita somente `"stable"`. Políticas omitidas não restringem.

`plugins` aceita `false`, que esconde Instalar > Plugins e Ferramentas > Plugins e recusa adicionar, atualizar e iniciar plugins, ou `{"allow": ["https://git.example.org/team/tools.git", "git@github.com:team/plugin.git"]}`, que permite apenas esses repositórios. As entradas da lista permitida são URLs HTTPS ou SSH e coincidem independentemente de esquema, usuário, porta, sufixo `.git`, barra final e maiúsculas; um alias de host SSH de `~/.ssh/config` deve ser listado como é escrito. Aplicar essa política em uma máquina instalada para e desativa os serviços dos plugins que ela não permite mais e mantém seus arquivos.

Receitas usam `group/name` de `distro/software.json`. Só receitas pacman e Flatpak pré-compiladas são aceitas. AUR, instaladores interativos e aplicações web são recusados; forneça pacotes pré-compilados no pendrive. Pacotes de repositório, receitas e Flathub precisam de internet. Arquivos de pacote funcionam offline se as dependências estiverem na ISO ou no pendrive. Os nomes precisam existir nos bancos atuais do pacman; atualize pelo processo normal antes de validar adições online. Não há compilação AUR. Adições pacman online fazem atualização completa. O repositório extra serve às próximas atualizações; forneça no pendrive os pacotes exclusivos dele.

Durante a instalação, os aplicativos Flathub e as receitas Flatpak ficam na fila para o usuário do desktop e são instalados na primeira inicialização com conexão à internet. Instalações que falham são tentadas novamente na próxima inicialização. Aplicar um perfil em uma máquina já instalada instala esses aplicativos diretamente.

Navegadores: Firefox e Chromium; adicione Chromium explicitamente. Tema e papel de parede são salvos para o próximo login do usuário selecionado, sem reiniciar a sessão. Canal e repositório são globais. `setup` roda como root ao final, no diretório privado do pendrive copiado, depois de registrar o perfil. Um marcador SHA-256 registra a tentativa antes de iniciar: falhas ou interrupções não provocam repetição silenciosa. Altere o script e o hash para autorizar outra tentativa. Falhas permanecem visíveis; transações concluídas não são revertidas.

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check` lê arquivos e metadados e usa diretórios temporários, sem alterar a configuração. `apply` usa `eitr-system profile-apply` como root, copia e revalida os arquivos, mostra o resumo e exige digitar `APPLY PROFILE`. Cancelar não altera nada. Remove com pacman, instala adições, salva padrões e grava `/etc/eitr/policies.json` (0644, root:root) e `/etc/eitr/profile.json`. Outro perfil substitui as escolhas registradas, sem reinstalar automaticamente remoções anteriores nem redefinir preferências omitidas. Os marcadores de setup permanecem.

As exclusões filtram os manifestos do instalador e um `IgnorePkg` nas opções do pacman impede reinstalação por dependência durante System Update; um conflito deve interromper a atualização. A criação das configurações do usuário não instala aplicativos. Políticas escondem menus e busca do Elephant, controles de Acesso Remoto na barra, colaboração de assistentes e troca de canal. As ferramentas também recusam chamadas diretas. Menus e painéis podem precisar de atualização para refletir novas políticas.

**Isto não bloqueia um usuário com root.** Root pode editar políticas e usar outras ferramentas. Um bloqueio real também exige não conceder root. Não é gerenciamento de frota. Instalações com e sem rede, um perfil recusado, a aplicação em uma máquina instalada, as atualizações, os controles ocultos e as telas do instalador em cada idioma passaram em uma VM (`distro/PROFILE-VM-TESTING.md`).
