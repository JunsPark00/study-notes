# 책 추가 안내

책마다 별도 원고·목차·출처 파일을 만들고 `content/books.json`에 한 항목을 추가합니다. 사이트 공통 HTML이나 JavaScript는 수정하지 않아도 됩니다.

## 1. 원고와 목차 만들기

권장 구조:

```text
content/books/<book-id>/
  chapters.json
  attribution.md
  chapter01.md
  chapter02.md
```

`chapters.json`은 다음 구조의 배열입니다. 아래는 형식 예시이며 실제 책을 등록하기 전에는 공개 등록부에 추가하지 않습니다.

```json
[
  {
    "number": 1,
    "title": "첫 장 제목",
    "file": "books/<book-id>/chapter01.md",
    "description": "이 장에서 무엇을 배우는지 짧게 설명합니다.",
    "tags": ["개념 A", "개념 B"],
    "category": "FOUNDATIONS"
  }
]
```

필수 필드는 `number`, `title`, `file`입니다. `number`는 책 안에서 중복되지 않는 양의 정수이며 연속될 필요는 없습니다. 배열에 쓴 순서가 화면의 목차와 이전·다음 장 순서입니다. 장 수 제한은 없습니다. 설명을 생략하면 책 설명을 사용하며 태그와 카테고리는 선택 사항입니다.

원고는 Markdown입니다. 맨 위 `# 장 제목`은 페이지 제목과 중복되지 않도록 제거합니다. 본문은 `##`로 나누면 장별 목차와 검색 문단이 자동 생성됩니다. `##`가 없어도 본문 전체를 검색할 수 있습니다. 인라인 수식은 `$...$`, 여러 줄 수식은 단독 줄의 `$$` 사이에 씁니다. 코드 펜스 안의 내용은 그대로 보존됩니다. KaTeX 문법 오류가 있으면 빌드는 중단됩니다.

같은 책의 다른 장을 `[다음 장](chapter02.md)`처럼 상대 Markdown 링크로 연결하면 등록된 HTML 경로로 변환합니다. 다른 책으로 연결할 때는 해당 책의 공개 경로를 사용하세요. 본문 HTML은 실행하지 않습니다.

`attribution.md`에는 `# 출처와 이용 안내`를 하나만 두고 저자, 제목, 참고 판본, 공식 교재 안내 링크와 직접 작성한 보충 자료의 범위를 기록합니다. 원전 PDF를 저장하거나 직접 PDF 링크로 연결하지 않습니다. 비공개 저장소 주소·개인 정보·출판사 도판은 포함하지 않습니다.

## 2. 책 등록하기

`content/books.json` 배열에 실제 책 한 항목을 추가합니다:

```json
{
  "id": "<book-id>",
  "title": "책 제목",
  "subtitle": "부제",
  "authors": ["저자 이름"],
  "category": "주제 분류",
  "description": "책의 주제와 이 노트의 학습 범위를 설명합니다.",
  "edition": "참고 판본",
  "language": "한국어 학습 노트",
  "officialUrl": "https://공식-교재-안내-주소/",
  "chaptersFile": "books/<book-id>/chapters.json",
  "attributionFile": "books/<book-id>/attribution.md"
}
```

필수: `id`, `title`, 비어 있지 않은 `authors` 배열, `category`, `description`, `chaptersFile`, `attributionFile`.

- `id`는 URL에 쓰는 고유 값이며 영문 소문자, 숫자와 단어 사이 하이픈만 허용합니다. 예: `linear-algebra`. 공개 후에는 기존 링크를 위해 바꾸지 않는 것이 좋습니다
- `subtitle`, `edition`, `language`, `officialUrl`은 선택 사항입니다
- 메타데이터와 원고 경로는 항상 `content/` 기준입니다. 절대 경로나 폴더 밖으로 벗어나는 경로는 허용하지 않습니다
- 등록 순서가 홈의 책 카드 순서입니다. 개별 책의 장 번호는 다른 책의 장 번호와 겹쳐도 됩니다
- `legacyChapterUrls: true`는 기존 MPC 주소를 보존하는 첫 책 전용입니다. 두 권 이상에 설정하면 빌드가 중단됩니다

실제 결과는 `/books/<id>/`, `/books/<id>/about.html`, `/books/<id>/chapters/chapterNN.html`에 생성됩니다. 홈, 책별 출처 목록과 검색 범위는 자동 갱신됩니다.

## 3. 선택 자료 추가하기

기본 원고만으로 책을 추가할 수 있습니다. 없는 자료의 빈 섹션은 표시하지 않습니다.

- `diagramsFile`: 도식 배열 JSON. 기존 `content/diagrams.json`의 구조를 참고하세요. 각 항목은 `chapter`, `id`, `image`, `svg`, `alt`, `caption`을 사용합니다. `image`·`svg`는 `docs/` 기준 경로입니다
- `formulasFile`: 수식 카드 배열 JSON. 각 항목은 `chapter`, 고유 `id`, `title`, `caption`, `latex` 배열, `assumptions` 배열, `attribution`을 사용합니다
- `videosFile`: 관련 영상 배열 JSON. 각 항목은 `chapter`, `provider`, `title`, `url`, `note`, `source_url`, `verification_note`를 사용합니다. 원전 공식 강의인지 별도 보충 자료인지 구분해 적습니다
- `examplesManifest`: `docs/` 기준 예제 manifest 경로. 현재는 단독 실행 Python 예제를 지원하며 기존 `docs/examples/manifest.json`의 구조를 사용합니다. 코드와 그래프 경로는 manifest가 있는 폴더 기준입니다. `README.ko.md`, `requirements.txt`, `validation_summary.json`도 같은 폴더에 둡니다. 새 책은 `docs/examples/<book-id>/`처럼 독립 폴더를 권장합니다

새 도식 파일은 `docs/assets/books/<book-id>/`에 저장하고, 원고에서 `![의미를 설명하는 대체 텍스트](assets/books/<book-id>/diagram.svg)`로 연결합니다. 이미지는 저작권·출처를 확인한 직접 제작 자료를 사용하세요.

`generatedAppendixHeading`은 기존 MPC 원고의 중복 수식·영상 부록을 구조화 자료로 대체하기 위한 명시적 호환 옵션입니다. 새 책에는 일반적으로 설정하지 않습니다. 설정하면 해당 `##` 제목부터 뒤의 원고를 대체하므로, 일반 본문을 제거하지 않도록 주의해야 합니다.

## 4. 빌드·검증·미리보기

```sh
npm run build
npm run check
npm test
npm run serve
```

확인할 것:

1. 홈에 실제 책 카드가 보이며 책 소개·목차로 이동하는지
2. 책 제목, 출처, 장별 목차와 이전·다음 링크가 해당 책 안에서 이어지는지
3. 모든 책 검색과 책별 검색에서 결과에 책 제목이 붙는지
4. 수식·도식·모바일 배치·키보드 탐색·그림 확대가 잘 동작하는지
5. 다른 책과 기존 MPC 주소도 계속 읽히는지

테스트는 가상 두 번째 책을 임시 폴더에서만 생성합니다. 실제 등록부와 배포 폴더에는 넣지 않습니다. 빌드를 다른 폴더에서 점검하려면 `SITE_CONTENT_DIR`, `SITE_OUT_DIR`, `SITE_QA_DIR`, `SITE_BASE`를 지정할 수 있습니다. 별도 출력 폴더에도 참조하는 도식·예제 자산을 먼저 복사해야 합니다.

생성된 `docs/`까지 저장소에 반영해야 GitHub Pages에 적용됩니다. 빌드와 테스트 자체는 게시하지 않습니다.
