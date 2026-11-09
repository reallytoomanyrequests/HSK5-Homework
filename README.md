# 기솔의 HSK 5급 스터디룸 — 설치 메모

## 1. GitHub Pages (사이트)
1. GitHub에 Public 저장소 `HSK5-Homework` 생성
2. 이 폴더의 파일 전부 업로드 (`index.html`, `manifest.json`, `icon.png`, `homework/`)
3. Settings → Pages → Branch `main` → Save
4. 주소: `https://reallytoomanyrequests.github.io/HSK5-Homework/`

## 2. 구글 시트 서버 (제출·피드백·알림)
1. 구글 시트 새로 만들기
2. 확장 프로그램 → Apps Script → 기본 코드 지우고 `apps-script/Code.gs` 붙여넣기
3. 코드 맨 위 설정 채우기
   - `TEACHER_PIN` 선생님 모드 비밀번호
   - `APP_URL` GitHub Pages 주소 (끝에 `/`)
   - `STUDENT_EMAIL` / `TEACHER_EMAIL` 이메일 알림 (선택)
   - `NTFY_STUDENT` / `NTFY_TEACHER` 폰 푸시 알림 토픽 (선택, 아래 참고)
4. 배포 → 새 배포 → 웹 앱 → 실행 사용자 **나** / 액세스 **모든 사용자** → 배포 → 권한 허용
5. 웹 앱 URL(`.../exec`) 복사 → `index.html`의 `SUBMIT_URL`에 붙여넣기 → GitHub에 다시 업로드
6. Code.gs를 고칠 때마다: 배포 → 배포 관리 → 연필 → 버전 "새 버전" → 배포

## 3. 폰 푸시 알림 (ntfy, 무료)
1. 기솔 폰에 **ntfy** 앱 설치 (iOS/Android)
2. 앱에서 Subscribe to topic → 아무도 못 맞출 이름으로 (예: `gisol-hsk5-x7q2k`)
3. 그 이름을 `NTFY_STUDENT`에 입력 → 피드백 저장할 때마다 푸시 알림
4. 네 폰에도 같은 방식으로 다른 토픽 구독 → `NTFY_TEACHER` → 기솔 제출 시 알림
- ntfy 설치가 싫으면 이메일만 써도 됨 (Gmail 알림이 사실상 푸시 역할)

## 4. 매일 숙제 올리기
- `homework/YYYY-MM-DD/` 폴더째 업로드 (`set.json`, mp3, `answers.json`)
- `answers.json`이 있으면 제출 직후 정답·해설이 열리고 듣기·독해 자동 채점
- 폴더 목록은 자동 인식 (GitHub API). 실패 시 `homework/index.json` 사용

## 5. 선생님 모드
- 앱 오른쪽 위 "선생님" → 비밀번호 → 회차 열면 제출 현황(답·점수·작문 전문·녹음 링크) + 피드백 입력
