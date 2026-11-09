# Segurança e bloqueio

**SUPER + M** bloqueia a tela imediatamente. Clique no ícone de Bloqueio automático à esquerda da barra (depois de Uso de IA) para ligar ou desligar o bloqueio por inatividade; a dica mostra o estado. Ligado, a tela bloqueia após 15 minutos de inatividade, desliga após 30 e o computador suspende após 60. A Central de controle oferece o mesmo controle e um botão Bloquear.

Vinte segundos antes do bloqueio, as telas compatíveis reduzem o brilho para cerca de 30% do nível anterior (nunca zero). Qualquer atividade restaura exatamente o nível anterior, mesmo após o bloqueio; desativar o bloqueio automático também o restaura. Monitores externos sem controle de brilho DDC são ignorados.

## Senha e autenticação alternativa

**Configurações > Usuários > Alterar senha** altera a senha da conta e mantém o chaveiro de login abrindo com ela. Impressão digital e Chave de segurança FIDO2 têm etapas próprias de cadastro e ativação. Uma chave de segurança FIDO2 é um dispositivo físico, não o leitor de impressão digital do notebook. Cadastre primeiro e depois ative a autenticação. O auxiliar faz backup das configurações do PAM; mantenha uma senha que funcione e uma forma de acessar um TTY.

Voltar à autenticação por senha restaura o acesso somente por senha. As mudanças afetam os serviços PAM compatíveis de bloqueio, login e sudo; exigem hardware compatível e os auxiliares instalados. A autenticação por impressão digital pode atrasar brevemente a solicitação de senha. Ler esta página não altera o PAM.

## Firewall

Novas instalações começam com o firewall ativo. Ele recusa conexões de entrada, exceto respostas a conexões iniciadas pelo computador, descoberta de nomes locais e os aplicativos de compartilhamento instalados pelo Eitr: KDE Connect (portas 1714-1764) e LocalSend (53317). Máquinas virtuais e contêineres no computador continuam podendo acessá-lo, e o tráfego de saída nunca é filtrado. Se o SSH estiver ativo, ele também continua acessível.

**Configurações > Segurança > Proteção > Firewall** mostra o estado e permite alterá-lo após confirmação. Computadores configurados antes da existência do firewall começam com ele desativado. Para permitir conexões em outro aplicativo, adicione um arquivo em `/etc/eitr/firewall.d/`, como `game.nft`, contendo:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

Depois, desligue o firewall e ligue-o novamente.

## Criptografia de disco e TPM

A criptografia do disco é uma escolha do instalador. Desbloqueio do disco por TPM pode adicionar um slot TPM2 a uma raiz LUKS2 existente e compatível; o instalador não faz esse cadastro automaticamente. Guarde a senha/chave de recuperação offline, nunca em capturas de tela ou arquivos do repositório. Mudanças no firmware ou no Secure Boot podem exigir a senha no próximo boot.

Leia [Recuperação e snapshots](handbook:recovery) antes de alterar a autenticação ou o TPM. [Secure Boot](handbook:secure-boot) é um procedimento manual avançado: o EITR não cadastra chaves no firmware nem assina arquivos de boot por você. Um erro pode impedir o boot e, em alguns equipamentos, até o acesso à configuração do firmware.

## Contas de usuário

**Configurações > Usuários > Criar usuário…** cria um acesso separado. Informe o nome de usuário, nome completo opcional, tipo de conta e senha; revise os dados e pressione Enter para criar. Esc cancela antes de aplicar. Contas padrão não podem usar sudo; administradores entram no grupo wheel e recebem uma regra sudo protegida por senha.

A nova pasta pessoal não contém arquivos da sua conta. No primeiro login no Hyprland pelo UWSM, o Eitr executa a configuração de desktop por usuário do instalador e adota a estrutura do pacote com a identidade do novo usuário. A configuração do shell pode precisar de internet. Se falhar, o marcador permanece para o próximo login; após o sucesso, não se repete. Falhas na criação deixam a conta incompleta bloqueada e expirada para revisão manual.

Administradores veem as abas **Usuários** e **Gerenciar** em Configurações > Usuários; contas padrão veem apenas a lista de usuários. Um Administrador pertence ao grupo wheel e tem uma regra sudo do Eitr; uma conta Padrão não tem nenhum dos dois. Gerenciar permite criar contas, mudar seu tipo, definir a senha de outra conta e remover contas. Cada ação abre uma folha de confirmação e depois um terminal de tarefa: Enter continua e Esc cancela. A redefinição pede a nova senha duas vezes no terminal; o chaveiro de login da outra conta não pode ser atualizado e mantém a senha antiga. Para sua própria conta, use Alterar senha em Usuários. A remoção mantém a pasta pessoal por padrão; escolha Excluir pasta pessoal para apagar seus arquivos. Você não pode remover sua própria conta, uma conta com sessão ativa ou o último administrador; este também não pode ser rebaixado. Apenas contas humanas (UID 1000–65533) podem ser gerenciadas. A lista é atualizada quando você retorna do terminal.

Contas cujo grupo principal é wheel não podem ser rebaixadas aqui; altere primeiro o grupo principal pela administração manual.

## Fotos de perfil

Configurações > Usuários lista cada conta deste PC. Clique ali na sua foto para alterá-la, ou use o ícone de lixeira abaixo dela para removê-la. Veja [Configurações](handbook:system) para escolher uma imagem e ajustar o recorte. A Central de controle apenas exibe a foto.
