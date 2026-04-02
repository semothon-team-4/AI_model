# 🧺 new_care_label

의류 케어 라벨의 세탁 심볼을 자동으로 감지하고 한국어로 설명해주는 AI 모델입니다.  
YOLOv8 기반으로 학습된 모델을 사용하여 실시간으로 심볼을 인식합니다.

---

## 📁 프로젝트 구조

```
new_care_label/
├── pipeline.py         # 메인 실행 파일 (예측 + 시각화)
├── unified_best.pt     # 학습된 YOLO 모델 가중치
├── test_1.png          # 테스트 이미지
├── test_2.png
├── test_3.jpg
├── test_4.png
├── test_5.png
└── result_*.jpg        # 분석 결과 이미지 (자동 생성)
```

---

## ⚙️ 설치 방법

```bash
pip install ultralytics opencv-python
```

---

## 🚀 사용 방법

```bash
# 기본 실행 (test_5.png 사용)
python pipeline.py

# 특정 이미지 지정
python pipeline.py test_1.png
```

실행하면 터미널에 감지된 심볼 목록과 한국어 설명이 출력되고,  
결과 이미지가 `result_YYYYMMDD_HHMMSS.jpg` 형식으로 저장됩니다.

---

## 📊 출력 예시

```
분석 중: test_1.png

감지된 심볼: 5개

심볼                                     신뢰도  설명
------------------------------------------------------------------------------------------
hand_wash                                 0.900  손세탁만 가능
DN_bleach                                 0.880  표백제 사용 불가
iron_low                                  0.870  저온 다림질 가능 (110°C 이하)
DN_dry_clean                              0.920  드라이클리닝 금지
dry_flat                                  0.860  뉘어서 자연건조
```

---

## 🏷️ 인식 가능한 심볼 목록

| 카테고리 | 심볼 예시 |
|----------|-----------|
| 세탁 | `30C`, `40C`, `hand_wash`, `DN_wash`, `machine_wash_normal` |
| 표백 | `bleach`, `DN_bleach`, `chlorine_bleach`, `non_chlorine_bleach` |
| 건조 | `tumble_dry_low`, `DN_tumble_dry`, `line_dry`, `dry_flat` |
| 다림질 | `iron_low`, `iron_medium`, `iron_high`, `DN_iron` |
| 드라이클리닝 | `dry_clean`, `DN_dry_clean`, `dry_clean_low_heat` |
| 기타 | `DN_wring`, `steam`, `wet_clean` 등 |

총 **50개 이상**의 케어 심볼 인식 가능

---

## 🧠 모델 정보

- **아키텍처**: YOLOv8
- **모델 파일**: `unified_best.pt`
- **기본 신뢰도 임계값**: `conf=0.1`
- **IOU 임계값**: `iou=0.3`
