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

1. 새 신문판이나 과거 판본을 **`legacy/index_YYYYMMDDHHMM.html`** 규칙으로 업로드합니다(예: `legacy/index_202611270900.html`).
2. 별도로 루트 `index.html`을 교체하지 않아도, GitHub Actions(`.github/workflows/sync-archive.yml`)가 `legacy/index_*.html` 중 가장 최신 시각 파일을 자동으로 루트 `index.html`로 승격하고 `legacy/editions.json`과 `archive.js` 연결을 동기화합니다.
   - 로컬에서 즉시 반영할 때는 `python scripts/build_archive.py`를 실행한 뒤 커밋/푸시하면 됩니다.
   - 기존 루트 `index.html`이 `legacy/`에 아직 보관되지 않은 상태라면 승격 전에 `legacy/index_YYYYMMDDHHMM.html`로 자동 보존됩니다.
   - Actions 반영 직전에도 `archive.js`와 `legacy/index.html`이 GitHub API로 `legacy/index_*.html`을 탐색해 드롭다운/목록에 표시합니다.
