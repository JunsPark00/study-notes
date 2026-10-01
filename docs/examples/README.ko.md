# MPC 한국어 학습 노트: 독립 실행 보충 예제

8개 장의 핵심 계산을 작고 읽을 수 있는 Python 프로그램으로 구현했습니다. 각 파일은 단독 실행할 수 있고 다른 장의 코드, 별도 데이터 파일, 계정, 네트워크 연결이 필요하지 않습니다. 실행에는 NumPy, SciPy, Matplotlib을 설치한 Python 환경만 필요합니다.

이 코드는 이 사이트를 위해 새로 작성한 학습용 보충 구현입니다. 특정 연구용 솔버나 교재의 모든 수치 예제를 재현하는 패키지가 아닙니다. 책의 그림·본문·PDF·해답을 포함하지 않습니다.

## 원전과 범위

학습 주제의 원전은 James B. Rawlings, David Q. Mayne, Moritz M. Diehl, *Model Predictive Control: Theory, Computation, and Design*, 2판 1쇄(2017)입니다. [저자 공식 교재 사이트](https://sites.engineering.ucsb.edu/~jbraw/mpc/)에서 판본과 독서 자료를 확인할 수 있습니다. 이 프로젝트는 비공식 보충 학습 자료이며 저자·출판사의 공식 번역 또는 공식 소프트웨어가 아닙니다.

코드는 본 사이트의 작은 손계산 모델을 계산으로 확장합니다. 일반 수학식·개념의 원전 표시는 유지하되, 코드 자체는 별도의 구현입니다. 책 전체를 대체하거나 일반적인 MPC 안정성·강인성·안전성을 인증하지 않습니다.

## 빠른 시작

Python 3.10 이상을 권장합니다. 실제 검증한 Python과 라이브러리 버전은 `validation_summary.json`에 기록되어 있습니다. 패키지는 해당 환경에 미리 설치되어 있어야 하며, 실행 중에는 네트워크를 사용하지 않습니다.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell에서는 .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python chapter01_double_integrator.py
```

기본 출력은 실행한 작업 폴더 아래 `output/chapter01/figure.png`와 `output/chapter01/result.json`입니다. 원하는 폴더를 지정할 수 있습니다.

```bash
python chapter02_constrained_mpc.py --output-dir my-results/chapter02
```

각 프로그램은 그림을 화면에 띄우지 않고 PNG로 저장합니다. JSON은 계산값, 가정, 검증 항목을 담고 표준 출력에도 표시됩니다. 그림의 축·범례는 별도 한글 글꼴 설치 없이 재현되도록 영어로 표시했습니다. 한국어 실행·해석 안내는 이 문서에서 확인할 수 있습니다.

검사는 Python `assert`와 NumPy 검사 함수로 수행합니다. `python -O`로 실행하면 일부 검사가 꺼지므로 사용하지 마세요. 실패하면 비정상 종료하며 `status: passed` 결과를 새로 쓰지 않습니다. 기존 출력 폴더를 다시 쓰는 경우 이전 파일과 혼동하지 않도록 실행 종료 코드와 새 JSON의 수정 시각을 함께 확인하세요.

## 장별 실행과 읽을 거리

1. `python chapter01_double_integrator.py`
   - 일정 가속도 이중 적분기를 Euler와 정확한 영차 유지(ZOH)로 전파합니다
   - 총 시간 4초를 고정합니다. 간격 0.4초의 Euler 위치는 7.2 m, 정확값은 8 m이며 간격을 절반으로 하면 오차도 절반입니다
   - 위치 m, 속도 m/s, 가속도 m/s², 시간 s를 사용합니다. 최적 입력을 계산하는 예제는 아닙니다

2. `python chapter02_constrained_mpc.py`
   - 무차원 스칼라 모델 x⁺=1.1x+u, 상태 한계 ±4, 입력 한계 ±1, 종단 집합 ±0.5의 작은 QP를 풉니다
   - Q=1, R=0.2, N=5, DARE 종단 비용을 사용하며, 선형 계획으로 초기 실행 가능점을 찾고 SLSQP로 이차 비용을 최소화합니다
   - 한 단계 실행 가능 반경 1.363636과 x=1.3/1.4의 차이를 확인합니다. 20단계 명목 폐루프에서 이전 계획의 이동 후보, 제약, 값 함수 감소를 검사합니다
   - 모델이 정확하고 상태가 알려진 명목 조건입니다. 외란·추정 오차가 있는 경우의 안전성을 주장하지 않습니다

3. `python chapter03_tube_chance.py`
   - 유계 외란의 불변 오차 반경 0.2, 명목 상태 한계 2.8, 명목 입력 한계 0.88을 계산합니다
   - 별도의 영평균 가우스 오차 실험에서 10단계 전체 위험 5%를 단계별 0.5%로 배분합니다. 양측 여유는 1.960σ에서 2.807σ로 바뀝니다
   - 합집합 상계는 시점 간 독립성을 요구하지 않지만, 코드의 검증 표본은 독립입니다. 유계 잡음과 가우스 잡음을 같은 모델로 혼동하지 마세요
   - 튜브 여유와 위험 예산만 구현하며 완전한 강인·확률적 MPC 최적화는 아닙니다

4. `python chapter04_scalar_kalman.py`
   - 사전 N(0,1), y=1, R=0.25에서 칼만 이득 0.8, 사후 평균 0.8, 분산 0.2, 다음 예측 분산 0.24를 확인합니다
   - 독립적인 가우스 궤적 20,000개로 최종 오차의 공분산 보정과 95% 구간 빈도를 비교합니다
   - 현재 측정으로 필터링한 뒤 다음 시각을 예측합니다. MHE·평활화·MPC 결합은 구현하지 않습니다

5. `python chapter05_coupled_covariance.py`
   - 예측형 관측기의 추정 오차 ε와 추종 오차 e를 함께 전파합니다
   - 이산 Lyapunov 방정식과 고정 난수 시드 모사를 비교하고 Var(ε+e)의 교차 공분산을 확인합니다
   - 모든 경로의 유계 여유와 확률적 RMS는 다른 수치입니다. 균등 잡음의 오차 분포를 가우스로 가정하지 않습니다

6. `python chapter06_distributed_qp.py`
   - 세 참여자의 새 블록을 단순 결합하면 발산할 수 있고, 전체 후보를 평균하면 비용을 낮출 수 있음을 계산합니다
   - 별도의 상자 제약 볼록 QP에서 분산 반복을 중앙집중 수치해와 비교하고 전체 기울기로 목적함수 오차 상한을 계산합니다
   - 목적함수 차이의 인증은 폐루프 안정성이나 통신 지연 인증이 아닙니다

7. `python chapter07_explicit_mpc.py`
   - J=x²+xu+u²/2, |u|≤1의 세 영역 입력·가치함수를 만들고 독립적인 온라인 스칼라 최적화와 비교합니다
   - 경계의 연속성, KKT 조건, 같은 영역을 유지하는 측정 오차 반지름을 검사합니다
   - 이 작은 스칼라 문제의 포화 법칙을 일반 다변수 MPC에 그대로 적용할 수는 없습니다

8. `python chapter08_rk4_taylor.py`
   - ẋ=−x+u를 Euler, RK4, 정확해로 비교하고 같은 물리 시간에서 이산화 오차를 확인합니다
   - 한 단계 이차 비용의 올바른 기울기와 의도적으로 틀린 기울기를 Taylor 잔차 차수로 구분합니다
   - 시간은 s이고 상태·입력은 정규화된 값입니다. 일반 NMPC·SQP 솔버 전체를 구현하지 않습니다

## 전체 독립 실행 검증

```bash
python validate_all.py
```

검증기는 각 장 파일 **하나만** 새 임시 폴더로 복사하고, 서로 다른 새 Python 프로세스에서 실행합니다. 따라서 다른 장 파일이나 프로젝트의 모듈에 의존하는 코드는 검증을 통과할 수 없습니다. 실행 결과는 `validation_output/chapter01/` 등으로 모으고 `validation_summary.json`에 실행 환경, 소스 SHA-256, 성공 여부를 기록합니다. 각 프로그램의 `--output-dir` 사용도 이때 함께 검사합니다.

```bash
python validate_all.py --output-root validation_output --summary validation_summary.json
```

수치값의 끝자리, PNG 파일 바이트, 최적화 반복 수는 Python·라이브러리·플랫폼에 따라 달라질 수 있습니다. Monte Carlo 빈도는 표본 결과이지 증명이 아닙니다. 허용오차와 실제 검증 항목은 각 코드와 JSON을 확인하세요.
