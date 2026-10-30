# WiFi, Bluetooth e modo avião

Abra pelos ícones da barra ou por **Configurações > Conectividade**. Abrir um painel nunca troca o serviço de rede nem desconecta um dispositivo por conta própria.

## WiFi

O painel separa redes conectadas, conhecidas e outras redes. Escolha uma disponível para conectar; os campos de senha ocultam o conteúdo. Redes salvas e indisponíveis continuam visíveis, sem percentual de sinal inventado. Desconectar fica na linha conectada; esquecer uma rede salva exige confirmação.

A parte superior mostra estado da rede, ping, banda WiFi, endereço IP e gateway. O compartilhamento por QR usa uma senha WiFi fornecida e mantém a imagem gerada na memória. Credenciais corporativas não são compartilhadas como QR de rede pessoal.

Redes corporativas aceitam PEAP/MSCHAPv2 e TTLS/PAP. Peça ao administrador usuário, certificado da autoridade certificadora e domínio do servidor de autenticação; não desative a validação do certificado. Outros métodos exigem configuração avançada. Veja [Serviços de rede](handbook:network-backends).

## Bluetooth

Ative ou desative o adaptador, procure, pareie, conecte, desconecte ou esqueça dispositivos. Conectados, conhecidos e recém-descobertos ficam em grupos separados. A busca iniciada pelo painel para após 20 segundos ou ao fechar o painel.

O pareamento pode exigir PIN ou um agente de confirmação. O desktop atual usa o agente Blueman para esses diálogos; reconectar um dispositivo já pareado não comprova suporte a novos pareamentos. Mantenha o agente até testar um pareamento com PIN ou confirmação. A cobertura do agente em instalações novas ainda precisa ser verificada.

## Modo avião

Central de controle > Geral bloqueia WiFi e Bluetooth com rfkill. Desativar o modo restaura apenas as rádios que ele próprio bloqueou. Bloqueios físicos ou aplicados externamente não são ignorados silenciosamente. Ative uma rádio individualmente se necessário.

## VPN

Abra Install > VPN para Tailscale, WireGuard ou NetworkManager VPN. O Tailscale mantém seu painel de acesso remoto e seu fluxo de configuração.

WireGuard instala o pacote oficial `wireguard-tools` pela verificação habitual de atualizações pendentes. Importe uma configuração informando o nome e o caminho completo de um arquivo `.conf`; revise nome, endpoints e quantidade de peers. Chaves nunca são exibidas. Hooks executáveis e SaveConfig são recusados. Com NetworkManager o perfil é importado nele; com iwd é salvo de forma privada em `/etc/wireguard` para wg-quick, sem sobrescrever perfis existentes.

NetworkManager VPN instala `networkmanager-openvpn` e `networkmanager-openconnect`. O NetworkManager já inclui WireGuard sem plugin separado. Com iwd o fluxo explica o requisito e abre a escolha existente de backend, sem alterá-lo. Veja [Serviços de rede](handbook:network-backends). A importação aceita `.ovpn` para OpenVPN e arquivos compatíveis com o importador OpenConnect. Erros não exibem o conteúdo.

Perfis ficam desconectados, salvo escolha explícita de conectar após importar. A conexão automática na inicialização fica desativada. Reabra o menu para conectar ou desconectar pelo nome salvo. Nenhum controle VPN é adicionado à Central de Controle. Testes usam simulações; conexões reais não foram verificadas em hardware.
