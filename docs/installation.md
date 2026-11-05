# 설치와 업데이트

## ZIP 설치

1. [최신 정식 릴리스](https://github.com/contentriumkorea/rium-shorts-skill-ramen/releases/latest)의 `rium-shorts-skill-ramen.zip`을 받는다. 버전이 붙은 ZIP도 동일한 내용이다.
2. 압축을 풀면 `rium-shorts-skill-ramen/SKILL.md`가 나온다. 폴더가 한 단계 더 중첩되지 않게 설치한다.
3. Codex는 기본 `~/.codex/skills/`, Claude Code는 `~/.claude/skills/` 아래에 이 폴더를 둔다. Codex의 `CODEX_HOME`이 지정돼 있다면 그 아래 `skills/`를 사용한다. Windows의 `~`는 사용자 프로필 폴더다.
4. 앱에서 스킬을 다시 읽거나 새 대화를 시작하고 `Rium Shorts Skill - ramen`을 호출한다. 현재 열려 있는 대화의 자동 재로딩을 보장하지 않는다.

기존 설치본은 사용자가 수정한 문서·설정을 포함해 별도 경로에 백업한 뒤 교체한다. v1.3.0은 편집기별 실행 지침을 다시 구성했다. ZIP을 단순 덮어써 오래된 전용 실행 지침이 남지 않도록, 기존 폴더를 백업한 후 새 폴더를 설치한다. 기존 프로젝트·영상·편집기 설정은 옮기거나 삭제하지 않는다.

## Git으로 새 설치

Git이 설치된 환경에서만 사용한다. 대상 폴더가 이미 있으면 이 명령은 업데이트 명령이 아니다.

Windows PowerShell, Codex 기본 경로:

```powershell
git clone https://github.com/contentriumkorea/rium-shorts-skill-ramen.git "$env:USERPROFILE\.codex\skills\rium-shorts-skill-ramen"
```

Windows PowerShell, Claude Code 기본 경로:

```powershell
git clone https://github.com/contentriumkorea/rium-shorts-skill-ramen.git "$env:USERPROFILE\.claude\skills\rium-shorts-skill-ramen"
```

macOS·Linux의 기본 경로:

```sh
git clone https://github.com/contentriumkorea/rium-shorts-skill-ramen.git ~/.codex/skills/rium-shorts-skill-ramen
```

Claude Code에서는 위 대상 경로를 `~/.claude/skills/rium-shorts-skill-ramen`으로 바꾼다. Git 업데이트는 사용자 수정 사항을 확인·백업한 뒤 진행하며 강제 초기화하지 않는다.

## 편집기 연결

편집기 이름·버전과 실제 프로젝트를 확인한다. 도구가 이미 연결돼 있으면 현재 가이드·권한·지원 기능을 조회하고, 연결이 없으면 실행 가능한 자료부터 준비한다. 특정 프로그램·플러그인 설치나 인증을 자동 강요하지 않는다. 이름이 같은 기능이라도 앱별 지원 여부가 다를 수 있다.

실제 조작 경로와 완료 기준은 [편집기 실행 지침](../references/editor-workflow.md)을 따른다. 컷표나 중간 JSON은 편집기에서 열어 검증한 네이티브 프로젝트가 아니다. 기존 편집기를 임의로 바꾸지 않는다.

## 로컬 분석 도우미

Python 3.9 이상과 PATH에서 실행 가능한 `ffprobe`가 인벤토리에 필요하다. 오디오 측정에는 `ffmpeg`도 필요하다. 시간대 데이터가 없는 Windows Python 환경에서는 `tzdata`가 필요할 수 있다. `librosa`와 `numpy`는 선택적 템포 분석에만 쓰며, 없어도 음압 측정을 진행할 수 있다. 도우미는 의존성을 자동 설치하지 않는다.

스킬 폴더에서 실행하거나 스크립트 경로를 실제 설치 위치로 바꾼다.

```text
python scripts/inventory_media.py --source "촬영본 폴더" --output "기존 기록 폴더/media-index.json" --timezone Asia/Seoul
python scripts/inspect_audio.py --source "준비 BGM 폴더" --output "기존 기록 폴더/audio-index.json"
```

출력의 부모 폴더는 먼저 존재해야 하고, 기존 출력 파일은 덮어쓰지 않는다. 도우미는 원본 파일을 수정하지 않는다. 생성 JSON에는 로컬 경로가 들어갈 수 있으므로 작업 기록을 공개 배포할 때 내용과 경로를 따로 검사한다.

인벤토리는 메타데이터 후보를 만들며 날짜·장소·얼굴·인파를 자동 확정하지 않는다. 음압·템포 측정은 실제 청취나 곡·효과음 식별을 대신하지 않는다.

## 검증과 무결성

릴리스의 `SHA256SUMS.txt`와 받은 ZIP의 SHA-256을 비교할 수 있다. ZIP은 스킬 문서·SVG·Python 도우미만 포함한다. 편집기·모델 가중치·원본 매체·인증정보는 포함하지 않는다. 특정 편집기에서 프로젝트 열기·미디어 재연결·자막 스타일·오디오·출력까지 확인한 범위만 그 환경의 검증 완료로 기록한다.
