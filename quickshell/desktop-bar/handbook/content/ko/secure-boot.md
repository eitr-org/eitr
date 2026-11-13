# sbctl을 사용한 Secure Boot

Eitr는 Secure Boot에 대해 설명하지만 **사용자를 대신하여 키를 등록하거나 파일에 서명하지 않습니다**. 여기서 실수가 발생하면 컴퓨터가 부팅되지 않거나 화면이 전혀 나오지 않을 수 있으므로, 펌웨어 설정에 접근할 수 있는 컴퓨터에서 디스크 암호문과 [복구 지침](RECOVERY.md)을 준비한 후 이 단계를 직접 수행하세요. 이 가이드의 내용은 아직 Eitr 테스트 하드웨어에서 검증되지 않았습니다.

## 시작하기 전에

- UEFI 부팅 전용입니다. 펌웨어 설정을 여는 방법(주로 F2, Del 또는 F12)을 확인하고 펌웨어 관리자 비밀번호를 설정하세요. 그렇지 않으면 누구나 Secure Boot를 다시 끌 수 있습니다.
- TPM 디스크 잠금 해제가 등록되어 있다면 암호문을 준비해 두세요. 키를 등록하면 TPM PCR 7이 변경되므로 다음 부팅 시 암호문을 한 번 묻습니다. 그 후 TPM 잠금 해제를 다시 등록하세요(보안 → TPM 디스크 잠금 해제: 제거 후 등록).
- 펌웨어 설정에서 Secure Boot를 **Setup Mode**(주로 "Clear keys" 또는 "Reset to Setup Mode")로 전환하세요. 복원할 수 없는 키는 삭제하지 마세요. 대부분의 펌웨어에는 "Restore factory keys" 옵션이 있습니다.

## sbctl 워크플로

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s`는 파일을 sbctl의 데이터베이스에 저장합니다. sbctl의 pacman 후크는 커널 및 부트로더 업데이트 후 저장된 파일에 다시 서명합니다. 변경할 때마다 `sudo sbctl verify`를 실행한 다음, 펌웨어에서 Secure Boot를 활성화하고 재부팅하세요. `/var/lib/sbctl`을 오프라인에서 안전하게 백업하세요. 여기에는 서명 키가 저장됩니다. 이 저장소에 절대 복사하지 마세요.

## 위험 요소

- **Option ROM 및 공급업체 키.** 그래픽 카드, NVMe 드라이브 및 네트워크 카드는 Microsoft의 UEFI CA가 서명한 펌웨어(Option ROM)를 실행하는 경우가 많습니다. `-m` 없이 자체 키만 등록하면 펌웨어가 이를 거부하여 디스플레이가 나오지 않거나, 부팅 디스크가 인식되지 않으며, 일부 노트북에서는 펌웨어 설정으로 돌아갈 수 없게 될 수 있습니다. 하드웨어에 이러한 펌웨어가 없다는 것을 확실히 알지 못한다면 `-m`을 유지하세요. 대신 `sbctl enroll-keys --tpm-eventlog`를 사용하여 이번 부팅에 사용된 Option ROM의 해시를 추가할 수도 있지만, 하드웨어나 펌웨어 업데이트 시 해시가 변경됩니다.
- **서명되지 않은 파일.** 부팅 경로의 모든 EFI 바이너리는 사용자의 키로 서명되어야 합니다. 누락된 파일이 있으면 부팅이 중단됩니다. 복구하려면 펌웨어에서 Secure Boot를 비활성화하세요.
- **듀얼 부팅.** Windows는 `-m`이 있어야만 계속 부팅됩니다.

## 부트로더 및 스냅샷 항목

- **GRUB:** `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock` 명령으로 다시 설치한 후 새 `grubx64.efi` 및 `/boot`의 커널에 서명하세요. 이 설정에서 GRUB은 커널 서명을 확인하지 않으므로 grub-btrfs 스냅샷 항목이 계속 부팅되지만, 보호 범위는 각 커널이 아닌 GRUB 바이너리로 한정됩니다. 이미지를 변경하는 GRUB 업데이트 후에는 `grub-install` 및 `sbctl sign`을 다시 실행하세요.
- **Limine:** Limine EFI 바이너리(`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` 또는 설치된 위치)에 서명하세요. Limine은 서명 대신 해시로 구성 및 커널을 보호합니다. 바이너리에 구성 해시를 등록하면(`limine enroll-config`), limine-snapper-sync의 새 스냅샷 항목을 포함하여 `limine.conf`가 변경될 때마다 다시 등록하고 서명해야 합니다. Secure Boot를 활성화하기 전에 `limine-mkinitcpio-hook` 설정이 이를 수행하는지 확인하세요(설치된 경우 sbctl을 사용함). 그렇지 않으면 다음 스냅샷 동기화 시 로더가 메뉴를 거부하게 됩니다.
- **systemd-boot:** `systemd-bootx64.efi` 및 로드되는 커널이나 통합 커널 이미지에 서명하세요. 스냅샷 부팅 항목은 지원하지 않습니다.
- 이전 커널의 스냅샷 항목도 로더의 검사를 통과해야 합니다. Secure Boot를 활성화한 후, 실제로 필요해지기 전에 스냅샷 항목으로 한 번 부팅하여 정상 작동하는지 확인하세요.

## 실행 취소

1. 펌웨어 설정으로 들어가 Secure Boot를 비활성화하거나, "Restore factory keys"를 선택하여 공급업체 키 세트로 되돌립니다. Secure Boot를 끄면 설치된 시스템이 계속 부팅됩니다.
2. 선택 사항으로 `sudo sbctl remove-file <file>`을 사용하여 sbctl 데이터베이스에서 저장된 파일을 제거할 수 있습니다. 파일 자체에 남은 서명은 무해합니다.
3. Secure Boot가 켜져 있는 동안 TPM 잠금 해제가 등록되었다면 PCR 7이 다시 변경됩니다. 암호문을 한 번 입력하고 다시 등록하세요.

참고 자료: [sbctl](https://github.com/Foxboron/sbctl), [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
