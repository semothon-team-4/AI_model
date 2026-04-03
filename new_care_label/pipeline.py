from ultralytics import YOLO
from datetime import datetime
import cv2
import sys
import os
import base64

# =============================================
# 모델 로드
# =============================================
BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "unified_best.pt")
model = YOLO(MODEL_PATH)

# =============================================
# 심볼 PNG 폴더 경로
# PNG 파일명 = 심볼 ID 그대로 (예: 30C.png, hand_wash.png)
# =============================================
SYMBOL_IMG_DIR = os.path.join(BASE, "symbols")   # ← PNG들 넣는 폴더

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
# PNG 이미지 로드 (base64 인코딩 → HTML 임베드용)
# =============================================
def load_symbol_img_b64(symbol_id):
    """symbols/{symbol_id}.png 를 base64로 반환. 없으면 None."""
    path = os.path.join(SYMBOL_IMG_DIR, f"{symbol_id}.png")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def symbol_img_tag(symbol_id, size=56):
    """심볼 PNG → <img> 태그. 없으면 placeholder div 반환."""
    b64 = load_symbol_img_b64(symbol_id)
    if b64:
        return f'<img src="data:image/png;base64,{b64}" width="{size}" height="{size}" style="object-fit:contain;filter:invert(1);">'
    # PNG 없을 때 fallback: 심볼 ID 첫 글자 표시
    return f'<div style="width:{size}px;height:{size}px;display:flex;align-items:center;justify-content:center;background:#f0f0f0;border-radius:4px;font-size:10px;color:#888;">{symbol_id[:6]}</div>'

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
# 시각화 (기존 cv2 방식 유지)
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
        print(f"결과 이미지 저장: {save_path}")
    else:
        cv2.imshow("Care Label Result", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# =============================================
# HTML 리포트 생성 (PNG 심볼 매핑 포함)
# =============================================
def save_html_report(image_path, results, save_path):
    # 분석 대상 이미지 base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 심볼 카드 HTML
    cards_html = ""
    for r in results:
        sym      = r["symbol"]
        conf     = r["confidence"]
        desc     = r["desc"]
        img_tag  = symbol_img_tag(sym, size=56)
        conf_pct = int(conf * 100)
        bar_color = "#22c55e" if conf_pct >= 70 else "#f59e0b" if conf_pct >= 40 else "#ef4444"

        cards_html += f"""
        <div class="card">
          <div class="card-icon">{img_tag}</div>
          <div class="card-body">
            <div class="sym-id">{sym}</div>
            <div class="sym-desc">{desc}</div>
            <div class="conf-bar-wrap">
              <div class="conf-bar" style="width:{conf_pct}%;background:{bar_color};"></div>
            </div>
            <div class="conf-label">{conf:.3f}</div>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>케어 라벨 분석 결과</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
          background: #f5f4f0; color: #111; min-height: 100vh; }}

  header {{ background: #111; color: #f5f4f0; padding: 18px 28px;
            display: flex; align-items: center; justify-content: space-between; }}
  header h1 {{ font-size: 17px; font-weight: 600; }}
  header small {{ font-size: 11px; opacity: 0.45; }}

  .layout {{ display: grid; grid-template-columns: 340px 1fr;
             gap: 20px; padding: 20px 28px; max-width: 1200px; margin: 0 auto; }}

  .panel {{ background: #fff; border-radius: 10px; border: 1px solid #e5e3dc;
            overflow: hidden; }}

  .panel-title {{ font-size: 11px; font-weight: 600; color: #888;
                  letter-spacing: 0.5px; text-transform: uppercase;
                  padding: 12px 16px; border-bottom: 1px solid #e5e3dc; }}

  .source-img {{ width: 100%; display: block; }}

  .meta {{ padding: 12px 16px; font-size: 12px; color: #666; line-height: 1.8; }}
  .meta b {{ color: #111; font-weight: 600; }}

  .cards {{ padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }}

  .card {{ display: flex; gap: 14px; align-items: flex-start;
           padding: 12px; border-radius: 8px; border: 1px solid #e5e3dc;
           background: #fafaf8; }}
  .card-icon {{ flex-shrink: 0; width: 56px; height: 56px;
                background: #111; border-radius: 8px;
                display: flex; align-items: center; justify-content: center; }}
  .card-icon img {{ filter: invert(1); width: 44px; height: 44px; object-fit: contain; }}
  .card-body {{ flex: 1; }}
  .sym-id {{ font-size: 12px; font-weight: 600; margin-bottom: 3px; }}
  .sym-desc {{ font-size: 12px; color: #555; margin-bottom: 8px; line-height: 1.4; }}
  .conf-bar-wrap {{ height: 4px; background: #e5e3dc; border-radius: 2px; margin-bottom: 3px; }}
  .conf-bar {{ height: 4px; border-radius: 2px; transition: width 0.3s; }}
  .conf-label {{ font-size: 10px; color: #999; }}

  @media (max-width: 720px) {{
    .layout {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<header>
  <h1>🧺 케어 라벨 분석 결과</h1>
  <small>{timestamp}</small>
</header>

<div class="layout">

  <div>
    <div class="panel">
      <div class="panel-title">분석 이미지</div>
      <img class="source-img" src="data:image/{mime};base64,{img_b64}" alt="분석 이미지">
      <div class="meta">
        <b>파일</b>: {os.path.basename(image_path)}<br>
        <b>감지 심볼</b>: {len(results)}개<br>
        <b>분석 시각</b>: {timestamp}
      </div>
    </div>
  </div>

  <div>
    <div class="panel">
      <div class="panel-title">감지된 심볼 ({len(results)}개)</div>
      <div class="cards">
        {cards_html if cards_html else '<div style="padding:20px;color:#aaa;font-size:13px;">감지된 심볼이 없습니다.</div>'}
      </div>
    </div>
  </div>

</div>
</body>
</html>"""

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 리포트 저장: {save_path}")

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

    # 터미널 출력 (기존 유지)
    print(f"감지된 심볼: {len(results)}개\n")
    print(f"{'심볼':<40} {'신뢰도':>6}  설명")
    print("-" * 90)
    for r in results:
        has_img = "🖼" if os.path.exists(os.path.join(SYMBOL_IMG_DIR, f"{r['symbol']}.png")) else "  "
        print(f"{has_img} {r['symbol']:<38} {r['confidence']:>6.3f}  {r['desc']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # cv2 결과 이미지 저장
    img_save = os.path.join(BASE, f"result_{timestamp}.jpg")
    visualize(TEST_IMAGE, results, save_path=img_save)

    # HTML 리포트 저장 (PNG 심볼 매핑 포함)
    html_save = os.path.join(BASE, f"report_{timestamp}.html")
    save_html_report(TEST_IMAGE, results, html_save)
