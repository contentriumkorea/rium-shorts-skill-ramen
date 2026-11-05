# 편별 작업과 재수정

프로젝트의 기존 `Footage`, `Sequence`, `Export`, `codex` 구조를 확인하고 재사용한다. 스킬을 호출했다는 이유로 모든 빈 폴더를 미리 만들지 않는다. 최초 사용에서는 편 번호·주제·저장 루트를 기존 운영계획과 맞춘다.

```
Footage/                         # 기준 원본, 기존 구조 유지
Sequence/Kino/R08/               # 한 편의 승인된 기록/소스 스냅샷
  episode.json                  # 의도·프로젝트 ID·구간·자막·음원·진행 상태
  edit-plan.md                  # 사람이 읽는 방향·대본·수정 사항
  snapshots/<revision>/         # 실제 마운트의 텍스트 소스 사본(필요 시)
Export/R08/                     # 요청한 렌더와 검수 결과
codex/.../episode-index.json     # 편 번호 ↔ Kino 프로젝트 ↔ 실제 마운트/작업 위치
```

이는 예시다. 기존 저장 규칙과 승인된 위치가 있으면 그대로 사용한다. Kino 실제 작업 마운트를 위 폴더로 옮기거나 `.kino`라는 임의 시퀀스 파일을 만들지 않는다. **Kino 프로젝트 ID와 실제 mountDir가 편집 기준**이고 Sequence 폴더는 해당 프로젝트의 대본·매핑·복구 가능한 소스 사본을 보관한다. 마운트 자체, `.kino-mount`, 미디어 캐시를 복사/이동해 동기화를 바꾸지 않는다.

프로젝트명은 `R08 | 금오산 키즈페스티벌`처럼 찾기 쉽게 짓되, 번호/주제는 실제 운영계획을 따른다. Kino 내부 DOCUMENT bin은 축제→날짜/편으로 정리할 수 있다. MEDIA bin과 혼동하지 않는다. 기존 편이 있으면 열고 수정한다. 대안 편집 비교가 필요한 경우에만 새 프로젝트/변형을 만든다.

## episode.json 필수 내용

- `episode_id`, `title`, `intent`, `project_id`, `project_url`, `mount_dir`, `status`, `revision`.
- `format`: width/height/fps/duration, 기본 1080×1920이며 소스/요청에 따라 판단.
- `direction`: chosen_layout, hook, narrative, voice, music, reason, user_decision_or_delegation.
- `shots`: source_id, kino_media_id, source_in_s/out_s, timeline_in_s/out_s, clip_id, role, crop_note.
- `text`: wording, start_s/end_s, clip_id, role(hook/chapter/caption), position_choice.
- `caption_layout`: 기본 조합, 컷별 배치 예외, 실제 자막 소스 경로·clipId, 가림 문제/수정/재검수 구간. [자막 조합·재검수](caption-layout-review.md)를 따른다. 생성 자막의 문구/타이밍 단일 기준은 Kino가 반환한 파일이며 인덱스에 별도 편집용 복제본을 만들지 않는다.
- `audio`: asset/media id, provider/source, license status, start/end, speech/music/sfx role, generated voice/model/settings if used (비밀값 제외).
- `verification`: hook_by_2s, source_coverage, safe_area, sync, audio_review, playback, render; 각 항목 pass/fail/not_checked + 근거.
- `changes`: 수정 요청, 변경 범위, 그대로 둔 결정, 새 결과 경로.

검수 문제마다 `text_origin`(baked_in/authored_overlay/transcript_caption), 실제 확인 시각, 수정 대상 레이어, 확인 당시 clipId, 선택한 수정과 재검수 결과를 연결한다. 원본 자체 가림은 새 레이어 수정으로 해결됐다고 표시하지 않는다. 에피소드 목적이 `internal_test`인지 실제 본편인지도 구분한다.

이 JSON은 인계용 스키마이며 Kino에 직접 임포트하는 고유 포맷이 아니다. 경로/ID가 실제로 존재하는지 확인한다. 없는 값을 임의 UUID로 채우지 않는다.

## 원하는 편만 수정하기

“08편 5초에 있는 컷 바꿔줘” → index로 projectId 찾기 → 현재 timelineGet/entry source 조회 → 해당 clipId 및 소스 구간 확인 → 대체 컷의 내용 확인 → 수정 → 관련 자막/오디오/총 길이 재검수. 파일명만 보고 다른 편을 열지 않는다. “그 말 나오는 곳”은 effective transcript/lookup을 사용한다. 의미가 다른 두 장면이면 선택을 확인한다.

“목소리는 빼줘”는 독립 VO 트랙이 있으면 그 레이어만 제거/음소거하고 자막·음악·현장음을 보존한다. 원본이나 BGM에 말·노래가 섞여 있으면 전체 오디오를 통째로 끄지 않는다. 무엇을 남길지 짧게 확인하고, 분리가 요청된 경우 현재 Kino stem/speech 관련 가이드를 읽어 실행한다. 별도 생성·분리 비용을 모르게 사용하지 않는다. 분리 결과는 원본과 따로 보존하고 실제 잔류 음성/음악 손상을 확인한다.

큰 재구성 전 현재 소스 스냅샷과 수정 기록을 남긴다. 새로운 미리보기·렌더를 검증한 후에만 기존 결과를 프로젝트의 이전안 규칙에 따라 보관한다. 원본·작업 마운트·현재 미디어 연결은 유지한다. 전체 폴더 미러링이나 자동 정리 삭제를 하지 않는다.
