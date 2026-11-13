# Eitrの復元スナップショット

スナップショットは復旧ポイントであり、**別マシンへのバックアップではありません**。ディスク障害が発生すると、システムとスナップショットの両方が同時に失われる可能性があります。独立したバックアップを必ず保持してください。

Eitrは現在、`/usr`、`/etc`、`/var/lib/pacman`が同一のルートサブボリューム内に存在するBtrfsルート上のSnapperをサポートしています。`/home`は別になっている場合もありますが、その場合はルートスナップショットの対象にはなりません。サポートされていないレイアウトでは、アップグレード前に安全のため処理が中断されます。`install.sh`はディスクのフォーマットや既存のサブボリュームの再構成を行いません。確認後にディスクを消去してこのレイアウトを作成するのは、ISOの`eitr-guided-install`のみです（READMEのGuided installセクションを参照してください）。

## アップデート前

インストーラーは`/etc/eitr/system-update-policy.conf`を有効化します。Settings → Updates → System Updateが公式パッケージおよびAURパッケージをアップグレードする前に、以下の処理を実行します。

1. サポートされているレイアウトとSnapperルート構成を検証します。
2. `/boot`と`/efi`が個別のマウントである場合にのみアーカイブします（Btrfsルート内の`/boot`ディレクトリはすでにルートスナップショットに含まれています）。アーカイブはrootのみアクセス可能な`/var/lib/eitr/boot-backups/<snapshot-number>/`に保存されます。
3. アップグレード前のルートスナップショットを作成します。
4. ブートバックアップまたはスナップショットの作成に失敗した場合はアップグレードを中止します。

アップグレードが完了、失敗、または拒絶された場合、ワークフローは対応する事後（post）スナップショットを作成します。その説明文には結果が記録されます（"after package upgrade"、"after failed package upgrade"）。それ以前にワークフローが強制終了された場合、次回のSystem Updateではまず残された事前（pre）スナップショットを"after interrupted package upgrade"事後スナップショットで閉じます。アップグレードが失敗した場合でも、事前スナップショットとブートアーカイブは保持されます。
Flatpak、SDKMAN/NVMランタイム、個別のhomeサブボリューム上のファイルへの更新は、これらのスナップショットでは保護されません。ターミナルコマンド`eitr update pacman|aur|full`および直接のpacman/yayコマンドは意図的に自動スナップショットを作成しません。手動でインストールされた古いEitrスナップショットフックがある場合は、このポリシーを適用するために削除する必要があります。

新しいSnapper構成では、クリーンアップタイマーを通じて最大10個の通常スナップショットと5個の重要番号付きスナップショットが保持されます。既存のポリシーは維持されます。ブートアーカイブはSystem Updateごとにデフォルトのスナップショット制限に合わせて最新の10個に削減されます。Snapperが先にスナップショットを削除した場合、アーカイブの方が長く残ることがあるため、復元前にスナップショットが存在することを確認してください。ディスク容量が不足している場合は、保護をスキップするのではなくアップデートが防止されます。

## ブートガード

Eitrのガイド付きインストールレイアウトでSystem Updateが成功すると、ブートガードはそのアップデートの「更新前」スナップショットを待機状態に保ちます（`/var/lib/eitr/boot-guard.json`）。`eitr-boot-guard.service`は起動の早い段階で各起動をカウントし、`eitr-boot-guard-healthy.service`はログイン画面が45秒間維持された時点で正常な起動としてカウントし、ガードを解除します。

アップデート後に2回連続でその状態に達しなかった場合、3回目の起動時に初期状態へのリセットでテスト済みの手順を使用して自動的に復元されます。

1. スナップショットのブートファイル（`/var/lib/eitr/boot-backups/<number>/boot.tar`）がEFIパーティションにコピーされます（元に戻せるよう現在のブートファイルを保持した上で行われます）。
2. 失敗したルートサブボリュームは`@eitr-guard-failed`にリネームされ、スナップショットの書き込み可能なコピーが`@`になり、Snapperの`.snapshots`ストレージがその中に移動されます。
3. コンピューターが復元されたシステムで再起動します。いずれかのステップが失敗した場合、サブボリュームとブートファイルは元の状態に戻され、再起動は行われません。

復元されたシステムはログイン画面に到達した時点で`@eitr-guard-failed`を削除し、次回のログイン時に通知を表示します。ホームフォルダには一切手が加えられません。カーネル自体が起動しない場合はガードが機能しません。その場合は代わりにブートメニューからアップデートのスナップショットを起動してください（後述）。その他のディスクレイアウトではブートガードは有効化されません。

## 認証の変更

Security → Enable Fingerprint/FIDO2は、編集前に`/etc/pam.d/hyprlock`、`sddm`、`sudo`を`/var/lib/eitr/pam-backups/<timestamp>/`にバックアップし、いずれかの書き込みに失敗した場合は3つすべてを復元します。指紋認証は3つすべてに追加されるため、「パスワードのみ」はロック画面にも適用されます。pam_fprintdによってパスワードプロンプトが最大10秒遅延する場合があります。動作するrootシェルまたはTTYから以前のポリシーに戻すには:

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## TPMによるディスクのロック解除

Security → TPM Disk Unlockを使用すると、LUKS2ルートにTPM2キースロットを追加して、パスフレーズを入力せずに起動時にディスクのロックを解除できます。インストーラーから実行されるものはここにはありません。rootヘルパー（`luks-tpm-check`、`luks-recovery-key`、`luks-tpm-enroll`、`luks-tpm-remove`）は、デバイスがLUKS2であり、`systemd-cryptenroll --tpm2-device=list`によってTPM2デバイスが一覧表示され、パスフレーズまたはリカバリスロットがすでに存在する場合にのみ処理を許可します。これはスロットを**追加**するだけであり、パスフレーズはそのまま残ります。

- **リカバリキーを最初に作成。** Walkerのフローで`systemd-cryptenroll --recovery-key`が提示されます。キーはターミナルに一度だけ表示され、保存されることはありません。オフラインで書き留めておいてください。通常のパスフレーズプロンプトで使用できます。
- **PCRの選択。** EitrはPCR 7（セキュアブートの状態とキー）にバインドします。ファームウェアのアップデートで変更されることはほとんどありませんが、セキュアブートのキー変更では変化します。PCR 7は、独自のキーでセキュアブートが有効になっている場合にのみ実質的な保護を提供します（[SECURE-BOOT.md](SECURE-BOOT.md)を参照）。そうでなければ、誰でも編集されたカーネルコマンドラインでこのマシンを起動し、ロック解除されたディスクを取得できてしまいます。より強固な保護を得るには、PINを指定して手動で登録してください: `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`。
- **Initramfs。** busyboxの`encrypt`フックはTPM2トークンを使用できないため、これが構成されている間は登録が拒否されます。`HOOKS`で`systemd`および`sd-encrypt`に切り替えること（カーネルコマンドラインの`cryptdevice=`を`rd.luks.name=<LUKS-UUID>=root`に置き換えるか、`/etc/crypttab.initramfs`を使用）は、Eitrではユーザー自身に委ねられているブートに関わる重要な変更です。変更を行い、`sudo mkinitcpio -P`を実行してブートエントリを更新し、TPMを登録する**前**にパスフレーズによる起動が1回正常に機能することを確認してください。

TPMによるロック解除が機能しなくなった場合（ファームウェアやセキュアブートの変更、TPMリセットなど）、以前と同様にパスフレーズプロンプトが表示されます。パスフレーズを入力し、一度削除してから再登録してください。完全にロールバックするには、Remove TPM Unlockを使用するか、動作するシェルから以下を実行します:

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## 初期状態にリセット

Eitr ISOでインストールされたコンピューターには、Snapperの外部に初回ログイン時の読み取り専用の復旧ポイントも保持されています。Walker → Settings → System → Maintenance → Factory Resetで、ホームフォルダファイルの有無を選択してそこに戻すことができます。[FACTORY-RESET.md](FACTORY-RESET.md)を参照してください。

## 復元ポイントの確認

Walker → Settings → System → Maintenance → Snapshotsを使用するか、以下の読み取り専用チェックを実行します:

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

デスクトップは起動しないもののシステムはまだ起動する場合は、テキストコンソールに切り替えるか、自身で設定したSSH接続を使用してください。起動しない場合は、公式のArchインストーラーISOを使用してシステムのBtrfsファイルシステムをマウントしてください。変更を行う前に、正しいディスク、暗号化マッピング、ルートサブボリューム、スナップショット番号、EFIマウントを特定してください。他のマシンのコマンドを盲目的にコピーしないでください。

## ホームフォルダのスナップショット

デフォルトではオフになっています。**Walker > Settings > System > Maintenance > Snapshots > Home Folder Snapshots**で有効化できます（事前に確認が表示され、オフにすると削除されます）。Snapperの`home`構成によって`/home`のスナップショットが1日間は毎時、1週間は毎日保持され、空き容量が20%を下回ると最も古いものが削除されます。

キャッシュ、`~/Downloads`、VMディスクフォルダ（`~/.local/share/libvirt/images`、GNOME Boxes、`~/VirtualBox VMs`）、Steamライブラリは除外されます。次回起動時、誰かがログインする前に`eitr-home-exclusions.service`によってこれらがネストされたBtrfsサブボリュームに変換され、ホームスナップショットには含まれなくなります。それらのファイルは保持されます（reflinkされるため、移動に追加の容量はかかりません）。初期状態へのリセットの「個人用ファイルを保持」では、これらのサブボリュームが復元後のホームに引き継がれます（隠し項目は「Settings before reset」フォルダに移動され、キャッシュは破棄されます）。移動できないものがある場合、以前のホームは削除されずに確認のために保持されます。

変換および不足している除外フォルダの作成は、そのアカウントの補助グループを含め、ホームの所有者として実行されます。シンボリックリンクされたホームや別ファイルシステム上のパスは拒絶されます。シンボリックリンクである除外フォルダ、またはシンボリックリンクされたフォルダの下にある除外フォルダ（別ディスク上のDownloadsなど）はそのまま残され、たどられることはありません。変換に失敗した場合、セットアップは保留状態のままとなり、調査用に`NAME.eitr-subvolume`または`NAME.eitr-old`フォルダが残されます。元のファイルは`NAME`または`NAME.eitr-old`に残ります。残骸を削除して再試行する前にこれらを確認してください。特権による自動クリーンアップは試行されません。空でないBtrfsサブボリュームを所有者として削除するには、通常`user_subvol_rm_allowed`が必要です。

**Snapshots > Restore a File or Folder**（または`eitr restore PATH`）は、そのパスを含むスナップショットを一覧表示し、選択したバージョンを現在のものの隣に`NAME (restored DATE)`としてコピーするか、削除されていた場合は元の場所に戻します。何かが上書きされることは決してありません。

## 各アップデートでの変更内容

ロールバックする前に、元に戻す内容を確認してください。**Walker > Settings > System > Maintenance > Snapshots > What Each Update Changed**（または`eitr snapshots changes`）は、各アップデートの更新前/更新後ペアと、アップグレード、ダウングレード、新規インストール、削除されたパッケージの数を一覧表示します。`eitr snapshots changes <before number>`は、特定のアップデートの全パッケージを新旧バージョンとともに一覧表示します。これは2つのスナップショット内に保持されているパッケージデータベースを比較します。まだ更新後スナップショットがないアップデートは、稼働中のシステムと比較されます。

## 以前のスナップショットからの起動

GRUBまたはLimineを使用すると、ブートメニューに読み取り専用のSnapperスナップショットを一覧表示できるため、ライブメディアを使用せずに問題のあるアップデートを調査してロールバックできます。インストーラーでは、`yes`と入力した後にのみこれが提示されます。既存のインストールでは、`bash distro/bootloader/setup.sh`を実行してください（`--check`はレポートのみを行います）。結果はWalker → Settings → System → Maintenance → Snapshots → Bootable Snapshot Status、または`sudo /usr/lib/eitr/eitr-system snapshots-boot-status`で確認できます。

| ブートローダー | 連携 | パッケージ（`distro/bootloader/`） |
|---|---|---|
| GRUB | Snapperがスナップショットを追加または削除するたびに、`grub-btrfsd.service`が「Arch Linux snapshots」サブメニューを再構築します | `grub-btrfs`、`inotify-tools`（公式） |
| Limine | `limine-snapper-sync.service`が`limine.conf`にスナップショットエントリを追加します | `limine-snapper-sync`、`limine-mkinitcpio-hook`（AUR） |
| systemd-boot | **非対応。** EFI/XBOOTLDRパーティションからのみカーネルをロードし、Btrfsスナップショットを開くことはできません | 後述のライブメディア手順を使用してください |

検出処理は、`/boot`、`/efi`、`/boot/efi`配下のGRUB、Limine、systemd-bootのファイルを読み取ります。複数のローダーが構成されている場合（例えばGRUBの横に残されたsystemd-bootファイルなど）、推測するのではなくセットアップが中止されます。古いファイルを削除するか、手動でエントリを構成してください。セットアップはまず現在の`grub.cfg`/`limine.conf`を`/var/lib/eitr/boot-config-backups/<timestamp>/`にコピーし、次回の起動に向けてサービスを有効化します。

- **GRUB:** セットアップは`grub-mkconfig -o /boot/grub/grub.cfg`を1回実行します。`/boot`が個別のパーティションである場合、スナップショットエントリは*現在*のカーネルを起動します。カーネルアップデートの後は、一致するブートアーカイブ（後述）も復元してください。
- **Limine:** `limine-snapper-sync`は`limine-entry-tool`（`limine-mkinitcpio-hook`付属）によって作成されたエントリを管理し、各スナップショットのカーネルのコピーをEFIパーティションに保持するため、そのパーティションに十分な空き容量が必要です（アップストリームでは4 GiBを推奨）。`/etc/default/limine`（`SNAPPER_CONFIG_NAME="root"`、未検出の場合は`ESP_PATH`）を確認し、`sudo limine-update`を実行してメニューを確認し、その後`sudo systemctl start limine-snapper-sync.service`を実行してください。Eitrはブートメニューを書き換えるため、代わりに`limine-update`を実行することはありません。

元に戻すには、サービスを無効化してバックアップをコピーして戻します。例えば`sudo systemctl disable grub-btrfsd.service`および`sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`を実行します。

### 読み取り専用スナップショット

Snapperのスナップショットは読み取り専用です。そのまま起動されたスナップショットは`/var`に書き込みができないため、SDDMやその他のサービスが失敗する可能性があります。グラフィカルログインが開始されない場合は、テキストコンソール（Ctrl+Alt+F3）でログインしてください。initramfsオーバーレイを使用すると、起動されたスナップショットをRAM上で書き込み可能にできます（変更は再起動時に消去されます）。Eitrは`HOOKS`を編集しません。自身で追加して再生成してください。なお、フックが含まれるのはその後作成されたスナップショットのみであることに注意してください:

- GRUB: `/etc/mkinitcpio.conf`の`HOOKS=(...)`に`grub-btrfs-overlayfs`を追加し、`sudo mkinitcpio -P`を実行します。
- Limine: `filesystems`の後に`btrfs-overlayfs`を追加し（またはsystemdフックを使用している場合は`sd-btrfs-overlayfs`）、`sudo limine-update`を実行します。

### 恒久的なロールバック

1. ブートメニューのスナップショット一覧から最新の「before package upgrade」スナップショットを選択し、そこでシステムが正常に動作することを確認します。
2. **Limine:** `sudo limine-snapper-restore`を実行してスナップショットを選択します。設定された`RESTORE_METHOD`で復元され、置き換えられたシステムのバックアップエントリが追加されるため、復元自体をブートメニューから元に戻すことができます。
3. **GRUB:** `snapper rollback`は、ルートがBtrfsのデフォルトサブボリュームを通じてマウントされている場合にのみ機能します。Archのレイアウトは通常`rootflags=subvol=@`で起動するため（`findmnt -no OPTIONS /`および`/etc/fstab`を確認）、rollbackを実行しても効果がありません。最上位ファイルシステムのサブボリュームリストを確認した上で、ライブメディアからルートサブボリュームを置き換えてください。以下の例は、Snapperがネストされた`@/.snapshots`サブボリュームを作成したEitrのガイド付きインストールレイアウト**専用**です。他のレイアウトでは実際のパスに合わせる必要があります:

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   いずれかのコマンドが失敗した場合は停止して調査し、保持されているルートを削除しないでください。復元されたルートの下にスナップショットストアが存在することを確認し、先に進む前にそのfstabを確認してください。`/boot`が別個の場合は、一致する`/var/lib/eitr/boot-backups/<number>/`アーカイブを復元し、通常のエントリで再起動し、`sudo grub-mkconfig -o /boot/grub/grub.cfg`を実行し、復元されたシステムが確認された後にのみ`sudo btrfs subvolume delete`で`@.broken`を削除してください。

## ライブメディアからの安全な復旧

1. 必要な新しいファイルをバックアップします。Btrfs最上位ファイルシステムをマウントしてサブボリュームリストを確認し、選択したスナップショットの`snapshot`サブボリュームを見つけます。パスは`.snapshots`がどこにマウントされているかによって異なります。
2. 失敗したルートサブボリュームをリネームして保持します。インストールされているブートローダーのrootflagsとfstabに合わせて、元のルートサブボリュームのパスに、選択した復元スナップショットの**書き込み可能なBtrfsスナップショット**を作成します。
3. その復元されたルートと実際のboot/EFIパーティションをマウントします。カーネル/initramfs/ブートローダーファイルが変更されている場合は、一致するブートアーカイブを復元します。アーカイブは選択したルートスナップショットと一致していなければなりません。新しいカーネルと古いモジュールを決して混在させないでください。
4. fstabとブートローダー構成を確認し、そのマシンに必要な応じて`arch-chroot`からinitramfsを再生成するかブートエントリを修復します。ルートとブートファイルの一致が確認できた後にのみ再起動してください。

これはレイアウトを意識した手動の復旧手順であり、**検証済みのワンクリックロールバック実装ではありません**。Snapperの`rollback`コマンド単体では、任意のArchサブボリューム/ブートローダーレイアウトに対して不十分です。上記のGRUBおよびLimineスナップショットエントリも、自動復旧を謳う前に実機での検証が依然として必要です。

参考資料: [grub-btrfs](https://github.com/Antynea/grub-btrfs)、
[limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync),
[Snapper recovery concepts](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html)、
[Arch installation guide](https://wiki.archlinux.org/title/Installation_guide)。
