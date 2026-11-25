# バックアップと復元

デスクトップ設定、選択した個人フォルダー、インストール済みアプリの一覧を、暗号化された1つの `.eitrbackup` ファイルとして別のPCや新しいEitr環境へ移行します。

[復元とスナップショット](handbook:recovery) のスナップショットは更新の巻き戻し用に同じディスク上へ保存されます。バックアップと復元では、`zstd` で圧縮し `age` パスフレーズで暗号化した持ち運び可能なアーカイブを作成します。

## バックアップと復元を開く

- **設定**: **SUPER + ,** を押し、**システム > バックアップと復元** を開きます。
- **Walker**: **SUPER + F** を押し、**設定 > システム > バックアップと復元** を選択します。
- **端末**: `eitr backup`（または `eitr-backup wizard`）を実行します。

## バックアップを作成する

1. 含めるカテゴリを選びます:
   - **Eitr設定**: デスクトップ設定、`~/.config/eitr/overrides` の上書き設定、自作テーマ・壁紙・ロック画面。
   - **アプリ設定**: `~/.config` 内のEitr以外のフォルダー（ブラウザープロファイルとキャッシュは除外）。
   - **個人フォルダー**: `$HOME` 直下のフォルダー（既定では未選択）および `$HOME` 内のサブフォルダーを追加する **フォルダーを追加…**。サイズはバックグラウンドで計算されます。
   - **インストール済みアプリ**: Eitr標準以外に追加した公式・AUR・Flatpak・プラグイン・Store項目の一覧。
   - **マシン設定**: 既定ではオフ。このPC固有のディスプレイ設定と `hypr/local.lua`。
   - **Gitアカウント**（任意選択の機密項目、既定ではオフ）: `eitr/git-accounts.json`、`eitr/git-accounts` 配下の管理インクルード、`~/.gitconfig`、各アカウントが指定するSSH鍵（秘密鍵と `.pub`、権限 `0600` を維持）、`~/.ssh/config`、`~/.ssh/known_hosts`、および `gpg --export-secret-keys --armor` でエクスポートされるGPG秘密鍵（GPG自身がパスフレーズを尋ねます）。
   - **クラウドアカウント**（任意選択の機密項目、既定ではオフ）: `~/.aws`、`~/.config/gcloud`、`~/.azure`、`~/.kube` およびEitrのクラウドラベル（`eitr/cloud-contexts.json`、`eitr/cloud-navigation.json`）。
   - **WiFiネットワーク**（任意選択の機密項目、既定ではオフ）: 保存済みのiwd（`/var/lib/iwd/*.psk`、`*.8021x`、`*.open`）とNetworkManager（`/etc/NetworkManager/system-connections/*.nmconnection`）プロファイル（`pkexec` 経由で `/usr/lib/eitr/eitr-network` がエクスポート）。
2. 必要なら個別のアプリ設定やアプリ（ソース別・検索可能）のチェックを外します。
3. 保存先を選びます。外付けドライブが `~/Backups` より先に表示されます。同じディスクへの保存には警告が出て、空き容量不足の場合は書き込み前に拒否されます。
4. パスフレーズを2回入力します。パスフレーズがコマンド引数・環境変数・ファイルへ保存されることはありません。
5. **確認** 画面で内容（機密カテゴリや機密項目が含まれる場合は警告が表示されます）を確認し、**Enter** でアトミックに書き込みます（**Esc** で何も書かずに中止）。

### 自動で除外されるもの

- ブラウザープロファイル、各種キャッシュ、ロック/ソケット/一時ファイル。
- システム同梱コードや生成ファイル（復元後に再生成されます）。
- ログインキーリング、Git CLIトークン（`~/.config/gh`、`eitr/git-accounts/cli`）、および短期クラウドセッションキャッシュ: AWS SSO/CLIキャッシュ（`~/.aws/sso/cache`、`~/.aws/cli/cache`）、gcloudトークン/認証情報データベース（`~/.config/gcloud/access_tokens.db*`、`~/.config/gcloud/credentials.db*`、`legacy_credentials`、`logs`）、Azureトークンキャッシュ（`~/.azure/msal_token_cache*`、`accessTokens.json`、`msal_http_cache*`、`logs`、`telemetry`、`commands`）、Kubernetesディスカバリキャッシュ（`~/.kube/cache`、`~/.kube/http-cache`）。

## バックアップから復元する

1. アーカイブ（接続ドライブ、`~/Backups`、前回の保存先、または指定パス）を選び、パスフレーズを入力します。
2. 先に `manifest.json` を読み取り、ディスク変更前にカテゴリ・フォルダー・アプリの選択解除を行えます。
3. **確認** で確定します。上書き対象ファイルは事前に `~/.local/state/eitr/restore-backups/<id>/` にジャーナル付きで退避されます。
4. アプリは次の順で再インストールされます: 利用可能な公式パッケージを1回の `pacman` トランザクションで導入（見つからないものはスキップして一覧表示）、AURパッケージを `yay` で1つずつ導入、Flatpak、最後にEitrプラグインとStore項目を **通常のレビュー承認を通して** 導入（無言で自動導入しません）。
5. 通常ファイルが先に復元され、機密カテゴリは最後に復元されます。SSHとGPGのディレクトリは `0700`、SSH鍵（秘密鍵と `.pub`）・GPGファイル・クラウド設定は `0600` の権限を保ち、GPG鍵は `gpg --import` でインポートされ、WiFiプロファイルは `pkexec` 経由の `/usr/lib/eitr/eitr-network` により `root:root` `0600` で書き込まれます。
6. テーマと生成設定はディスプレイ別壁紙を保ったまま再構築され、Hyprlandが起動中なら再読み込みします。復元後、ブラウザーや短期クラウド/Git CLIセッション（`gh`, `gcloud`, `aws`, `az`）に再ログインしてください。

## 復元を取り消す (Undo)

```sh
eitr backup undo <id>
```

`<id>` は **設定 > システム > バックアップと復元** または `eitr-backup status` で確認できます。Undoは上書き前のファイル（機密ファイル、GPGキーリング、WiFiプロファイルを含む）を戻し、新規追加されたファイルを削除してテーマを再生成します。
ファイルを置き換える前に、復元先に同名のディレクトリがないか、親フォルダーがシンボリックリンクでないかなどを確認します。途中で止まった場合は、同じ一覧から取り消しポイントを探してください。

## CLIリファレンス

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

パスフレーズは `/dev/tty` での非表示入力または `--passphrase-fd N` で受け取ります。新しい未対応フォーマットのアーカイブは変更を行わずエラーで停止します。
