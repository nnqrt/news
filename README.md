# news

한반도 안보·군사 OSINT 인터랙티브 신문판 (`news.bubutech2.com`)

## 구조

- `index.html`: 현재 메인 최신판
- `legacy/index_YYYYMMDDHHMM.html`: 과거 시점 판본 아카이브 (날짜/시각 기준, 중복 제거)
- `legacy/index.html`: 역대 판본 아카이브 목록 페이지 (`/legacy/`)
- `legacy/editions.json`: 전체 판본 메타데이터 매니페스트
- `archive.js`: 메인판 및 모든 과거 판본 상단에 시점 이동 드롭다운/아카이브 링크를 자동 삽입하는 공용 스크립트
- `scripts/build_archive.py`: `legacy/editions.json` 생성 및 HTML 파일에 `archive.js` 자동 연결 스크립트

## 앞으로 새 콘텐츠 추가 방법

1. 과거 판본을 보존할 때는 `legacy/index_YYYYMMDDHHMM.html` 규칙으로 저장합니다.
2. 새 메인판 `index.html` 또는 `legacy/index_*.html`을 올릴 때:
   - 로컬에서는 `python scripts/build_archive.py`를 실행한 뒤 커밋/푸시하면 `legacy/editions.json`과 `archive.js` 연결이 자동 반영됩니다.
   - 웹에서 직접 파일을 업로드하더라도 `archive.js`와 `legacy/index.html`이 GitHub API로 `legacy/index_*.html`을 자동 탐색해 목록에 표시합니다(`.github/workflows/sync-archive.yml`이 활성화된 경우 `editions.json`도 자동 갱신).
