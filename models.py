from pydantic import BaseModel, Field
from typing import Optional
from collections import defaultdict

# 태그 목록 (UI 표시 순서)
TAG_LIST = [
    "일반세탁",
    "드라이클리닝",
    "얼룩제거",
    "신발관리",
    "명품케어",
    "수선",
    "기타",
]

TAG_EMOJI = {
    "일반세탁":    "🧺",
    "드라이클리닝": "👔",
    "얼룩제거":    "✨",
    "신발관리":    "👟",
    "명품케어":    "👜",
    "수선":        "🪡",
    "기타":        "📦",
}


class ReceiptItem(BaseModel):
    항목: str = Field(description="상품/서비스 이름")
    수량: Optional[int] = Field(default=1, description="수량")
    단가: Optional[int] = Field(default=None, description="단가 (원)")
    금액: Optional[int] = Field(default=None, description="금액 (원)")
    태그: Optional[str] = Field(default="기타", description="서비스 카테고리 태그")


class TagGroup(BaseModel):
    태그: str
    이모지: str
    항목들: list[ReceiptItem]
    소계: int


class ReceiptResult(BaseModel):
    업체명: Optional[str] = Field(default=None)
    날짜: Optional[str] = Field(default=None)
    시간: Optional[str] = Field(default=None)
    주소: Optional[str] = Field(default=None)
    이용내역: list[ReceiptItem] = Field(default_factory=list)
    태그그룹: list[TagGroup] = Field(default_factory=list)
    소계: Optional[int] = Field(default=None)
    부가세: Optional[int] = Field(default=None)
    할인금액: Optional[int] = Field(default=None)
    총금액: Optional[int] = Field(default=None)
    결제방법: Optional[str] = Field(default=None)
    카드번호: Optional[str] = Field(default=None)
    메모: Optional[str] = Field(default=None)

    def build_tag_groups(self) -> "ReceiptResult":
        """이용내역을 태그별로 묶어 태그그룹 생성"""
        bucket: dict[str, list[ReceiptItem]] = defaultdict(list)
        for item in self.이용내역:
            tag = item.태그 if item.태그 in TAG_LIST else "기타"
            bucket[tag].append(item)

        groups = []
        for tag in TAG_LIST:
            if tag not in bucket:
                continue
            items = bucket[tag]
            subtotal = sum(i.금액 or 0 for i in items)
            groups.append(TagGroup(
                태그=tag,
                이모지=TAG_EMOJI.get(tag, "📦"),
                항목들=items,
                소계=subtotal,
            ))
        self.태그그룹 = groups
        return self
