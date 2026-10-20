# Idioma

O Eitr segue o idioma das mensagens do sistema. **Central de controle > Sistema > Idioma** mostra o idioma usado para a localidade atual e abre um seletor de idioma; **Walker > Sistema > Idioma** lista as mesmas opções, com a atual marcada. Escolha um idioma ou **Padrão do sistema** e depois saia da sessão e entre novamente. O Eitr nunca encerra sua sessão automaticamente.

O Eitr verifica **LC_ALL**, depois **LC_MESSAGES** e, por fim, **LANG**. Variáveis vazias são ignoradas. `LC_MESSAGES` altera as mensagens sem mudar os formatos de data, números ou moeda; `LC_ALL` substitui todas as categorias de localidade e normalmente fica sem definição. `C`, `POSIX` e idiomas não disponíveis usam inglês. Uma mensagem sem tradução aparece em inglês; um capítulo ausente do manual usa o capítulo inteiro em inglês.

## Alterar o idioma do sistema

Se também precisar alterar as configurações de todo o sistema, use a configuração de localidade. No Arch Linux, habilite a localidade desejada em `/etc/locale.gen` e gere as localidades instaladas com `sudo locale-gen`. Depois, defina o idioma em `/etc/locale.conf`, por exemplo:

```text
LANG=pt_BR.UTF-8
```

Os idiomas iniciais são `pt_BR.UTF-8` (português brasileiro), `es_ES.UTF-8` (espanhol), `de_DE.UTF-8` (alemão) e `fr_FR.UTF-8` (francês). Variantes regionais podem usar a tradução do idioma base. Execute `locale` em um terminal para verificar substituições e `locale -a` para listar as localidades instaladas. Saia da sessão e entre novamente para aplicar o idioma ao desktop, aos menus e aos novos terminais. O seletor grava apenas `~/.config/environment.d/90-eitr-language.conf`: define `LC_MESSAGES` e esvazia `LC_ALL` para a próxima sessão, preservando os formatos de data e números. **Padrão do sistema** remove essa preferência. Ele não altera `/etc/locale.conf` nem gera localidades; aplicativos já abertos mantêm o idioma atual.

## Contribuir com uma tradução

O texto em inglês é a fonte. Os catálogos ficam em `i18n/catalogs/<locale>/`; edite os valores traduzidos e mantenha as chaves em inglês. Mensagens Python e shell usam um único domínio gettext: `eitr`. Preserve os marcadores `%1` e `{name}`, os glifos, os nomes dos pacotes, os comandos e os caminhos. As palavras digitadas para confirmar ações destrutivas devem corresponder às palavras aceitas pela verificação.

Os capítulos do manual ficam em `quickshell/desktop-bar/handbook/content/<locale>/<chapter-id>.md`. Preserve os links `handbook:`, os blocos de código e os comandos. As tabelas de teclado e mouse são geradas a partir das fontes oficiais dos atalhos; traduza suas mensagens no catálogo do manual em vez de manter uma segunda lista de teclas.

Execute `python3 tools/i18n-build.py --check`, gere o manual com `python3 quickshell/desktop-bar/scripts/handbook-build.py` e execute sua opção `--check`, além de `bash tools/check.sh`. As verificações listam mensagens ausentes e marcadores alterados. Confira traduções longas em prévias fora da tela antes de enviar sua contribuição.

Depois de traduzir integralmente um capítulo alterado, atualize sua entrada em `source-hashes.json` com o SHA-256 da fonte em inglês. A verificação aponta fontes alteradas ou não registradas; apenas gerar os catálogos nunca confirma uma alteração da fonte.
