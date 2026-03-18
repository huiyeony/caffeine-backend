from tasks.crawler import run_crawler, BRAND_REGISTRY
from tasks.loader import run_loader


async def run_pipeline():
    """
    ELT 파이프라인 — BRAND_REGISTRY에 등록된 모든 브랜드 처리
    1. Extract + Load → 크롤링 → S3 raw 저장
    2. Transform + Load → S3 raw 읽기 → 변환 → PostgreSQL upsert
    """
    print(">>> [Pipeline] ELT 파이프라인 시작")

    for brand in BRAND_REGISTRY:
        print(f">>> [Pipeline] {brand} 처리 시작")
        s3_key = await run_crawler(brand)
        await run_loader(s3_key)
        print(f">>> [Pipeline] {brand} 처리 완료")

    print(">>> [Pipeline] ELT 파이프라인 완료")
