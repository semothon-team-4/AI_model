import sys
import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 환경변수 로드 (.env 파일이 있다면)
load_dotenv()

# 팀원 폴더들 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'receipt_scan'))
sys.path.append(os.path.join(current_dir, 'new_care_label'))

# 서비스 및 함수 임포트
from receipt_scan.receipt_service import ReceiptService
from new_care_label.pipeline import predict_care_label

app = FastAPI(title="Clothes Up AI API") # API 문서 제목도 변경

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 전체의 서비스 객체 생성
receipt_service = ReceiptService()

@app.get("/")
def health():
    return {"status": "Clothes Up AI Server Online"}

# [1] 영수증 스캔 엔드포인트
@app.post("/predict/receipt")
async def predict_receipt(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        content_type = file.content_type
        result = await receipt_service.analyze(image_bytes, content_type)
        return {"success": True, "type": "receipt", "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# [2] 세탈 택 분석 엔드포인트
@app.post("/predict/care-label")
async def predict_care(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        
        # 바이트 데이터를 이미지로 변환
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # YOLO 모델 실행
        result = predict_care_label(img)
        
        return {"success": True, "type": "care_label", "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)