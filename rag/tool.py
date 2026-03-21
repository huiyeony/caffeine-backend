from pydantic import BaseModel, Field
from langchain_core.tools import tool
from rag.search import search_drinks_by_brand, search_drinks_by_menu, search_drinks_hybrid


class BrandInput(BaseModel):
    brand: str = Field(description="검색할 브랜드 이름 (예: '스타벅스')")

class MenuInput(BaseModel):
    query: str = Field(description="검색할 음료 메뉴 이름 또는 키워드")

class BrandAndMenuInput(BaseModel):
    brand: str = Field(description="검색할 브랜드 이름")
    query: str = Field(description="검색할 음료 메뉴 이름 또는 키워드")


def _format(results: list) -> str:
    if not results:
        return "검색 결과가 데이터베이스에 없습니다."
    return "\n".join([
        f"브랜드: {item['brand']}, 메뉴: {item['drink_name']}, 카페인: {item['caffeine_amount']}mg"
        for item in results
    ])


@tool(args_schema=BrandInput)
async def search_by_brand(brand: str):
    """브랜드 전체 메뉴의 카페인 정보를 조회합니다. 특정 음료명 없이 브랜드만 언급된 경우 사용하세요."""
    results = await search_drinks_by_brand(brand=brand)
    return _format(results)


@tool(args_schema=MenuInput)
async def search_by_menu(query: str):
    """음료 메뉴명으로 전 브랜드에서 카페인 정보를 검색합니다. 브랜드 없이 메뉴명만 언급된 경우 사용하세요."""
    results = await search_drinks_by_menu(query_text=query)
    return _format(results)


@tool(args_schema=BrandAndMenuInput)
async def search_by_brand_and_menu(brand: str, query: str):
    """브랜드와 메뉴명을 함께 사용해 카페인 정보를 검색합니다. 브랜드와 음료명이 모두 언급된 경우 사용하세요."""
    results = await search_drinks_hybrid(brand=brand, query_text=query)
    return _format(results)
