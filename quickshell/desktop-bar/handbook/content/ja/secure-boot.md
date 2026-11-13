# sbctlによるセキュアブート

Eitrではセキュアブートに関するドキュメントを提供していますが、**キーの登録やファイルの署名を自動で行うことは決してありません**。ここでの誤りは、マシンが起動しなくなったり画面が表示されなくなったりする原因となるため、ディスクのパスフレーズと[復元手順](RECOVERY.md)を手元に用意し、ファームウェア設定画面を開くことができるマシン上で、これらのステップを手動で実行してください。本ガイドの内容は、まだEitrテスト用実機ハードウェアでは検証されていません。

## 開始する前に

- UEFIブートのみ対応です。ファームウェア設定の開き方（多くはF2、Del、F12）を確認し、ファームウェア管理者パスワードを設定してください。設定しない場合、誰でもセキュアブートを再び無効化できてしまいます。
- TPMによるディスクロック解除が登録されている場合は、パスフレーズを用意しておいてください。キーの登録によってTPM PCR 7が変更されるため、次回の起動時にパスフレーズが1回要求されます。その後、TPMロック解除を再登録してください（Security → TPM Disk Unlock: 削除してから登録）。
- ファームウェア設定で、セキュアブートを**Setup Mode**（多くは「Clear keys」または「Reset to Setup Mode」）に設定してください。復元できないキーは削除しないでください。ほとんどのファームウェアには「Restore factory keys」があります。

## sbctlワークフロー

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s`はファイルをsbctlのデータベースに保存します。sbctlのpacmanフックは、カーネルやブートローダーのアップデート後に保存されたファイルに再署名します。変更ごとに`sudo sbctl verify`を実行し、ファームウェアでセキュアブートを有効にして再起動してください。`/var/lib/sbctl`はオフラインで非公開にバックアップしてください。ここには署名キーが保持されています。このリポジトリにコピーすることは決してしないでください。

## リスク

- **Option ROMとベンダーキー。** グラフィックカード、NVMeドライブ、ネットワークカードでは、MicrosoftのUEFI CAによって署名されたファームウェア（Option ROM）が動作していることがよくあります。`-m`を指定せずに自身のキーのみを登録すると、ファームウェアがそれらを拒絶する可能性があります。その結果、画面が表示されない、ブートディスクが認識されない、一部のノートPCではファームウェア設定に戻る手段すらなくなるという事態に陥ります。そのようなファームウェアがハードウェアに存在しないことが確実でない限り、`-m`を維持してください。代わりに`sbctl enroll-keys --tpm-eventlog`を使用すると、今回の起動で使用されたOption ROMのハッシュを追加できますが、ハードウェアやファームウェアのアップデートによって変化します。
- **未署名ファイル。** ブートパス内のすべてのEFIバイナリが自身のキーで署名されている必要があります。ファイルが1つでも欠けていると起動が停止します。復旧するにはファームウェアでセキュアブートを無効にしてください。
- **デュアルブート。** Windowsは`-m`を指定した場合にのみ起動を継続できます。

## ブートローダーとスナップショットエントリ

- **GRUB:** `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock`で再インストールし、新しい`grubx64.efi`と`/boot`内のカーネルに署名します。この設定ではGRUBはカーネルの署名をチェックしないため、grub-btrfsのスナップショットエントリは引き続き起動可能ですが、保護の範囲は各カーネルではなくGRUBバイナリに留まります。イメージが変更されるGRUBアップデートの後は、`grub-install`と`sbctl sign`を再実行してください。
- **Limine:** Limine EFIバイナリ（`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI`またはインストール先）に署名します。Limineは署名ではなくハッシュで設定とカーネルを保護します。バイナリに設定ハッシュを登録する場合（`limine enroll-config`）、limine-snapper-syncからの新しいスナップショットエントリを含む`limine.conf`への変更のたびに、再登録と再署名を行う必要があります。セキュアブートを有効にする前に、`limine-mkinitcpio-hook`設定がこれを行うようになっていることを確認してください（インストールされている場合はsbctlを使用します）。そうしないと、次のスナップショット同期でローダーがメニューを拒否するようになります。
- **systemd-boot:** `systemd-bootx64.efi`およびそれが読み込むカーネルまたは統合カーネルイメージ（UKI）に署名します。スナップショットブートエントリはサポートされていません。
- 古いカーネル用のスナップショットエントリも、ローダーのチェックにパスする必要があります。セキュアブートを有効にした後、実際に必要になる前にスナップショットエントリを1回起動して動作することを確認してください。

## 元に戻す手順

1. ファームウェア設定に入り、セキュアブートを無効化するか、「Restore factory keys」を選択してベンダーキーセットに戻します。インストールされたシステムは、セキュアブートがオフの状態で起動を継続できます。
2. 必要に応じて、`sudo sbctl remove-file <file>`でsbctlのデータベースから保存されたファイルを削除します。ファイル自体の署名は無害です。
3. セキュアブートが有効な状態でTPMロック解除を登録していた場合、PCR 7が再び変化します。パスフレーズを1回入力し、再登録してください。

参考資料: [sbctl](https://github.com/Foxboron/sbctl)、
[Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot)。
