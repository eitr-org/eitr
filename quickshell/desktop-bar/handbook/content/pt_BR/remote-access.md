# Acesso remoto

Abra System > Connectivity > Acesso remoto. O compartilhamento fica desligado até
você ativá-lo. Esta etapa controla a sessão do Eitr já iniciada e acordada. Uso sem
monitor, acesso antes do login e wake on LAN ficam para depois. O comportamento
com a tela bloqueada ainda precisa de validação; pare o compartilhamento antes de
bloquear quando a privacidade for importante.

## Sunshine no Eitr

Em Compartilhar este PC, escolha Configurar compartilhamento. O pacote nativo assinado do Eitr é
compilado das fontes oficiais pelo responsável pela versão, sem compilação AUR no
primeiro clique. Flatpak e AppImage não oferecem captura KMS. Suas configurações e
dispositivos pareados são preservados. Não execute outra instância simultaneamente.

Leia o aviso de controle total e digite `yes` apenas se aceitar captura KMS e entrada
virtual de teclado, mouse e controle. O estado original fica em
`/var/lib/eitr/remote-access`. A configuração adiciona uma regra udev para uinput,
carrega uinput na inicialização, concede acesso ao usuário e aplica
`cap_sys_admin+p` ao Sunshine. Restaurar configuração de compartilhamento restaura os arquivos, a
capacidade e a ACL originais. Se a configuração carregou uinput, a restauração também o descarrega. Se outro
aplicativo ainda o usa, a falha é informada e o registro é mantido para você
fechar o aplicativo e tentar novamente.

Iniciar compartilhamento pede confirmação e abre `https://localhost:47990`. Aceite o
certificado local autoassinado somente nesse endereço. Defina usuário e senha
forte antes de parear. Abrir configurações volta às configurações; Parear um dispositivo abre a
página do PIN. Digite somente o PIN exibido no seu Moonlight. O Eitr impõe
`upnp=off`. Não configure encaminhamento de portas no roteador.

TCP 47984, 47989 e 48010 e UDP 47998-48000 aceitam apenas sub-redes privadas da LAN
diretamente conectadas e `tailscale0`. TCP 47990 fica acessível somente neste PC,
mesmo se outra regra permitir acesso. As redes são identificadas a cada início;
pare e inicie novamente ao trocar de rede. Use apenas sua rede doméstica confiável.
Parar compartilhamento desativa também o início automático e fecha as portas, inclusive
conexões existentes. Falhas do serviço também fecham as portas; as aberturas não
sobrevivem à reinicialização. Iniciar ao entrar é opcional e pede confirmação separada;
Desativar início ao entrar mantém o início manual. Estado do compartilhamento mostra erros.

Na primeira vez, a transmissão fica bloqueada enquanto você define a senha. Volte ao terminal, confirme a definição e digite `yes` na confirmação do assistente root para liberar o controle remoto.

Uma atualização do pacote Sunshine remove a capacidade de captura do executável.
Se o compartilhamento não iniciar depois, use Configurar compartilhamento novamente
e confirme a permissão; o registro original de restauração é preservado.

## Moonlight no Mac

Instale pelo [projeto Moonlight](https://moonlight-stream.org/). Para o primeiro
teste, coloque os dois computadores na mesma rede. Adicione o endereço LAN do Eitr
manualmente se necessário. Selecione o PC, leia o PIN e use Parear um dispositivo no Eitr.
Escolha Desktop para controlar aplicativos e jogos. Selecione a tela nas
configurações do Sunshine e verifique cada monitor. Gaming > Moonlight e Connect
to another PC instalam ou abrem o cliente no Eitr para a direção inversa. A ISO
não inclui esses programas de transmissão.

## Tailscale nos dois computadores

Em Acessar fora de casa, escolha Configurar acesso fora de casa. Após instalar, o assistente
root confirmado ativa e inicia `tailscaled.service` e define seu usuário como
operador. As ações seguintes dispensam sudo. Entrar abre no navegador a URL de
`tailscale login`. Connect conecta; Disconnect desconecta sem apagar credenciais.
Estado da conexão mostra o endereço deste PC, sessão desconectada e conexões
diretas, retransmitidas ou ociosas. Testar conexão com outro dispositivo executa `tailscale ping` para um
par específico. A retransmissão pode aumentar a latência e reduzir a qualidade.

Instale [Tailscale no Mac](https://tailscale.com/download/mac), entre na mesma
tailnet e conecte os dois PCs. Adicione o endereço Tailscale do Eitr ao Moonlight e
pareie como antes. A política da tailnet deve permitir as portas de transmissão.
As configurações web do Sunshine continuam locais ao Eitr.

Restaurar configuração de acesso fora de casa restaura o operador e o estado original de inicialização
e execução do serviço; preserva conta e pacotes. Se já estava ativo, continua ativo.
Use Disconnect antes se quiser encerrar a conexão. Erros ficam visíveis no terminal;
corrija e repita a etapa. Nenhum pacote é removido implicitamente.

## Validação pendente

Os testes automatizados usam simulações. Com o proprietário, verifique captura
Hyprland/NVIDIA, teclado, mouse, áudio, controle, ambos os monitores, bloqueio e
início no login; depois, pareamento no MacBook e caminhos diretos/retransmitidos.
Testes aprovados não comprovam esse comportamento no hardware.
