from ultralytics import YOLO
from datetime import datetime
import cv2
import sys
import os

# =============================================
# 모델 로드
# =============================================
BASE = r"C:\new_care_label"
MODEL_PATH = os.path.join(BASE, "unified_best.pt")
model = YOLO(MODEL_PATH)

# =============================================
# 심볼 한국어 설명
# =============================================
SYMBOL_DESC = {
    "30C":                    "30°C 이하의 미지근한 물에서 세탁기 사용 가능",
    "40C":                    "40°C 이하의 물에서 세탁기 사용 가능",
    "50C":                    "50°C 이하의 물에서 세탁기 사용 가능",
    "60C":                    "60°C 이하의 물에서 세탁기 사용 가능",
    "70C":                    "70°C 이하의 물에서 세탁기 사용 가능",
    "95C":                    "95°C 이하의 물에서 세탁기 사용 가능",
    "hand_wash":              "손세탁만 가능",
    "DN_wash":                "세탁 불가",
    "DN_bleach":              "표백제 사용 불가",
    "bleach":                 "표백제 사용 가능",
    "chlorine_bleach":        "염소 표백제 사용 가능",
    "non_chlorine_bleach":    "산소계 표백제만 사용 가능",
    "DN_dry_clean":           "드라이클리닝 금지",
    "dry_clean":              "드라이클리닝 가능",
    "dry_clean_any_solvent":  "모든 용제로 드라이클리닝 가능",
    "dry_clean_any_solvent_except_trichloroethylene": "트리클로로에틸렌 제외 드라이클리닝 가능",
    "dry_clean_low_heat":     "저온으로 드라이클리닝 가능",
    "dry_clean_no_steam":     "스팀 없이 드라이클리닝 가능",
    "dry_clean_petrol_only":  "석유계 용제로만 드라이클리닝 가능",
    "dry_clean_reduced_moisture": "저습도로 드라이클리닝 가능",
    "dry_clean_short_cycle":  "단축 사이클로 드라이클리닝 가능",
    "DN_tumble_dry":          "건조기 사용 불가",
    "tumble_dry_normal":      "건조기 사용 가능",
    "tumble_dry_low":         "저온으로 건조기 사용 가능",
    "tumble_dry_medium":      "중온으로 건조기 사용 가능",
    "tumble_dry_high":        "고온으로 건조기 사용 가능",
    "tumble_dry_no_heat":     "열 없이 건조기 사용 가능",
    "iron":                   "다림질 가능",
    "iron_low":               "저온 다림질 가능 (110°C 이하)",
    "iron_medium":            "중온 다림질 가능 (150°C 이하)",
    "iron_high":              "고온 다림질 가능 (200°C 이하)",
    "DN_iron":                "다림질 불가",
    "DN_steam":               "스팀 다림질 불가",
    "line_dry":               "걸어서 자연건조",
    "line_dry_in_shade":      "그늘에서 걸어 자연건조",
    "drip_dry":               "짜지 말고 자연건조",
    "drip_dry_in_shade":      "그늘에서 짜지 말고 자연건조",
    "dry_flat":               "뉘어서 자연건조",
    "natural_dry":            "자연건조",
    "shade_dry":              "그늘에서 건조",
    "DN_dry":                 "건조 불가",
    "DN_wet_clean":           "물세탁 불가",
    "wet_clean":              "물세탁 가능",
    "DN_wring":               "비틀어 짜기 금지",
    "wring":                  "비틀어 짜기 가능",
    "DN_solvent":             "용제 사용 불가",
    "steam":                  "스팀 처리 가능",
    "machine_wash_normal":    "일반 세탁기 세탁 가능",
    "machine_wash_delicate":  "약한 세탁기 세탁 가능",
    "machine_wash_permanent_press": "영구 프레스 세탁 가능",
}

# =============================================
# 예측
# =============================================
def predict_care_label(image_path, conf=0.1, iou=0.3):
    results = model(image_path, conf=conf, iou=iou, verbose=False)[0]
    output = []
    for box in results.boxes:
        cls_id   = int(box.cls[0])
        cls_conf = float(box.conf[0])
        cls_name = model.names[cls_id]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        output.append({
            "symbol":     cls_name,
            "confidence": round(cls_conf, 3),
            "bbox":       [x1, y1, x2, y2],
            "desc":       SYMBOL_DESC.get(cls_name, "설명 없음"),
        })
    output.sort(key=lambda x: x["confidence"], reverse=True)
    return output

# =============================================
# 시각화
# =============================================
def visualize(image_path, results, save_path=None):
    img = cv2.imread(image_path)
    for r in results:
        x1, y1, x2, y2 = r["bbox"]
        label = f"{r['symbol']} {r['confidence']:.2f}"
        cv2.rectangle(img, (x1, y1), (x2, y2), (34, 197, 94), 2)
        cv2.putText(img, label, (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (34, 197, 94), 1)
    if save_path:
        cv2.imwrite(save_path, img)
        print(f"결과 저장: {save_path}")
    else:
        cv2.imshow("Care Label Result", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# =============================================
# 실행
# =============================================
if __name__ == "__main__":
    TEST_IMAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "test_5.png")

    if not os.path.exists(TEST_IMAGE):
        print(f"이미지 파일이 없어요: {TEST_IMAGE}")
        sys.exit(1)

    print(f"분석 중: {TEST_IMAGE}\n")
    results = predict_care_label(TEST_IMAGE, conf=0.1)

    print(f"감지된 심볼: {len(results)}개\n")
    print(f"{'심볼':<40} {'신뢰도':>6}  설명")
    print("-" * 90)
    for r in results:
        print(f"{r['symbol']:<40} {r['confidence']:>6.3f}  {r['desc']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(BASE, f"result_{timestamp}.jpg")
    visualize(TEST_IMAGE, results, save_path=save_path)
