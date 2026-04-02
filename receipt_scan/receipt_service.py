import base64
import json
import re
import anthropic
from fastapi import HTTPException

from models import ReceiptResult, TAG_LIST

SYSTEM_PROMPT = """당신은 세탁소 영수증 분석 전문 AI입니다.
영수증 이미지를 보고 정보를 정확하게 추출하여 JSON 형식으로만 반환합니다.
JSON 외에 어떤 설명, 마크다운 코드블록, 전처리 텍스트도 포함하지 마세요."""

EXTRACT_PROMPT = """이 영수증 이미지를 분석하여 아래 JSON 스키마에 맞게 정보를 추출하세요.
찾을 수 없는 필드는 null로 채우고, 금액은 반드시 숫자(정수)만 입력하세요.

태그는 각 항목의 서비스 종류에 따라 아래 중 하나로 분류하세요:
- "일반세탁"    : 일반 의류 세탁 (브랜드 없는 셔츠, 바지, 티셔츠 등)
- "드라이클리닝" : 드라이클리닝 의류 (코트, 정장, 패딩 — 명품 브랜드면 명품케어 우선)
- "얼룩제거"    : 얼룩/오염 처리 (품목 무관 — 명품 브랜드면 명품케어 우선)
- "신발관리"    : 신발 세탁/광택/클리닝 (명품 브랜드 신발이면 명품케어 우선)
- "명품케어"    : 영수증 항목명에 명품 브랜드명 또는 "명품"이라는 단어가
                  명시적으로 적혀있을 때만 분류. 브랜드명/명품 표기가 없으면
                  드라이클리닝/얼룩제거/신발관리 등 다른 태그로 분류.
                  인식 가능한 브랜드 예시:
                  샤넬 구찌 루이비통 에르메스 프라다 버버리 발렌시아가 몽클레어
                  디올 셀린느 지방시 발렌티노 보테가베네타 페라가모 롤렉스
                  Chanel Gucci LV Hermes Prada Burberry Balenciaga Moncler 등
- "수선"        : 수선, 단추, 지퍼, 줄임/늘림
- "기타"        : 위에 해당 없는 항목

명품 브랜드가 감지된 항목은 "브랜드" 필드에 브랜드명을 기록하세요.

{
  "업체명": "string | null",
  "날짜": "YYYY-MM-DD | null",
  "시간": "HH:MM | null",
  "주소": "string | null",
  "이용내역": [
    {
      "항목": "string",
      "수량": "integer",
      "단가": "integer | null",
      "금액": "integer | null",
      "태그": "일반세탁 | 드라이클리닝 | 얼룩제거 | 신발관리 | 명품케어 | 수선 | 기타",
      "브랜드": "string | null"
    }
  ],
  "소계": "integer | null",
  "부가세": "integer | null",
  "할인금액": "integer | null",
  "총금액": "integer | null",
  "결제방법": "string | null",
  "카드번호": "끝 4자리 string | null",
  "메모": "string | null"
}

JSON만 반환하세요."""


class ReceiptService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key="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")
        self.model = "claude-sonnet-4-5"

    async def analyze(self, image_bytes: bytes, media_type: str) -> ReceiptResult:
        if media_type in ("image/heic", "image/heif"):
            image_bytes, media_type = self._convert_heic(image_bytes)

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": EXTRACT_PROMPT},
                        ],
                    }
                ],
            )
        except anthropic.AuthenticationError:
            raise HTTPException(status_code=401, detail="Anthropic API 키가 유효하지 않습니다.")
        except anthropic.APIError as e:
            raise HTTPException(status_code=502, detail=f"Claude API 오류: {str(e)}")

        raw_text = message.content[0].text
        parsed = self._parse_json(raw_text)
        result = ReceiptResult(**parsed)
        result.build_tag_groups()
        return result

    def _parse_json(self, text: str) -> dict:
        clean = re.sub(r"```(?:json)?\n?|```", "", text).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=422,
                detail=f"AI 응답을 파싱할 수 없습니다. 영수증 이미지가 선명한지 확인하세요. ({e})",
            )

    def _convert_heic(self, image_bytes: bytes) -> tuple[bytes, str]:
        try:
            import pillow_heif
            from PIL import Image
            import io

            pillow_heif.register_heif_opener()
            img = Image.open(io.BytesIO(image_bytes))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            return buf.getvalue(), "image/jpeg"
        except ImportError:
            raise HTTPException(
                status_code=400,
                detail="HEIC 파일 변환을 위해 pillow-heif 패키지가 필요합니다: pip install pillow-heif",
            )
