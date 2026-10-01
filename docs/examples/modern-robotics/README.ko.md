# Modern Robotics 독립 보충 실험

**Made by Codex.** 직접 작성한 작은 교육용 모델과 설명입니다. 교재 전체 번역이나 공식 예제 모음이 아닙니다. 각 파일은 다른 장, 노트북, 비공개 저장소 또는 외부 데이터를 불러오지 않고 단독 실행합니다. 그림은 코드에서 새로 계산하며 라벨은 영어입니다.

Python 3.11 이상을 사용합니다. 검증 버전은 `requirements.txt`에 고정했으며 실제 환경은 `validation_summary.json`과 각 그림 폴더의 `metrics.json`에 기록합니다.

```sh
python -m pip install -r requirements.txt
python chapter01.py --output-dir output/chapter01
```

전체 재검증에는 13개 chapterNN.py, manifest.json과 validate_all.py를 같은 폴더에 두고 실행하세요:

```sh
python validate_all.py --output-dir output/verified
```

그림과 잔차 JSON이 출력됩니다. 기본 설정 38개 검사와 13장의 원호·직진·정지·제자리 회전 네 경우를 검증합니다. `assert` 검사이므로 Python의 `-O` 옵션을 사용하지 마세요. 설치 후 실행은 네트워크를 사용하지 않습니다.

길이 m, 시간 s, 각도 rad, 열벡터·오른손 좌표계, 난수 seed=42를 사용합니다. 패키지 라이선스는 각 프로젝트를 따릅니다. Modern Robotics 패키지는 공식 교육용 라이브러리를 import하며 그 소스를 복사하지 않습니다.

공개 allowlist와 파일 해시는 `provenance.json`에 있습니다. 교재 PDF, 스캔, 과거 노트·TeX·슬라이드·저장소 이력은 포함하지 않습니다. 수정 시 저장소의 `content/books/modern-robotics/study-content.json`을 편집하고 `python scripts/build-modern-robotics.py` 후 이 검증기를 실행하세요.
