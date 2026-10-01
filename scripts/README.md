# 웹사이트와 시각화 재생성

프로젝트 루트에서 실행합니다.

- `npm ci && npm run build`: Markdown과 TeX를 정적 HTML로 만들며 수식 오류가 있으면 중단합니다
- `npm run check`: 등록된 모든 책의 로컬 링크·앵커·이미지·KaTeX 글꼴·장별 수식 카드·예제 체크섬·검색 색인과 기존 주소를 검사합니다
- `npm test`: 임시 폴더의 두 번째 책으로 다중 책 등록·탐색·검색·잘못된 등록 거부를 검사합니다
- `npm run verify`: 빌드, 정적 검사와 다중 책 테스트를 순서대로 실행합니다
- `npm run serve`: `http://127.0.0.1:8765/study-notes/`에서 미리 봅니다
- `python scripts/generate_diagrams.py`: 새로 제작한 도식 17개의 PNG·SVG를 `docs/assets/diagrams/`에 다시 만듭니다
- `python scripts/generate_formulas.py`: `content/formulas.json`으로 선택적으로 수식 카드 PNG 32개를 `docs/assets/formulas/`에 만듭니다. 공개 사이트에서는 이미지 대신 TeX·MathML 카드를 사용합니다

시각화 의존 패키지는 `scripts/requirements.txt`에 있습니다. Noto Sans CJK Regular/Bold 글꼴이 필요하며, 설치 경로가 다르면 `MPC_FONT_REGULAR`와 `MPC_FONT_BOLD`를 지정하세요. 한 도식만 재생성하려면 `MPC_DIAGRAM_ONLY=ch08_shooting_structure`와 같이 도식 ID를 설정합니다.

장별 독립 실행 예제와 별도 검증 방법은 `docs/examples/README.ko.md`를 보세요. 개념 시각화와 작은 실행 예제는 교재 전체의 계산·증명을 재현하거나 일반적인 제어 안전성을 보증하지 않습니다.

책 추가는 [책 등록 안내](../content/ADDING_BOOKS.md)를 참고하세요. 기존 MPC 시각화 생성기는 MPC 전용이며 새 책을 등록할 때 실행할 필요가 없습니다.
