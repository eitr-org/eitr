# Como navegar pelo Sistema

Abra **SUPER + F > Sistema**. As ações são agrupadas em ordem alfabética; a busca global continua encontrando-as diretamente, sem precisar abrir cada grupo.

## Conectividade

**Bluetooth**, **Infraestrutura de rede**, **WiFi**. As entradas de dispositivos abrem os mesmos painéis da barra. A escolha do serviço de rede prepara a próxima inicialização, sem reiniciar a conexão atual.

## Dispositivos e entrada

**Áudio**, **Limite de Carga da Bateria**, **Tela**, **Teclado**, **Iluminação**, **Microfone**. O limite de carga exige firmware compatível de notebook. Tela reúne brilho, luz noturna, seleção de monitores e perfis de energia compatíveis de notebooks.

**Iluminação** decide se as trocas de tema recolorem ventoinhas, teclados e outros dispositivos controlados pelo OpenRGB. Fica desativado por padrão para preservar sua iluminação. Escolha **Seguir o tema** para aplicar a cor do tema agora e a cada troca.

## Informações

**Sobre**, **Uso de IA**, **Hardware**, **Relatar um problema**, **Clima**. Sobre abre o resumo do sistema EITR; Relatar um problema coleta um relatório privado para você ler antes de enviar. Os demais usam painéis nativos. Calendário e visão geral dos espaços continuam na barra e na busca global, sem ocupar esse menu. Busque **Ragnarök** para o Fenrir morder a tela; um clique ou Escape encerra antes do fim.

## Manutenção

**Limpeza**, **Redefinição de fábrica**, **Instantâneos**, **Atualizar**. Atualizar oferece Atualização do sistema e Canal de atualização. A redefinição de fábrica é destrutiva e exige dois avisos: leia [Redefinição de fábrica](handbook:factory-reset) antes.

## Segurança

**Chave de segurança FIDO2**, **Impressões digitais**, **Desbloqueio do disco por TPM**, **Firewall**, **Voltar à autenticação da senha**, **Atualizar senha**. A documentação de Secure Boot fica em **Aprender > Manual do EITR > Secure Boot**, não em uma ação separada de menu ou segurança.

## Dotfiles

Abre sua pasta de configuração no VS Code ou, se ele não estiver instalado, no LazyVim. Mantenha ajustes de monitores e hardware específicos do computador em `~/.config/hypr/local.lua`, não nos padrões compartilhados. Não coloque tokens, chaves de recuperação ou senhas em backups de configuração.

Os próximos capítulos detalham os fluxos e limites de segurança.

## Idioma

**Walker > Sistema > Idioma** lista os idiomas, com o atual marcado; veja o [Guia de idioma](handbook:language). A busca aceita nomes em inglês e traduzidos. Submenus aparecem primeiro, seguidos de ações, ordenados pelos títulos traduzidos. Principal e Aplicativos mantêm a ordem existente.
