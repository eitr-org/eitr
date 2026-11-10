# WiFi, Bluetooth e modo avião

Abra Configurações > Conexões e escolha Wi-Fi ou Bluetooth. Os ícones da barra abrem painéis rápidos para os mesmos dispositivos. Abrir essas telas não troca o serviço de rede nem desconecta nada.

## Conectar ao Wi-Fi

Abra Configurações > Conexões > Wi-Fi, ative Wi-Fi e escolha uma rede em Outras redes. Digite a senha se for solicitada. Buscar procura novamente. Rede conectada mostra a conexão atual; Redes conhecidas mantém redes salvas, inclusive sem sinal. Desconectar encerra a conexão; Esquecer remove uma rede salva após confirmação. O progresso e os erros aparecem ao lado da rede.

A parte superior mostra estado da rede, ping, banda WiFi, endereço IP e gateway. O compartilhamento por QR usa uma senha WiFi fornecida e mantém a imagem gerada na memória. Credenciais corporativas não são compartilhadas como QR de rede pessoal.

Redes corporativas aceitam PEAP/MSCHAPv2 e TTLS/PAP. Peça ao administrador usuário, certificado da autoridade certificadora e domínio do servidor de autenticação; não desative a validação do certificado. Outros métodos exigem configuração avançada. Veja [Serviços de rede](handbook:network-backends).

Escolha o serviço WiFi em Configurações > Conexões > Wi-Fi > Backend WiFi; Walker > Configurações > Dispositivos > Conexões > Infraestrutura de rede é uma alternativa. Leia [Serviços de rede](handbook:network-backends) antes de trocar. A escolha vale após reiniciar e mantém a conexão atual.

## Parear um dispositivo Bluetooth

Abra Configurações > Conexões > Bluetooth e ative Bluetooth. Escolha Buscar e selecione um dispositivo para parear e conectar. Dispositivos conectados, Dispositivos conhecidos e Outros dispositivos são listas separadas. Use Mostrar dispositivos sem nome se o seu não tiver nome. Desconectar mantém o pareamento; Esquecer o remove. A busca para após 20 segundos, ao sair da página ou ao fechar o painel.

O pareamento pode exigir PIN ou um agente de confirmação. O desktop atual usa o agente Blueman para esses diálogos; reconectar um dispositivo já pareado não comprova suporte a novos pareamentos. Mantenha o agente até testar um pareamento com PIN ou confirmação. A cobertura do agente em instalações novas ainda precisa ser verificada.

## Modo avião

Central de controle > Geral bloqueia WiFi e Bluetooth com rfkill. Desativar o modo restaura apenas as rádios que ele próprio bloqueou. Bloqueios físicos ou aplicados externamente não são ignorados silenciosamente. Ative uma rádio individualmente se necessário.

## VPN

O Walker não tem menu de VPN. WireGuard e NetworkManager VPN estão previstos como plugins (Instalar > Plugins). As linhas do Tailscale ficam em Walker > Configurações > Dispositivos > Streaming > Acessar este PC remotamente; veja [Acesso remoto](handbook:remote-access).
