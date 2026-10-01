# Numerical Optimization 독립 실행 보충 예제

Jorge Nocedal·Stephen J. Wright의 *Numerical Optimization*, 2판(2006)에 등장하는 수학적 주제를 공부하기 위해 새로 작성한 19개 작은 실험입니다. 각 파일은 다른 장의 코드·외부 데이터·계정·네트워크 연결 없이 단독으로 실행됩니다. 원전의 코드, 도판, PDF 또는 전체 연습문제 해답을 배포하는 자료가 아닙니다.

## 한 장만 실행하기

원하는 `chapterNN.py`와 이 폴더의 `requirements.txt`를 같은 폴더에 저장합니다. Python 3.10 이상에서 다음 명령을 실행합니다. 실제 게시 전 검증 환경은 Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8입니다. 다른 버전에서는 마지막 자릿수와 솔버의 중간 경로가 달라질 수 있습니다.

```sh
python -m pip install -r requirements.txt
python chapter01.py --output-dir output/chapter01
```

`--output-dir`은 모든 장에 공통으로 구현된 실제 옵션입니다. 폴더를 지정하지 않아도 각 코드의 기본 폴더에 저장되지만, 다른 실행과 섞이지 않도록 명시하는 편이 좋습니다. 실행하면 PNG 한 개와 JSON 한 개가 생깁니다. 장에 따라 JSON 파일명은 `chapterNN.json` 또는 `chapterNN-results.json`이며, 내용에는 새로 계산한 수치와 검사 결과가 담깁니다. 수치 assertion이 실패하면 0이 아닌 종료 코드로 중단합니다. `python -O`는 assertion을 끄므로 검증 실행에 사용하지 마세요.

한글 글꼴이 설치되어 있으면 한글 라벨을 사용하고, 없으면 코드에 포함한 영문 라벨을 사용합니다. 글꼴을 자동으로 내려받지는 않습니다. 계산은 글꼴에 의존하지 않습니다.

## 장별 실행 명령

아래는 각 파일을 현재 폴더에 저장했을 때의 명령입니다.

```sh
python chapter01.py --output-dir output/chapter01
python chapter02.py --output-dir output/chapter02
python chapter03.py --output-dir output/chapter03
python chapter04.py --output-dir output/chapter04
python chapter05.py --output-dir output/chapter05
python chapter06.py --output-dir output/chapter06
python chapter07.py --output-dir output/chapter07
python chapter08.py --output-dir output/chapter08
python chapter09.py --output-dir output/chapter09
python chapter10.py --output-dir output/chapter10
python chapter11.py --output-dir output/chapter11
python chapter12.py --output-dir output/chapter12
python chapter13.py --output-dir output/chapter13
python chapter14.py --output-dir output/chapter14
python chapter15.py --output-dir output/chapter15
python chapter16.py --output-dir output/chapter16
python chapter17.py --output-dir output/chapter17
python chapter18.py --output-dir output/chapter18
python chapter19.py --output-dir output/chapter19
```

## 전체 재검증

모든 `chapter01.py`–`chapter19.py`와 `validate_all.py`를 같은 폴더에 저장한 뒤 실행합니다.

```sh
python validate_all.py --output-dir validation_output
```

검증기는 각 파일을 서로 다른 임시 폴더에 하나씩 복사하고 Python 격리 모드(`-I`)의 새 프로세스로 실행합니다. 다른 장 파일이나 이전 결과 없이 assertion, 새 JSON 저장, 새 PNG 생성을 확인합니다. 결과를 `validation_output/chapterNN/result.json`과 `figure.png`로 정규화해 모으고, 버전·코드 SHA-256·상태를 `validation_output/validation_summary.json`에 씁니다.

사이트와 함께 제공되는 `validation_summary.json`과 `validation_output/chapterNN/result.json`은 게시 전 별도로 다시 실행한 결과입니다. `manifest.json`은 코드 체크섬, 본문에서 확인할 주장, 검증 파일과 그림 경로를 연결합니다. 사이트의 그림은 같은 게시 전 실행에서 생성한 PNG입니다. 일부 manifest 경로는 사이트 배포 폴더 안의 상대 경로이므로, 한 파일만 내려받아 실행할 때 필요하지 않습니다.

## 검증 범위

- 1장: 새 에너지 구매 LP를 SciPy HiGHS로 풀고 일변수 소거 해와 대조
- 2–6장: 최급강하와 뉴턴, 선 탐색, 신뢰영역 하위문제, 선형 CG, BFGS·DFP·SR1의 작은 계산
- 7–12장: 행렬 없는 CG, 차분과 복소 스텝, 좌표 폴링, 비선형 최소제곱, Newton·Broyden, KKT와 민감도
- 13–19장: LP 심플렉스·원시쌍대 반복, 비선형 제약 기하, QP 활성집합, 벌점·증강 라그랑지안, 등식 SQP, 원시 장벽 경로

SciPy 호출을 사용하는 장은 자체 구현과 기준 솔버 호출을 구분합니다. 어느 실험도 상용 솔버의 모든 전처리·실패 처리·수렴 이론을 구현했다고 주장하지 않습니다. 수치 검사는 명시한 모델과 초기값의 유한 실행에 대한 확인이며 일반 수렴 증명, 전역 탐색 보증, 모든 입력에 대한 정확성 인증 또는 알고리즘 성능 순위가 아닙니다.

일반 부등식은 `c(x) >= 0`, 라그랑지안은 `L = f - lambda^T c`로 설명합니다. LP 표준형과 라이브러리가 사용하는 별도 입력 규약은 각 장에서 명시합니다. 부등식 승수는 음이 아니며 등식 승수에는 부호 제한이 없습니다.

## 출처

- [저자의 공식 교재 안내](https://users.iems.northwestern.edu/~nocedal/book/)
- [공식 목차](https://users.iems.northwestern.edu/~nocedal/book/toc.html)
- [2판 정오표 게시 안내](https://users.iems.northwestern.edu/~nocedal/book/errata2.html): 2026-10-01 확인 당시 실제 정오표는 아직 게시되지 않았다고 표시됨
- [Springer 출판사 안내](https://link.springer.com/book/10.1007/978-0-387-40065-5)

AI의 도움으로 작성한 비공식 보충 학습 자료입니다. 저자·출판사의 승인이나 자료 전체에 대한 포괄적인 재사용 허락을 뜻하지 않습니다.
