# 🧾 영수증 AI 스캐너

Claude Vision AI를 활용해 영수증 이미지에서 정보를 자동 추출합니다.

## 📁 파일 구조

```
receipt_scanner/
├── main.py             # FastAPI 서버
├── receipt_service.py  # Claude Vision 분석 로직
├── models.py           # 데이터 모델 (Pydantic)
├── cli.py              # CLI (카메라 촬영 / 파일 선택)
└── requirements.txt
```

## ⚙️ 설치

```bash
pip install -r requirements.txt
```

## 🔑 API 키 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 🖥️ 사용법 1 — CLI (터미널)

```bash
# 대화형 메뉴 (카메라 or 파일 선택)
python cli.py

# 파일 직접 지정
python cli.py --file receipt.jpg

# 카메라로 바로 촬영
python cli.py --camera

# JSON 저장 없이 출력만
python cli.py --file receipt.jpg --no-save
```

### CLI 출력 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🧾  영수증 분석 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  업체명     스타벅스 수원영통점
  방문일시   2025-03-28 14:32
  주소       경기도 수원시 영통구 반달로 74-1
  결제방법   신용카드

  이용 내역────────────────────────────────
  · 아메리카노                        4,500원
  · 카페라떼                          5,500원
  · 치즈케이크                        6,800원
  ────────────────────────────────────────────
  총 결제액  16,800원
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 결과 저장: receipt_receipt_20250328_143512.json
```

---

## 🌐 사용법 2 — REST API 서버

```bash
python main.py
# 서버: http://localhost:8000
# 문서: http://localhost:8000/docs
```

### API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/scan` | 영수증 이미지 분석 |
| GET | `/health` | 서버 상태 확인 |

### curl 예시

```bash
curl -X POST http://localhost:8000/scan \
  -F "file=@receipt.jpg"
```

### 응답 JSON 예시

```json
{
  "업체명": "스타벅스 수원영통점",
  "날짜": "2025-03-28",
  "시간": "14:32",
  "주소": "경기도 수원시 영통구 반달로 74-1",
  "이용내역": [
    { "항목": "아메리카노", "수량": 1, "단가": 4500, "금액": 4500 },
    { "항목": "카페라떼",   "수량": 1, "단가": 5500, "금액": 5500 }
  ],
  "소계": 10000,
  "부가세": null,
  "할인금액": null,
  "총금액": 10000,
  "결제방법": "신용카드",
  "카드번호": "1234",
  "메모": null
}
```

---

## 📱 모바일 앱에 연동하려면?

이 API 서버를 백엔드로 두고, 아래 방식으로 연동할 수 있어요:

- **React Native**: `expo-camera` → 촬영 후 `/scan`으로 POST
- **Flutter**: `image_picker` → 촬영 후 `http.MultipartRequest`로 POST
- **Swift/Kotlin**: 네이티브 카메라 → `URLSession` / `OkHttp`로 POST
