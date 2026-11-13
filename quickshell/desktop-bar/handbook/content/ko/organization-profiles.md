# 조직 프로필

공식 ISO를 변경하지 않고 그대로 사용하세요. `EITRANSWERS`라는 레이블이 지정된 FAT32 USB 드라이브에서 `eitr-answers.json` 옆에 또는 그 대신 `eitr-profile.json`을 넣으세요. 프로필만 있는 경우 일반 마법사의 검토(Review) 단계에 변경 사항이 포함됩니다. 두 파일이 모두 있는 경우 설치 프로그램은 15초 카운트다운 전에 디스크 작업과 모든 프로필 변경 사항을 나열합니다. Ctrl+C를 누르면 디스크가 변경되기 전에 취소됩니다. 전원이 꺼질 때까지 USB 드라이브 연결을 유지하세요.

전체 예시(`sha256sum`의 실제 소문자 SHA-256으로 모든 예시 다이제스트를 교체하세요. 이 파일들을 USB 드라이브에 복사하세요):

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "eitr",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

`version`과 `name`만 필수입니다. 알 수 없거나 중복된 JSON 키는 오류로 처리됩니다. 필요하지 않은 선택적 섹션은 제거하세요. 경로는 USB 드라이브 기준 상대 경로여야 하며 심볼릭 링크, 상위 탐색(`..`) 또는 절대 경로는 허용되지 않습니다. 참조된 모든 파일은 설치 프로그램이 디스크를 변경하기 전에 존재해야 하고 체크섬과 일치해야 합니다. 배경화면 파일은 PNG, JPEG 또는 WebP로 디코딩되어야 합니다. 저장소 키에는 정확히 하나의 OpenPGP 공개 키가 포함되어야 합니다. HTTPS 서버에는 자격 증명이 포함될 수 없습니다. 해당 키는 pacman의 키링에 추가되고 로컬에서 신뢰됩니다. 신뢰하는 조직 키만 사용하세요. 패키지 아카이브 및 설치 스크립트는 샌드박스 처리되지 않는 신뢰할 수 있는 관리자 코드입니다.

`remove`는 검토된 `distro/removable-apps.json` 허용 목록만 수락합니다. 항목별 검토 내용은 `distro/PROFILE-PACKAGE-REVIEW.md`에 있습니다. 보호되거나 알 수 없는 패키지가 있으면 프로필 전체가 거부됩니다. pacman이 종속성을 확인하며, 재귀적 제거 또는 종속성 무시를 절대 사용하지 않습니다. 그룹 정책은 해당 그룹의 모든 허용 목록 패키지를 제외합니다: `gaming`, `media`, `development`, `sharing` 및 `remote_access`. `true`는 기능을 허용하고 `false`는 비활성화합니다. `update_channel` 정책은 `"stable"`만 허용합니다. 생략된 정책에는 제한이 없습니다.

`plugins`는 플러그인 메뉴를 숨기고 플러그인 추가, 업데이트 및 실행을 거부하는 `false`, 또는 해당 저장소만 허용하는 `{"allow": ["https://git.example.org/team/tools.git", "git@github.com:team/plugin.git"]}`를 허용합니다. 허용 목록 항목은 HTTPS 또는 SSH URL이며 스킴, 사용자, 포트, `.git` 접미사, 후행 슬래시 및 대소문자에 관계없이 일치합니다. `~/.ssh/config`의 SSH 호스트 별칭은 작성된 그대로 나열되어야 합니다. 설치된 시스템에 이러한 정책을 적용하면 더 이상 허용되지 않는 플러그인의 서비스를 중지하고 비활성화하며 해당 파일은 유지합니다.

레시피는 `distro/software.json`의 `group/name`을 사용합니다. 사전 빌드된 pacman 및 Flatpak 레시피만 허용됩니다. AUR 및 대화형 관리형/웹앱 레시피는 거부됩니다. 대신 검토된 사전 빌드 패키지 파일을 제공하세요. 저장소 패키지, 레시피 및 Flathub 추가 항목에는 인터넷이 필요합니다. USB 드라이브 패키지는 종속성이 이미 ISO에 있거나 USB 드라이브에도 제공되는 경우 오프라인으로 설치됩니다. 확인할 때 pacman의 현재 동기화 데이터베이스에서 패키지 이름을 사용할 수 있어야 합니다. 온라인 추가 항목을 확인하기 전에 일반 업데이트 워크플로를 통해 데이터베이스를 새로 고치세요. 설치 중에는 AUR 빌드가 실행되지 않습니다. 온라인 pacman 추가는 전체 업그레이드를 사용하며 부분 업그레이드는 절대 사용하지 않습니다. 추가 저장소는 향후 업데이트를 위해 구성됩니다. 해당 저장소에서만 사용할 수 있는 패키지는 설치를 위해 USB 드라이브 파일로 제공해야 합니다.

설치 중에 Flathub 앱과 Flatpak 레시피는 데스크톱 사용자를 위해 대기열에 추가되며 네트워크 연결이 있는 첫 시작 시 설치됩니다. 실패한 설치는 다음 부팅 시 다시 시도합니다. 이미 설치된 시스템에 프로필을 적용하면 직접 설치됩니다.

브라우저 기본값은 Firefox와 Chromium을 지원합니다. Chromium도 추가되어야 합니다. 테마 및 배경화면 기본값은 선택한 데스크톱 사용자의 다음 로그인을 위해 저장되며, 프로필 적용으로 인해 데스크톱이 다시 시작되지는 않습니다. 추가 저장소와 업데이트 채널은 시스템 전반에 적용됩니다. `setup`은 프로필이 기록된 후 준비된 USB 드라이브 디렉터리를 작업 디렉터리로 하여 root로 실행됩니다. 시작하기 전에 SHA-256 마커가 시도를 기록하므로 실패하거나 중단된 스크립트가 알림 없이 다시 실행되지 않습니다. 다른 시도를 승인하려면 스크립트(및 해당 다이제스트)를 변경하세요. 스크립트 출력과 실패는 열린 상태를 유지합니다. 설치 실패가 완료된 패키지 트랜잭션을 롤백하지는 않습니다.

설치된 머신에서:

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check`는 파일과 패키지 메타데이터를 읽고 임시 검증 디렉터리를 사용하며, 시스템 구성을 변경하지 않습니다. `apply`는 명시적인 root 소유의 `eitr-system profile-apply` 작업을 사용하고, USB 드라이브를 비공개로 스테이징하고 다시 확인하며, 동일한 요약을 표시한 다음 `APPLY PROFILE` 입력을 요구합니다. 취소하면 아무것도 변경되지 않습니다. pacman을 통해 설치된 제외 패키지를 제거하고, 추가 항목을 설치하며, 기본값을 저장하고, root 소유의 `/etc/eitr/policies.json`(0644, root:root)을 작성하고, `/etc/eitr/profile.json`을 기록합니다. 다른 프로필을 적용하면 기록된 선택 사항이 대체되며, 이전에 제거된 앱을 자동으로 다시 설치하거나 생략된 환경설정을 재설정하지는 않습니다. setup 마커는 프로필 교체 후에도 유지됩니다.

기록된 제외 항목은 수동 설치 프로그램 매니페스트를 필터링합니다. 또한 pacman 옵션의 `IgnorePkg` 포함은 System Update가 제외된 패키지를 종속성으로 다시 가져오는 것을 방지합니다. 이러한 종속성 충돌이 발생하면 업그레이드를 중지해야 합니다. 사용자 설정을 시드해도 애플리케이션은 설치되지 않습니다. 정책은 Elephant 메뉴/검색 행, 원격 접속(Remote Access) 바 항목, 어시스턴트 협업 스위치 및 채널 제어를 숨깁니다. Eitr의 도구도 이러한 작업을 직접 거부합니다. 기존 세션의 경우 새로 적용된 정책을 반영하기 위해 다음 메뉴/패널 새로고침이 필요할 수 있습니다.

**이는 root 권한이 있는 사용자에 대한 잠금(lockdown)이 아닙니다.** root는 정책을 편집하거나 다른 도구를 실행할 수 있습니다. 진정한 잠금은 root 권한을 부여하지 않는 것을 의미합니다. 정책은 임의의 서드파티 소프트웨어나 플릿 관리가 아니라 Eitr 워크플로를 관리합니다.

네트워크 연결 유무에 따른 설치, 거부된 프로필, 설치된 머신에 프로필 적용, 업그레이드, 숨겨진 제어 항목 및 모든 언어의 설치 프로그램 화면이 VM에서 통과되었습니다(`distro/PROFILE-VM-TESTING.md`).
