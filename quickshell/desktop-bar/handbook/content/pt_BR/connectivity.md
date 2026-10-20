# WiFi, Bluetooth e modo avião

Abra pelos ícones da barra ou por **Sistema > Conectividade**. Abrir um painel nunca troca o serviço de rede nem desconecta um dispositivo por conta própria.

## WiFi

O painel separa redes conectadas, conhecidas e outras redes. Escolha uma disponível para conectar; os campos de senha ocultam o conteúdo. Redes salvas e indisponíveis continuam visíveis, sem percentual de sinal inventado. Desconectar fica na linha conectada; esquecer uma rede salva exige confirmação.

A parte superior mostra estado da rede, ping, banda WiFi, endereço IP e gateway. O compartilhamento por QR usa uma senha WiFi fornecida e mantém a imagem gerada na memória. Credenciais corporativas não são compartilhadas como QR de rede pessoal.

Redes corporativas aceitam PEAP/MSCHAPv2 e TTLS/PAP. Peça ao administrador usuário, certificado da autoridade certificadora e domínio do servidor de autenticação; não desative a validação do certificado. Outros métodos exigem configuração avançada. Veja [Serviços de rede](handbook:network-backends).

## Bluetooth

Ative ou desative o adaptador, procure, pareie, conecte, desconecte ou esqueça dispositivos. Conectados, conhecidos e recém-descobertos ficam em grupos separados. A busca iniciada pelo painel para após 20 segundos ou ao fechar o painel.

O pareamento pode exigir PIN ou um agente de confirmação. O desktop atual usa o agente Blueman para esses diálogos; reconectar um dispositivo já pareado não comprova suporte a novos pareamentos. Mantenha o agente até testar um pareamento com PIN ou confirmação. A cobertura do agente em instalações novas ainda precisa ser verificada.

## Modo avião

Central de controle > Geral bloqueia WiFi e Bluetooth com rfkill. Desativar o modo restaura apenas as rádios que ele próprio bloqueou. Bloqueios físicos ou aplicados externamente não são ignorados silenciosamente. Ative uma rádio individualmente se necessário.
