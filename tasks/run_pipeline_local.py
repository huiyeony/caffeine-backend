"""로컬 전용 파이프라인 — S3 없이 크롤링 → 직접 DB 적재"""
import asyncio
from core.database import init_pool, close_pool
from tasks.crawler import BRAND_REGISTRY
from tasks.loader import transform, load_to_db


async def main():
    await init_pool()
    print(">>> [Local Pipeline] 시작")

    for brand, crawler_cls in BRAND_REGISTRY.items():
        print(f">>> [Local Pipeline] {brand} 크롤링 중...")
        raw = crawler_cls().crawl()
        print(f">>> [Local Pipeline] {brand} {len(raw)}개 수집, DB 적재 중...")
        records = transform(raw)
        await load_to_db(records)
        print(f">>> [Local Pipeline] {brand} 완료")

    print(">>> [Local Pipeline] 전체 완료")
    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
