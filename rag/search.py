from typing import Optional
import psycopg
from langsmith import traceable
from core.database import get_pool
from rag.embedding import get_query_embedding


@traceable()
async def search_drinks_by_brand(brands: list[str], fetch_k: int = 20) -> list[any]:
    """브랜드 전체 메뉴를 카페인 높은 순으로 반환합니다."""
    async with get_pool().connection() as conn:
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            await cur.execute("""
                SELECT id, drink_name, brand, caffeine_amount, ice_type
                FROM drinks
                WHERE brand = ANY(%(brand)s::text[])
                ORDER BY caffeine_amount DESC
                LIMIT %(fetch_k)s;
            """, {"brand": brands, "fetch_k": fetch_k})
            return await cur.fetchall()


@traceable()
async def search_drinks_by_menu(query_text: str, fetch_k: int = 10) -> list[any]:
    """전 브랜드에서 메뉴명으로 하이브리드 검색합니다."""
    query_vector = await get_query_embedding(query_text)
    async with get_pool().connection() as conn:
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            await cur.execute("""
                WITH semantic_search AS (
                    SELECT id, drink_name, brand, caffeine_amount, ice_type,
                        ROW_NUMBER() OVER (ORDER BY embedding <=> %(embedding)s::vector) as rank
                    FROM drinks
                    ORDER BY embedding <=> %(embedding)s::vector
                    LIMIT %(fetch_k)s
                ),
                keyword_search AS (
                    SELECT id, drink_name, brand, caffeine_amount, ice_type,
                        ROW_NUMBER() OVER (ORDER BY similarity(drink_name, %(query)s) DESC) as rank
                    FROM drinks
                    WHERE drink_name %% %(query)s
                    ORDER BY similarity(drink_name, %(query)s) DESC
                    LIMIT %(fetch_k)s
                )
                SELECT
                    COALESCE(s.id, k.id) as id,
                    COALESCE(s.drink_name, k.drink_name) as drink_name,
                    COALESCE(s.brand, k.brand) as brand,
                    COALESCE(s.caffeine_amount, k.caffeine_amount) as caffeine_amount,
                    COALESCE(s.ice_type, k.ice_type, 'ice') as ice_type,
                    (COALESCE(1.0 / (s.rank + 100), 0.0) + COALESCE(1.0 / (k.rank + 60), 0.0)) AS rrf_score
                FROM semantic_search s
                FULL OUTER JOIN keyword_search k ON s.id = k.id
                ORDER BY rrf_score DESC
                LIMIT %(fetch_k)s;
            """, {"embedding": str(query_vector), "query": query_text, "fetch_k": fetch_k})
            return await cur.fetchall()


@traceable()
async def search_drinks_hybrid(brands: list[str], query_text: str, fetch_k: int = 10) -> list[any]:
    """브랜드 + 메뉴명으로 하이브리드 검색합니다."""
    query_vector = await get_query_embedding(query_text)
    async with get_pool().connection() as conn:
        async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            await cur.execute("""
                WITH semantic_search AS (
                    SELECT id, drink_name, brand, caffeine_amount, ice_type,
                        ROW_NUMBER() OVER (ORDER BY embedding <=> %(embedding)s::vector) as rank
                    FROM drinks
                    WHERE brand = ANY(%(brand)s::text[])
                    ORDER BY embedding <=> %(embedding)s::vector
                    LIMIT %(fetch_k)s
                ),
                keyword_search AS (
                    SELECT id, drink_name, brand, caffeine_amount, ice_type,
                        ROW_NUMBER() OVER (ORDER BY similarity(drink_name, %(query)s) DESC) as rank
                    FROM drinks
                    WHERE brand = ANY(%(brand)s::text[])
                    AND drink_name %% %(query)s
                    ORDER BY similarity(drink_name, %(query)s) DESC
                    LIMIT %(fetch_k)s
                )
                SELECT
                    COALESCE(s.id, k.id) as id,
                    COALESCE(s.drink_name, k.drink_name) as drink_name,
                    COALESCE(s.brand, k.brand) as brand,
                    COALESCE(s.caffeine_amount, k.caffeine_amount) as caffeine_amount,
                    COALESCE(s.ice_type, k.ice_type, 'ice') as ice_type,
                    (COALESCE(1.0 / (s.rank + 100), 0.0) + COALESCE(1.0 / (k.rank + 60), 0.0)) AS rrf_score
                FROM semantic_search s
                FULL OUTER JOIN keyword_search k ON s.id = k.id
                ORDER BY rrf_score DESC
                LIMIT %(fetch_k)s;
            """, {"embedding": str(query_vector), "query": query_text, "fetch_k": fetch_k, "brand": brands})
            return await cur.fetchall()
