import base64
import json
import re
import anthropic
from fastapi import HTTPException

from models import ReceiptResult

SYSTEM_PROMPT = """당신은 영수증 분석 전문 AI입니다.
영수증 이미지를 보고 정보를 정확하게 추출하여 JSON 형식으로만 반환합니다.
JSON 외에 어떤 설명, 마크다운 코드블록, 전처리 텍스트도 포함하지 마세요."""

EXTRACT_PROMPT = """이 영수증 이미지를 분석하여 아래 JSON 스키마에 맞게 정보를 추출하세요.
찾을 수 없는 필드는 null로 채우고, 금액은 반드시 숫자(정수)만 입력하세요.

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
      "금액": "integer | null"
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
        # API 키는 환경변수 ANTHROPIC_API_KEY 에서 자동으로 읽습니다
        self.client = anthropic.Anthropic()
        self.model = "claude-opus-4-5"

    async def analyze(self, image_bytes: bytes, media_type: str) -> ReceiptResult:
        # HEIC → JPEG 처리 (Anthropic API는 HEIC 미지원)
        if media_type in ("image/heic", "image/heif"):
            image_bytes, media_type = self._convert_heic(image_bytes)

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
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
        return ReceiptResult(**parsed)

    # ── 내부 유틸 ──────────────────────────────────────────────

    def _parse_json(self, text: str) -> dict:
        """모델 응답에서 JSON 추출 및 파싱"""
        # 코드블록 제거
        clean = re.sub(r"```(?:json)?\n?|```", "", text).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=422,
                detail=f"AI 응답을 파싱할 수 없습니다. 영수증 이미지가 선명한지 확인하세요. ({e})",
            )

    def _convert_heic(self, image_bytes: bytes) -> tuple[bytes, str]:
        """HEIC 이미지를 JPEG로 변환 (pillow-heif 필요)"""
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
