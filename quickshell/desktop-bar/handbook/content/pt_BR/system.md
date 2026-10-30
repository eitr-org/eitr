# Como navegar pelas Configurações

Abra **SUPER + F > Configurações**. As pastas aparecem antes das ações, em ordem alfabética. A busca global também encontra os nomes anteriores, incluindo System e Toggle.

**Conectividade**, **Dispositivos e entrada**, **Idioma**, **Segurança**, **Estilo**, **Sistema** são pastas. **Central de controle** abre os mesmos controles que SUPER + vírgula. **Arquivos de configuração** abre sua pasta de configuração no VS Code ou LazyVim.

Conectividade abre os painéis nativos de Bluetooth e WiFi, a infraestrutura de rede e o acesso remoto. A escolha do serviço prepara a próxima inicialização sem reiniciar a conexão atual.

Dispositivos e entrada contém Áudio, Limite de Carga da Bateria, Tela, Teclado, Iluminação e Microfone. O limite só aparece com uma bateria do sistema e exige firmware compatível. Baterias de periféricos não ativam controles de notebook. Tela inclui brilho, luz noturna e perfis de energia compatíveis.

Iluminação fica desativada por padrão. Seguir o tema permite recolorir os dispositivos controlados pelo OpenRGB a cada troca de tema.

Estilo mantém as opções de tema, papel de parede, bloqueio, fontes e aparência da área de trabalho. Toggle agora se chama Ações rápidas no Principal; Iniciar protetor de tela o inicia imediatamente.

**Configurações > Sistema** contém **Informações**, **Manutenção**, **Canal de atualização**, **Sobre**, **Atualização do sistema**. Sobre abre o resumo do sistema EITR. Informações contém Uso de IA, Hardware, Relatar um problema e Clima. Calendário, visão geral das áreas de trabalho e Ragnarök continuam disponíveis na busca global.

Manutenção contém Redefinição de fábrica, Instantâneos, Verificar este PC, Escolher os espelhos mais rápidos e Limpeza. A redefinição exige dois avisos e confirmação digitada; leia [Redefinição de fábrica](handbook:factory-reset) antes.

Segurança mantém os controles de autenticação, firewall e usuários. A documentação continua em [Secure Boot](handbook:secure-boot). Guarde ajustes de hardware em `~/.config/hypr/local.lua` e mantenha segredos fora dos backups de configuração.

**Walker > Configurações > Idioma** lista os idiomas com o atual marcado; veja [Idioma](handbook:language). Os nomes ingleses e traduzidos continuam pesquisáveis. Principal e Aplicativos mantêm sua ordem.

Segurança: Acesso dos assistentes, Chave de segurança FIDO2, Impressões digitais, Desbloqueio do disco por TPM, Usuários, Firewall, Voltar à autenticação da senha, Atualizar senha.
