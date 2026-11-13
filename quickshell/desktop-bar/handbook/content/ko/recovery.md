# Eitr 복구 스냅샷

스냅샷은 복구 지점일 뿐, **외부 백업이 아닙니다**. 디스크가 고장 나면 시스템과 스냅샷이 함께 손상될 수 있습니다. 독립적인 백업을 유지하세요.

Eitr는 현재 동일한 루트 서브볼륨에 `/usr`, `/etc`, `/var/lib/pacman`이 있는 Btrfs 루트의 Snapper를 지원합니다. `/home`은 별도로 분리될 수 있으며 루트 스냅샷의 보호를 받지 않습니다. 지원되지 않는 레이아웃은 업그레이드 전에 실패로 처리되어 진행을 차단합니다. `install.sh`는 디스크를 포맷하거나 기존 서브볼륨을 재배치하지 않습니다. ISO의 `eitr-guided-install`만이 사용자가 확인한 디스크를 지우고 이 레이아웃을 생성합니다(README의 Guided install 섹션 참조).

## 업데이트 전

설치 프로그램은 `/etc/eitr/system-update-policy.conf`를 활성화합니다. 설정 → 업데이트 → 시스템 업데이트에서 공식 및 AUR 패키지를 업그레이드하기 전에 다음 작업을 수행합니다:

1. 지원되는 레이아웃 및 Snapper 루트 구성을 확인합니다.
2. `/boot` 및 `/efi`가 별도의 마운트인 경우에만 이를 아카이브합니다(Btrfs 루트 내부의 `/boot` 디렉터리는 이미 루트 스냅샷에 포함되어 있음). 아카이브는 루트 전용 접근 권한으로 `/var/lib/eitr/boot-backups/<snapshot-number>/` 아래에 저장됩니다.
3. 업그레이드 전 루트 스냅샷을 생성합니다.
4. 부팅 백업 또는 스냅샷 생성이 실패하면 업그레이드를 중단합니다.

업그레이드가 완료되거나 실패하거나 거부되면 워크플로는 해당하는 사후(post) 스냅샷을 생성합니다. 설명란에는 결과("after package upgrade", "after failed package upgrade")가 기록됩니다. 그 전에 워크플로가 강제 종료된 경우 다음 시스템 업데이트 시 먼저 "after interrupted package upgrade" 사후 스냅샷으로 남아 있는 사전(pre) 스냅샷을 닫습니다. 업그레이드가 실패하더라도 사전 스냅샷과 부팅 아카이브는 그대로 유지됩니다.
Flatpak, SDKMAN/NVM 런타임 및 별도의 홈 서브볼륨에 있는 파일에 대한 업데이트는 이러한 스냅샷으로 보호되지 않습니다. 터미널 명령 `eitr update pacman|aur|full` 및 직접 실행하는 pacman/yay 명령은 의도적으로 자동 스냅샷을 생성하지 않습니다. 수동으로 설치한 이전 Eitr 스냅샷 훅이 있는 경우 이 정책을 적용하려면 제거해야 합니다.

새 Snapper 구성은 정리 타이머를 통해 번호가 매겨진 일반 스냅샷을 최대 10개, 중요 스냅샷을 최대 5개까지 유지합니다. 기존 정책은 보존됩니다. 부팅 아카이브는 기본 스냅샷 제한에 맞춰 각 시스템 업데이트 시 최신 10개로 정리됩니다. Snapper가 스냅샷을 먼저 삭제하면 아카이브가 스냅샷보다 오래 남아 있을 수 있으므로 복원하기 전에 스냅샷이 존재하는지 확인하세요. 디스크 공간이 부족하면 보호 조치를 건너뛰는 대신 업데이트 진행을 방지합니다.

## 부트 가드

Eitr 가이드 설치 레이아웃에서 시스템 업데이트가 성공한 후, 부트 가드는 해당 업데이트의 "before" 스냅샷을 준비 상태로 유지합니다(`/var/lib/eitr/boot-guard.json`). `eitr-boot-guard.service`는 부팅 초기마다 시작 횟수를 계산하며, 로그인 화면이 45초 동안 유지되면 `eitr-boot-guard-healthy.service`가 정상 시작으로 간주하고 가드를 해제합니다.

업데이트 후 두 번 연속으로 해당 시점에 도달하지 못하면 세 번째 시작 시 공장 초기화의 검증된 단계를 사용하여 자동으로 복원합니다:

1. 오늘 사용하던 부팅 파일을 보관해 둔 뒤, 스냅샷의 부팅 파일(`/var/lib/eitr/boot-backups/<number>/boot.tar`)을 EFI 파티션으로 복사합니다.
2. 실패한 루트 서브볼륨은 `@eitr-guard-failed`로 이름이 변경되고, 스냅샷의 쓰기 가능한 복사본이 `@`가 되며, Snapper의 `.snapshots` 저장소가 그 안으로 이동합니다.
3. 컴퓨터가 복원된 시스템으로 재시작합니다. 어떤 단계라도 실패하면 서브볼륨과 부팅 파일이 원래대로 되돌아가며 아무것도 재시작되지 않습니다.

복원된 시스템은 로그인 화면에 도달하면 `@eitr-guard-failed`를 삭제하며, 다음 로그인 시 알림이 표시됩니다. 홈 폴더는 변경되지 않습니다. 커널 자체가 시작되지 않는 경우에는 부트 가드가 도움이 되지 못하므로, 대신 부팅 메뉴에서 해당 업데이트의 스냅샷으로 부팅하세요(아래 참조). 다른 디스크 레이아웃에는 가드가 활성화되지 않습니다.

## 인증 변경 사항

보안 → 지문/FIDO2 활성화는 `/etc/pam.d/hyprlock`, `sddm`, `sudo`를 편집하기 전에 `/var/lib/eitr/pam-backups/<timestamp>/` 아래에 백업하고, 쓰기가 하나라도 실패하면 세 항목 모두 복원합니다. 세 항목 모두에 지문이 추가되므로 "비밀번호 전용" 설정은 잠금 화면에도 적용됩니다. pam_fprintd로 인해 비밀번호 입력 프롬프트가 최대 10초까지 지연될 수 있습니다. 작동 중인 루트 셸 또는 TTY에서 이전 정책으로 되돌리려면 다음과 같이 실행하세요:

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## TPM 디스크 잠금 해제

보안 → TPM 디스크 잠금 해제를 사용하면 LUKS2 루트에 TPM2 키 슬롯을 추가하여 암호를 입력하지 않고도 부팅 시 디스크를 잠금 해제할 수 있습니다. 설치 프로그램에서는 아무것도 실행되지 않습니다. 루트 헬퍼(`luks-tpm-check`, `luks-recovery-key`, `luks-tpm-enroll`, `luks-tpm-remove`)는 장치가 LUKS2이고, `systemd-cryptenroll --tpm2-device=list`에 TPM2 장치가 표시되며, 암호 또는 복구 슬롯이 이미 존재하지 않는 한 작업을 거부합니다. 이 기능은 슬롯을 **추가**할 뿐이며 기존 암호는 그대로 유지됩니다.

- **복구 키 우선.** Walker 흐름에서 `systemd-cryptenroll --recovery-key`를 제공합니다. 키는 터미널에 한 번만 출력되며 저장되지 않습니다. 오프라인에 기록해 두세요. 일반 암호 프롬프트에서 작동합니다.
- **PCR 선택.** Eitr는 PCR 7(보안 부팅 상태 및 키)에 바인딩합니다. 펌웨어 업데이트로 변경되는 경우는 드물지만 보안 부팅 키 변경 시에는 바뀝니다. PCR 7은 사용자 고유 키로 보안 부팅이 활성화된 경우에만 상당한 보호를 제공합니다([SECURE-BOOT.md](SECURE-BOOT.md) 참조). 그렇지 않으면 누구든 편집된 커널 명령줄로 이 머신을 부팅하여 잠금 해제된 디스크에 접근할 수 있습니다. 더 강력한 보호를 원한다면 PIN을 사용하여 수동으로 등록하세요: `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`.
- **Initramfs.** busybox의 `encrypt` 훅은 TPM2 토큰을 사용할 수 없으므로 해당 훅이 구성되어 있는 동안에는 등록을 거부합니다. `HOOKS`에서 `systemd` 및 `sd-encrypt`로 전환하는 작업(커널 명령줄에서 `cryptdevice=`를 `rd.luks.name=<LUKS-UUID>=root`로 교체하거나 `/etc/crypttab.initramfs` 사용)은 부팅에 중요한 변경 사항이므로 Eitr가 사용자에게 맡깁니다. 변경을 적용하고 `sudo mkinitcpio -P`를 실행한 후 부팅 항목을 업데이트하고, TPM을 등록하기 **전에** 암호 부팅이 정상 작동하는지 확인하세요.

TPM 잠금 해제가 중단되는 경우(펌웨어 또는 보안 부팅 변경, TPM 초기화) 이전처럼 암호 프롬프트가 나타납니다. 암호를 입력한 후 등록을 제거하고 다시 등록하세요. 완전히 롤백하려면 TPM 잠금 해제 제거를 사용하거나 작동 중인 셸에서 다음을 실행하세요:

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## 공장 초기화

Eitr ISO로 설치된 컴퓨터는 Snapper 외부에 읽기 전용 첫 로그인 복원 지점도 유지합니다. Walker → 설정 → 시스템 → 유지 관리 → 공장 초기화를 사용하면 홈 폴더 파일의 유지 여부를 선택하여 해당 지점으로 되돌릴 수 있습니다. [FACTORY-RESET.md](FACTORY-RESET.md)를 참조하세요.

## 복구 지점 확인

Walker → 설정 → 시스템 → 유지 관리 → 스냅샷을 사용하거나 다음 읽기 전용 확인 명령을 실행하세요:

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

데스크톱이 실패하더라도 시스템이 여전히 부팅되는 경우 텍스트 콘솔로 전환하거나 직접 구성한 SSH 연결을 사용하세요. 부팅되지 않는 경우 공식 Arch 설치 프로그램 ISO를 사용하여 시스템의 Btrfs 파일 시스템을 마운트하세요. 변경하기 전에 올바른 디스크, 암호화 매핑, 루트 서브볼륨, 스냅샷 번호 및 EFI 마운트를 확인하세요. 다른 컴퓨터의 명령을 맹목적으로 복사하지 마세요.

## 홈 폴더 스냅샷

기본적으로 꺼져 있습니다. **Walker > 설정 > 시스템 > 유지 관리 > 스냅샷 > 홈 폴더 스냅샷**에서 켤 수 있습니다(먼저 확인을 요청하며, 끄면 스냅샷이 삭제됩니다). 활성화하면 Snapper의 `home` 구성이 하루 동안은 매시간, 일주일 동안은 하루에 한 번씩 `/home`의 스냅샷을 유지하며, 여유 공간이 20% 미만으로 떨어지면 가장 오래된 스냅샷부터 삭제합니다.

캐시, `~/Downloads`, 가상 머신(VM) 디스크 폴더(`~/.local/share/libvirt/images`, GNOME Boxes, `~/VirtualBox VMs`) 및 Steam 라이브러리는 제외됩니다. 다음 시작 시 아무도 로그인하기 전에 `eitr-home-exclusions.service`가 이들을 중첩된 Btrfs 서브볼륨으로 변환하며, 홈 스냅샷에는 포함되지 않습니다. 파일들은 유지됩니다(reflink되므로 이동 시 추가 공간을 차지하지 않음). 공장 초기화의 내 파일 유지 옵션은 이러한 서브볼륨을 복원된 홈으로 가져옵니다. 숨겨진 서브볼륨은 "Settings before reset" 폴더로 이동하며 캐시는 삭제됩니다. 서브볼륨을 이동할 수 없는 경우 이전 홈은 삭제되지 않고 검토를 위해 보존됩니다.

누락된 제외 폴더의 변환 및 생성은 해당 계정의 보조 그룹을 포함하여 홈 소유자 권한으로 실행됩니다. 심볼릭 링크된 홈 및 다른 파일 시스템의 경로는 거부됩니다. 심볼릭 링크이거나 심볼릭 링크된 폴더 아래에 있는 제외 폴더(예: 다른 디스크의 Downloads)는 그대로 유지되며 절대 추적되지 않습니다. 변환이 실패하면 설정은 보류 상태로 유지되고 검사를 위해 `NAME.eitr-subvolume` 또는 `NAME.eitr-old` 폴더가 남습니다. 원본 파일은 `NAME` 또는 `NAME.eitr-old`에 남아 있습니다. 잔여 항목을 제거하고 다시 시도하기 전에 이를 확인하세요. 특권 기반의 자동 정리는 시도되지 않습니다. 비어 있지 않은 Btrfs 서브볼륨을 소유자 권한으로 삭제하려면 일반적으로 `user_subvol_rm_allowed`가 필요하기 때문입니다.

**스냅샷 > 파일 또는 폴더 복원**(또는 `eitr restore PATH`)은 해당 경로를 포함하는 스냅샷을 나열하고 선택한 버전을 현재 버전 옆에 `NAME (restored DATE)` 형식으로 복사하거나, 삭제된 경우 원래 위치로 복원합니다. 어떤 파일도 덮어쓰지 않습니다.

## 각 업데이트의 변경 내용

롤백하기 전에 무엇이 취소되는지 확인하세요. **Walker > 설정 > 시스템 > 유지 관리 > 스냅샷 > 각 업데이트의 변경 내용**(또는 `eitr snapshots changes`)은 업그레이드, 다운그레이드, 설치 및 제거된 패키지 수와 함께 각 업데이트의 전/후 쌍을 나열합니다. `eitr snapshots changes <before number>`는 이전 버전과 새 버전이 포함된 단일 업데이트의 모든 패키지를 나열합니다. 두 스냅샷 내에 보관된 패키지 데이터베이스를 비교하며, 아직 사후(after) 스냅샷이 없는 업데이트는 실행 중인 시스템과 비교됩니다.

## 이전 스냅샷으로 부팅

GRUB 또는 Limine을 사용하면 부팅 메뉴에 읽기 전용 Snapper 스냅샷이 나열될 수 있으므로 라이브 미디어 없이도 문제가 발생한 업데이트를 검사하고 롤백할 수 있습니다. 설치 프로그램은 사용자가 `yes`를 입력한 경우에만 이를 제공합니다. 기존 설치 환경에서는 `bash distro/bootloader/setup.sh`를 실행하세요(`--check`는 상태만 보고함). 결과를 Walker → 설정 → 시스템 → 유지 관리 → 스냅샷 → 부팅 가능한 스냅샷 상태 또는 `sudo /usr/lib/eitr/eitr-system snapshots-boot-status`로 확인하세요.

| 부트로더 | 통합 | 패키지 (`distro/bootloader/`) |
|---|---|---|
| GRUB | Snapper가 스냅샷을 추가하거나 제거할 때마다 `grub-btrfsd.service`가 "Arch Linux snapshots" 하위 메뉴를 다시 빌드합니다 | `grub-btrfs`, `inotify-tools` (공식) |
| Limine | `limine-snapper-sync.service`가 `limine.conf`에 스냅샷 항목을 추가합니다 | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **지원되지 않음.** EFI/XBOOTLDR 파티션에서만 커널을 로드하며 Btrfs 스냅샷을 열 수 없습니다 | 아래의 라이브 미디어 절차를 사용하세요 |

감지 기능은 `/boot`, `/efi`, `/boot/efi` 아래의 GRUB, Limine 및 systemd-boot 파일을 읽습니다. 두 개 이상의 로더가 구성되어 있는 경우(예: GRUB 옆에 남아 있는 systemd-boot 파일) 설정은 임의로 추측하는 대신 작업을 거부합니다. 오래된 파일을 제거하거나 항목을 수동으로 구성하세요. 설정 시 먼저 현재 `grub.cfg`/`limine.conf`를 `/var/lib/eitr/boot-config-backups/<timestamp>/`에 복사하고 다음 부팅을 위해 서비스를 활성화합니다:

- **GRUB:** 설정 시 `grub-mkconfig -o /boot/grub/grub.cfg`를 한 번 실행합니다. `/boot`가 별도의 파티션인 경우 스냅샷 항목은 *현재* 커널로 부팅됩니다. 커널 업데이트 후에는 일치하는 부팅 아카이브(아래 참조)도 함께 복원하세요.
- **Limine:** `limine-snapper-sync`는 `limine-entry-tool`(`limine-mkinitcpio-hook` 제공)에 의해 생성된 항목을 관리하고 EFI 파티션에 각 스냅샷 커널의 복사본을 보관하므로 해당 파티션에 여유 공간이 필요합니다(업스트림 권장 사항: 4 GiB). `/etc/default/limine`(`SNAPPER_CONFIG_NAME="root"`, 감지되지 않는 경우 `ESP_PATH`)을 검토하고, `sudo limine-update`를 실행한 후 메뉴를 확인하고 `sudo systemctl start limine-snapper-sync.service`를 실행하세요. 부팅 메뉴를 다시 작성하므로 Eitr는 `limine-update`를 자동으로 실행하지 않습니다.

실행 취소하려면 서비스를 비활성화하고 백업을 다시 복사하세요. 예: `sudo systemctl disable grub-btrfsd.service` 및 `sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`.

### 읽기 전용 스냅샷

Snapper 스냅샷은 읽기 전용입니다. 그대로 부팅된 스냅샷은 `/var`에 쓸 수 없으므로 SDDM 및 기타 서비스가 실패할 수 있습니다. 그래픽 로그인이 시작되지 않으면 텍스트 콘솔(Ctrl+Alt+F3)에서 로그인하세요. initramfs 오버레이를 사용하면 부팅된 스냅샷을 RAM에서 쓰기 가능하게 만듭니다(변경 사항은 재부팅 시 사라짐). Eitr는 `HOOKS`를 편집하지 않습니다. 사용자가 직접 추가한 후 재생성해야 하며, 그 이후에 생성된 스냅샷에만 이 훅이 포함된다는 점에 유의하세요:

- GRUB: `/etc/mkinitcpio.conf`의 `HOOKS=(...)`에 `grub-btrfs-overlayfs`를 추가한 후 `sudo mkinitcpio -P`를 실행합니다.
- Limine: `filesystems` 뒤에 `btrfs-overlayfs`(또는 systemd 훅을 사용하는 경우 `sd-btrfs-overlayfs`)를 추가한 후 `sudo limine-update`를 실행합니다.

### 영구 롤백

1. 부팅 메뉴의 스냅샷 목록에서 최신 "before package upgrade" 스냅샷을 선택하고 시스템이 정상 작동하는지 확인합니다.
2. **Limine:** `sudo limine-snapper-restore`를 실행하고 해당 스냅샷을 선택합니다. 구성된 `RESTORE_METHOD`로 복원되며 교체된 시스템에 대한 백업 항목을 추가하므로 부팅 메뉴에서 복원 작업 자체를 되돌릴 수 있습니다.
3. **GRUB:** `snapper rollback`은 루트가 Btrfs 기본 서브볼륨을 통해 마운트된 경우에만 작동합니다. Arch 레이아웃은 일반적으로 `rootflags=subvol=@`로 부팅되므로(`findmnt -no OPTIONS /` 및 `/etc/fstab` 확인) 롤백이 적용되지 않습니다. 최상위 파일 시스템의 서브볼륨 목록을 검사한 후 라이브 미디어에서 루트 서브볼륨을 교체하세요. 다음 예시는 Snapper가 중첩된 `@/.snapshots` 서브볼륨을 생성한 Eitr의 가이드 설치 레이아웃**에만** 해당하며, 다른 레이아웃에는 실제 경로가 필요합니다:

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   명령이 하나라도 실패하면 중지하고 점검하세요. 보존된 루트를 삭제하지 마세요. 복원된 루트 아래에 스냅샷 저장소가 있는지 확인하고 진행하기 전에 fstab을 검토하세요. `/boot`가 별도로 분리되어 있다면 일치하는 `/var/lib/eitr/boot-backups/<number>/` 아카이브를 복원하고, 일반 항목으로 재부팅하여 `sudo grub-mkconfig -o /boot/grub/grub.cfg`를 실행하며, 복원된 시스템이 확인된 후에만 `sudo btrfs subvolume delete`로 `@.broken`을 삭제하세요.

## 라이브 미디어에서 안전하게 복구

1. 필요한 최신 파일을 백업합니다. Btrfs 최상위 파일 시스템을 마운트하고 서브볼륨 목록을 검사하여 선택한 스냅샷의 `snapshot` 서브볼륨을 찾습니다. 경로는 `.snapshots`가 마운트된 위치에 따라 다릅니다.
2. 실패한 루트 서브볼륨의 이름을 변경하여 보존합니다. 설치된 부트로더의 rootflags 및 fstab과 일치하도록 원래 루트 서브볼륨 경로에 선택한 복구 스냅샷의 **쓰기 가능한 Btrfs 스냅샷**을 만듭니다.
3. 복원된 루트와 실제 부팅/EFI 파티션을 마운트합니다. 커널/initramfs/부트로더 파일이 변경된 경우 일치하는 부팅 아카이브를 복원합니다. 아카이브는 선택한 루트 스냅샷과 일치해야 합니다. 최신 커널과 이전 모듈을 혼용하지 마세요.
4. fstab 및 부트로더 구성을 검토한 다음 해당 시스템에 필요에 따라 `arch-chroot`에서 initramfs를 재생성하거나 부팅 항목을 복구합니다. 루트와 부팅 파일이 일치한 후에만 재부팅하세요.

이것은 레이아웃을 고려한 수동 복구 절차이며 **검증된 원클릭 롤백 구현이 아닙니다**. Snapper의 `rollback` 명령만으로는 임의의 Arch 서브볼륨/부트로더 레이아웃에 충분하지 않습니다. 위의 GRUB 및 Limine 스냅샷 항목은 자동 복구를 지원한다고 확언하기 전에 실제 하드웨어에서의 검증이 여전히 필요합니다.

참고 자료: [grub-btrfs](https://github.com/Antynea/grub-btrfs), [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync), [Snapper 복구 개념](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html), [Arch 설치 가이드](https://wiki.archlinux.org/title/Installation_guide).
