import sys
import os
import numpy as np
import cv2

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

sys.path.append(os.path.join(parent_dir, 'receipt_scan'))
sys.path.append(os.path.join(parent_dir, 'new_care_label'))
sys.path.append(os.path.join(parent_dir, 'cloth_grade'))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from receipt_scan.receipt_service import ReceiptService
from new_care_label.pipeline import predict_care_label
from cloth_grade.server import analyze_image, GradeResult

app = FastAPI(title="Clothes Up AI Integrated API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

receipt_service = ReceiptService()

@app.get("/")
def health():
    return {"status": "Clothes Up AI Server Online (Receipt + CareLabel + ClothGrade)"}

# [1] 영수증 스캔
@app.post("/predict/receipt")
async def predict_receipt(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        content_type = file.content_type
        result = await receipt_service.analyze(image_bytes, content_type)
        return {"success": True, "type": "receipt", "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# [2] 세탁 택 분석
@app.post("/predict/care-label")
async def predict_care(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        result = predict_care_label(img)
        return {"success": True, "type": "care_label", "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# [3] 옷 품질 등급 분석
@app.post("/predict/cloth-grade", response_model=GradeResult)
async def predict_grade(file: UploadFile = File(...)):
    try:
        # 이미지 파일 검증
        if file.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
            raise HTTPException(status_code=400, detail='jpg/png/webp 파일만 가능합니다.')
        image_bytes = await file.read()
        
        # 분석 함수 호출
        result = analyze_image(image_bytes, file.content_type)
        
        return result # GradeResult 모델 형식을 그대로 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)