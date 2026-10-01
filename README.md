# Study Notes

여러 책을 한 권씩 추가하며 쌓아 가는 한국어 학습 노트입니다. 책장 → 책 소개·목차 → 장별 본문으로 읽습니다.

공개 사이트: https://junspark00.github.io/study-notes/

현재 세 권, 총 40개 장을 읽을 수 있습니다.

- Rawlings·Mayne·Diehl, *Model Predictive Control: Theory, Computation, and Design*, 2판 1쇄(2017): 8개 장, 직접 제작한 도식 17개, 수식 카드 32개, 독립 Python 예제 8개
- Nocedal·Wright, *Numerical Optimization*, 2판(2006): 19개 장, 새로 계산한 그래프 19개, 본문의 선택 가능한 수식, 독립 Python 예제 19개

Numerical Optimization의 설명·모델·계산·그림은 별도로 구성한 비공식 학습 자료입니다. [실행 안내](docs/examples/numerical-optimization/README.ko.md)와 [책별 출처](content/books/numerical-optimization/attribution.md)에서 범위와 검증 환경을 확인하세요.

- Lynch·Park, *Modern Robotics: Mechanics, Planning, and Control* (2017): 13개 장의 직접 작성한 보충 설명, 독립 Python 실험 13개, 새 계산 그림 26개. 전체 교재 번역이 아닙니다. [실험 안내](docs/examples/modern-robotics/README.ko.md)와 [출처](content/books/modern-robotics/attribution.md)를 확인하세요.

## 여러 책을 위한 구조

Modern Robotics 공개 자료를 수정할 때는 `content/books/modern-robotics/study-content.json`을 편집하고 다음 순서로 생성·검증합니다. 외부 원본 저장소 없이 재생성할 수 있습니다.

```sh
python scripts/build-modern-robotics.py
python docs/examples/modern-robotics/validate_all.py
npm run build
python scripts/check-modern-robotics-provenance.py
npm run check
npm test
```

Python 의존성은 해당 예제 폴더의 `requirements.txt`로 설치합니다. 공개 allowlist·파일 해시·검증 한계는 `docs/examples/modern-robotics/provenance.json`에 기록합니다. push/PR 시 같은 검증을 CI에서 실행합니다.

- 홈은 책 카드가 모인 책장입니다
- `/books/<book-id>/`에는 각 책의 소개와 전체 목차가 있습니다
- `/books/<book-id>/chapters/chapterNN.html`에는 장별 노트가 있습니다
- `/books/<book-id>/about.html`에는 그 책의 참고 판본과 출처를 기록합니다
- 전체 검색은 책 제목을 표시하며, 한 권만 골라 검색할 수도 있습니다
- 기존 MPC `/chapters/chapter01.html`부터 `chapter08.html`까지의 주소도 그대로 읽을 수 있습니다. 기존 앵커는 유지되며 canonical과 탐색 링크는 새 책별 경로를 가리킵니다

새 책을 추가할 때 공통 템플릿을 수정할 필요가 없습니다. [책 추가 안내](content/ADDING_BOOKS.md)에 따라 원고·목차·출처를 만들고 `content/books.json`에 등록하세요. 장 수, 번호, 제목, 순서와 선택 자료는 책마다 독립적입니다.

## 빌드와 검증

Node.js 20.11 이상, npm과 Python 3.10 이상이 필요합니다.

```sh
npm ci
npm run build
npm run check
npm test
npm run serve
```

로컬 미리보기: `http://127.0.0.1:8765/study-notes/`

`docs/`가 바로 배포 가능한 정적 사이트입니다. 실행 시 서버, CDN이나 API 키가 필요하지 않습니다. GitHub Pages의 배포 소스는 `main` 브랜치의 `/docs`이며 `.nojekyll`을 포함합니다. 외부 게시나 저장소 변경은 빌드 과정에 포함되지 않습니다.

기본 경로는 `/study-notes/`입니다. 다른 경로에 배포한다면 `SITE_BASE=/other-notes/ npm run build`처럼 지정합니다. 경로에는 영문, 숫자, 밑줄과 하이픈을 사용합니다. 정적 검사에도 같은 `SITE_BASE`를 전달하세요.

- `npm run check`: 등록된 모든 책의 페이지·로컬 링크·앵커·수식 카드·그림·예제 체크섬·검색 색인과 기존 주소를 검사합니다
- `npm test`: 임시 폴더에서 두 번째 테스트용 책을 추가하고 책장·책별 탐색·범위 검색·서로 다른 장 번호·잘못된 등록 거부·다른 배포 경로를 검사합니다. 테스트 책은 공개 `content/`나 `docs/`에 들어가지 않습니다
- 실제 화면 배치, 키보드 탐색, 검색 창과 그림 확대는 브라우저에서 별도로 점검합니다

## 파일 구조

- `content/books.json`: 책 등록부와 책별 메타데이터 파일 경로
- `content/chapters/`, `content/chapters.json`: 기존 MPC 원고와 목차
- `content/books/<book-id>/`: 새 책의 원고·목차·출처에 권장하는 위치
- `src/`: 공통 스타일, 검색·탐색·그림 확대 기능
- `scripts/build.mjs`: 등록부에서 정적 HTML, 검색 색인과 KaTeX 자산 생성
- `scripts/test-multi-book.mjs`: 격리된 다중 책 회귀 테스트
- `docs/assets/diagrams/`: 기존 MPC 도식 원본. 새 책의 자산은 `docs/assets/books/<book-id>/` 사용 권장
- `docs/examples/`: 기존 MPC 독립 실행 코드와 검증 결과
- `docs/assets/page-manifest.json`: 빌드가 생성한 HTML 목록
- `docs/`: 완성된 공개 사이트와 배포 자산

빌드는 기존 이미지·예제 자산을 삭제하지 않습니다. 이전 빌드의 페이지 목록에 있는 HTML만 정리하므로, 등록부에서 제거한 책의 생성 페이지가 남지 않습니다. 생성 HTML을 직접 편집하지 말고 원고와 공통 소스를 수정하세요. 독립 실행 예제 및 시각화 재생성은 [스크립트 안내](scripts/README.md)와 [예제 안내](docs/examples/README.ko.md)를 참고하세요.

## 출처와 이용 범위

공식 번역이나 저자·출판사가 승인한 자료가 아닙니다. 책별 출처 안내에서 판본과 이용 범위를 확인하세요. 교재 모델·예제는 해당 본문에 출처를 표시하며, 직접 구성한 문제는 학습용 보충 예제로 구분합니다. 원전 PDF·스캔·출판사 도판은 포함하지 않습니다.

AI의 도움으로 작성되어 오류가 있을 수 있습니다. 수식·가정·수치 결과는 원전과 독립 계산으로 검토해 주세요. 이 저장소는 교재나 제3자 자료에 대한 포괄적인 재사용 허락을 부여하지 않습니다. KaTeX의 MIT 라이선스는 `docs/assets/katex/LICENSE.txt`에 있으며 학습 자료 전체에 적용되지 않습니다.
