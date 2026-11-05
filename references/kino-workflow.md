# Kino 실행·보관 절차

2026-11-05 연결된 Kino MCP 도구 명세와 설치된 Kino 가이드에서 확인한 절차다. 실제 작업 때 도구 명세를 다시 읽으며, 이 문서의 예시 ID·경로를 실제 프로젝트에 사용하지 않는다. Codex·Claude Code 모두 같은 SKILL.md와 연결된 Kino MCP를 사용한다. 특정 에이전트의 함수 네임스페이스 대신 아래 도구 이름으로 발견한다.

## 1. 연결과 실제 프로젝트 확인

1. 먼저 `getKinoInstructions`를 호출한다. `getCurrentKinoContext`로 현재 projectId, composition, mountDir, mountStatus를 확인한다. 선택 프로젝트가 없으면 `listProjects`로 찾는다.
2. 이번 작업의 편 번호와 제목이 인덱스에 있으면 해당 projectId를 명시한다. 화면에 선택된 다른 프로젝트를 임의로 편집하지 않는다. 한 편 수정 요청에 새 프로젝트를 만들지 않는다.
3. 새 편 제작일 때만 `createProject`를 사용한다. 9:16 초벌은 보통 1080×1920이며 fps는 소스·납품 요구를 보고 정한다. Kino는 생성 시 fps를 선택하므로 이미 존재하는 프로젝트의 fps를 추측·변경하지 않는다.
4. source 작성 전 현재 서버가 가리키는 `skills/remotion/SKILL.md`와 필요한 rules를 읽는다. `readFile`은 Kino 가이드용이며 프로젝트 파일 읽기 도구가 아니다.
5. `openProject`는 외부 MCP에서 편집기로 이동시킬 수 있다. 다른 창에서 작업 중인 사용자의 포커스 규칙을 따르고, 이미 얻은 mountDir에서 비활성 파일 작업을 우선한다.

### 호출 제한·클라우드 처리

호출 실패 시 도구 이름·오류·executed/ran·재시도 가능 여부를 구분한다. 가이드 또는 조회 한 번의 한도 오류만으로 다른 모든 기능도 막혔다고 단정하지 않는다. 실행하지 않은 exportVideo를 거절됐다고 보고하지 않는다. 명시적으로 허용되는 조회는 해당 범위에서 사용하되, 거절된 작업을 UI·다른 API·다른 계정으로 우회하지 않는다. 현재 도구가 제거되거나 연결되지 않았다면 없는 도구를 실행했다고 하지 않는다.

로컬 파일 가져오기도 분석용 업로드와 서버 분석을 수반할 수 있고, 마운트 소스 수정은 공유 프로젝트로 동기화될 수 있다. `uploadOriginal:false` 또는 원본 업로드 미요청을 전체 클라우드 OFF로 설명하지 않는다. 사용자가 클라우드 사용 중단을 요청하면 새 반입·분석·업로드·공유를 시작하지 않고, 공식 설정의 실제 적용 범위를 확인한다. 기존 서버 파일 삭제·계정 전환·앱 네트워크 차단은 별도 범위다.

## 2. 파일 분류와 Kino Bin은 별개

프로젝트의 기존 Footage·Sequence·Export·codex 구조를 재사용한다. 사용자가 전달한 소스 폴더는 먼저 읽기 전용 인벤토리로 확인한다. 촬영 시각·장소가 불확실한 파일을 이름만 보고 확정하지 않는다.

- MEDIA bin: 원본 영상·음원 등 전체 파일. 날짜 → 장소/촬영팀 단위로 최소 분류한다. `createBin({name, folderType:'MEDIA', parentBinId})`의 부모도 MEDIA여야 한다.
- DOCUMENT bin: 편집 프로젝트. `getBins({folderType:'DOCUMENT'})`로 기존 폴더 확인 → 필요하면 `createBin`의 DOCUMENT 형식으로 생성 → `listUiActions({query:'MoveToBin'})`에서 현재 액션 확인 → `runUiAction`의 `project::MoveToBin`에 실제 projectId·binId 전달.
- `addMediaToBin`은 한 파일을 한 bin으로 **이동**한다. 하나의 파일을 시간대·장소·회차마다 복제·분산하지 않는다. 여러 회차의 추천 구간은 타임코드가 있는 별도 선별 목록으로 연결한다.
- Kino 프로젝트도 한 DOCUMENT bin에 속한다. 한 편당 독립된 편집 프로젝트와 짧은 식별자를 유지한다. 후보 예: `R26-E04 우리밀라면`.
- Kino가 관리하는 mountDir와 `.kino-mount`를 프로젝트의 Sequence 폴더로 강제 이동·복사해 살아 있는 프로젝트라고 취급하지 않는다. `.kino-mount` 및 recovery/baseline 파일을 건드리지 않는다.

프로젝트의 `Sequence/Kino/E04-우리밀라면/`에는 실제 생성·저장 가능한 자료만 둔다: 편집 지시·대본, `project-index.json`의 해당 행 또는 인덱스 링크, 현재 원본 소스 경로 매핑, 승인된 소스 백업, 검수 기록. 빈 가짜 `.kino`·시퀀스 파일을 만들지 않는다. Kino의 살아 있는 편집 원본은 반환된 mountDir이고, Sequence 아래의 소스 스냅샷은 백업임을 명시한다.

편 인덱스 최소 항목: episodeId, title, projectId, projectUrl, mountDir(이 PC 연결값), documentBinId, composition(width/height/fps), brief/script 위치, 최신 렌더 경로, status, updatedAt. portable 패키지에서는 PC 경로를 설정값으로 분리한다.

## 3. 가져오기·분석·선별

- 라이브러리에 이미 들어간 파일은 `findMedia`와 인덱스의 mediaId로 재사용한다. 새 로컬 자산은 `addMediaToKino`의 `type:'localFile'` 및 실제 절대경로로 가져온다. 키/UUID를 절대경로에 넣지 않는다. Windows에서는 현재 서버가 반환·허용하는 드라이브 절대경로를 사용한다. 문서의 POSIX 예시를 위해 가짜 `/C:/...` 경로를 만들지 않는다.
- `media`, `pending`, `failed`를 개별 확인하고 받은 mediaId를 기록한다. 부분 실패의 mediaId를 버리고 같은 파일을 무조건 재가져오지 않는다. 가져오기 성공은 AI 분석·원본 업로드 완료가 아니다. `uploadOriginal:true`는 별도 원본 업로드이며 요청 범위 없이 켜지 않는다.
- `getMediaAnalysisStatus`로 transcript/wordTiming/visualDescriptions/spriteSheet 등 필요한 단계가 ready인지 확인한다. overall `finished`라도 개별 단계는 실패했을 수 있다. `processing`은 안내된 간격으로 재확인하고, `upload_failed`·`not_started`는 기다리면 해결되는 상태로 표현하지 않는다.
- `readVideo`의 구간별 전사·설명을 받아 후보를 찾는다. `visualSemanticSearch`·`transcriptSemanticSearch`는 탐색 보조다. 얼굴 인식 결과의 사람 수는 군중 규모가 아니다.
- 후보를 실제로 쓰거나 화면을 설명하기 전 `lookAtFrames`로 원본 범위를 본다. 현지 파일의 레퍼런스 분석은 ffmpeg 추출로 충분하며, 분석만 위해 새로 Kino에 업로드하지 않는다. 영상의 큰 흐름을 접촉시트로 본 뒤 필요한 구간만 촘촘히 확인한다.
- 사람 많음은 인원 추정치보다 화면 점유·공간 깊이·동선·시간대를 함께 기록한다. 같은 순간·같은 구도를 반복 추천하지 않는다. 장소 표지·촬영 메모로 장소를 검증하고 불명확하면 미확인으로 둔다.
- 선별 행: sourceId/mediaId, source path, sourceInSec/sourceOutSec, 촬영 날짜·시각·시간대·장소·근거와 확신도, 보이는 행동, 훅/전개/먹거리/반응/브리지 역할, 사용 추천 이유, 화면·음성 문제, 대체 구간. 한 클립 안에서 장소가 바뀌면 구간별로 기록한다.

## 4. 편집 가능한 초벌 만들기

- 새 비주얼 작업은 `templates({command:'search'})`로 한 번 참고하되 템플릿을 강제하지 않는다. 선택한 시작점만 inspect/use하고, 공개 배포나 publishTemplate은 요청 범위가 아니다.
- 현재 entry 파일을 읽고 사용자 수정사항을 보존한다. 미디어는 반드시 `src='kino:<media_id>'`로 연결한다. 로컬 경로·서명 URL·base64를 JSX 자산으로 박지 않는다.
- Kino는 browser ESM 프로젝트다. 프로젝트 소스에 package.json, npm 설치, `<Composition>` 등록, public 폴더를 추가하지 않는다. JSX inline style을 사용한다. CSS/Tailwind/className·CSS animation을 사용하지 않는다.
- 미디어 삽입·순서·trim·분할·길이·ripple은 `timelineGet`의 안정된 clipId와 `timelineEdit`로 처리한다. 새 자막·공간 배치·시각 스타일은 JSX에서 만든다. `timelineEdit`의 applied뿐 아니라 validationError/bundleError/runtimeError/executionSkipped를 읽는다. 실패 응답이어도 일부 편집은 저장되어 있을 수 있으므로 맹목 재실행하지 않는다.
- JSX 컴포넌트 추가·이동 등 구조를 바꾼 뒤에는 `timelineGet`을 다시 읽고 레이어명·소스·구간을 대조한다. TEST01에서는 Caption 추가 후 영상 clipId 접두부가 바뀌었다. 타임라인 도구가 특정 인스턴스용 컴포넌트 복사본을 만들 수도 있으므로 이후 공통 스타일 수정 전에 현재 호출과 소스를 확인한다.
- 현재 Kino는 `comment/reply/resolve`와 `set/insert` 등 편집 연산을 한 호출에 섞으면 거절한다. 주석과 실제 편집을 별도의 `timelineEdit` 호출로 실행한다. 수정 후 실제 화면을 재검수한 항목만 resolve한다. 현재 도구의 오류·명세가 이 기록보다 우선이다.
- 타이밍은 `3s`, `90f`처럼 단위를 명시한다. JSX에서는 실제 composition fps를 `useVideoConfig()`로 받아 계산한다. `trimBefore`, `startFrom` 및 sourceStart 프레임은 **소스 fps가 아닌 composition fps** 기준이다. sourceInSec는 원본 내 시각, timelineStart는 편집본 내 시각으로 분리한다. 속도·trim은 부모와 자식에 중복 적용하지 않는다.
- 독립 편집 클립마다 명시적 `<Sequence layout='none'>` 노드를 만들고 root fragment 아래 형제 레이어로 둔다. 컷 목록을 `.map()`이나 helper로 숨기지 않는다. 자막 도구가 만든 공식 segment 구조는 별도 계약을 그대로 유지한다.
- 텍스트 레이어 이름은 `훅`, `본문 요점`, `상단 주제` 등 역할이 드러나도록 하고, `zIndex`는 실제 겹치는 레이어의 순서에만 사용한다. 화면에 보이는 트랙 번호는 고정 식별자가 아니다.
- 초벌 뒤 텍스트·컷·VO/BGM/SFX를 각각 수정할 수 있어야 한다. 한 편을 단일 렌더 영상으로 굳혀 놓고 편집 원본이라 부르지 않는다.
- 자막 위치·폰트·주제 고정 여부는 편별 선택이다. 편집자가 바꿀 값은 현재 `schema-knobs.md`에 맞는 nonempty literal defaultProps와 필요할 때 zod schema로 노출한다. root는 incoming props를 실제로 사용해야 한다. 대주제 on/off, 자막 배치 모드, 텍스트 크기·색·위치 등만 유용하게 열고 과도한 컨트롤을 만들지 않는다. 배열은 현재 inspector에서 읽기 전용일 수 있어 컷 목록을 배열 컨트롤 하나에 숨기지 않는다.

## 5. 자막·대본·음성

원음 대사 자막은 `timelineGet`에서 실제 소스 clipId 선택 → `addCaptions({projectId,clipId})` → 반환된 JSON와 componentFilePaths를 수정한다. 설치된 자막 JSON이 단일 기준이며 같은 단어를 별도 JSON에 복사하거나 또 자막을 삽입하지 않는다. 기존 linked captions는 보존한다. segment.from은 composition 절대 프레임, word.from은 segment 상대 프레임이다. 원본 trim·재생속도를 도구가 반영하므로 다시 변환하지 않는다. 정보형 후킹 문구·요약 자막은 전사와 구별하고, 실제로 말하지 않은 내용을 음성 전사인 것처럼 만들지 않는다.

`getEffectiveTranscript`로 타임라인에서 실제 들리는 대본을 확인한다. `lookupTimelineText`로 원하는 말의 시점을 찾으며 근사 타이밍은 단어 단위 정밀 편집의 근거로 쓰지 않는다. 한 문장의 뜻이 바뀌거나 인터뷰 동의 맥락이 잘리지 않도록 원음 범위도 확인한다.

목소리가 필요한 편은 방향·대본을 편집자에게 제시한 뒤 해당 요청 범위에서 ElevenLabs를 사용한다. 자막만으로 충분한 짧은 현장 영상에는 VO를 자동 추가하지 않는다.

### ElevenLabs 연결 경로

1. 연결 도구가 있으면 현재 ElevenLabs `creative-studio` 가이드와 live tool schema를 읽는다. `creative_list_voices`에서 한국어·목적에 맞는 실제 voice_id를 찾는다. 고정 예시 voice ID를 복사하지 않는다. 스킬 문서의 모델 기본값과 live tool이 다를 수 있으므로 현재 도구 명세가 우선이다.
2. `creative_generate_speech`는 비용을 쓰는 실제 생성이다. 필요한 대본·voice_id·허용 모델을 전달하고 중복 호출을 재시도로 사용하지 않는다. 후보 수 기본값이 여러 개일 수 있으므로 편집자와 정한 생성 수를 정확히 반영한다. 일괄 생성·여러 후보는 estimate_only로 예상량을 먼저 확인한다.
3. 결과 뷰가 상태를 추적하면 기다린다. 뷰가 없을 때만 현재 도구 지침의 flow_id/session_ids로 상태를 확인한다. 완료 전 빈 자산을 Kino에 넣지 않는다.
4. 완료된 음원을 승인된 프로젝트 자산 위치에 저장·검증하고, 생성 기록의 flow/node/session/generation ID·모델·voice ID·대본·파일 해시를 남긴다. 임시 서명 URL은 기록·소스에 넣지 않는다. API 토큰·쿠키·키는 출력하지 않는다.
5. 음원 파일을 `addMediaToKino`로 가져와 mediaId로 타임라인에 넣는다. 실제 발음·속도·쉼을 확인하고 음원 길이에 맞게 컷과 자막을 조정한다. 글자 수로 가짜 단어 타이밍을 만들지 않는다. 필요한 경우 Kino의 전사·word timing 완료 후 addCaptions를 사용한다.
6. ElevenLabs 연결이 없는 Claude 환경은 준비된 ElevenLabs SDK/CLI와 안전한 인증을 사용할 수 있다. 설치·비밀키 입력을 임의로 수행하지 않는다. 인증 부재이면 대본·컷 편집까지 진행하고 VO만 보류한다고 명확히 알린다.

BGM·효과음은 `music-selection` 및 관련 audio 가이드를 읽는다. 실제 트랙 정보와 허용 용도를 기록하고, 실제 본편에 레퍼런스 음원을 자동 재사용하지 않는다. 사용자가 명시한 내부 테스트는 용도·출처·구간을 기록하고 본편 사용 허용과 구분한다. `Audio`는 `@remotion/media`에서 가져오고 `kino:` 자산을 사용한다. 말이 묻히지 않도록 음량을 조정하되 파형·BPM·자동 라벨을 청취 확인이라고 보고하지 않는다. 음악·SFX의 시작/끝과 잔향을 확인하고 의미 없는 riser·whoosh 반복을 피한다.

## 6. 검수·저장·재편집

- 첫 렌더 성공 즉시 `projectScreenshot`, 이후 외형 변경마다 다시 확인한다. 첫 0~2초 훅, 중간 자막, 대주제와 얼굴·음식 간섭, 우측/상하 Instagram UI 안전영역, 마지막 장면을 별도로 본다. timing-only 편집은 timelineEdit 결과로 확인할 수 있다.
- 최종 자막 문구·노출 시작·종료 및 컷 리듬은 `timelineGet`으로 검증한다. 한 장의 screenshot은 속도·컷·오디오 검증이 아니다. 과도한 렌더 부하가 예상되면 projectProfile을 확인한다.
- 저장 뒤 `getCurrentKinoContext({projectId})`로 mountStatus.error와 recentWarnings를 확인한다. 오래된 warning과 현재 error를 구분한다. 현재 동기화 오류가 있으면 완료로 보고하지 않는다.
- `exportVideo`에는 기존의 승인된 Export 목적지, 실제 projectId, 파일명을 전달한다. renderTaskId로 `getVideoExportTask`의 done/error까지 확인한다. export 시작과 완료를 구분하고 실제 출력 파일의 존재·길이·화면·음성을 확인한다.
- Adobe/Resolve 편집 파일이 별도로 요청될 때만 `exportProject`의 preflight → review/download를 사용한다. editable ZIP은 원본 미디어를 포함하지 않으며 Kino 자체 시퀀스 포맷이 아니다.
- 수정 요청은 편 인덱스로 해당 projectId·현재 코드를 다시 연다. 이전 승인본 스냅샷·렌더를 보존하고 해당 컷/문구만 수정한다. 최신 상태·남은 검수·출력 경로를 기록한다. 스냅샷만 복사했다고 다른 PC의 Kino 연결·미디어 재연결·Dropbox 동기화가 검증된 것은 아니다.

### 느린 렌더를 확인할 때

기존 코덱·크기·fps·품질·실제 프레임 수·소요 시간을 먼저 기록한다. 지원되는 옵션만 사용해 같은 2초 구간에서 기준 설정과 검수용 낮은 출력 해상도/품질을 비교한다. 편집 좌표계를 줄이는 것과 출력 배율을 바꾸는 것을 구분한다. 더 빠른 설정은 실제 출력 시간·프레임·화질을 확인한 뒤 적용한다.

GPU 프로세스 존재나 VRAM 점유는 하드웨어 인코딩 사용 증거가 아니다. 실제 렌더 중 대상 프로세스의 인코딩·디코딩·3D 사용량과 렌더 기록을 함께 관찰한다. 대기 상태의 GPU 0%로 과거 렌더가 CPU 전용이었다고 결론내리지 않는다. FFmpeg 속도를 Kino 렌더 속도로 대체 보고하지 않는다.

## 검증 범위

2026-11-05 TEST01에서 로컬 레퍼런스 가져오기, 신규 1080×1920/30fps 프로젝트, DOCUMENT/MEDIA bin 정리, 8개 영상 구간의 30초 타임라인, 독립 혼합 오디오 트랙·편집 자막, 장면별 배치 수정, 구간/문구 재검수, 타임라인 주석·해결 및 mount 오류 없음까지 확인했다. 상세 검증 상태는 [테스트 기록](kino-test-validation.md)에 구분한다. 수동 요점 자막을 시험한 것이며 `addCaptions` 전사 자막·ElevenLabs 생성·다른 PC 재연결은 미검증이다. 현재 Free workspace 안내는 Are.na/YouTube 연구 도구 사용을 막으므로 반복 호출하지 않는다. 로컬 촬영본·라이브러리 편집 경로는 별개다.
