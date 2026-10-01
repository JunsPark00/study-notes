# 출처와 이용 안내

Kevin M. Lynch · Frank C. Park, *Modern Robotics: Mechanics, Planning, and Control*, Cambridge University Press, 2017의 장 주제에 연결한 비공식 한국어 보충 학습 노트입니다.

- [공식 저자 자료와 영상 안내](https://modernrobotics.northwestern.edu/)
- [공식 책·소프트웨어·정오표 안내](https://modernrobotics.org/)

## 직접 작성한 공개 자료

**Made by Codex.** 이 사이트의 한국어 설명, 작은 교육용 모델, Python 실험은 이번 학습 자료 개편에서 직접 작성했습니다. 그림 26개는 공개된 독립 코드로 새로 계산합니다. 표준 수학 관계는 각 모델의 가정과 함께 설명합니다. 교재 전체 절의 번역, 문제 해답집, 공식 저자 자료 또는 저자의 승인을 받은 출판물이 아닙니다.

공개 범위는 13장별 세 가지 개념과 선택적인 입문 실험입니다. 예를 들어 동역학은 한 링크 모델, 제어는 무포화 선형 모델, 이동 로봇은 미끄럼 없는 차동 구동 모델에 한정합니다. 해당 장 전체 이론이나 실제 하드웨어를 검증하지 않습니다.

교재 PDF·스캔·출판사 그림·기존 출처가 불명확한 노트와 슬라이드는 게시하지 않습니다. 이전 저장소의 이력이나 비공개 링크도 공개 자료에 포함하지 않습니다. [공개 파일 출처 기록](../../examples/modern-robotics/provenance.json)에 파일별 역할과 해시를 기록합니다. 이 기록은 공개 범위 검증이며 법적 권리 보증을 뜻하지 않습니다.

## 실행 의존성과 검증 한계

실험은 NumPy, SciPy, Matplotlib 및 [Modern Robotics 공식 교육용 Python 라이브러리](https://github.com/NxRLab/ModernRobotics)를 사용합니다. `modern_robotics` 함수는 설치된 패키지에서 호출하며 라이브러리 소스나 교재 예제 구현을 배포하지 않습니다. 각 의존성의 라이선스는 해당 프로젝트에 따릅니다.

코드·수식·설명에는 오류가 있을 수 있습니다. 게시된 수치 검증은 고정된 입력과 허용오차에서의 실행 결과입니다. 변경한 파라미터, 브라우저별 표시, 실제 로봇 성능을 모두 검증했다는 의미는 아닙니다.
