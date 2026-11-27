# 차곡 — Claude Code 작업 안내

선생님용 할 일 정리 프로그램. 공문·업무 메신저(GOE) 글을 붙여 넣으면 날짜를 찾아 할 일로 정리한다.
만든 사람: 심훈철(오남초). 배포: https://shimhuncheol.github.io/chagok/ (이 저장소의 `main` → GitHub Pages)

## 꼭 지킬 원칙
- **파일 하나**: 결과물은 `index.html` 하나. 더블클릭(file://)으로도, 인터넷 없이도 동작해야 한다.
- **서버·API·로그인·AI 토큰 없음**: 외부 요청을 새로 만들지 말 것. 할 일 찾기는 규칙 기반(정규식) 엔진이다.
  (예외: 자리 배치의 PDF 명부 읽기만 cdnjs 의 PDF.js 를 불러온다.
   예외 2: 📆 일정 협의 메뉴만 선생님이 넣은 '모여요' 웹 앱 주소(script.google.com …/exec)로 fetch 한다. 다른 메뉴는 그대로 인터넷 없이.)
- **내용은 브라우저에만**: IndexedDB(안 되면 localStorage) 에 저장. 어디로도 보내지 않는다.
- **화면 글은 존댓말·쉬운 말**: "~해요" 체. 개발 용어(파싱, 렌더 등) 대신 선생님이 쓰는 말.
- 사용자는 비개발자 선생님. 설명도 쉬운 한국어로.

## 폴더 구조
```
index.html              ← 빌드 결과 (직접 고치지 말 것! 8.5MB)
src/chagok.html         ← 실제로 고치는 소스 (~290KB, CSS+HTML+JS 한 파일)
src/assets/*.txt        ← 큰 덩어리: 글꼴(base64), 교표, OCR 엔진, 한국어 학습 데이터, 자리 배치 묶음
src/seats/original/     ← '우리 반 자리' 원본 (index.html·style.css·theme.css·app.js)
src/seats/recolor.py    ← 원본 CSS 고정 색 → 차곡 테마 변수로 바꾸기
src/seats/build_seats.py← 원본을 한 문서로 묶어 src/assets/seatApp.txt 생성
tools/build.py          ← src → index.html  (--check: 같은지 확인)
tools/smoke_test.py     ← 빠른 점검 (Playwright)
sw.js                   ← 오프라인 캐시 (버전 올릴 때 CACHE 이름도 올림)
manifest.webmanifest, icons/  ← 앱 설치(PWA)
README.md, OFL.txt, NOTICE.txt, LICENSE-Apache-2.0.txt ← 안내·라이선스
```
`src/chagok.html` 안의 `{{asset:이름}}` 은 빌드 때 `src/assets/이름.txt` 로 채워진다.

## 작업 순서
```bash
# 1) src/chagok.html 고치기   (자리 배치는 src/seats/ 고친 뒤 python src/seats/build_seats.py)
python tools/build.py           # 2) index.html 만들기
python tools/smoke_test.py      # 3) 점검 (처음 한 번: pip install playwright && python -m playwright install chromium)
# 4) 버전 올리기 (아래) → 5) git commit && git push  → 1~2분 뒤 사이트에 반영
```
커밋 전에 `python tools/build.py --check` 가 통과해야 한다 (index.html 과 소스가 같아야 함).

### 새 버전 낼 때 함께 바꿀 것
1. `src/chagok.html` 의 `const APP_VERSION = '1.8';`
2. `sw.js` 의 `const CACHE = 'chagok-v1.8';`
3. `README.md` 맨 아래 `차곡 v1.8` 과 기능 목록

## src/chagok.html 안의 순서 (JS 큰 제목 주석 `/* ===== */` 기준)
1. 할 일 찾기 엔진 (규칙 기반) — 날짜 표현(`11. 20.(금)`, `내일`, `다음 주 금요일`, 기간 `~`), 마감/행사 구분
2. 파일 읽기 (TXT · HWPX · DOCX · HWP)
3. 저장소 — `Store` (IndexedDB 'todo-organizer', kv 저장소. `Store.getKV/putKV` 로 다른 키도 저장)
   + 사진 `ImgStore`(IndexedDB 'chagok-images') + 그림 속 글자 읽기(OCR: `ocrWorker()`, `ocrImage()`)
4. 상태 — `S`(tasks·sources·memos·settings…), 테마 `THEMES`, 교표 색 뽑기 `extractColors`, `applyTheme()`
5. 화면 그리기 — `render()` 가 `UI.tab` 에 따라 `renderInput/Review/Todo/Library/School/Memo/Backup` 로 `#main` 을 통째로 다시 그림
6. 동작 + 🪑 자리 배치(`SEAT`, `seatMount`, `ChagokSeat`) + 🏃 달리기 뽑기(`PICK`, `pickMount`, `pickStart`) + 붙여넣기→자동 정리(`organizePaste`, `UI.draft.cands`)
7. 모달(`openModal`)·토스트(`toast`)·테마, 명령창(Ctrl+K, `add(...)` 로 항목 추가)
8. 이벤트 연결 — 클릭은 `data-action="..."` 하나의 switch 에서 처리
9. 시작

메뉴(탭) 추가: 사이드바 `<button class="tab" data-tab="...">`, `PAGE_TITLE`, `TABS`, `render()` 의 fn 표 세 곳.

## 디자인
- CSS 변수: `--bg --surface --surface2 --text --text2 --text3 --border --primary --on-primary --soft --soft-text --mark --font --radius --shadow`
- 기본 디자인 `onam`(오남초 교표 색). 그 밖에 edufine(K-에듀파인)·neis(나이스)·aurora·chagok·toss·naver·kakao·claude·chatgpt, 그리고 교표로 만든 `school`.
  학교 디자인은 `schoolVars(colors)` 가 인라인 변수로 넣고 `html[data-kind="school"]`.
- 회사 로고·상표는 넣지 않는다(이름만 "~ 스타일", 색 점 아이콘).
- 글꼴: Paperlogy(기본), K-에듀파인=나눔고딕 → `ChagokGothicE`, 나이스=Noto Sans KR → `ChagokSansN` 으로 **이름을 바꾼 부분 글꼴**(OFL 예약 글꼴 이름 규정 때문). 새 글자를 써야 하면 fonttools `pyftsubset` 으로 다시 만들고 이름도 유지.

## 🪑 자리 배치 (우리 반 자리)
- 원본 프로그램을 거의 그대로 `iframe srcdoc` 으로 띄운다. `#seatHost` 는 `#main` 밖에 있어 화면을 다시 그려도 유지된다.
- 원본 코드는 `src/seats/original/` 에서만 고치고, `build_seats.py` 가 다음을 바꿔 묶는다:
  `localStorage` → `SEATLS`(부모 `ChagokSeat.get/set` → 차곡 저장소 키 `seats-v1`),
  `window.Tesseract` → 차곡 내장 OCR(psm 11), 이름 글자 붙이기, 브랜드·바닥글 숨김, 좁은 화면 사이드바 폭.
- 색은 `recolor.py` 가 차곡 테마 변수로 바꾸고, 부모의 `seatTheme()` 이 변수·글꼴을 iframe 에 넣는다.
- 차곡 백업(`exportBackup`)에 `data.seats` 로 함께 들어가고, 불러오기 때 `seatReplace()`.
- 원래 사이트의 백업 파일(`우리반자리_날짜.json`)은 자리 배치 안의 **파일로 복원**으로 그대로 불러올 수 있어야 한다(형식 유지).

## 🏃 달리기 뽑기
- `#pickHost`(main 밖)에 한 번만 만들고 유지. canvas 2D 로 경기장·캐릭터를 그린다(사진이 있으면 얼굴 자리에 사진).
- 명단: 자리 배치 저장값(`SEAT.raw` 의 students: no·name·photo) → 없으면 `S.settings.pick.names`(직접 적은 이름).
- 순위는 출발 전에 `crypto.getRandomValues` 로 섞어 정하고, 달리는 모습(흔들림)만 연출. 결승 통과 시각이 순위대로라 화면과 결과가 항상 같다.
- 방식: `mode` 'count'(몇 명 뽑기, 뽑힌 학생은 used 에 기록) / 'all'(모두 순서 정하기, used 기록 안 함).
- 느린 화면: 실제 시간 대신 경주 시간 `PICK.vt` 를 `PICK.speed` 배로 흘린다. 선두가 바뀌면(역전, 한 경주 5번까지)·결승 직전에 잠깐 0.28배.
- 설정 `S.settings.pick`: mode·count·skipUsed·used(뽑힌 학생 id)·out(오늘 빠짐)·names·source·sound. `pickSet()` 은 같은 객체를 고쳐 쓴다(새 객체로 바꾸지 말 것).

## 📆 일정 협의 (모여요)
- 응답을 여러 사람에게서 모아야 해서 구글 Apps Script 웹 앱 **모여요**를 서버로 쓴다. 참가자는 모여요 페이지(…/exec?p=ID)에서 로그인 없이 제출.
- 모여요 원본: `src/meet/Code.gs`(서버: 시트 저장, `doGet` 페이지, `doPost` 차곡용 통로), `src/meet/index.html`(참가자·결과·웹 관리자 화면).
  고쳤으면 `python src/meet/build_meet.py` 로 `src/assets/meetGs.txt`·`meetPage.txt`(base64)를 다시 만든다 — 메뉴 안 '코드 복사' 버튼이 이걸 쓴다.
- 차곡 쪽 코드: `MEET`·`renderMeet`·`meetDo`(클릭은 `data-action="meet" data-do="..."`), 서버 부르기 `meetApi(fn, ...args)` = POST `{fn,args}` (text/plain 이라 사전 요청 없음).
  서버 함수: ping · createPoll · loadPoll · summaries · adminUpdate · adminDeleteResponse.
- 저장: `S.settings.meet = { url, list:[{id,key,title,at}] }` (백업 파일에 함께 들어감). `MEET_DEFAULT_URL` = 심훈철 계정(shimhuncheol@ssem.re.kr)의 Apps Script 프로젝트 '모여요 (차곡 일정 협의 서버)' 웹 앱 주소. 서버 코드를 고치면 그 프로젝트에 붙여 넣고 **배포 관리 → 수정 → 새 버전**으로 다시 배포(주소는 그대로). 6개월 지난 협의는 서버가 자동 정리.
- 관리 키(key)가 있어야 결과·설정을 볼 수 있다. 참가자 링크에는 key 가 없다.

## OCR (그림 속 글자 읽기)
Tesseract.js 5.1.1 + 한국어 tessdata_best 를 `src/assets/ocr*.txt` 로 넣었다. file:// 에서 blob 안의 importScripts 가 막혀서,
fetch 대체 + core + worker 를 **한 worker Blob** 으로 만든다. 이 구조는 건드리지 말 것.

## 하지 말 것
- `index.html` 을 직접 고치기 (빌드가 덮어씀)
- 학생 사진·이름이 든 실제 백업 파일을 저장소에 올리기
- 새 외부 라이브러리를 CDN 으로 불러오기 (오프라인이 깨짐) — 꼭 필요하면 assets 로 넣기
