# Acesso remoto

Status detalhado abre um terminal de diagnóstico que permanece aberto até você pressionar Esc.

Abra System > Connectivity > Acesso remoto. O compartilhamento fica desligado até
você ativá-lo. Esta etapa controla a sessão do Eitr já iniciada e acordada. Uso sem
monitor, acesso antes do login e wake on LAN ficam para depois. Se este computador
bloquear durante o compartilhamento, a tela remota mostra a tela de bloqueio:
quem estiver conectado a vê e pode digitar a senha. Pare o compartilhamento antes
de se ausentar quando a privacidade for importante.

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
ACL originais e remove as permissões de captura. Se a configuração carregou uinput, a restauração também o descarrega. Se outro
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
sobrevivem à reinicialização. Depois do primeiro início, Iniciar e Parar compartilhamento mudam na hora, sem perguntas nem senha. Iniciar ao entrar é opcional e muda na hora pelo painel Streaming ou pelo menu;
Desativar início ao entrar mantém o início manual. Estado do compartilhamento mostra erros.

Na primeira vez, a transmissão fica bloqueada enquanto você define a senha. Volte ao terminal e confirme a definição; sua senha de administrador então libera o controle remoto.

Uma atualização do pacote Sunshine remove a capacidade de captura do executável.
Se o compartilhamento não iniciar depois, use Configurar compartilhamento novamente
e confirme a permissão; o registro original de restauração é preservado.

O Sunshine usa a capacidade KMS apenas como root ou pela conta que configurou o compartilhamento: a configuração define `root:eitr-sharing`, modo `0750`, e adiciona sua conta ao grupo do sistema. Saia e entre novamente antes de iniciar o compartilhamento para atualizar os grupos do serviço de usuário. A configuração mantém o processo em execução; reiniciá-lo antes de entrar novamente pode falhar. Parar mantém as permissões. Restaurar remove a associação ao grupo e todas as capacidades do executável, retornando a `root:root`, modo `0755`, inclusive para registros antigos. Após uma atualização do pacote, Configurar compartilhamento corrige proprietário e modo antes de conceder novamente a capacidade.

## Moonlight no Mac

Instale pelo [projeto Moonlight](https://moonlight-stream.org/). Para o primeiro
teste, coloque os dois computadores na mesma rede. Adicione o endereço LAN do Eitr
manualmente se necessário. Selecione o PC, leia o PIN e use Parear um dispositivo no Eitr.
Escolha Desktop para controlar aplicativos e jogos. Selecione a tela nas
configurações do Sunshine e verifique cada monitor. Gaming > Moonlight e Connect
to another PC instalam ou abrem o cliente no Eitr para a direção inversa. Instalações novas incluem esses aplicativos; o compartilhamento permanece
desativado até você ativá-lo explicitamente.

Atalhos com SUPER a partir do Mac: nas configurações do Moonlight, ative **Capture system keyboard shortcuts** (em tela cheia ou sempre). Só assim o Moonlight envia a tecla Command do Mac como SUPER; caso contrário, os atalhos com Command ficam no Mac. Ctrl+Alt+Shift+K liga ou desliga a captura durante uma sessão.

## Tailscale nos dois computadores

Em Acessar fora de casa, escolha Configurar acesso fora de casa. Após instalar, o assistente
root confirmado ativa e inicia `tailscaled.service` e define seu usuário como
operador. Por isso entrar, conectar e desconectar não pedem senha. Um Tailscale configurado de outra forma pede a senha de administrador. Entrar abre no navegador a URL de
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

## O que foi testado

Os testes automatizados usam simulações. Em um desktop real (com um e depois dois
monitores) e um MacBook com Moonlight: configuração, iniciar o compartilhamento,
pareamento pelo endereço, imagem, teclado, mouse, áudio, a tela de bloqueio
(desbloqueada pelo Mac), início no login, Parar compartilhamento e Restaurar
configuração na rede de casa, e a configuração, o login e a conexão do Tailscale
fora de casa. Controles, outras placas de vídeo e outros clientes não foram
testados.
