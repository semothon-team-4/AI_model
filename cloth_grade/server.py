"""
👕 옷 품질 등급 AI — FastAPI 서버
실행: uvicorn server:app --reload
"""

import anthropic
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not API_KEY:
    raise RuntimeError('.env 파일에 ANTHROPIC_API_KEY를 입력하세요!')

client = anthropic.Anthropic(api_key=API_KEY)
app    = FastAPI(title='👕 옷 품질 등급 AI')

# CORS 설정 (팀원 백엔드 연동 시 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# ── 프롬프트 ──────────────────────────────
PROMPT = """
이 옷 이미지를 분석해줘. 반드시 아래 JSON 형식으로만 답해. 다른 말은 하지 마.
이 앱은 개인 옷장 관리용이야. 옷 상태를 파악해서 계속 입을지, 관리가 필요한지, 처분할지 알려주는 게 목적이야.

## 사진 품질 체크 (분석 전 먼저 확인)
photo_quality를 'poor'로 설정하는 건 정말 분석이 불가능한 경우만이야.
웬만하면 good으로 판단하고 최대한 분석을 시도해줘.

poor로 판단하는 경우 (이 경우만 poor):
- 옷이 거의 보이지 않을 정도로 너무 어두움
- 사진이 심하게 흔들려서 옷 형태 자체가 불분명함
- 옷이 화면의 절반 이하로만 찍혀서 전체 상태 파악 불가

아래는 poor로 판단하지 않음:
- 구겨지거나 접혀있음 → 보이는 부분만으로 분석
- 배경이 복잡함 → 옷에 집중해서 분석
- 약간 어두운 조명 → 최대한 분석 시도
- 한쪽 면만 찍힘 → 보이는 면으로 분석

## 분석 순서
1. 사진 품질 체크
2. 빈티지/워싱/의도적 디자인 여부 판단
   - 빈티지: 고의적으로 낡게 만든 워싱, 에이징, 페이딩, 디스트레스드 디자인
   - 일반: 사용으로 인한 자연스러운 마모/오염
3. 빈티지면 낡음/워싱/페이딩은 디자인으로 인정
   단, 실제 오염(얼룩, 땀자국)과 의도치 않은 손상(구멍, 뜯김)은 결함으로 봐
4. 오염도/손상도 수치화
5. 아래 공식으로 종합 점수 계산 후 등급 산정

## 오염도 판단 기준
옷 전체 면적 대비 오염 영역 비율:
- 확인 항목: 색상 불균일, 얼룩 패턴, 밝기 차이, 텍스처 변화
- 빈티지 워싱/페이딩은 오염으로 보지 않음
- 소재별 민감도: 흰색/면 소재는 오염에 더 민감하게 판단

## 손상도 판단 기준
옷 전체 면적 대비 손상 영역 비율:
- 확인 항목: 구멍/뚫린 부분, 실밥 풀림, 마모로 인한 색 변화, 보풀
- 의도된 디스트레스드 디자인은 손상으로 보지 않음
- 빈티지 옷은 손상도 판단 시 10점 감점 보정 적용

## 종합 점수 계산 (등급 산정 기준)
1단계 — 손상도 우선 체크:
  손상도 36% 이상이면 오염도 상관없이 무조건 C등급

2단계 — 손상도 36% 미만이면 종합점수로 판단:
  종합점수 = 오염도 × 0.4 + 손상도 × 0.6
  - A: 종합점수 0~25
  - B: 종합점수 26~45
  - C: 종합점수 46+

(손상은 세탁으로 해결 불가하므로 더 높은 가중치 부여)

## 관리 태그 판단 기준
오염도와 손상도를 각각 독립적으로 판단:
- need_wash: 오염도 6% 이상이면 true
- need_repair: 손상도 6% 이상이면 true
- A등급이고 오염도/손상도 모두 6% 미만이면 관리 불필요
- 빈티지 옷은 임계값을 각각 5점씩 높여서 판단 (더 관대하게)

{
  "photo_quality": "good 또는 poor",
  "photo_warn": "재촬영 안내 메시지 (good이면 null)",
  "clothing": "옷 종류 (예: 청바지, 티셔츠, 니트, 코트 등)",
  "fabric": "소재 (예: 데님, 면, 폴리에스테르, 울, 실크 등)",
  "is_vintage": true 또는 false,
  "vintage_reason": "빈티지 판단 근거 (빈티지 아니면 null)",
  "stain": 오염도 숫자만 (0~100 사이 정수),
  "damage": 손상도 숫자만 (0~100 사이 정수),
  "total_score": 종합점수 숫자만 (오염도×0.4 + 손상도×0.6, 소수점 첫째자리),
  "grade": "A/B/C 중 하나 (photo_quality가 poor면 null)",
  "need_wash": true 또는 false (오염도 기준, poor면 null),
  "need_repair": true 또는 false (손상도 기준, poor면 null),
  "action": "추천 행동 (그대로 착용 / 세탁 권장 / 수선 권장 / 세탁+수선 권장 / 처분 권장, poor면 null)",
  "storage_tip": "소재/옷 종류에 맞는 보관 팁 한 줄 (poor면 null)",
  "reason": "등급 판단 이유 한 줄 (poor면 null)"
}
"""

# ── 응답 모델 (팀원 참고용) ───────────────
class GradeResult(BaseModel):
    photo_quality  : str
    photo_warn     : str | None
    clothing       : str | None
    fabric         : str | None
    is_vintage     : bool | None
    vintage_reason : str | None
    stain          : int | None
    damage         : int | None
    total_score    : float | None
    grade          : str | None
    need_wash      : bool | None
    need_repair    : bool | None
    action         : str | None
    storage_tip    : str | None
    reason         : str | None


# ── 핵심 분석 함수 ────────────────────────
def analyze_image(image_bytes: bytes, media_type: str) -> GradeResult:
    img_data = base64.standard_b64encode(image_bytes).decode()

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=512,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': img_data,
                    },
                },
                {'type': 'text', 'text': PROMPT},
            ],
        }],
    )

    raw   = response.content[0].text.strip()
    start = raw.find('{')
    end   = raw.rfind('}') + 1
    data  = json.loads(raw[start:end])
    return GradeResult(**data)


# ── API 엔드포인트 ────────────────────────

@app.get('/', response_class=HTMLResponse)
async def index():
    """브라우저 UI"""
    html = Path('index.html').read_text(encoding='utf-8')
    return HTMLResponse(content=html)


@app.post('/analyze', response_model=GradeResult)
async def analyze(file: UploadFile = File(...)):
    """
    [팀원용 API]
    POST /analyze
    Body: multipart/form-data, field name = 'file'
    Response: GradeResult JSON
    """
    # 이미지 파일 검증
    ext_map = {
        'image/jpeg': 'image/jpeg',
        'image/png' : 'image/png',
        'image/webp': 'image/webp',
    }
    media_type = ext_map.get(file.content_type)
    if not media_type:
        raise HTTPException(status_code=400, detail='jpg/png/webp 파일만 가능합니다.')

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB 제한
        raise HTTPException(status_code=400, detail='파일 크기는 10MB 이하여야 합니다.')

    try:
        result = analyze_image(image_bytes, media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


@app.get('/health')
async def health():
    """서버 상태 확인"""
    return {'status': 'ok'}
