# Contas Git

Abra **Desenvolvimento > Contas Git**. Você pode usar contas GitHub e GitLab simultaneamente, inclusive várias do mesmo provedor ou host empresarial. Novas instalações incluem GitHub CLI (`gh`) e GitLab CLI (`glab`); imagens ISO existentes precisam ser reconstruídas para incluir mudanças.

Cada conta mostra onde o Git a usa: **Padrão**, os nomes das pastas ou **Ainda não usada**. Enter abre suas ações; Shift+Backspace volta à lista.

## Primeira configuração

1. **Adicionar conta** abre um formulário com provedor, nome da conta, nome e e-mail do autor dos commits, host e uma chave SSH privada existente (lista as chaves em `~/.ssh`), ou nenhuma por enquanto. Depois pergunta se a conta será o padrão e qual pasta usa somente essa conta, mostra uma prévia e salva com Enter.
2. **Importar Configuração Existente** lê identidades configuradas manualmente: `user.name`/`user.email` padrão e regras por pasta `includeIf "gitdir:…"` em `~/.gitconfig` ou `~/.config/git/config`, incluindo alias SSH e a chave usados por um arquivo incluído (`url.<alias>.insteadOf`). Mostra o que encontrou e cria contas e regras correspondentes após confirmação. Seus arquivos permanecem intactos; padrões de pastas com curingas aparecem como ignorados.

## Padrão e pastas

A conta **padrão** vale nas pastas sem conta própria. Uma conta **de pasta** vale apenas nos repositórios daquela pasta. A pasta mais específica vence; configurações locais do repositório e opções da linha de comando ou do ambiente do Git ainda têm prioridade. O EITR preserva configurações globais e comentários existentes, acrescenta uma inclusão identificada ao fim de `~/.gitconfig`, e as regras confirmadas prevalecem sobre identidades de outras inclusões.

As ações do Walker pedem confirmação antes de salvar e mostram uma notificação: **Definir como padrão** ou **Deixar de usar como padrão**, **Adicionar pasta** (escolha `~/Development`, uma pasta dentro dela ou **Outra pasta…** para digitar um caminho) e **Remover pasta**. O Git considera o diretório `.git` real; worktrees vinculadas e submódulos podem seguir a conta de um repositório pai.

## Chaves SSH

A identidade dos commits não concede acesso ao repositório. **Mostrar chave pública** exibe a chave pública, copia-a e informa onde adicioná-la no provedor (GitHub: Settings > SSH keys). **Escolher chave SSH existente** escolhe uma chave de `~/.ssh`; **Criar chave SSH** cria uma Ed25519 com senha e mostra a chave pública. **Testar conexão** mostra a saudação do provedor, como "Hi username!", em uma notificação. Nunca compartilhe a chave privada.

As chaves valem apenas para o host SSH daquele provedor. O inicializador resolve aliases existentes sem se conectar e usa apenas a chave selecionada, ignorando outras configurações SSH dessa conexão. Conexões por proxy são recusadas; mantenha um `core.sshCommand` local ao repositório para configurações avançadas. A verificação de hosts conhecidos permanece ativa. Contas sem chave definida usam o SSH normal, nunca a chave de outra conta. Credenciais HTTPS e seus auxiliares permanecem intactos.

## CLIs dos provedores

**Entrar na CLI** entra em um diretório de configuração separado para cada conta, sem trocar a conta global normal do `gh` ou `glab`. Variáveis de tokens herdadas são removidas nesse processo. A confirmação informa que os tokens ficam em arquivos de perfil privados e não criptografados, evitando entradas de chaveiro compartilhadas entre contas do mesmo host. Nunca compartilhe `~/.config/eitr/git-accounts/cli`; essa pasta não entra nos backups do EITR.

Dentro de um repositório, use a CLI que seleciona a conta correta:

```sh
eitr-git cli auth status
eitr-git cli repo view
```

A conta padrão ou da pasta escolhe `gh` ou `glab`. Os comandos normais dessas CLIs mantêm seu comportamento global. Cadastrar a chave SSH não autentica operações da API da CLI. Nenhuma CLI do Bitbucket é incluída.

## Remoção e recuperação

**Editar nome e e-mail** altera os campos de identidade; **Remover conta** remove a conta e suas regras após confirmação. Remover uma regra de pasta volta à regra mais abrangente ou ao padrão; retirar o padrão restaura as configurações anteriores do Git fora das regras restantes. Projetos, chaves e credenciais das CLIs nunca são excluídos; remover uma regra não revoga acesso no provedor.

As configurações versionadas ficam em `~/.config/eitr/git-accounts.json`. A cada alteração aplicada, é salva uma cópia do arquivo global do Git, da inclusão ativa e das configurações em `~/.local/state/eitr/git-account-backups/<id>`, com permissões privadas. `manifest.json` registra caminhos originais, nomes dos backups e permissões. Chaves e tokens de CLI nunca são copiados. Para recuperar manualmente, confira o manifesto e preserve alterações feitas desde o backup antes de restaurar. Blocos de inclusão do EITR editados ou inválidos são recusados, não substituídos silenciosamente.

Referências: [inclusões condicionais do Git](https://git-scm.com/docs/git-config), [perfis da GitHub CLI](https://cli.github.com/manual/gh_help_environment), [perfis da GitLab CLI](https://docs.gitlab.com/cli/configuration/).
