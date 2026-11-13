# ターミナルとエディタ

**SUPER + Enter**で選択したターミナル（デフォルトはKitty）を開きます。**SUPER + Ctrl + Enter**でメインのtmuxセッションを開くかアタッチします。**SUPER + P**でファイルをあいまい検索し、**SUPER + Ctrl + P**でファイル内容を検索します。Learn > Cmux Commands、Tmux Commands、LazyVim Commandsは検索可能なリファレンスです。コマンドを選択すると、実行されるのではなくクリップボードにコピーされます。

Kittyは、Enter、Home/End、単語間の移動など、2セル以上のジャンプ時に短いカーソル軌跡（トレイル）を表示します。これはカーソルが3ミリ秒停止した後に開始され、0.05〜0.15秒でフェードアウトします。カスタマイズするには、`~/.config/kitty/local.conf`で`cursor_trail`、`cursor_trail_decay`、または`cursor_trail_start_threshold`を設定してください。`cursor_trail 0`で無効化されます。個人の設定はパッケージのデフォルトを上書きし、テーマ変更後も保持されます。

### Cursor Fire

Kittyの燃え上がるカーソルトレイルを有効にするには、**Settings > Appearance > Terminal**でCursor Fireをオンにします。デフォルトはオフです。オフにすると、通常のカーソルトレイルと個人のシェーダーの選択が復元されます。

このエフェクトにはKitty 0.49以上と、Eitrのデスクトップ依存関係に含まれる`shader-slang`が必要です。有効化すると、Kittyの保存または再読み込みの前に組み込みシェーダーが検証されます。マシン固有の設定は`~/.config/eitr/terminal.json`に保存されます。ヘルパーは`kitty/cursor-fire.conf`を出力し、これはKittyのユーザーローダーによって最後に読み込まれます。有効になっている間はfireシェーダーが選択され、移動しきい値が1セルに引き下げられます。フォント、テーマ、個人の設定ファイルは変更されずに維持されます。

## ターミナルの選択

Settings > Appearance > TerminalでKittyまたはGhosttyを選択します。代替としてWalker > Settings > Desktop > Appearance > Terminalも利用できます。`~/.config/eitr/terminal.json`内のマシン固有の`terminal`フィールドが、Super+Enter、tmux、ユーザーターミナルセッション、AI/プロジェクトターミナル、およびWalkerのターミナルで開くアクションを制御します。Ghosttyがインストールされていない状態でこれを選択すると、公式パッケージの通常のInstallフローが開きます: Enterでインストール、Escでキャンセルします。インストールが成功するまでKittyが選択されたままになります。後でGhosttyが削除された場合、起動はKittyにフォールバックします。Ghosttyはオプションであり、ISOペイロードには含まれていません。

テーマを切り替えると、テーマの16個のANSIカラー、背景色、前景色、選択色、テキストカーソル色を含む`~/.config/ghostty/eitr.conf`が再生成されます。フォントを変更すると、選択されたフォントファミリーが再生成されます。デフォルトのサイズは10ポイントです。Ghosttyは同じzshとプロンプトを実行し、デフォルトで75%の不透明度と通常のウィンドウパディングなし（ゼロ）に設定されます。Hyprlandがぼかし効果と同じ通常のウィンドウ装飾/ルールを提供します。`eitr/cursor.json`内のポインタファミリー、サイズ、およびAuto/Light/Darkの選択は、GTKおよびコンポジター全体に適用され、ターミナルのテキストカーソルとは別個のものです。

GhosttyはEitrランチャーを介して生成されたファイルを読み込みます。`font-size = 12`や`cursor-style = bar`などの個人の設定は`~/.config/ghostty/local.conf`に記述してください。このファイルは最後に読み込まれ、テーマ変更後も保持されます。実行中のGhosttyセッションは、テーマ/フォントの変更後にサポートされている再読み込みシグナルを受信します。一部のオプションは新しいウィンドウにのみ適用されます。KittyのカーソルトレイルとCursor FireはKitty専用の機能です。Ghosttyには同等の組み込みの炎エフェクト設定はありません。

Eitrのタスク、メニュー、ステータス、セットアップのターミナル（`eitr-menu-terminal`、`eitr-plugins`、`fif-terminal`を含む）は、常にKittyを使用します。これらの`--class`、`--hold`、`--title`オプションおよびフローティングウィンドウのルールはKitty固有のままです。Ghosttyを選択してもこれらは変更されません。

## ターミナルの外観と共有のぼかし

Walker > Settings > Desktop > Appearance > TerminalおよびSettings > Appearance > Terminalでは、KittyとGhosttyの両方に不透明度、パディング、ぼかしのプリセットを適用します。不透明度にはSolid（100%）、Light（90%）、Medium（80%）、Default（75%）、Strong（70%）が用意されています。パディングにはNone、Small（4ポイント）、Comfortable（8ポイント）があります。デフォルトは不透明度75%、パディングなし、ぼかしOnが維持されます。ユーティリティターミナルは、ソリッドな背景とタスク用パディングを維持します。

ぼかしをOffにすると、通常のKittyおよびGhosttyウィンドウに対するコンポジターのぼかしが無効になりますが、不透明になるわけではありません。ぼかしの強度はデスクトップ全体で共有されます: Gentle（サイズ2、1パス）、Medium（サイズ3、2パス、デフォルト）、Strong（サイズ5、3パス）。同じ選択肢は、WalkerのDesktop BarおよびSettings（SUPER + ,）のDesktop Barの外観の隣にも表示されます。

Hyprland 0.57のぼかし強度はグローバル設定であるため、パネル、通知、Overview、その他のぼかしを使用しているアプリケーションを含む、すでにぼかしを使用しているすべてのサーフェスに影響します。強度を選択してもターミナルのぼかしが有効になるわけではありません。ぼかしを強くするとGPUの負荷が増加します。Theme Colorは既存の不透明な外観を維持します。

ターミナルの選択は`eitr/terminal.json`に保存され、共有の`blur-strength`は`quickshell/desktop-bar/bar-settings.json`（バージョン1）に保存されます。生成された`kitty/appearance.conf`、`ghostty/eitr.conf`、`hypr/appearance.lua`は、これらの設定に基づいて再生成後も維持されます。コンポジターは生成された外観設定を`hypr/local.lua`の前に読み込むため、個人のコンポジタールールが優先されます。`kitty/local.conf`および`ghostty/local.conf`内のターミナル設定はプリセットを上書きします。テーマの切り替えやパッケージのアップデートにより設定が再生成されます。KittyはSIGUSR1を、サポートされているGhosttyセッションはSIGUSR2を受信します。動的に再読み込みできないオプションは新しいウィンドウに適用されます。

## eitrコマンド

`eitr`はEitrのツールを1つのコマンドに統合したものです。引数なしで実行すると一覧が表示されます。メニューと同じスクリプトを実行するため、両者の動作は常に一致します。

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Eitr" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
eitr about
eitr matrix                  # rune rain; any key stops it
```

`eitr about`はAbout Eitrを開くか、すでに開いている場合はそのウィンドウにフォーカスを合わせます。

`eitr config`および`eitr git`は引数を`eitr-config`および`eitr-git`に渡します。各コマンドには`--help`が用意されています。

## 独自のフック

フックは、Eitrが特定のタイミングで実行する小さな自作スクリプトであり、Eitr自体を変更することなく機能を拡張できます。そのタイミングにちなんだ名前の実行可能ファイルを`~/.config/eitr/hooks/`に配置してください:

| ファイル | 実行タイミング | 受け取る引数 |
| --- | --- | --- |
| `post-update` | システムアップデートまたはpacman/AURアップデートの後 | `system`、`pacman`、`yay`、または`full` |
| `theme-set` | テーマ切り替えの後 | テーマのフォルダ名 |
| `battery-low` | バッテリーが15%に低下するごとに1回 | パーセンテージ |
| `post-boot` | 各起動後の初回ログイン時 | なし |

例えば、テーマが変更されるたびにSpotifyの色を変更する（Spicetifyを使用）には、`~/.config/eitr/hooks/theme-set`を作成します:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

作成後、`chmod +x ~/.config/eitr/hooks/theme-set`で実行可能にします。各フックには最大60秒が与えられます。その出力や失敗は`~/.local/state/eitr/hooks.log`に記録され、フックが失敗してもアップデートやテーマの切り替えが停止することはありません。`eitr hook list`で存在するフックを確認でき、`eitr hook run theme-set eitr`でフックをテスト実行できます。アップデートがこのフォルダを変更することはありません。

## cmux TUI

Kitty内で`cmux`を実行するか、名前付きセッションの場合は`cmux --session work`を実行します。cmux TUIはtmuxと並ぶオプションのワークフローであり、Kittyやその既存のショートカットを置き換えるものではありません。新規のEITRインストールには、`/usr/bin/cmux`に固定された公式バイナリが含まれています。既存のユーザーごとのインストールがPATH上で優先される場合があります。どちらが選択されているかを確認するには`command -v cmux`を使用してください。ターミナル出力やテキストファイルの閲覧用として`less`が含まれています。

デフォルトのプレフィックスは**Ctrl-b**です: キーを離してから次のキーを押します。

| ショートカット | 操作 |
| --- | --- |
| Ctrl-b ? | 現在のショートカットを表示 |
| Ctrl-b W | ワークスペースを作成 |
| Ctrl-b c | 画面を作成 |
| Ctrl-b % / Ctrl-b " | 左右に分割 / 上下に分割 |
| Ctrl-b t | 新しいターミナルタブ |
| Ctrl-b h/j/k/l | 左/下/上/右にフォーカス |
| Ctrl-b s | サイドバーの表示/非表示 |
| Ctrl-b d | ローカルで終了またはサーバーから切断 |

UIなしで継続するセッションの場合は、`cmux --headless --session work`を実行し、後から`cmux attach --session work`でアタッチします。ブラウザタブにはChrome/Chromiumが必要です。タブ、ペイン、またはワークスペースを閉じると、実行中のタスクに影響を与える可能性があります。これらの操作を行う前に確認してください。Learn > Cmux Commandsには、セッションコマンド、ナビゲーション、マウス操作、終了用ショートカットが含まれています。デフォルト設定は変更または上書きされる可能性があるため、**Ctrl-b ?**が最新のリファレンスとなります。

## タスクターミナル

メニューから開くターミナル、およびアップデートや問題報告の通知から開くターミナルは、ウィンドウの中央にフローティング表示され、テーマのソリッドな背景を使用します。AIアシスタントのセッションおよびLazyVimプロジェクト（Developmentメニュー）は、自分で開くターミナルと同様に通常のタイル表示ウィンドウとして開き、半透明の背景を使用します。通常のターミナルは対話型でブランド表示はありません。

インストーラー、アップデート、セットアップのターミナルには、テーマに合わせたルーン文字スタイルのEITRバナーが表示されます。成功したタスクは通常自動的に閉じ、失敗したタスクは閉じるまで開いたままになります。情報レポートは意図して開いたままになる場合があります。Elephantを再起動しても、起動済みのアプリが閉じることはありません: メニュー、キーバインド、バーボタンから開いたアプリやターミナルは、uwsmセッション内の独立したアプリケーションスコープを使用します。

uwsmがない場合は直接起動されます。Elephantは、デスクトップヘルパーおよびフォールバック起動用にプロセスのみの停止処理を維持します。

待機中のタスク、アカウント、レポート、Aboutのターミナルを閉じるには**Esc**を押します。Enterは、復旧キーの確認やインストーラーの電源オフなど、回答や確認のために使用されます。

## シェル履歴

`history`で最近のコマンドが一覧表示されます。zshでは、実際の履歴ファイルのパスを次のように確認できます:

```sh
printf '%s\n' "$HISTFILE"
```

Neovimで開くには:

```sh
nvim "$HISTFILE"
```

履歴にはトークンや認証情報が含まれる場合があるため、バグレポートにコピーしないでください。手動で編集する前に他のシェルを閉じてください。実行中のシェルがメモリ上の履歴を書き戻す可能性があるためです。zshの拡張履歴にはタイムスタンプのメタデータや複数行のコマンドが含まれる場合があります。任意の断片ではなく、該当するエントリ全体を削除してください。元に戻す必要がある場合に備えて、非公開の場所にバックアップを作成してください。

## エディタの外観

テーマを変更すると、生成されたVS CodeおよびLazyVimの設定が更新されます。サポートされている実行中のLazyVimセッションは、開き直すことなく更新されます。ユーザー独自の上書き設定やプラグインで独自の色を選択することもできます。エディタがデスクトップに従わない場合は、その設定を確認してください。デフォルトフォントの統合は、アプリが対応している場合にのみ適用されます。

## プロフィール画像

`eitr picture`（または`eitr picture show`）で現在の画像の状態がJSONとして表示されます。`eitr picture set FILE`で中央を基準とした最大の正方形を保存します。`eitr picture remove`で削除します。トリミングを調整するにはSettings > Usersを使用してください。
