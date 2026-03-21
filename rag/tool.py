from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from rag.search import search_drinks_hybrid

# 1. LLM이 추출해야 할 파라미터 구조 정의
class CaffeineSearchInput(BaseModel):
    brands: List[str] = Field(
        description="검색할 브랜드 이름 리스트 (예: ['스타벅스', '컴포즈커피']). 반드시 포함해야 합니다."
    )
    query: Optional[str] = Field(
        default=None,
        description="검색할 음료 메뉴 이름 또는 키워드. 음료명이 언급된 경우에만 입력하세요."
    )

# 2. 실제 검색을 수행하는 도구 함수
@tool(args_schema=CaffeineSearchInput)
async def search_caffeine_by_brands(brands: List[str], query: Optional[str] = None):
    """
    브랜드와 메뉴명을 기반으로 DB에서 카페인 정보를 검색합니다.
    브랜드는 필수이며, 음료명이 언급된 경우에만 query를 함께 전달하세요.
    """
    results = await search_drinks_hybrid(query_text=query, brands=brands)
    
    if not results:
        return "검색 결과가 데이터베이스에 없습니다."
    
    # LLM이 읽기 좋게 텍스트로 변환하여 반환 (이것이 Context가 됨)
    return "\n".join([
        f"브랜드: {item['brand']}, 메뉴: {item['drink_name']}, 카페인: {item['caffeine_amount']}mg" 
        for item in results
    ])