---
name: rium-shorts-skill-ramen
description: 구미 라면축제 촬영본을 날짜·시간·장소와 하이라이트로 정리하고, 레퍼런스를 바탕으로 방향·대본을 큐레이션해 Kino에서 수정 가능한 인스타그램 숏폼 초벌 편집을 만든다. 간단한 제작 의도, 특정 편 수정, 촬영본 추가 정리 요청에 사용한다.
metadata:
  version: 1.2.1
---

# Rium Shorts Skill - ramen

편집 경험이 적은 사람도 **촬영본 폴더와 한 문장 의도**로 Kino 편집까지 갈 수 있게 한다. Codex와 Claude가 같은 SKILL.md를 읽는다. 도구 namespace·사용자 홈·MCP 연결 주소를 하드코딩하지 않는다. 사용자의 현행 지침과 프로젝트 구조가 우선이다.

## 시작과 결과

예: “금요일 사람 많은 분위기로 30초 만들어줘”, “우리밀 라면 소개, 백팩 따라가는 느낌”, “08편 도입만 더 강하게”. 먼저 기존 프로젝트 안내와 편별 인덱스를 읽어 해당 편을 찾는다. 의도가 명확하면 동일한 정보를 다시 질문하지 않는다. 이 스킬 자체가 모든 파일 이동·공개·음성 생성의 포괄 승인이 되지는 않는다.

기본 결과는 **소스 구간 근거가 있는 편집안 + 실제 Kino 프로젝트 + 재수정 가능한 소스와 편별 인덱스 + 검수 상태**다. 계획서만 작성하고 편집 완료라고 하지 않는다. 실제 촬영본이나 연결이 없으면 준비된 기준과 필요한 입력을 구분한다. 렌더·외부 업로드·게시 여부는 요청 범위를 따른다.

## 작업 순서

1. **경로와 도구 확인.** 지정된 폴더와 기존 안내를 확인한다. Kino `getKinoInstructions`와 해당 작업 가이드를 읽고 현재 MCP 도구를 발견한다. [Kino 실행](references/kino-workflow.md)을 참조한다. 연결 불가면 실행 가능한 편집안까지 저장하고 연결이 필요한 단계만 알린다. 다른 편집기로 몰래 바꾸지 않는다.
2. **촬영본 분류와 분석.** [소스 관리](references/media-workflow.md)에 따라 촬영 시각의 근거·불확실성과 장소를 기록한다. `scripts/inventory_media.py`는 메타데이터 인덱스만 생성한다. 사람 밀집·표정·음식 동작·현장감·기술 상태를 실제 프레임/음성으로 확인해 구간을 추린다. Kino 분석이 진행 중이면 완료분만 사용하고 대기 상태를 기록한다.
3. **방향 큐레이션.** [편집 기준](references/editorial.md)과 [8편 분석](references/reference-analysis.md)을 읽는다. 실제 소스에 맞는 방향 2개와 추천 하나를 보여준다. [자막 조합·재검수](references/caption-layout-review.md)에 따라 중앙/하중앙/상단 타이틀 유지 등을 조합하고 촬영본의 구체적 장면을 추천 이유로 든다. 현장음/내레이션, 훅 예문과 전개의 차이도 쉬운 말로 설명한다. 질문은 한 번에 하나. 이미 방향을 골랐거나 “알아서”라고 위임했으면 가정을 짧게 알리고 진행한다. 응답이 필요한 방향 선택은 임의 확정하지 않되 소스 분석은 계속한다.
4. **짧은 대본과 구간표.** 0~2초에 핵심 훅을 완성해 읽히게 하고 곧바로 화면 증거로 답한다. 모든 문장을 사실·주관적 감상·미확인으로 구분한다. 편집안에 source ID, source in/out, timeline in/out, 화면 문구, 오디오 역할을 넣는다. [편별 관리](references/episode-management.md)를 따른다.
5. **Kino 초벌.** 편별 프로젝트를 찾거나 생성하고 독립된 클립·자막·BGM·효과음·VO 레이어로 편집한다. 소스를 한 덩어리로 구워 재수정을 막지 않는다. 루트 Sequence를 명시적으로 작성하고 Kino 현재 규칙을 따른다. 범위가 승인된 기존 작업은 다시 승인받지 않는다.
6. **음성·음악.** [오디오](references/audio.md)에 따라 사용자가 사전 준비한 BGM 파일을 먼저 분석·큐레이션한다. [음원 라이브러리](references/prepared-music-library.md)에서 곡 전체뿐 아니라 쓸 구간·말과의 간섭·마무리까지 고른다. 필요할 때 ElevenLabs를 사용하되 먼저 대본/톤을 결정하고 실제 연결 도구와 현재 모델 스키마를 확인한다. 생성이 요청·위임되지 않았다면 필요성을 제안한다. 생성된 음성의 실제 길이로 타이밍을 다시 맞춘다.
7. **검수·인계.** [안전영역](references/instagram-safe-area.md)과 [장면별 자막 검수](references/caption-layout-review.md)로 UI와 얼굴·손·라면·간판·상황 가림을 확인한다. 초기 선택을 정답으로 고정하지 말고 ‘어느 시점에 무엇을 가려서 어떻게 바꾸는지’를 제안·수정·재확인한다. 훅·최장 문구·세로 크롭·음성 시작/끝도 검수한다. Kino 스크린샷, 타임라인/마운트 동기화 및 가능하면 실제 재생·청취·렌더를 확인한다. 수행하지 못한 검사는 구체적으로 남긴다.

## 바꾸면 안 되는 핵심

- **첫 2초:** 막연한 “여러분!”만 나온 것은 훅 완료가 아니다. 무엇을 볼 이유가 있는지 2초 이내 알 수 있어야 한다. 낚시 문구의 주장을 실제 촬영본이 뒷받침해야 한다.
- **스타일의 선택권:** 폰트·좌표·컷 길이·효과음을 전 편에 강제하지 않는다. 레퍼런스의 원리를 적용하고 작품별 차이를 유지한다. 동일 편 안에서는 읽기 규칙을 일관되게 한다.
- **현장 영상 우선:** 의미 없는 도형·파티클·AI 일러스트·과한 줌·템플릿 인트로를 자동 추가하지 않는다. 정보가 필요한 단순 라벨/가독성 보조판은 목적이 있을 때만 쓴다.
- **원본과 시간:** 원본 파일은 보존한다. 파일 수정일을 촬영일로 확정하지 않는다. 장소·인파·인기 순위를 추측해서 사실로 만들지 않는다.
- **재수정:** “몇 번 편의 어떤 부분”이라는 요청을 프로젝트/클립/소스 구간으로 연결한다. Kino가 관리하는 마운트는 임의 이동하지 않는다.
- **실제 가림:** 원본에 박힌 글자와 새 편집 자막을 구분한다. 위치를 옮긴 뒤에도 피사체가 이동해 겹칠 수 있으므로 문구의 전체 노출 구간과 소스 내부 장면전환을 재검수한다. 짧게 줄이거나 특정 컷에서 생략하는 것도 정상적인 편집이다.

## 필요한 자료만 읽기

- 새 촬영본·날짜/장소 구분 → [media-workflow.md](references/media-workflow.md)
- 훅·문장·구성·레퍼런스 → [editorial.md](references/editorial.md), [reference-analysis.md](references/reference-analysis.md)
- 안전영역·자막 배치/조합/가림 재검수 → [instagram-safe-area.md](references/instagram-safe-area.md), [caption-layout-review.md](references/caption-layout-review.md), `assets/safe-area-preview.svg`
- 편별 폴더·재편집 → [episode-management.md](references/episode-management.md)
- Kino 실행 → [kino-workflow.md](references/kino-workflow.md)
- 음악/효과음/음성 → [audio.md](references/audio.md), [실제 오디오 분석](references/reference-audio-analysis.md)
- 준비된 BGM 파일 선택·구간 큐레이션 → [prepared-music-library.md](references/prepared-music-library.md)
- 기존 프로젝트 연결·재개 → [project-context.md](references/project-context.md)
- 실제 Kino 테스트에서 확인한 절차·한계 → [kino-test-validation.md](references/kino-test-validation.md)
