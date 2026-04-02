from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from receipt_service import ReceiptService
from models import ReceiptResult

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 영수증 스캐너 API 시작")
    yield
    print("🛑 영수증 스캐너 API 종료")

app = FastAPI(
    title="영수증 AI 스캐너 API",
    description="Claude Vision AI를 이용해 영수증을 분석합니다.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

receipt_service = ReceiptService()


@app.post("/scan", response_model=ReceiptResult, summary="영수증 이미지 분석")
async def scan_receipt(file: UploadFile = File(..., description="영수증 이미지 (JPG, PNG, HEIC)")):
    """
    영수증 이미지를 업로드하면 Claude AI가 다음 정보를 추출합니다:
    - 업체명, 주소
    - 방문 날짜 & 시간
    - 이용 내역 (항목별 가격)
    - 총 결제 금액, 결제 방법
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file.content_type}")

    image_bytes = await file.read()

    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB 제한
        raise HTTPException(status_code=400, detail="파일 크기가 너무 큽니다 (최대 10MB)")

    result = await receipt_service.analyze(image_bytes, file.content_type)
    return result


@app.get("/health", summary="서버 상태 확인")
async def health_check():
    return {"status": "ok", "message": "영수증 스캐너 API가 정상 작동 중입니다."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
