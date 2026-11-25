# 백업 및 복원

데스크톱 설정, 선택한 개인 폴더 및 설치된 앱 목록을 암호화된 단일 `.eitrbackup` 파일로 묶어 다른 PC나 새 Eitr 설치 환경으로 옮깁니다.

[복구 및 스냅샷](handbook:recovery)의 스냅샷은 업데이트 롤백을 위해 같은 디스크에 남습니다. 백업 및 복원은 `zstd`로 압축하고 `age` 암호로 보호된 휴대용 아카이브를 생성합니다.

## 백업 및 복원 열기

- **설정**: **SUPER + ,** 를 누르고 **시스템 > 백업 및 복원**을 엽니다.
- **Walker**: **SUPER + F**를 누르고 **설정 > 시스템 > 백업 및 복원**을 선택합니다.
- **터미널**: `eitr backup` (또는 `eitr-backup wizard`)을 실행합니다.

## 백업 만들기

1. 포함할 범주를 선택합니다:
   - **Eitr 설정**: 데스크톱 기본 설정, `~/.config/eitr/overrides` 재정의 파일, 사용자 테마·배경화면·잠금 화면.
   - **앱 설정**: `~/.config` 안의 비-Eitr 폴더(브라우저 프로필과 캐시 제외).
   - **개인 폴더**: 기본 선택 해제된 `$HOME` 최상위 폴더 및 `$HOME` 내부 하위 폴더용 **폴더 추가…**. 크기는 백그라운드에서 계산됩니다.
   - **설치된 앱**: 기본 Eitr 외에 추가한 공식 패키지, AUR, Flatpak, Eitr 플러그인 및 Store 항목 목록.
   - **기기 설정**: 기본 꺼짐; 이 PC에 종속된 디스플레이 및 `hypr/local.lua` 재정의.
   - **Git 계정** (선택형 비밀 범주, 기본 꺼짐): `eitr/git-accounts.json`, `eitr/git-accounts` 아래의 관리형 포함 파일, `~/.gitconfig`, 각 계정이 지정한 SSH 키(개인 키와 `.pub`, `0600` 권한 유지), `~/.ssh/config`, `~/.ssh/known_hosts`, 그리고 `gpg --export-secret-keys --armor`로 내보낸 GPG 비밀 키(GPG가 자체 암호를 직접 묻습니다).
   - **클라우드 계정** (선택형 비밀 범주, 기본 꺼짐): `~/.aws`, `~/.config/gcloud`, `~/.azure`, `~/.kube` 및 Eitr 클라우드 레이블(`eitr/cloud-contexts.json`, `eitr/cloud-navigation.json`).
   - **WiFi 네트워크** (선택형 비밀 범주, 기본 꺼짐): `pkexec`를 통해 `/usr/lib/eitr/eitr-network`로 내보내는 저장된 iwd(`/var/lib/iwd/*.psk`, `*.8021x`, `*.open`) 및 NetworkManager(`/etc/NetworkManager/system-connections/*.nmconnection`) 프로필.
2. 필요 시 개별 앱 설정 폴더 및 설치된 앱(검색·출처별 그룹화)의 체크를 해제합니다.
3. 대상 위치를 선택합니다. 외장 드라이브가 `~/Backups`보다 먼저 표시됩니다. 같은 디스크를 고르면 경고를 표시하며, 남은 공간이 부족하면 쓰기 전에 거부합니다.
4. 암호를 두 번 입력합니다. 암호는 명령 인수, 환경 변수, 파일 어디에도 저장되지 않습니다.
5. **검토** 화면에서 요약(비밀 범주와 항목이 포함되면 경고를 표시함)을 확인하고 **Enter**를 눌러 원자적으로 기록하거나 **Esc**로 기록 없이 취소합니다.

### 자동 제외 항목

- 브라우저 프로필, 캐시, 잠금/소켓/임시 파일.
- 배포된 시스템 코드, 기본값, 재생성 출력(복원 후 다시 생성됨).
- 로그인 키링, Git CLI 토큰(`~/.config/gh`, `eitr/git-accounts/cli`) 및 단기 클라우드 세션 캐시: AWS SSO/CLI 캐시(`~/.aws/sso/cache`, `~/.aws/cli/cache`), gcloud 토큰 및 자격 증명 데이터베이스(`~/.config/gcloud/access_tokens.db*`, `~/.config/gcloud/credentials.db*`, `legacy_credentials`, `logs`), Azure 토큰 캐시(`~/.azure/msal_token_cache*`, `accessTokens.json`, `msal_http_cache*`, `logs`, `telemetry`, `commands`), Kubernetes 검색 캐시(`~/.kube/cache`, `~/.kube/http-cache`).

## 백업에서 복원하기

1. 연결된 드라이브, `~/Backups`, 최근 백업 위치 또는 직접 입력 경로에서 아카이브를 선택하고 암호를 입력합니다.
2. 먼저 `manifest.json`만 읽어 디스크를 바꾸기 전에 범주·폴더·앱을 선택 해제할 수 있습니다.
3. **검토** 단계에서 확인합니다. 교체되는 기존 파일은 `~/.local/state/eitr/restore-backups/<id>/`에 저널과 함께 먼저 보관됩니다.
4. 패키지는 다음 순서로 다시 설치됩니다: 사용 가능한 공식 패키지는 단일 `pacman` 트랜잭션(누락된 항목은 건너뛰고 목록 표시), AUR 패키지는 `yay`로 하나씩(실패 시 계속 진행), Flatpak, 마지막으로 Eitr 플러그인과 Store 항목은 **일반 검토 승인을 거쳐** 설치됩니다.
5. 일반 파일이 먼저 복원되고 비밀 범주는 마지막에 복원됩니다: SSH 및 GPG 디렉터리는 `0700` 권한을, SSH 키(개인 키와 `.pub`)·GPG 파일·클라우드 설정은 `0600` 권한을 유지하며, GPG 키는 `gpg --import`로 가져오고 WiFi 프로필은 `pkexec`를 통한 `/usr/lib/eitr/eitr-network`로 `root:root` `0600` 권한으로 기록됩니다.
6. 복원된 모니터별 배경화면을 유지한 채 테마와 생성 구성을 다시 빌드하고, 실행 중이면 Hyprland를 다시 불러옵니다. 복원 후 브라우저와 단기 클라우드/Git CLI 세션(`gh`, `gcloud`, `aws`, `az`)에 다시 로그인하세요.

## 복원 되돌리기 (Undo)

```sh
eitr backup undo <id>
```

`<id>`는 **설정 > 시스템 > 백업 및 복원** 또는 `eitr-backup status`에서 확인할 수 있습니다. Undo는 덮어쓴 파일(비밀 파일, GPG 키링, WiFi 프로필 포함)을 되돌리고 새로 추가된 파일을 지운 뒤 테마를 재생성합니다.
파일을 바꾸기 전에 복원 대상의 충돌을 검사합니다. 대상 위치에 디렉터리가 있거나 상위 폴더가 심볼릭 링크인 경우가 포함됩니다. 복원이 중단되면 같은 목록에서 실행 취소 지점을 찾으세요.

## CLI 참고

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

암호는 `/dev/tty` 비표시 프롬프트 또는 `--passphrase-fd N`으로 전달합니다. 지원보다 상위 버전 형식의 아카이브는 파일을 건드리지 않고 거부됩니다.
