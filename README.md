# Study Notes

책별로 정리하는 한국어 학습 노트입니다. 첫 번째 책은 Rawlings·Mayne·Diehl의 *Model Predictive Control: Theory, Computation, and Design*, 2판 1쇄(2017)입니다.

## 읽기

GitHub Pages: https://junspark00.github.io/study-notes/

- 8개 장의 개념 설명, 가정, 손계산 예제와 보충 문제
- 직접 제작한 도식 17개, 웹 수식 카드 32개
- 미리 조판한 KaTeX 수식과 접근성을 위한 MathML
- 각 장에서 단독 실행할 수 있는 Python 예제 8개
- 전체 본문 검색, 장별 목차, 모바일 레이아웃, 그림 확대

## 사이트 만들기

Node.js 20.11 이상과 npm이 필요합니다.

```sh
npm ci
npm run build
npm run check
npm run serve
```

로컬 미리보기는 `http://127.0.0.1:8765/study-notes/`입니다. `docs/`가 바로 배포 가능한 정적 사이트이며 런타임 서버, CDN, API 키가 필요하지 않습니다. GitHub Pages의 배포 소스를 `main` 브랜치의 `/docs`로 지정합니다. `.nojekyll`을 포함합니다.

기본 경로는 `/study-notes/`입니다. 다른 경로에 배포한다면 `SITE_BASE=/다른경로/ npm run build`로 지정하세요. 외부 게시나 GitHub 저장소 변경은 빌드 과정에 포함되지 않습니다.

## 파일 구조

- `content/chapters/`: 한국어 학습 노트 원문
- `content/*.json`: 장, 도식, 수식, 관련 영상 메타데이터
- `src/`: 공통 스타일, 검색·탐색·확대 기능
- `scripts/build.mjs`: 정적 HTML·검색 색인·KaTeX 자산 생성
- `scripts/generate_*.py`: 새로 제작한 시각화 재생성
- `docs/assets/diagrams/`: 버전 관리되는 원본 생성 도식
- `docs/examples/`: 독립 실행 코드, 실행 안내와 검증 결과
- `docs/`: 완성된 공개 사이트. 생성 자산과 예제 파일도 배포에 포함

`npm run build`는 자산 원본을 삭제하지 않으며 모든 배포 파일은 저장소에 포함됩니다. 시각화와 실행 예제의 재생성 방법은 [스크립트 안내](scripts/README.md)와 [예제 안내](docs/examples/README.ko.md)를 참고하세요.

`npm run check`는 정적 무결성 검사입니다. 검색·그림 확대·키보드 탐색과 실제 화면 크기별 배치는 브라우저에서 별도로 점검해야 합니다.

## 출처와 이용 범위

공식 번역이나 저자·출판사가 승인한 자료가 아닙니다. [저자 공식 교재 페이지](https://sites.engineering.ucsb.edu/~jbraw/mpc/)와 [출처·이용 안내](content/ATTRIBUTION.ko.md)를 확인해 주세요. 교재 모델·예제는 해당 본문에 출처를 표시하고, 직접 구성한 문제는 학습용 보충 예제로 구분합니다. 원전 PDF·스캔·출판사 도판은 포함하지 않습니다.

AI의 도움으로 작성되어 오류가 있을 수 있습니다. 수식·가정·수치 결과는 원전과 독립 계산으로 검토해 주세요. 이 저장소는 교재나 제3자 자료에 대한 포괄적인 재사용 허락을 부여하지 않습니다. 포함된 KaTeX 소프트웨어의 MIT 라이선스는 `docs/assets/katex/LICENSE.txt`에 있으며 학습 자료 전체에 적용되는 라이선스가 아닙니다.
