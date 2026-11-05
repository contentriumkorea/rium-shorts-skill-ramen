# 편별 작업과 재수정

프로젝트의 기존 `Footage`, `Sequence`, `Export`, `codex` 구조를 확인하고 재사용한다. 스킬을 호출했다는 이유로 빈 폴더를 미리 만들지 않는다. 편 번호·주제·저장 루트·사용 편집기를 기존 프로젝트와 맞춘다.

```text
Footage/                         # 기준 원본, 기존 구조 유지
Sequence/<기존 편집기 분류>/R08/   # 실제 네이티브 프로젝트 또는 승인된 편별 기록
  episode.json                  # 의도·편집기·프로젝트/시퀀스 연결·검수 상태
  edit-plan.md                  # 방향·대본·수정 사항
  snapshots/<revision>/         # 필요한 실제 프로젝트/소스 버전 사본
Export/R08/                     # 요청한 렌더와 검수 결과
codex/.../episode-index.json     # 편 번호 ↔ 편집기 ↔ 프로젝트/시퀀스 위치
```

이는 예시이며 기존 저장 규칙이 우선이다. 앱이 관리하는 프로젝트·마운트·캐시·공유 폴더를 강제로 옮기지 않는다. 편집기에서 실제 저장한 파일이나 반환된 프로젝트/시퀀스 식별자를 기준으로 삼는다. 편집기 중립 JSON이나 소스 사본을 네이티브 프로젝트라고 표시하지 않는다.

프로젝트/시퀀스명은 `R08 | 현장 체험과 먹거리`처럼 알아보기 쉽게 짓되 실제 번호와 주제를 사용한다. 한 프로젝트에 여러 편의 시퀀스가 있으면 시퀀스별로 인덱싱한다. 기존 편이 있으면 그 편을 수정하고, 비교안이 필요한 경우에만 별도 버전/시퀀스를 만든다.

## episode.json에 남길 내용

- `episode_id`, `title`, `intent`, `purpose`(실제 본편/내부 시험 등), `revision`.
- `editor`: `name`, `version`, `native_project_path`, 실제 제공되는 경우 `project_id`, `sequence_id`. 파일 기반이 아닌 환경이나 아직 미작성인 경우 경로는 `null`이며 그 이유를 기록한다. 식별자를 임의 UUID로 채우지 않는다.
- `capabilities`: 현재 연결에서 확인한 읽기·클립 편집·자막·오디오·저장·렌더·교환 포맷의 지원 여부와 근거. 제품 이름만으로 지원을 추정하지 않는다.
- `status`: `planned`, `handoff_ready`, `native_edit_in_progress`, `native_saved`, `render_verified`, `blocked`처럼 실제 단계. 네이티브 저장 성공과 렌더 검증은 따로 기록한다. 일부 작업만 막히면 그 항목의 상태와 남은 작업을 적는다.
- `format`: width/height, 시퀀스 fps, duration, 총 프레임 수와 시간/프레임 기준. 세로 1080×1920은 후보이며 소스·요청·기존 시퀀스에 따라 정한다.
- `direction`: chosen_layout, hook, narrative, voice, music, reason, user_decision_or_delegation.
- `shots`: source_id/path, 실제 편집기 media/clip ID가 있으면 해당 값, source_in/out, timeline_in/out, 각 단위와 fps 기준, role, crop/speed_note.
- `text`: wording, start/end, 단위, 실제 clip/layer ID 또는 트랙·이름, role(hook/chapter/caption), position_choice.
- `caption_layout`: 기본 조합, 컷별 예외, 실제 자막 파일/트랙, 가림 문제·수정·재검수 구간. [자막 조합·재검수](caption-layout-review.md)를 따르고 문구/타이밍의 단일 기준을 지정한다.
- `audio`: asset/path 또는 실제 media ID, provider/source, 사용 권리 상태, start/end, speech/music/sfx 역할, 음량·페이드, 생성 음성이면 voice/model/settings(비밀값 제외).
- `verification`: hook_by_2s, source_coverage, safe_area, source_links, native_save, audio_review, playback, render. 각 항목 pass/fail/not_checked + 실제 근거.
- `changes`: 수정 요청, 변경 범위, 기존 결정, 새 결과 경로, 미실행 항목과 다음 단계.

검수 문제마다 `text_origin`(baked_in/authored_overlay/transcript_caption), 실제 확인 시각, 대상 레이어/트랙, 식별 근거, 선택한 수정과 재검수 결과를 연결한다. 원본 자체 가림은 새 레이어 수정으로 해결됐다고 표시하지 않는다. 인계용 JSON은 어떤 편집기에나 바로 임포트되는 포맷이 아니다.

## 원하는 편만 수정하기

“08편 5초에 있는 컷 바꿔줘” → 인덱스에서 편집기·프로젝트·시퀀스 확인 → 현재 타임라인과 원본 구간 조회 → 실제 대상 클립 확인 → 대체 컷 검토 → 지원되는 연결로 수정 → 관련 자막·음원·총 길이·저장 상태 재검수. 클립 ID가 없으면 트랙·이름·구간을 함께 확인한다. “그 말 나오는 곳”은 실제 전사와 해당 시퀀스의 타이밍으로 찾는다. 파일명만 보고 다른 편을 열지 않는다.

“목소리는 빼줘”는 독립 VO 트랙이 있으면 해당 트랙만 처리하고 자막·BGM·현장음을 보존한다. 원본이나 BGM에 말·노래가 섞여 있으면 무엇을 남길지 구분한다. 분리가 요청됐을 때 실제 제공되는 도구와 비용·전송 범위를 확인하고 별도 결과로 보존한다. 전체 오디오 음소거를 음성 분리 완료라고 보고하지 않는다.

직접 편집 연결이 없으면 현재 편의 컷표·자막·믹스 지시·변경 목록을 갱신하고 `handoff_ready`로 표시한다. 파일을 생성했다는 이유로 `native_saved`나 `render_verified`로 올리지 않는다. 큰 재구성 전 필요한 프로젝트 버전을 보존하며 원본·미디어 연결·다른 편의 결과는 유지한다.
