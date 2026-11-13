# 터미널 및 편집기

**SUPER + Enter**는 선택한 터미널(기본값은 Kitty)을 엽니다. **SUPER + Ctrl + Enter**는 기본
tmux 세션을 열거나 연결합니다. **SUPER + P**는 파일 유사 검색을 실행하며, **SUPER + Ctrl + P**는 파일
내용을 검색합니다. 둘러보기 > Cmux 명령어, Tmux 명령어 및 LazyVim 명령어는
검색 가능한 참조 메뉴입니다. 명령어를 선택하면 실행되는 대신 복사됩니다.

Kitty는 Enter, Home/End 및 단어 간 이동과 같이 2개 이상의 셀을 건너뛸 때
짧은 커서 궤적을 표시합니다. 커서가 3 ms 동안 멈춘 후 시작되어
0.05–0.15초 내에 서서히 사라집니다. 이를 맞춤 설정하려면
`~/.config/kitty/local.conf`에서 `cursor_trail`,
`cursor_trail_decay` 또는 `cursor_trail_start_threshold`를 설정하세요. `cursor_trail 0`은 이 기능을 비활성화합니다. 개인 설정 옵션은
패키지 기본값보다 우선하며 테마가 변경되어도 유지됩니다.

### 커서 불꽃

Kitty의 화려한 커서 궤적을 사용하려면 **설정 > 모양 > 터미널**에서 커서 불꽃을 켜세요. 기본적으로 꺼져 있습니다. 이를 끄면 일반 커서 궤적 및 개인 셰이더 선택 항목이 복원됩니다.

이 효과에는 Eitr의 데스크톱 의존성에 포함된 Kitty 0.49+ 및 `shader-slang`이
필요합니다. 활성화하면 Kitty를 저장하거나 다시 로드하기 전에 내장 셰이더의
유효성을 검사합니다. 로컬 머신 설정 파일은 `~/.config/eitr/terminal.json`이며, 헬퍼가
`kitty/cursor-fire.conf`를 작성하여 Kitty의 사용자 로더에서 마지막으로 포함됩니다. 활성화되어
있는 동안에는 fire 셰이더를 선택하고 이동 임계값을 1개 셀로
낮춥니다. 글꼴, 테마 및 개인 설정 파일은 그대로 유지됩니다.

## 터미널 선택

설정 > 모양 > 터미널을 사용하여 Kitty 또는 Ghostty를 선택하세요. Walker > 설정 > 데스크톱 > 모양 > 터미널을 사용할 수도 있습니다. `~/.config/eitr/terminal.json`의 로컬 머신 `terminal` 필드는
Super+Enter, tmux, 사용자 터미널 세션, AI/프로젝트 터미널 및 Walker의 터미널에서 열기 동작을 제어합니다. Ghostty가 설치되어 있지 않은 경우
이를 선택하면 일반적인 공식 패키지 설치 절차가 열립니다: Enter는 설치하고,
Esc는 취소합니다. 설치가 완료될 때까지는 Kitty가 선택된 상태로 유지됩니다. 나중에 Ghostty를
제거하면 실행 시 Kitty로 대체됩니다. Ghostty는 선택 사항이며 ISO
페이로드에는 포함되어 있지 않습니다.

테마를 변경하면 테마의 16개 ANSI 색상, 배경, 전경, 선택 영역 및 텍스트 커서
색상으로 `~/.config/ghostty/eitr.conf`가 다시 생성됩니다. 글꼴을 변경하면
선택한 글꼴 패밀리가 다시 생성되며, 기본 크기는 10포인트입니다. Ghostty는
동일한 zsh 및 프롬프트를 실행하며, 기본적으로 75% 불투명도와 일반 창 안쪽 여백 0으로 설정됩니다.
Hyprland는 블러와 동일한 일반 창 장식/규칙을 제공합니다. `eitr/cursor.json`의 포인터
패밀리, 크기 및 Auto/Light/Dark 선택 항목은 GTK와
컴포지터 전반에 적용되며, 터미널의 텍스트 커서와는 별개입니다.

Ghostty는 Eitr 런처를 통해 생성된 파일을 로드합니다. `font-size = 12` 또는
`cursor-style = bar`와 같은 개인 설정은 `~/.config/ghostty/local.conf`에
입력하세요. 이 파일은 마지막에 로드되며 테마가 변경되어도 유지됩니다.
실행 중인 Ghostty 세션은 테마/글꼴 변경 후 지원되는 다시 로드 신호를 받습니다.
일부 옵션은 새 창에만 적용됩니다. Kitty의 커서 궤적 및 커서 불꽃은
Kitty 전용 기능이며, Ghostty에는 이에 상응하는 내장 blaze 설정이 없습니다.

Eitr의 작업, 메뉴, 상태 및 설정 터미널은 `eitr-menu-terminal`, `eitr-plugins` 및
`fif-terminal`을 포함하여 항상 Kitty를 사용합니다: 이들의 `--class`, `--hold`,
`--title` 옵션 및 플로팅 창 규칙은 Kitty 전용으로 유지됩니다. Ghostty를
선택해도 이 동작은 변경되지 않습니다.

## 터미널 모양 및 공유 블러

Walker > 설정 > 데스크톱 > 모양 > 터미널 및 설정 > 모양 > 터미널은 Kitty와
Ghostty 모두에 불투명도, 안쪽 여백 및 블러 프리셋을 적용합니다. 불투명도는 솔리드 (100%),
라이트 (90%), 중간 (80%), 기본값 (75%) 및 강하게 (70%)를 제공합니다. 안쪽 여백은 없음,
좁게 (4포인트) 및 편안하게 (8포인트)를 제공합니다. 기본 설정은 75% 불투명도, 안쪽
여백 없음, 블러 켬 상태를 유지합니다. 유틸리티 터미널은 솔리드 배경과 작업용 여백을 유지합니다.

블러 끔은 일반 Kitty 및 Ghostty 창의 컴포지터 블러를 비활성화하며, 창을 불투명하게
만들지는 않습니다. 블러 강도는 데스크톱 전체에서 공유됩니다: 부드럽게 (크기 2,
1패스), 중간 (크기 3, 2패스, 기본값) 및 강하게 (크기 5, 3패스). 동일한 선택 항목이 Walker의 데스크톱 바와
설정 (SUPER + ,)의 데스크톱 바에서 모양 옆에 표시됩니다.

Hyprland 0.57은 전역 블러 강도를 사용하므로, 패널, 알림, 작업 공간 개요(Overview) 및
기타 블러가 적용된 애플리케이션을 포함하여 이미 블러를 사용 중인 모든 표면에
영향을 줍니다. 강도를 선택한다고 해서 터미널 블러가 활성화되는 것은 아닙니다. 블러가 강할수록 더 많은 GPU 연산이 소모됩니다. 테마 색상은 기존의 솔리드 모양을 유지합니다.

터미널 선택 항목은 `eitr/terminal.json`에 저장되며, 공유된 `blur-strength`는
`quickshell/desktop-bar/bar-settings.json` (버전 1)에 저장됩니다. 생성된
`kitty/appearance.conf`, `ghostty/eitr.conf` 및 `hypr/appearance.lua`는
이러한 환경설정을 통해 재생성 시에도 유지됩니다. 컴포지터는 `hypr/local.lua`보다
먼저 생성된 모양을 로드하므로 개인 컴포지터 규칙이 우선합니다. `kitty/local.conf` 및
`ghostty/local.conf`의 터미널 설정은 프리셋보다 우선합니다. 테마 변경 및
패키지 업데이트 시 설정이 다시 생성됩니다. Kitty는 SIGUSR1을 받고 지원되는 Ghostty
세션은 SIGUSR2를 수신하며, 실시간 재로드가 불가능한 옵션은 새 창에 적용됩니다.

## eitr 명령어

`eitr`는 Eitr의 도구들을 하나의 명령어로 모아 제공합니다. 인자 없이 실행하면 목록을 확인할 수 있습니다. 메뉴와
동일한 스크립트를 실행하므로 둘 다 항상 동일하게 동작합니다.

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

`eitr about`은 Eitr 정보 창을 열거나, 이미 열려 있는 경우 해당 창으로 포커스를 이동합니다.

`eitr config` 및 `eitr git`은 전달된 인자를 `eitr-config` 및 `eitr-git`으로 넘깁니다.
각 명령어에는 `--help`가 제공됩니다.

## 사용자 정의 훅

훅은 특정 시점에 Eitr가 실행하는 작은 사용자 스크립트로, Eitr 자체를
변경하지 않고도 동작을 확장할 수 있게 해줍니다. 해당 시점의 이름으로 명명된
실행 파일을 `~/.config/eitr/hooks/`에 배치하세요:

| 파일 | 실행 시점 | 전달되는 인자 |
| --- | --- | --- |
| `post-update` | 시스템 업데이트 또는 pacman/AUR 업데이트 후 | `system`, `pacman`, `yay` 또는 `full` |
| `theme-set` | 테마를 변경한 후 | 테마의 폴더 이름 |
| `battery-low` | 배터리가 15%로 떨어질 때마다 1회 | 배터리 백분율 |
| `post-boot` | 부팅 후 첫 로그인 시 | 없음 |

예를 들어 테마가 바뀔 때마다 Spotify의 색상을 (Spicetify를 사용하여) 다시 지정하려면
`~/.config/eitr/hooks/theme-set`을 생성하세요:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

그런 다음 `chmod +x ~/.config/eitr/hooks/theme-set`으로 실행 권한을 부여하세요. 각 훅에는
최대 60초의 실행 시간이 주어집니다. 훅의 출력 및 모든 실패 내역은
`~/.local/state/eitr/hooks.log`에 기록되며, 훅이 실패하더라도 업데이트나
테마 전환이 중단되지 않습니다. `eitr hook list`는 존재하는 훅을 보여주고,
`eitr hook run theme-set eitr`는 훅을 테스트 실행합니다. 업데이트 시 이 폴더는 절대 변경되지 않습니다.

## cmux TUI

Kitty에서 `cmux`를 실행하거나, 이름이 지정된 세션을 실행하려면 `cmux --session work`를
실행하세요. cmux TUI는 tmux와 함께 사용할 수 있는 선택적 워크플로이며, Kitty나 기존
단축키를 대체하지는 않습니다. 새로운 EITR 설치본에는 `/usr/bin/cmux`에 고정된 공식 바이너리가
포함되어 있습니다. 기존 사용자별 설치본이 PATH에서 우선할 수 있습니다.
어떤 것이 선택되었는지 확인하려면 `command -v cmux`를 사용하세요. 터미널 출력과
텍스트 파일을 읽기 위해 `less`가 포함되어 있습니다.

기본 접두사 키는 **Ctrl-b**입니다: 키를 뗐다가 다음 키를 누르세요.

| 단축키 | 동작 |
| --- | --- |
| Ctrl-b ? | 현재 단축키 표시 |
| Ctrl-b W | 작업 공간 생성 |
| Ctrl-b c | 화면 생성 |
| Ctrl-b % / Ctrl-b " | 오른쪽 / 아래로 분할 |
| Ctrl-b t | 새 터미널 탭 |
| Ctrl-b h/j/k/l | 왼쪽/아래/위/오른쪽 포커스 |
| Ctrl-b s | 사이드바 표시/숨김 |
| Ctrl-b d | 로컬에서 종료 또는 서버에서 분리 |

UI 없이 계속 실행되는 세션을 원한다면
`cmux --headless --session work`를 실행한 다음, `cmux attach --session work`로 연결하세요.
브라우저 탭에는 Chrome/Chromium이 필요합니다. 탭, 패널(pane) 또는 작업 공간을 닫으면
실행 중인 작업에 영향을 줄 수 있으므로 이러한 동작을 사용하기 전에 확인하세요. 둘러보기 > Cmux 명령어에는
세션 명령어, 탐색, 마우스 제어 및 닫기 단축키가 포함되어 있습니다.
기본값은 변경되거나 재정의될 수 있으며, **Ctrl-b ?**가 실시간 참조 안내입니다.

## 작업 터미널

메뉴에서 열리는 터미널과 업데이트 및 문제 보고 알림의
터미널은 창 중앙 위에 플로팅 상태로 표시되며 테마의 솔리드 배경을 사용합니다. AI 어시스턴트 세션 및 LazyVim 프로젝트 (개발 메뉴)는
직접 연 터미널과 마찬가지로 반투명 배경을 가진 일반 타일형 창으로
열립니다. 일반 터미널은 대화형이며 브랜드 요소가 표시되지 않습니다.

설치기/업데이트/설정
터미널은 테마가 적용된 룬 스타일의 EITR 배너를 표시합니다. 성공한 작업은 일반적으로
닫히며, 실패한 작업은 사용자가 닫을 때까지 열린 상태로 유지됩니다. 정보성 보고서는 의도적으로
열려 있을 수 있습니다. Elephant를 다시 시작해도 실행된 앱이 닫히지 않아야 합니다:
메뉴, 키 바인딩 및 바 버튼에서 열린 앱과 터미널은 uwsm 세션에서 별도의
애플리케이션 스코프를 사용합니다.

uwsm이 없으면 직접 실행됩니다. Elephant는
데스크톱 헬퍼 및 대체 실행을 위해 프로세스 전용 중지를 유지합니다.

대기 중인 작업, 계정, 보고서 및 정보 터미널을 닫으려면 **Esc**를 누르세요. 복구 키 확인 및 설치기 전원 끄기를 포함하여 답변 및 확인에는 Enter가 유지됩니다.

## 셸 기록

`history`는 최근 명령어를 나열합니다. zsh에서는 다음 명령어로 실제 기록 파일 경로를 확인할 수 있습니다:

```sh
printf '%s\n' "$HISTFILE"
```

Neovim에서 열려면 다음과 같이 실행합니다:

```sh
nvim "$HISTFILE"
```

기록에는 토큰이나 자격 증명이 포함되어 있을 수 있으므로 버그 보고서에 그대로 복사하지 마세요.
수동으로 편집하기 전에 다른 셸을 모두 닫으세요. 실행 중인 셸이
메모리에 있는 기록을 다시 덮어쓸 수 있습니다. 확장된 zsh 기록에는 타임스탬프
메타데이터와 여러 줄 명령어가 포함될 수 있으므로 임의의 일부분이 아닌
해당 항목 전체를 삭제하세요. 실행 취소가 필요할 수 있으므로 비공개 위치에 백업해 두세요.

## 편집기 모양

테마가 변경되면 생성된 VS Code 및 LazyVim 환경설정이 업데이트됩니다. 지원되는 실행 중인
LazyVim 세션은 다시 열지 않고도 새로고침됩니다. 사용자 재정의/플러그인은
자체 색상을 선택할 수 있으므로, 편집기가 데스크톱 설정을 따르지 않는 경우
해당 구성을 확인하세요. 기본 글꼴 연동은 앱이 이를 지원하는 경우에만 적용됩니다.

## 프로필 사진

`eitr picture` (또는 `eitr picture show`)는 현재 사진 상태를 JSON으로 보여줍니다. `eitr picture set FILE`은 중앙에 맞춘 가장 큰 정사각형으로 저장하며, `eitr picture remove`는 사진을 제거합니다. 자르기 영역을 조정하려면 설정 > 사용자를 사용하세요.
