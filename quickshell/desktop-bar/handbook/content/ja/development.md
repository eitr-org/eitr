# 開発ツール

Main > Developmentには**AI**、**Cloud**、**Git Accounts**、**Monitoring**、**LazyVim**、**VS Code**が集約されています。プロジェクトセレクターは選択したディレクトリをエディタで開きます。テーマの統合により、LazyVimセッションを含むサポートされている開いているエディタが更新されます。

**Git Accounts**は、GitHub/GitLabのデフォルトID、フォルダごとの上書き、SSHキー、個別のプロバイダーCLIログインを設定します。すべてのルール変更にはプレビューでの確認が必要です。プロジェクトのリモートを書き換えたり、グローバルCLIアカウントを変更したりすることはありません。[Gitアカウント](handbook:git-accounts)をご覧ください。

## オプションのツールチェーン

Install > Development LanguagesおよびJavaScript Toolsから、選択したツールをインストールできます。EITRのバー、ランチャー、テーマを実行するためだけにJava、Flutter、データベースクライアントが必要になることはありません。Install > Databasesにはオプションのデータベースツールが用意されています。Install > Developer AppsにはBruno、Cursor、GitHub Desktop、Insomnia、JetBrains Toolbox、Meld、Postman、VS Code、Zedがあります。Install > Productivityには1Password、Bitwarden、Discord、LibreOffice、Obsidian、Slack、Thunderbirdがあります。AURエントリはマシン上でダウンロードおよびビルドされます。ライセンスによってはEITRでの直接配布が許可されていないものもあります。

Languagesには、オプションのArchパッケージとして**mise (many runtimes)**も用意されています。`~/.zshrc`内で`eval "$(mise activate zsh)"`を実行して手動で有効化してください。同じランタイムに対してnvm/uvと競合する可能性があります。既存の言語ごとのマネージャーはそのまま変更されません。

## Webアプリ

Install > Web Apps > Create Web Appでは、名前とアドレスを入力することで、そのサイトを専用ウィンドウで開くランチャーを追加できます。サイトのアイコンは作成時にHTTP(S)経由でのみダウンロードされます。マニフェストが不正な場合やアイコンが利用できない場合は、ページのファビコンまたは汎用ブラウザアイコンにフォールバックします。

アドレスにログイン認証情報を含めないでください。ランチャーとアイコンは、カスタムの`XDG_DATA_HOME`を含むユーザーのXDGデータディレクトリを使用します。いずれかのメニューからの削除時にも同じ場所が使用されます。WebアプリにはChrome、Chromium、Edge、Brave、またはVivaldiが必要です（Install > Browsers）。NetflixなどDRMを備えたストリーミングサイトにはChromeが必要です。削除するには、Install > Web AppsまたはAppsメニューでDeleteを押します。

複数のブラウザプロファイルが存在する場合、Webアプリの作成時にどのプロファイルで開くかを尋ねられます。変更する場合は、アプリを一度削除して再度追加してください。

Install > BrowsersにはBrave（AUR）も用意されています。Install > ProductivityにはBasecampとNotionがオプションのWebアプリとして用意されています。これらのレシピには名前とURLのみが含まれ、サイトのアイコンはインストール時にマシン上でダウンロードされます。事前にインストールされているものはありません。

## AIアシスタント

Settings > AI Assistantを開くと、デフォルトのアシスタントの選択、アカウントおよびAssistant Accessの管理、同意の上でのアシスタント間の連携設定を行えます。Development > AIにはセッションランチャーが保持されます。

**SUPER + A**はホームフォルダでアシスタントを開き、安全にサポートされている場合はそのフォルダを信頼し、サポートされている追加の指示オプションを介してハンドブックのガイダンスを渡します。Development > AIはホームフォルダから開始してフォルダの選択を求め、各アシスタント自身のコマンドと同様にその場所でアシスタントを開きます。CLIの制限事項についてはdistro/ASSISTANT-STARTUP.mdに記載されています。読み取り専用のクイックチャットには、Eitrの概要と関連する翻訳済みハンドブックの抜粋が含まれ、ハンドブックが質問を網羅していない場合はその旨を伝えます。

[herdr](https://herdr.dev)（AIコーディングエージェントを並行して実行するためのターミナル）がEitrに同梱されています: 初回ログイン時（既存のデスクトップ環境では次回ログイン時）に、Eitrはバックグラウンドでherdrの公式インストーラーを実行します。インストーラーはダウンロードを検証し、`~/.local/bin`に`herdr`を配置します。ネットワーク接続がない場合は、以降のログイン時に再試行されます。一度インストールされると再インストールされることはないため、削除した場合は削除された状態が維持されます。`herdr update`でアップデートできます。Walker > Learn > Herdr Commandsにそのキーとコマンドが一覧表示され、Walker > Development > Agent Workspacesでターミナル内にherdrまたはcmuxを開きます。

各サイドアシスタント（クラウドAI）には、Development > AIの下にAccountsサブメニューがあります。Defaultはファイルを移動することなく既存の設定とログインを使用します。「Add Account…」ではラベルの入力を求め、確認画面を表示した上で、対応している環境ではプライベートブラウザウィンドウで各CLI独自のサインインを開きます（未知のブラウザでは通常の起動ツールが使用されます）。Enterで確定し、Escでキャンセルします。

アカウントを選択して、今後の対話型セッション、Ask the AI、および読み取り専用ヘルパーを手動で切り替えます。実行中のセッションは現在のアカウントを維持します。追加したアカウントとそのローカル設定は、確認後にDeleteで削除できます。Defaultは削除できません。選択中のアカウントを削除するとDefaultに戻り、他のアカウントからログアウトすることはありません。Antigravity CLIには設定フォルダを上書きするサポートされたオプションがないため、Defaultのみを提供します。

Ratatoskrはローカルアカウントを1つ持ちます。アカウントのラベルと選択状態はこのPC内の`eitr/ai-accounts.json`（0600）に保存され、独立したフォルダは`$XDG_DATA_HOME/eitr/ai-accounts/`（0700）に保存されます。AI Usageは読み取り可能なアカウントをアシスタントごとにグループ化し、読み取り不可または未対応の使用状況を非表示にします。各セクションはログイン時に閉じた状態で開始され、セッション中の開閉状態を維持します。

Development > AIには、インストールされている各アシスタントのメニューが用意されています: Antigravity CLI、Claude Code、Codex、Gemini CLI、GitHub Copilot CLI、Grok Build、OpenCode、Pi。これらはInstall > AI CLIsからインストールできます。何もインストールされていない場合、Development > AIにはそこへのリンクが表示されます。

セッションメニューでは**New**が先頭に固定され、その他のアクションはアルファベット順に並べられます。Claude CodeおよびGitHub Copilot CLIには**New Named**、**Continue Last**、**Resume Picker**、および名前またはIDによる再開（Claudeでは**Resume by Name**と表記）が用意されています。Codexには**Continue Last**、**Resume Picker**、**Resume by Name or ID**があります。Gemini CLIには**Continue Last**、Walker **Resume Picker**、**Resume by Number**があり、最後のオプションはターミナルに番号付きのセッション一覧を表示してから番号の入力を求めます。

Grok Buildには**Continue Last**、Walker **Resume Picker**、**Resume by ID or Title**があります。OpenCodeには**Continue Last**、Walker **Resume Picker**、**Resume by ID**があり、そのセッションIDオプションを介して**New Named**を提供します: 新しい名前を指定するとセッションが作成され、既存のIDを指定すると再開されます。Antigravity CLIには**Continue Last**および**Resume by ID**があり、セッション一覧の取得や名前付けのオプションはサポートされていません。

Piは、利用可能なパッケージドキュメントからセッションオプションを確認できなかったため、**New**のみを保持しています。Walkerのピッカーでは、利用可能な場合にセッションのタイトルと日付が表示されます。空の一覧ではメッセージが表示されます。名前/IDプロンプトで空のまま決定するとキャンセルされます。Accountsサブメニューは引き続き利用可能です。

LazyVimまたはVS Codeのプロジェクトを開く際は、まずホームフォルダを起点としてフォルダの選択が求められます（隠しフォルダは除外されます）: フォルダを選択してより深い階層に進み、Openで現在いる場所を使用し、Backで1階層上に戻るか最上位でメニューに戻ります。文字を入力すると、現在いる場所から6階層下までのすべてのフォルダが検索されます（`node_modules`、`target`、`build`、`dist`、`venv`、`__pycache__`はスキップされます）。完全に一致する名前のフォルダが先頭に、浅い階層のフォルダが深い階層のものより前に表示されます。AIメニューのフォルダ選択ステップも同様に動作します。

Antigravity CLI、Claude Code、Codex、Gemini CLI、GitHub Copilot CLI、Grok Build、OpenCode、Piはコマンドからも起動できます。ツールが見つからない場合、Eitrはその旨を説明し、Install > AI CLIsと同じインストールを提供します。Enterでインストールを確定し、Escでキャンセルします。対話型ターミナルがない場合、コマンドはインストール手順を表示して終了します。インストール済みのバイナリはこれらのランチャーよりも優先されます。各ツールの独自のワークフローに従ってサインインしてください。アシスタントのバイナリや認証情報は同梱されていません。

Development > AI > Default Assistantで、このコンピューター用のインストール済みアシスタントを1つ選択します。**SUPER + A**でターミナル内にそれが開きます。デフォルトが設定されていない場合は選択画面が開きます。SUPER + Aのアシスタントはデフォルトで完全なアクセス権で開きます: 確認を求めることなくファイルを変更したりコマンドを実行したりできます。Development > AIから開いたアシスタントは、通常の権限確認プロンプトを維持します。

通常の権限確認プロンプトに戻すには、**Settings > AI Assistant > Assistant Access > Ask before changes**を選択します。この設定はこのPCの`eitr/ai.json`にのみ保存されます。組織の制限によって権限プロンプトが強制される場合もあります。sudoには引き続きパスワードが必要です。ヘッドレスの連携および音声リマインダーは読み取り専用のままです。

テーマを変更すると、既存の読み取り可能なClaude Code、Gemini CLI、Grok Buildの設定において、ライト/ダークのテーマ設定のみが更新されます。その他の設定や書式設定はそのまま維持されます。見つからない、壊れている、またはアンインストールされたクライアントはスキップされます。ライト/ダーク設定をサポートしていないアシスタントは、ターミナルの色に従います。

インストールされているSDKのバージョンとインストーラーのソースは、ディストリビューションのマニフェストで管理されています。ハンドブックの例が最新の上流バージョンを保証していると思い込まず、実際のピッカーに従ってください。ツールチェーンのインストールにはダウンロードが必要になる場合があります。

### OpenCode、Pi、およびEitrスキル

Install > AI CLIsには**OpenCode**（`opencode`、Arch公式パッケージ）および**Pi**（`pi`、npmパッケージ`@mariozechner/pi-coding-agent`）も用意されています。どちらもDevelopment > AIメニュー、初回使用時のコマンドランチャー、SUPER + A用のDefault Assistantの選択肢を備えています。OpenCodeは完全なアクセス権を得るために`--auto`を使用します。そのAccountsメニューにはDefaultのみが提供されます: 設定ディレクトリの上書きでは認証情報が隔離されないためです。Piは`PI_CODING_AGENT_DIR`を介して個別の外部アカウントをサポートし、`--append-system-prompt`を通じてハンドブックのガイダンスを受け取ります。Piには組み込みの権限確認プロンプトがないため、Eitrは「Ask before changes」モード時や組織の制限下ではその対話型起動を拒否します。いずれも読み取り専用の連携ヘルパーとしては機能しません。

パッケージ化された**Eitr**スキルは、安全なデスクトップ変更方法を教え、このオフラインハンドブックを参照させます。スキル検出が有効になっている場合、`eitr-config seed`は同じソースをClaude Code用の`~/.claude/skills/eitr/SKILL.md`、およびCodex、Gemini CLI、OpenCode用の`~/.agents/skills/eitr/SKILL.md`にコピーします。`eitr-config update`は未編集のコピーを更新し、ユーザーが作成または編集したコピーを保持し、変更されたデフォルトをレビュー用に`.eitr-new`に出力します。既存のインストール環境には、ログイン時に不足しているスキルが提供されます。CLIごとの起動指示は有効なまま維持されます。自動的なサインインは行われません。

### Ratatoskr（ローカル、実験的）

Development > AI > Default Assistantには常に**Ratatoskr（ローカル、実験的）**が用意されており、アカウントやサブスクリプションを必要としません。初回起動時には、何も変更される前に一度限りのダウンロードについてターミナルで説明が表示されます: Archパッケージの`ollama`（約15 MB）と言語モデル`qwen3:4b`（約2.5 GB、Apache-2.0ライセンス）です。1回の確認（Enterで確定、Escでキャンセル）により、パッケージがインストールされ、ユーザーサービス`eitr-ollama.service`が作成され、進捗が表示されながらモデルがダウンロードされてデフォルトに設定されます。ステップが失敗した場合、その出力が画面に残り、以前のデフォルトが維持されます。

すべてがこのPC内に留まります: サービスは`127.0.0.1:11434`でのみリッスンし、必要なときに起動し、そのモデルを`~/.local/share/eitr/ollama`に保存します。クラウドのアシスタントに比べて信頼性が明らかに低く、特に通常とは異なる言い回しに弱く、プロセッサ上での動作も遅くなります。音声リマインダーは他のアシスタントと同様にその回答を検証するため、間違った回答によって何かが変更されることはありません。**SUPER + A**でモデルとのチャットが開き、`/bye`で終了します。アシスタント間の連携ヘルパーになることはなく、AI Usageのエントリもありません。

同じメニューで**Ratatoskr**を選択し、**Delete**を押します。1回確認が表示された後、サービスとモデルが削除され、デフォルトがローカルに設定されていた場合はリセットされ、セットアップによってインストールされていた場合は`ollama`がアンインストールされます。`~/.ollama`にあるOllama自体のキーとチャット履歴は保持されます。

## モニタリング

Development > Monitoringにより、検索ですぐにダッシュボードにアクセスできます。**Add Dashboard**ではサービス（Grafana、Datadog、Sentry、New Relic、Prometheus、またはOther）、名前、アドレスを入力し、メニューからブラウザでダッシュボードを開くことができます。これらはこのコンピューター内の`~/.config/eitr/monitoring.json`にのみ保存されます。Deleteで削除できます。アドレスにパスワードやトークンを含めないでください。

**Monitoring Tools**はコマンドラインツールをインストールします: Prometheusの`promtool`およびSentry CLIです。Amazon Managed Grafanaのワークスペースは、他のAWSツールとともにCloud > AWS > 対象アカウント > Grafanaにあります。

## アカウントとクラウドワークフロー

AIの使用には、インストールおよび設定されたクライアントが必要です。通常のワークフローに従ってサインインしてください。アカウントのクォータやエンタープライズ/API課金は、サポートされている個人アカウントパネルとは異なる場合があります。EITRに認証情報は同梱されていません。

クラウドメニューは、ローカルのプロバイダーアカウント/プロファイルを使用します。AWSプロファイルはローカルのAWS設定または設定されたEITRクラウドプロファイルマッピングから取得されます。Google Cloudは、名前付きのgcloud設定をアカウントおよびプロジェクトとともに一覧表示します。プロジェクトのない設定の場合、リソースツールを開く際にプロジェクトの選択が求められるため、プロジェクトの検出前でもLoginにアクセスできます。

Azureは有効なサブスクリプションをテナントIDとともに一覧表示します。ツールを選択する前にコンテキストを選択してください: Google CloudおよびAzureのツールは、グローバル検索からではなく、それぞれのコンテキストメニュー内で検索されます。Googleのコンテキストを開くと、無関係な継承されたプロジェクトの上書き設定がクリアされます。プロジェクトのない設定の場合は、リソースツール用にプロジェクトを選択するよう求められます。

ターミナルから戻っても、コンテキストおよびプロジェクトなし設定用に選択したプロジェクトは維持され、グローバルCLIのデフォルトが切り替わることはありません。Login、Check Auth、Refreshは検出された各コンテキスト内に存在します。Google Loginは設定されたアカウントを対象とします。Azure Loginはそのテナントを対象とし、認証後に以前のデフォルトサブスクリプションを復元します。Azure Refreshはサブスクリプションキャッシュを更新し、選択されたサブスクリプションを表示します。

AWSアカウントは、AWS設定ファイル（`~/.aws/config`、または設定されている場合は`AWS_CONFIG_FILE`）内に一致する`[default]`または`[profile NAME]`セクションを持つ必要があります。認証情報ファイルにのみ存在するプロファイルは除外されます。また、ネストされたサービス設定や参照される`[services NAME]`グループを含め、`endpoint_url`を設定している設定プロファイル（空の値であっても）も、Cloudflare R2などのS3互換サービスを対象としている可能性があるため除外されます。`EITR_AWS_PROFILES`を使用して対象となるプロファイルにラベルを付けたり制限したりできますが、除外されたプロファイルを含めることはできません。EITRがいずれのAWSファイルも編集することはありません。

各プロバイダーメニューには**Add AWS Account**、**Add GCP Account**、または**Add Azure Account**が用意されており、企業の「Development」と「Production」など、必要なだけアカウントをセットアップできます。最初に名前の入力を求め、次にその名前でプロバイダーCLI自身のセットアップを実行します: AWS SSO（IAM Identity Center）またはアクセスキーによるAWSプロファイル、サインインとプロジェクトを伴う個別のgcloud設定、またはサブスクリプションに名前を付けるAzureサインインです。

`gcloud`や`az`が見つからない場合は、まずそれらのインストールが提案されます。**Ctrl+R**でアカウントの名前を変更できます。名前は`~/.config/eitr/cloud-contexts.json`に保存されます（AWSプロファイル、gcloud設定、またはサブスクリプションIDをキーとします）。EITRが環境を推測したり、そこに認証情報を保存したりすることはなく、AddによってグローバルCLIのデフォルトが切り替わることも決してありません。Grafanaやクラウド操作には、対応するアカウントと権限が必要です。

一部のアクションは読み取り専用ですが、リモートリソースを変更できるアクションもあります—確定する前に要求された操作とアカウントを確認してください。

トークン、`.env`の機密情報、認証情報は、共有するドットファイルやスクリーンショットの外に保持してください。シェル設定は、インストーラーがプロファイルを書き換えることなく、サポートされているマネージャーを読み込みます。Learnには、専用のLazyVim、tmux、cmuxのリファレンスが保持されています。

## アシスタントの連携

Development > AI > Let assistants work togetherはデフォルトでオフになっています。これを有効にすると、サインイン済みとして認識されているインストール済みのClaude Code、Codex、Copilot、Grok、Gemini CLIクライアントが接続されます。各ハンドオフはヘルパー側のサブスクリプションまたはAPI課金を使用し、その制限に対してカウントされます。他のクライアントのAPIキーのみやキーリングのみのサインインは検出されません。

Geminiは、空でない`GEMINI_API_KEY`または`GOOGLE_API_KEY`が存在するか、`~/.gemini/settings.json`で`security.auth.selectedType`が`gemini-api-key`または`vertex-ai`に設定されている場合にのみ検出されます。個人のGoogleサインインはカウントされません: Googleはもはやこれを提供していません。Geminiはプランモードでヘッドレス実行され、MCPサーバーや拡張機能は除外されます。Eitrは無料のAPIキーを使用してこれをテストしました: 読み取り専用の質問およびブリッジ経由で渡された質問の双方が回答を返しました。プランモードは読み取り専用として文書化されていますが、Eitrはそのファイル、シェル、またはプランファイルの動作を独自に検証したわけではありません。

メインのアシスタントに対して、レビュー、説明、提案のために他のアシスタントに相談するよう依頼します。各ハンドオフは呼び出し元アシスタントの通常のツールプロンプトを通じて承認してください。Eitrがこれらのツールを事前承認することはありません。アシスタントサーバーの自動ツール承認を有効にしないでください。ヘルパーは読み取りのみを行い、編集はメインのアシスタントが行います。ヘルパーがさらに別のヘルパーに依頼することはできません。誰が誰に依頼したかを通知で特定し、各リクエストには3分のタイムアウトがあります。ヘルパーは呼び出し元の現在の作業ディレクトリを読み取ります。その質問とコンテキストはそのアシスタントのプロバイダーに送信される可能性があります。

このスイッチをオンにすると、各アシスタント自身のコマンド（`claude mcp add`、`codex mcp add`、`copilot mcp add`、`grok mcp add`、`gemini mcp add -s user`）を通じて1つの`assistants` MCPサーバーが登録されるため、各アシスタントが独自の設定を書き込みます。同じ名前の既存のサーバーは変更されずに残され、報告されます。変更はこのコンピューター上の`~/.local/state/eitr/assistants.json`（または`XDG_STATE_HOME`）にのみ記録されます。スイッチをオフにすると、Eitrのエントリのみが正確に削除されます。エントリが後から編集されていた場合、Eitrはそれを保持し、競合を報告します。

スイッチを変更した後は、既存のアシスタントセッションを再起動してください。実アカウントでのハンドオフは、依然として個別のエンドツーエンド検証を待っている段階です。

Antigravity CLI（`agy`）は、Install > AI CLIsおよび初回使用時のランチャーから個人のGoogleアカウントで利用できます。同梱されることはありません。ダウンロードを検証するGoogleの公式インストーラーを介してインストールされ、Googleアカウントでサインインします。現時点ではアシスタント連携ヘルパーとしては提供されていません。すでにインストールされている`agy`は通常通り起動できます。

Gemini CLIにはGemini APIキーまたはGoogle Cloud/企業アカウントが必要です。Antigravityはコラボレーションヘルパーではありません: ヘッドレスモードでは読み取りすら拒否されます。唯一のロック解除方法は、権限をバイパスするかグローバルルールを変更することです。Eitrは、実行ごとの権限または読み取り専用のヘッドレスモードが利用可能になった時点で再検討します。

### 追加のプロバイダー

Development > Cloudには、Cloudflare（`wrangler`）、DigitalOcean（`doctl`）、Hetzner Cloud（`hcloud`）、Oracle Cloud（`oci`）、Vercel、Netlify、IBM Cloud（`ibmcloud`）も並んでいます。英小文字、数字、またはハイフンを使用した名前でアカウントを追加します。これらのアカウントは`~/.config/eitr/cloud-accounts/<provider>/<name>`の下にあるプライベートワークスペースです。既存のプロバイダー設定がインポートされることはありません。選択されたプロバイダーとワークスペースは、ツールピッカーおよびターミナル内で常に表示されます。ターミナルから戻ると同じワークスペースに戻ります。Shift+Backspaceでアカウント一覧に戻ります。ワークスペースを選択しても、グローバルCLIのデフォルトが切り替わることは決してありません。

見つからない`wrangler`、`doctl`、`hcloud`は、Archの公式リポジトリから提供されます（`doctl`と`hcloud`はextraにあります）。Oracle CloudおよびIBM Cloudは、`distro/installers.json`に記載された公式のHTTPSシェルインストーラーを使用します（Oracleは`--accept-all-defaults`を渡します）。Vercel（`vercel`）およびNetlify（`netlify-cli`、コマンド`netlify`）は既存のNVM/npmインストールレシピを使用します。インストールには確認が必要です。サインインおよびアカウント操作は、選択されたプライベートワークスペース内でのみ実行されます。

DigitalOceanとHetznerはネイティブコンテキストを一覧表示します。Oracleはそのワークスペースの`~/.oci/config`からプロファイルを一覧表示します。それらのコンテキスト/プロファイルを選択すると、ローカルの選択が保存され、グローバルなデフォルトを変更することなくコマンドごとのフラグが使用されます。VercelとNetlifyはネイティブの切り替えアクションを公開しています。後から選択したチーム/アカウントのラベルを入力してください。Vercelはログイン前にもスコープを尋ね、以降のコマンドに`--scope TEAM`を渡します。

IBMはSSOおよびAPIキーによるサインインを提供し、`ibmcloud target`を表示して、明示的なアカウントとリージョンを対象とします。メニューに戻っても、選択されたコンテキスト/プロファイル/スコープ/アカウントおよび保存されたリージョンが表示されたままになります。これらのラベルはローカルの選択肢であり、検証されたリモートIDではありません。既存の認証情報やプロバイダーの上書き設定は継承されません。ブラウザコンソールは独自のセッションを使用するため、操作前にアカウントを確認してください。

7つのプライベートワークスペースプロバイダーは、短い説明が付いたニュートラルなリソースおよびアクションアイコンを使用します。アカウントがアルファベット順で先頭に表示され、その後にAdd Accountが続きます。ツールは翻訳された名前のアルファベット順に並べられます。ピッカーには選択されたアカウント、コンテキスト、保存されたリージョンが表示され、各読み取り専用レポートはその出力の上にそのコンテキストを再度表示します。レポートは共通のAWSページャーを維持します。追加のリソースコマンドやログ検索は導入されません。

| プロバイダー | サインイン | 一覧 / 切り替え / コマンドコンテキスト |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

クラウドナビゲーションは本物のElephantメニューを使用します。Shift+Backspaceで前のメニューに戻ります: サービスまたはリソースの選択はそれを含むメニューに戻り、アカウントメニューはプロバイダーのアカウント一覧に戻り、その一覧はCloudに戻ります。選択されたアカウントとコンテキストは表示されたままになります。Eitrはこのナビゲーションの選択を`~/.config/eitr/cloud-navigation.json`に保存します。プロバイダーCLIのデフォルトは変更されません。レポートはページャーを保持し、ログ検索はfzfを保持し、セットアップは確認付きのターミナルフォームを保持します。フリーテキスト検索プロンプトはWalkerで引き続きテキストを受け付けます。これらはナビゲーションリストではありません。

アカウント行でDeleteキーを押すか、メニュー内の**Delete Account**を押すと、アカウントを削除できます。確認画面にはプロバイダーとアカウント名が表示されます: リモートのアカウントに影響を与えることなく、このコンピューター上のそのアカウントに対するプロバイダーのサインイン情報を削除します。キャンセルしても何も変更されません。削除されるのは選択されたEitrプライベートアカウントフォルダのみです。シンボリックリンク、プロバイダールート外のパス、実行中のEitrアクションがあるアカウントは拒否されます。AWS、Azure、Google Cloudには新しい削除アクションはありません。確認画面はCancelとConfirm付きでWalker内に開き、ターミナルは開きません。

読み取り専用レポートは、選択されたプライベートアカウント環境と既存のクラウドページャーを使用します。Cloudflare: Account、R2 Buckets、D1 Databases、KV Namespaces、Pages Projects、Queues。DigitalOcean: Droplets、Apps、Databases、Kubernetes、Volumes、Domains、Load Balancers、Balance。Hetzner: Servers、Volumes、Networks、Firewalls、Load Balancers、Primary IPs、Snapshots。Oracle: Compartments、Instances、Buckets、VCNs。Vercel: Projects、Deployments、Domains。

Netlify: Status、Sites。IBM: Account、Target、Resource Groups、Service Instances。DigitalOceanとHetznerは常に選択されたコンテキストを渡します。Oracleは選択されたプロファイルとセキュリティトークン認証を渡し、そのアカウントのプライベートプロファイルからのみテナンシーを読み取ります。バケットの一覧表示はまずそのネームスペースを読み取ります。Vercelは選択されたチームスコープを渡します。エラーは読み取り可能なまま表示され、別のアカウントでの再試行がトリガーされることは決してありません。

ログ検索は既存のfzfビューアを維持します。実アカウントでのライブ確認は保留されたままです。

クラウドアカウント、Gitアカウント（AddおよびEdit）、モニタリングダッシュボード、Webアプリのセットアップフォームは、左側にステップ、右側に現在の回答が一覧表示されます。矢印キーまたはTabキーでステップを選択し、Enterで回答を入力します。確認画面では、適用する前にすべての回答が一覧表示されます。Leftキーまたは矢印キーでステップに戻ることができ、長い確認画面はPgUp/PgDnでスクロールできます。

EscまたはCtrl+Cで保存せずにキャンセルします。ベンダーのサインインは確認の後に開始されます。サインインが失敗または中断された場合、新しいアカウントは破棄されます。Google Cloudはサインイン前にオプションのプロジェクトIDを要求します。Azureはサインイン前にオプションのサブスクリプションラベルを要求し、指定しない場合は各サブスクリプションの既存の名前を維持します。Vercelはサインイン前にそのスコープを要求します。

## Docker

Docker、docker-compose、Lazydockerがインストールされていますが、Dockerサービスはデフォルトでオフになっています。`sudo systemctl enable --now docker.service`で有効化してください。

`docker ps`でpermission deniedが報告される場合は、`sudo usermod -aG docker $USER`でユーザーを追加してください。dockerグループのメンバーシップはroot権限と同等です。ログアウトして再度ログインするか、1つのターミナル内で`newgrp docker`を使用してください。`id -nG`で所属グループを確認できます。
