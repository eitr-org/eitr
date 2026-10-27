# Segurança e bloqueio

**SUPER + M** bloqueia a tela imediatamente. Clique no ícone de Bloqueio automático à esquerda da barra (depois de Uso de IA) para ligar ou desligar o bloqueio por inatividade; a dica mostra o estado. Ligado, a tela bloqueia após 15 minutos de inatividade, desliga após 30 e o computador suspende após 60. A Central de controle oferece o mesmo controle e um botão Bloquear.

Vinte segundos antes do bloqueio, as telas compatíveis reduzem o brilho para cerca de 30% do nível anterior (nunca zero). Qualquer atividade restaura exatamente o nível anterior, mesmo após o bloqueio; desativar o bloqueio automático também o restaura. Monitores externos sem controle de brilho DDC são ignorados.

## Senha e autenticação alternativa

**Sistema > Segurança > Atualizar senha** altera a senha da conta. Impressão digital e FIDO2 têm etapas próprias de cadastro e ativação. Uma chave de segurança FIDO2 é um dispositivo físico, não o leitor de impressão digital do notebook. Cadastre primeiro e depois ative a autenticação. O auxiliar faz backup das configurações do PAM; mantenha uma senha que funcione e uma forma de acessar um TTY.

Voltar à autenticação por senha restaura o acesso somente por senha. As mudanças afetam os serviços PAM compatíveis de bloqueio, login e sudo; exigem hardware compatível e os auxiliares instalados. A autenticação por impressão digital pode atrasar brevemente a solicitação de senha. Ler esta página não altera o PAM.

## Firewall

Novas instalações começam com o firewall ativo. Ele recusa conexões de entrada, exceto respostas a conexões iniciadas pelo computador, descoberta de nomes locais e os aplicativos de compartilhamento instalados pelo Eitr: KDE Connect (portas 1714-1764) e LocalSend (53317). Máquinas virtuais e contêineres no computador continuam podendo acessá-lo, e o tráfego de saída nunca é filtrado. Se o SSH estiver ativo, ele também continua acessível.

**Sistema > Segurança > Firewall** mostra o estado e permite alterá-lo após confirmação. Computadores configurados antes da existência do firewall começam com ele desativado. Para permitir conexões em outro aplicativo, adicione um arquivo em `/etc/eitr/firewall.d/`, como `game.nft`, contendo:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

Depois, desligue o firewall e ligue-o novamente.

## Criptografia de disco e TPM

A criptografia do disco é uma escolha do instalador. Desbloqueio do disco por TPM pode adicionar um slot TPM2 a uma raiz LUKS2 existente e compatível; o instalador não faz esse cadastro automaticamente. Guarde a senha/chave de recuperação offline, nunca em capturas de tela ou arquivos do repositório. Mudanças no firmware ou no Secure Boot podem exigir a senha no próximo boot.

Leia [Recuperação e snapshots](handbook:recovery) antes de alterar a autenticação ou o TPM. [Secure Boot](handbook:secure-boot) é um procedimento manual avançado: o EITR não cadastra chaves no firmware nem assina arquivos de boot por você. Um erro pode impedir o boot e, em alguns equipamentos, até o acesso à configuração do firmware.
