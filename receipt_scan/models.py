from pydantic import BaseModel, Field
from typing import Optional


class ReceiptItem(BaseModel):
    항목: str = Field(description="상품/서비스 이름")
    수량: Optional[int] = Field(default=1, description="수량")
    단가: Optional[int] = Field(default=None, description="단가 (원)")
    금액: Optional[int] = Field(default=None, description="금액 (원)")


class ReceiptResult(BaseModel):
    업체명: Optional[str] = Field(default=None, description="가게/업체 이름")
    날짜: Optional[str] = Field(default=None, description="방문 날짜 (YYYY-MM-DD)")
    시간: Optional[str] = Field(default=None, description="방문 시간 (HH:MM)")
    주소: Optional[str] = Field(default=None, description="업체 주소")
    이용내역: list[ReceiptItem] = Field(default_factory=list, description="이용 내역 목록")
    소계: Optional[int] = Field(default=None, description="소계 (원)")
    부가세: Optional[int] = Field(default=None, description="부가세 (원)")
    할인금액: Optional[int] = Field(default=None, description="할인 금액 (원)")
    총금액: Optional[int] = Field(default=None, description="최종 결제 금액 (원)")
    결제방법: Optional[str] = Field(default=None, description="결제 수단 (카드/현금 등)")
    카드번호: Optional[str] = Field(default=None, description="카드 번호 끝 4자리")
    메모: Optional[str] = Field(default=None, description="기타 특이사항")
